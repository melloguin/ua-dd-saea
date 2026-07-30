"""[R3-b5] Prob-RVEA (b5r, mode 7) e Prob-MOEA/D (b5m, mode 72) — OFFLINE.

1 sessao = 1 cartao: este cobre os DOIS configs (b5r E b5m) e NAO toca em nenhum
outro algoritmo (em especial, NAO o mode 12 = moead_media, cartao proprio).

Roda em `env_b5` (py3.7.12 x86_64/Rosetta, sklearn 0.21.3) com o `desdeo_*`
VENDORIZADO em `algorithms/b5_Prob-RVEA/` A FRENTE do `sys.path` (root-first) — o
pip nao tem `desdeo-emo` (VENDORED e a fonte unica, cravado no gate R3.2, autor
delegou) e a `SurrogateKriging` de kernel fixo mora no `desdeo_problem`
vendorizado. NUNCA co-importar com c311 (N.1.2).

Molde: `standalone_harness.run_stubr3` (o encanamento offline) + e103 (④ = 1 linha
por retreino). Regime OFFLINE:
  - o dataset D90 E o orcamento (31D−1, ESGOTADO na carga; ① = o dataset);
  - surrogate GP treinado UMA vez no dataset (offline nao retreina);
  - MOEA interno sobre o surrogate: 40.000 avaliacoes-surrogate, ZERO FE real
    (`offline_guard` converte qualquer FE real em `OfflineBudgetViolation`);
  - ⑦ `__final`: o ND final avaliado 1× na VERDADE (`src/problems.py`, pos-hoc,
    fora do orcamento — DI-08/DI-13.9), reconstituivel da ③ (DI-16.16);
  - SONDA: 1 bloco de 20.000 por config, `geracao`=NULL (DI-13.5).

Patches vendorizados (ancoras b5-mode72-kde / b5-mode7-archive; re-lacrar com
`preflight --write`):
  - b5m: `ProbMOEAD_select.py:66-75` comentado (KDE morto + `plt_density` crashy);
  - b5r: `BaseEA._next_gen` re-carimba o arquivo POS-`keep()` (DI-16.16) — sem
    isso a ⑦ do mode 7 nasce irreconstituivel da ③ (defeito 🔴 do R3-00).
"""
from __future__ import annotations

# ── shim py3.7: o loader de NDS do pymoo 0.6.1.2 (env_b5, p/ os finais ⑦ via
#    src.problems) importa `typing.Literal`, que so existe em py3.8+. Precisa
#    existir ANTES de qualquer import de `src.problems`. [R3-b5/pymoo] ──────────
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


# ── identidade dos configs ────────────────────────────────────────────────────
_ALG_ID = {"b5r": 17, "b5m": 18}          # seeds.json (D91) — anti-descompasso
_MODE = {"b5r": 7, "b5m": 72}
_MODELO_FLAG = {"b5r": "b5r/ProbRVEA-v3+GPR", "b5m": "b5m/ProbMOEAD-PBI+GPR"}
USO_RANDOM = 1
USO_NUMPY = 2
ALGO_VERSION = "b5-prob-1.0"

# FE total do MOEA interno — SEMPRE 40000 (a rampa θ do APD divide por ele:
# `total_function_evaluations=0` daria ZeroDivision). Main_Execute.py:35.
_FE_TOTAL = 40000
_GEN_PER_ITER = 10                         # Main_Execute.py:34

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_VENDOR = os.path.join(_REPO, "algorithms", "b5_Prob-RVEA")


# ══════════════════════════════════════════════════════════════════════════════
#  Despacho (o `experiment.run` chama com `(exp, alg, problema, semente, **kw)`)
# ══════════════════════════════════════════════════════════════════════════════
def run_b5r(exp, alg, problema, semente, **kwargs):
    """b5r — Prob-RVEA_v3 (mode 7)."""
    return _run_b5("b5r", exp, problema, semente, **kwargs)


def run_b5m(exp, alg, problema, semente, **kwargs):
    """b5m — Prob-MOEA/D (mode 72)."""
    return _run_b5("b5m", exp, problema, semente, **kwargs)


