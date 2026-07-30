"""e81 — qPOTS (q-Pareto Optimal Thompson Sampling), ONLINE, sobre o
`standalone_harness` (R3-00). Cartão **R3-e81** · SPEC §22.4·3.5 · I.12/L.12/
E.6/M.9/N.2.2.

═══════════════════════════════════════════════════════════════════════════
O QUE ESTE MÓDULO É
═══════════════════════════════════════════════════════════════════════════
Um **driver instrumentado** sobre o repo vendorizado `algorithms/e81_qPOTS/`
(pacote `qpots` v2.0.1, content-hash `d2fa63a4…` em `artifacts/repos.lock`).
O miolo do algoritmo — `ModelObject.fit_gp()`, `Acquisition.qpots()`,
`select_candidates()` — roda **STOCK, sem fork**: a árvore vendorizada NÃO é
tocada (precedente c122/c149; o `repos.lock` continua válido). Tudo o que a
sessão acrescenta entra por três ganchos de escopo limitado, montados e
desmontados por contextmanager (`_matern_patch`, `_instrumentacao`).

**Receita canônica — README/ablation, NUNCA a dos `examples/`** (§22.4·3.5).
Por iteração: recriar `ModelObject(train_x, train_y, B01, nobj=M, ncons=0)` →
`fit_gp()` → recriar `Acquisition(func, gps, q=q)` →
`acq.qpots(bounds=B01, iteration=i, nystrom=0, dim=D, ngen=10, q=q)`.
Os `examples/unconstrained_branin.py` têm o **bug do `Acquisition` stale**
(constroem a `Acquisition` UMA vez, fora do laço ⇒ `self.gps` congela no GP
inicial para sempre). Há ainda uma segunda razão, medida nesta sessão, para
recriar o `ModelObject`: `fit_gp()` faz `self.models.append(...)` e o `__init__`
é o ÚNICO ponto que zera a lista — dois `fit_gp()` no mesmo objeto deixam
`len(models) == 2·M` e a `Acquisition` passa a amostrar do modelo errado.

═══════════════════════════════════════════════════════════════════════════
OS TRÊS GANCHOS (o que a sessão acrescenta, e por quê)
═══════════════════════════════════════════════════════════════════════════
1. **Matérn 5/2 ARD** — `_matern_patch` (🔵 ARTIGO · D30/DEF-B17.8; âncora
   `e81-matern`, `model_object.py:120`, conferida bit-a-bit nesta sessão).
   O paper usa Matérn 5/2 ARD; o código usa o **RBF ARD default** do BoTorch
   0.16.1 porque simplesmente não passa `covar_module=`. A correção é *uma
   linha*, e é aplicada interceptando `SingleTaskGP` **no namespace do módulo
   `qpots.model_object`** — assim o `fit_gp()` executado é o STOCK, byte a
   byte, e o diff efetivo é exatamente o `covar_module=` que a âncora pede.
   (Um fork do `fit_gp` seria 15 linhas copiadas com 1 alterada: mais
   superfície para divergir, menos auditável.)
   O kernel injetado é `get_matern_kernel_with_gamma_prior(D)` — **o mesmo
   helper que c262 e c154 já usam para esta MESMA decisão**, que o bundle
   marca "Compartilhado (c262, e81)". Ver o docstring de `_matern_patch`
   para o porquê (e para o efeito colateral medido no ZDT1).

2. **Offset D22/DEF-A6 nas sementes hard-coded** — `_instrumentacao`.
   `artifacts/seeds.json:offset_D22_hardcoded.e81` lista **exatamente dois**
   sítios, ambos conferidos nesta sessão:
     - `acquisition.py:219` → `torch.manual_seed(1024 + seed_iter)`
     - `acquisition.py:366` → `nsga2(..., seed=2430)`
   Aplicados sem tocar o vendor: (a) o wrapper de `_gp_posterior` **desloca o
   próprio `seed_iter`** (`seed_iter + 1000·s`) — como `seed_iter` alimenta
   NADA além do `manual_seed`, deslocá-lo é idêntico a offsetar a semente, e
   deixa o corpo stock intacto; (b) o wrapper de `nsga2` soma `1000·s` ao
   `seed` recebido. O terceiro seed do repo — `select_candidates(..., seed=2043)`
   — **NÃO** está na lista do artefato e **NÃO** é offsetado (a SPEC o
   classifica como "quase inócuo": é um reset pós-seleção).

3. **Instrumentação read-only** (§17.1/§17.5 · critério DI-12.1/DI-21: expor
   valor já computado é permitido; custo novo em hot-loop ou mudança de decisão
   não é). Wrappers de `_gp_posterior` (resumo dos draws de Thompson),
   `select_candidates` (front + índice escolhido) e `nsga2` (a `res` do pymoo,
   que o `qpots()` não devolve — é a população final da aquisição, DEF-C2).
   Nenhum deles altera argumento ou retorno; o único cálculo novo é o resumo
   estatístico dos draws e a distância maximin do escolhido, ambos fora da
   decisão.

═══════════════════════════════════════════════════════════════════════════
CONTRATOS QUE ESTE RUNNER HONRA (e onde)
═══════════════════════════════════════════════════════════════════════════
- **bounds = [0,1]^D em TODA parte** (§22.4·3.5, OBRIGATÓRIO). O `qpots()`
  monta o `PyMooFunction` com `xl/xu = bounds`, e o `_gp_posterior` faz
  `normalize(x, gps.bounds)`; o `select_candidates` compara `res.X` com
  `gps.train_x` por `cdist`. Se os dois espaços divergirem, o maximin mistura
  nativo × normalizado — o bug que a SPEC manda matar. Passando `B01` ao
  `ModelObject` **e** ao `qpots()`, `normalize` vira identidade e os três
  espaços coincidem. A desnormalização para o espaço NATIVO acontece só no
  `_Oracle` (L.14), na fronteira com o `FEBudget`.
- **`train_y = −f`** (E.6): o repo MAXIMIZA (`_gp_posterior` devolve `−Ys`).
  Com `train_y = −f`, o NSGA-II interno minimiza `f` — sem dupla negação.
- **`FEBudget` = fonte ÚNICA do orçamento (D89)**: o `_Oracle` só desnormaliza
  e delega; contagem, dedup-por-X bit-a-bit e hard-stop `31D−1` vivem lá.
- **cache-hit × dataset crescente (DI-21, regra RATIFICADA)**: o treino sai de
  `bud.records`, que **não cresce** num cache-hit ⇒ o hazard c122 §5.3 morre
  por construção. A ③ continua gravada (a predição FOI decisão-relevante) com
  o `real_solution_id` da solução preexistente; cap para hits consecutivos.
- **float64 FORÇADO** (N.2.2 + N.1.1 generalizada/DI-21): o `DEFAULT_DTYPE =
  torch.float64` do `qpots/config.py` é só uma constante de módulo — o repo
  **nunca** chama `torch.set_default_dtype`, então o default do processo segue
  float32 (medido nesta sessão). O runner força o default E passa
  `dtype=torch.float64` explícito ao `ModelObject`/`Acquisition`, e registra o
  dtype efetivo no manifesto.
- **Sonda** (§17.2.2/DI-13.5): 2000 pontos do artefato, cadência NORMATIVA
  `g==1 OU mod(g,k)==0` + a última via `BudgetExhausted`, ordem do artefato
  preservada, `fe_treino_max` preenchido, RNG salvo/restaurado. As colunas
  DEF-C3 entram pelo kwarg `c3=` do `emit_sonda_block` (DI-23/§3.4) — e
  `transf_params` vai como **dict**, não string: o helper repassa `**c3` ao
  `surrogate_row`, que serializa (uma string ali sairia com duplo-encode).
- **④ por iteração** (§17.6): `n_acumulado` = o TREINO; `tempo_geracao_s`
  EXCLUI a sonda. A linha da ④ é **fechada em `finally`**, antes de qualquer
  `break` — sem isso, um aborto (teto/cache-cap) deixaria a última geração com
  os 3 tempos NULL e reprovaria o próprio gate (defeito observado no molde
  c149, §achados do handoff).
- **Custo O(n³) é o DADO** (§17.6/N.2.2): importar BoTorch eleva
  `max_cholesky_size` a 4096 ⇒ Cholesky EXATO em todo o regime (n ≤ 929).
  A curva `(n_acumulado, tempo_fit_s)` da ④ é a parede.

⚠ **Fidelidade NÃO é julgada aqui (D97)** — o runner instrumenta e aplica o
gate objetivo; o julgamento é manual, do autor, a posteriori.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import time
import warnings
from typing import Any

import numpy as np

from src import export as _export
from src import naming
from src import standalone_harness as H
from src.checkpoint import Checkpointer as _Checkpointer   # [DI-43]
from src.budget import BudgetExhausted, FEBudget, maxfe_por_exp

# ── Identidade e constantes do config (Balde de parâmetros do cartão) ───────

#: `artifacts/seeds.json:alg_id.e81` — a 2ª coordenada da tupla do D62.
ALG_ID = 11

ALGO_VERSION = "qpots-2.0.1+e81-r3 (vendor intocado; Matérn D30 + offsets A6)"

#: Gerações do NSGA-II interno. **D46** — o paper é omisso; 10 é o valor do
#: README/`examples` do autor, adotado como escolha NOSSA declarada.
NGEN = 10

#: Nyström OFF ✓ (E.6: implementação incorreta no repo, e o próprio paper o
#: desliga no caso real; a semente dele nunca varia — mais um motivo).
NYSTROM = 0

#: q=1 no experimento principal (o `exp=batch` do grid usa q=10 — §D66).
Q_PRINCIPAL = 1

#: Sementes hard-coded no repo que recebem `+1000·s` (D22/DEF-A6).
SEED_GP_POSTERIOR = 1024      # acquisition.py:219 — base do `1024+seed_iter`
SEED_NSGA2 = 2430             # acquisition.py:366 — `nsga2(..., seed=2430)`
SEED_SELECT = 2043            # acquisition.py:372/377 — NÃO offsetado (artefato)

#: Cap de cache-hits CONSECUTIVOS antes do aborto (molde c122/c149): sem ele,
#: um candidato reescolhido para sempre trava o orçamento em livelock.
CACHE_CAP = 10

#: `nu` do Matérn do paper (DEF-B17.8).
MATERN_NU = 2.5


# ═══════════════════════════════════════════════════════════════════════════
#  Contexto de runtime — import do repo vendorizado + float64 + silêncio
# ═══════════════════════════════════════════════════════════════════════════


def _repo_root() -> str:
    """A raiz do pacote `qpots` vendorizado."""
    import os
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "algorithms", "e81_qPOTS")


@contextlib.contextmanager
def _e81_runtime():
    """`sys.path` do vendor + **float64 forçado** (N.2.2), restaurados na saída.

    O `qpots/config.py` define `DEFAULT_DTYPE = torch.float64`, mas é só uma
    constante de módulo: o repo NUNCA chama `torch.set_default_dtype`, então
    sem esta guarda o processo segue no float32 default do torch e o
    `SingleTaskGP` seria construído em precisão simples (medido nesta sessão).
    """
    import torch

    root = _repo_root()
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    dtype_ant = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        yield
    finally:
        torch.set_default_dtype(dtype_ant)
        if added and root in sys.path:
            sys.path.remove(root)


@contextlib.contextmanager
def _silencio():
    """Engole o `stdout` do stock (`print` por fit, por objetivo e por seleção).

    São ~3 linhas por iteração × 600 iterações no ZDT1 — ruído puro que
    poluiria o log do operador. Não é supressão de erro: `stderr`, warnings e
    exceções passam intactos.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        yield


