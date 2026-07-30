"""Harness transversal da Rodada 2 — BoTorch (contrato N.1 / §22.3 / L.18).

Infra COMPARTILHADA que os cartões R2 (c262 qNEHVI, c154 JES) — e, por reuso, a
Rodada 3 — consomem. **SEM algoritmo** (os adapters entram nos cartões R2-c262/
R2-c154) e **SEM julgamento de fidelidade** (D97): aqui vive só o encanamento
comum da família BoTorch, provado ponta-a-ponta por um run-STUB (`run_stubpy`,
token `stubpy` — espelho Python do STUB MATLAB do R1-00).

O que este módulo fornece (e de onde vem cada exigência):

- **Pinning D79/N.1.1** — `OMP/OPENBLAS/MKL/NUMEXPR=1` (setados NO TOPO deste
  módulo, antes do `import torch`) + `pin_runtime()` (`torch.set_num_threads(1)`,
  `float64` default, CPU). Nota honesta: no despacho da bateria (D79) o pinning
  autoritativo é o `subprocess` com env limpo; aqui o módulo pina o que é
  pinável em-processo (threads torch/dtype são runtime) e REGISTRA o estado no
  manifesto para auditoria.
- **Guarda N.2.3** — `env_info()` exige o BoTorch OFICIAL (`__version__ ==
  "Unknown"` = o fork do device com kernel `-march=native` ⇒ RuntimeError,
  pára-e-loga D81) e registra versão exata + hash do RECORD instalado, mais a
  versão do scipy (fast-path do L-BFGS-B — L.18) para o manifesto.
- **DoE D63/D87/D88** — `load_doe()` CARREGA o artefato parquet por
  `(problema, semente)` e confere o hash do array decodificado contra o sidecar;
  **NUNCA regenera** (artefato ausente ⇒ FileNotFoundError, pára-e-loga).
- **Adapter §5.5** — `BoTorchProblemAdapter`: a família BoTorch anda em
  `[0,1]^D` e MAXIMIZA; o problema pymoo é nativo e minimiza. `normalize/
  unnormalize` DO BOTORCH fazem a bijeção; `evaluate_unit_max` devolve `−f`;
  `make_standardize()` dá o `Standardize` de Y p/ os modelos. A avaliação real
  é DIRETA (`src.problems.evaluate_problem`, mesmo processo — sem ponte) e passa
  SEMPRE pelo `FEBudget` (cache-hit = 0 FE D89; hard-stop `BudgetExhausted`
  D21/D61).
- **Sementes D62/D91 + L.10** — `iteration_seed()` materializa
  `SeedSequence((base, alg_id, iteracao, uso_id))` como manda o
  `artifacts/seeds.json` (truncando a 32 bits p/ `torch.manual_seed`/pymoo);
  `torch_seed_for()` chama `torch.manual_seed` — a receita L.10 manda invocá-lo
  ANTES de construir modelo+acqf a cada iteração.
- **RNG global N.1.3** — `preserve_global_rng()` salva/restaura `np.random` e
  `random` (o `pymoo.minimize(seed=·)` os re-semeia GLOBALMENTE);
  `guarded_pymoo_minimize()` embrulha a chamada.
- **Higiene D86/N.1.5** — a predição roda sob `torch.no_grad()`;
  `iteration_cleanup()` é o gancho de fim-de-iteração (o chamador `del`eta seus
  tensores e chama o gancho: `gc.collect()` + `empty_cache` se houver GPU).
- **Snapshot §17.3/§17.6** — `SnapshotBuffer` coleta ② (membership do arquivo),
  ③ (candidatos com μ/σ, via `export.surrogate_row`) e a série de timing POR
  ITERAÇÃO DE BO (a política EA-cêntrica "por geração" mapeia p/ "por iteração"
  nos BO puros — §17.3). Pós-retrofit carrega também o `fe_treino_max` corrente
  (DI-09/A1) e completa a linha ④ da geração por `update_timing`.
- **SONDA DI-09/§17.2.2** — `load_sonda()` CARREGA o artefato dos 2000 pontos
  fixos por problema e confere o hash (nunca gera — mesma disciplina do DoE);
  `sonda_due()` dá a cadência k=2; `emit_sonda_block()` prediz e grava as 2000
  linhas ③ `regime='sonda'` + o evento `sonda` do jsonl. `preserve_torch_rng()`
  é a 🔴 guarda de NÃO-PERTURBAÇÃO: nenhum consumo de RNG pela instrumentação
  pode deslocar a trajetória da busca.
- **Persistência §17.7/D58** — `write_run_outputs()` grava as 4 camadas + o
  `.jsonl` + o manifesto (com `doe_hash` do CP-init, env e fit_series) via os
  módulos F0 (`export`/`manifest` — reusados, nunca duplicados);
  `dual_write_run()` espelha no bucket via `gcs.mirror_run` (construído aqui,
  reusado pela R3). No Mac/pilotos `enable_bucket=False` = local puro; a
  política bucket-only plena dos 5 volumosos é da bateria (M8).

Módulo PESADO (torch/botorch) — importe-o LAZY (o `src.experiment` resolve o
despacho por loader string; `import src.experiment` continua leve).
"""

from __future__ import annotations

import gc
import hashlib
import json
import os
import platform
import random
import sys
import time
from contextlib import contextmanager

# ── Pinning D79 (env vars ANTES de qualquer import numérico deste módulo) ────
#: As 4 variáveis de threads BLAS pinadas a 1 (D79 — 1 run = 1 core).
D79_THREAD_VARS: tuple[str, ...] = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
)
for _v in D79_THREAD_VARS:
    os.environ[_v] = "1"

import numpy as np  # noqa: E402 (após o pinning — proposital)
import torch        # noqa: E402

from src import naming                      # noqa: E402
from src import budget as _budget           # noqa: E402
from src import export as _export           # noqa: E402
from src import gcs as _gcs                 # noqa: E402
from src import manifest as _manifest       # noqa: E402
from src.audit_log import AuditLogger       # noqa: E402

#: Dispositivo canônico da Rodada 2 (N.1.1): CPU, sempre (nunca `cuda` sem índice).
DEVICE = torch.device("cpu")

#: alg_id sentinela do STUB (fora da tabela de 22 configs do `seeds.json` —
#: o stubpy NÃO é config do estudo; valor fixo e logado no `.jsonl`).
STUBPY_ALG_ID = 99


# ═══════════════════════════════════════════════════════════════════════════
#  Pinning e ambiente (D79 / N.1.1 / N.2.3 / L.18)
# ═══════════════════════════════════════════════════════════════════════════

def pin_runtime() -> dict:
    """Aplica o pinning em-processo (N.1.1/D79) e devolve o estado p/ auditoria:
    `torch.set_num_threads(1)` + dtype default float64 + CPU. Idempotente —
    chame no INÍCIO de todo run da Rodada 2 (e 3, onde houver torch)."""
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    return {
        "torch_num_threads": torch.get_num_threads(),
        "default_dtype": str(torch.get_default_dtype()),
        "device": str(DEVICE),
        **{v: os.environ.get(v) for v in D79_THREAD_VARS},
    }