# ── util: silenciar os prints verbosos do repo vendorizado ────────────────────
@contextlib.contextmanager
def _quiet():
    """Redireciona o stdout do repo vendorizado (Selection/FE count/warnings)
    — em 40k FE eles inundam o terminal (achado M3). `B5_VERBOSE=1` desliga o
    silenciamento p/ depuracao. NAO engole excecoes."""
    if os.environ.get("B5_VERBOSE"):
        yield
        return
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def _stub_pygmo():
    """`pygmo` e FORCE-importado por `desdeo_emo.EAs.__init__` (via NSGAIII/PPGA)
    e `selection.__init__` (NSGAIII_select) — todos `from pygmo import
    fast_non_dominated_sorting` no TOPO. O caminho do b5 (ProbRVEA_v3/ProbMOEAD)
    NUNCA instancia esses; pygmo e dep pesada (Boost), AUSENTE ate no env_c311 (o
    env desdeo irmao). Stub minimo (so o simbolo importado, que nunca e chamado).
    Fidelidade: nenhuma classe do b5 toca pygmo. [R3-b5/env — ver handoff]."""
    if "pygmo" in sys.modules:
        return
    import types
    m = types.ModuleType("pygmo")

    def _absent(*_a, **_k):
        raise RuntimeError("pygmo e stub no env_b5 (nao usado pelo b5); "
                           "NSGAIII/PPGA nao entram no caminho do b5.")
    m.fast_non_dominated_sorting = _absent
    sys.modules["pygmo"] = m


def _import_vendored():
    """Poe o root vendorizado A FRENTE do `sys.path` e importa as classes.
    Root-first => o `desdeo_*` vendorizado ganha do pip. Confere que de fato
    resolveu p/ o vendorizado (senao para-e-loga: pip nao pode vencer)."""
    _stub_pygmo()
    while _VENDOR in sys.path:
        sys.path.remove(_VENDOR)
    sys.path.insert(0, _VENDOR)
    from desdeo_problem.Problem import DataProblem
    from desdeo_problem.surrogatemodels.SurrogateKriging import SurrogateKriging
    from desdeo_emo.EAs.ProbRVEA import ProbRVEA_v3
    from desdeo_emo.EAs.ProbMOEAD import ProbMOEAD
    import desdeo_problem
    if not os.path.abspath(desdeo_problem.__file__).startswith(_VENDOR):
        raise RuntimeError(
            "root-first FALHOU: desdeo_problem resolveu p/ "
            + desdeo_problem.__file__ + " (esperado sob " + _VENDOR + "). "
            "Pin desdeo-emo = VENDORED (gate R3.2). Para-e-loga (D81).")
    _patch_lhs_seeding()
    return DataProblem, SurrogateKriging, {7: ProbRVEA_v3, 72: ProbMOEAD}


def _patch_lhs_seeding():
    """[R3-b5/env — DETERMINISMO] O pyDOE 0.9.1 MUDOU a API: `lhs(n, samples)` SEM
    `random_state`/`seed` cria um `np.random.default_rng()` FRESCO (semeado da
    entropia do SO) — IGNORA `np.random.seed()`. O vendorizado
    `create_new_individuals` chama `lhs(n, samples=pop_size)` exatamente assim, o
    que torna a POPULAÇÃO INICIAL não-reprodutível (quebra o gate de determinismo
    e a não-perturbação).

    Fix runner-local (NÃO edita o vendorizado — c311 tem cópia própria): injeta
    `random_state = np.random.mtrand._rand` (o `RandomState` GLOBAL, que o runner
    SEMEIA via `iteration_seed`) quando o chamador não passa semente. Isso replica
    EXATAMENTE o pyDOE clássico (que usava `np.random.rand`, o global) — logo é
    fiel à intenção do desdeo, e agora determinístico. Declarado no sigma_dict."""
    from desdeo_emo.population import CreateIndividuals as _CI
    if getattr(_CI, "_b5_lhs_patched", False):
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
    _CI._b5_lhs_patched = True


