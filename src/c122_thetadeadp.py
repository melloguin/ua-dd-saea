"""[R3-c122] θ-DEA-DP (Yuan et al.) sobre o `standalone_harness` — regime ONLINE.

O 1º algoritmo da Rodada 3. Nasce NATIVO no contrato de dados v5.2.1 (sonda,
`fe_treino_max`, timing completo, jsonl DI-10) — não há retrofit depois.

**O mecanismo (I.6/M.12).** Duas FNNs 2×200 ReLU com saída softmax-3 sobre PARES
concatenados `[x_i, x_j]` no espaço de DECISÃO — Pareto-Net (dominância) e
θ-Net (θ-dominância PBI, θ=5) — usadas SEMPRE em conjunto:

  ① *estágio 1 (triagem)*: os `N*=7000` offsprings são preditos contra o
    representante do cluster corrente (`nn_predict_dom_inter`, 7000×1 por rede) e
    caem em 3 categorias por ACORDO das duas redes — Q1 `ps` (ambas dominam),
    Q2 `s` (θ-domina, Pareto-não-dominado), Q3 `p` (Pareto-domina,
    θ-não-dominado). Cada categoria é truncada a `Q_max=300` pelo score inter
    `scf = p_cfs + s_cfs`.
  ② *estágio 2 (escolha)*: dentro da PRIMEIRA categoria não-vazia (Q1≻Q2≻Q3),
    `e(z) = Σ_j I(z ≻ j)·p̂(z,j)` somado sobre as 2 redes
    (`nn_predict_dom_intra`, O(k²) com k≤300) e `z* = argmax e(z)` → **1 FE**.

A survival selection usa fitness **REAL** (`sel_scalar_dea`): o surrogate nunca
substitui a avaliação — ele só decide QUEM gasta FE (preseleção pura).

**O que este módulo faz — e o que NÃO faz.** Ele é um FORK INSTRUMENTADO do
`examples/tdeadp_main.py` + do laço `scalar_dom_ea_dp`. O repo oficial em
`algorithms/c122_θ-DEA-DP/` fica **INTOCADO** (zero patches, D30): tudo o que o
cartão pedia como "patch" ou já é ponto de extensão do próprio código, ou é
resolvido aqui fora. Ver `handoff/R3-c122.md` §patches.

**Fidelidade = validação MANUAL do autor, em lote (D97).** Este módulo
instrumenta e aplica o gate objetivo; NUNCA julga nem auto-conserta fidelidade.
"""

from __future__ import annotations

import contextlib
import math
import os
import random
import sys
import time

# ⚠ ORDEM: o `standalone_harness` pina as env vars de thread (D79/N.1.1) no TOPO
# do módulo, ANTES de qualquer `import numpy`. Importá-lo primeiro é o que faz o
# pinning valer neste processo.
from src import standalone_harness as H

import numpy as np

from src import export as _export
from src import metrics as _metrics
from src import naming
from src.budget import BudgetExhausted, FEBudget

# ── Identidade e constantes do config ───────────────────────────────────────

#: `alg_id` canônico do c122 — `claude_code_context/artifacts/seeds.json:alg_id`
#: (D62/D91). NÃO é um inteiro livre: há teste que o compara com o artefato.
ALG_ID = 5

#: `uso_id` do c122 (D62). O c122 semeia **UMA VEZ por run** (`iteracao=0`): as
#: 3 streams (stdlib `random` p/ DEAP+PerCounter, `np.random`, `torch`) correm
#: CONTÍNUAS pelo run inteiro — re-semear por iteração destruiria a trajetória
#: do SBX/PM e do shuffle de minibatch. Por isso o catálogo é por STREAM.
USO_TORCH = 0
USO_RANDOM = 1
USO_NUMPY = 2

ALGO_VERSION = "c122-thetadeadp-1.0"

#: Nome da pasta do repo oficial (com o θ no nome — é assim no disco).
REPO_DIRNAME = "c122_θ-DEA-DP"

# ── Parâmetros — Balde B (código oficial). O Balde C NÃO se aplica ao c122. ──
LAMBDA = 7000          #: N* — pool de candidatos por iteração (tdeadp_main.py:44)
CXPB = 1.0             #: probabilidade de cruzamento (tdeadp_main.py:45)
MUTPB = 1.0            #: probabilidade de mutação (tdeadp_main.py:46)
ETA_C = 30.0           #: disC do SBX (tdeadp_main.py:79) — filhos colados aos pais
ETA_M = 20.0           #: disM do PM (tdeadp_main.py:82)
CATEGORY_SIZE = 300    #: Q_max (tdeadp_main.py:64)
E_INIT = 20            #: épocas do 1º treino (model_init default)
HIDDEN = 200           #: largura das camadas ocultas (model.py default)
N_HIDDEN = 2           #: nº de camadas ocultas — FNN 2×200 ReLU
ACC_THR = 0.9          #: γ — gate do warm-start, `min_acc >= 0.9` ⇒ ZERO épocas
LR = 1e-3
BATCH_SIZE = 32
WEIGHT_DECAY = 1e-5

#: Cap anti-spin (fork do laço) — `algorithms.py:44-45` faz `continue` SEM cap
#: quando as 3 categorias saem vazias, e cada retry regenera 7000 offsprings
#: sem gastar 1 FE. O paper é fiel ao re-sample sem cap (fn. 6); o cap é um
#: **desvio de segurança DECLARADO** (E.7: "► 10 tentativas → fallback melhor
#: p_sum"). Cada disparo é LOGADO — hazard conhecido, não conserto silencioso.
SPIN_MAX = 10

#: Quantas linhas da ③-BUSCA por iteração — a CABEÇA do ranking [P3/DI-16.3,
#: opção A+ ratificada pelo autor]. Ver `_ez_rows` para a semântica exata.
TOP_BUSCA = 100


# ═══════════════════════════════════════════════════════════════════════════
#  DEF-B11.1 — f_min/f_max por problema, entregues PELA ASSINATURA
# ═══════════════════════════════════════════════════════════════════════════

def f_limits(problema: str) -> tuple[np.ndarray, np.ndarray]:
    """Os `f_min`/`f_max` FIXOS do problema (DEF-B11.1) — S.5 + margem de 10%.

    **Por que é patch OBRIGATÓRIO.** `scalar_dom_ea_dp` já aceita `f_min`/`f_max`
    na assinatura (`evolution/algorithms.py:7-8`), mas `tdeadp_main.py:135`
    **não os passa** — então `init_obj_limits` (`evolution/utils.py:22-29`)
    default-a para `f_min=0`, `f_max=f_min+1`, e a "normalização" vira a
    IDENTIDADE. O paper DECLARA normalização à la ParEGO com os limites do
    problema (§III-A); com 0/1 implícito o PBI/clustering colapsa em qualquer
    escala ≠ [0,1] (o f₁ do BBOB F17 vive em 10⁷). Sem este patch **o código
    viola o próprio paper**.

    **Vantagem informacional DECLARADA (D73b):** os limites vêm dos fronts
    VERDADEIROS — informação que um otimizador real não teria. Registrada no
    manifesto (`params.f_limits_fonte`) e no handoff.

    **Sem tocar o core:** a entrega é pela ASSINATURA, no ponto de chamada.

    Fórmula de uso (S.5, `00_fundacao/05_problemas.md:57`)::

        f_min     = ideal do front verdadeiro
        f_max_uso = nadir_front + 0,1·(nadir_front − f_min)

    A margem de 10% (🟢 escolha nossa, consistente com o ref-point do HV em
    espaço normalizado — D69) acomoda os pontos PIORES que o front que dominam
    o início da busca; sem ela os `f` normalizados do DoE estourariam ≫1 e o PBI
    ficaria dominado por outliers. Guarda `range ≥ 1e-12` (S.5).

    REUSA a tabela S.5 congelada em `src/metrics.py:F_MIN_MAX` — a MESMA fonte
    que a métrica oficial usa (D69). Duplicá-la aqui criaria duas verdades.
    """
    ideal, nadir = _metrics.reference_bounds(problema)
    rng = np.maximum(nadir - ideal, 1e-12)
    return ideal.astype(np.float64), (nadir + 0.1 * rng).astype(np.float64)


