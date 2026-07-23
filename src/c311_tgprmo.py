# -*- coding: utf-8 -*-
"""c311 TGPR-MO — runner OFFLINE do treed-GP escalável (autor · Python/DESDEO/GPy).

Molde: o `run_stubr3` de `standalone_harness` (encanamento OFFLINE ponta-a-ponta)
REUSADO à risca; o mecanismo do algoritmo (treed-GP) entra por **VENDOR INTOCADO +
GANCHOS EM RUNTIME** — o precedente OFICIAL do e81 (`vendor intocado + 3 ganchos`).
Nenhum arquivo de `algorithms/c311_TGPR-MO/**` é editado; toda instrumentação vive
AQUI, por monkeypatch instalado/desmontado por contextmanager.

═══════════════════════════════════════════════════════════════════════════
O FLUXO (I.17/L.17 · §22.4·3.3 · §11)
═══════════════════════════════════════════════════════════════════════════
OFFLINE puro: o **dataset É o orçamento** (D90). Carrega-se `ds_{prob}_{sem}.parquet`
(CP-init x_hash **E** f_hash) → o `FEBudget` nasce ESGOTADO (① = as 31D−1 do dataset)
→ constrói-se o treed-GP → RVEA final sobre o surrogate → o ND final é avaliado 1×
na verdade (⑦, fora do orçamento, DI-08). Qualquer FE REAL na busca é
`OfflineBudgetViolation` (pára-e-loga D81).

Duas fases, UM surrogate:
  1. **CONSTRUÇÃO** (`treedGP_build`): árvore de regressão (MSE, min_samples_leaf=10D,
     max_depth=100) por objetivo + laço RVEA `I_max = N/(10D)` (float→ceil) × `G_max=50`;
     a cada iteração a folha visitada de MAIOR impureza sem GP ganha 1 GP local
     (GPy Matérn 5/2 ARD, `optimize('bfgs')` ÚNICO). `_refresh_population` re-avalia
     tudo (+1 geração/iteração). Early-stop: `delta = total_points − seq[it−3]`, `it>5`.
  2. **FINAL** (`treedGP_final`): RVEA `10 × 100 = 1000` gerações sobre o surrogate FIXO.

═══════════════════════════════════════════════════════════════════════════
OS GANCHOS (o que a sessão acrescenta em runtime, e por quê)
═══════════════════════════════════════════════════════════════════════════
1. **σ das folhas** (`_patched_predict`) — 🟢 B15.5, extensão NOSSA. O `treeGP.predict`
   do autor devolve `(μ, None)`: o GPy JÁ computa a variância no `.predict()`, o código
   a DESCARTA. O gancho a EXPÕE — `σ = sqrt(max(var,0))` (σ, NUNCA σ² — DI-16.9), `NaN`
   nas folhas SÓ-árvore (sem GP, sem variância). μ fica BYTE-idêntico ao stock (mesma
   expressão `predict(...)[0][0]`, mesmo laço 1-ponto-por-linha). Como o RVEA seleciona
   por `selection_type="mean"` (`APD_Select._calculate_fitness` lê SÓ `pop.fitness`,
   NUNCA `pop.uncertainity`), expor σ **não pode** mover a busca — não-perturbação por
   CONSTRUÇÃO. O pipeline já converte None→NaN (`np.ndarray[:,c]=None → NaN`), então o
   patch "encaixa sem plumbing" (⟦v2.2⟧).
2. **`predict_batch`** (`_predict_batch`) — NOVO (DI-16.13), OBRIGATÓRIO p/ a sonda:
   o `predict` canônico é 1-ponto-por-linha (20.000 × M ≈ 40–60k chamadas GPy/bloco).
   O batch agrupa os pontos por FOLHA e chama cada GP UMA vez. NÃO é cópia do
   `predict_new` (é de OUTRA classe, `HybridTreeGP_v2`) — é reimplementação para o
   `treeGP`, devolvendo (μ, σ). Custo medido em `tempo_pred_sonda_s`.
3. **Instrumentação read-only** (`_Recorder` + wrappers de `_next_gen`/`_refresh_population`):
   captura a população SELECIONADA por geração (X, μ=`pop.objectives`, σ=`pop.uncertainity`)
   para a ③, com o **contador `geracao` ÚNICO e MONOTÔNICO** que atravessa as 2 fases
   (C311-11/DI-16.19) — build: `_current_gen_count` (inclui o +1 do refresh); final:
   `último_build + _current_gen_count`. Nenhum wrapper altera argumento ou retorno.

═══════════════════════════════════════════════════════════════════════════
CONTRATOS QUE ESTE RUNNER HONRA (e onde)
═══════════════════════════════════════════════════════════════════════════
- **2 blocos de sonda** (DI-16.12): `treedGP_build` (fim da construção) e `treedGP_final`
  (fim do run), AMBOS `geracao=NULL`, 20.000 linhas na ORDEM do artefato (join posicional).
  Construídos MANUALMENTE via `surrogate_row(None, …)` — o `emit_sonda_block` força
  `int(geracao)` e o `auditar.py` REPROVA sonda offline com geração não-nula.
- **② VAZIA por construção** (DI-16.17): a população do RVEA são candidatos gerados
  (SBX/PM) sobre o surrogate, nunca membros do dataset ⇒ `real_solution_id=NULL` na busca.
- **④ = 1 linha por RETREINO** (construção; C311-09 `fit_series` MULTI-linha) — o eixo da
  escalabilidade treed-GP; a fase final (sem retreino) e a sonda entram no agregado do
  manifesto. `tempo_geracao_s` EXCLUI a sonda (DI-13.10).
- **⑦ RECONSTITUÍVEL da ③**: a ⑦ nasce da `evf.population` = o ÚLTIMO bloco `treedGP_final`
  da ③ (`origem_geracao=última`, `origem_linha`=posição). TODOS os finais avaliados; ND
  filtrado DEPOIS da real (DI-13.9/B7.5).
- **VENV-only / não-co-importar** (D79/N.1.2): venv `env_c311` próprio; `desdeo_*` do c311
  isolado; b5 NUNCA no mesmo processo. `evaluate_population` NUNCA importado (dispara
  `matlab.engine`). `pygmo` AUSENTE do caminho framework/ (DI-16.14) — nenhum swap NDS.

⚠ **Fidelidade NÃO é julgada aqui (D97)** — o runner instrumenta e aplica o gate objetivo;
o julgamento é manual, do autor, a posteriori.
"""
from __future__ import annotations

