"""[R3-piso-off] Piso OFFLINE — MOEA/D-média (moead_media, DESDEO mode 12) — OFFLINE.

1 sessao = 1 cartao: este cobre SO o `moead_media` (mode 12 = Gen-MOEA/D PBI) e
NAO toca em nenhum outro algoritmo (em especial NAO o b5r/b5m = modes 7/72, cartao
proprio).

**O que e (D77 / DEF-E3):** o piso offline e a ABLACAO CIRURGICA do b5 — o MESMO
motor (MOEA/D do repo DESDEO), o MESMO surrogate (SurrogateKriging), o MESMO
orcamento (40k aval-surrogate), mudando SO a selecao: mode 12 usa `MOEAD_select`
(decomposicao PBI generica, so a MEDIA), enquanto o b5m (mode 72) usa
`ProbMOEAD_select` (comparacao MC probabilistica). O contraste piso x b5 mede
exatamente o VALOR de usar σ. Por isso e "o b5 sem σ".

Roda em `env_b5` (py3.7.12 x86_64/Rosetta, sklearn 0.21.3) com o `desdeo_*`
VENDORIZADO em `algorithms/b5_Prob-RVEA/` A FRENTE do `sys.path` (root-first) — o
pip nao tem `desdeo-emo` (VENDORED e a fonte unica, gate R3.2) e a
`SurrogateKriging` de kernel fixo mora no `desdeo_problem` vendorizado. NUNCA
co-importar com c311 (N.1.2/D79).

Molde: `src/b5_prob.py` (o cartao irmao — mesmo env, mesma arvore, mesmo fluxo
`DataProblem -> SurrogateKriging -> evolver`). O UNICO desvio de fundo vs o b5m:
  - evolver = `MOEA_D` (mode 12, `desdeo_emo.EAs.ProbMOEAD`) no lugar de `ProbMOEAD`;
  - σ NULL em TODA a ③ (busca E sonda) — DI-16.1: o piso reporta so μ. `_predict`
    devolve `(mu, None)`; as linhas de busca vao com `sigma=None`.

Regime OFFLINE (identico ao b5):
  - o dataset D90 E o orcamento (31D−1, ESGOTADO na carga; ① = o dataset);
  - surrogate GP treinado UMA vez no dataset (offline nao retreina);
  - MOEA interno sobre o surrogate: 40.000 avaliacoes-surrogate, ZERO FE real
    (`offline_guard` converte qualquer FE real em `OfflineBudgetViolation`);
  - ⑦ `__final`: o ND final avaliado 1× na VERDADE (`src/problems.py`, pos-hoc,
    fora do orcamento — DI-08/DI-13.9), reconstituivel da ③;
  - SONDA: 1 bloco de 20.000, `geracao`=NULL (DI-13.5), μ preenchido / σ NULL.

Notas de ambiente (herdadas do b5, VALIDADAS no Fase 0 desta sessao):
  - o `doe.py` JA e pyarrow-12-safe (DI-26) => o shim local do b5 NAO e mais
    necessario (omitido); `load_offline_budget` roda limpo no env_b5;
  - patches vendorizados `b5-mode72-kde` / `b5-mode7-archive` sao INERTES para o
    mode 12 (usa `MOEAD_select`, arquivo distinto, e sobrescreve `_next_gen` sem
    super()) — a ⑦ nasce reconstituivel da ③ NATIVAMENTE (arquivamento pos-replace
    por geracao no proprio `MOEA_D._next_gen`; sem necessidade do patch-archive).
"""
from __future__ import annotations

# ── shim py3.7: o loader de NDS do pymoo 0.6.1.2 (env_b5, p/ os finais ⑦ via
#    src.problems) importa `typing.Literal`, que so existe em py3.8+. Precisa
#    existir ANTES de qualquer import de `src.problems`. [herdado do b5] ─────────
import typing as _typing
if not hasattr(_typing, "Literal"):
    import typing_extensions as _te
    _typing.Literal = _te.Literal  # type: ignore[attr-defined]

# ── ORDEM: o `standalone_harness` pina as env vars de thread (D79/N.1.1) no
#    import, ANTES de numpy. ───────────────────────────────────────────────────
from src import standalone_harness as H

import contextlib
import io
import os
import random
import sys
import time

import numpy as np

from src import export as _export
from src import naming


# ── identidade do config ──────────────────────────────────────────────────────
_ALG = "moead_media"
_ALG_ID = 21                              # seeds.json (D91) — anti-descompasso
_MODE = 12                                # StartAll.py:68 "12 = Gen-MOEA/D (PBI)"
_MODELO_FLAG = "moead_media/MOEAD-PBI+GPR-media"
USO_RANDOM = 1
USO_NUMPY = 2
ALGO_VERSION = "piso-off-moead_media-1.0"