# ═══════════════════════════════════════════════════════════════════════════
#  Bypass do factory + stub do visualizer
# ═══════════════════════════════════════════════════════════════════════════

def _repo_root() -> str:
    return os.path.join(H.ROOT, "algorithms", REPO_DIRNAME)


@contextlib.contextmanager
def _c122_runtime():
    """Contexto de import do repo oficial + o dtype que o código dele exige.

    **Bypass do factory (S.8).** `problems/factory.py:3` importa `pymop.factory`,
    e `problems/{dtlz1,wfg}.py` importam `pymop`/`autograd`/`optproblems` —
    imports DUROS que o env-main não tem (o factory foi removido do env de
    propósito). **Nós nunca importamos `problems/`**: `evolution/` e `learning/`
    NÃO dependem dele (verificado — nenhum `from problems…` nos dois pacotes),
    então o bypass é completo e não exige cortar `problems/wfg.py`. Os nossos
    25 problemas entram pelo `_Adapter`.

    **Stub do visualizer.** `evolution/selection.py:9` importa
    `evolution/visualizer.py`, que faz `import matplotlib.pyplot` no topo (import
    DURO, resolve porque o matplotlib está no env). Dupla proteção:
    `MPLBACKEND=Agg` (nunca abre janela / nunca bloqueia em `plt.show()`) **e**
    a substituição de `visualize_preselection` por um no-op. O motivo real de
    desligar não é estética: `visualize_preselection` **avalia a função verdadeira
    fora do contador** (vazamento de FE, só em M=2) e BLOQUEIA em `plt.show()`.
    Nosso fork nunca o chama (passa `visualization=False`), mas o stub garante
    que uma reintrodução acidental não gaste FE nem trave a bateria.

    **dtype float32 — FORÇADO PELO CÓDIGO, não é escolha (D29 🟠 impl→código).**
    `pin_runtime()` deixa o default do torch em float64 (N.1.1), mas o c122 é
    float32-nativo: `learning/prediction.py:24` faz `torch.tensor(data).float()`
    explicitamente. Com pesos float64 × entrada float32 o forward levanta
    `RuntimeError: mat1 and mat2 must have the same dtype` — MEDIDO, não
    estimado. O default é restaurado na saída do contexto; o estado vai ao
    manifesto (`params.torch_default_dtype`).
    """
    import torch

    root = _repo_root()
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"repo oficial do c122 ausente: {root} — pára-e-loga (D81).")
    os.environ.setdefault("MPLBACKEND", "Agg")

    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    dtype_ant = torch.get_default_dtype()
    torch.set_default_dtype(torch.float32)
    try:
        for proibido in ("pymop", "optproblems", "autograd"):
            if proibido in sys.modules:                       # pragma: no cover
                raise RuntimeError(
                    f"{proibido!r} carregado — o bypass do factory falhou "
                    f"(S.8). Pára-e-loga (D81).")
        from evolution import selection as _sel
        _sel.visualize_preselection = _no_op_visualizer       # stub (FE leak)
        yield
    finally:
        torch.set_default_dtype(dtype_ant)
        if added and root in sys.path:
            sys.path.remove(root)


def _no_op_visualizer(*_a, **_kw) -> None:
    """Stub do `visualize_preselection` — ver `_c122_runtime`."""
    return None


def _fresh_creator(n_obj: int):
    """`creator` do DEAP NOVO por run — o estado global do DEAP VAZA entre runs.

    `creator.create` registra a classe como ATRIBUTO DE MÓDULO do `deap.creator`;
    um 2º run no mesmo processo (a bateria!) herdaria o `FitnessMin` do run
    anterior, com `weights` do M ERRADO se o problema mudar de M — e sem erro
    nenhum. Apagamos e recriamos.
    """
    from deap import base, creator
    for nome in ("Individual", "FitnessMin"):
        if hasattr(creator, nome):
            delattr(creator, nome)
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,) * int(n_obj))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    return creator


# ═══════════════════════════════════════════════════════════════════════════
#  Adapter (L.6) — o problema do estudo com a cara que o driver espera
# ═══════════════════════════════════════════════════════════════════════════