def _sigma_dict(alg, n_ds):
    """DEF-C4: o dicionario que torna a ③ auditavel. Declara TODAS as excecoes
    do offline (② vazia, NULLs, semantica do σ, o pin, a rampa θ, o overshoot)."""
    mode = _MODE[alg]
    if mode == 7:
        fidelidade = ("mode 7 (ProbRVEA_v3 / Prob_APD_select_v3): APD "
                      "probabilistico via aproximacao MEDIA-MC — DECLARADA "
                      "como aproximacao, NAO o Prob-APD publicado exato")
    else:
        fidelidade = ("mode 72 (ProbMOEAD / ProbMOEAD_select): comparacao MC "
                      "pareada (compute_probability_wrong_MC, P_wrong>0.5) — "
                      "QUASE-FIEL ao paper (o KDE morto foi removido)")
    return {
        "modelo": ("SurrogateKriging (DESDEO vendorizado): 1 GaussianProcess por "
                   "objetivo; kernel C(1,(1e-3,1e3))*RBF(10,(1e-2,1e2)), alpha=0, "
                   "n_restarts_optimizer=9, normalize_y=False (hard-coded na "
                   "SurrogateKriging.fit); treino UNICO no dataset (offline nao "
                   "retreina)."),
        "mu_*": "media a posteriori do GPR, em f de MINIMIZACAO (sem flip de sinal)",
        "sigma_*": ("DESVIO-PADRAO a posteriori do GPR por objetivo (NUNCA "
                    "variancia); mesma semantica em b5r e b5m (surrogate identico "
                    "— so a selecao difere)."),
        "regime": "offline = candidatos da busca no surrogate · sonda = regua fixa (§17.2.2)",
        "espaco_modelo": "cru — o GP prediz em f nativa (b5 NAO transforma); transf_tipo/params NULL",
        "fe_treino_max": ("constante %d (=n_dataset-1) em TODA linha (busca+sonda) "
                          "— o modelo ve o dataset inteiro 1×." % (n_ds - 1)),
        "pop_inicial_②": ("VAZIA POR CONSTRUCAO (DI-16.17): a pop inicial do motor "
                          "e LHS NOVO (create_new_individuals/LHSDesign) + SBX/PM "
                          "continuos => nenhum individuo coincide com o dataset; "
                          "real_solution_id=NULL em TODA linha de busca; "
                          "n_ds_membros=0 (no jsonl). O gate NAO exige ② nao-vazia."),
        "sonda_offline": ("1 bloco de 20.000 (§17.2.2), geracao=NULL (DI-13.5 — "
                          "carimbada pos-hoc no buffer, pois emit_sonda_block faz "
                          "int(geracao); precedente c149._stamp_c3_sonda). Custo "
                          "FE=ZERO; RNG salvo/restaurado (nao-perturbacao §3.1)."),
        "dist_min_arquivo": "NULL no offline — nao ha arquivo crescente/infill real [D-08]",
        "modelo_hp": "NULL no offline — HP fixos, treino unico [D-08]",
        "fidelidade_por_modo": fidelidade,
        "rampa_theta": ("o APD/decomposicao usa rampa θ funcao de "
                        "fe/total_function_evaluations (=40000, SEMPRE); por isso "
                        "40000 e obrigatorio mesmo com FE real=0."),
        "overshoot": ("terminacao por FE (>=40000): a ultima geracao que cruza o "
                      "teto completa (mate+add+select+keep) => overshoot <= 1 "
                      "geracao, esperado e documentado."),
        "④_1_linha": ("④ = 1 LINHA por config (cartao): n_acumulado=n_dataset, "
                      "tempo_fit_s=wall do train, tempo_busca_s=wall do laco, "
                      "tempo_geracao_s EXCLUI a sonda (o motor e caixa-preta: "
                      "iterate() roda 10 geracoes sem gancho por geracao)."),
        "desdeo_emo_pin": ("VENDORED root-first, SEM pacote pip (cravado no gate "
                           "R3.2; content-hash b5_desdeo no repos.lock)."),
        "patches_vendorizados": ("b5m: ProbMOEAD_select.py:66-75 comentado (KDE "
                                 "morto + plt_density crashy); b5r: "
                                 "BaseEA._next_gen re-carimba o arquivo pos-keep "
                                 "(DI-16.16). Ancoras b5-mode72-kde / "
                                 "b5-mode7-archive."),
        "pymoo": ("0.6.1.2 em env_b5 (finais ⑦ + filtro ND via src/problems.py; "
                  "shim py3.7 typing.Literal; puro-python sem Cython = so "
                  "velocidade, finais pequenos)."),
        "LHS_determinismo": ("o pyDOE 0.9.1 mudou a API: lhs(n,samples) SEM semente "
                             "usa np.random.default_rng() FRESCO (ignora "
                             "np.random.seed), tornando a pop inicial NAO-reprodutivel. "
                             "O runner injeta o RandomState GLOBAL semeado no lhs do "
                             "create_new_individuals (replica o pyDOE classico) — LHS "
                             "deterministico E fiel. [R3-b5/env — ver handoff]."),
    }