def _botorch_record_sha256() -> str | None:
    """Hash SHA256 do RECORD da distribuição instalada do botorch (§22.3 —
    'versão exata + hash no manifesto'). O RECORD lista cada arquivo instalado
    com seu hash ⇒ um só SHA identifica a instalação byte-a-byte."""
    try:
        from importlib import metadata
        txt = metadata.distribution("botorch").read_text("RECORD")
        return hashlib.sha256(txt.encode("utf-8")).hexdigest() if txt else None
    except Exception:  # noqa: BLE001 — hash é informativo; a GUARDA é a versão
        return None


def env_info() -> dict:
    """Versões do stack p/ o manifesto (§22.3/L.18) + GUARDA N.2.3.

    Levanta RuntimeError se o botorch instalado for o FORK do device
    (`__version__ == "Unknown"` — kernel C++ `-march=native` que falha
    silenciosamente no arm64; PROIBIDO). Registra a versão do scipy (o
    fast-path do L-BFGS-B do `optimize_acqf` muda em [1.13, 1.19) — L.18)."""
    import botorch
    import gpytorch
    import pymoo
    import scipy

    if botorch.__version__ == "Unknown":
        raise RuntimeError(
            "botorch.__version__ == 'Unknown' — este é o FORK do device "
            "(N.2.3), PROIBIDO na Rodada 2. Instale o BoTorch OFICIAL 0.18.1. "
            "Pára-e-loga (D81).")
    return {
        "python": platform.python_version(),
        # [G-3/I-09] O INTÉRPRETE que rodou — o `standalone_harness.env_info`
        # (:212) já o gravava e o lado BoTorch não: sem ele o gate de
        # proveniência não tem como afirmar que a célula correu no venv do
        # roster (`envs.json:venvs_aceitos`), e é o roteamento por venv que
        # impede o desastre silencioso do N.1.2. A quimera do c149 só pôde ser
        # DIAGNOSTICADA porque o ⑤ dela declarava o intérprete.
        "executable": sys.executable,
        "numpy": np.__version__,
        "scipy": scipy.__version__,          # L.18 (fonte de não-repro bit-a-bit)
        "pymoo": pymoo.__version__,
        "torch": torch.__version__,
        "gpytorch": gpytorch.__version__,
        "botorch": botorch.__version__,      # N.2.3: exige o OFICIAL
        "botorch_record_sha256": _botorch_record_sha256(),
    }


def restart_de_linha(n_linhas: int, best: int) -> list[int]:
    """[I-12] Qual RESTART é cada linha da ③-online de uma iteração BoTorch.

    A ③ vem na ordem dos restarts com o VENCEDOR removido e re-anexado no fim:
    `linha j → restart j` (j < best) · `→ restart j+1` (j ≥ best) ·
    `linha R−1 → best`. Casar por índice ingênuo conclui "mismatch em **89%** das
    iterações" — e a conclusão é do LEITOR, não do dado (J27 REFUTADO).

    ⚠ Vale para **q=1**. No lote (`c154_jes.py:720-736`, `:810-830`) a montagem
    é outra: se o batch voltar, a regra tem de ser RE-DERIVADA, não presumida.
    """
    R = int(n_linhas)
    best = int(best)
    if R <= 0:
        return []
    if not (0 <= best < R):
        raise ValueError(f"best={best} fora de [0,{R})")
    return [(j if j < best else j + 1) for j in range(R - 1)] + [best]


# ═══════════════════════════════════════════════════════════════════════════
#  Sementes (D62/D91 — fórmula do artifacts/seeds.json; L.10)
# ═══════════════════════════════════════════════════════════════════════════

def iteration_seed(base: int, alg_id: int, iteracao: int, uso_id: int,
                   *, bits32: bool = False) -> int:
    """Materialização canônica do seeds.json (D91):
    `int(SeedSequence((base, alg_id, iteracao, uso_id)).generate_state(1,
    uint64)[0])` — truncada a 32 bits onde a API exigir (`bits32=True` p/
    `torch.manual_seed` e `pymoo.minimize(seed=·)`, como o artefato manda).
    `base` = a semente externa do run (o offset D22 é só de e81/c149 — não R2)."""
    ss = np.random.SeedSequence(
        (int(base), int(alg_id), int(iteracao), int(uso_id)))
    s = int(ss.generate_state(1, dtype=np.uint64)[0])
    return s & 0xFFFFFFFF if bits32 else s


def torch_seed_for(base: int, alg_id: int, iteracao: int,
                   uso_id: int = 0) -> int:
    """`torch.manual_seed(h(run, it))` — a receita L.10 manda chamar ANTES de
    construir modelo+acqf a cada iteração de BO (uso_id 0 no catálogo do c262).
    Devolve a semente usada (para o `.jsonl` — D91: valores efetivos logados)."""
    s = iteration_seed(base, alg_id, iteracao, uso_id, bits32=True)
    torch.manual_seed(s)
    return s


@contextmanager
def preserve_torch_rng():
    """🔴 A guarda de NÃO-PERTURBAÇÃO da sonda (DI-09/§17.2.2).

    O invariante do retrofit é que a instrumentação NÃO altera a busca — a prova
    objetiva é a ① do run com sonda ser bit-idêntica à do run sem. O laço dos 2
    runners BoTorch depende do RNG GLOBAL do torch (`manual_seed` por iteração,
    e o `optimize_acqf`/`fit_gpytorch_mll` consomem desse stream), então
    QUALQUER consumo de RNG pela instrumentação deslocaria a trajetória. Este
    gerenciador salva e restaura o estado do RNG torch em volta da predição.

    O preditor do c262/c154 é determinístico sob `no_grad` (não há o hazard de
    MC-dropout do e7) — a guarda é, portanto, defensiva **por contrato**: ela
    vale mesmo que uma versão futura da lib passe a sortear internamente."""
    state = torch.get_rng_state()
    try:
        yield
    finally:
        torch.set_rng_state(state)


@contextmanager
def preserve_all_rng():
    """`preserve_torch_rng` + `preserve_global_rng` — os 3 streams (torch, numpy
    global e `random`) intactos em volta de um bloco de instrumentação."""
    with preserve_torch_rng(), preserve_global_rng():
        yield


@contextmanager
def preserve_global_rng():
    """N.1.3: `pymoo.minimize(seed=·)` re-semeia `np.random`/`random` GLOBAIS —
    salvar/restaurar o estado em volta de cada chamada (o `Generator` próprio do
    DoE já é imune por construção — D87)."""
    np_state = np.random.get_state()
    py_state = random.getstate()
    try:
        yield
    finally:
        np.random.set_state(np_state)
        random.setstate(py_state)