# FE total do MOEA interno — SEMPRE 40000 (a rampa θ do PBI divide por ele:
# `total_function_evaluations=0` daria ZeroDivision). Main_Execute.py:115. [D77]
_FE_TOTAL = 40000
_GEN_PER_ITER = 10                        # Main_Execute.py:34 (= b5)

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_VENDOR = os.path.join(_REPO, "algorithms", "b5_Prob-RVEA")


# ══════════════════════════════════════════════════════════════════════════════
#  Despacho (o `experiment.run` chama com `(exp, alg, problema, semente, **kw)`)
# ══════════════════════════════════════════════════════════════════════════════
def run_piso_offline(exp, alg, problema, semente, *,
                     data_root: str = naming.DEFAULT_DATA_ROOT,
                     enable_bucket: bool = False, sonda_on: bool = True,
                     teto_s: float | None = None, **_kwargs) -> dict:
    """Piso offline — MOEA/D-média (mode 12). O `alg` do despacho e sempre
    `moead_media`; o cartao e unico."""
    if alg != _ALG:
        raise ValueError(
            "run_piso_offline so cobre %r (recebeu %r) — 1 sessao = 1 cartao."
            % (_ALG, alg))
    return _run(exp, problema, semente, data_root=data_root,
                enable_bucket=enable_bucket, sonda_on=sonda_on, teto_s=teto_s)


# ── [BL-02/A25] o flag dos vetores de referência, TAMBÉM no piso ──────────────
#  A F5.4 pediu este campo e ele nunca foi escrito aqui — 0 ocorrências de
#  `reference_vectors` neste arquivo. Não era escolha: era omissão, e ela
#  esvazia justamente a ABLAÇÃO. O `MOEA_D` do mode 12 herda o
#  `manage_preferences` do `BaseDecompositionEA` (`BaseEA.py:244`), que chama
#  `reference_vectors.adapt(...)` a cada `iterate()` — ou seja, **o piso está
#  sujeito à MESMA cadeia A8 do b5m** (`adapt` → norma 0 → PBI NaN → P_wrong ≡ 0
#  → zero substituições). Sem o campo aqui, um congelamento do b5m não pode ser
#  atribuído à maquinaria probabilística: pode ser comum aos dois, e aí o achado
#  se descaracteriza. É exatamente o contraste que a ablação existe para medir.
#  Read-only (D97): nenhuma decisão da busca vê isto acontecer.

def _vetores_degenerados(evolver):
    """A norma dos vetores de referência colapsou a zero? (gêmeo do b5_prob)"""
    try:
        V = evolver.reference_vectors.values
        n = np.linalg.norm(np.asarray(V, dtype=float), axis=1)
        nmin, nmax = float(np.min(n)), float(np.max(n))
        return {"n_vetores": int(n.size),
                "n_norma_zero": int(np.count_nonzero(n == 0.0)),
                "norma_min": nmin, "norma_max": nmax,
                "amplitude": float(nmax - nmin)}
    except Exception:                        # noqa: BLE001 — nunca derruba (D97)
        return None


def _registra_vetores(evolver, serie, desde):
    """Carimba o estado dos vetores nas gerações que ele GOVERNOU.

    Gêmeo de `b5_prob._registra_vetores`: o `adapt` roda 1× por `iterate()`, que
    produz `n_gen_per_iter` gerações — a série é amostrada na cadência do
    `iterate`, e é isso que ela declara. Nasce já assim aqui (o b5 precisou de
    correção; este não repete o erro).
    """
    d = _vetores_degenerados(evolver)
    try:
        ate = max(int(k) for k in evolver.population.individuals_archive)
    except Exception:                        # noqa: BLE001
        return desde
    for g in range(int(desde) + 1, ate + 1):
        serie[g] = d
    return ate


# ── util: silenciar os prints verbosos do repo vendorizado ────────────────────
@contextlib.contextmanager
def _quiet():
    """Redireciona o stdout do repo vendorizado (Selection/FE count/warnings)
    — em 40k FE eles inundam o terminal. `PISO_VERBOSE=1` desliga o silenciamento
    p/ depuracao. NAO engole excecoes."""
    if os.environ.get("PISO_VERBOSE"):
        yield
        return
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def _stub_pygmo():
    """`pygmo` e FORCE-importado por `desdeo_emo.EAs.__init__` (via NSGAIII/PPGA)
    e `selection.__init__` (NSGAIII_select) — todos `from pygmo import
    fast_non_dominated_sorting` no TOPO. O caminho do piso (MOEA_D/MOEAD_select)
    NUNCA instancia esses; pygmo e dep pesada (Boost), AUSENTE ate no env_c311.
    Stub minimo (so o simbolo importado, que nunca e chamado). [herdado do b5]."""
    if "pygmo" in sys.modules:
        return
    import types
    m = types.ModuleType("pygmo")

    def _absent(*_a, **_k):
        raise RuntimeError("pygmo e stub no env_b5 (nao usado pelo piso); "
                           "NSGAIII/PPGA nao entram no caminho do MOEA_D.")
    m.fast_non_dominated_sorting = _absent
    sys.modules["pygmo"] = m


