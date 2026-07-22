"""[R3-c149] LBN-MOBO (Ansari et al.) sobre o `standalone_harness` — regime ONLINE.

O 2º algoritmo da Rodada 3. Nasce NATIVO no contrato de dados v5.2.1 (sonda,
`fe_treino_max`, timing completo, jsonl DI-10) — não há retrofit depois.

**O mecanismo (I.14/M.11).** Deep ensemble de K=10 MLPs (D→100→50→100→M, uma
ativação DISTINTA na raiz por rede) retreinado DO ZERO a cada iteração (60
épocas, sum_mse, Adam 5e-4 ×0,95/época — D43: o retreino É o mecanismo que dá a
incerteza). Aquisição 2M-objetivo: NSGA-II (pop=1000, 100 ger) minimiza
`[μ₁..μ_M, −σ²₁..−σ²_M]`, onde σ² é a variância POPULACIONAL (ddof=0) entre as
K=10 predições — a discordância do ensemble é a incerteza epistêmica. O paper
avalia o front INTEIRO (batch 1000–20k); **no principal q=1 a sub-seleção de 1
ponto é regra NOSSA (D41/D96 — HVI-greedy(μ), FECHADA)**.

**O que este módulo faz — e o que NÃO faz.** O repo oficial em
`algorithms/c149_LBN-MOBO/` é um HARNESS DE CLUSTER (pipeline .mat/ckpt em
disco, wait-loops por contagem de arquivos, paths fixos) — **não um algoritmo
chamável**. Este módulo RECONSTRÓI o loop de BO in-memory (D78/N.3) a partir
das peças: `_bnn_diverse_func` (fork fiel de `Forward_BNN.BNN_diverse_func`,
I/O de disco removido), `_AcqProblem` (fork de `BO_surrogate_uncertainty`, com
o **fix `[:, :M]`** — 🔴 ARTIGO: `BO_surrogate_function_uncertainty.py:46` faz
`[:, :2]` e truncaria M=3 em silêncio) e `_calculate_pareto` (fork de
`Acquisition_4_D.calculate_pareto_4_D`, sem Oracle nem `.mat`). A ARQUITETURA
(classe `MultiLayerPerceptron_forward` + lista de ativações) é IMPORTADA do
repo oficial — zero cópia onde dá para importar. O repo fica INTOCADO (D30).

**Desvios declarados (bússola D29):**
- 🔴 fix `[:, :M]` (fidelidade→artigo): M genérico na aquisição.
- 🟢 z-score de Y por objetivo (B13.4 — refit por iteração; o próprio autor
  normaliza Y na variante Airfoil): sem ele, Y de escala grande + sum_mse +
  init N(0,1e-3²) diverge/NaN. NSGA-II roda em z; HVI sobre μ DES-padronizado.
- 🟢 q=1 = HVI-greedy(μ) (D41/D96 — o paper NÃO sub-seleciona): HVI em
  objetivos normalizados pelo min/max do arquivo OBSERVADO da iteração (nunca
  a S.5 — vazaria o oráculo); ref = nadir observado ×1,1 no espaço
  normalizado; desempate = maior σ² agregada (em z — escala-neutra, coerente
  com a normalização do próprio D96); fallback = aleatório-do-front com o RNG
  do harness (D91, uso_id=2).
- 🟠 `torch.no_grad()` na predição (N.1.5/D86 — o stock constrói grafo e
  descarta com `.detach()`; sem o no_grad o retreino-por-FE acumula grafo).
- 🟠 PM `prob_var` = default do pymoo `min(0.5, 1/D)` — **decisão do autor
  2026-07-22**: o repo chama `NSGA2(pop_size=1000)` puro (nenhum operador
  explícito); o "1/30" da nota SPEC:722 é o default AVALIADO no ZDT3-30D do
  paper, não um hard-code (medido no env_main).

**Fidelidade = validação MANUAL do autor, em lote (D97).** Este módulo
instrumenta e aplica o gate objetivo; NUNCA julga nem auto-conserta fidelidade.
"""

from __future__ import annotations

import contextlib
import os
import sys
import time

# ⚠ ORDEM: o `standalone_harness` pina as env vars de thread (D79/N.1.1) no
# TOPO do módulo, ANTES de qualquer `import numpy`.
from src import standalone_harness as H

import numpy as np

from src import export as _export
from src import manifest as _manifest
from src import naming
from src.budget import BudgetExhausted, FEBudget

# ── Identidade e constantes do config ───────────────────────────────────────

#: `alg_id` canônico do c149 — `claude_code_context/artifacts/seeds.json:alg_id`
#: (D62/D91). NÃO é um inteiro livre: há teste que o compara com o artefato.
ALG_ID = 12

#: `uso_id` do c149 (seeds.json:uso_id_catalogo) — POR ITERAÇÃO (≠ c122, que
#: semeia por STREAM 1× por run): o retreino-do-zero re-consome o RNG a cada
#: iteração, então cada uso concorrente deriva a SUA semente com `iteracao=g`.
#:  - uso 0 ("torch.manual_seed por rede net_n"): materializado pela metade
#:    HARD-CODED do D22 — `1000·s + net_n + 1` (offset A6 sobre o
#:    `manual_seed(net_n+1)` do stock, `Forward_BNN.py:57`); o harness ainda
#:    semeia o torch da iteração com uso 0 por higiene (cobre consumo residual).
#:  - uso 1: seed do NSGA-II da aquisição — POR ITERAÇÃO via helper. ⚠ O
#:    artefato `offset_D22_hardcoded` sugere `+1000·s` sobre o seed stock
#:    (que é o índice de run, ≡0 no q=1) ⇒ seed CONSTANTE; a SPEC §22.4·3.4
#:    manda `seed=h(s,iter,run)` (por iteração). A leitura por-iteração é a
#:    ÚNICA autoconsistente com o dedup D89: com seed constante, um cache-hit
#:    (treino não cresce ⇒ mesmo ensemble ⇒ mesma aquisição ⇒ mesmo candidato)
#:    entra em LIVELOCK até o cap. Precedência D83: SPEC > artifacts.
#:  - uso 2 ("Generator(PCG64)"): o RNG numpy do harness — aqui usado SÓ no
#:    fallback aleatório-do-front (D96). ⚠ O rótulo "do DoE" no catálogo está
#:    STALE (D87/D88 mataram a geração de DoE) — sinalizado no handoff.
USO_TORCH_ITER = 0
USO_NSGA2 = 1
USO_NP_HARNESS = 2