# ═══════════════════════════════════════════════════════════════════════════
#  Adapter (L.14) — desnormalização [0,1]→nativo + delegação ao FEBudget
# ═══════════════════════════════════════════════════════════════════════════


class _Oracle:
    """Faz **APENAS** `xl + X01·(xu−xl)` e DELEGA a `bud.evaluate`.

    O `FEBudget` é a fonte ÚNICA do orçamento (D89): conta, deduplica por X
    nativo bit-a-bit (cache-hit = 0 FE) e aplica o hard-stop exato `31D−1`.
    Contar FE aqui duplicaria a contabilidade.
    """

    def __init__(self, problema: str, bud: FEBudget):
        from src import experiment as _exp
        self._p = _exp._instantiate_problem(problema)
        self._bud = bud
        self.name = problema
        self.n_var = int(self._p.n_var)
        self.n_obj = int(self._p.n_obj)
        self.xl = np.asarray(self._p.xl, dtype=np.float64)
        self.xu = np.asarray(self._p.xu, dtype=np.float64)
        self.tempo_aval_real_s = 0.0

    def _true_f(self, x: np.ndarray) -> np.ndarray:
        from src import problems as _problems
        return np.asarray(
            _problems.evaluate_problem(self._p, np.asarray(x).reshape(1, -1)),
            dtype=np.float64).reshape(-1)

    def to01(self, X_nat: np.ndarray) -> np.ndarray:
        """Nativo → [0,1] (o espaço interno do modelo e da aquisição)."""
        return (np.asarray(X_nat, dtype=np.float64) - self.xl) / (
            self.xu - self.xl)

    def to_native(self, X01: np.ndarray) -> np.ndarray:
        """[0,1] → nativo — a ÚNICA transformação do adapter."""
        return self.xl + np.asarray(X01, dtype=np.float64) * (self.xu - self.xl)

    def eval_native(self, x_nat: np.ndarray) -> np.ndarray:
        """1 avaliação REAL (ou cache-hit) via FEBudget. Cronometrada."""
        t0 = time.time()
        f = self._bud.evaluate(np.asarray(x_nat, dtype=np.float64),
                               self._true_f)
        self.tempo_aval_real_s += time.time() - t0
        return f


# ═══════════════════════════════════════════════════════════════════════════
#  Gancho 1 — Matérn 5/2 ARD (🔵 ARTIGO · D30/DEF-B17.8 · âncora e81-matern)
# ═══════════════════════════════════════════════════════════════════════════


@contextlib.contextmanager
def _matern_patch(D: int, torch):
    """Injeta `covar_module=get_matern_kernel_with_gamma_prior(D)`.

    Intercepta `SingleTaskGP` **no namespace de `qpots.model_object`** — o
    `fit_gp()` que roda é o STOCK, e o efeito é exatamente a 1 linha que a
    âncora `e81-matern` (`model_object.py:120`, `expect_after:
    "SingleTaskGP(..., covar_module=<Matérn>)"`) descreve.

    **Por que o helper do BoTorch e não um `ScaleKernel(MaternKernel(...))`
    montado à mão.** A D30 é marcada **"Compartilhado (c262, e81)"** no bundle,
    e os DOIS runners BoTorch já aceitos materializam essa mesma decisão como
    `covar_module=get_matern_kernel_with_gamma_prior(D)`
    (`c262_qnehvi.py:195`, `c154_jes.py:247`). Reusar o helper é o que faz
    "compartilhado" ser verdade no dado: mesmo `nu=5/2`, mesmo ARD, e as
    MESMAS `GammaPrior` em lengthscale e outputscale — se o e81 usasse um
    Matérn sem prior, os três configs teriam surrogates diferentes sob o
    rótulo de uma decisão só.

    Efeito colateral MEDIDO nesta sessão (registrado no handoff): um
    `ScaleKernel(MaternKernel(...))` **sem prior** faz o `fit_gpytorch_mll`
    do ZDT1 (D=30, n=329, objetivo 1) esgotar as tentativas com o L-BFGS-B em
    `ABNORMAL` → `ModelFittingError`; com o helper priorado, os 3 problemas
    ajustam limpo. A regularização dos priors é parte da receita canônica do
    BoTorch, não um remédio inventado aqui.

    Nota de contraste com o stock: o default do `SingleTaskGP` no BoTorch
    0.16.1 é um `RBFKernel` **puro** (sem `ScaleKernel`, sem outputscale) —
    é isso que a D30 corrige.

    `setdefault` e não atribuição: se algum dia o stock passar o seu próprio
    `covar_module`, o dele vence e o patch vira no-op visível — falha aberta,
    não silenciosa.
    """
    from botorch.models.utils.gpytorch_modules import (
        get_matern_kernel_with_gamma_prior)
    from qpots import model_object as _MO

    original = _MO.SingleTaskGP

    def _com_matern(*args, **kwargs):
        kwargs.setdefault("covar_module",
                          get_matern_kernel_with_gamma_prior(int(D)))
        return original(*args, **kwargs)

    _MO.SingleTaskGP = _com_matern
    try:
        yield
    finally:
        _MO.SingleTaskGP = original