def _patch_doe_pyarrow_compat():
    """[R3-b5/env — BUG DE TORRE sinalizado no handoff] `doe._read_matrix_parquet`
    faz `ChunkedArray.to_numpy(zero_copy_only=False)`; o kwarg so existe em
    `Array.to_numpy`. Funciona no pyarrow 25 do env_main (onde o stub R3-00
    rodou) mas ESTOURA no pyarrow 12 do env_b5 — o caminho `load_dataset`
    (offline-Python) nunca fora exercitado (o Fase-0 so provou `load_sonda`).

    Shim LOCAL, nao edita o `doe.py` COMPARTILHADO (ha sessao R3-c311 concorrente
    que tocaria o mesmo arquivo): so ativa se o pyarrow corrente rejeitar o kwarg;
    saida BIT-IDENTICA (`combine_chunks()` -> Array). O fix central (b5 + c311 +
    moead_media) e da torre."""
    import pyarrow as pa
    try:
        pa.chunked_array([pa.array([0.0])]).to_numpy(zero_copy_only=False)
        return                                   # pyarrow corrente OK — nao mexe
    except TypeError:
        pass
    from src import doe as _doe_mod

    def _safe_read_matrix_parquet(path, columns):
        import pyarrow.parquet as pq
        t = pq.read_table(path, columns=columns)
        cols = [np.asarray(
                    t.column(c).combine_chunks().to_numpy(zero_copy_only=False),
                    dtype=np.float64)
                for c in columns]
        return np.ascontiguousarray(np.column_stack(cols), dtype=np.float64)

    _doe_mod._read_matrix_parquet = _safe_read_matrix_parquet