import contextlib
import io
import math
import os
import random
import sys
import time
import types

# ── D79: 1 run = 1 core. Fixa os limites de thread do BLAS ANTES do numpy
#    (belt — efetivo na invocacao DIRETA `python -c "from src.c311_tgprmo ..."`,
#    onde este e o 1o import de numpy). O suspenders e o `threadpoolctl` em
#    runtime (`_threads_pinned`), robusto a ordem de import (ex.: a suite que
#    importa numpy antes). CRITICO p/ o determinismo: sem isto o BLAS multi-thread
#    injeta ruido de reducao ~1e-5 que 1000 geracoes de RVEA amplificam ⇒ ⑦ varia.
#    (O `pin_runtime` do harness NAO limita threads em env sem torch — so REGISTRA.)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

from src import export as _export
from src import naming
from src import standalone_harness as H
from src.budget import BudgetExhausted

# ── Identidade e constantes do config (Balde de parâmetros do cartão) ───────

#: `artifacts/seeds.json:alg_id.c311` — a 2ª coordenada da tupla do D62.
ALG_ID = 19

ALGO_VERSION = ("TGPR-MO-c311-r3 (vendor intocado; σ-export B15.5 + predict_batch "
                "DI-16.13 + geracao unico DI-16.19)")

#: Raiz do vendor c311 (contém desdeo_emo/, desdeo_problem/, framework/).
VENDOR_ROOT = os.path.join(H.ROOT, "algorithms", "c311_TGPR-MO")

#: §22.4·3.3 / §11 (números do paper, corroborados no código):
G_MAX_BUILD = 50            #: gerações por iteração da CONSTRUÇÃO (RVEA n_gen_per_iter)
N_ITER_FINAL = 10           #: iterações da FINAL (× n_gen_per_iter default 100 = 1000 ger)
#: min_samples_leaf = 10*D e max_depth=100 vivem no `treeGP.fit` vendorizado;
#: α=2 e selection_type="mean" são os DEFAULTS do RVEA (o run_treed_GP não os passa) —
#: reproduzimos a chamada do autor à risca (defaults ⇒ mean/α=2, o que a SPEC crava).


# ═══════════════════════════════════════════════════════════════════════════
#  Import do vendor — root-first + shim de dependência ausente (env pins intocados)
# ═══════════════════════════════════════════════════════════════════════════

def _import_vendor():
    """Importa os 3 tijolos do vendor c311 com resolução ROOT-first, sem tocar o env.

    - **optproblems** NÃO está no `env_c311` (o `desdeo_problem/__init__.py` o importa
      avidamente via `testproblems`, que o nosso caminho — `DataProblem` com dados
      injetados — NUNCA usa). Em vez de instalar um pacote não-autorizado (D80: os pins
      são do autor; só o pymoo foi pré-autorizado), injeta-se um STUB em `sys.modules`
      ANTES do import — o precedente do shim `pygmo`/`typing.Literal` do b5. `zdt.ZDT1`
      etc. só são tocados DENTRO de `test_problem_builder` (que não chamamos).
    - `pygmo` está AUSENTE do caminho RVEA→APD_Select_constraints→Population (DI-16.14
      verificado): nenhum shim necessário para o c311.
    - `sys.path.insert(0, VENDOR_ROOT)` resolve `desdeo_*` PARA A CÓPIA vendorizada
      (o `sys.path.insert('/home/amrzr/…')` hard-coded do autor é no-op no Mac).
    """
    if "optproblems" not in sys.modules:
        _opt = types.ModuleType("optproblems")
        _opt.zdt = types.ModuleType("optproblems.zdt")
        _opt.dtlz = types.ModuleType("optproblems.dtlz")
        sys.modules["optproblems"] = _opt
        sys.modules["optproblems.zdt"] = _opt.zdt
        sys.modules["optproblems.dtlz"] = _opt.dtlz
    if VENDOR_ROOT not in sys.path:
        sys.path.insert(0, VENDOR_ROOT)

    from desdeo_problem.Problem import DataProblem
    from desdeo_problem.surrogatemodels.surrogate_treedGP import treeGP
    from desdeo_emo.EAs.RVEA import RVEA
    from desdeo_emo.EAs.BaseEA import BaseDecompositionEA
    from desdeo_emo.population import CreateIndividuals

    # Prova ROOT-first (o hazard N.1.2: co-import com b5 usaria as classes ERRADAS).
    import desdeo_problem
    import desdeo_emo
    for mod in (desdeo_problem, desdeo_emo):
        p = os.path.abspath(mod.__file__)
        if not p.startswith(os.path.abspath(VENDOR_ROOT)):
            raise RuntimeError(
                f"root-first FALHOU: {mod.__name__} resolveu p/ {p} (esperado sob "
                f"{VENDOR_ROOT}). Co-import com o vendor do b5? Pára-e-loga (D81).")
    if "pygmo" in sys.modules:                       # DI-16.14: não deveria acontecer
        raise RuntimeError(
            "pygmo foi importado no caminho framework/ — contradiz a DI-16.14. "
            "Investigar antes de seguir. Pára-e-loga (D81).")
    return DataProblem, treeGP, RVEA, BaseDecompositionEA, CreateIndividuals