def _import_vendored():
    """Poe o root vendorizado A FRENTE do `sys.path` e importa as classes.
    Root-first => o `desdeo_*` vendorizado ganha do pip. Confere que de fato
    resolveu p/ o vendorizado (senao para-e-loga: pip nao pode vencer).

    `MOEA_D` vem de `desdeo_emo.EAs.ProbMOEAD` — e a classe do MODE 12 (a mesma
    que o `Main_Execute.py:21/115` do repo usa; usa `MOEAD_select` PBI e arquiva
    por geracao). NAO e a `desdeo_emo.EAs.MOEAD.MOEA_D` (default TCH, outra
    implementacao)."""
    _stub_pygmo()
    while _VENDOR in sys.path:
        sys.path.remove(_VENDOR)
    sys.path.insert(0, _VENDOR)
    from desdeo_problem.Problem import DataProblem
    from desdeo_problem.surrogatemodels.SurrogateKriging import SurrogateKriging
    from desdeo_emo.EAs.ProbMOEAD import MOEA_D
    import desdeo_problem
    if not os.path.abspath(desdeo_problem.__file__).startswith(_VENDOR):
        raise RuntimeError(
            "root-first FALHOU: desdeo_problem resolveu p/ "
            + desdeo_problem.__file__ + " (esperado sob " + _VENDOR + "). "
            "Pin desdeo-emo = VENDORED (gate R3.2). Para-e-loga (D81).")
    _patch_lhs_seeding()
    return DataProblem, SurrogateKriging, MOEA_D


def _patch_lhs_seeding():
    """[herdado do b5 — DETERMINISMO; RATIFICADO DI-28.3] O pyDOE 0.9.1 MUDOU a
    API: `lhs(n, samples)` SEM `random_state`/`seed` cria um
    `np.random.default_rng()` FRESCO (semeado da entropia do SO) — IGNORA
    `np.random.seed()`. O vendorizado `create_new_individuals` chama
    `lhs(n, samples=pop_size)` exatamente assim, o que torna a POPULACAO INICIAL
    nao-reprodutivel (quebra o gate de determinismo e a nao-perturbacao).

    Fix runner-local (NAO edita o vendorizado — c311 tem copia propria): injeta
    `random_state = np.random.mtrand._rand` (o `RandomState` GLOBAL, que o runner
    SEMEIA via `iteration_seed`) quando o chamador nao passa semente. Isso replica
    EXATAMENTE o pyDOE classico (que usava `np.random.rand`, o global) — logo e
    fiel a intencao do desdeo, e agora deterministico. Declarado no sigma_dict."""
    from desdeo_emo.population import CreateIndividuals as _CI
    if getattr(_CI, "_piso_lhs_patched", False):
        return
    _orig = _CI.lhs

    def _seeded_lhs(n, samples=None, criterion=None, iterations=None,
                    random_state=None, seed=None, **kw):
        if random_state is None and seed is None:
            random_state = np.random.mtrand._rand      # global RandomState SEMEADO
        return _orig(n, samples=samples, criterion=criterion,
                     iterations=iterations, random_state=random_state,
                     seed=seed, **kw)

    _CI.lhs = _seeded_lhs
    _CI._piso_lhs_patched = True


def _params_efetivos(n_ds) -> dict:
    """[I-07] A config EFETIVA do moead_media para o ⑤ (CONTRATO §5)."""
    return {"alg": "moead_media", "mode": 12,
            "motor": ("MOEA/D mode 12 (Gen-MOEA/D, PBI) — a ABLACAO EXATA do "
                      "b5m: MOEAD_select em vez de ProbMOEAD_select, sem "
                      "maquinaria probabilistica (D77/DEF-E3)"),
            "surrogate": ("SurrogateKriging DESDEO — MESMA ESPECIFICACAO do b5, "
                          "treino INDEPENDENTE (DI-28)"),
            "sigma": "NULL por construcao (DI-16.1: 'o b5 sem σ')",
            "treino": "UNICO no dataset", "n_dataset": int(n_ds),
            "regime": "offline", "q": 1}