ALGO_VERSION = "c149-lbnmobo-1.0"

#: Nome da pasta do repo oficial (é assim no disco).
REPO_DIRNAME = "c149_LBN-MOBO"

# ── Parâmetros — Balde B (código oficial; ver tabela §22.4 da SPEC) ─────────
K_ENSEMBLE = 10        #: K redes (paper ✓; `range(10)`, Forward_BNN/BO_surrogate)
HIDDEN = [100, 50, 100]  #: D→100→50→100→M (Forward_BNN.py:36)
EPOCHS = 60            #: por rede, por iteração (paper ✓; Forward_BNN.py:38)
BATCH = 10             #: Forward_BNN.py:39
LR0 = 5e-4             #: Forward_BNN.py:40
LR_DECAY = 0.95        #: ×/época (Forward_BNN.py:41; o `reg=0.001` é morto)
SPLIT_FRAC = 0.9       #: split 90/10 (Forward_BNN.py:56); val só logado
POP_ACQ = 1000         #: NSGA-II pop (Acquisition_4_D.py:11)
NGEN_ACQ = 100         #: NSGA-II gerações (Acquisition_4_D.py:20)
HVI_REF = 1.1          #: D96 — ref = nadir observado ×1,1 no espaço normalizado
CACHE_CAP = 10         #: cap p/ cache-hits consecutivos (molde c122 §5.3/DI-21)
N_MIN_SPLIT = 10       #: n<10 quebra o split 90/10 (guard + pára — cartão)

# ═══════════════════════════════════════════════════════════════════════════
#  Contexto de runtime — import do repo oficial + dtype float32
# ═══════════════════════════════════════════════════════════════════════════


def _repo_root() -> str:
    return os.path.join(H.ROOT, "algorithms", REPO_DIRNAME)


@contextlib.contextmanager
def _c149_runtime():
    """Contexto de import do repo oficial + o dtype que o código dele exige.

    **Import mínimo:** só `layer_config_forward` (a arquitetura + lista de
    ativações) — puro torch, sem paths fixos. `Forward_BNN`/`Acquisition_4_D`/
    `acquisition_organizeer` NÃO são importados (fazem I/O de disco no corpo
    — é exatamente o que a reconstrução D78 elimina).

    **dtype float32 — FORÇADO PELO CÓDIGO (D29 🟠 impl→código; N.1.1
    generalizada por DI-21).** `pin_runtime()` deixa o default do torch em
    float64, mas o c149 é float32-nativo (`torch.from_numpy(...).float()`,
    `torch.tensor(design).float()` — Forward_BNN.py:50-51,
    BO_surrogate_function_uncertainty.py:30). Com pesos float64 × entrada
    float32 o forward levanta `RuntimeError` (mesmo caso MEDIDO no c122).
    Criar os pesos JÁ em float32 também preserva os bits do init N(0,1e-3²)
    do stock (normal_ em float64 + cast daria outros valores). O default é
    restaurado na saída; o estado vai ao manifesto.
    """
    import torch

    root = _repo_root()
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"repo oficial do c149 ausente: {root} — pára-e-loga (D81).")
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    dtype_ant = torch.get_default_dtype()
    torch.set_default_dtype(torch.float32)
    try:
        yield
    finally:
        torch.set_default_dtype(dtype_ant)
        if added and root in sys.path:
            sys.path.remove(root)


# ═══════════════════════════════════════════════════════════════════════════
#  Adapter (L.14) — desnormalização [0,1]→nativo + delegação ao FEBudget
# ═══════════════════════════════════════════════════════════════════════════