# ═══════════════════════════════════════════════════════════════════════════
#  Ganchos 2+3 — offsets D22/A6 e instrumentação read-only
# ═══════════════════════════════════════════════════════════════════════════


class _Espia:
    """Coletor da iteração corrente (zerado a cada `nova_iteracao`)."""

    def __init__(self) -> None:
        self.res = None            # a `Result` do pymoo (população final)
        self.front = None          # `res.X` — o rank-0 que o maximin ranqueia
        self.escolhidos = None     # os q candidatos devolvidos
        self.idx_escolhidos: list[int] = []
        self.draws_stats: dict = {}
        self.n_chamadas_post = 0
        self.seed_nsga2 = None
        self.seed_gp = None
        self.n_front_1d = 0        # vezes que `res.X` veio 1-D (|ND|==1)

    def nova_iteracao(self) -> None:
        self.__init__()


@contextlib.contextmanager
def _instrumentacao(espia: _Espia, *, offset: int, torch):
    """Monta os wrappers de `_gp_posterior`, `nsga2` e `select_candidates`.

    **Offsets D22/A6** (os 2 sítios do `seeds.json`, e só eles):
      - `_gp_posterior`: desloca `seed_iter` em `+offset`. O corpo stock faz
        `manual_seed(1024 + seed_iter)` e `seed_iter` não alimenta mais nada,
        logo deslocá-lo ≡ offsetar a semente, com zero edição do corpo.
      - `nsga2`: soma `+offset` ao `seed` recebido (o `2430` de `:366`).
      - `select_candidates(seed=2043)` fica INTACTO — não está no artefato.

    **Instrumentação** (read-only, DI-12.1): resumo dos draws de Thompson, a
    `res` do pymoo (que o `qpots()` não devolve) e o front + índice escolhido.

    **Guarda `|ND|==1`**: o pymoo devolve `res.X` **1-D** quando o front tem um
    único ponto; o `cdist` do `select_candidates` exige 2-D e levantaria um
    erro de forma no meio do run. O wrapper faz `atleast_2d` e LOGA — é a
    leitura óbvia ("selecione do conjunto de Pareto"), não uma mudança de
    decisão: com uma linha só, o maximin devolve essa mesma linha.
    """
    from qpots import acquisition as _ACQ
    from qpots.acquisition import Acquisition

    orig_post = Acquisition._gp_posterior
    orig_nsga2 = _ACQ.nsga2
    orig_select = _ACQ.select_candidates

    def _post(self, x, gps, seed_iter: int = 1):
        espia.seed_gp = SEED_GP_POSTERIOR + int(seed_iter) + offset
        out = orig_post(self, x, gps, seed_iter=int(seed_iter) + offset)
        espia.n_chamadas_post += 1
        with torch.no_grad():                       # higiene D86
            arr = out.detach().cpu().numpy()
        d = espia.draws_stats
        d["min"] = arr.min(axis=0) if "min" not in d else np.minimum(
            d["min"], arr.min(axis=0))
        d["max"] = arr.max(axis=0) if "max" not in d else np.maximum(
            d["max"], arr.max(axis=0))
        d["soma"] = arr.sum(axis=0) + d.get("soma", 0.0)
        d["n"] = d.get("n", 0) + arr.shape[0]
        return out

    def _nsga2(problem, ngen=100, pop_size=100, seed=2436, callback=None):
        espia.seed_nsga2 = int(seed) + offset
        res = orig_nsga2(problem, ngen=ngen, pop_size=pop_size,
                         seed=int(seed) + offset, callback=callback)
        espia.res = res
        return res

    def _select(gps, pareto_set, device, q: int = 1, seed=None):
        ps = np.asarray(pareto_set)
        if ps.ndim == 1:
            espia.n_front_1d += 1
            ps = ps.reshape(1, -1)
        espia.front = ps
        out = orig_select(gps, ps, device, q=q, seed=seed)
        sel = np.asarray(out.detach().cpu(), dtype=np.float64).reshape(-1,
                                                                      ps.shape[1])
        espia.escolhidos = sel
        idx = []
        for linha in sel:
            hit = np.flatnonzero((ps == linha).all(axis=1))
            idx.append(int(hit[0]) if hit.size else -1)
        espia.idx_escolhidos = idx
        return out

    Acquisition._gp_posterior = _post
    _ACQ.nsga2 = _nsga2
    _ACQ.select_candidates = _select
    try:
        yield
    finally:
        Acquisition._gp_posterior = orig_post
        _ACQ.nsga2 = orig_nsga2
        _ACQ.select_candidates = orig_select


# ═══════════════════════════════════════════════════════════════════════════
#  μ/σ DES-PADRONIZADOS — a semântica EXATA da ③ (DEF-C4)
# ═══════════════════════════════════════════════════════════════════════════


def _mu_sigma(mo, X01: np.ndarray, torch) -> tuple[np.ndarray, np.ndarray]:
    """Posterior do GP em `X01` ([0,1]^D), devolvido em **f de minimização**.

    A cadeia de padronização do repo tem DOIS estágios, e desfazer só um
    devolveria número sem sentido:
      1. `fit_gp` treina sobre `standardize(train_y[..., j])` (z-score
         explícito, `ddof=1` — a convenção do `botorch.utils.transforms`);
      2. o `SingleTaskGP` do BoTorch 0.16.1 aplica, por default, o seu PRÓPRIO
         `outcome_transform=Standardize`, que o `posterior()` já desfaz.
    Logo `posterior()` devolve no espaço **z do estágio 1**; falta
    `·std_j + mean_j` para voltar a `train_y`, e `train_y = −f` ⇒ um sinal.

    É exatamente a inversa que o próprio stock usa no `_gp_posterior`
    (`unstandardize(Ys, gps.train_y)` seguido de `return −Ys`) — as duas rotas
    coincidem por construção, o que torna a ③ RECONSTITUÍVEL.

    σ é escala, não posição: `σ_f = σ_z · std_j` (a negação não a afeta).
    """
    Xq = torch.as_tensor(np.atleast_2d(X01), dtype=torch.float64)
    mus, sigs = [], []
    with torch.no_grad():                                   # higiene D86
        for j, modelo in enumerate(mo.models):
            post = modelo.posterior(Xq)
            col = mo.train_y[..., j]
            mean_j, std_j = col.mean(), col.std()
            mu_y = post.mean.reshape(-1) * std_j + mean_j
            sd_y = post.variance.clamp_min(0.0).sqrt().reshape(-1) * std_j
            mus.append((-mu_y).cpu().numpy())               # train_y=−f ⇒ −μ
            sigs.append(sd_y.cpu().numpy())
    return np.asarray(mus).T, np.asarray(sigs).T


def _sonda_predict(estado: dict, oracle: _Oracle, torch):
    """Gancho `predict(X_nat) -> (mu, sigma)` do `emit_sonda_block`.

    Recebe os 2000 pontos em espaço NATIVO (é assim que o artefato os guarda),
    converte para [0,1] — o espaço do modelo — e devolve μ/σ em f de
    minimização. Roda sob `preserve_all_rng()` (o helper garante): o posterior
    do GP é determinístico, mas a guarda é obrigatória pelo invariante §3.1.
    """
    def _p(X_nat: np.ndarray):
        mo = estado["mo"]
        return _mu_sigma(mo, oracle.to01(np.asarray(X_nat, dtype=np.float64)),
                         torch)
    return _p