def _run_b5(alg, exp, problema, semente, *,
            data_root: str = naming.DEFAULT_DATA_ROOT,
            enable_bucket: bool = False, sonda_on: bool = True,
            teto_s: float | None = None, **_kwargs) -> dict:
    t_run = time.time()
    status, motivo_parada = "ok", "orcamento"   # [DI-35.5] teto pode mudar
    _patch_doe_pyarrow_compat()               # env_b5 pyarrow 12 (bug de torre)
    pinning = H.pin_runtime()
    env = H.env_info()
    semente = int(semente)
    mode = _MODE[alg]
    modelo_flag = _MODELO_FLAG[alg]

    # ── seeds globais (D62/D91) ANTES do train — o GPR n_restarts=9 consome o
    #    RNG global do numpy, e o motor consome np.random/random p/ LHS+SBX+PM.
    #    (O cartao L.16 diz `np.random.seed(s)`; a convencao do pipeline
    #    D62/c122/seeds.json usa iteration_seed c/ o alg_id — canonico e
    #    anti-descompasso. Seguimos a convencao; ver handoff.) ────────────────
    base = H.seed_base(alg, semente)          # b5 nao tem offset D22 => base=s
    random.seed(H.iteration_seed(base, _ALG_ID[alg], 0, USO_RANDOM, bits32=True))
    np.random.seed(H.iteration_seed(base, _ALG_ID[alg], 0, USO_NUMPY, bits32=True))

    DataProblem, SurrogateKriging, evolvers = _import_vendored()

    # ── [T7-sweep] a CÉLULA do grid sai do token exp (`sweep-<tier>-<dist>`) ──
    #    `tier/dist` = o par literal (vai ao manifesto/log); `t_ds/d_ds` = a
    #    VARIANTE de arquivo (small/lhs reusa o principal, sem sufixo — D90).
    #    Sem isto um run de sweep lia o dataset principal e gravava sob o nome
    #    do sweep: erro SILENCIOSO (o CP-init passa, pois confere contra o
    #    arquivo lido). Derivamos do exp — nunca de kwarg — p/ que o nome do
    #    run e os dados não possam divergir.
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

    buf = H.SnapshotBuffer()
    log = H.AuditLogger.for_run(exp, alg, problema, semente,
                                data_root=data_root, append=False)
    sigma_dict = _sigma_dict(alg, n_ds)

    try:
        log.header(alg=alg, versao=ALGO_VERSION, problema=problema, D=D, M=M,
                   semente=semente, regime="offline", maxfe=bud.maxfe,
                   n_dataset=n_ds, doe_hash=ds["x_hash"], f_hash=ds["f_hash"],
                   dataset_hash=ds.get("dataset_hash"),
                   ambiente=env, pinning=pinning, sigma_dict=sigma_dict,
                   sonda_x_hash=sonda["x_hash"], sonda_S=sonda["S"],
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

        # ── predict do surrogate: (n,D) nativo -> (μ,σ) (n,M), f de MIN ──────
        #    Usa o MESMO caminho do motor (problem.evaluate use_surrogates=True):
        #    .objectives = μ (media GPR), .uncertainity = σ (desvio GPR). GPR
        #    .predict e deterministico => nao move RNG (nao-perturbacao trivial).
        def _predict(Xnat):
            # DataProblem.evaluate(decision_vectors, use_surrogate) — SINGULAR
            # (o motor chama posicionalmente; aqui explicito o nome correto).
            r = problem.evaluate(np.asarray(Xnat, dtype=np.float64),
                                 use_surrogate=True)
            mu = np.asarray(r.objectives, dtype=np.float64).reshape(-1, M)
            sg = np.asarray(r.uncertainity, dtype=np.float64).reshape(-1, M)
            return mu, sg

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

        # ── MOEA interno sobre o surrogate — ZERO FE real ───────────────────
        EVOLVER = evolvers[mode]
        evolver = EVOLVER(problem, use_surrogates=True,
                          n_gen_per_iter=_GEN_PER_ITER,
                          total_function_evaluations=_FE_TOTAL)
        t_busca0 = time.time()
        with H.offline_guard(log, alg=alg, problema=problema):
            with _quiet():
                while evolver.continue_evolution():
                    # [DI-35.5] TETO UNIVERSAL (12h nas baterias): checado a
                    # cada iterate (10 geracoes, ~s). Aborto LIMPO com as
                    # camadas PARCIAIS (os archives ja acumulados viram a ③).
                    if teto_s is not None and (time.time() - t_run) > teto_s:
                        status, motivo_parada = "failed", "teto_wall"
                        log.guard("teto_wall", fe=bud.fe,
                                  decorrido_s=round(time.time() - t_run, 1),
                                  teto_s=teto_s,
                                  acao="ABORTO LIMPO — curva parcial "
                                       "preservada; manifesto failed (D-07)")
                        break
                    evolver.iterate()
        t_busca_total = time.time() - t_busca0

        # ── ③ busca: replay dos arquivos por geracao (o motor e caixa-preta) ─
        #    individuals/objectives/uncertainty_archive (chaves str(gen_count)):
        #    b5r pos mini-patch = sobreviventes POS-selecao; b5m = pop pos-
        #    substituicao. A ⑦ e a ULTIMA geracao gravada (invariante DI-16.16).
        pop = evolver.population
        ind_arc = pop.individuals_archive
        obj_arc = pop.objectives_archive
        unc_arc = pop.uncertainty_archive
        keys = sorted(ind_arc.keys(), key=lambda k: int(k))
        if not keys:
            raise RuntimeError(
                "b5: nenhum arquivo de geracao — a ③ ficaria vazia. Para-e-loga.")
        pop_final = None
        gen_final = int(keys[-1])
        for k in keys:
            g = int(k)
            Xg = np.asarray(ind_arc[k], dtype=np.float64)
            if Xg.ndim == 1:
                Xg = Xg.reshape(1, -1)
            ng = Xg.shape[0]
            Og = np.asarray(obj_arc[k], dtype=np.float64).reshape(ng, M)
            raw_u = unc_arc.get(k)
            Ug = (np.full((ng, M), np.nan) if raw_u is None
                  else np.asarray(raw_u, dtype=np.float64).reshape(ng, M))
            for i in range(ng):
                buf.add_surrogate(_export.surrogate_row(
                    g, Xg[i], regime="offline", real_solution_id=None,
                    mu=Og[i], sigma=Ug[i], pred_tipo="valor",
                    modelo_flag=modelo_flag, espaco_modelo="cru",
                    fe_treino_max=n_ds - 1))
            # ⑥ (jsonl DI-10) por geracao — excecoes offline: modelo_hp/
            # dist_min_arquivo/tempo_busca_s = NULL (caixa-preta); tempo_fit_s
            # so na 1a geracao. ② vazia => n_ds_membros=0.
            log.decision(
                caminho="b5_gen", motivo="selecao no surrogate (mode %d)" % mode,
                geracao=g, n_ds_membros=0,
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
        # float64 cru cria assimetria float32/float64 em empates proximos (medido
        # em b5m/ZDT1: 20 vs 19) e reprova uma ⑦ correta (docstring do write_final).
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
            sonda_info={"S": sonda["S"], "cadencia": "offline: 1x por modelo",
                        "n_blocos": 1 if sonda_on else 0,
                        "x_hash": sonda["x_hash"], "f_hash": sonda["f_hash"]},
            status=status, motivo_parada=motivo_parada, q=1,
            tier=tier, dist=dist,
            data_root=data_root, enable_bucket=enable_bucket)

        log.footer(status=status, fe_final=bud.fe, cp_init=True,
                   cache_hits=bud.cache_hits, n_geracoes=gen_final,
                   n_final=n_fin, n_nd_pos_real=len(nd_idx))
    except Exception as exc:                          # noqa: BLE001 — D23/D60
        # [T7-sweep] Parada anômala = `failed` NO MANIFESTO, nunca silenciosa.
        # Antes: a exceção subia e o run não deixava manifesto — e um run sem
        # manifesto SOME da varredura do portão (o total cai, nada fica
        # vermelho). Escrevemos a certidão e RE-LEVANTAMOS: o retry D23 do
        # despachante segue valendo e o caminho de sucesso é bit-intocado.
        log.guard("erro_inesperado", detalhe=repr(exc))
        log.footer(status="failed", motivo=f"erro_{type(exc).__name__}",
                   fe_final=bud.fe, cp_init=None, cache_hits=bud.cache_hits)
        H.write_failed_manifest(
            exp, alg, problema, semente,
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
        "alg": alg, "mode": mode,
    }


def _null_sonda_geracao(buf, S):
    """geracao=NULL nas S linhas de sonda RECEM-emitidas (DI-13.5). O
    emit_sonda_block faz int(geracao) e nao aceita None; o runner completa as
    linhas do SEU buffer (precedente c149._stamp_c3_sonda — mesma mutacao de
    buf.surr_rows[-S:]). A ORDEM do bloco fica intacta."""
    for row in buf.surr_rows[-int(S):]:
        assert row.get("regime") == "sonda", "bloco de sonda esperado"
        row["geracao"] = None