@contextlib.contextmanager
def _silencio():
    """Cala o `print` do vendor (RVEA/treeGP imprimem 'size pop:' etc.) — ruído que
    poluiria o stdout que o despachante parseia. Só stdout; o `.jsonl` é separado."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield


@contextlib.contextmanager
def _threads_pinned():
    """D79 em runtime: re-limita a 1 thread TODO BLAS já carregado (OpenBLAS/MKL/
    Accelerate/OpenMP), robusto à ordem de import. É o que torna o run DETERMINÍSTICO
    quando a invocação não veio pelo `run_in_venv` (env limpo). Se o `threadpoolctl`
    faltar, cai no belt (os env-vars do topo do módulo)."""
    try:
        import threadpoolctl
    except ImportError:                                   # pragma: no cover
        yield
        return
    with threadpoolctl.threadpool_limits(limits=1):
        yield


# ═══════════════════════════════════════════════════════════════════════════
#  Ganchos σ / predict_batch (monkeypatch do treeGP — vendor INTOCADO)
# ═══════════════════════════════════════════════════════════════════════════

def _predict_batch(model, X):
    """`predict_batch(X) -> (μ, σ)` de UM objetivo (um `treeGP`). VETORIZADO (DI-16.13).

    Agrupa os pontos por FOLHA e chama cada GP local UMA vez (à la `predict_new`, mas
    reimplementado p/ o `treeGP` — NÃO importa a classe irmã). μ = predição da árvore,
    sobreposta pelo μ do GP nas folhas com GP; σ = `sqrt(max(var,0))` nas folhas com GP,
    `NaN` nas folhas só-árvore (sem variância). B15.5/DI-16.9.
    """
    X = np.atleast_2d(np.asarray(X, dtype=np.float64))
    y_mean = np.asarray(model.regr.predict(X=X), dtype=np.float64).copy()
    y_std = np.full(X.shape[0], np.nan, dtype=np.float64)
    if model.error_leaves is not None:
        leaves = model.regr.apply(X)
        gp_leaves = np.intersect1d(leaves, np.atleast_1d(np.asarray(model.error_leaves)))
        for lf in gp_leaves:
            loc = np.where(leaves == lf)[0]
            mu, var = model.dict_gps[str(lf)].predict(X[loc])      # (k,1),(k,1)
            y_mean[loc] = np.asarray(mu, dtype=np.float64).reshape(-1)
            y_std[loc] = np.sqrt(np.maximum(
                np.asarray(var, dtype=np.float64).reshape(-1), 0.0))
    return y_mean, y_std


def _patched_predict(self, X):
    """Substituto de `treeGP.predict` que EXPÕE σ (o stock devolve `None`).

    μ é BYTE-idêntico ao stock: mesma árvore, mesmo laço 1-ponto-por-linha, mesma
    expressão `predict(...)[0][0]` — a única adição é ler `predict(...)[1][0][0]`
    (a variância que o GPy JÁ computou) da MESMA chamada. Custo idêntico ao stock
    (o 1-ponto-por-linha é o custo REAL do building, não o encurtamos na busca).
    """
    Y_predict = self.regr.predict(X=X)
    Y_test_leaf = self.regr.apply(X)
    Y_predict_mod = Y_predict
    y_std = np.full(np.shape(X)[0], np.nan, dtype=np.float64)
    if self.error_leaves is not None:
        for i in range(np.shape(X)[0]):
            if Y_test_leaf[i] in self.error_leaves:
                pred = self.dict_gps[str(Y_test_leaf[i])].predict(X[i].reshape(1, -1))
                Y_predict_mod[i] = pred[0][0]                          # EXATO stock (μ)
                y_std[i] = float(np.sqrt(max(float(pred[1][0][0]), 0.0)))   # σ (B15.5)
    y_mean = Y_predict_mod
    return (y_mean, y_std)


# ═══════════════════════════════════════════════════════════════════════════
#  Recorder — ③ por geração + contador ÚNICO C311-11 (via wrappers do RVEA)
# ═══════════════════════════════════════════════════════════════════════════

class _Recorder:
    """Captura a população selecionada por geração para a ③, com o `geracao` unificado.

    build: `geracao = _current_gen_count` (já inclui o +1/iteração do `_refresh_population`).
    final: `geracao = ultimo_build + _current_gen_count` (RVEA final é instância NOVA, cujo
    contador reinicia em 0 — sem o offset as ③ das 2 fases colidiriam em 1..50, DI-16.19).
    """

    def __init__(self, buf, *, D, M, fe_treino_max):
        self.buf = buf
        self.D = D
        self.M = M
        self.fe_treino_max = int(fe_treino_max)
        self.offset = 0
        self.flag = "treedGP_build"
        self.max_geracao = 0

    def start_final(self, ultimo_build_gen):
        self.offset = int(ultimo_build_gen)
        self.flag = "treedGP_final"

    def capture(self, evolver):
        g = self.offset + int(evolver._current_gen_count)
        self.max_geracao = max(self.max_geracao, g)
        pop = evolver.population
        Xg = np.asarray(pop.individuals, dtype=np.float64)
        MU = np.asarray(pop.objectives, dtype=np.float64)
        SG = pop.uncertainity
        SG = (np.full_like(MU, np.nan) if SG is None
              else np.asarray(SG, dtype=np.float64))
        for i in range(Xg.shape[0]):
            # ② VAZIA por construção (DI-16.17): candidatos gerados ≠ dataset ⇒
            # real_solution_id=NULL na busca (declarado no sigma_dict; sem lookup).
            self.buf.add_surrogate(_export.surrogate_row(
                g, Xg[i], regime="offline", real_solution_id=None,
                mu=MU[i], sigma=SG[i], pred_tipo="valor",
                modelo_flag=self.flag, espaco_modelo="cru",
                fe_treino_max=self.fe_treino_max))


def _lhs_determinismo(CI):
    """GANCHO 4 (DETERMINISMO) — semeia o `lhs` da população inicial do RVEA.

    ⚠ DRIFT DE PROVISIONAMENTO: o `env_c311` resolveu um **pyDOE NOVO** (o pip do
    PROVISIONAMENTO §3 instala `pyDOE` SEM pin). Nesse pyDOE, `lhs(..., seed=None)`
    usa um `RandomState` PRÓPRIO (entropia do SO) — NÃO o `np.random` global. Prova
    (diag): o estado global fica IDÊNTICO após `RVEA.__init__`, mas a pop inicial
    (design 'LHSDesign', Population.py:116) VARIA ⇒ o run é NÃO-determinístico, o que
    reprova o gate de determinismo (D79/§22.6). A receita L.17 assumia o pyDOE ANTIGO
    (lhs pelo global). Correção mínima e vendor-intocada: injeta `seed=` derivado do
    `np.random` global (que ESTE runner semeia por iteration_seed) ⇒ o lhs volta a ser
    determinístico e atado à semente do run. [A torre DEVE levantar com o autor: pinar
    o pyDOE, OU ratificar este gancho — a init-pop LHS difere de um pyDOE antigo, mas é
    um LHS válido e reprodutível da semente; fidelidade é D97, do autor.]
    """
    orig = CI.lhs

    def _lhs(*args, **kw):
        if "seed" not in kw and "random_state" not in kw:
            kw["seed"] = int(np.random.randint(0, 2 ** 31 - 1))
        return orig(*args, **kw)

    return orig, _lhs


@contextlib.contextmanager
def _hooks(treeGP, RVEA, BaseDecompositionEA, CreateIndividuals, recorder):
    """Instala os ganchos (σ, predict_batch, snapshot, lhs-determinismo) e os DESMONTA.

    `_next_gen` mora em `BaseDecompositionEA` (definidor); `_refresh_population` em `RVEA`;
    `lhs` no namespace de `CreateIndividuals`. Restaura tudo no `finally` — vendor bit-a-bit.
    """
    orig_predict = treeGP.predict
    orig_next_gen = BaseDecompositionEA._next_gen
    orig_refresh = RVEA._refresh_population
    orig_lhs, hooked_lhs = _lhs_determinismo(CreateIndividuals)

    def _hooked_next_gen(self, *a, **k):
        r = orig_next_gen(self, *a, **k)
        recorder.capture(self)
        return r

    def _hooked_refresh(self, *a, **k):
        r = orig_refresh(self, *a, **k)
        recorder.capture(self)
        return r

    treeGP.predict = _patched_predict
    treeGP.predict_batch = _predict_batch
    BaseDecompositionEA._next_gen = _hooked_next_gen
    RVEA._refresh_population = _hooked_refresh
    CreateIndividuals.lhs = hooked_lhs
    try:
        yield
    finally:
        treeGP.predict = orig_predict
        if hasattr(treeGP, "predict_batch"):
            delattr(treeGP, "predict_batch")
        BaseDecompositionEA._next_gen = orig_next_gen
        RVEA._refresh_population = orig_refresh
        CreateIndividuals.lhs = orig_lhs


# ═══════════════════════════════════════════════════════════════════════════
#  Sonda OFFLINE (2 blocos, DI-16.12) — construída à mão (geracao=NULL)
# ═══════════════════════════════════════════════════════════════════════════

def _sonda_predict(models):
    """`predict(X) -> (μ, σ)` (S, M) do treed-GP inteiro (empilha os M objetivos)."""
    def f(X):
        mus, sgs = [], []
        for m in models:
            mu, sg = _predict_batch(m, X)
            mus.append(mu)
            sgs.append(sg)
        return np.column_stack(mus), np.column_stack(sgs)
    return f


def _emit_sonda_offline(buf, log, sonda, *, modelo_flag, predict, fe_treino_max,
                        fe):
    """Emite UM bloco de sonda OFFLINE: S linhas `regime='sonda'`, `geracao=NULL`.

    NÃO usa `H.emit_sonda_block` (que força `int(geracao)` e cravaria uma geração — o
    `auditar.py` REPROVA sonda offline com geração não-nula, DI-16.12). Constrói as linhas
    via `surrogate_row(None, …)`. Roda sob `preserve_all_rng()`: a predição da sonda NÃO
    pode mover a busca (invariante §3.1) — mesmo determinística, o save/restore é o cinto.
    Retorna `tempo_pred_sonda_s`.
    """
    X = sonda["X"]
    t0 = time.time()
    with H.preserve_all_rng():
        MU, SG = predict(X)
    MU = np.asarray(MU, dtype=np.float64)
    SG = np.asarray(SG, dtype=np.float64)
    if MU.shape[0] != X.shape[0] or MU.shape[0] != SG.shape[0]:
        raise RuntimeError(
            f"sonda {modelo_flag}: predict devolveu {MU.shape[0]}×σ{SG.shape[0]} p/ "
            f"{X.shape[0]} pontos — ORDEM/cardinalidade do artefato (join posicional, "
            f"R4 regra 5) quebrada. Pára-e-loga (D81).")
    for i in range(X.shape[0]):
        buf.add_surrogate(_export.surrogate_row(
            None, X[i], regime="sonda", real_solution_id=None,
            mu=MU[i], sigma=SG[i], pred_tipo="valor",
            modelo_flag=modelo_flag, espaco_modelo="cru",
            fe_treino_max=int(fe_treino_max)))
    dt = time.time() - t0
    log.event("sonda", modelo_flag=modelo_flag, geracao=None, fe=int(fe),
              n_pontos=int(X.shape[0]), tempo_pred_sonda_s=round(dt, 4),
              fe_treino_max=int(fe_treino_max),
              sonda_x_hash=sonda["x_hash"], sonda_f_hash=sonda["f_hash"],
              hash_check="ok (conferido no arranque — load_sonda)",
              motivo="offline: 1 bloco por modelo treinado (2 blocos, DI-16.12)")
    return dt


# ═══════════════════════════════════════════════════════════════════════════
#  build_surrogates — reimplementação do vendor (o vendor FICA intocado)
# ═══════════════════════════════════════════════════════════════════════════

def _build_surrogates(DataProblem, treeGP, X, F, x_low, x_high):
    """Idêntico a `framework/treedGP_framework.py:build_surrogates` (fidelidade).

    Constrói o `DataProblem` a partir dos dados injetados e treina UMA `treeGP` por
    objetivo (só a ÁRVORE; os GPs entram no laço de construção). Reproduzido aqui para
    o vendor não ser tocado e para instrumentarmos o laço (os archives do building são
    descartados no caminho 2-fases — L.17).
    """
    import pandas as pd
    nvars, nobjs = X.shape[1], F.shape[1]
    x_names = [f"x{i}" for i in range(1, nvars + 1)]
    y_names = [f"f{i}" for i in range(1, nobjs + 1)]
    data = pd.DataFrame(np.hstack((X, F)), columns=x_names + y_names)
    bounds = pd.DataFrame(np.vstack((x_low, x_high)), columns=x_names,
                          index=["lower_bound", "upper_bound"])
    problem = DataProblem(data=data, variable_names=x_names,
                          objective_names=y_names, bounds=bounds)
    problem.train(treeGP, model_parameters={"min_samples_leaf": 10 * nvars})
    return problem


# ═══════════════════════════════════════════════════════════════════════════
#  O runner
# ═══════════════════════════════════════════════════════════════════════════

def run_c311(exp: str, alg: str, problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             teto_s: float | None = None,
             q: int = 1,
             emitir_sonda: bool = True,
             **_kwargs) -> dict:
    """Roda o TGPR-MO OFFLINE sob o contrato v5.2.1. Assinatura padrão dos runners R3.

    `teto_s` = teto de wall-clock (o O(n³) do GPy em n grande sob Rosetta é o gargalo);
    ao estourar durante a construção: aborto LIMPO → `write_run_outputs(status='failed',
    motivo_parada='teto_wall')` (aborto por teto = DADO, não exceção). None = sem teto
    (o default dos pilotos small, que fecham em minutos).

    `emitir_sonda=False` DESLIGA os 2 blocos de sonda — usado SÓ pela prova de
    não-perturbação (§3.1): a ⑦ e a ③-busca têm de sair BIT-idênticas com a sonda
    ligada ou desligada (a sonda roda FORA da busca, sob `preserve_all_rng`).
    """
    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)

    (DataProblem, treeGP, RVEA, BaseDecompositionEA,
     CreateIndividuals) = _import_vendor()

    # ── ① = o DATASET (D90): o orçamento nasce ESGOTADO; CP x_hash E f_hash ──────
    bud, ds = H.load_offline_budget(problema, semente, data_root=data_root)
    D, M, n_ds = ds["D"], ds["M"], ds["n"]
    x_low, x_high = (np.asarray(b, dtype=np.float64) for b in H._bounds(problema))
    fe_treino_max = n_ds - 1                       # DI-09/A1: constante no offline

    sonda = H.load_sonda(problema, regime="offline", data_root=data_root)
    buf = H.SnapshotBuffer()
    buf.set_fe_treino_max(fe_treino_max)
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)

    params = {
        "receita": "run_treed_GP(X,F,x_low,x_high) [2 fases] + RVEA(n_iterations=10) final",
        "min_samples_leaf": 10 * D, "max_depth": 100,
        "G_max_build": G_MAX_BUILD, "I_max": "N/(10D) (float→ceil via continue_evolution)",
        "n_iter_final": N_ITER_FINAL, "n_gen_final": 100, "n_gen_total_final": 1000,
        "kernel": "GPy Matern52 ARD; sem White/normalizer/priors; optimize('bfgs') unico",
        "selection_type": "mean", "alpha": 2, "early_stop": "delta=total_pts-seq[it-3], it>5",
        "sigma": "sqrt(var_GPy) exposto (B15.5); NaN nas folhas sem GP (DI-16.9)",
    }
    sigma_dict = {
        "modelo": ("TGPR-MO (treed-GP): arvore de regressao MSE (min_samples_leaf=10D, "
                   "max_depth=100) por objetivo + GP local (GPy Matern52 ARD, bfgs unico) "
                   "na folha de maior impureza; predicao = mu da arvore, sobreposta pelo "
                   "mu do GP nas folhas com GP."),
        "regime": ("offline = candidatos da busca RVEA sobre o surrogate (2 fases); "
                   "sonda = a regua fixa §17.2.2."),
        "modelo_flag": ("treedGP_build = construcao (arvore+GPs crescendo); treedGP_final "
                        "= otimizacao final 10x100 ger (o MESMO surrogate, agora fixo). O "
                        "contador `geracao` e UNICO e monotonico atravessando as 2 fases "
                        "(C311-11/DI-16.19); a fase le-se no modelo_flag."),
        "mu_*": ("mu por objetivo em f de MINIMIZACAO, espaco NATIVO (treed-GP treina em Y "
                 "cru — sem normalizer/z-score; DI-16.9: nada a des-padronizar)."),
        "sigma_*": ("sigma = sqrt(var_GPy) por objetivo — extensao NOSSA (B15.5; o paper "
                    "anuncia e nunca consome; o codigo descartava). sigma, NUNCA sigma^2 "
                    "(DI-16.9). NaN nas folhas SEM GP (predicao so-arvore nao tem variancia) "
                    "— semantica POR-REGIAO, nao por-run."),
        "espaco_modelo": "cru (nativo); transf_* = NULL (sem transformacao).",
        "sonda": ("2 blocos de 20.000 (treedGP_build @fim da construcao; treedGP_final "
                  "@fim do run), geracao=NULL (DI-16.12), ordem do artefato POR POSICAO. "
                  "predict_batch NOVO (DI-16.13) vetoriza a predicao."),
        "pop_2_vazia": ("② SAI VAZIA por construcao (DI-16.17): a populacao do RVEA sao "
                        "candidatos gerados (SBX/PM) sobre o surrogate, nunca membros do "
                        "dataset ⇒ real_solution_id=NULL na busca. O gate NAO deve exigir "
                        "② nao-vazia."),
        "fe_treino_max": (f"constante {fe_treino_max} — o dataset E o orcamento (D90); o "
                          f"modelo ve as {n_ds} linhas 1x; offline nao retreina em FE reais."),
        "timing_4": ("④ = 1 linha por iteracao de CONSTRUCAO (retreino: cada addGPs; "
                     "C311-09 fit_series MULTI-linha, o eixo da escalabilidade treed-GP). "
                     "A fase final (sem retreino) e as 2 sondas entram no agregado do "
                     "manifesto; tempo_geracao_s EXCLUI a sonda (DI-13.10)."),
        "abertas_torre": ("TODAS RATIFICADAS pelo autor (DI-28, 2026-07-23): (a) uso_id "
                          "do c311 = _default/0 (mesmo s p/ numpy e random) RATIFICADO; "
                          "(b) ④ por retreino de construcao RATIFICADA; (c) contagem de "
                          "building inclui o +1/it do _refresh_population (=51/it via "
                          "_current_gen_count) CONFIRMADA. Gancho lhs = DEFINITIVO "
                          "(DI-28.3, sem re-pin do pyDOE)."),
    }

    status, motivo_parada = "ok", None
    pop_final = None
    n_nd = 0
    t_fit_total = t_busca_total = t_sonda_total = 0.0

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="offline", maxfe=bud.maxfe,
                   n_dataset=n_ds, doe_hash=ds["x_hash"], f_hash=ds["f_hash"],
                   dataset_hash=ds.get("dataset_hash"),
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"], params=params,
                   emitir_sonda=bool(emitir_sonda))

        # ── RNG global (L.17): numpy (pyDOE/SBX/PM/sklearn-tree) + stdlib (shuffle) ──
        # uso_id=0 (default): c311 nao tem RNG concorrente do harness; np.random e random
        # recebem o MESMO s (a receita literal da L.17). [uso_id em aberto p/ a torre]
        s = H.iteration_seed(H.seed_base(alg, semente), ALG_ID, 0, 0, bits32=True)
        np.random.seed(s)
        random.seed(s)

        recorder = _Recorder(buf, D=D, M=M, fe_treino_max=fe_treino_max)

        with _threads_pinned(), \
                _hooks(treeGP, RVEA, BaseDecompositionEA, CreateIndividuals,
                       recorder), \
                H.offline_guard(log, alg=alg, problema=problema):
            # ══ FASE 1 — CONSTRUCAO (treedGP_build) ══════════════════════════════
            t0 = time.time()
            with _silencio():
                problem = _build_surrogates(DataProblem, treeGP,
                                            ds["X"], ds["F"], x_low, x_high)
            t_fit_tree = time.time() - t0             # custo da(s) arvore(s)
            models = [problem.objectives[i]._model for i in range(M)]

            I_max = n_ds / (10.0 * D)                 # FLOAT (vendor); ceil via continue
            with _silencio():
                evolver = RVEA(problem, use_surrogates=True,
                               n_iterations=I_max, n_gen_per_iter=G_MAX_BUILD)

            total_points_all = 0
            total_points_all_sequence = []
            n_iter_build = 0
            while evolver.continue_evolution():
                if teto_s is not None and (time.time() - t_run) > teto_s:
                    raise _TetoWall()
                t_it0 = time.time()
                with _silencio():
                    evolver.iterate()                  # G_max geracoes (hook captura cada)
                t_busca_it = time.time() - t_it0
                Xs = evolver.population.individuals
                t_fit0 = time.time()
                try:
                    for i in range(M):
                        models[i].addGPs(Xs)           # GPy bfgs SEM try no stock
                        total_points_all += models[i].total_point_gps
                except np.linalg.LinAlgError as exc:   # jitchol falhou (~5 jitters)
                    log.guard("gpy_bfgs_linalg",
                              detalhe=("LinAlgError no addGPs (covariancia nao-PD; o dedup "
                                       "do dataset ja e garantido por load_offline_budget). "
                                       "O stock nao tem try — LinAlgError mata a run."),
                              iteracao=n_iter_build + 1, erro=str(exc))
                    raise
                t_fit_it = (time.time() - t_fit0) + (t_fit_tree if n_iter_build == 0 else 0.0)
                total_points_all_sequence = np.append(total_points_all_sequence,
                                                      total_points_all)
                if evolver._iteration_counter > 5:     # early-stop (>5) — L.17
                    delta = total_points_all - total_points_all_sequence[
                        evolver._iteration_counter - 3]
                else:
                    delta = 1
                with _silencio():
                    evolver._refresh_population()       # +1 geracao (hook captura)
                n_iter_build += 1
                g_it = int(evolver._current_gen_count)
                n_acum = int(sum(m.total_point for m in models))
                # ④ — 1 linha por RETREINO (C311-09 fit_series MULTI-linha)
                buf.add_timing(geracao=g_it, n_acumulado=n_acum, tempo_fit_s=t_fit_it)
                buf.update_timing(g_it, tempo_busca_s=t_busca_it,
                                  tempo_pred_sonda_s=0.0,
                                  tempo_geracao_s=t_fit_it + t_busca_it)
                t_fit_total += t_fit_it
                t_busca_total += t_busca_it
                log.decision(
                    caminho="c311_build",
                    motivo="construcao treed-GP: +GP na folha de maior impureza",
                    geracao=g_it, iteracao=n_iter_build,
                    n_gps=[len(m.dict_gps) for m in models],
                    n_acumulado=n_acum,
                    n_folhas=[int(m.regr.get_n_leaves()) for m in models],
                    profundidade=[int(m.regr.get_depth()) for m in models],
                    total_points_per_model=[float(m.total_point) for m in models],
                    delta_total_point=float(delta), early_stop=bool(delta <= 0),
                    **H.minimo_comum_di10(evolver.population.objectives, fe=bud.fe,
                                          tempo_fit_s=t_fit_it, tempo_busca_s=t_busca_it))
                if delta <= 0:
                    break
            build_gen_final = int(evolver._current_gen_count)
            H.iteration_cleanup()

            # ── SONDA 1: treedGP_build (fim da construcao) ──────────────────────
            spred = _sonda_predict(models)
            if emitir_sonda:
                t_sb = _emit_sonda_offline(buf, log, sonda, modelo_flag="treedGP_build",
                                           predict=spred, fe_treino_max=fe_treino_max,
                                           fe=bud.fe)
                t_sonda_total += t_sb
                buf.update_timing(build_gen_final, tempo_pred_sonda_s=t_sb)

            # ══ FASE 2 — FINAL (treedGP_final): RVEA 10x100 sobre o surrogate fixo ══
            recorder.start_final(build_gen_final)
            with _silencio():
                evf = RVEA(problem, use_surrogates=True, n_iterations=N_ITER_FINAL)
            t_f0 = time.time()
            with _silencio():
                while evf.continue_evolution():
                    if teto_s is not None and (time.time() - t_run) > teto_s:
                        raise _TetoWall()
                    evf.iterate()                       # 100 geracoes (hook captura cada)
                    H.iteration_cleanup()
            t_final_busca = time.time() - t_f0
            t_busca_total += t_final_busca
            final_gen_last = build_gen_final + int(evf._current_gen_count)
            pop_final = np.ascontiguousarray(evf.population.individuals, dtype=np.float64)

            # ── SONDA 2: treedGP_final (fim do run). O surrogate NAO muda na fase
            #    final (RVEA read-only, sem addGPs) ⇒ o modelo e o MESMO da SONDA 1;
            #    os 2 blocos saem identicos por construcao (invariante util p/ a R4).
            #    Emitimos os DOIS mesmo assim — o contrato (DI-16.12) crava 2 blocos.
            if emitir_sonda:
                t_sf = _emit_sonda_offline(buf, log, sonda, modelo_flag="treedGP_final",
                                           predict=spred, fe_treino_max=fe_treino_max,
                                           fe=bud.fe)
                t_sonda_total += t_sf

        # ── ⑦ __final: TODOS os finais avaliados 1x na verdade; ND filtrado DEPOIS ──
        from src import problems as _problems
        F_final = np.ascontiguousarray(
            _problems.evaluate_problem(H._instantiate(problema), pop_final),
            dtype=np.float64)
        # [DI-27/A15] `nd_pos_real`: NAO passar — o `write_final` o calcula sobre a
        # vista FLOAT32 que a ⑦ PERSISTE (a mesma que o `final_eval --check` re-le).
        # Calcula-lo no float64 CRU cria assimetria float32/float64 em empates de
        # borda (o b5 mediu b5m/ZDT1: 20 vs 19) e reprovaria uma ⑦ correta (o
        # anti-padrao que a docstring do write_final proibe). Molde: b5_prob.py.
        H.write_final(
            exp, alg, problema, semente, pop_final, F_final,
            origem_solution_id=[bud.solution_id_of(x) for x in pop_final],
            origem_geracao=[final_gen_last] * pop_final.shape[0],
            origem_linha=np.arange(pop_final.shape[0]),
            origem_camada="surrogate (③), ultima geracao treedGP_final",
            data_root=data_root)
        # footer/retorno: conta o ND sobre a MESMA vista float32 da ⑦ (consistente
        # com a coluna nd_pos_real gravada e com o --check).
        nd_idx = set(int(i) for i in _problems._nds_filter(
            F_final.astype(np.float32).astype(np.float64)))
        n_nd = len(nd_idx)

    except H.OfflineBudgetViolation:
        # o offline_guard ja gravou guard+footer(failed) e re-levantou: uma avaliacao
        # REAL na busca e desenho ERRADO (nao termino) — para-e-loga HARD (D81), sem
        # gravar as 4 camadas de um run invalido.
        log.close()
        raise
    except _TetoWall:
        status, motivo_parada = "failed", "teto_wall"
        log.guard("teto_wall", detalhe=(
            f"wall {time.time() - t_run:.1f}s > teto_s={teto_s}. Aborto LIMPO: as camadas "
            f"parciais ficam gravadas; a ⑦ NAO sai (sem populacao final valida). "
            f"Aborto por teto = DADO (D61/§22.5)."))
    except np.linalg.LinAlgError:
        # jitchol do GPy nao fechou (~5 jitters) no addGPs — o guard ja foi logado no
        # laco. Para-e-loga com manifesto HONESTO (status=failed), camadas parciais.
        status, motivo_parada = "failed", "gpy_bfgs_linalg"
    except Exception as exc:                                   # noqa: BLE001 — D81
        # Qualquer outra falha: NUNCA silenciosa (D23/D60/D81) — loga + manifesto failed.
        status, motivo_parada = "failed", f"erro_{type(exc).__name__}"
        log.guard("erro_inesperado", detalhe=repr(exc))

    # n_geracoes = a maior geracao da ③-busca (o topo do contador unico C311-11)
    n_geracoes = _max_busca_geracao(buf)

    timing_totais = _export.manifest_timing_block(
        tempo_total_s=time.time() - t_run, tempo_fit_surrogate_s=t_fit_total,
        tempo_busca_s=t_busca_total, tempo_aval_real_s=0.0,
        tempo_pred_sonda_s=t_sonda_total)

    res = H.write_run_outputs(
        exp, alg, problema, semente, bud, buf, D=D, M=M,
        cp_hashes={"x_hash": ds["x_hash"], "f_hash": ds["f_hash"]},
        env=env, pinning=pinning, n_geracoes=n_geracoes,
        algo_version=ALGO_VERSION, timing_totais=timing_totais,
        sigma_dict=sigma_dict, regime="offline", params=params,
        sonda_info=({"S": sonda["S"], "cadencia": "offline: 2 blocos (build+final)",
                     "n_blocos": (2 if emitir_sonda else 0),
                     "modelo_flags": ["treedGP_build", "treedGP_final"],
                     "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]}
                    if emitir_sonda else
                    {"S": sonda["S"], "cadencia": "DESLIGADA (prova nao-perturbacao)",
                     "n_blocos": 0}),
        status=status, motivo_parada=motivo_parada, q=int(q),
        data_root=data_root, enable_bucket=enable_bucket)

    log.footer(status=status, motivo=motivo_parada, fe_final=bud.fe, cp_init=True,
               cache_hits=bud.cache_hits, n_geracoes=n_geracoes,
               n_final=(0 if pop_final is None else int(pop_final.shape[0])),
               n_nd_pos_real=n_nd)
    log.close()

    return {
        "status": status, "motivo_parada": motivo_parada,
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_dataset": n_ds,
        "cp_init_ok": bool(res["cp_init_ok"]), "n_geracoes": n_geracoes,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows),
        "n_sonda_blocos": (2 if emitir_sonda else 0),
        "n_final": (0 if pop_final is None else int(pop_final.shape[0])),
        "n_nd_pos_real": n_nd, "regime": "offline", "cache_hits": bud.cache_hits,
        "tempo_pred_sonda_s": t_sonda_total, "emitir_sonda": bool(emitir_sonda),
    }


class _TetoWall(RuntimeError):
    """Sinaliza estouro do teto de wall-clock — aborto LIMPO (DADO, não exceção)."""


def _max_busca_geracao(buf) -> int:
    """A maior `geracao` das linhas de BUSCA da ③ (regime='offline') = n_geracoes."""
    gs = [int(r["geracao"]) for r in buf.surr_rows
          if r.get("regime") == "offline" and r.get("geracao") is not None]
    return max(gs) if gs else 0