class _Oracle:
    """`Oracle_eval(X01)→Y` do cartão: **APENAS** `xl + X01·(xu−xl)` e DELEGA
    a `bud.evaluate` — o FEBudget é a FONTE ÚNICA do orçamento (D89): conta,
    deduplica (cache-hit = 0 FE) e aplica o hard-stop exato 31D−1. NUNCA se
    conta FE aqui (v5.2.1: contagem no adapter duplicaria a contabilidade).

    O repo só roda [0,1] (`query_oracle.py` avalia direto) — a desnormalização
    é NOVA, criada pelo adapter (L.14), porque MMF1 vive em xl=[1,−1].
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
        """Nativo → [0,1] (o espaço interno do modelo)."""
        return (np.asarray(X_nat, dtype=np.float64) - self.xl) / (
            self.xu - self.xl)

    def to_native(self, X01: np.ndarray) -> np.ndarray:
        """[0,1] → nativo — a ÚNICA transformação do adapter."""
        return self.xl + np.asarray(X01, dtype=np.float64) * (self.xu - self.xl)

    def eval_native(self, x_nat: np.ndarray) -> np.ndarray:
        """1 avaliação REAL (ou cache-hit) via FEBudget. Cronometrada."""
        t0 = time.time()
        f = self._bud.evaluate(np.asarray(x_nat, dtype=np.float64), self._true_f)
        self.tempo_aval_real_s += time.time() - t0
        return f


# ═══════════════════════════════════════════════════════════════════════════
#  Reconstrução 1/3 — treino de UMA rede (fork fiel de Forward_BNN)
# ═══════════════════════════════════════════════════════════════════════════


def _bnn_diverse_func(net_n: int, X01: np.ndarray, Yz: np.ndarray,
                      D: int, M: int, seed: int, torch, MLP):
    """`BNN_diverse_func(net_n, X, Y) → model` — fork FIEL de
    `Forward_BNN.BNN_diverse_func`, com o I/O de disco (`Dataset/dset_%d.mat`,
    `Models/iter_%d/*.ckpt`) substituído por arrays in-memory (D78/L.14).

    **ORDEM DE CONSUMO DE RNG idêntica ao stock (Forward_BNN.py:50-67):**
    `manual_seed(seed)` → `random_split` (consome `randperm(n)`) → construção
    do modelo (o init DEFAULT das Linear consome RNG) → `weights_init`
    (`normal_(0, 1e-3)` sobrescreve; bias 0). Alterar a ordem mudaria os bits
    do init. `seed` = `1000·s + net_n + 1` (offset A6/D22 sobre o
    `manual_seed(net_n+1)` do stock).

    DataLoader SEM shuffle (stock) — a única aleatoriedade do treino é o
    seed: split + init. Loss `sum_mse` = Σ_batch mean_M((ŷ−y)²) (gradiente
    ×batch — stock). Val-MSE computado por época como no stock (era só
    impresso e descartado — aqui a ÚLTIMA época é retida e vai ao jsonl, B1).

    Devolve `(model em eval(), val_mse_final, n_train, n_val)`.
    """
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    def weights_init(m):                              # Forward_BNN.py:15-18
        if type(m) == nn.Linear:
            m.weight.data.normal_(0.0, 1e-3)
            m.bias.data.fill_(0.)

    def update_lr(optimizer, lr):                     # Forward_BNN.py:20-22
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

    def sum_mse(yhat, y):                             # Forward_BNN.py:71-72
        return torch.sum(torch.mean((yhat - y) ** 2, dim=1))

    x_t = torch.from_numpy(np.ascontiguousarray(X01)).float()
    y_t = torch.from_numpy(np.ascontiguousarray(Yz)).float()
    dataset = TensorDataset(x_t, y_t)
    n = len(dataset)
    lengths = [int(n * SPLIT_FRAC), n - int(n * SPLIT_FRAC)]  # :56

    torch.manual_seed(int(seed))                      # :57 (+1000·s — D22/A6)
    train_ds, val_ds = torch.utils.data.random_split(dataset, lengths)
    train_loader = DataLoader(train_ds, batch_size=BATCH)      # sem shuffle
    val_loader = DataLoader(val_ds, batch_size=BATCH)

    model = MLP(D, HIDDEN, M, net_n)                  # :64 (init default…)
    model.apply(weights_init)                         # :67 (…sobrescrito)

    criterion_MSE = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR0)

    lr = LR0
    val_mse = float("nan")
    for _epoch in range(EPOCHS):
        for controll, state in train_loader:
            optimizer.zero_grad()
            outputs = model(controll)
            loss = sum_mse(outputs, state)
            loss.backward()
            optimizer.step()
        lr *= LR_DECAY                                # :100-101 (pós-época)
        update_lr(optimizer, lr)
        with torch.no_grad():                         # :102-117 (val por época)
            state_all = torch.zeros(0, M)
            outputs_all = torch.zeros(0, M)
            for controll, state in val_loader:
                state_all = torch.cat((state_all, state), 0)
                outputs_all = torch.cat((outputs_all, model(controll)), 0)
            val_mse = float(criterion_MSE(state_all, outputs_all))

    model.eval()
    return model, val_mse, lengths[0], lengths[1]


# ═══════════════════════════════════════════════════════════════════════════
#  Reconstrução 2/3 — a aquisição 2M (fork com o fix [:, :M])
# ═══════════════════════════════════════════════════════════════════════════


def _make_acq_problem(models, D: int, M: int, torch):
    """`BO_surrogate_uncertainty(models, D, M)` — fork FIEL de
    `BO_surrogate_function_uncertainty.BO_surrogate_uncertainty`, com:
    (i) modelos INJETADOS (in-memory, sem `Models/iter_%d/*.ckpt`);
    (ii) `n_var=D`/`n_obj=2M` genéricos (stock: 30/4 hard-coded);
    (iii) **fix `[:, :M]`** (🔴 ARTIGO — o `[:, :2]` da linha 46 trunca M=3);
    (iv) `torch.no_grad()` (N.1.5/D86 — o stock constrói grafo e `.detach()`a).

    A aritmética do μ e da σ² é a do stock, termo a termo
    (BO_surrogate_function_uncertainty.py:37-43): μ = (1/10)Σ e
    σ² = (1/10)Σ(ŷ² − μ²) — variância POPULACIONAL ddof=0, em float32 (pode
    sair <0 residual — o clamp acontece SÓ na seleção/export, nunca aqui:
    o F da aquisição fica byte-fiel ao stock).
    """
    from pymoo.core.problem import Problem

    class _AcqProblem(Problem):
        def __init__(self):
            super().__init__(n_var=D, n_obj=2 * M, xl=0.0, xu=1.0)

        def _evaluate(self, design, out, *args, **kwargs):
            with torch.no_grad():
                designs = torch.tensor(design).float()
                batchsize = designs.shape[0]
                ens = torch.empty(K_ENSEMBLE, batchsize, M)
                for net_n in range(K_ENSEMBLE):
                    ens[net_n, :, :] = models[net_n](designs)
                mu = (1 / K_ENSEMBLE) * torch.sum(ens, 0)
                unc = (1 / K_ENSEMBLE) * torch.sum(
                    ens ** 2 - mu.repeat(K_ENSEMBLE, 1, 1) ** 2, 0)
                out["F"] = torch.cat(
                    (mu[:, :M], -unc[:, :M]), 1).numpy()   # fix [:, :M] 🔴

    return _AcqProblem()


def _calculate_pareto(problem, seed: int):
    """`calculate_pareto(models, seed)` — fork de
    `Acquisition_4_D.calculate_pareto_4_D` sem Oracle nem `Acquisition/*.mat`:
    NSGA-II defaults do pymoo (pop=1000, 100 ger, SBX 0.9/15, PM 0.9/20 com
    `prob_var` default `min(0.5, 1/D)` — decisão do autor 2026-07-22) e
    devolve `(res.X, res.F)` = o rank-0 da população final (≤pop).

    SEMPRE via `guarded_pymoo_minimize` (N.2.3 — cinto-e-suspensórios: o
    pymoo 0.6.2 medido NÃO desloca os RNGs globais, mas a guarda custa zero).
    """
    from pymoo.algorithms.moo.nsga2 import NSGA2

    algorithm = NSGA2(pop_size=POP_ACQ)               # Acquisition_4_D.py:17
    res = H.guarded_pymoo_minimize(problem, algorithm, ('n_gen', NGEN_ACQ),
                                   seed=int(seed), verbose=False)
    X = np.atleast_2d(np.asarray(res.X, dtype=np.float64))
    F = np.atleast_2d(np.asarray(res.F, dtype=np.float64))
    return X, F


# ═══════════════════════════════════════════════════════════════════════════
#  Reconstrução 3/3 — q=1 HVI-greedy(μ) (D41/D96 — regra NOSSA, FECHADA)
# ═══════════════════════════════════════════════════════════════════════════


def _hvi_greedy_d96(F_arc: np.ndarray, mu_nat: np.ndarray,
                    sig2_z: np.ndarray, rng_fallback) -> dict:
    """A regra FECHADA do D96. Devolve `{idx, caminho, hvi, hvi_top5, ...}`.

    - Normalização: min/max do arquivo OBSERVADO na iteração corrente (NUNCA o
      f_min/f_max da S.5 — vazaria o oráculo; o HVI cru degenera nos BBOB).
    - ref = nadir observado ×1,1 no espaço normalizado ⇒ (1.1, …, 1.1).
    - HVI(c) = HV(ND ∪ {c}) − HV(ND). Atalho EXATO (não aproximação): um
      candidato fracamente dominado pelo ND observado, ou fora da caixa do
      ref, tem HVI ≡ 0 — o HV só é computado para os sobreviventes.
    - Desempate (empate EXATO no HVI): maior σ² agregada em z (escala-neutra —
      somar σ² NATIVA deixaria o objetivo de maior escala dominar o desempate,
      a degenerescência que o próprio D96 mata; declarado no sigma_dict).
    - Fallback (tudo empatado — tipicamente todos HVI=0 e σ² igual): índice
      ALEATÓRIO entre os empatados, com o RNG do harness (uso_id=2/D91).
    """
    from pymoo.indicators.hv import HV

    M = F_arc.shape[1]
    fmin = F_arc.min(axis=0)
    fmax = F_arc.max(axis=0)
    rng_obj = np.maximum(fmax - fmin, 1e-12)          # guarda de range (S.5)
    A = (F_arc - fmin) / rng_obj
    C = (mu_nat - fmin) / rng_obj
    ref = np.full(M, HVI_REF, dtype=np.float64)

    nd = A[_nds_idx(A)]
    hv0 = float(HV(ref_point=ref)(nd))

    n = C.shape[0]
    hvi = np.zeros(n, dtype=np.float64)
    # atalho exato: dominado pelo ND (>= em tudo vs algum ponto) ou fora do ref
    for i in range(n):
        c = C[i]
        if np.any(c >= ref):
            continue
        if np.any(np.all(nd <= c, axis=1)):
            continue
        hvi[i] = float(HV(ref_point=ref)(np.vstack([nd, c]))) - hv0

    s2_agg = np.sum(np.maximum(sig2_z, 0.0), axis=1)  # clamp σ²<0 (float32)
    best = float(hvi.max())
    empatados = np.flatnonzero(hvi == best)
    if len(empatados) == 1:
        idx, caminho = int(empatados[0]), "hvi"
    else:
        s2_e = s2_agg[empatados]
        vence = empatados[s2_e == s2_e.max()]
        if len(vence) == 1:
            idx, caminho = int(vence[0]), "desempate_sigma"
        else:
            idx = int(vence[int(rng_fallback.integers(len(vence)))])
            caminho = "fallback_aleatorio"
    top5 = np.sort(hvi)[::-1][:5]
    return {"idx": idx, "caminho": caminho, "hvi": float(hvi[idx]),
            "hvi_top5": [float(v) for v in top5],
            "sigma2_agg_sel_z": float(s2_agg[idx]),
            "n_hvi_pos": int((hvi > 0).sum()), "n_empatados": len(empatados)}


def _nds_idx(F: np.ndarray) -> np.ndarray:
    from src import problems as _problems
    return np.asarray(_problems._nds_filter(np.asarray(F, dtype=np.float64)))


# ═══════════════════════════════════════════════════════════════════════════
#  Sonda — μ/σ DES-padronizados na escala nativa de f (L.14/A-02)
# ═══════════════════════════════════════════════════════════════════════════


def _sonda_predict(estado: dict, oracle: _Oracle, torch):
    """Gancho `predict(X)->(μ, σ)` do `emit_sonda_block` (pred_tipo='valor').

    Recebe (n, D) NATIVO → normaliza a [0,1] (o espaço do modelo) → forward do
    ensemble sob `no_grad` → DES-padroniza com o mean/std do refit da iteração
    CORRENTE: `μ_nat = μ_z·std + mean`, `σ_nat = sqrt(max(σ²_z, 0))·std`
    (A-02/DI-16.9: a coluna `sigma_*` carrega σ, NUNCA σ²). O forward do
    ensemble não consome RNG (eval, sem dropout), mas o `emit_sonda_block` o
    roda sob `preserve_all_rng()` de qualquer forma — o invariante §3.1 é
    provado por gate (① com sonda ≡ ① sem), não por inspeção.
    """
    def predict(X_nat: np.ndarray):
        models = estado["models"]
        mean, std = estado["z_mean"], estado["z_std"]
        X01 = oracle.to01(X_nat)
        with torch.no_grad():
            designs = torch.from_numpy(np.ascontiguousarray(X01)).float()
            ens = torch.empty(K_ENSEMBLE, designs.shape[0], len(mean))
            for net_n in range(K_ENSEMBLE):
                ens[net_n, :, :] = models[net_n](designs)
            mu_z = ((1 / K_ENSEMBLE) * torch.sum(ens, 0)).numpy()
            s2_z = ((1 / K_ENSEMBLE) * torch.sum(
                ens ** 2 - torch.from_numpy(mu_z).float()
                .repeat(K_ENSEMBLE, 1, 1) ** 2, 0)).numpy()
        mu_nat = mu_z.astype(np.float64) * std + mean
        sig_nat = np.sqrt(np.maximum(s2_z.astype(np.float64), 0.0)) * std
        return mu_nat, sig_nat

    return predict


# ═══════════════════════════════════════════════════════════════════════════
#  O RUNNER
# ═══════════════════════════════════════════════════════════════════════════


def run_c149(exp: str, alg: str, problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             teto_s: float | None = None,
             **_kwargs) -> dict:
    """Roda o LBN-MOBO sob o contrato v5.2.1. Assinatura padrão dos runners.

    `enable_bucket=False` por padrão: bucket-only (D54) vale do M8 em diante;
    no Mac, até o M7, camadas LOCAIS COMPLETAS sem podar a ③ (RI-08/DI-16.8).

    `teto_s` (opcional) = teto de wall-clock (padrão c122/D-07). Ao estourar:
    aborto LIMPO — curva parcial preservada (4 camadas gravadas), manifesto
    `failed` + `motivo_parada='teto_wall'` (reescrito APÓS o
    `write_run_outputs`, que carimba 'ok' hard-coded — lacuna conhecida do
    harness, sinalizada no handoff). O despachante já conhece o padrão
    WallClockAbort/failed não-retriável (D-07/DI-21).
    """
    import torch

    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)

    with _c149_runtime():
        return _run_c149_inner(exp, alg, problema, semente, torch=torch,
                               pinning=pinning, env=env, t_run=t_run,
                               data_root=data_root,
                               enable_bucket=enable_bucket, teto_s=teto_s)


def _run_c149_inner(exp, alg, problema, semente, *, torch, pinning, env, t_run,
                    data_root, enable_bucket, teto_s):
    from layer_config_forward import MultiLayerPerceptron_forward as MLP

    # ── determinismo (L.14) ─────────────────────────────────────────────────
    base = H.seed_base(alg, semente)                  # 1000·s (D22 — c149!)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)

    # ── orçamento + DoE do artefato (D63/D87/D88 — NUNCA regenerado) ────────
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    doe = H.load_doe(problema, semente, data_root=data_root)
    D = int(doe["X"].shape[1])
    bud = FEBudget(D=D, logger=log)
    oracle = _Oracle(problema, bud)
    M = oracle.n_obj
    if doe["X"].shape[0] != bud.n_init:
        raise RuntimeError(
            f"DoE com {doe['X'].shape[0]} pontos != 11D−1 = {bud.n_init} "
            f"— pára-e-loga (D81).")

    sonda = H.load_sonda(problema, regime="online", data_root=data_root)
    buf = H.SnapshotBuffer()

    ativacoes = ["tanh", "ReLU", "CELU", "LeakyReLU", "ELU",
                 "Hardswish", "tanh", "ReLU", "CELU", "LeakyReLU"]
    sigma_dict = {
        "modelo": f"deep ensemble K={K_ENSEMBLE} MLPs {D}->100->50->100->{M} "
                  f"(1a camada com ativacao distinta por rede — convencao da "
                  f"RAIZ), retreinado DO ZERO por iteracao (D43)",
        "pred_tipo": "valor — mu_*/sigma_* por objetivo",
        "mu": "media das K=10 predicoes, DES-padronizada do z-score da "
              "iteracao corrente (mu_nat = mu_z*std_j + mean_j) — escala "
              "NATIVA de f, minimizacao",
        "sigma": "desvio-padrao POPULACIONAL (ddof=0) ENTRE as K=10 redes, "
                 "computado em z e DES-padronizado (sigma_nat = "
                 "sqrt(max(sigma2_z,0))*std_j) — e a incerteza EPISTEMICA do "
                 "ensemble (Eq. 2b), NUNCA sigma2 (A-02/DI-16.9); "
                 "sigma2<0 residual do float32 e clampado a 0 (guard logado)",
        "espaco_modelo": "'cru' — os VALORES gravados sao des-padronizados; o "
                         "modelo opera em z (transf_tipo='zscore', "
                         "transf_params={mean,std} POR ITERACAO — DEF-C3: o "
                         "espaco z e reconstituivel por (mu-mean)/std)",
        "regime=online": "populacao final (rank-0, <=1000) do NSGA-II da "
                         "aquisicao 2M por iteracao (DEF-C2 'BO com EA "
                         "interno'); res.F da aquisicao = [mu_z, -sigma2_z] e "
                         "RECONSTITUIVEL destas linhas (mu_z=(mu-mean)/std; "
                         "sigma2_z=(sigma/std)^2)",
        "regime=sonda": "os 2000 pontos fixos do artefato, mesma semantica "
                        "mu/sigma acima, com o modelo da iteracao corrente; "
                        "colunas C3 carimbadas pelo runner (o emit do "
                        "harness nao as aceita — lacuna sinalizada)",
        "real_solution_id": "preenchido SO na linha do escolhido pelo "
                            "HVI-greedy (unico que vira FE; em cache-hit "
                            "aponta a solucao PREEXISTENTE — D89/DI-21)",
        "fe_treino_max": "n_treino-1 no momento do fit — o treino e o arquivo "
                         "INTEIRO (init+infills, dedup D57): MONOTONICO",
        "selecao_q1": "HVI-greedy(mu) D96 FECHADA: HVI em objetivos "
                      "normalizados pelo min/max do arquivo OBSERVADO da "
                      "iteracao; ref=nadir_obs*1.1 normalizado; desempate="
                      "maior sigma2 agregada EM Z (escala-neutra, declarado); "
                      "fallback=aleatorio-do-front com RNG do harness (uso 2)",
    }
    params = {
        "K": K_ENSEMBLE, "arch": f"{D}->100->50->100->{M}",
        "ativacoes_raiz": ativacoes,
        "init": "N(0, 1e-3^2), bias 0", "loss": "sum_mse",
        "adam": {"lr0": LR0, "decay_por_epoca": LR_DECAY},
        "epocas": EPOCHS, "batch": BATCH,
        "split": "90/10 sem shuffle; seed = 1000*s + net_n + 1 (D22/A6 "
                 "sobre o manual_seed(net_n+1) do stock)",
        "nsga2_acq": {"pop": POP_ACQ, "n_gen": NGEN_ACQ,
                      "sbx": {"prob": 0.9, "eta": 15},
                      "pm": {"prob": 0.9, "eta": 20,
                             "prob_var": f"default pymoo min(0.5, 1/D) = "
                                         f"{min(0.5, 1.0 / D):.6g}",
                             "decisao": "autor 2026-07-22 — o repo nao passa "
                                        "operador; a nota SPEC:722 '1/30 "
                                        "hard-coded' e factualmente incorreta "
                                        "(medido no env_main)"},
                      "seed": "iteration_seed(base, 12, g, uso=1) por "
                              "iteracao (SPEC §22.4·3.4 'h(s,iter,run)'; ver "
                              "docstring USO_NSGA2 — unica leitura sem "
                              "livelock no cache-hit D89)"},
        "q": 1, "regra_q1": "HVI-greedy(mu) D41/D96 (NOSSA, declarada)",
        "z_score": "por objetivo, refit por iteracao, ddof=0 (NOSSA B13.4 "
                   "declarada; precedente: o autor normaliza Y no Airfoil)",
        "fix_M": "[:, :M] (ARTIGO — BO_surrogate...py:46 truncava M=3)",
        "espaco_busca_interno": "[0,1] (stock); desnormalizacao xl+X01*(xu-xl) "
                                "SO no adapter (L.14)",
        "seed_base": f"1000*semente = {base} (D22 — SEED_OFFSET_ALGS)",
        "torch_default_dtype": "float32 (FORCADO pelo codigo — .float() em "
                               "Forward_BNN:50/BO_surrogate:30; float64 "
                               "levanta RuntimeError; N.1.1/DI-21)",
        "cache_cap": CACHE_CAP,
        "retreino": "do zero, K*60 epocas/iteracao — ACEITO, medido (D43)",
    }

    n_cache_infill = n_cache_seguidos = n_clamp_sigma2 = 0
    abortar_cache = False        # [DI-24] o break do cache-cap sai APOS a ④ fechar
    g = 0
    status, motivo_parada = "ok", "orcamento"
    t_fit_total = t_busca_total = t_sonda_total = 0.0
    ultima_sonda_g = None
    models = None
    estado_sonda: dict = {}
    rng_fallback_cache: dict = {}

    def _rng_fallback(it: int):
        """RNG do harness p/ o fallback D96 — derivado POR ITERAÇÃO (uso 2),
        lazy (só quando o fallback dispara; consumo zero fora dele)."""
        if it not in rng_fallback_cache:
            rng_fallback_cache.clear()
            rng_fallback_cache[it] = np.random.Generator(np.random.PCG64(
                H.iteration_seed(base, ALG_ID, it, USO_NP_HARNESS)))
        return rng_fallback_cache[it]

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="online", maxfe=bud.maxfe,
                   n_init=bud.n_init, doe_hash=doe["doe_hash"],
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   params=params,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"])

        # ── init: o DoE do artefato, bit-a-bit, na ORDEM do arquivo (D88) ───
        for x in doe["X"]:
            oracle.eval_native(x)

        # ── laço principal — dirigido pelo bud.fe (a fonte ÚNICA, D89) ──────
        while bud.fe < bud.maxfe:
            g += 1
            t_g0 = time.time()

            # treino = o arquivo REAL inteiro (fonte única: bud.records; em
            # cache-hit ele NÃO cresce — o hazard c122 §5.3 morre por construção)
            X_nat = np.vstack([r.x for r in bud.records])
            Y_nat = np.vstack([r.f for r in bud.records])
            n = X_nat.shape[0]
            if n < N_MIN_SPLIT:
                log.guard("split_quebrado", geracao=g, n=n,
                          motivo=f"n<{N_MIN_SPLIT} quebra o split 90/10")
                raise RuntimeError(
                    f"n={n} < {N_MIN_SPLIT} — split 90/10 inviável. "
                    f"Pára-e-loga (D81).")
            X01 = oracle.to01(X_nat)
            z_mean = Y_nat.mean(axis=0)
            z_std = Y_nat.std(axis=0, ddof=0)
            dege = z_std < 1e-12
            if np.any(dege):
                z_std = np.where(dege, 1.0, z_std)
                log.guard("zscore_std_degenerada", geracao=g,
                          objetivos=[int(j) for j in np.flatnonzero(dege)],
                          acao="std_j := 1.0 (objetivo constante no arquivo)")
            Yz = (Y_nat - z_mean) / z_std

            # ── fit: ensemble K=10 do zero (D43) ────────────────────────────
            t_f0 = time.time()
            torch.manual_seed(H.iteration_seed(base, ALG_ID, g,
                                               USO_TORCH_ITER, bits32=True))
            models = []
            val_mses = []
            for net_n in range(K_ENSEMBLE):
                m_, vmse, n_tr, n_val = _bnn_diverse_func(
                    net_n, X01, Yz, D, M,
                    seed=base + net_n + 1,            # 1000·s + net_n+1 (A6)
                    torch=torch, MLP=MLP)
                models.append(m_)
                val_mses.append(vmse)
            t_fit = time.time() - t_f0
            t_fit_total += t_fit
            fe_treino_max = n - 1
            buf.set_fe_treino_max(fe_treino_max)
            buf.add_timing(geracao=g, n_acumulado=n, tempo_fit_s=t_fit)
            estado_sonda.update(models=models, z_mean=z_mean, z_std=z_std,
                                ftm=fe_treino_max)
            log.event("fit", geracao=g, n_treino=n, epocas=EPOCHS,
                      tempo_fit_s=round(t_fit, 6), fe_treino_max=fe_treino_max,
                      val_mse=[_f(v) for v in val_mses],
                      z_mean=[_f(v) for v in z_mean],
                      z_std=[_f(v) for v in z_std])

            # sonda DEPOIS do fit, ANTES da decisão: mede o modelo COM QUE
            # esta iteração decide (k lido dinamicamente — teste §3.1)
            t_snd = 0.0
            if H.sonda_due(g, k=H.SONDA_K):
                t_snd = H.emit_sonda_block(
                    buf, log, geracao=g, fe=bud.fe, sonda=sonda,
                    predict=_sonda_predict(estado_sonda, oracle, torch),
                    fe_treino_max=fe_treino_max, pred_tipo="valor",
                    modelo_flag=f"BNN-ensemble(K={K_ENSEMBLE})",
                    motivo=f"cadencia k={H.SONDA_K} (g=1,2,4,6,…)")
                _stamp_c3_sonda(buf, sonda["S"], z_mean, z_std)
                t_sonda_total += t_snd
                ultima_sonda_g = g

            # ── busca: NSGA-II 2M + HVI-greedy (D96) ───────────────────────
            t_b0 = time.time()
            seed_nsga2 = H.iteration_seed(base, ALG_ID, g, USO_NSGA2,
                                          bits32=True)
            problem = _make_acq_problem(models, D, M, torch)
            cand_X01, cand_F = _calculate_pareto(problem, seed_nsga2)
            mu_z = cand_F[:, :M]
            sig2_z = -cand_F[:, M:]                   # F guarda −σ² (stock)
            n_neg = int((sig2_z < 0).sum())
            if n_neg:
                n_clamp_sigma2 += n_neg
                log.guard("sigma2_negativa_float32", geracao=g, n=n_neg,
                          min=_f(float(sig2_z.min())),
                          acao="clamp a 0 na selecao/export (aquisicao "
                               "intocada — fiel ao stock)")
            mu_nat = mu_z * z_std + z_mean
            sig_nat = np.sqrt(np.maximum(sig2_z, 0.0)) * z_std
            F_arc = Y_nat                              # o arquivo OBSERVADO
            sel = _hvi_greedy_d96(F_arc, mu_nat, sig2_z,
                                  _rng_fallback(g))
            i_sel = sel["idx"]
            t_busca = time.time() - t_b0
            t_busca_total += t_busca

            # ── 1 FE: o escolhido (dedup D89 no FEBudget) ───────────────────
            x_sel_nat = oracle.to_native(cand_X01[i_sel])
            dist_min = _dist_min(x_sel_nat, X_nat)
            fe_antes = bud.fe
            oracle.eval_native(x_sel_nat)
            sid = bud.solution_id_of(x_sel_nat)
            cache_hit = (bud.fe == fe_antes)
            if cache_hit:
                # [DI-21/c122 §5.3 — o hazard gêmeo, morto por construção]: o
                # treino sai de bud.records, que NÃO cresce no cache-hit. A ③
                # continua gravada (a predição FOI decisão-relevante), com
                # real_solution_id da solução PREEXISTENTE. Cap p/ hits
                # consecutivos: o orçamento não avança — pára-e-loga.
                n_cache_infill += 1
                n_cache_seguidos += 1
                log.guard("cache_hit_infill", geracao=g, solution_id=sid,
                          fe=bud.fe, seguidos=n_cache_seguidos,
                          motivo="o HVI-greedy reescolheu uma X ja avaliada "
                                 "(bit-a-bit) — 0 FE (D89); o treino NAO "
                                 "cresce")
                if n_cache_seguidos >= CACHE_CAP:
                    # [DI-24/achado §4.3 do e81] NAO dar break aqui: a linha da
                    # ④ desta geracao ja foi aberta (add_timing) e sairia com 3
                    # NULLs que o proprio gate reprova. Seta o aborto e deixa a
                    # iteracao fechar ③/②/④ — o break vem apos o update_timing.
                    status, motivo_parada = "failed", "cache_hit_travado"
                    log.guard("cache_hit_travado", geracao=g, fe=bud.fe,
                              seguidos=n_cache_seguidos,
                              acao="ABORTO — o orcamento nao avanca; "
                                   "para-e-loga (D81)")
                    abortar_cache = True
            else:
                n_cache_seguidos = 0

            # ── ③ BUSCA: a população final da aquisição (DEF-C2), μ/σ nat ──
            for i in range(cand_X01.shape[0]):
                buf.add_surrogate(_export.surrogate_row(
                    g, oracle.to_native(cand_X01[i]),
                    regime="online",
                    real_solution_id=(sid if i == i_sel else None),
                    mu=mu_nat[i], sigma=sig_nat[i],
                    pred_tipo="valor",
                    modelo_flag=f"BNN-ensemble(K={K_ENSEMBLE})",
                    espaco_modelo="cru",
                    transf_tipo="zscore",
                    transf_params={"mean": [float(v) for v in z_mean],
                                   "std": [float(v) for v in z_std]}))
            # ② membership: o arquivo REAL corrente (o "estado" do BO —
            # precedente c262; o c149 não tem outra população real)
            buf.add_pop(g, [r.solution_id for r in bud.records])

            # ── ④ + ⑥ ──────────────────────────────────────────────────────
            buf.update_timing(g, tempo_busca_s=t_busca,
                              tempo_pred_sonda_s=t_snd,
                              tempo_geracao_s=(time.time() - t_g0) - t_snd)
            F_arc_pos = np.vstack([r.f for r in bud.records])
            log.decision(
                caminho=f"c149_gen:{sel['caminho']}",
                motivo=f"HVI-greedy D96 (q=1) sobre {cand_X01.shape[0]} "
                       f"candidatos do front 2M",
                geracao=g, seed_nsga2=int(seed_nsga2),
                n_front_acq=int(cand_X01.shape[0]),
                hvi_escolhido=_f(sel["hvi"]),
                hvi_top5=[_f(v) for v in sel["hvi_top5"]],
                n_hvi_pos=sel["n_hvi_pos"], n_empatados=sel["n_empatados"],
                sigma2_agg_sel_z=_f(sel["sigma2_agg_sel_z"]),
                std_ensemble_sel=[_f(v) for v in sig_nat[i_sel]],
                mu_sel_nat=[_f(v) for v in mu_nat[i_sel]],
                acq_resF_mu_z_min=[_f(v) for v in mu_z.min(axis=0)],
                acq_resF_mu_z_max=[_f(v) for v in mu_z.max(axis=0)],
                acq_resF_sigma2_z_max=[_f(v) for v in sig2_z.max(axis=0)],
                n_clamp_sigma2_iter=n_neg,
                cache_hit=bool(cache_hit), solution_id=sid,
                **H.minimo_comum_di10(
                    F_arc_pos, fe=bud.fe,
                    modelo_hp={"val_mse": [_f(v) for v in val_mses],
                               "epocas": EPOCHS,
                               "arch": f"{D}->100->50->100->{M}",
                               "lr0": LR0, "lr_decay": LR_DECAY,
                               "batch": BATCH, "n_train": n_tr,
                               "n_val": n_val},
                    tempo_fit_s=t_fit, tempo_busca_s=t_busca,
                    dist_min_arquivo=dist_min))

            # ── higiene D86 (p/ o c149 é sobrevivência, não estilo) ────────
            del problem, cand_X01, cand_F, mu_z, sig2_z, mu_nat, sig_nat
            H.iteration_cleanup()

            # [DI-24/achado §4.3 do e81] o aborto do cache-cap sai AQUI, com a
            # ④/③/②/⑥ desta geracao COMPLETAS (o break no sitio deixava a ④
            # com 3 NULLs que o proprio gate reprova).
            if abortar_cache:
                break

            if teto_s is not None and (time.time() - t_run) > teto_s:
                status, motivo_parada = "failed", "teto_wall"
                log.guard("teto_wall", geracao=g, fe=bud.fe,
                          decorrido_s=round(time.time() - t_run, 1),
                          teto_s=teto_s,
                          acao="ABORTO LIMPO — curva parcial preservada; "
                               "manifesto failed (D-07); a decisao de "
                               "completar e do M7 (D81)")
                break

    except BudgetExhausted:
        # Fim NATURAL (D61) — o laço já para em bud.fe == maxfe; rede de
        # segurança do hard-stop exato.
        log.guard("hard_stop_capturado", fe=bud.fe, maxfe=bud.maxfe,
                  motivo="fim natural do orcamento (D61)")
    except Exception as exc:                          # pragma: no cover
        status, motivo_parada = "failed", f"{type(exc).__name__}: {exc}"
        log.footer(status="failed", fe_final=bud.fe, erro=motivo_parada)
        log.close()
        raise

    # ── sonda final (fora do try do laço p/ rodar também pós-BudgetExhausted)
    if g and ultima_sonda_g != g and models is not None:
        # fe_treino_max do bloco final = o do ÚLTIMO fit (o modelo é o da
        # última iteração; o infill final NUNCA entra em treino — honesto,
        # e a coluna diz exatamente o que o modelo viu):
        ftm_final = estado_sonda.get("ftm")
        buf.set_fe_treino_max(ftm_final)
        t_snd = H.emit_sonda_block(
            buf, log, geracao=g, fe=bud.fe, sonda=sonda,
            predict=_sonda_predict(estado_sonda, oracle, torch),
            fe_treino_max=ftm_final, pred_tipo="valor",
            modelo_flag=f"BNN-ensemble(K={K_ENSEMBLE})",
            motivo="ultima geracao (§3.1/finalProbe)")
        _stamp_c3_sonda(buf, sonda["S"],
                        estado_sonda["z_mean"], estado_sonda["z_std"])
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
            sonda_info={"S": sonda["S"], "regime": "online",
                        "cadencia": f"online: k={H.SONDA_K} (g=1,2,4,6,…) + "
                                    f"1a e ultima (finalProbe)",
                        "n_blocos": _n_blocos(buf, sonda["S"]),
                        "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]},
            data_root=data_root, enable_bucket=enable_bucket)
        # `write_run_outputs` carimba status='ok' hard-coded (lacuna do
        # harness, sinalizada no handoff): acrescenta-se `motivo_parada` e,
        # num aborto (teto/cache-cap), o status vira `failed` NO SÍTIO —
        # o padrão D-07 feito certo (o c122 prometia isto no docstring mas
        # o manifesto dele sai 'ok'; ver REPASSE §definições).
        man = res["manifest"]
        man["motivo_parada"] = motivo_parada
        if status != "ok":
            man["status"] = "failed"
        _manifest.write_manifest(man, data_root)
        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=g,
                   motivo_parada=motivo_parada, n_front1=n_front1,
                   n_cache_infill=n_cache_infill,
                   n_clamp_sigma2=n_clamp_sigma2)
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_geracoes": g,
        "cp_init_ok": bool(res["cp_init_ok"]), "status": status,
        "motivo_parada": motivo_parada,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows),
        "n_blocos_sonda": _n_blocos(buf, sonda["S"]), "regime": "online",
        "cache_hits": bud.cache_hits, "n_cache_infill": n_cache_infill,
        "n_clamp_sigma2": n_clamp_sigma2, "n_front1": n_front1,
        "tempo_pred_sonda_s": t_sonda_total,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Auxiliares
# ═══════════════════════════════════════════════════════════════════════════


def _stamp_c3_sonda(buf, S: int, z_mean: np.ndarray, z_std: np.ndarray) -> None:
    """Carimba as colunas C3 (DEF-C3) nas S linhas do bloco de sonda RECÉM
    emitido: os μ/σ da sonda também são DES-padronizados (cru), e os params
    do z-score da iteração pertencem a TODA linha — `emit_sonda_block` não
    aceita as C3 (lacuna do harness, sinalizada no handoff), então o runner
    completa as linhas do SEU buffer. A ORDEM do bloco fica intacta."""
    import json as _json
    params = _json.dumps({"mean": [float(v) for v in z_mean],
                          "std": [float(v) for v in z_std]},
                         ensure_ascii=False)
    for row in buf.surr_rows[-S:]:
        assert row.get("regime") == "sonda", "bloco de sonda esperado"
        row["espaco_modelo"] = "cru"
        row["transf_tipo"] = "zscore"
        row["transf_params"] = params


def _dist_min(x_nat: np.ndarray, X_arc_nat: np.ndarray) -> float | None:
    """`dist_min_arquivo` (B3/DI-10) — NATIVO, vs o arquivo ANTERIOR ao FE."""
    if X_arc_nat.shape[0] == 0:
        return None
    return float(np.min(np.linalg.norm(
        X_arc_nat - np.asarray(x_nat, dtype=np.float64), axis=1)))


def _n_blocos(buf, S: int) -> int:
    return sum(1 for r in buf.surr_rows if r.get("regime") == "sonda") // S


def _f(v):
    """float() tolerante a None/NaN — o jsonl não carrega NaN cru."""
    if v is None:
        return None
    v = float(v)
    return None if not np.isfinite(v) else round(v, 6)


__all__ = ["run_c149", "ALG_ID", "ALGO_VERSION"]