# ═══════════════════════════════════════════════════════════════════════════
#  Auxiliares
# ═══════════════════════════════════════════════════════════════════════════


def _f(v) -> float | None:
    """float() tolerante a None/NaN — para o `.jsonl` (JSON não tem NaN)."""
    if v is None:
        return None
    v = float(v)
    return None if (v != v or v in (float("inf"), float("-inf"))) else v


def _nds_idx(F: np.ndarray) -> np.ndarray:
    """Índices do conjunto não-dominado (minimização)."""
    F = np.atleast_2d(np.asarray(F, dtype=np.float64))
    n = F.shape[0]
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        dom = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if dom.any():
            keep[i] = False
    return np.flatnonzero(keep)


def _dist_min(x_nat: np.ndarray, X_arc_nat: np.ndarray) -> float | None:
    """`dist_min_arquivo` (DI-10/B3) — espaço de decisão **NATIVO** (DI-19.4)."""
    if X_arc_nat is None or len(X_arc_nat) == 0:
        return None
    d = np.linalg.norm(np.asarray(X_arc_nat, dtype=np.float64)
                       - np.asarray(x_nat, dtype=np.float64), axis=1)
    return _f(float(d.min()))


def _n_blocos(buf, S: int) -> int:
    """Nº de blocos de sonda gravados na ③."""
    n = sum(1 for r in buf.surr_rows if r.get("regime") == "sonda")
    return int(n // int(S)) if S else 0


def _maximin_do_escolhido(front: np.ndarray, X01_treino: np.ndarray,
                          idx: int) -> float | None:
    """A distância maximin do candidato escolhido (instrumentação S.7).

    Recomputa APENAS para a linha escolhida — fora da decisão, custo O(n·D).
    """
    if idx is None or idx < 0 or front is None or len(X01_treino) == 0:
        return None
    d = np.linalg.norm(np.asarray(X01_treino, dtype=np.float64)
                       - np.asarray(front[idx], dtype=np.float64), axis=1)
    return _f(float(d.min()))


class FitFalhouError(RuntimeError):
    """O `fit_gpytorch_mll` do stock desistiu (`ModelFittingError`).

    O stock **não tem `try/except` no fit, por desenho** (§22.4·3.5): a
    fidelidade manda a exceção subir. Esta classe apenas a re-etiqueta com o
    contexto (iteração, objetivo, n) para o `.jsonl` e para o `motivo_parada`
    do manifesto, e o run encerra como `failed` — **pára-e-loga (D81)**, sem
    remédio inventado pela sessão.
    """


# ═══════════════════════════════════════════════════════════════════════════
#  O RUNNER
# ═══════════════════════════════════════════════════════════════════════════


def run_e81(exp: str, alg: str, problema: str, semente, *,
            sonda_on: bool = True,
            data_root: str = naming.DEFAULT_DATA_ROOT,
            enable_bucket: bool = False,
            teto_s: float | None = None,
            q: int = Q_PRINCIPAL,
            sonda_k: int | None = None,
            **_kwargs) -> dict:
    """Roda o qPOTS sob o contrato v5.2.1. Assinatura padrão dos runners R3.

    `enable_bucket=False` por padrão: o bucket-only (D54) vale do M8 em diante;
    no Mac, até o M7, gravam-se as camadas LOCAIS COMPLETAS, sem podar a ③
    (RI-08/DI-16.8).

    `teto_s` = teto de wall-clock. Ao estourar: **aborto LIMPO** — as 4 camadas
    ficam gravadas com a curva parcial e o manifesto nasce `failed` +
    `motivo_parada='teto_wall'` pelos kwargs `status=`/`motivo_parada=` do
    `write_run_outputs` (DI-23/§3.3 — nada de reescrever o manifesto por fora,
    como o molde c149 precisou fazer antes do kwarg existir).

    `q` = tamanho do lote (1 no principal; o `exp=batch` do grid usa 10).
    `sonda_k` sobrepõe a cadência da sonda — usado APENAS pelo teste de
    não-perturbação (k=10**9 ⇒ sonda praticamente desligada).
    """
    import torch

    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info(extra_mods=("botorch", "gpytorch", "pymoo"))
    semente = int(semente)

    with _e81_runtime():
        return _run_e81_inner(exp, alg, problema, semente, torch=torch,
                              pinning=pinning, env=env, t_run=t_run,
                              data_root=data_root,
                              enable_bucket=enable_bucket, teto_s=teto_s,
                              q=int(q), sonda_k=sonda_k,
                               sonda_on=sonda_on)


def _run_e81_inner(exp, alg, problema, semente, *, torch, pinning, env, t_run,
                   data_root, enable_bucket, teto_s, q, sonda_k, sonda_on=True):
    from botorch.exceptions.errors import ModelFittingError
    from qpots.acquisition import Acquisition
    from qpots.model_object import ModelObject

    # ── determinismo (N.1.1/D79) ────────────────────────────────────────────
    torch.set_num_threads(1)
    base = H.seed_base(alg, semente)            # 1000·s (D22 — e81 e c149)
    k_sonda = H.SONDA_K if sonda_k is None else int(sonda_k)

    # ── orçamento + DoE do artefato (D63/D87/D88 — NUNCA regenerado) ────────
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    doe = H.load_doe(problema, semente, data_root=data_root)
    D = int(doe["X"].shape[1])
    # [T6-batch] orcamento POR EXP (D66): main = 31D-1; batch = 11D-1+200q.
    bud = FEBudget(D=D, maxfe=maxfe_por_exp(exp, D, q), logger=log)
    oracle = _Oracle(problema, bud)
    M = oracle.n_obj
    if doe["X"].shape[0] != bud.n_init:
        raise RuntimeError(
            f"DoE com {doe['X'].shape[0]} pontos != 11D−1 = {bud.n_init} "
            f"— pára-e-loga (D81).")

    sonda = H.load_sonda(problema, regime="online", data_root=data_root)
    buf = H.SnapshotBuffer()
    # [DI-43] checkpoint atômico periódico — 25 gerações OU 30 min.
    ckpt = _Checkpointer(exp, alg, problema, semente, D=D, M=M,
                         regime="online", q=int(q), data_root=data_root, log=log)
    espia = _Espia()

    #: **bounds = [0,1]^D** — o invariante que mata o bug maximin (§22.4·3.5).
    B01 = torch.stack([torch.zeros(D, dtype=torch.float64),
                       torch.ones(D, dtype=torch.float64)])

    modelo_flag = f"GP-Matern52-ARD(TS,q={q})"
    sigma_dict = {
        "modelo": f"{M} SingleTaskGP INDEPENDENTES (1 por objetivo), BoTorch "
                  f"0.16.1, kernel get_matern_kernel_with_gamma_prior({D}) = "
                  f"ScaleKernel(Matern nu=5/2, ARD, GammaPrior(3,6)) com "
                  f"outputscale GammaPrior(2,0.15) — correcao D30/DEF-B17.8 "
                  f"sobre o RBFKernel PURO que e o default do BoTorch 0.16.1; "
                  f"MESMA construcao de c262/c154 (a D30 e Compartilhada); train_Yvar FIXO = noise_std^2 "
                  f"= 1e-12 (stock; o paper usa tau^2=1e-3 — divergencia "
                  f"registrada, mantido o codigo); RECRIADO E REAJUSTADO DO "
                  f"ZERO a cada iteracao (receita canonica README/ablation)",
        "pred_tipo": "valor — mu_*/sigma_* por objetivo",
        "mu": "media da posterior do GP, DES-PADRONIZADA nos DOIS estagios "
              "(o standardize() explicito do fit_gp e o outcome_transform="
              "Standardize default do SingleTaskGP) e com o SINAL invertido: "
              "mu_f = -(mu_z*std_j + mean_j), onde mean_j/std_j sao os da "
              "coluna j de train_y = -f (ddof=1, a convencao do "
              "botorch.utils.transforms). Escala NATIVA de f, MINIMIZACAO. "
              "E a mesma inversa que o stock usa em _gp_posterior "
              "(unstandardize + return -Ys) => a ③ e RECONSTITUIVEL",
        "sigma": "desvio-padrao da POSTERIOR do GP (sqrt(posterior.variance), "
                 "SEM ruido de observacao), des-padronizado por sigma_f = "
                 "sigma_z*std_j — a negacao do sinal NAO afeta a escala. "
                 "E incerteza EPISTEMICA do GP (VAR-GP), nunca variancia",
        "espaco_modelo": "'cru' — os VALORES gravados sao des-padronizados; o "
                         "modelo opera em z (transf_tipo='zscore', "
                         "transf_params={mean,std,sinal} POR ITERACAO — "
                         "DEF-C3: o espaco z e reconstituivel por "
                         "z = (-mu - mean)/std)",
        "regime=online": f"o FRONT (rank-0) da populacao final do NSGA-II "
                         f"interno da aquisicao, por iteracao (DEF-C2 'BO com "
                         f"EA interno'; pop={100 * D}=100*D, ngen={NGEN}) — e "
                         f"EXATAMENTE o conjunto `res.X` que o "
                         f"select_candidates ranqueia por maximin, i.e. o "
                         f"universo da decisao. Precedente materializado: "
                         f"c149 (rank-0 do NSGA-II da aquisicao)",
        "regime=sonda": "os 2000 pontos fixos do artefato, mesma semantica "
                        "mu/sigma acima, com o modelo da iteracao corrente; "
                        "colunas C3 declaradas pelo kwarg c3= do "
                        "emit_sonda_block (DI-23/§3.4)",
        "real_solution_id": f"preenchido nas {q} linha(s) do lote escolhido "
                            f"pelo maximin (as unicas que viram FE; em "
                            f"cache-hit aponta a solucao PREEXISTENTE — "
                            f"D89/DI-21)",
        "fe_treino_max": "n_treino-1 no momento do fit — o treino e o dataset "
                         "INTEIRO (init+infills, dedup D57), pois o qPOTS nao "
                         "poda nem subamostra: MONOTONICO",
        "selecao": f"maximin vs o dataset INTEIRO (select_candidates: "
                   f"cdist(res.X, train_x).min(axis=-1).argsort()[-q:]) — "
                   f"top-{q} do MESMO ranking, sem diversidade mutua (a "
                   f"leitura do paragrafo de implementacao do paper; a Eq.6 "
                   f"formal admite a leitura greedy-sequencial — ambiguidade "
                   f"do paper, B17.5, documentada)",
        "n_baseline": "NAO SE APLICA (P6/DI-16.6): o qPOTS nao tem baseline "
                      "nem prune — `n_baseline` e conceito do qLogNEHVI. O "
                      "campo equivalente e `n_train` no jsonl",
    }
    params = {
        "receita": "canonica README/ablation — ModelObject+Acquisition "
                   "RECRIADOS por iteracao (os examples/ tem o bug do "
                   "Acquisition stale: gps congelado no GP inicial)",
        "qpots_kwargs": {"nystrom": NYSTROM, "dim": D, "ngen": NGEN, "q": q,
                         "mt": "NAO passado (default 0)",
                         "partial_info": "NAO passado (default 0)"},
        "ngen": f"{NGEN} (D46 — README do autor; o paper e omisso: escolha "
                f"NOSSA declarada)",
        "nystrom": f"{NYSTROM} (OFF — E.6: implementacao incorreta no repo e o "
                   f"proprio paper o desliga no caso real)",
        "nsga2_interno": {"pop": 100 * D, "n_gen": NGEN,
                          "operadores": "defaults do pymoo 0.6.1.6 (o repo "
                                        "chama NSGA2(pop_size=...) sem "
                                        "operadores)",
                          "seed": f"{SEED_NSGA2}+1000*s = "
                                  f"{SEED_NSGA2 + base} (offset D22/A6 sobre "
                                  f"acquisition.py:366)"},
        "thompson": {"base_samples": f"manual_seed({SEED_GP_POSTERIOR}+"
                                     f"iteration+1000*s) por chamada de "
                                     f"_gp_posterior (offset D22/A6 sobre "
                                     f"acquisition.py:219)",
                     "semantica": "re-amostrado POR GERACAO do NSGA-II sobre "
                                  "a populacao corrente (base samples fixos "
                                  "DENTRO da iteracao; a MVN muda com a pop) "
                                  "— 'TS acoplado a populacao', nao 1 caminho "
                                  "coerente",
                     "objetivos": "amostrados INDEPENDENTES (1 GP por objetivo)"},
        "seed_select_candidates": f"{SEED_SELECT} — INTOCADO (nao consta no "
                                  f"seeds.json:offset_D22_hardcoded.e81; a "
                                  f"SPEC o classifica como quase inocuo, "
                                  f"reset pos-selecao)",
        "seed_base": f"1000*semente = {base} (D22 — SEED_OFFSET_ALGS)",
        "bounds": "[0,1]^D no ModelObject E no qpots() — OBRIGATORIO "
                  "(§22.4·3.5): mata o bug do maximin misturando espaco "
                  "nativo x normalizado. Desnormalizacao xl+X01*(xu-xl) SO no "
                  "adapter (L.14)",
        "sinal": "train_y = -f (o repo MAXIMIZA; _gp_posterior devolve -Ys) — "
                 "sem dupla negacao (E.6)",
        "kernel": f"get_matern_kernel_with_gamma_prior({D}) = ScaleKernel("
                  f"MaternKernel(nu={MATERN_NU}, ard_num_dims={D}, "
                  f"lengthscale_prior=Gamma(3,6)), outputscale_prior="
                  f"Gamma(2,0.15)) — D30/DEF-B17.8 (ARTIGO). E a MESMA chamada "
                  f"de c262_qnehvi.py:195 e c154_jes.py:247: a D30 e marcada "
                  f"'Compartilhado (c262, e81)' no bundle, entao os tres "
                  f"configs precisam do MESMO kernel, priors inclusive. "
                  f"Injetado no namespace de qpots.model_object (vendor "
                  f"INTOCADO; ancora e81-matern). O default do SingleTaskGP "
                  f"no BoTorch 0.16.1 e um RBFKernel PURO (sem ScaleKernel) "
                  f"— e isso que a D30 corrige",
        "train_Yvar": "1e-12 fixo (= noise_std=1e-6 ao quadrado, stock). "
                      "NOTA: o gpytorch emite NumericalWarning e ARREDONDA "
                      "ruidos < 1e-6 para 1e-6 internamente — comportamento "
                      "do stock, registrado",
        "torch_default_dtype": "float64 FORCADO pelo runner (N.2.2 + N.1.1 "
                               "generalizada/DI-21): o DEFAULT_DTYPE do "
                               "qpots/config.py e so uma constante de modulo, "
                               "o repo nunca chama set_default_dtype",
        "max_cholesky_size": "4096 (elevado globalmente ao importar BoTorch) "
                             "=> Cholesky EXATO em todo o regime (n<=929); a "
                             "DEF-L3 e a premissa 'Lanczos rank~100' estao "
                             "RETIRADAS (N.2)",
        "q": q, "cache_cap": CACHE_CAP,
        "sonda_k": k_sonda,
        "vendor": f"algorithms/e81_qPOTS (qpots 2.0.1) — NAO modificado; "
                  f"3 ganchos por contextmanager (Matern, offsets A6, "
                  f"instrumentacao read-only)",
    }

    n_cache_infill = n_cache_seguidos = n_lote_menor = 0
    n_lote_completado = 0
    g = 0
    status, motivo_parada = "ok", "orcamento"
    t_fit_total = t_busca_total = t_sonda_total = 0.0
    ultima_sonda_g = None
    estado_sonda: dict = {}
    n_front1 = 0
    res = None

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="online", maxfe=bud.maxfe,
                   n_init=bud.n_init, doe_hash=doe["doe_hash"],
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   params=params,
                   dtype_check=str(torch.get_default_dtype()),
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"])

        # ── init: o DoE do artefato, bit-a-bit, na ORDEM do arquivo (D88) ───
        for x in doe["X"]:
            oracle.eval_native(x)

        # ── laço principal — dirigido pelo bud.fe (a fonte ÚNICA, D89) ──────
        while bud.fe < bud.maxfe:
            g += 1
            t_g0 = time.time()
            espia.nova_iteracao()
            t_fit = t_busca = t_snd = 0.0
            linha_timing_aberta = False
            try:
                # treino = o dataset REAL inteiro (o qPOTS não poda nem
                # subamostra). Fonte única: `bud.records` — que NÃO cresce
                # num cache-hit ⇒ a regra DI-21 vale por construção.
                X_nat = np.vstack([r.x for r in bud.records])
                Y_nat = np.vstack([r.f for r in bud.records])
                n = X_nat.shape[0]
                X01 = oracle.to01(X_nat)
                fe_treino_max = n - 1

                # ── fit: M GPs do zero (receita canônica) ───────────────────
                t_f0 = time.time()
                tx = torch.as_tensor(X01, dtype=torch.float64)
                ty = torch.as_tensor(-Y_nat, dtype=torch.float64)  # −f (E.6)
                try:
                    with _silencio(), _matern_patch(D, torch), \
                            warnings.catch_warnings(record=True) as fit_warns:
                        warnings.simplefilter("always")
                        mo = ModelObject(train_x=tx, train_y=ty, bounds=B01,
                                         nobj=M, ncons=0, device="cpu",
                                         dtype=torch.float64)
                        mo.fit_gp()
                except ModelFittingError as exc:
                    log.guard("fit_falhou", geracao=g, n_treino=n, fe=bud.fe,
                              erro=f"{type(exc).__name__}: {exc}",
                              motivo="fit_gpytorch_mll esgotou as tentativas "
                                     "(L-BFGS-B ABNORMAL). O stock NAO tem "
                                     "try/except no fit por desenho "
                                     "(§22.4·3.5) — nenhum remedio e "
                                     "inventado aqui",
                              acao="ABORTO — para-e-loga (D81)")
                    raise FitFalhouError(
                        f"fit do GP falhou na iteracao {g} (n={n}, D={D}): "
                        f"{exc}") from exc
                t_fit = time.time() - t_f0
                t_fit_total += t_fit
                n_retries_fit = sum(
                    1 for w in fit_warns
                    if "attempt" in str(w.message).lower()
                    or "retry" in str(w.message).lower()
                    or "optimization" in str(w.message).lower())

                buf.set_fe_treino_max(fe_treino_max)
                buf.add_timing(geracao=g, n_acumulado=n, tempo_fit_s=t_fit)
                linha_timing_aberta = True
                estado_sonda.update(mo=mo, ftm=fe_treino_max)
                log.event("fit", geracao=g, n_treino=n,
                          tempo_fit_s=round(t_fit, 6),
                          fe_treino_max=fe_treino_max,
                          n_modelos=len(mo.models),
                          fit_retries=n_retries_fit,
                          dtype=str(mo.train_x.dtype),
                          kernel="get_matern_kernel_with_gamma_prior(D)")

                # sonda DEPOIS do fit, ANTES da decisão: mede o modelo COM QUE
                # esta iteração decide (k lido dinamicamente — teste §3.1)
                if sonda_on and H.sonda_due(g, k=k_sonda):      # [G-6]
                    t_snd = H.emit_sonda_block(
                        buf, log, geracao=g, fe=bud.fe, sonda=sonda,
                        predict=_sonda_predict(estado_sonda, oracle, torch),
                        fe_treino_max=fe_treino_max, pred_tipo="valor",
                        modelo_flag=modelo_flag,
                        c3=_c3(Y_nat),
                        motivo=f"cadencia k={k_sonda} (g=1,2,4,6,…)")
                    t_sonda_total += t_snd
                    ultima_sonda_g = g

                # ── busca: Thompson + NSGA-II + maximin (receita canônica) ──
                t_b0 = time.time()
                acq = Acquisition(None, mo, q=q, device="cpu",
                                  dtype=torch.float64)
                # O pymoo re-semeia np.random/random GLOBAIS a cada `minimize`
                # (N.1.3): a guarda impede que a aquisição desloque a
                # trajetória de tudo o que vier depois. Os offsets A6 já
                # tornam a busca reprodutível por dentro.
                with H.preserve_all_rng(), _silencio(), \
                        _instrumentacao(espia, offset=base, torch=torch):
                    newx = acq.qpots(bounds=B01, iteration=g - 1,
                                     nystrom=NYSTROM, dim=D, ngen=NGEN, q=q)
                t_busca = time.time() - t_b0
                t_busca_total += t_busca

                lote01 = np.asarray(newx.detach().cpu(),
                                    dtype=np.float64).reshape(-1, D)
                lote_extra01 = None            # os completados pelo fallback
                n_stock_sel = int(lote01.shape[0])

                # **assert |lote| == q** (§22.4·3.5): quando |ND| < q, o
                # `argsort()[-q:]` do stock devolve um lote MENOR — em
                # SILÊNCIO. Aqui o silêncio acaba.
                if lote01.shape[0] != q:
                    n_lote_menor += 1
                    log.guard("lote_menor_que_q", geracao=g,
                              n_lote=int(lote01.shape[0]), q=q,
                              n_front=int(len(espia.front)
                                          if espia.front is not None else 0),
                              motivo="|ND| < q: o argsort()[-q:] do "
                                     "select_candidates devolve lote menor "
                                     "SILENCIOSAMENTE (stock)",
                              acao="fallback qmaximin (DI-25 #3): completar "
                                   "ate q sobre os rank-1+ da populacao")
                    # ── [T6-batch] FALLBACK qmaximin (DI-25 #3, ratificado
                    #    2026-07-22): completar o lote ate q por MAXIMIN sobre
                    #    o RESTANTE da populacao do NSGA-II (rank-1+), maximizando
                    #    a distancia minima aos JA-selecionados; falha-alto se
                    #    nem assim fechar. Usa o `qmaximin` VENDORIZADO (fiel —
                    #    o mesmo farthest-point do repo, examples/Parallel_TC).
                    faltam = int(q) - int(lote01.shape[0])
                    ranks = espia.res.pop.get("rank")
                    Xpop = np.asarray(espia.res.pop.get("X"),
                                      dtype=np.float64).reshape(-1, D)
                    pool = (Xpop[np.asarray(ranks) >= 1] if ranks is not None
                            else np.empty((0, D)))
                    # dedup bit-a-bit contra o que ja esta no lote (D89)
                    if pool.shape[0] and lote01.shape[0]:
                        keep = ~np.array([
                            bool(np.any(np.all(lote01 == p, axis=1)))
                            for p in pool])
                        pool = pool[keep]
                    if pool.shape[0] < faltam:
                        raise RuntimeError(
                            f"e81 |ND|<q e o fallback qmaximin NAO fecha o lote: "
                            f"faltam {faltam}, rank-1+ disponiveis {pool.shape[0]} "
                            f"(g={g}, |ND|={lote01.shape[0]}, q={q}). "
                            f"Falha-alto (DI-25 #3) — para-e-loga (D81).")
                    from qpots.utils.tc_utils import qmaximin
                    extra = qmaximin(torch.as_tensor(lote01),
                                     torch.as_tensor(pool), q=faltam)
                    extra = np.asarray(extra.detach().cpu(),
                                       dtype=np.float64).reshape(-1, D)
                    # [T6-batch/fix] os pontos COMPLETADOS (rank-1+) não estão
                    # no `espia.front` ⇒ a ③, que itera sobre o front, os
                    # perderia. Guarda p/ gravá-los na ③ depois (com o sid do
                    # FE), senão a |lote|==q do gate reprova (só |ND| escolhidos).
                    n_stock_sel = int(lote01.shape[0])   # quantos vieram do stock
                    lote_extra01 = extra                 # os completados (q−|ND|)
                    lote01 = np.vstack([lote01, extra])
                    n_lote_completado += 1
                    log.guard("lote_completado_por", geracao=g,
                              valor="qmaximin", n_completado=faltam,
                              n_pool_rank1mais=int(pool.shape[0]), q=q,
                              motivo="DI-25 #3: maximin sobre rank-1+ "
                                     "maximizando dist-min aos ja-selecionados")
                    if lote01.shape[0] != q:
                        raise RuntimeError(
                            f"e81 fallback qmaximin fechou {lote01.shape[0]}!=q "
                            f"({q}) — para-e-loga (D81).")

                front01 = (espia.front if espia.front is not None
                           else lote01)
                mu_nat, sig_nat = _mu_sigma(mo, front01, torch)
                if espia.n_front_1d:
                    log.guard("front_1d", geracao=g,
                              motivo="pymoo devolveu res.X 1-D (|ND|==1); o "
                                     "cdist do select_candidates exige 2-D",
                              acao="reshape(1,-1) — leitura obvia, decisao "
                                   "inalterada (com 1 linha o maximin "
                                   "devolve essa linha)")

                # ── os FEs do lote: dedup D89 no FEBudget ───────────────────
                sids: list[int] = []
                houve_cache = False
                dists = []
                hard_stop_lote = False
                for x01 in lote01:
                    x_nat = oracle.to_native(x01)
                    dists.append(_dist_min(x_nat, X_nat))
                    fe_antes = bud.fe
                    try:
                        oracle.eval_native(x_nat)
                    except BudgetExhausted:
                        # [DI-34] STRADDLE: o orçamento esgotou no meio do
                        # lote. Os picks JÁ avaliados desta geração entraram
                        # na ① — sem este rito eles sumiam da ③/②/⑥ (a
                        # paisagem da última geração ficava incompleta).
                        # Grava a geração PARCIAL e re-levanta após o ⑥.
                        hard_stop_lote = True
                        dists.pop()   # o dist do ponto NÃO avaliado sai do ⑥
                        log.guard("hard_stop_lote", geracao=g, fe=bud.fe,
                                  n_avaliados_do_lote=len(sids), q=q,
                                  motivo="orçamento esgotou no meio do lote "
                                         "— geração parcial VÁLIDA (D61)")
                        break
                    sid = bud.solution_id_of(x_nat)
                    sids.append(sid)
                    if bud.fe == fe_antes:
                        houve_cache = True
                        n_cache_infill += 1
                        log.guard("cache_hit_infill", geracao=g,
                                  solution_id=sid, fe=bud.fe,
                                  motivo="o maximin reescolheu uma X ja "
                                         "avaliada (bit-a-bit) — 0 FE (D89); "
                                         "o treino NAO cresce (DI-21)")
                if houve_cache:
                    n_cache_seguidos += 1
                else:
                    n_cache_seguidos = 0

                # ── ③ BUSCA: o front da aquisição (DEF-C2), μ/σ nativos ────
                c3 = _c3(Y_nat)
                idx_sel = {i: s for i, s in zip(espia.idx_escolhidos, sids)
                           if i is not None and i >= 0}
                for i in range(front01.shape[0]):
                    buf.add_surrogate(_export.surrogate_row(
                        g, oracle.to_native(front01[i]),
                        regime="online",
                        real_solution_id=idx_sel.get(i),
                        mu=mu_nat[i], sigma=sig_nat[i],
                        pred_tipo="valor", modelo_flag=modelo_flag, **c3))
                # [T6-batch/fix] os pontos COMPLETADOS pelo fallback qmaximin
                # (rank-1+, fora do front) também são LOTE — a ③ tem de
                # registrá-los com o real_solution_id do seu FE, senão o gate
                # `|lote|==q` conta só os |ND| do front (o defeito medido no
                # 1º smoke: 28 gerações com <q escolhidos).
                if lote_extra01 is not None and lote_extra01.shape[0]:
                    mu_ex, sig_ex = _mu_sigma(mo, lote_extra01, torch)
                    for j in range(lote_extra01.shape[0]):
                        k = n_stock_sel + j
                        if k >= len(sids):
                            break   # [DI-34] straddle: extra NÃO avaliado
                        buf.add_surrogate(_export.surrogate_row(
                            g, oracle.to_native(lote_extra01[j]),
                            regime="online",
                            real_solution_id=sids[k],
                            mu=mu_ex[j], sigma=sig_ex[j],
                            pred_tipo="valor",
                            modelo_flag=modelo_flag + "+qmaximin", **c3))
                # ② membership: o dataset REAL corrente — é literalmente o
                # conjunto contra o qual o maximin decide (o "estado" do BO;
                # precedente c262/c149).
                buf.add_pop(g, [r.solution_id for r in bud.records])

                # ── ⑥ jsonl: DI-10 + os campos S.7 do e81 ──────────────────
                F_arc = np.vstack([r.f for r in bud.records])
                dr = espia.draws_stats
                log.decision(
                    caminho="e81_gen:thompson+nsga2+maximin",
                    motivo=f"1 realizacao de Thompson por geracao do NSGA-II "
                           f"(pop={100 * D}, ngen={NGEN}) e selecao top-{q} "
                           f"por maximin vs o dataset INTEIRO (n={n})",
                    geracao=g, iteracao=g - 1,
                    seed_nsga2=espia.seed_nsga2, seed_gp=espia.seed_gp,
                    nystrom=NYSTROM, ngen=NGEN, q=q,
                    n_train=n,                       # P6/DI-16.6 (NUNCA n_baseline)
                    n_front_acq=int(front01.shape[0]),
                    idx_escolhidos=[int(i) for i in espia.idx_escolhidos],
                    n_lote=int(lote01.shape[0]),
                    assert_lote_eq_q=bool(lote01.shape[0] == q),
                    maximin_escolhido=[
                        _maximin_do_escolhido(front01, X01, i)
                        for i in espia.idx_escolhidos],
                    draws_thompson={
                        "n_chamadas": espia.n_chamadas_post,
                        "n_pontos": int(dr.get("n", 0)),
                        "min": [_f(v) for v in dr.get("min", [])],
                        "med": [_f(v) for v in (dr["soma"] / dr["n"])]
                               if dr.get("n") else [],
                        "max": [_f(v) for v in dr.get("max", [])]},
                    mu_sel_nat=[[_f(v) for v in mu_nat[i]]
                                for i in espia.idx_escolhidos if i >= 0],
                    sigma_sel_nat=[[_f(v) for v in sig_nat[i]]
                                   for i in espia.idx_escolhidos if i >= 0],
                    dtype_check=str(mo.train_x.dtype),
                    cache_hit=bool(houve_cache), solution_id=sids,
                    fit_retries=n_retries_fit,
                    **H.minimo_comum_di10(
                        F_arc, fe=bud.fe,
                        modelo_hp=_modelo_hp(mo, torch),
                        tempo_fit_s=t_fit, tempo_busca_s=t_busca,
                        dist_min_arquivo=(min(d for d in dists
                                              if d is not None)
                                          if any(d is not None for d in dists)
                                          else None)))
                # [DI-34] o straddle re-levanta AQUI, com ③/②/⑥ da geração
                # parcial completos (a ④ fecha no finally, como sempre) — o
                # tratamento externo o recebe como o fim natural que é (D61).
                if hard_stop_lote:
                    raise BudgetExhausted(
                        f"fim do orçamento no meio do lote (fe={bud.fe})")
            finally:
                # ⚠ A ④ é FECHADA AQUI, aconteça o que acontecer. No molde
                # c149 o `break` do cache-cap saltava o `update_timing` e a
                # geração ficava com os 3 tempos NULL — o que reprova o
                # próprio gate (`④ timing v5.2.1 completa`). Em `finally` o
                # aborto preserva uma ④ VÁLIDA, que é o entregável.
                if linha_timing_aberta:
                    buf.update_timing(
                        g, tempo_busca_s=t_busca, tempo_pred_sonda_s=t_snd,
                        tempo_geracao_s=(time.time() - t_g0) - t_snd)
                ckpt.talvez_gravar(bud, buf, iteracao=g)   # [DI-43]
                # higiene D86: soltar os tensores/objetos da iteração antes
                # do `gc.collect()`. O `mo` NÃO entra aqui — fica retido de
                # propósito em `estado_sonda` (a sonda final o usa); é 1
                # modelo, não um acúmulo. `locals()` não serve para `del` em
                # escopo de função (devolve um snapshot), então é explícito.
                acq = tx = ty = newx = None
                lote01 = front01 = mu_nat = sig_nat = None
                espia.res = espia.front = espia.escolhidos = None
                H.iteration_cleanup()

            if n_cache_seguidos >= CACHE_CAP:
                status, motivo_parada = "failed", "cache_hit_travado"
                log.guard("cache_hit_travado", geracao=g, fe=bud.fe,
                          seguidos=n_cache_seguidos,
                          acao="ABORTO — o orcamento nao avanca; "
                               "para-e-loga (D81)")
                break

            if teto_s is not None and (time.time() - t_run) > teto_s:
                status, motivo_parada = "failed", "teto_wall"
                log.guard("teto_wall", geracao=g, fe=bud.fe,
                          decorrido_s=round(time.time() - t_run, 1),
                          teto_s=teto_s,
                          acao="ABORTO LIMPO — curva parcial preservada; "
                               "manifesto failed (D-07/DI-23); a decisao de "
                               "completar e do M7 (D81)")
                break

    except BudgetExhausted:
        # Fim NATURAL (D61) — o laço já para em bud.fe == maxfe; rede de
        # segurança do hard-stop exato.
        log.guard("hard_stop_capturado", fe=bud.fe, maxfe=bud.maxfe,
                  motivo="fim natural do orcamento (D61)")
    except FitFalhouError as exc:
        status, motivo_parada = "failed", "fit_falhou"
        log.guard("aborto_fit", fe=bud.fe, geracao=g, erro=str(exc))
    except Exception as exc:                          # pragma: no cover
        status, motivo_parada = "failed", f"{type(exc).__name__}: {exc}"
        log.footer(status="failed", fe_final=bud.fe, erro=motivo_parada)
        log.close()
        raise

    # ── sonda final (§3.1/finalProbe) — fora do try do laço para rodar
    # também depois do BudgetExhausted. Não roda se o run abortou no fit
    # (não há modelo válido a sondar).
    if (sonda_on and g and ultima_sonda_g != g          # [G-6]
            and estado_sonda.get("mo") is not None
            and motivo_parada != "fit_falhou"):
        ftm_final = estado_sonda.get("ftm")
        buf.set_fe_treino_max(ftm_final)
        with _silencio():
            t_snd = H.emit_sonda_block(
                buf, log, geracao=g, fe=bud.fe, sonda=sonda,
                predict=_sonda_predict(estado_sonda, oracle, torch),
                fe_treino_max=ftm_final, pred_tipo="valor",
                modelo_flag=modelo_flag,
                c3=_c3(np.vstack([r.f for r in bud.records[:ftm_final + 1]])),
                motivo="ultima geracao (§3.1/finalProbe)")
        t_sonda_total += t_snd
        buf.update_timing(g, tempo_pred_sonda_s=t_snd)
        ultima_sonda_g = g

    try:
        n_front1 = len(_nds_idx(np.vstack([r.f for r in bud.records])))
        timing_totais = _export.manifest_timing_block(
            tempo_total_s=time.time() - t_run,
            tempo_fit_surrogate_s=t_fit_total, tempo_busca_s=t_busca_total,
            tempo_aval_real_s=oracle.tempo_aval_real_s,
            tempo_pred_sonda_s=t_sonda_total)
        res = H.write_run_outputs(
            exp, alg, problema, semente, bud, buf, D=D, M=M,
            cp_hashes={"doe_hash": doe["doe_hash"]},
            env=env, pinning=pinning, n_geracoes=g,
            algo_version=ALGO_VERSION, timing_totais=timing_totais,
            sigma_dict=sigma_dict, regime="online", params=params,
            # DI-23/§3.3: o manifesto nasce HONESTO — nada de reescrever
            # por fora (o contorno que o c149 precisou antes destes kwargs).
            status=status, motivo_parada=motivo_parada, q=int(q),
            sonda_info={"S": sonda["S"], "regime": "online",
                        "cadencia": f"online: k={k_sonda} (g=1,2,4,6,…) + "
                                    f"1a e ultima (finalProbe)",
                        "n_blocos": _n_blocos(buf, sonda["S"]),
                        "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]},
            data_root=data_root, enable_bucket=enable_bucket)
        # [T6-batch] `q` carimbado DIRETO no `write_run_outputs` (o harness já
        # o repassa ao `new_manifest`) — o remendo de reescrita pós-hoc (2
        # escritas) foi removido.
        man = res["manifest"]
        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=g,
                   motivo_parada=motivo_parada, n_front1=n_front1,
                   n_cache_infill=n_cache_infill, n_lote_menor=n_lote_menor,
                   n_lote_completado=n_lote_completado)
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_geracoes": g,
        "cp_init_ok": bool(res["cp_init_ok"]) if res else False,
        "status": status, "motivo_parada": motivo_parada,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows),
        "n_blocos_sonda": _n_blocos(buf, sonda["S"]), "regime": "online",
        "cache_hits": bud.cache_hits, "n_cache_infill": n_cache_infill,
        "n_lote_menor": n_lote_menor,
        "n_lote_completado": n_lote_completado, "n_front1": n_front1,
        "tempo_pred_sonda_s": t_sonda_total, "q": q,
    }