class _Adapter:
    """Objeto `n_var/n_obj/xl/xu/name` + `evaluate(lista de Individuals)→(N,M)`.

    **TODA avaliação real passa pelo `FEBudget`** — o driver NUNCA avalia direto:
    cache-hit = 0 FE (D89), a 31D-ésima X inédita levanta `BudgetExhausted`
    (hard-stop exato, D21/D61). O `x` chega em espaço NATIVO (os `Individual` do
    DEAP SÃO listas de variáveis nativas; o `[−1,1]` vive só em
    `ind.normalized_var`, para a entrada das redes).
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

    def evaluate(self, individuals) -> np.ndarray:
        """`(N, M)` float64 — a fitness VERDADEIRA de minimização."""
        t0 = time.time()
        out = []
        for ind in individuals:
            x = np.asarray(list(ind), dtype=np.float64)
            out.append(self._bud.evaluate(x, self._true_f))
        self.tempo_aval_real_s += time.time() - t0
        return np.asarray(out, dtype=np.float64)


class _Shim:
    """Portador mínimo de `normalized_var` para as chamadas de predição.

    `nn_predict_dom_inter` só lê `.normalized_var` (uma lista); construir
    `Individual` do DEAP para os 2.000 pontos da sonda seria caro e sujaria o
    `creator`. Este shim é usado SOMENTE na sonda — nunca na busca.
    """
    __slots__ = ("normalized_var",)

    def __init__(self, normalized_var):
        self.normalized_var = normalized_var


# ═══════════════════════════════════════════════════════════════════════════
#  Filtro instrumentado (fork fiel) — o cerne da telemetria
# ═══════════════════════════════════════════════════════════════════════════

def _conf_max_sem_diagonal(*mats: np.ndarray) -> np.ndarray:
    """max-softmax por linha, IGNORANDO a diagonal.

    `nn_predict_dom_intra` inicializa `conf_matrix = np.ones(...)` e nunca
    escreve a diagonal (`prediction.py:11-12`, laço `j = i+1`), então
    `conf[i,i] == 1.0` é LIXO — não é uma predição. Incluí-lo faria a confiança
    de TODA linha valer 1,0 e a coluna `pred_confianca` da ③ ficaria constante.
    """
    empilhado = np.stack([np.array(m, dtype=np.float64, copy=True) for m in mats])
    n = empilhado.shape[-1]
    if empilhado.shape[-2] == n:                      # matriz intra (quadrada)
        idx = np.arange(n)
        empilhado[:, idx, idx] = -np.inf
    v = empilhado.max(axis=(0, 2))
    return np.where(np.isfinite(v), v, np.nan)


def _e_of_z(individuals, p_net, s_net, device) -> tuple[np.ndarray, np.ndarray]:
    """`e(z)` e a max-softmax do conjunto — fork FIEL de `select_best_individual`.

    Replica `evolution/selection.py:158-166` termo a termo::

        p_conf[p_label != 1] = 0        # I(z ≻ j)
        s_conf[s_label != 1] = 0
        e(z) = Σ_j p_conf + Σ_j s_conf  # as 2 redes somadas

    Devolve `(e_z, conf_max)`. As matrizes CRUAS (pré-máscara) alimentam a
    confiança — a máscara zera justamente as entradas que ainda informam quão
    seguro o modelo estava.
    """
    from learning.prediction import nn_predict_dom_intra

    mats = []
    e_z = np.zeros(len(individuals), dtype=np.float64)
    for net in (p_net, s_net):
        if net is None:
            continue
        lab, conf = nn_predict_dom_intra(individuals, net, device)
        mats.append(conf)
        mascarado = np.array(conf, dtype=np.float64, copy=True)
        mascarado[lab != 1] = 0.0
        e_z += np.sum(mascarado, axis=1)
    if not mats:
        return e_z, np.full(len(individuals), np.nan)
    return e_z, _conf_max_sem_diagonal(*mats)


def _filtro_instrumentado(offsprings, rep_individuals, nd_rep_individuals,
                          p_net, s_net, max_size, device, ref_points, counter):
    """Fork INSTRUMENTADO de `pareto_scalar_nn_filter` (`selection.py:15-48`).

    Mesma sequência de chamadas e o MESMO consumo de RNG que o original — o
    `tests/test_c122.py` prova a equivalência da ESCOLHA contra as funções stock.
    `visualization` não existe aqui: o fork nunca visualiza (ver `_c122_runtime`).

    Devolve `(best_ind, tel)` — `tel` carrega o que a ③ e o jsonl precisam e o
    original joga fora.
    """
    from evolution.selection import (find_candidate_individuals,
                                     find_distinct_individuals, truncate)
    from evolution.utils import get_pareto_rep_ind
    from learning.prediction import nn_predict_dom_inter

    cid = counter()
    s_rep_ind = rep_individuals.get(cid)
    tel: dict = {"cid": int(cid), "n_pool": len(offsprings),
                 "ramo": None, "n_q1": 0, "n_q2": 0, "n_q3": 0,
                 "n_acordo": None, "n_desacordo": None,
                 "scf_min": None, "scf_med": None, "scf_max": None,
                 "e_z": None, "conf": None, "cands": None}

    if s_rep_ind is None:
        # Cold start do cluster `cid`: nenhum representante ainda. Ramo
        # `find_distinct_individuals` (`selection.py:36-41`).
        tel["ramo"] = "distinct"
        rep_ind_list = list(rep_individuals.values())
        cands = find_distinct_individuals(rep_ind_list, offsprings, s_net,
                                          device, max_size)
        tel["n_q1"] = len(cands)
    else:
        tel["ramo"] = "categorias"
        p_rep_ind = get_pareto_rep_ind(s_rep_ind, nd_rep_individuals, ref_points)
        if p_net is not None and s_net is not None:
            # Recomputamos a triagem AQUI (em vez de chamar
            # `find_candidate_individuals`) para não pagar 2× os 2×7000 forwards
            # só por telemetria. As predições são `eval()`+`no_grad()`
            # (`prediction.py:76-78`) ⇒ ZERO consumo de RNG ⇒ a trajetória é a
            # mesma. A lógica abaixo é `selection.py:86-124` linha a linha.
            p_lab, p_cfs = nn_predict_dom_inter(offsprings, [p_rep_ind],
                                                p_net, device)
            s_lab, s_cfs = nn_predict_dom_inter(offsprings, [s_rep_ind],
                                                s_net, device)
            p_lab, s_cfs = p_lab.squeeze(), s_cfs.squeeze()
            s_lab, p_cfs = s_lab.squeeze(), p_cfs.squeeze()
            scf = np.asarray(p_cfs, dtype=np.float64) + np.asarray(s_cfs,
                                                                   dtype=np.float64)
            q1, q1c, q2, q2c, q3, q3c = [], [], [], [], [], []
            for i in range(len(offsprings)):
                pl, sl, ind = p_lab[i], s_lab[i], offsprings[i]
                if pl == 1 and sl == 1:
                    q1.append(ind); q1c.append(scf[i])
                elif sl == 1 and pl == 0:
                    q2.append(ind); q2c.append(scf[i])
                elif pl == 1 and sl == 0:
                    q3.append(ind); q3c.append(scf[i])
            # Agregados do pool INTEIRO (7000) — [P3/DI-16.3 opção A+]: são os
            # números que o algoritmo REALMENTE computou sobre todo o pool.
            acordo = int(np.sum(np.asarray(p_lab) == np.asarray(s_lab)))
            tel.update(n_acordo=acordo, n_desacordo=int(len(offsprings) - acordo),
                       scf_min=float(np.min(scf)), scf_max=float(np.max(scf)),
                       scf_med=float(np.median(scf)),
                       n_q1=len(q1), n_q2=len(q2), n_q3=len(q3))
            ps = truncate(q1, q1c, max_size)
            s_ = truncate(q2, q2c, max_size)
            p_ = truncate(q3, q3c, max_size)
        else:
            ps, s_, p_ = find_candidate_individuals(
                p_rep_ind, s_rep_ind, offsprings, p_net, s_net, device, max_size)
            tel.update(n_q1=len(ps), n_q2=len(s_), n_q3=len(p_))
        cands = ps or s_ or p_
        tel["categoria_escolhida"] = ("Q1" if ps else "Q2" if s_ else
                                      "Q3" if p_ else None)

    if not cands:
        return None, tel

    # ── estágio 2: e(z) sobre a categoria vencedora ─────────────────────────
    if len(cands) == 1:
        best = cands[0]                                   # `selection.py:148-149`
        tel.update(e_z=np.array([np.nan]), conf=np.array([np.nan]), cands=cands)
        return best, tel
    if p_net is None and s_net is None:
        best = random.choice(cands)                       # `selection.py:151-152`
        tel["ramo"] = "aleatorio_sem_modelo"
        return best, tel

    e_z, conf = _e_of_z(cands, p_net, s_net, device)
    best = cands[int(np.argmax(e_z))]                     # `selection.py:168-170`
    tel.update(e_z=e_z, conf=conf, cands=cands)
    return best, tel


def _fallback_p_sum(offsprings, rep_individuals, nd_rep_individuals,
                    p_net, s_net, device, ref_points, cid):
    """Fallback do cap anti-spin: o melhor do pool por `p_sum` (= `scf`).

    Só é chamado quando o cap de `SPIN_MAX` re-samples estourou — as 3 categorias
    saíram vazias 10× seguidas. É um **desvio DECLARADO** do paper (fn. 6 manda
    re-samplar sem cap); sem ele o run gira para sempre gerando 7000 offsprings
    por volta e sem gastar 1 FE. Receita do E.7: "► 10 tentativas → fallback
    melhor p_sum".
    """
    from evolution.utils import get_pareto_rep_ind
    from learning.prediction import nn_predict_dom_inter

    s_rep_ind = rep_individuals.get(cid)
    if s_rep_ind is None or p_net is None or s_net is None:
        return random.choice(offsprings)
    p_rep_ind = get_pareto_rep_ind(s_rep_ind, nd_rep_individuals, ref_points)
    _, p_cfs = nn_predict_dom_inter(offsprings, [p_rep_ind], p_net, device)
    _, s_cfs = nn_predict_dom_inter(offsprings, [s_rep_ind], s_net, device)
    scf = np.asarray(p_cfs).squeeze() + np.asarray(s_cfs).squeeze()
    return offsprings[int(np.argmax(scf))]


# ═══════════════════════════════════════════════════════════════════════════
#  ③ — as linhas da BUSCA [P3/DI-16.3 · opção A+ ratificada pelo autor]
# ═══════════════════════════════════════════════════════════════════════════

def _ez_rows(tel: dict, geracao: int, escolhido, sid, modelo_flag: str) -> list:
    """As linhas da ③-BUSCA: o **TOP-100 por `e(z)`** — a cabeça do ranking.

    **[P3/DI-16.3, opção A+ — decidida pelo autor em 2026-07-19.]** A redação
    original da DI-16.3 pedia "TOP-100 do pool N*=7000 por `e(z)` + agregados de
    `e(z)` do pool INTEIRO". **Isso não tem referente no código** (verificado por
    4 lentes adversariais independentes, 4/4 confirmaram): `e(z)` é uma grandeza
    INTRA-CONJUNTO, calculada só sobre a categoria vencedora já truncada em
    `Q_max=300` (`selection.py:158-168`). Sobre os 7.000 o código computa OUTRA
    coisa — um score INTER contra o representante do cluster
    (`scf = p_cfs + s_cfs`, `selection.py:108`): sem soma em *j* (o rep é 1 só) e
    **sem o indicador de dominância** (soma a confiança do argmax, seja qual for
    — no ramo Q2 ele soma confiança de NÃO-dominância com sinal positivo). Um
    `e(z)` real sobre 7.000 custaria C(7000,2)×2 = 49 milhões de pares/iteração,
    materializados como lista Python antes do `torch.tensor` (~8–10 GB por rede
    por iteração): não é lento, é inviável.

    **O que gravamos (A+):** o TOP-100 por `e(z)` entre os candidatos que
    REALMENTE têm `e(z)` — exatamente onde a decisão acontece, e só 1 vira FE
    (o racional literal da DI-16.3). Os agregados do pool INTEIRO vão ao jsonl
    como as grandezas que o algoritmo de fato computou sobre os 7.000:
    contagens por categoria (Q1/Q2/Q3), `n_acordo`/`n_desacordo` das 2 redes, e
    min/mediana/máx do score INTER. Custo extra: ZERO. Perturbação: ZERO.

    O escolhido é sempre o `argmax` ⇒ está sempre no topo; só ELE recebe
    `real_solution_id` (os outros 99 nunca viram FE — `NULL` por construção).
    """
    cands, e_z, conf = tel.get("cands"), tel.get("e_z"), tel.get("conf")
    if not cands or e_z is None:
        return []
    ordem = np.argsort(-np.asarray(e_z, dtype=np.float64))[:TOP_BUSCA]
    rows = []
    for i in ordem:
        ind = cands[int(i)]
        eh_escolhido = ind is escolhido
        c = conf[int(i)] if conf is not None else np.nan
        rows.append(_export.surrogate_row(
            geracao, np.asarray(list(ind), dtype=np.float64),
            regime="online",
            real_solution_id=(sid if eh_escolhido else None),
            pred_tipo="score",
            pred_score=float(e_z[int(i)]),
            pred_confianca=(None if not np.isfinite(c) else float(c)),
            modelo_flag=modelo_flag))
    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  Sonda [P2/DI-16.2] — e(z) contra a POPULAÇÃO SELECIONADA
# ═══════════════════════════════════════════════════════════════════════════

def _sonda_predict(estado: dict, xl: np.ndarray, xu: np.ndarray):
    """Gancho `predict(X)->(score, confianca)` do `emit_sonda_block`.

    **[P2/DI-16.2] A referência é a POPULAÇÃO SELECIONADA corrente** (N=11 em
    M=2 / 15 em M=3). `e(z)` só existe RELATIVO a um conjunto; escolheu-se a
    população porque tem **tamanho FIXO** — parâmetro do próprio algoritmo ⇒ o
    score é comparável entre gerações, sementes e configs (o arquivo inteiro
    cresceria de 11D−1 a 31D−1 e o score subiria SÓ pela escala, falsificando a
    curva "o surrogate melhora com as épocas?", que é o propósito da sonda).

    ⚠ **Nota de honestidade para o dossiê de fidelidade (D97).** A DI-16.2
    justifica a escolha também por "(ii) é o contexto REAL em que o modelo decide
    na busca". Isso **não se sustenta no código**: o contexto real de decisão é
    de dois estágios — (1) UM representante de cluster, (2) intra-conjunto entre
    ≤300 co-candidatos. A população selecionada NUNCA aparece do lado direito de
    uma consulta de dominância. A perna (i) — tamanho fixo ⇒ comparabilidade —
    é sozinha suficiente e é a que sustenta a decisão. **Isto é um INSTRUMENTO de
    medida com referência própria, não uma reconstrução do score interno do
    algoritmo.** Levantado no handoff para a torre.

    Kernel FIEL (idêntico a `select_best`): máscara `label != 1` → 0, soma em j,
    as 2 redes somadas. `pred_confianca` = max-softmax sobre os pares (as duas
    redes), a mesma régua da busca.
    """
    from learning.prediction import nn_predict_dom_inter

    def predict(Xc: np.ndarray):
        pop, p_net, s_net = estado["pop"], estado["p_net"], estado["s_net"]
        device = estado["device"]
        Xc = np.asarray(Xc, dtype=np.float64)
        n = Xc.shape[0]
        if not pop or (p_net is None and s_net is None):
            # Sem modelo (cold start): nada a medir — a sonda registra NaN em
            # vez de fabricar um número (D53: sem arredondar, sem inventar).
            return np.full(n, np.nan), np.full(n, np.nan)
        # normalização de variáveis p/ [−1,1] — `evolution/norm.py:16`
        Z = ((Xc - xl) / np.maximum(xu - xl, 1e-300)) * 2.0 - 1.0
        shims = [_Shim(z.tolist()) for z in Z]
        e_z = np.zeros(n, dtype=np.float64)
        confs = []
        for net in (p_net, s_net):
            if net is None:
                continue
            lab, conf = nn_predict_dom_inter(shims, pop, net, device)
            confs.append(np.asarray(conf, dtype=np.float64))
            m = np.asarray(conf, dtype=np.float64).copy()
            m[np.asarray(lab) != 1] = 0.0
            e_z += np.sum(m, axis=1)
        conf_max = np.max(np.stack(confs), axis=(0, 2))
        return e_z, conf_max

    return predict


# ═══════════════════════════════════════════════════════════════════════════
#  O RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_c122(exp: str, alg: str, problema: str, semente, *,
             data_root: str = naming.DEFAULT_DATA_ROOT,
             enable_bucket: bool = False,
             teto_s: float | None = None,
             **_kwargs) -> dict:
    """Roda o θ-DEA-DP sob o contrato v5.2.1. Assinatura padrão dos runners.

    `enable_bucket=False` por padrão: o carimbo `bucket-only` (D54) **vale do M8
    em diante**; no Mac, até o M7, gravam-se as camadas LOCAIS COMPLETAS, sem
    podar a ③ (RI-08/DI-16.8). Nenhuma credencial GCS é configurada aqui.

    `teto_s` (opcional) = teto de wall-clock. Ao estourar, o run ABORTA LIMPO:
    preserva a curva parcial, grava as 4 camadas + manifesto com
    `status='failed'` e `motivo_parada='teto_wall'`, e **pára-e-loga** (D81) — a
    decisão de completar é do M7, não deste cartão.
    """
    import torch

    t_run = time.time()
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)

    with _c122_runtime():
        return _run_c122_inner(exp, alg, problema, semente, torch=torch,
                               pinning=pinning, env=env, t_run=t_run,
                               data_root=data_root, enable_bucket=enable_bucket,
                               teto_s=teto_s)


def _run_c122_inner(exp, alg, problema, semente, *, torch, pinning, env, t_run,
                    data_root, enable_bucket, teto_s):
    from evolution.counter import PerCounter
    from evolution.dom import pareto_dominance, scalar_dominance
    from evolution.norm import var_normalization
    from evolution.selection import sel_scalar_dea
    from evolution.utils import (full_evaluate, get_non_dominated_scalar_rep,
                                 init_dom_rel_map, init_scalar_rep,
                                 update_scalar_rep)
    from evolution.variation import random_genetic_variation
    from learning.model_init import init_dom_nn_classifier
    from learning.model_update import update_dom_nn_classifier
    from problems.rp import get_reference_points

    # ── determinismo (L.6) ──────────────────────────────────────────────────
    # 4 sementes derivadas por `SeedSequence((base, alg_id, 0, uso_id))` (D62) —
    # UMA vez por run (as streams correm contínuas; ver USO_* no topo).
    base = H.seed_base(alg, semente)
    random.seed(H.iteration_seed(base, ALG_ID, 0, USO_RANDOM, bits32=True))
    np.random.seed(H.iteration_seed(base, ALG_ID, 0, USO_NUMPY, bits32=True))
    torch.manual_seed(H.iteration_seed(base, ALG_ID, 0, USO_TORCH, bits32=True))
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    device = torch.device("cpu")

    # ── orçamento + DoE do artefato (D63/D87/D88 — NUNCA regenerado) ────────
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    doe = H.load_doe(problema, semente, data_root=data_root)
    D = int(doe["X"].shape[1])
    bud = FEBudget(D=D, logger=log)
    adapter = _Adapter(problema, bud)
    M = adapter.n_obj
    if doe["X"].shape[0] != bud.n_init:
        raise RuntimeError(
            f"DoE com {doe['X'].shape[0]} pontos != 11D−1 = {bud.n_init} "
            f"— pára-e-loga (D81).")

    f_min, f_max = f_limits(problema)                      # DEF-B11.1
    if f_min.shape[0] != M:
        raise RuntimeError(
            f"S.5 de {problema!r} tem M={f_min.shape[0]} != n_obj={M} "
            f"— pára-e-loga (D81).")

    creator = _fresh_creator(M)
    ref_points = get_reference_points(M)
    MU = len(ref_points)                                   # 11 (M=2) / 15 (M=3)
    T_MAX = 11 * D + 24                                    # janela do update
    counter = PerCounter(MU)                               # NOVO por run
    sonda = H.load_sonda(problema, regime="online", data_root=data_root)
    buf = H.SnapshotBuffer()

    sigma_dict = {
        "modelo": "2 FNNs 2x200 ReLU par-a-par (Pareto-Net + theta-Net), "
                  "softmax-3 SO na inferencia",
        "pred_tipo": "score (par-a-par) — mu_*/sigma_* NAO se aplicam ao c122",
        "pred_score": "e(z) = SOMA_j I(z domina j)·p_hat(z,j), somado sobre as "
                      "2 redes (fork fiel de select_best, selection.py:158-166)",
        "pred_confianca": "max-softmax sobre os pares da linha (diagonal "
                          "EXCLUIDA — conf[i,i]=1 e lixo, prediction.py:11-12)",
        "regime=online": f"[P3/DI-16.3 opcao A+] TOP-{TOP_BUSCA} por e(z) entre "
                         f"os candidatos da CATEGORIA vencedora (<=Q_max=300) — "
                         f"e(z) NAO existe p/ o pool de {LAMBDA} (e intra-"
                         f"conjunto). Agregados do pool inteiro no jsonl.",
        "regime=sonda": f"[P2/DI-16.2] e(z) vs a POPULACAO SELECIONADA corrente "
                        f"(n_ref={MU}) — referencia de tamanho FIXO. E um "
                        f"INSTRUMENTO de medida, nao o score interno da busca.",
        "real_solution_id": "preenchido SO na linha do escolhido (unico que "
                            "vira FE); os outros nunca foram avaliados (NULL)",
        "fe_treino_max": "|archive|−1 no momento do fit — MONOTONICO no c122 "
                         "(a janela T_max move o INICIO, nao o fim)",
    }
    params = {
        "N_MU": MU, "lambda_pool": LAMBDA, "infill_por_iter": 1,
        "sbx": {"proC": CXPB, "disC": ETA_C},
        "pm": {"proM": MUTPB, "indpb": 1.0 / D, "disM": ETA_M},
        "fnn": "2x200 ReLU, logits-3", "adam": {"lr": LR, "batch": BATCH_SIZE,
                                                "weight_decay": WEIGHT_DECAY},
        "E_init": E_INIT, "T_max": T_MAX, "gamma_acc_thr": ACC_THR,
        "Q_max": CATEGORY_SIZE, "theta_PBI": 5, "x_norm": "[-1,1]",
        "f_limits_fonte": "S.5 (fronts VERDADEIROS) + margem 10% — DEF-B11.1, "
                          "vantagem informacional DECLARADA (D73b)",
        "f_min": f_min.tolist(), "f_max": f_max.tolist(),
        "spin_cap": SPIN_MAX,
        "torch_default_dtype": "float32 (FORCADO pelo codigo — prediction.py:24 "
                               "faz .float(); float64 levanta RuntimeError)",
        "visualization": False,
    }

    n_spin_total = n_cache_infill = n_cache_seguidos = 0
    n_reinit = {"p": 0, "s": 0}
    n_skip_treino = {"p": 0, "s": 0}
    g = 0
    status, motivo_parada = "ok", "orcamento"
    t_fit_total = t_busca_total = t_sonda_total = 0.0
    ultima_sonda_g = None
    estado_sonda = {"pop": [], "p_net": None, "s_net": None, "device": device}

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="online", maxfe=bud.maxfe,
                   n_init=bud.n_init, doe_hash=doe["doe_hash"],
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   params=params, n_ref=MU,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"])

        # ── init: o DoE do artefato vira a população inicial ────────────────
        t0 = time.time()
        pop = [creator.Individual(list(x)) for x in doe["X"]]
        var_normalization(pop, low=adapter.xl, up=adapter.xu)
        full_evaluate(pop, _ToolboxShim(adapter, ref_points), f_min, f_max)
        archive = list(pop)
        rep_individuals = init_scalar_rep(pop)
        nd_rep = get_non_dominated_scalar_rep(rep_individuals)
        p_rel_map, s_rel_map = init_dom_rel_map(bud.maxfe)
        t_init_eval = time.time() - t0

        # ── treino inicial das 2 redes (E_init=20, arquivo INTEIRO) ─────────
        # Assinatura do repo: (archive, rel_map, dom, device, input_size,
        # hidden_size, num_hidden_layers, epochs, ...) — a entrada das redes é o
        # PAR concatenado [x_i, x_j] em [−1,1] ⇒ input_size = 2·D.
        t0 = time.time()
        p_net = init_dom_nn_classifier(archive, p_rel_map, pareto_dominance,
                                       device, 2 * D, HIDDEN, N_HIDDEN, E_INIT,
                                       batch_size=BATCH_SIZE, lr=LR,
                                       weight_decay=WEIGHT_DECAY)
        s_net = init_dom_nn_classifier(archive, s_rel_map, scalar_dominance,
                                       device, 2 * D, HIDDEN, N_HIDDEN, E_INIT,
                                       batch_size=BATCH_SIZE, lr=LR,
                                       weight_decay=WEIGHT_DECAY)
        t_fit = time.time() - t0
        t_fit_total += t_fit
        fe_treino_max = len(archive) - 1
        if p_net is None:
            n_reinit["p"] += 1
        if s_net is None:
            n_reinit["s"] += 1
        log.event("fit_inicial", epocas=E_INIT, n_treino=len(archive),
                  tempo_fit_s=round(t_fit, 6), fe_treino_max=fe_treino_max,
                  p_net=(p_net is not None), s_net=(s_net is not None),
                  motivo_none="compute_class_weight=None (classe ausente) "
                              "⇒ modelo None ⇒ selecao aleatoria (design)")

        # ── laço principal — fork de `scalar_dom_ea_dp` (algorithms.py:35) ──
        # Dirigido pelo `bud.fe` (a fonte ÚNICA do orçamento) e não por um
        # contador local: assim um cache-hit (0 FE, D89) não "gasta" iteração e
        # o FE final fecha em 31D−1 EXATO.
        while bud.fe < bud.maxfe:
            g += 1
            t_g0 = time.time()
            buf.set_fe_treino_max(fe_treino_max)
            estado_sonda.update(pop=list(pop), p_net=p_net, s_net=s_net)

            # sonda ANTES da decisão: mede o modelo COM QUE esta geração decide
            t_snd = 0.0
            if H.sonda_due(g, k=H.SONDA_K):
                t_snd = H.emit_sonda_block(
                    buf, log, geracao=g, fe=bud.fe, sonda=sonda,
                    predict=_sonda_predict(estado_sonda, adapter.xl, adapter.xu),
                    fe_treino_max=fe_treino_max, pred_tipo="score",
                    modelo_flag="EDN-par(2xFNN)",
                    motivo=f"cadencia k={H.SONDA_K} (g=1,2,4,6,…); n_ref={MU}")
                t_sonda_total += t_snd
                ultima_sonda_g = g

            # ── estágios 1+2 com cap anti-spin ──────────────────────────────
            t_b0 = time.time()
            escolhido, tel, n_spin = None, {}, 0
            while escolhido is None:
                offsprings = random_genetic_variation(
                    pop, LAMBDA, _ToolboxShim(adapter, ref_points),
                    cxpb=CXPB, mutpb=MUTPB)
                var_normalization(offsprings, low=adapter.xl, up=adapter.xu)
                escolhido, tel = _filtro_instrumentado(
                    offsprings, rep_individuals, nd_rep, p_net, s_net,
                    CATEGORY_SIZE, device, ref_points, counter)
                if escolhido is None:
                    n_spin += 1
                    n_spin_total += 1
                    log.guard("spin_resample", geracao=g, tentativa=n_spin,
                              cid=tel.get("cid"), n_pool=len(offsprings),
                              motivo="as 3 categorias sairam vazias — o paper "
                                     "re-sampla SEM cap (fn. 6)")
                    if n_spin >= SPIN_MAX:
                        escolhido = _fallback_p_sum(
                            offsprings, rep_individuals, nd_rep, p_net, s_net,
                            device, ref_points, tel.get("cid"))
                        log.guard("spin_cap", geracao=g, tentativas=n_spin,
                                  acao="fallback melhor p_sum (scf)",
                                  desvio="DECLARADO — E.7; o paper nao capeia")
                        break
            t_busca = time.time() - t_b0
            t_busca_total += t_busca

            # ── 1 FE: o único candidato que vira avaliação real ─────────────
            fe_antes = bud.fe
            full_evaluate([escolhido], _ToolboxShim(adapter, ref_points),
                          f_min, f_max)
            sid = bud.solution_id_of(np.asarray(list(escolhido),
                                                dtype=np.float64))
            #: **Cache-hit (D89): 0 FE ⇒ o arquivo NÃO cresce.** O laço original
            #: (`algorithms.py:48-50`) faz `evaluations += 1` e `archive.append`
            #: incondicionalmente, porque o repo não tem dedup. O nosso contrato
            #: tem: um X bit-a-bit idêntico é a MESMA solução, já está no
            #: arquivo, e re-consultá-la é grátis. Anexá-la de novo (i) estouraria
            #: o `rel_map`, dimensionado em `maxfe` (MEDIDO: `IndexError` na
            #: última geração de MMF1), (ii) criaria um par (i,i) degenerado nas
            #: matrizes de dominância e (iii) quebraria o invariante
            #: `len(archive) == bud.fe`. A predição desta geração É
            #: decisão-relevante e continua na ③ — com `real_solution_id`
            #: apontando a solução PREEXISTENTE (o join fica correto).
            cache_hit = (bud.fe == fe_antes)
            if cache_hit:
                n_cache_infill += 1
                n_cache_seguidos += 1
                log.guard("cache_hit_infill", geracao=g, solution_id=sid,
                          fe=bud.fe, seguidos=n_cache_seguidos,
                          motivo="o modelo reescolheu uma X ja avaliada "
                                 "(bit-a-bit) — 0 FE (D89); o arquivo NAO cresce")
                if n_cache_seguidos >= SPIN_MAX:
                    status, motivo_parada = "failed", "cache_hit_travado"
                    log.guard("cache_hit_travado", geracao=g, fe=bud.fe,
                              seguidos=n_cache_seguidos,
                              acao="ABORTO — o orcamento nao avanca; "
                                   "para-e-loga (D81)")
                    break
            else:
                n_cache_seguidos = 0
                archive.append(escolhido)
            if update_scalar_rep(rep_individuals, escolhido):
                nd_rep = get_non_dominated_scalar_rep(rep_individuals)
            pop = sel_scalar_dea(pop + [escolhido], MU)

            # ── ③ BUSCA: o TOP-100 por e(z) [P3/DI-16.3 A+] ────────────────
            for row in _ez_rows(tel, g, escolhido, sid, "EDN-par(2xFNN)"):
                buf.add_surrogate(row)
            # ② membership da população REAL selecionada
            buf.add_pop(g, [s for s in (bud.solution_id_of(
                np.asarray(list(i), dtype=np.float64)) for i in pop)
                if s is not None])

            # ── retreino das 2 redes (warm-start gateado por acc ≥ γ) ───────
            t_f0 = time.time()
            p_net, ev_p = _atualiza(p_net, archive, p_rel_map, pareto_dominance,
                                    device, T_MAX, n_reinit, n_skip_treino, "p",
                                    init_dom_nn_classifier,
                                    update_dom_nn_classifier, D)
            s_net, ev_s = _atualiza(s_net, archive, s_rel_map, scalar_dominance,
                                    device, T_MAX, n_reinit, n_skip_treino, "s",
                                    init_dom_nn_classifier,
                                    update_dom_nn_classifier, D)
            t_fit = time.time() - t_f0
            t_fit_total += t_fit
            fe_treino_max = len(archive) - 1

            # ── ④ timing (tempo_geracao_s EXCLUI a sonda) ──────────────────
            buf.add_timing(geracao=g, n_acumulado=len(archive),
                           tempo_fit_s=t_fit, tempo_busca_s=t_busca,
                           tempo_pred_sonda_s=t_snd,
                           tempo_geracao_s=(time.time() - t_g0) - t_snd)

            # ── ⑥ jsonl: mínimo comum DI-10 + os campos do c122 (S.7.1) ────
            F_arc = np.asarray([ind.fitness.values for ind in archive],
                               dtype=np.float64)
            i_esc = (int(np.argmax(tel["e_z"])) if tel.get("e_z") is not None
                     else None)
            log.decision(
                caminho=f"c122_gen:{tel.get('ramo')}",
                motivo=f"categoria={tel.get('categoria_escolhida')} "
                       f"(Q1>Q2>Q3, acordo das 2 redes)",
                geracao=g, cid=tel.get("cid"), n_ref=MU,
                softmax_escolhido=(None if i_esc is None or tel["conf"] is None
                                   else _f(tel["conf"][i_esc])),
                e_z_escolhido=(None if i_esc is None
                               else _f(tel["e_z"][i_esc])),
                n_q1=tel["n_q1"], n_q2=tel["n_q2"], n_q3=tel["n_q3"],
                n_acordo=tel["n_acordo"], n_desacordo=tel["n_desacordo"],
                pool_scf_min=_f(tel["scf_min"]), pool_scf_med=_f(tel["scf_med"]),
                pool_scf_max=_f(tel["scf_max"]),
                ez_cat_min=_agg(tel.get("e_z"), np.min),
                ez_cat_med=_agg(tel.get("e_z"), np.median),
                ez_cat_max=_agg(tel.get("e_z"), np.max),
                n_cands=(len(tel["cands"]) if tel.get("cands") else 0),
                accs_p=ev_p.get("accs"), accs_s=ev_s.get("accs"),
                epocas_p=ev_p.get("epocas"), epocas_s=ev_s.get("epocas"),
                skip_treino_p=ev_p.get("skip"), skip_treino_s=ev_s.get("skip"),
                reinit_p=ev_p.get("reinit"), reinit_s=ev_s.get("reinit"),
                n_spin=n_spin, fe_treino_max=fe_treino_max,
                f_min=f_min.tolist(), f_max=f_max.tolist(),
                **H.minimo_comum_di10(
                    F_arc, fe=bud.fe, tempo_fit_s=t_fit,
                    tempo_busca_s=t_busca,
                    dist_min_arquivo=_dist_min(escolhido, archive)))

            del offsprings
            H.iteration_cleanup()

            if teto_s is not None and (time.time() - t_run) > teto_s:
                status, motivo_parada = "failed", "teto_wall"
                log.guard("teto_wall", geracao=g, fe=bud.fe,
                          decorrido_s=round(time.time() - t_run, 1),
                          teto_s=teto_s,
                          acao="ABORTO LIMPO — curva parcial preservada; a "
                               "decisao de completar e do M7 (D81)")
                break

        # ── sonda da ÚLTIMA geração (§3.1: "SEMPRE a 1ª e a última") ────────
        if g and ultima_sonda_g != g:
            estado_sonda.update(pop=list(pop), p_net=p_net, s_net=s_net)
            buf.set_fe_treino_max(fe_treino_max)
            t_snd = H.emit_sonda_block(
                buf, log, geracao=g, fe=bud.fe, sonda=sonda,
                predict=_sonda_predict(estado_sonda, adapter.xl, adapter.xu),
                fe_treino_max=fe_treino_max, pred_tipo="score",
                modelo_flag="EDN-par(2xFNN)",
                motivo=f"ultima geracao (§3.1); n_ref={MU}")
            t_sonda_total += t_snd
            buf.update_timing(g, tempo_pred_sonda_s=t_snd)
            ultima_sonda_g = g

    except BudgetExhausted:
        # Fim NATURAL (D61) — o laço já para em `bud.fe == maxfe`; esta captura
        # é a rede de segurança do hard-stop exato.
        log.guard("hard_stop_capturado", fe=bud.fe, maxfe=bud.maxfe,
                  motivo="fim natural do orcamento (D61)")
    except Exception as exc:                                # pragma: no cover
        status, motivo_parada = "failed", f"{type(exc).__name__}: {exc}"
        log.footer(status="failed", fe_final=bud.fe, erro=motivo_parada)
        log.close()
        raise

    try:
        n_front1 = len(_nds(np.asarray([r.f for r in bud.records],
                                       dtype=np.float64)))
        timing_totais = _export.manifest_timing_block(
            tempo_total_s=time.time() - t_run,
            tempo_fit_surrogate_s=t_fit_total, tempo_busca_s=t_busca_total,
            tempo_aval_real_s=adapter.tempo_aval_real_s,
            tempo_pred_sonda_s=t_sonda_total)
        # [DI-23] status/motivo REAIS no manifesto — cumpre a promessa do
        # docstring (:576-579): um aborto por teto/cache-cap grava `failed`,
        # não o 'ok' hard-coded que o harness carimbava (achado §3.3 do c149).
        res = H.write_run_outputs(
            exp, alg, problema, semente, bud, buf, D=D, M=M,
            cp_hashes={"doe_hash": doe["doe_hash"]},
            env=env, pinning=pinning, n_geracoes=g,
            algo_version=ALGO_VERSION, timing_totais=timing_totais,
            status=status, motivo_parada=motivo_parada,
            sigma_dict=sigma_dict, regime="online", params=params,
            sonda_info={"S": sonda["S"], "cadencia": f"online: k={H.SONDA_K} "
                        f"(g=1,2,4,6,…) + 1a e ultima",
                        "n_blocos": _n_blocos(buf), "n_ref": MU,
                        "referencia": "populacao selecionada [P2/DI-16.2]",
                        "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]},
            data_root=data_root, enable_bucket=enable_bucket)
        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=g,
                   motivo_parada=motivo_parada, n_front1=n_front1,
                   n_spin_total=n_spin_total, n_reinit=n_reinit,
                   n_skip_treino=n_skip_treino,
                   n_cache_infill=n_cache_infill)
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_geracoes": g,
        "cp_init_ok": bool(res["cp_init_ok"]), "status": status,
        "motivo_parada": motivo_parada,
        "n_surrogate_rows": len(buf.surr_rows), "n_pop_rows": len(buf.pop_rows),
        "n_timing_rows": len(buf.timing_rows), "n_sonda_pontos": sonda["S"],
        "n_blocos_sonda": _n_blocos(buf), "n_ref": MU, "regime": "online",
        "cache_hits": bud.cache_hits, "n_spin_total": n_spin_total,
        "n_cache_infill": n_cache_infill, "n_archive": len(archive),
        "tempo_pred_sonda_s": t_sonda_total, "n_front1": n_front1,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Auxiliares
# ═══════════════════════════════════════════════════════════════════════════

class _ToolboxShim:
    """O mínimo do `base.Toolbox` que as funções do repo consomem.

    `full_evaluate` usa `.evaluate` + `.cluster_scalarization`;
    `random_genetic_variation` usa `.clone`/`.mate`/`.mutate`. Um shim em vez do
    `Toolbox` real porque o `Toolbox` do DEAP é registrado por `partial` global e
    misturaria estado entre runs.
    """

    def __init__(self, adapter: _Adapter, ref_points):
        from copy import deepcopy
        from deap import tools
        from evolution.scalar import cluster_scalarization
        self._a, self._rp = adapter, ref_points
        self._tools, self._deepcopy = tools, deepcopy
        self._cs = cluster_scalarization

    def evaluate(self, individuals):
        return self._a.evaluate(individuals)

    def cluster_scalarization(self, individuals):
        return self._cs(individuals, ref_points=self._rp)

    def clone(self, ind):
        return self._deepcopy(ind)

    def mate(self, a, b):
        return self._tools.cxSimulatedBinaryBounded(
            a, b, low=list(self._a.xl), up=list(self._a.xu), eta=ETA_C)

    def mutate(self, ind):
        return self._tools.mutPolynomialBounded(
            ind, low=list(self._a.xl), up=list(self._a.xu), eta=ETA_M,
            indpb=1.0 / self._a.n_var)


def _atualiza(net, archive, rel_map, dom, device, t_max, n_reinit, n_skip,
              tag, init_fn, update_fn, D):
    """Um retreino: warm-start gateado, ou RE-INIT no arquivo INTEIRO.

    `net is None` ⇒ **re-init**: `init_dom_nn_classifier` treina no arquivo
    INTEIRO (`start=0`), E_init=20 épocas. Acontece quando
    `compute_class_weight` devolveu `None` — uma das 3 classes está AUSENTE no
    lote (`learning/utils.py:78-79`) — o "cold-start: classe ausente → modelo
    None → seleção aleatória (design)" do cartão (S.3#3).

    `net` existente ⇒ **update**: janela `T_max = 11n+24` (só o INÍCIO se move,
    `learning/utils.py:122-126`), gate `min_acc >= γ=0,9` ⇒ **ZERO épocas**
    (`model_update.py:22` — a borda que o cartão sinaliza: 0,9 EXATO pula o
    treino, porque o operador é `>=` e não `>`), senão
    `E_upd = ceil(20·(γ − min_acc)/γ)`.

    ⚠ As accs vêm de `get_accuracy`, que devolve o SENTINELA `1` para uma classe
    AUSENTE (`learning/utils.py:144-145`) — logamos `accs` cruas e o leitor do
    dossiê precisa saber disso (registrado no handoff).
    """
    ev: dict = {"skip": False, "reinit": False, "accs": None, "epocas": None}
    if net is None:
        ev["reinit"] = True
        n_reinit[tag] += 1
        novo = init_fn(archive, rel_map, dom, device, 2 * D, HIDDEN, N_HIDDEN,
                       E_INIT, batch_size=BATCH_SIZE, lr=LR,
                       weight_decay=WEIGHT_DECAY)
        ev["epocas"] = E_INIT if novo is not None else 0
        return novo, ev

    accs, epocas = _captura_accs(net, archive, rel_map, dom, device, t_max,
                                 update_fn)
    ev.update(accs=accs, epocas=epocas, skip=(epocas == 0))
    if epocas == 0:
        n_skip[tag] += 1
    return net, ev


def _captura_accs(net, archive, rel_map, dom, device, t_max, update_fn):
    """Chama o `update_dom_nn_classifier` STOCK e captura accs/épocas EXATAS.

    O `update` do repo só IMPRIME as accs (`model_update.py:19`) e não devolve
    nada. Em vez de forkar o miolo (patch invasivo, D30), sombreamos dois nomes
    do MÓDULO — adição **read-only** que só expõe valor JÁ computado (o critério
    da DI-12.1). O treino em si é 100% o código do autor:

    - `mu.print` → captura `(acc0, acc1, acc2)` (`model_update.py:19`);
    - `mu.train_nn` → captura o `epochs` REALMENTE passado
      (`model_update.py:39`). Medir aqui, e não recomputar a Eq. 5, é o que
      distingue os **três** caminhos de "zero época", que a fórmula confunde:
      (i) gate `min_acc >= γ` passou (`:22`), (ii) `compute_class_weight`
      devolveu `None` — classe ausente (`:28-29`), (iii) treinou de fato.
      Sem isso, o (ii) apareceria no dossiê como se tivesse treinado.
    """
    import learning.model_update as mu

    capturado: dict = {"accs": None, "epocas": 0}
    print_ant, train_ant = getattr(mu, "print", None), mu.train_nn

    def _print(*a, **_kw):
        if a and isinstance(a[0], str) and a[0].startswith("Estimated accuracy"):
            capturado["accs"] = [float(v) for v in a[1:]]
        return None

    def _train_nn(data, loader, net_, criterion, optimizer, batch_size, epochs):
        capturado["epocas"] = int(epochs)
        return train_ant(data, loader, net_, criterion, optimizer,
                         batch_size, epochs)

    mu.print, mu.train_nn = _print, _train_nn
    try:
        update_fn(net, archive, rel_map, dom, device, t_max,
                  max_adjust_epochs=E_INIT, batch_size=BATCH_SIZE, lr=LR,
                  acc_thr=ACC_THR, weight_decay=WEIGHT_DECAY)
    finally:
        mu.train_nn = train_ant
        if print_ant is None:
            with contextlib.suppress(AttributeError):
                del mu.print
        else:                                            # pragma: no cover
            mu.print = print_ant
    return capturado["accs"], capturado["epocas"]


def _dist_min(ind, archive) -> float | None:
    """`dist_min_arquivo` (B3/DI-10) — distância do infill ao arquivo ANTERIOR."""
    if len(archive) < 2:
        return None
    X = np.asarray([list(a) for a in archive[:-1]], dtype=np.float64)
    x = np.asarray(list(ind), dtype=np.float64)
    return float(np.min(np.linalg.norm(X - x, axis=1)))


def _nds(F: np.ndarray) -> np.ndarray:
    from src import problems as _problems
    return np.asarray(_problems._nds_filter(np.asarray(F, dtype=np.float64)))


def _n_blocos(buf) -> int:
    return sum(1 for r in buf.surr_rows if r.get("regime") == "sonda") // 2000


def _f(v):
    """float() tolerante a None/NaN — o jsonl não carrega NaN cru."""
    if v is None:
        return None
    v = float(v)
    return None if not np.isfinite(v) else round(v, 6)


def _agg(arr, fn):
    if arr is None or len(arr) == 0:
        return None
    return _f(fn(np.asarray(arr, dtype=np.float64)))


__all__ = ["run_c122", "f_limits", "ALG_ID", "ALGO_VERSION"]