def _sigma_dict(n_ds):
    """DEF-C4: o dicionario que torna a ③ auditavel. Declara TODAS as excecoes do
    offline (② vazia, σ NULL, NULLs, o pin, a rampa θ, o overshoot) + a diferenca
    ANCORA vs o b5 (a selecao)."""
    return {
        "modelo": ("SurrogateKriging (DESDEO vendorizado): MESMA ESPECIFICACAO do "
                   "b5 — 1 GaussianProcess por objetivo; kernel "
                   "C(1,(1e-3,1e3))*RBF(10,(1e-2,1e2)), alpha=0, "
                   "n_restarts_optimizer=9, normalize_y=False (hard-coded na "
                   "SurrogateKriging.fit); treino UNICO no dataset, INDEPENDENTE "
                   "por config (offline nao retreina). [DI-28: 'mesma "
                   "ESPECIFICACAO, treino INDEPENDENTE' — nunca 'identico']."),
        "motor": ("MOEA/D mode 12 (Gen-MOEA/D, PBI) do DESDEO vendorizado: classe "
                  "MOEA_D (desdeo_emo.EAs.ProbMOEAD), selecao MOEAD_select "
                  "(decomposicao PBI), SEM maquinaria probabilistica — a ABLACAO "
                  "EXATA do b5m (mode 72, que usa ProbMOEAD_select). D77/DEF-E3."),
        # [I-04/A30] GRANULARIDADE DA ③ — a chave "1" do archive é a pop
        # INICIAL, não uma geração de seleção (Population.__init__ já a escreve;
        # o patch DI-16.16 re-carimba `str(gen_count−1)`, que já vale ≥2 na 1ª
        # `_next_gen`, então a chave "1" é ESTRUTURALMENTE inalcançável por ele).
        # Provado: `|pop| ger 1 == N_RV` em 45/45 células, LHS-perfeito em 727/727
        # dimensões na ger 1 (9/727 na ger 2), e a contabilidade de 40k FE fecha
        # 45/45 nesta leitura e falha 45/45 na outra.
        "granularidade_③": ("ger 1 = pop INICIAL (LHS, PRÉ-seleção); 2..n = "
                            "PÓS-seleção; passos de seleção = n_geracoes−1; "
                            "FE conta init+pop (bundle v2.2)"),
        "mu_*": "media a posteriori do GPR, em f de MINIMIZACAO (sem flip de sinal)",
        "sigma_*": ("NULL POR CONSTRUCAO (DI-16.1): o piso e 'o b5 sem σ' — o motor "
                    "seleciona SO pela media; a incerteza do GPR NAO e reportada "
                    "(nem na busca nem na sonda). O contraste da sonda piso x "
                    "b5r/b5m isola o VALOR de σ: MESMA ESPECIFICACAO de GP e os "
                    "MESMOS 20.000 pontos, diferindo SO em σ entrar (b5) ou nao "
                    "(piso) na selecao. ⚠ NAO e 'o mesmo GP byte-a-byte': o treino "
                    "e INDEPENDENTE por config (DI-28 — alg_id 21 vs 18 semeia RNGs "
                    "distintos; os 9 restarts do GPR podem convergir a μ nao "
                    "identico), entao a leitura R4 compara μ da MESMA especificacao, "
                    "nao μ presumido-igual. Excluir σ AQUI e o que torna o contraste "
                    "atribuivel so a σ."),
        "regime": "offline = candidatos da busca no surrogate · sonda = regua fixa (§17.2.2)",
        "espaco_modelo": "cru — o GP prediz em f nativa (o piso NAO transforma); transf_tipo/params NULL",
        "fe_treino_max": ("constante %d (=n_dataset-1) em TODA linha (busca+sonda) "
                          "— o modelo ve o dataset inteiro 1×." % (n_ds - 1)),
        "N_lattice": ("N = o LATTICE do b5m (Das-Dennis default do "
                      "BaseDecompositionEA: 50 vetores em M=2 / 105 em M=3) — "
                      "HERDADO sem override (lattice_resolution=None), IDENTICO ao "
                      "b5m. DI-16.4: N=100 seria residuo dos pisos ONLINE e mediria "
                      "DUAS variaveis (uso de σ E estrutura da busca)."),
        "pop_inicial_②": ("VAZIA POR CONSTRUCAO (DI-16.17): a pop inicial do motor "
                          "e LHS NOVO (create_new_individuals/LHSDesign) + SBX/PM "
                          "continuos => nenhum individuo coincide com o dataset; "
                          "real_solution_id=NULL em TODA linha de busca; "
                          "n_ds_membros=0 (no jsonl). O gate NAO exige ② nao-vazia."),
        "sonda_offline": ("1 bloco de 20.000 (§17.2.2), geracao=NULL (DI-13.5 — "
                          "carimbada pos-hoc no buffer, pois emit_sonda_block faz "
                          "int(geracao); precedente c149/b5._null_sonda). μ "
                          "preenchido, σ NULL. Custo FE=ZERO; RNG salvo/restaurado "
                          "(nao-perturbacao §3.1)."),
        "dist_min_arquivo": "NULL no offline — nao ha arquivo crescente/infill real [D-08]",
        "modelo_hp": ("NULL no offline — HP fixos, treino unico [D-08], idem b5. "
                      "RATIFICADO pelo autor (DI-30.B2, 2026-07-23): gravar HP no "
                      "piso e nao no b5m criaria assimetria espuria na ablacao."),
        "rampa_theta": ("a decomposicao PBI usa rampa θ funcao de "
                        "fe/total_function_evaluations (=40000, SEMPRE); por isso "
                        "40000 e obrigatorio mesmo com FE real=0."),
        "overshoot": ("terminacao por FE (>=40000): a ultima geracao que cruza o "
                      "teto completa o laco interno de N vetores => overshoot <= 1 "
                      "geracao, esperado e documentado."),
        "④_1_linha": ("④ = 1 LINHA (treino unico; molde b5): n_acumulado=n_dataset, "
                      "tempo_fit_s=wall do train, tempo_busca_s=wall do laco, "
                      "tempo_geracao_s EXCLUI a sonda (o motor e caixa-preta: "
                      "iterate() roda 10 geracoes sem gancho por geracao)."),
        "desdeo_emo_pin": ("VENDORED root-first, SEM pacote pip (gate R3.2; "
                           "content-hash b5_desdeo no repos.lock)."),
        "patches_vendorizados": ("b5-mode72-kde (ProbMOEAD_select.py) e "
                                 "b5-mode7-archive (BaseEA._next_gen) — INERTES "
                                 "para o mode 12: usa MOEAD_select (arquivo "
                                 "distinto) e MOEA_D._next_gen sobrescreve "
                                 "BaseDecompositionEA._next_gen sem super(). A ⑦ "
                                 "nasce reconstituivel da ③ NATIVAMENTE (MOEA_D "
                                 "arquiva ind/obj/unc pos-replace por geracao)."),
        "pyarrow": ("doe.py JA e pyarrow-12-safe (DI-26: combine_chunks().to_numpy) "
                    "=> o shim local do b5 NAO e usado aqui (validado no Fase 0)."),
        "pymoo": ("0.6.1.2 em env_b5 (finais ⑦ + filtro ND via src/problems.py; "
                  "shim py3.7 typing.Literal; puro-python sem Cython = so "
                  "velocidade, finais pequenos)."),
        "LHS_determinismo": ("o pyDOE 0.9.1 mudou a API: lhs(n,samples) SEM semente "
                             "usa np.random.default_rng() FRESCO (ignora "
                             "np.random.seed), tornando a pop inicial NAO-reprodutivel. "
                             "O runner injeta o RandomState GLOBAL semeado no lhs do "
                             "create_new_individuals (replica o pyDOE classico) — LHS "
                             "deterministico E fiel. RATIFICADO DI-28.3."),
    }