def guarded_pymoo_minimize(*args, **kwargs):
    """`pymoo.minimize` sob a guarda N.1.3 — o embrulho que c262/c154 (e R3)
    usam para TODO otimizador interno pymoo."""
    from pymoo.optimize import minimize as _minimize
    with preserve_global_rng():
        return _minimize(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
#  Higiene de memória (D86 / N.1.5)
# ═══════════════════════════════════════════════════════════════════════════

def iteration_cleanup() -> None:
    """Gancho D86 de FIM de iteração dos loops torch: o chamador `del`eta seus
    tensores intermediários (modelo, acqf, posteriors) e então chama este
    gancho — `gc.collect()` + `torch.cuda.empty_cache()` quando houver GPU
    (não há no grid pinado a CPU; a guarda é defensiva). Nenhum tensor de
    iterações passadas sobrevive (o export grava e solta)."""
    gc.collect()
    if torch.cuda.is_available():  # pragma: no cover — grid é CPU (N.1.1)
        torch.cuda.empty_cache()


# ═══════════════════════════════════════════════════════════════════════════
#  DoE (D63/D87/D88 — o runner CARREGA; NUNCA regenera)
# ═══════════════════════════════════════════════════════════════════════════

def load_doe(problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Carrega o artefato DoE de `(problema, semente)` e confere o hash do
    array DECODIFICADO contra o sidecar (D87). Artefato ausente ⇒
    FileNotFoundError (o runner NUNCA regenera — D63; o gerador é o F0-02:
    `src.doe.ensure_doe`/`materialize_all`). Hash divergente ⇒ RuntimeError
    (pára-e-loga D81). Retorna `{X (float64), doe_hash, sidecar, path}`."""
    from src import doe as _doe  # lazy — só o leitor/hash (pyarrow)
    path = naming.doe_path(problema, semente, data_root)
    mpath = naming.doe_manifest_path(problema, semente, data_root)
    if not (os.path.exists(path) and os.path.exists(mpath)):
        raise FileNotFoundError(
            f"artefato DoE ausente p/ ({problema}, {semente}): {path} "
            f"(+sidecar). O runner NUNCA regenera (D63) — materialize antes "
            f"com src.doe.ensure_doe (F0-02). Pára-e-loga (D81).")
    with open(mpath, encoding="utf-8") as fh:
        side = json.load(fh)
    X = _doe._read_matrix_parquet(path, side["columns"])
    h = _doe.decoded_hash(X)
    if h != side.get("doe_hash"):
        raise RuntimeError(
            f"DoE ({problema}, {semente}): hash do array decodificado diverge "
            f"do sidecar ({h[:16]}… != {str(side.get('doe_hash'))[:16]}…) — "
            f"artefato corrompido. Pára-e-loga (D81).")
    return {"X": X, "doe_hash": h, "sidecar": side, "path": path}


# ═══════════════════════════════════════════════════════════════════════════
#  SONDA canônica DI-09 / SPEC §17.2.2 (a régua fixa de 2000 pontos)
# ═══════════════════════════════════════════════════════════════════════════

#: Cadência ONLINE da sonda (decisão do autor, DI-09): a cada k=2 iterações,
#: SEMPRE a 1ª e a última. (OFFLINE = 1× por modelo treinado — não é a R2.)
SONDA_K = 2

#: Tamanho do lote de predição da sonda. Numericamente neutro (os 2000 pontos
#: são independentes no posterior: μ é linha-a-linha e σ é a diagonal), mas
#: evita materializar a covariância 2000×2000 do gpytorch. Constante FIXA —
#: mudá-la é mudar o custo, nunca o valor.
SONDA_CHUNK = 512

#: Cache por processo: o artefato é FIXO por problema e o hash é conferido no
#: primeiro carregamento (a sonda roda dezenas de vezes por run — carregar e
#: re-hashear 2000×D floats a cada bloco seria puro desperdício).
_SONDA_CACHE: dict[str, dict] = {}


def clear_sonda_cache() -> None:
    """Esvazia o cache de sonda por processo. [DI-13.5] A chave é
    `(problema, regime, data_root)` — o `data_root` FALTAVA (bug latente: um
    load de outra pasta devolvia o artefato cacheado, mascarando adulteração).
    Testes usam ESTA função em vez de mexer no dict interno."""
    _SONDA_CACHE.clear()


def load_sonda(problema: str, *,
               regime: str = "online",
               data_root: str = naming.DEFAULT_DATA_ROOT) -> dict:
    """Carrega o artefato da SONDA de `problema` e confere os hashes do sidecar.

    Mesma disciplina do DoE (D63/D87/D88): o runner **NUNCA gera** os pontos —
    carrega `data/sonda/sonda_{problema}.parquet` (gerado 1× por
    `scripts/gen_sonda.py`) e confere `x_hash`/`f_hash` (sha256 dos bytes
    float64 row-major) contra `sonda_{problema}.manifest.json`. Ausente ⇒
    FileNotFoundError; hash divergente ⇒ RuntimeError (pára-e-loga D81).

    A ORDEM DAS LINHAS é a ordem de geração Sobol e é o que o writer da ③ tem
    de preservar — o gabarito (`F`) casa com o bloco de sonda POR POSIÇÃO
    (CONTRATO §3.1 / R4 regra 5). Retorna
    `{X, F, S, D, M, x_hash, f_hash, path, sidecar}` (X/F float64).
    Resultado cacheado por processo (o artefato é imutável)."""
    _ck = (problema, regime, os.path.abspath(data_root))
    if _ck in _SONDA_CACHE:
        return _SONDA_CACHE[_ck]
    base = os.path.join(data_root, "sonda", f"sonda_{problema}")
    path, mpath = base + ".parquet", base + ".manifest.json"
    if not (os.path.exists(path) and os.path.exists(mpath)):
        raise FileNotFoundError(
            f"artefato da SONDA ausente p/ {problema}: {path} (+sidecar). O "
            f"runner NUNCA gera pontos de sonda (§17.2.2) — materialize antes "
            f"com scripts/gen_sonda.py. Pára-e-loga (D81).")
    with open(mpath, encoding="utf-8") as fh:
        side = json.load(fh)
    import pyarrow.parquet as pq
    tbl = pq.read_table(path)
    D, M, S = int(side["D"]), int(side["M"]), int(side["S"])
    X = np.column_stack([np.asarray(tbl.column(f"x{j}"), dtype=np.float64)
                         for j in range(D)])
    F = np.column_stack([np.asarray(tbl.column(f"f{j}"), dtype=np.float64)
                         for j in range(M)])
    if X.shape != (S, D) or F.shape != (S, M):
        raise RuntimeError(
            f"SONDA {problema}: shapes {X.shape}/{F.shape} != "
            f"({S},{D})/({S},{M}) do sidecar. Pára-e-loga (D81).")
    xh, fh_ = _sonda_hash(X), _sonda_hash(F)
    if xh != side.get("x_hash") or fh_ != side.get("f_hash"):
        raise RuntimeError(
            f"SONDA {problema}: hash do array decodificado diverge do sidecar "
            f"(x {xh[:16]}… vs {str(side.get('x_hash'))[:16]}…; f {fh_[:16]}… "
            f"vs {str(side.get('f_hash'))[:16]}…) — artefato corrompido. "
            f"Pára-e-loga (D81).")
    # ── [DI-13.5, autor 2026-07-19] fatia por REGIME ──────────────────────────
    # O artefato tem S=20.000. ONLINE lê as PRIMEIRAS `S_online` (2.000), a cada
    # k=2 gerações; OFFLINE lê TODAS (o modelo treina 1×, então cabe MUITO mais
    # ponto pela mesma análise). Sobol é ANINHADO: a fatia online é BIT-IDÊNTICA
    # a uma sonda gerada com 2.000 (provado em tests/test_di13.py) — a régua é a
    # MESMA nos dois regimes na faixa compartilhada, e os runs online já
    # retrofitados NÃO precisam ser refeitos.
    if regime == "online":
        n_on = int(side.get("S_online", 2000))
        X, F = X[:n_on], F[:n_on]
        xh_on = _sonda_hash(X)
        if side.get("x_hash_online") and xh_on != side["x_hash_online"]:
            raise RuntimeError(
                f"SONDA {problema}: a fatia ONLINE [0:{n_on}] diverge do "
                f"`x_hash_online` do sidecar — artefato corrompido. Pára-e-loga (D81).")
        fh_on = _sonda_hash(F)
        # [DI-24/achado §8.7 do e81] o f_hash_online também se confere — antes
        # era recalculado e NUNCA comparado (ia não-auditado ao manifesto).
        if side.get("f_hash_online") and fh_on != side["f_hash_online"]:
            raise RuntimeError(
                f"SONDA {problema}: o F da fatia ONLINE diverge do "
                f"`f_hash_online` do sidecar — artefato corrompido. Pára-e-loga (D81).")
        xh, fh_, S = xh_on, fh_on, n_on
    art = {"X": X, "F": F, "S": S, "D": D, "M": M, "regime": regime,
           "x_hash": xh, "f_hash": fh_, "path": path, "sidecar": side}
    _SONDA_CACHE[_ck] = art
    return art


def _sonda_hash(arr: np.ndarray) -> str:
    """sha256 dos bytes float64 row-major — a MESMA convenção do DoE (D87)."""
    return hashlib.sha256(
        np.ascontiguousarray(arr, dtype=np.float64).tobytes()).hexdigest()


def sonda_due(it: int, *, k: int = SONDA_K) -> bool:
    """Cadência ONLINE (§17.2.2): a 1ª iteração e depois a cada `k`. A ÚLTIMA
    também é obrigatória, mas só se sabe qual é quando o hard-stop chega — o
    runner cobre esse caso emitindo o bloco no ramo `BudgetExhausted` se a
    iteração corrente ainda não tiver emitido (ver `run_c262`/`run_c154`)."""
    it = int(it)
    return it == 1 or it % int(k) == 0


def sonda_predict_gp(model, adapter: "BoTorchProblemAdapter",
                     X_sonda: np.ndarray, *, chunk: int = SONDA_CHUNK):
    """Prediz μ/σ POR OBJETIVO nos pontos da sonda com um modelo BoTorch de
    regressão (a semântica da linha do CONTRATO §3.2 p/ c262/c154 e os demais
    regressores da família).

    - Roda sob `no_grad` (D86) **e** sob `preserve_torch_rng` — a guarda de
      não-perturbação (§17.2.2).
    - O modelo vive em [0,1]^D e em −f (maximização, §5.5): a entrada é
      convertida pelo adapter e o μ devolvido é **em f (minimização)**, como
      manda o export — o sinal invertido nunca vaza.
    - Em lotes de `chunk` (independentes ⇒ numericamente neutro).

    Retorna `(mu_f (S,M), sigma (S,M))` em float64, na ORDEM do artefato."""
    U = adapter.to_unit(np.asarray(X_sonda, dtype=np.float64))
    mus, sigmas = [], []
    with preserve_all_rng(), torch.no_grad():
        for i in range(0, U.shape[0], int(chunk)):
            post = model.posterior(U[i:i + int(chunk)])
            mus.append(post.mean.cpu().numpy())
            sigmas.append(np.sqrt(post.variance.cpu().numpy()))
            del post
    return -np.vstack(mus), np.vstack(sigmas)


def emit_sonda_block(buf: "SnapshotBuffer", log, *, it: int, fe: int,
                     sonda: dict, adapter: "BoTorchProblemAdapter", model,
                     fe_treino_max: int, modelo_flag: str = "GP",
                     motivo: str = "cadencia k=2") -> float:
    """Emite UM bloco de sonda: prediz os S pontos, grava as S linhas na ③ com
    `regime='sonda'` **na ordem do artefato** e loga o evento `sonda` do jsonl
    (§17.2.2 + CONTRATO §6). Custo de FE: ZERO (o `f` verdadeiro já está no
    artefato — exceção contábil documentada). Retorna `tempo_pred_sonda_s`.

    O bloco inteiro corre sob a guarda de RNG (dentro de `sonda_predict_gp`) e
    não toca o `FEBudget` — a busca não vê nada disto acontecer."""
    t0 = time.time()
    mu_f, sigma = sonda_predict_gp(model, adapter, sonda["X"])
    X = sonda["X"]
    for i in range(X.shape[0]):
        buf.add_surrogate(_export.surrogate_row(
            it, X[i], regime="sonda", real_solution_id=None,
            mu=mu_f[i], sigma=sigma[i], pred_tipo="valor",
            modelo_flag=modelo_flag, fe_treino_max=fe_treino_max))
    dt = time.time() - t0
    log.event("sonda", it=it, geracao=it, fe=int(fe),
              n_pontos=int(X.shape[0]),
              tempo_pred_sonda_s=round(dt, 4),
              fe_treino_max=int(fe_treino_max),
              sonda_x_hash=sonda["x_hash"], sonda_f_hash=sonda["f_hash"],
              hash_check="ok (conferido no arranque — load_sonda)",
              motivo=motivo)
    return dt


# ═══════════════════════════════════════════════════════════════════════════
#  Mínimo comum DI-10 do `<alg>_gen` (SPEC §S.7.1 — os 21 configs)
# ═══════════════════════════════════════════════════════════════════════════

def di10_minimo_comum(bud, *, u_infill=None, train_U=None) -> dict:
    """As grandezas que o DI-10 tornou mínimo comum de TODO `<alg>_gen`:

    - `f_best`: o melhor valor por objetivo no ① até aqui (o "melhor-até-agora"
      do §17.5; não é um ponto — é o ideal empírico).
    - `n_front1`: |ND| corrente do ① (o tamanho do front não-dominado).
    - `dist_min_arquivo` (B3): distância euclidiana do infill ao ponto mais
      próximo do arquivo, no **espaço de decisão NORMALIZADO** [0,1]^D — é o
      indicador de exploração×explotação sob incerteza (CONTRATO §9). Só sai
      quando `u_infill`/`train_U` são passados (é "por infill").

    Read-only sobre o `FEBudget` e sem RNG — não perturba nada. `fe` e os
    tempos ficam com o chamador (que os tem à mão)."""
    from src.problems import _nds_filter          # lazy (pymoo)
    with preserve_all_rng(), torch.no_grad():     # não-perturbação (defensivo)
        F = np.vstack([r.f for r in bud.records])
        out = {
            "f_best": [float(v) for v in F.min(axis=0)],
            # ⚠ `_nds_filter` devolve ÍNDICES (não máscara booleana) — o
            # tamanho do front é `len`, nunca um count_nonzero (que comeria
            # silenciosamente o índice 0 sempre que ele fosse não-dominado).
            "n_front1": int(len(_nds_filter(F))),
        }
        if u_infill is not None and train_U is not None:
            u = torch.as_tensor(u_infill, dtype=torch.float64).reshape(-1)
            A = torch.as_tensor(train_U,
                                dtype=torch.float64).reshape(-1, u.shape[0])
            if A.shape[0]:
                out["dist_min_arquivo"] = float(
                    torch.linalg.norm(A - u, dim=1).min())
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  Adapter de problema §5.5 (bounds [0,1]↔nativo · sinal −f · Standardize)
# ═══════════════════════════════════════════════════════════════════════════

class BoTorchProblemAdapter:
    """O contrato §5.5 da família BoTorch, amarrado ao `FEBudget`.

    - A implementação oficial anda em `[0,1]^D` e MAXIMIZA; o `problems.py`
      (fonte única A2) é nativo e minimiza. A bijeção usa `normalize/
      unnormalize` DO BOTORCH (`self.bounds_native`, 2×D float64); o sinal
      inverte SÓ na saída p/ o motor (`evaluate_unit_max` → `−f`) — a camada ①
      e a métrica ficam SEMPRE no `f` verdadeiro de minimização.
    - TODA avaliação real passa por `bud.evaluate` (D89: dedup por X NATIVO
      bit-a-bit; a des-normalização é determinística ⇒ a mesma `u` produz o
      mesmo X nativo ⇒ cache-hit). `BudgetExhausted` PROPAGA — o runner captura
      no ponto único (D61) e fecha o run com FE = 31D−1 cravado.
    - `tempo_aval_real_s` acumula o wall-clock das avaliações verdadeiras
      (desdobramento do manifesto — §17.6).
    """

    def __init__(self, problema_id: str, bud: _budget.FEBudget):
        from src import experiment as _exp  # lazy (evita ciclo de import)
        from src import problems as _problems
        self.problema_id = problema_id
        self.problem = _exp._instantiate_problem(problema_id)
        self._evaluate_problem = _problems.evaluate_problem
        self.bud = bud
        self.D = int(self.problem.n_var)
        self.M = int(self.problem.n_obj)
        self.xl = np.asarray(self.problem.xl, dtype=np.float64)
        self.xu = np.asarray(self.problem.xu, dtype=np.float64)
        #: bounds nativos p/ normalize/unnormalize do botorch (2×D, float64/CPU).
        self.bounds_native = torch.tensor(
            np.vstack([self.xl, self.xu]), dtype=torch.float64, device=DEVICE)
        self.tempo_aval_real_s = 0.0

    # ── bijeção [0,1] ↔ nativo (botorch.utils.transforms — §5.5) ───────────
    def to_native(self, U) -> np.ndarray:
        """`x_nativo = xl + u·(xu−xl)` via `botorch.utils.transforms.unnormalize`.
        `U` = (n×D) ou (D,) em [0,1] (torch ou numpy) → ndarray float64 nativo."""
        from botorch.utils.transforms import unnormalize
        Ut = torch.as_tensor(U, dtype=torch.float64, device=DEVICE)
        squeeze = Ut.dim() == 1
        if squeeze:
            Ut = Ut.unsqueeze(0)
        Xn = unnormalize(Ut, self.bounds_native).cpu().numpy()
        return Xn[0] if squeeze else Xn

    def to_unit(self, X) -> "torch.Tensor":
        """Nativo → [0,1]^D via `botorch.utils.transforms.normalize` (p/ montar
        train_X dos modelos). Retorna tensor float64/CPU."""
        from botorch.utils.transforms import normalize
        Xt = torch.as_tensor(X, dtype=torch.float64, device=DEVICE)
        squeeze = Xt.dim() == 1
        if squeeze:
            Xt = Xt.unsqueeze(0)
        U = normalize(Xt, self.bounds_native)
        return U[0] if squeeze else U

    # ── avaliação verdadeira (ponto único de orçamento) ────────────────────
    def _true_f(self, x: np.ndarray) -> np.ndarray:
        t0 = time.time()
        f = np.asarray(self._evaluate_problem(self.problem, x),
                       dtype=np.float64).reshape(-1)
        self.tempo_aval_real_s += time.time() - t0
        return f

    def evaluate_native(self, x) -> np.ndarray:
        """Avalia UM x NATIVO pelo wrapper de FE. Devolve `f` de minimização
        (float64). Cache-hit = 0 FE (D89); saldo zerado ⇒ `BudgetExhausted`."""
        return self.bud.evaluate(np.asarray(x, dtype=np.float64), self._true_f)

    def evaluate_unit_max(self, U) -> "torch.Tensor":
        """Avalia candidatos em [0,1]^D e devolve **−f** (n×M, float64) — a
        convenção de MAXIMIZAÇÃO do BoTorch (§5.5). O sinal invertido vive só
        aqui (dentro do motor); ① e métrica ficam no `f` verdadeiro."""
        Xn = self.to_native(U)
        if Xn.ndim == 1:
            Xn = Xn.reshape(1, -1)
        F = np.vstack([self.evaluate_native(Xn[i]) for i in range(Xn.shape[0])])
        return torch.as_tensor(-F, dtype=torch.float64, device=DEVICE)

    # ── Standardize de Y (§5.5) ────────────────────────────────────────────
    def make_standardize(self):
        """`Standardize(m=M)` do botorch — o outcome transform que c262/c154
        pluggam no modelo (Y = −f já em maximização)."""
        from botorch.models.transforms.outcome import Standardize
        return Standardize(m=self.M)


# ═══════════════════════════════════════════════════════════════════════════
#  Snapshot por iteração de BO (§17.3/§17.4/§17.6) — espelho do RunBuffer.m
# ═══════════════════════════════════════════════════════════════════════════

class SnapshotBuffer:
    """Coletor de ② (membership) + ③ (candidatos c/ μ/σ) + timing por ITERAÇÃO
    de BO. Nos BO puros, "geração" ≡ iteração de BO (§17.3); as linhas ③ são o
    conjunto de candidatos avaliados no surrogate naquela iteração."""

    def __init__(self) -> None:
        self.pop_rows: list[tuple[int, int]] = []
        self.surr_rows: list[dict] = []
        self.timing_rows: list[dict] = []
        #: DI-09/A1: o `fe_treino_max` CORRENTE (maior `fe_index` no treino do
        #: modelo ajustado nesta iteração). O runner o crava logo após o fit e
        #: toda linha ③ emitida daí em diante o herda — assim nenhuma predição
        #: sai sem o marcador in-sample × out-of-sample.
        self.fe_treino_max: int | None = None

    def set_fe_treino_max(self, fe_treino_max: int | None) -> None:
        """Crava o marcador A1 da iteração corrente (chamar logo após o fit)."""
        self.fe_treino_max = (None if fe_treino_max is None
                              else int(fe_treino_max))

    def add_pop(self, geracao: int, solution_ids) -> None:
        """Membership do arquivo real na iteração `geracao` (② — §17.2)."""
        self.pop_rows.extend((int(geracao), int(s)) for s in solution_ids)

    def add_surrogate(self, row: dict) -> None:
        """Uma linha ③ montada com `export.surrogate_row(...)` (C1/C3). Herda o
        `fe_treino_max` corrente do buffer quando a linha não trouxer o seu."""
        if row.get("fe_treino_max") is None and self.fe_treino_max is not None:
            row = {**row, "fe_treino_max": self.fe_treino_max}
        self.surr_rows.append(row)

    def add_timing(self, geracao: int, n_acumulado: int, tempo_fit_s: float,
                   tempo_busca_s: float | None = None,
                   tempo_pred_sonda_s: float | None = None,
                   tempo_geracao_s: float | None = None) -> None:
        """Um evento de retreino → série `(n_acumulado, tempo_fit_s)` (§17.6).

        Os runners BoTorch chamam este método IMEDIATAMENTE após o fit (para
        que a curva O(n³) retenha o fit final mesmo quando o hard-stop corta a
        iteração — D61), portanto os tempos de busca/sonda/geração ainda não
        existem: eles entram depois, por `update_timing`."""
        self.timing_rows.append({
            "geracao": int(geracao), "n_acumulado": int(n_acumulado),
            "tempo_fit_s": float(tempo_fit_s),
            "tempo_busca_s": (None if tempo_busca_s is None
                              else float(tempo_busca_s)),
            "tempo_pred_sonda_s": (None if tempo_pred_sonda_s is None
                                   else float(tempo_pred_sonda_s)),
            "tempo_geracao_s": (None if tempo_geracao_s is None
                                else float(tempo_geracao_s)),
        })

    def update_timing(self, geracao: int, **campos) -> None:
        """Completa a linha ④ da geração `geracao` com os tempos que só se
        conhecem no FIM da iteração (`tempo_busca_s`, `tempo_pred_sonda_s`,
        `tempo_geracao_s` — §17.6 expandida). Geração desconhecida ⇒ KeyError
        (falha barulhenta: uma ④ meio-preenchida em silêncio é pior que um
        aborto)."""
        alvo = int(geracao)
        for row in reversed(self.timing_rows):
            if row["geracao"] == alvo:
                row.update({k: (None if v is None else float(v))
                            for k, v in campos.items()})
                return
        raise KeyError(
            f"update_timing: geração {alvo} não está na série ④ "
            f"(add_timing precisa vir antes). Pára-e-loga (D81).")

    @property
    def fit_series(self) -> list[dict]:
        """Cópia leve p/ o manifesto (§17.6; a canônica é `__timing.parquet`)."""
        return [{"iter": t["geracao"], "n_acumulado": t["n_acumulado"],
                 "tempo_fit_s": t["tempo_fit_s"]} for t in self.timing_rows]


# ═══════════════════════════════════════════════════════════════════════════
#  Export + manifesto + dual-write (§17.2/§17.7/D58 — reusa os módulos F0)
# ═══════════════════════════════════════════════════════════════════════════

def write_run_outputs(exp: str, alg: str, problema: str, semente,
                      bud: _budget.FEBudget, buf: SnapshotBuffer, *,
                      adapter: BoTorchProblemAdapter,
                      doe_hash_sidecar: str, env: dict, pinning: dict,
                      n_geracoes: int, algo_version: str,
                      timing_totais: dict, regime: str = "online",
                      status: str = "ok",
                      motivo_parada: str | None = None,
                      params: dict | None = None,
                      q: int = 1,
                      data_root: str = naming.DEFAULT_DATA_ROOT,
                      enable_bucket: bool = False) -> dict:
    """Fecha o run: 4 camadas §17.2 (via `src.export` — reuso, não duplicação),
    manifesto §17.7 (doe_hash do CP-init + env N.2.3/L.18 + fit_series §17.6) e,
    se `enable_bucket`, o dual-write §17.7 (`dual_write_run`). O CP-init é
    AFIRMADO aqui: `hash(init_X float64) != sidecar` ⇒ RuntimeError (encanamento
    objetivo — D88; nada de fidelidade, D97). Retorna `{manifest, cp_init_ok,
    doe_hash_run, upload_status}`."""
    from src import doe as _doe

    _export.write_real(exp, alg, problema, semente, bud.records,
                       data_root=data_root)
    _export.write_pop(exp, alg, problema, semente, buf.pop_rows,
                      data_root=data_root)
    _export.write_surrogate(exp, alg, problema, semente, buf.surr_rows,
                            D=adapter.D, M=adapter.M, regime=regime,
                            data_root=data_root)
    _export.write_timing(exp, alg, problema, semente, buf.timing_rows,
                         data_root=data_root)

    # CP-init por-run (D87/D88): hash float64 da init X capturada pelo wrapper.
    doe_hash_run = _doe.decoded_hash(bud.init_X())
    if doe_hash_run != doe_hash_sidecar:
        raise RuntimeError(
            f"CP-init FALHOU: hash da init X do run ({doe_hash_run[:16]}…) != "
            f"sidecar do DoE ({doe_hash_sidecar[:16]}…) — o run NÃO partiu do "
            f"artefato compartilhado (D88). Pára-e-loga (D81).")

    # [DI-25] status/motivo/q pela infra (simétrico ao standalone_harness,
    # DI-23/DI-24): o batch (q=10) de c262/c154 nasce com manifesto honesto.
    man = _manifest.new_manifest(
        exp, alg, problema, semente, status=status, q=int(q),
        regime=regime, maxfe=bud.maxfe, fe_final=bud.fe,
        n_geracoes=int(n_geracoes), doe_hash=doe_hash_run,
        algo_version=algo_version,
        env={**env, "pinning": pinning},
        timing=timing_totais, fit_series=buf.fit_series,
        data_root=data_root,
        bucket=(_gcs.BUCKET if enable_bucket else None))
    man["cache_hits"] = bud.cache_hits                    # D89 (informativo)
    if motivo_parada is not None:
        man["motivo_parada"] = motivo_parada
    # [I-07] `params` = a CONFIG EFETIVA do algoritmo. O CONTRATO §5 a lista como
    # obrigatória e o stack BoTorch a gravava SÓ no header do ⑥: medido na s42,
    # 24 células de c262 + 13 de c154 sem a chave no ⑤ (com o roster completo,
    # 750+750 = 1.500 células violando o §5). Quem lê a tabela de execuções não
    # tem por que abrir o ⑥ de 40 MB para saber com que num_restarts o run correu.
    if params is not None:
        man["params"] = params
    _manifest.write_manifest(man, data_root)

    upload_status = None
    if enable_bucket:
        upload_status = dual_write_run(exp, alg, problema, semente,
                                       manifest_dict=man, data_root=data_root)
    return {"manifest": man, "cp_init_ok": True,
            "doe_hash_run": doe_hash_run, "upload_status": upload_status}


def dual_write_run(exp: str, alg: str, problema: str, semente, *,
                   manifest_dict: dict,
                   data_root: str = naming.DEFAULT_DATA_ROOT,
                   client=None) -> dict:
    """Dual-write §17.7 (local-primeiro já feito): `gcs.mirror_run` sobe as
    camadas + jsonl + manifesto (e poda a ③ local dos bucket-only — D58), o
    `upload_status` entra no manifesto, que é regravado e re-subido. Reusado
    pela R3.

    [DI-42.3] BLINDADO: falha de upload (lib gcs ausente no env, rede, auth)
    NUNCA mata o run — o dado JÁ está salvo local (local-primeiro §17.7) e o
    upload é re-executável a posteriori (gcs.sync). Sem esta blindagem, 7/58
    runs do c311 na rodada-42 morreram AQUI (env_c311 sem google-cloud-storage)
    DEPOIS do manifesto 'ok' e ANTES do footer do ⑥ — diário truncado sem
    sintoma. A falha fica REGISTRADA no manifesto (`upload_status.erro`)."""
    try:
        status = _gcs.mirror_run(exp, alg, problema, semente,
                                 data_root=data_root, client=client)
        manifest_dict["upload_status"] = status
        mpath = _manifest.write_manifest(manifest_dict, data_root)
        _gcs.upload(mpath,
                    naming.blob_path(exp, alg,
                                     naming.manifest_filename(exp, alg,
                                                              problema,
                                                              semente)),
                    client=client)
        return status
    except Exception as e:  # noqa: BLE001 — upload é acessório; dado é local
        status = {"erro": f"upload_failed: {e!r}"}
        manifest_dict["upload_status"] = status
        try:
            _manifest.write_manifest(manifest_dict, data_root)
        except Exception:  # noqa: BLE001 — manifesto local anterior permanece
            pass
        return status


# ═══════════════════════════════════════════════════════════════════════════
#  Run-STUB `stubpy` — prova de encanamento ponta-a-ponta (SEM algoritmo)
# ═══════════════════════════════════════════════════════════════════════════

def _rng_guard_probe(problema_adapter: BoTorchProblemAdapter) -> bool:
    """Prova N.1.3 contra o culpado REAL: roda um `pymoo.minimize` mínimo
    (NSGA-II pop 8 × 2 gerações sobre o problema pymoo canônico — fora do
    orçamento: é só sonda de RNG) via `guarded_pymoo_minimize` e confere que o
    estado global do numpy/random saiu INTACTO."""
    from pymoo.algorithms.moo.nsga2 import NSGA2
    np_before = np.random.get_state()
    py_before = random.getstate()
    guarded_pymoo_minimize(problema_adapter.problem, NSGA2(pop_size=8),
                           ("n_gen", 2), seed=1, verbose=False)
    np_after = np.random.get_state()
    py_after = random.getstate()
    same_np = (np_before[0] == np_after[0]
               and np.array_equal(np_before[1], np_after[1])
               and np_before[2:] == np_after[2:])
    return bool(same_np and py_before == py_after)


def run_stubpy(exp: str, alg: str, problema: str, semente, *,
               data_root: str = naming.DEFAULT_DATA_ROOT,
               enable_bucket: bool = False, **_kwargs) -> dict:
    """O run-STUB transversal do R2-00 (token `stubpy` — NUNCA `stub`, que é o
    STUB MATLAB do R1-00). SEM algoritmo (c262/c154 são os próximos cartões) e
    SEM fidelidade (D97): prova o ENCANAMENTO do contrato N.1 ponta-a-ponta —

      init = DoE carregado do artefato (D63) → 20D "infills" propostos por um
      sorteio torch semeado (L.10: `manual_seed` ANTES do "modelo+acqf" de cada
      iteração; predição fake sob `no_grad` — D86), unit-cube→nativo→`−f` pelo
      adapter §5.5 → cache-hit por U repetida E por X nativa (D89, 0 FE) →
      hard-stop NATURAL no laço (`BudgetExhausted` na 31D-ésima inédita — D61)
      → 4 camadas §17.2 + `.jsonl` §17.5 + manifesto com CP-init/env/pinning.

    Assinatura padrão dos runners R2 (o `experiment.run` repassa `**kwargs`).
    Retorna o dict de evidências que o `accept.py R2-00-harness` afere."""
    t0 = time.time()
    pinning = pin_runtime()
    env = env_info()                                  # guarda N.2.3 (fork ⇒ pára)
    semente = int(semente)

    doe_art = load_doe(problema, semente, data_root=data_root)
    log = AuditLogger.for_run(exp, alg, problema, semente,
                              data_root=data_root, append=False)
    try:
        return _run_stubpy_body(exp, alg, problema, semente, t0, pinning, env,
                                doe_art, log, data_root, enable_bucket)
    finally:
        log.close()


def _run_stubpy_body(exp, alg, problema, semente, t0, pinning, env,
                     doe_art, log, data_root, enable_bucket) -> dict:
    bud = _budget.FEBudget(D=doe_art["X"].shape[1], logger=log)
    adapter = BoTorchProblemAdapter(problema, bud)
    D, M = adapter.D, adapter.M
    buf = SnapshotBuffer()

    log.header(run_id=naming.run_id(exp, alg, problema, semente),
               alg=alg, alg_id=STUBPY_ALG_ID, problema=problema, D=D, M=M,
               semente=semente, regime="online", maxfe=bud.maxfe,
               doe_hash=doe_art["doe_hash"], env=env, pinning=pinning,
               algo_version="stubpy-R2-00")

    # (1) init: os 11D−1 pontos do DoE, NATIVOS, pelo wrapper (fase `init`).
    X0 = doe_art["X"]
    for i in range(X0.shape[0]):
        adapter.evaluate_native(X0[i])
    buf.add_pop(0, [r.solution_id for r in bud.records])   # arquivo inicial

    # provas §5.5 colhidas no laço: sinal (−f) e Standardize de Y.
    sign_ok = True
    stdz = adapter.make_standardize()
    Y0 = torch.as_tensor(-np.vstack([r.f for r in bud.records]),
                         dtype=torch.float64)
    Ystd, _ = stdz(Y0)
    standardize_ok = bool(torch.isfinite(Ystd).all()
                          and Ystd.shape == Y0.shape
                          and float(Ystd.mean().abs()) < 1e-6)
    del Y0, Ystd

    # (2) opt: infills até o hard-stop NATURAL (D61) — 20D cabem; o 20D+1-ésimo
    # levanta BudgetExhausted no ponto único de avaliação.
    seeds_used: list[int] = []
    cache_hit_zero_fe_unit = False
    cache_hit_zero_fe_native = False
    hard_stopped = False
    tempo_fit_total = 0.0
    tempo_busca_total = 0.0
    it = 0
    try:
        while True:
            it += 1
            # L.10: manual_seed ANTES de construir "modelo+acqf" da iteração.
            seed_it = torch_seed_for(semente, STUBPY_ALG_ID, it, uso_id=0)
            seeds_used.append(seed_it)
            # §17.6: o "fit" desta iteração treinou com os pontos JÁ avaliados
            # (11D−1 + it−1) — capturar ANTES do infill consumir o FE.
            n_train = bud.fe

            # "fit" + "aquisição" fake em torch (float64/CPU), predição sob
            # no_grad (D86). O candidato é u ~ U[0,1]^D do RNG torch semeado.
            t_fit0 = time.time()
            with torch.no_grad():
                u = torch.rand(1, D)                       # float64 (default)
                mu_fake = torch.sin(u).mean(dim=1, keepdim=True).repeat(1, M)
                sigma_fake = 1e-3 * (1.0 + torch.cos(u).abs().mean())
            tempo_fit = time.time() - t_fit0

            t_busca0 = time.time()
            x_nat = adapter.to_native(u)[0]
            if bud.solution_id_of(x_nat) is not None:      # colisão (prob≈0)
                u = (u + 0.5) % 1.0
                x_nat = adapter.to_native(u)[0]
            y_max = adapter.evaluate_unit_max(u)           # −f (consome 1 FE)
            tempo_busca = time.time() - t_busca0

            sid = bud.solution_id_of(x_nat)
            f_true = bud.records[sid].f
            sign_ok = sign_ok and bool(
                np.allclose(y_max.cpu().numpy()[0], -f_true))

            # snapshot da iteração (§17.3): o escolhido (ligado ao ①) + um
            # candidato só-surrogate (real_solution_id NULL).
            buf.add_surrogate(_export.surrogate_row(
                it, x_nat, real_solution_id=sid,
                mu=[float(mu_fake[0, j]) for j in range(M)],
                sigma=[float(sigma_fake)] * M,
                pred_tipo="valor", modelo_flag="GP-stub"))
            with torch.no_grad():
                u_ghost = torch.rand(1, D)
            buf.add_surrogate(_export.surrogate_row(
                it, adapter.to_native(u_ghost)[0],
                mu=[float(mu_fake[0, j]) + 0.1 for j in range(M)],
                sigma=[float(sigma_fake)] * M,
                pred_tipo="valor", modelo_flag="GP-stub"))
            buf.add_pop(it, [sid])
            buf.add_timing(it, n_acumulado=n_train, tempo_fit_s=tempo_fit,
                           tempo_busca_s=tempo_busca)
            tempo_fit_total += tempo_fit
            tempo_busca_total += tempo_busca
            log.decision(caminho="infill",
                         motivo="stub: torch.rand sob manual_seed (L.10)",
                         it=it, torch_seed=seed_it, fe=bud.fe,
                         solution_id=sid)
            log.timing(n_acumulado=n_train, tempo_fit_s=tempo_fit, it=it)

            if it == 5:
                # (3a) cache-hit pela MESMA u (D89: des-normalização é
                # determinística ⇒ mesmo X nativo bit-a-bit ⇒ 0 FE).
                fe_antes = bud.fe
                adapter.evaluate_unit_max(u)
                cache_hit_zero_fe_unit = (bud.fe == fe_antes)
                # (3b) cache-hit por X NATIVA do DoE, re-avaliada direto.
                fe_antes = bud.fe
                adapter.evaluate_native(X0[0])
                cache_hit_zero_fe_native = (bud.fe == fe_antes)

            # D86: fim da iteração — solta os tensores e coleta.
            del u, u_ghost, mu_fake, sigma_fake, y_max
            iteration_cleanup()
    except _budget.BudgetExhausted:
        hard_stopped = True                               # D21/D61: fim limpo
    n_iters = it - 1                                      # a última não consumiu

    # cache-hit também é livre APÓS o esgotamento (D89).
    fe_antes = bud.fe
    adapter.evaluate_native(X0[0])
    cache_hit_post_exhaust = (bud.fe == fe_antes)

    # uma linha C3 (espaço transformado) + uma de classificador — exercita o
    # schema único C1/C3 da ③ (§17.2), como o STUB do F0-03/R1-00.
    buf.add_surrogate(_export.surrogate_row(
        n_iters, bud.records[0].x, mu=[0.1], pred_tipo="valor",
        modelo_flag="GP-stub", espaco_modelo="transformado",
        transf_tipo="minmax", transf_params={"min": 0.0, "max": 1.0}))
    buf.add_surrogate(_export.surrogate_row(
        n_iters, adapter.xu, pred_tipo="classe", pred_classe="bom",
        pred_confianca=0.83, modelo_flag="FNN-stub"))

    # prova N.1.3 (RNG global preservado em volta de um pymoo.minimize REAL).
    rng_guard_ok = _rng_guard_probe(adapter)
    # determinismo L.10/D91: re-materializar as sementes = mesmos valores.
    seed_det_ok = all(
        iteration_seed(semente, STUBPY_ALG_ID, k + 1, 0, bits32=True) == s
        for k, s in enumerate(seeds_used))

    timing_totais = {
        "tempo_total_s": round(time.time() - t0, 4),
        "tempo_fit_surrogate_s": round(tempo_fit_total, 4),
        "tempo_busca_s": round(tempo_busca_total, 4),
        "tempo_aval_real_s": round(adapter.tempo_aval_real_s, 4),
    }
    out = write_run_outputs(
        exp, alg, problema, semente, bud, buf, adapter=adapter,
        doe_hash_sidecar=doe_art["doe_hash"], env=env, pinning=pinning,
        n_geracoes=n_iters, algo_version="stubpy-R2-00",
        timing_totais=timing_totais, regime="online",
        data_root=data_root, enable_bucket=enable_bucket)

    log.footer(status="ok", fe_final=bud.fe, n_geracoes=n_iters,
               cache_hits=bud.cache_hits, cp_init=out["cp_init_ok"],
               rng_guard_ok=rng_guard_ok, sign_ok=sign_ok)

    return {
        "D": D, "M": M, "maxfe": bud.maxfe, "fe_final": bud.fe,
        "n_init": bud.n_init, "n_iters": n_iters,
        "cache_hits": bud.cache_hits,
        "cache_hit_zero_fe_unit": cache_hit_zero_fe_unit,
        "cache_hit_zero_fe_native": cache_hit_zero_fe_native,
        "cache_hit_post_exhaust": cache_hit_post_exhaust,
        "hard_stopped": hard_stopped,
        "sign_ok": sign_ok, "standardize_ok": standardize_ok,
        "rng_guard_ok": rng_guard_ok, "seed_det_ok": seed_det_ok,
        "seeds_used_head": seeds_used[:3],
        "pinning": pinning, "env": env,
        "doe_hash_run": out["doe_hash_run"],
        "doe_hash_sidecar": doe_art["doe_hash"],
        "cp_init_ok": out["cp_init_ok"],
        "upload_status": out["upload_status"],
        "timing_totais": timing_totais,
    }


__all__ = [
    "restart_de_linha",
    "D79_THREAD_VARS", "DEVICE", "STUBPY_ALG_ID",
    "pin_runtime", "env_info",
    "iteration_seed", "torch_seed_for",
    "preserve_global_rng", "preserve_torch_rng", "preserve_all_rng",
    "guarded_pymoo_minimize",
    "iteration_cleanup",
    "SONDA_K", "SONDA_CHUNK", "load_sonda", "sonda_due",
    "sonda_predict_gp", "emit_sonda_block", "di10_minimo_comum",
    "load_doe", "BoTorchProblemAdapter", "SnapshotBuffer",
    "write_run_outputs", "dual_write_run", "run_stubpy",
]