def _c3(Y_nat: np.ndarray) -> dict:
    """As colunas DEF-C3 da iteração (cru + transformado + parâmetros).

    ⚠ `transf_params` vai como **dict** — o `surrogate_row` faz o
    `json.dumps`. Passá-lo já serializado (o que o `_stamp_c3_sonda` do c149
    precisava fazer, por mutar a row DEPOIS de construída) produziria
    duplo-encode ao entrar pelo kwarg `c3=`, que repassa `**c3` ao
    `surrogate_row`. Achado da recon adversarial desta sessão.

    `sinal=-1` faz parte da transformação: sem ele o z não é reconstituível
    (o modelo vive em `z = (train_y − mean)/std` com `train_y = −f`).
    """
    Y = np.atleast_2d(np.asarray(Y_nat, dtype=np.float64))
    ty = -Y
    mean = ty.mean(axis=0)
    std = ty.std(axis=0, ddof=1) if ty.shape[0] > 1 else np.ones(ty.shape[1])
    return {
        "espaco_modelo": "cru",
        "transf_tipo": "zscore",
        "transf_params": {"mean": [float(v) for v in mean],
                          "std": [float(v) for v in std],
                          "sinal": -1,
                          "ddof": 1,
                          "nota": "z = (-f - mean)/std ; os valores gravados "
                                  "em mu_*/sigma_* JA estao des-padronizados "
                                  "(escala nativa de f, minimizacao)"},
    }


def _modelo_hp(mo, torch) -> dict:
    """`modelo_hp` do DI-10/B1 — leitura dos hiperparâmetros já ajustados.

    Read-only e sob `no_grad`: não move a busca. Nunca derruba o run (a
    instrumentação B1 é acessório, não mecanismo — D97/patch-mínimo).
    """
    try:
        por_obj = []
        with torch.no_grad():
            for m in mo.models:
                ls = m.covar_module.base_kernel.lengthscale.detach().reshape(-1)
                por_obj.append({
                    "lengthscale_min": _f(float(ls.min())),
                    "lengthscale_med": _f(float(ls.mean())),
                    "lengthscale_max": _f(float(ls.max())),
                    "outputscale": _f(float(
                        m.covar_module.outputscale.detach())),
                })
        return {"kernel": "Matern5/2 ARD", "por_objetivo": por_obj,
                "train_Yvar": 1e-12}
    except Exception:                                  # noqa: BLE001
        return {"kernel": "Matern5/2 ARD", "erro": "leitura de hp falhou"}


__all__ = ["run_e81", "FitFalhouError", "ALG_ID", "ALGO_VERSION",
           "NGEN", "NYSTROM", "Q_PRINCIPAL", "CACHE_CAP"]