def _run(exp, problema, semente, *,
         data_root: str = naming.DEFAULT_DATA_ROOT,
         enable_bucket: bool = False, sonda_on: bool = True,
         teto_s: float | None = None) -> dict:
    t_run = time.time()
    status, motivo_parada = "ok", "orcamento"   # [DI-35.5] teto pode mudar
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)
    alg = _ALG
    modelo_flag = _MODELO_FLAG

    # ── seeds globais (D62/D91) ANTES do train — o GPR n_restarts=9 consome o
    #    RNG global do numpy, e o motor consome np.random/random p/ LHS+SBX+PM.
    #    Convencao D62/seeds.json com o alg_id (canonico, anti-descompasso;
    #    mesma escolha do b5 — ver handoff). ─────────────────────────────────
    base = H.seed_base(alg, semente)          # moead_media sem offset D22 => base=s
    random.seed(H.iteration_seed(base, _ALG_ID, 0, USO_RANDOM, bits32=True))
    np.random.seed(H.iteration_seed(base, _ALG_ID, 0, USO_NUMPY, bits32=True))

    DataProblem, SurrogateKriging, MOEA_D = _import_vendored()

    # ── [T7-sweep] a CÉLULA do grid sai do token exp (`sweep-<tier>-<dist>`) ──
    #    `tier/dist` = o par literal (manifesto/log); `t_ds/d_ds` = a VARIANTE
    #    de arquivo (small/lhs reusa o principal, sem sufixo — D90). Ver a nota
    #    completa em b5_prob.py (este é o gêmeo de ablação do b5m).
    #    ⚠ O roster do sweep (runs_matrix) NÃO inclui `moead_media` hoje — o fio
    #    fica pronto porque a SPEC §10/D38 PREVÊ o piso nos 3 tiers; o conflito
    #    artefato×SPEC está levantado à torre (handoff T7). Sem célula no grid,
    #    este caminho é inerte: `exp='off'` ⇒ (None, None) ⇒ comportamento atual.
    tier, dist = naming.parse_sweep(exp)
    t_ds, d_ds = naming.dataset_variant(exp)

    # ── orcamento OFFLINE = o dataset (D90; esgotado na carga; ① = n do tier) ─
    bud, ds = H.load_offline_budget(problema, semente, tier=t_ds, dist=d_ds,
                                    data_root=data_root)
    D, M, n_ds = ds["D"], ds["M"], ds["n"]
    X_ds = np.asarray(ds["X"], dtype=np.float64)
    F_ds = np.asarray(ds["F"], dtype=np.float64)

    # ── sonda OFFLINE: as 20.000 do artefato, 1× por modelo treinado ─────────
    sonda = H.load_sonda(problema, regime="offline", data_root=data_root)
    if sonda is None:          # [D102.10] sem sonda POR PROBLEMA — desarma, não some
        sonda_on = False

    buf = H.SnapshotBuffer()
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    sigma_dict = _sigma_dict(n_ds)

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="offline", maxfe=bud.maxfe,
                   n_dataset=n_ds, doe_hash=ds["x_hash"], f_hash=ds["f_hash"],
                   dataset_hash=ds.get("dataset_hash"),
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   # [D102.10] sem sonda POR PROBLEMA ⇒ declara em vez do hash.
                   **({"sonda": _sonda_decl()} if sonda is None else
                      {"sonda_x_hash": sonda["x_hash"], "sonda_S": sonda["S"]}),
                   tier=tier, dist=dist,             # [T7] a célula do grid
                   dataset_path=ds.get("path"))      # o arquivo REALMENTE lido

        # ── DataProblem (nomes 1-based, como Main_Execute) + bounds REAIS ────
        #    (NAO usar o read_dataset vendorizado: ele hard-coda bounds por
        #    testbench e nao conhece MMF1/DTLZ2/ZDT1.) ────────────────────────
        import pandas as pd
        xl, xu = H._bounds(problema)
        xn = ["x%d" % i for i in range(1, D + 1)]
        yn = ["f%d" % i for i in range(1, M + 1)]
        df = pd.DataFrame(np.hstack((X_ds, F_ds)), columns=xn + yn)
        bounds_df = pd.DataFrame(np.vstack((xl, xu)), columns=xn,
                                 index=["lower_bound", "upper_bound"])
        problem = DataProblem(data=df, variable_names=xn, objective_names=yn,
                              bounds=bounds_df)

        # ── fit UNICO (offline nao retreina), cronometrado ───────────────────
        t0 = time.time()
        with _quiet():
            problem.train(SurrogateKriging)     # kernel/alpha/n_restarts fixos
        t_fit = time.time() - t0
        buf.set_fe_treino_max(n_ds - 1)
        buf.add_timing(geracao=1, n_acumulado=n_ds, tempo_fit_s=t_fit)  # ④ 1 linha

        # ── predict do surrogate: (n,D) nativo -> (μ, None), f de MIN ────────
        #    O piso e "b5 sem σ" (DI-16.1): usa a MEDIA e DESCARTA a incerteza —
        #    `_predict` devolve σ=None => emit_sonda_block grava sigma_* NULL. O
        #    GPR .predict e deterministico => nao move RNG (nao-perturbacao
        #    trivial); o problem.evaluate ainda computa .uncertainity, mas ela
        #    nunca e reportada.
        def _predict(Xnat):
            r = problem.evaluate(np.asarray(Xnat, dtype=np.float64),
                                 use_surrogate=True)
            mu = np.asarray(r.objectives, dtype=np.float64).reshape(-1, M)
            return mu, None                       # σ NULL (DI-16.1)

        # ── SONDA: 1 bloco (S=20.000) emitido FORA do laco (tempo_geracao_s NAO
        #    inclui a sonda). geracao=1 na emissao -> NULL pos-hoc. ────────────
        t_snd = 0.0
        if sonda_on:
            t_snd = H.emit_sonda_block(
                buf, log, geracao=1, fe=bud.fe, sonda=sonda, predict=_predict,
                fe_treino_max=n_ds - 1, modelo_flag=modelo_flag,
                pred_tipo="valor", motivo="offline: 1x por modelo treinado",
                c3={"espaco_modelo": "cru"})
            _null_sonda_geracao(buf, sonda["S"])

        # ── MOEA/D interno (mode 12) sobre o surrogate — ZERO FE real ────────
        evolver = MOEA_D(problem, use_surrogates=True,
                         n_gen_per_iter=_GEN_PER_ITER,
                         total_function_evaluations=_FE_TOTAL)
        t_busca0 = time.time()
        # [BL-02] série do estado dos vetores POR GERAÇÃO (ver `_registra_vetores`)
        vetores_por_ger = {}
        ultima_ger_vet = _registra_vetores(evolver, vetores_por_ger, 0)
        with H.offline_guard(log, alg=alg, problema=problema):
            with _quiet():
                while evolver.continue_evolution():
                    # [DI-35.5] TETO UNIVERSAL — mesmo rito do b5.
                    if teto_s is not None and (time.time() - t_run) > teto_s:
                        status, motivo_parada = "failed", "teto_wall"
                        log.guard("teto_wall", fe=bud.fe,
                                  decorrido_s=round(time.time() - t_run, 1),
                                  teto_s=teto_s,
                                  acao="ABORTO LIMPO — curva parcial "
                                       "preservada; manifesto failed (D-07)")
                        break
                    evolver.iterate()
                    ultima_ger_vet = _registra_vetores(
                        evolver, vetores_por_ger, ultima_ger_vet)
        t_busca_total = time.time() - t_busca0

        # ── ③ busca: replay dos arquivos por geracao (o motor e caixa-preta) ─
        #    individuals/objectives_archive (chaves str(gen_count)): pop pos-
        #    substituicao (MOEA_D._next_gen arquiva pos-replace). A ⑦ e a ULTIMA
        #    geracao gravada. σ NULL => NAO leio uncertainty_archive.
        pop = evolver.population
        ind_arc = pop.individuals_archive
        obj_arc = pop.objectives_archive
        keys = sorted(ind_arc.keys(), key=lambda k: int(k))
        if not keys:
            raise RuntimeError(
                "piso: nenhum arquivo de geracao — a ③ ficaria vazia. Para-e-loga.")
        pop_final = None
        gen_final = int(keys[-1])
        for k in keys:
            g = int(k)
            Xg = np.asarray(ind_arc[k], dtype=np.float64)
            if Xg.ndim == 1:
                Xg = Xg.reshape(1, -1)
            ng = Xg.shape[0]
            Og = np.asarray(obj_arc[k], dtype=np.float64).reshape(ng, M)
            for i in range(ng):
                buf.add_surrogate(_export.surrogate_row(
                    g, Xg[i], regime="offline", real_solution_id=None,
                    mu=Og[i], sigma=None, pred_tipo="valor",   # σ NULL (DI-16.1)
                    modelo_flag=modelo_flag, espaco_modelo="cru",
                    fe_treino_max=n_ds - 1))
            # ⑥ (jsonl DI-10) por geracao — excecoes offline: modelo_hp/
            # dist_min_arquivo/tempo_busca_s = NULL (caixa-preta); tempo_fit_s
            # so na 1a geracao. ② vazia => n_ds_membros=0.
            log.decision(
                caminho="moead_media_gen",
                motivo="selecao no surrogate (MOEA/D mode 12, PBI; so a media)",
                geracao=g, n_ds_membros=0,
                # [BL-02] a CAUSA a montante da cadeia A8, agora medida também
                # no piso — sem ela o contraste b5m × ablação não fecha
                flag_vetores_degenerados=vetores_por_ger.get(g),
                **H.minimo_comum_di10(
                    Og, fe=bud.fe,
                    tempo_fit_s=(t_fit if g == int(keys[0]) else None)))
            pop_final = Xg
        pop_final = np.ascontiguousarray(pop_final, dtype=np.float64)

        # ── ⑦ __final: o ND final avaliado 1× na VERDADE (DI-08/DI-13.9) ────
        #    Caminho NATIVO (decs float64 em memoria) — fora do orcamento; o ND
        #    e filtrado DEPOIS da avaliacao real (nunca pela fantasia do modelo).
        from src import problems as _problems
        F_final = np.ascontiguousarray(
            _problems.evaluate_problem(H._instantiate(problema), pop_final),
            dtype=np.float64)
        n_fin = int(pop_final.shape[0])
        # nd_pos_real: NAO passar — o write_final o calcula sobre a vista FLOAT32
        # (a que a ⑦ persiste e que o final_eval --check re-le). Calcula-lo no
        # float64 cru cria assimetria float32/float64 em empates proximos e
        # reprova uma ⑦ correta (bug medido no b5m/ZDT1; docstring do write_final).
        H.write_final(
            exp, alg, problema, semente, pop_final, F_final,
            origem_solution_id=[None] * n_fin,        # sem vinculo c/ o dataset
            origem_geracao=[gen_final] * n_fin,
            origem_linha=np.arange(n_fin),
            data_root=data_root)
        # footer/retorno: conta o ND sobre a MESMA vista float32 da ⑦.
        nd_idx = set(int(i) for i in _problems._nds_filter(
            F_final.astype(np.float32).astype(np.float64)))

        # ── ④ = 1 LINHA: completa fit + busca (EXCLUINDO a sonda) ───────────
        buf.update_timing(1, tempo_busca_s=t_busca_total,
                          tempo_pred_sonda_s=t_snd,
                          tempo_geracao_s=t_fit + t_busca_total)

        timing_totais = _export.manifest_timing_block(
            tempo_total_s=time.time() - t_run, tempo_fit_surrogate_s=t_fit,
            # [I-02] NULL, não 0.0: no OFFLINE o orçamento nasce ESGOTADO (a ①
            # é o dataset, D90) e nenhuma avaliação real acontece DENTRO do run —
            # gravar zero afirmaria "avaliar custou zero". `bud.tempo_aval_real_s`
            # devolve None quando nenhuma avaliação passou pelo portão.
            tempo_busca_s=t_busca_total,
            tempo_aval_real_s=bud.tempo_aval_real_s,
            tempo_pred_sonda_s=t_snd)

        res = H.write_run_outputs(
            exp, alg, problema, semente, bud, buf, D=D, M=M,
            cp_hashes={"x_hash": ds["x_hash"], "f_hash": ds["f_hash"]},
            env=env, pinning=pinning, n_geracoes=gen_final,
            algo_version=ALGO_VERSION, timing_totais=timing_totais,
            sigma_dict=sigma_dict, regime="offline",
            # [I-07/A3] a config EFETIVA no ⑤ (CONTRATO §5): 45 células sem a
            # chave — 1.350 em 30 sementes.
            params=_params_efetivos(n_ds),
            sonda_info=(_sonda_decl() if sonda is None else   # [D102.10]
                        {"S": sonda["S"], "cadencia": "offline: 1x por modelo",
                         "n_blocos": 1 if sonda_on else 0,
                         "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]}),
            status=status, motivo_parada=motivo_parada, q=1,
            tier=tier, dist=dist,
            data_root=data_root, enable_bucket=enable_bucket)

        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=gen_final,
                   n_final=n_fin, n_nd_pos_real=len(nd_idx))
    except Exception as exc:                          # noqa: BLE001 — D23/D60
        # [T7-sweep] Gêmeo do b5: parada anômala = `failed` no manifesto, nunca
        # silenciosa. Ver a nota completa em `H.write_failed_manifest`.
        log.guard("erro_inesperado", detalhe=repr(exc))
        log.footer(status="failed", motivo=f"erro_{type(exc).__name__}",
                   fe_final=bud.fe, cp_init=None, cache_hits=bud.cache_hits)
        H.write_failed_manifest(
            exp, _ALG, problema, semente,
            motivo=f"erro_{type(exc).__name__}", regime="offline",
            maxfe=bud.maxfe, fe_final=bud.fe, tier=tier, dist=dist,
            env=env, pinning=pinning, algo_version=ALGO_VERSION,
            detalhe=repr(exc), data_root=data_root,
            enable_bucket=enable_bucket)  # [B-09] evidência do aborto sobe
        raise
    finally:
        log.close()

    return {
        "fe_final": bud.fe, "maxfe": bud.maxfe, "n_dataset": n_ds,
        "cp_init_ok": bool(res["cp_init_ok"]), "n_geracoes": gen_final,
        "n_final": n_fin, "n_nd_pos_real": len(nd_idx),
        "alg": alg, "mode": _MODE,
    }


def _sonda_decl() -> dict:
    """[D102.10] Bloco DECLARADO de sonda ausente POR PROBLEMA (⑤ e header ⑥)."""
    from src.experiment import SONDA_AUSENTE_INFO  # leve/lazy (sem ciclo)
    return dict(SONDA_AUSENTE_INFO)


def _null_sonda_geracao(buf, S):
    """geracao=NULL nas S linhas de sonda RECEM-emitidas (DI-13.5). O
    emit_sonda_block faz int(geracao) e nao aceita None; o runner completa as
    linhas do SEU buffer (precedente c149._stamp_c3_sonda / b5._null_sonda_geracao
    — mesma mutacao de buf.surr_rows[-S:]). A ORDEM do bloco fica intacta."""
    for row in buf.surr_rows[-int(S):]:
        assert row.get("regime") == "sonda", "bloco de sonda esperado"
        row["geracao"] = None
