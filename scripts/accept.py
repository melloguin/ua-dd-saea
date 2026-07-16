#!/usr/bin/env python3
"""accept.py — runner de aceitação OBJETIVA por cartão (Higiene v5.2 / D97).

Verifica SÓ o "encanamento" — checagens automáticas que bloqueiam a bateria:
  FE final exato, as 4 saídas válidas, CP-init, hash do DoE, e o andaime da
  Fase 0. NÃO julga fidelidade (isso é análise MANUAL do autor, a posteriori —
  D97; §20 da SPEC).

Uso:  python3 scripts/accept.py {CARTAO} [--exp main] [--alg c217] [--problema DTLZ2] [--semente 0]
Sai 0 se tudo verde; !=0 caso contrário. É o teste que o cartão referencia.

A nomenclatura das saídas vem de `src/naming.py` (fonte única §17.7/D55) — quem
VERIFICA um run e quem o ESCREVE (o despachante) consomem o MESMO módulo, então
não há como divergirem no nome do arquivo.
"""
import argparse, os, sys, tempfile, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # torna `src` importável

from src import naming  # fonte única da nomenclatura (§17.7)

EXPERIMENTS = os.path.join(ROOT, "data", "experiments")


def maxfe(problema_dim):
    return 31 * problema_dim - 1


# ── Checagens por run (cartões R1/R2/R3 — com --alg) ───────────────────────

def check_outputs(exp, alg, problema, semente, data_root=None):
    """As 4 saídas: 3 parquets (__real/__pop/__surrogate) + __timing + .jsonl."""
    data_root = data_root or os.path.join(ROOT, "data")
    d = naming.run_dir(exp, alg, data_root=data_root)
    need = naming.output_filenames(exp, alg, problema, semente)
    missing = [n for n in need if not os.path.exists(os.path.join(d, n))]
    if missing:
        return False, f"saídas faltando: {missing} (em {d})"
    return True, "4 saídas + jsonl presentes"


def check_fe(exp, alg, problema, semente, D, data_root=None):
    """FE final = 31D-1 EXATO — nº de linhas DISTINTAS da camada ① (D89)."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None, "pyarrow ausente — skip (instalar no env)"
    data_root = data_root or os.path.join(ROOT, "data")
    real = naming.layer_path(exp, alg, problema, semente, "real",
                             data_root=data_root)
    if not os.path.exists(real):
        return False, "camada ① ausente"
    n = pq.read_table(real).num_rows
    want = maxfe(D)
    return (n == want), f"FE={n} (esperado {want})"


def check_doe_hash(problema, semente, data_root=None):
    """CP-init (parte objetiva do harness, D87/D88): o DoE parquet existe E o
    hash do ARRAY DECODIFICADO bate com o do sidecar. Consome `src.naming`
    (fonte única do caminho) e `src.doe` (re-hash). Se `pyarrow`/`numpy` não
    estiverem no interpretador, cai p/ checagem de existência (skip do re-hash)."""
    from src import naming
    data_root = data_root or os.path.join(ROOT, "data")
    doe_p = naming.doe_path(problema, semente, data_root=data_root)
    man_p = naming.doe_manifest_path(problema, semente, data_root=data_root)
    if not os.path.exists(doe_p):
        return False, f"DoE ausente: {doe_p}"
    if not os.path.exists(man_p):
        return False, f"sidecar do DoE ausente: {man_p}"
    try:
        from src import doe as _doe
    except Exception:  # noqa: BLE001 — sem numpy/pyarrow: só confere existência
        return True, "DoE parquet + sidecar presentes (re-hash pulado: sem numpy/pyarrow)"
    with open(man_p, encoding="utf-8") as _mf:
        side = json.load(_mf)
    cols = side["columns"]
    back = _doe._read_matrix_parquet(doe_p, cols)
    h = _doe.decoded_hash(back)
    if h != side.get("doe_hash"):
        return False, f"hash do DoE diverge do sidecar ({h[:16]} != {str(side.get('doe_hash'))[:16]})"
    return True, f"DoE bit-a-bit OK (hash {h[:16]}… = sidecar)"


# ── Checagem de andaime da Fase 0 (F0-01-harness — sem run) ────────────────

def check_scaffold():
    """Encanamento do andaime comum (cartão F0-01-harness): os módulos de
    infra importam, a nomenclatura §17.7 está consistente, e manifesto + logger
    fazem round-trip. SEM algoritmo, SEM métrica — só o encanamento (D97)."""
    try:
        from src import atomic_io, manifest, audit_log, experiment  # noqa: F401
    except Exception as e:  # noqa: BLE001
        return False, f"import de módulo de infra falhou: {type(e).__name__}: {e}"

    # Catálogo A2: 25 problemas, MMF16_L3 removido; dispatch vazio na Fase 0.
    if len(experiment.ALL_PROBLEMS) != 25 or "MMF16_L3" in experiment.ALL_PROBLEMS:
        return False, f"catálogo != 25 canônicos (A2/§4): {len(experiment.ALL_PROBLEMS)}"
    if experiment.ALGORITHM_DISPATCH:
        return False, "ALGORITHM_DISPATCH deveria estar vazio na Fase 0 (R1/R2/R3 preenche)"

    # Nomenclatura §17.7 (base, camadas, jsonl, manifesto, blob).
    b = naming.base("main", "c217", "DTLZ2", 0)
    if b != "exp_main_c217_DTLZ2_0":
        return False, f"base inesperada: {b}"
    if naming.output_filenames("main", "c217", "DTLZ2", 0) != [
            f"{b}__real.parquet", f"{b}__pop.parquet", f"{b}__surrogate.parquet",
            f"{b}__timing.parquet", f"{b}.jsonl"]:
        return False, "output_filenames divergem da convenção §17.7"

    # Round-trip real do manifesto + logger num diretório temporário.
    with tempfile.TemporaryDirectory() as dr:
        assert manifest.is_run_done("main", "c217", "DTLZ2", 0, data_root=dr) is False
        man = manifest.new_manifest("main", "c217", "DTLZ2", 0, status="ok",
                                    bucket="mestrado_experiments", data_root=dr)
        mp = manifest.write_manifest(man, data_root=dr)
        back = manifest.read_manifest(mp)
        if back is None or back["run_id"] != "main_c217_DTLZ2_0":
            return False, "manifesto não fez round-trip"
        with audit_log.AuditLogger.for_run("main", "c217", "DTLZ2", 0, data_root=dr) as log:
            log.header(D=15, M=3, maxfe=maxfe(15))
            log.decision(caminho="estado_1", motivo="smoke")
            log.footer(status="ok", fe_final=maxfe(15))
        jp = naming.jsonl_path("main", "c217", "DTLZ2", 0, data_root=dr)
        with open(jp, encoding="utf-8") as f:
            recs = [json.loads(l)["rec"] for l in f]
        if recs != ["header", "decision", "footer"]:
            return False, f".jsonl inesperado: {recs}"

    return True, "andaime OK (infra importa · naming §17.7 · manifesto+jsonl round-trip)"


# ── Checagem do cartão F0-02-doe (DoE/dataset/seeds — sem run) ──────────────

def check_f0_02():
    """Encanamento objetivo do cartão F0-02-doe (D87/D88/D90/D91):

      1. `src/doe.py` importa; `seeds.json` (D91) publica os mapas canônicos.
      2. DoE bit-reprodutível: 2 chamadas de `generate_doe` = MESMO hash do
         array decodificado (D87) — a âncora exata do teste F0.
      3. Round-trip parquet: `ensure_doe` escreve e relê bit-a-bit (o hash do
         disco = o hash da memória) e o sidecar registra esse hash.
      4. Dataset offline (D90): F re-avaliado do `problems.py` canônico bate
         bit-a-bit com o F persistido (a metade Python do CP-init "avaliá-lo
         reproduz o F").

    NÃO faz o CP-init COMPLETO (X inicial na CAMADA ① de um run real, nos 2
    stacks) — isso depende do export ① (F0-03) + um run (R1-00): CORTE declarado
    (ver handoff). A metade MATLAB (`parquetread`→hash) roda por
    `scripts/check_doe_matlab.m`."""
    try:
        from src import doe
    except Exception as e:  # noqa: BLE001
        return False, f"import de src.doe falhou: {type(e).__name__}: {e}"

    # (1) seeds.json — mapas canônicos publicados e coerentes com o código.
    sp = os.path.join(ROOT, "claude_code_context", "artifacts", "seeds.json")
    try:
        with open(sp, encoding="utf-8") as _sf:
            sj = json.load(_sf)
    except Exception as e:  # noqa: BLE001
        return False, f"seeds.json ilegível: {e}"
    if len(sj.get("alg_id", {})) != 22:
        return False, f"seeds.json alg_id != 22 configs ({len(sj.get('alg_id', {}))})"
    shared = sj.get("shared_init_artifacts", {})
    if shared.get("problema_id") != doe.PROBLEMA_ID:
        return False, "seeds.json problema_id diverge de doe.PROBLEMA_ID (25 canônicos)"
    if shared.get("tier_id") != doe.TIER_ID or shared.get("dist_id") != doe.DIST_ID:
        return False, "seeds.json tier_id/dist_id divergem do código"
    if "SeedSequence" not in sj.get("materializacao", ""):
        return False, "seeds.json sem a fórmula de materialização (D91)"

    # (2) reprodutibilidade bit-a-bit (2 chamadas = mesmo hash) — 2 amostras.
    for prob, sem in (("MMF1", 0), ("ZDT4", 42)):
        h1 = doe.decoded_hash(doe.generate_doe(prob, sem)[0])
        h2 = doe.decoded_hash(doe.generate_doe(prob, sem)[0])
        if h1 != h2:
            return False, f"DoE {prob}/{sem} NÃO reprodutível ({h1[:12]} != {h2[:12]})"

    # (3) round-trip parquet + sidecar, num diretório temporário.
    with tempfile.TemporaryDirectory() as dr:
        r = doe.ensure_doe("MMF1", 0, data_root=dr)
        if r["skipped"]:
            return False, "ensure_doe pulou uma geração inédita (esperado skipped=False)"
        again = doe.ensure_doe("MMF1", 0, data_root=dr)
        if not again["skipped"] or again["doe_hash"] != r["doe_hash"]:
            return False, "2ª ensure_doe não foi idempotente (skip + mesmo hash)"

        # (4) dataset offline: F persistido = F re-avaliado do problems.py.
        rd = doe.ensure_dataset("MMF1", 0, data_root=dr)
        X, F, _ = doe.generate_dataset("MMF1", 0)
        from src import problems as _P
        F_re = _P.evaluate_problem(doe._instantiate_problem("MMF1"), X)
        if doe.decoded_hash(F) != doe.decoded_hash(F_re):
            return False, "dataset: F não reproduz do problems.py (CP-init Python falhou)"
        if not os.path.basename(rd["path"]).startswith("ds_MMF1_0.parquet"):
            return False, f"nome do dataset principal inesperado: {rd['path']}"

    return True, ("DoE bit-reprodutível (2 chamadas=mesmo hash) · round-trip parquet "
                  "+ sidecar · dataset F reproduz do problems.py · seeds.json coerente")


# ── Checagem do cartão F0-03-export (wrapper de FE + 3 camadas + gcs) ───────

def _f0_03_stub_run(exp, alg, problema, semente, data_root):
    """Roda um algoritmo-STUB (SEM algoritmo real) ponta-a-ponta pelo wrapper de
    FE (`src.budget`) + o export das 4 camadas (`src.export`), gravando local
    (caminho do Mac — sem GCS). Prova o ENCANAMENTO do cartão F0-03 (D89/D57/D53/
    D58); não julga fidelidade (D97). Retorna um dict com o que a checagem afere.

    O STUB: (1) carrega o DoE de (problema,semente) do F0-02 e avalia seus 11D−1
    pontos (fase init) pelo wrapper; (2) gasta 20D infills distintos (fase opt) →
    31D−1 distintos; (3) re-avalia um ponto do DoE → CACHE-HIT (0 FE, D89); (4) a
    32D−1-ésima X inédita levanta BudgetExhausted (hard-stop exato, D21). Grava as
    3 camadas + timing (§17.2), o .jsonl (§17.5) e o manifesto (§17.2/§17.7)."""
    import numpy as np
    from src import doe, budget, export, audit_log, manifest, gcs

    # (0) DoE compartilhado do F0-02 (D63) — CARREGADO, nunca regenerado no run.
    side = doe.ensure_doe(problema, semente, data_root=data_root)
    prob = doe._instantiate_problem(problema)
    D, M = int(prob.n_var), int(prob.n_obj)
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)
    doe_X = doe._read_matrix_parquet(side["path"], [f"x{i}" for i in range(D)])

    # objetivo STUB determinístico (o dedup é por X, o f é irrelevante ao gate).
    def true_f(x):
        return np.array([float(np.sum(x * (j + 1)) + j) for j in range(M)],
                        dtype=np.float64)

    log = audit_log.AuditLogger.for_run(exp, alg, problema, semente,
                                        data_root=data_root, append=False)
    bud = budget.FEBudget(D=D, logger=log)
    log.header(alg=alg, problema=problema, semente=semente, D=D, M=M,
               regime="online", maxfe=bud.maxfe, doe_hash=side["doe_hash"])

    # (1) init = os 11D−1 pontos do DoE (fase init).
    for i in range(doe_X.shape[0]):
        bud.evaluate(doe_X[i], true_f)

    # (2) opt = 20D infills distintos (na diagonal, em frações distintas).
    n_infill = 20 * D
    for i in range(n_infill):
        frac = (i + 1) / (n_infill + 2)
        x = xl + frac * (xu - xl)
        if bud.solution_id_of(x) is not None:            # colisão (prob≈0) → nudge
            x = x + (i + 1) * 1e-9 * (xu - xl)
        bud.evaluate(x, true_f)
        log.decision(caminho="infill", motivo=f"frac={frac:.4f}", fe=bud.fe)

    # (3) CACHE-HIT: re-avaliar o 1º ponto do DoE = 0 FE (D89).
    fe_antes = bud.fe
    bud.evaluate(doe_X[0], true_f)
    cache_hit_zero_fe = (bud.fe == fe_antes)

    # (4) hard-stop EXATO: a próxima X inédita levanta BudgetExhausted (D21).
    hard_stopped = False
    try:
        bud.evaluate(xu.copy(), true_f)                  # X inédita, saldo zerado
    except budget.BudgetExhausted:
        hard_stopped = True

    # ── camadas ② pop + ③ surrogate + timing (STUB — exercita os schemas) ──
    sids = [r.solution_id for r in bud.records]
    G = 3
    pop_rows = [(g, sid) for g in range(1, G + 1) for sid in sids[:5 + g]]

    srows, trows = [], []
    for g in range(1, G + 1):
        # regressor: μ/σ por objetivo, ligando ao ① via real_solution_id.
        for k in range(4):
            sid = sids[(g + k) % len(sids)]
            xk = bud.records[sid].x
            srows.append(export.surrogate_row(
                g, xk, real_solution_id=sid,
                mu=[0.5 * (g + j) for j in range(M)],
                sigma=[1e-3 * (g + 1) for _ in range(M)],
                pred_tipo="valor", modelo_flag="GP"))
        # C3: uma linha em espaço transformado (cru+params), mono-output estilo
        # b1 (mu_0 preenchido, mu_1.. NULL — §17.2/D47) — DEF-C3.
        srows.append(export.surrogate_row(
            g, bud.records[0].x, mu=[0.1 * g],
            pred_tipo="valor", modelo_flag="GP",
            espaco_modelo="transformado", transf_tipo="minmax",
            transf_params={"min": 0.0, "max": 1.0}))
        # classificador: exercita pred_classe/pred_score (μ/σ NULL) — DEF-C1.
        srows.append(export.surrogate_row(
            g, xu, pred_tipo="classe", pred_classe="bom",
            pred_confianca=0.83, modelo_flag="FNN"))
        # timing: um evento de retreino por geração (§17.6).
        trows.append({"geracao": g, "n_acumulado": bud.n_init + g * 5,
                      "tempo_fit_s": 0.001 * g, "tempo_busca_s": 0.002})
        log.timing(n_acumulado=bud.n_init + g * 5, tempo_fit_s=0.001 * g)

    export.write_real(exp, alg, problema, semente, bud.records, data_root=data_root)
    export.write_pop(exp, alg, problema, semente, pop_rows, data_root=data_root)
    export.write_surrogate(exp, alg, problema, semente, srows,
                           D=D, M=M, regime="online", data_root=data_root)
    export.write_timing(exp, alg, problema, semente, trows, data_root=data_root)

    # ── manifesto (D58/§17.2/§17.7): doe_hash ECOA o sidecar (CP-init por-run) ──
    doe_hash_run = doe.decoded_hash(bud.init_X())         # hash da init X do run
    fit_series = [{"iter": t["geracao"], "n_acumulado": t["n_acumulado"],
                   "tempo_fit_s": t["tempo_fit_s"]} for t in trows]
    man = manifest.new_manifest(
        exp, alg, problema, semente, status="ok",
        regime="online", maxfe=bud.maxfe, fe_final=bud.fe, n_geracoes=G,
        doe_hash=doe_hash_run, algo_version="stub-F0-03",
        timing={"tempo_total_s": 0.01, "tempo_fit_surrogate_s": 0.006,
                "tempo_busca_s": 0.002, "tempo_aval_real_s": 0.002},
        fit_series=fit_series, data_root=data_root)
    man["cache_hits"] = bud.cache_hits                   # D89 (evento, informativo)
    log.footer(status="ok", fe_final=bud.fe, n_geracoes=G, cache_hits=bud.cache_hits)
    log.close()
    manifest.write_manifest(man, data_root=data_root)

    # plano de destinos SEM rede (caminho local do Mac — não chama GCS).
    plan_local = gcs.plan_targets(exp, alg, problema, semente,
                                  enable_bucket=False, data_root=data_root)

    return {
        "D": D, "M": M, "maxfe": bud.maxfe, "fe_final": bud.fe,
        "n_init": bud.n_init, "cache_hits": bud.cache_hits,
        "cache_hit_zero_fe": cache_hit_zero_fe, "hard_stopped": hard_stopped,
        "doe_hash_run": doe_hash_run, "doe_hash_sidecar": side["doe_hash"],
        "plan_local": plan_local,
    }


def _check_export_schema(exp, alg, problema, semente, D, M, data_root):
    """As 3 camadas + timing batem EXATAMENTE com o schema §17.2 (nomes+tipos+
    nulabilidade), via `src.export.*_schema`. Prova o schema-as-code do cartão."""
    import pyarrow.parquet as pq
    from src import export
    want = {
        "real": export.real_schema(D, M),
        "pop": export.pop_schema(),
        "surrogate": export.surrogate_schema(D, M),
        "timing": export.timing_schema(),
    }
    for layer, sch in want.items():
        p = naming.layer_path(exp, alg, problema, semente, layer, data_root=data_root)
        got = pq.read_schema(p).remove_metadata()
        if not got.equals(sch, check_metadata=False):
            return False, (f"schema da camada {layer} diverge do §17.2 "
                           f"(esperado {sch.names}, obtido {got.names})")
    # a ③ tem de conter linhas de regressor (μ preenchido) E de classificador.
    surr = pq.read_table(naming.layer_path(exp, alg, problema, semente,
                                           "surrogate", data_root=data_root))
    import pyarrow.compute as pc
    n_mu = surr.num_rows - pc.sum(pc.is_null(surr.column("mu_0"))).as_py()
    n_classe = surr.num_rows - pc.sum(pc.is_null(surr.column("pred_classe"))).as_py()
    if n_mu == 0 or n_classe == 0:
        return False, f"③ não exercita C1 (μ preenchido={n_mu}, classe={n_classe})"
    # float32 nas colunas numéricas (D53) — checa uma de cada camada.
    import pyarrow as pa
    real_sch = pq.read_schema(naming.layer_path(exp, alg, problema, semente,
                                                "real", data_root=data_root))
    if real_sch.field("x0").type != pa.float32() or real_sch.field("f0").type != pa.float32():
        return False, "camada ① não está em float32 (D53)"
    return True, "schemas §17.2 exatos (①②③+timing) · ③ com C1 (μ+classe) · float32 (D53)"


def check_f0_03(exp="main", problema="MMF1", semente=0):
    """Encanamento objetivo do cartão F0-03-export (D89/D57/D53/D58/§17.2/§17.7):

      1. FE final = 31D−1 EXATO (avaliações reais distintas — D89).
      2. CACHE-HIT = 0 FE (re-avaliar X do DoE não move o saldo — D89) + hard-stop
         exato (BudgetExhausted na X inédita seguinte — D21).
      3. As 3 camadas + timing com o schema §17.2 (③ unificada C1: μ/σ + classe);
         float32 sem arredondamento (D53).
      4. Escrita ATÔMICA (zero `.tmp` residual — D58) e run pronto ⇒ skip (D58).
      5. `src/gcs.py`: import OK, `is_bucket_only` correto (D58), caminho LOCAL
         (plan sem rede) — no Mac NÃO chama GCS.
      6. CP-init por-run: `manifest['doe_hash']` (init X do run) = sidecar do DoE.

    Roda o STUB num diretório TEMP (não polui `data/`). SEM algoritmo real, SEM
    métrica, SEM julgamento de fidelidade (D97)."""
    alg = "stub"
    try:
        from src import gcs, budget, export  # noqa: F401 — import-gate dos módulos novos
    except Exception as e:  # noqa: BLE001
        return [("import dos módulos F0-03 (budget/export/gcs)",
                 (False, f"{type(e).__name__}: {e}"))]

    results = []
    with tempfile.TemporaryDirectory() as dr:
        # run-done é False ANTES de rodar (D58).
        pre_done = export.run_done(exp, alg, problema, semente, data_root=dr)

        try:
            info = _f0_03_stub_run(exp, alg, problema, semente, data_root=dr)
        except Exception as e:  # noqa: BLE001 — qualquer erro = VERMELHO (pára-e-loga)
            import traceback
            return [("STUB ponta-a-ponta",
                     (False, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))]

        D, M, mfe = info["D"], info["M"], info["maxfe"]

        # (1) FE final exato (D89).
        results.append(("FE final = 31D−1 exato (D89)",
                        check_fe(exp, alg, problema, semente, D, data_root=dr)))

        # (2) cache-hit=0 FE + hard-stop (D89/D21).
        ok2 = (info["cache_hit_zero_fe"] and info["cache_hits"] >= 1
               and info["hard_stopped"] and info["fe_final"] == mfe)
        results.append(("cache-hit = 0 FE + hard-stop exato (D89/D21)",
                        (ok2, f"cache_hits={info['cache_hits']} "
                              f"(0-FE={info['cache_hit_zero_fe']}), "
                              f"hard_stop={info['hard_stopped']}, "
                              f"fe_final={info['fe_final']}=={mfe}")))

        # (3) 4 saídas + schema §17.2 + float32.
        results.append(("4 saídas presentes (§17.7)",
                        check_outputs(exp, alg, problema, semente, data_root=dr)))
        results.append(("schema §17.2 (①②③+timing) + float32 (D53)",
                        _check_export_schema(exp, alg, problema, semente, D, M, dr)))

        # (4) escrita atômica (sem .tmp) + run pronto ⇒ skip (D58).
        rundir = naming.run_dir(exp, alg, data_root=dr)
        tmps = [f for f in os.listdir(rundir) if f.endswith(".tmp")]
        post_done = export.run_done(exp, alg, problema, semente, data_root=dr)
        results.append(("escrita atômica (0 .tmp) + skip idempotente (D58)",
                        ((not tmps and post_done and not pre_done),
                         f"tmp_residual={tmps}, run_done: pre={pre_done} post={post_done}")))

        # (5) gcs.py: bucket-only + caminho local (sem rede).
        bo_ok = (gcs.is_bucket_only("c149") and gcs.is_bucket_only("c262")
                 and not gcs.is_bucket_only("c217")
                 and not gcs.is_bucket_only("c149", "real"))
        plan = info["plan_local"]
        local_only = all(t["blob"] is None for t in plan.values()) and all(
            os.path.exists(plan[k]["local"])
            for k in ("real", "pop", "surrogate", "timing", "jsonl", "manifest"))
        try:                                   # a lib de gcs está ausente no Mac?
            import google.cloud.storage  # noqa: F401
            gcs_present = True
        except Exception:  # noqa: BLE001
            gcs_present = False
        results.append(("gcs.py: bucket-only (D58) + caminho local sem rede",
                        ((bo_ok and local_only),
                         f"bucket_only_ok={bo_ok}, local_only={local_only}, "
                         f"gcs_lib_no_mac={'ausente' if not gcs_present else 'presente'}")))

        # (6) CP-init por-run: manifest doe_hash = sidecar do DoE (D87/D88).
        cp_ok = (info["doe_hash_run"] == info["doe_hash_sidecar"])
        results.append(("CP-init por-run: manifest doe_hash = sidecar (D87/D88)",
                        (cp_ok, f"run={str(info['doe_hash_run'])[:16]}… "
                                f"{'=' if cp_ok else '!='} sidecar")))

        # regressão do gate F0-02 (o mesmo DoE materializado no temp valida CP-init).
        results.append(("regressão F0-02: DoE bit-a-bit (CP-init)",
                        check_doe_hash(problema, semente, data_root=dr)))

    return results


# ── Checagem do cartão F0-04-metrica (esqueleto da métrica + âncora D92) ────

#: Tolerância da âncora do smoke (D92). O HV discreto do front denso converge a
#: 1,0433 (analítico 1,21 − 1/6); 5e-4 separa com folga do ref errado (1,0 →
#: 0,8333, Δ≈0,21) e do não-normalizado (ordens de grandeza), sem exigir mais
#: densidade do que o necessário.
_TOL_HV_ANCHOR = 5e-4


def _f0_04_stub_real(dr, problema="MMF1"):
    """Escreve uma camada ① STUB com objetivos REAIS de `problema` (pontos do
    front + alguns dominados, dominados PRIMEIRO para a trajetória convergir) e
    devolve `(exp, alg, problema, semente)`. Prova a leitura ponta-a-ponta da ①
    pela métrica — SEM algoritmo, SEM fidelidade (D97). Não é um run de FE-exato
    (isso é o F0-03); a métrica opera sobre QUALQUER ①."""
    import numpy as np
    from src import problems as _P, budget, export, experiment
    prob = experiment._instantiate_problem(problema)
    Xf, Ff = prob.true_pareto_front(n=20)                 # pontos SOBRE o front
    rng = np.random.default_rng(0)
    Xd = prob.xl + rng.random((10, prob.n_var)) * (prob.xu - prob.xl)
    Fd = _P.evaluate_problem(prob, Xd)                    # pontos dominados
    X = np.vstack([Xd, Xf]); F = np.vstack([Fd, Ff])      # dominados → front
    recs = [budget.RealEval(solution_id=i, x=X[i], f=F[i], fe_index=i,
                            fase=("init" if i < Xd.shape[0] else "opt"))
            for i in range(X.shape[0])]
    export.write_real("main", "stub", problema, 0, recs, data_root=dr)
    return "main", "stub", problema, 0


def check_f0_04():
    """Encanamento objetivo do cartão F0-04-metrica (§12/D69/D70/D92):

      1. `src/metrics.py` importa (esqueleto da camada pós-hoc).
      2. **SMOKE DECISIVO (D92):** HV(front verdadeiro do BBOB_F1, normalizado
         por (ideal,nadir) da S.5, ref = 1,1 por coordenada) = **1,0433** (± tol).
      3. Sanity do FRONT (0,8333 = ref no nadir 1,0) — rotulado, **NÃO é o gate**.
      4. As 5 métricas rodam (IGD/IGD+/HV/GD/spacing): front vs front → IGD/IGD+/
         GD = 0; HV = âncora; spacing ≥ 0 e > 0 num conjunto não-uniforme.
      5. Lê a camada ① ponta-a-ponta: normaliza → métricas FINAIS + trajetória.
      6. Normalização D69 = tabela S.5 (25 problemas; o F1 bate com o front vivo).

    SEM algoritmo, SEM julgamento de fidelidade (D97). Fecha a Fase 0."""
    try:
        import numpy as np
        from src import metrics
    except Exception as e:  # noqa: BLE001 — import-gate dos módulos da métrica
        return [("import da camada de métrica (src.metrics)",
                 (False, f"{type(e).__name__}: {e}"))]

    results = []

    # (2) SMOKE DECISIVO — a âncora D92 que fecha a Fase 0.
    try:
        hv_smoke = metrics.hv_smoke_bbob_f1()
        d = abs(hv_smoke - metrics.HV_SMOKE_BBOB_F1)
        results.append((
            "SMOKE D92: HV(BBOB_F1, ref=1,1/coord, normalizado) = 1,0433",
            (d < _TOL_HV_ANCHOR,
             f"HV={hv_smoke:.5f} (|Δ|={d:.1e} < tol {_TOL_HV_ANCHOR:.0e})")))
    except Exception as e:  # noqa: BLE001
        import traceback
        return [("SMOKE D92: HV(BBOB_F1) = 1,0433",
                 (False, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))]

    # (3) sanity do FRONT (0,8333) — rotulado; NÃO confundir com o gate (D92).
    hv_sanity = metrics.hv_front_sanity_bbob_f1()
    ds = abs(hv_sanity - metrics.HV_SANITY_BBOB_F1)
    results.append((
        "sanity do FRONT (0,8333 = ref no nadir 1,0 — NÃO é o gate; D92)",
        (ds < _TOL_HV_ANCHOR, f"HV_sanity={hv_sanity:.5f} (|Δ|={ds:.1e})")))

    # (4) as 5 métricas rodam + são sãs (front vs front = 0; spacing>0 se irregular).
    Rraw = metrics.true_front_raw("BBOB_F1", 2000)
    ideal, nadir = metrics.reference_bounds("BBOB_F1")
    Rn = metrics.normalize(Rraw, ideal, nadir)
    igd0 = metrics.igd(Rn, Rn)
    igdp0 = metrics.igd_plus(Rn, Rn)
    gd0 = metrics.gd(Rn, Rn)
    hv_front = metrics.hv(Rn, metrics.HV_REF_COORD)
    sp_uniform = metrics.spacing(Rn)                      # front analítico ⇒ ~0
    sp_irreg = metrics.spacing(np.array(                  # gaps irregulares ⇒ > 0
        [[0.0, 1.0], [0.02, 0.9], [0.05, 0.6], [0.5, 0.5], [0.55, 0.1]]))
    five_ok = (igd0 < 1e-9 and igdp0 < 1e-9 and gd0 < 1e-9
               and abs(hv_front - metrics.HV_SMOKE_BBOB_F1) < 1e-3
               and sp_uniform >= 0.0 and sp_irreg > 0.0)
    results.append((
        "5 métricas rodam · front×front→IGD/IGD+/GD=0 · HV=âncora · spacing sã",
        (five_ok, f"IGD={igd0:.1e} IGD+={igdp0:.1e} GD={gd0:.1e} "
                  f"HV={hv_front:.4f} spacing(unif)={sp_uniform:.1e} "
                  f"spacing(irreg)={sp_irreg:.3f}")))

    # (5) lê a camada ① ponta-a-ponta → normaliza → métricas + trajetória.
    try:
        with tempfile.TemporaryDirectory() as dr:
            exp, alg, prob, sem = _f0_04_stub_real(dr, "MMF1")
            res = metrics.metrics_from_real(exp, alg, prob, sem, data_root=dr,
                                            n_checkpoints=5)
            fin = res["final"]; traj = res["trajectory"]
            need = {"igd", "igd_plus", "hv", "gd", "spacing", "n_nd"}
            read_ok = (need <= set(fin) and len(traj) >= 2
                       and all(k in traj[0] for k in ("fe", "igd_plus", "hv"))
                       and np.isfinite(fin["igd_plus"])
                       and traj[0]["igd_plus"] >= traj[-1]["igd_plus"])  # converge
            msg = (f"final IGD+={fin['igd_plus']:.4f} HV={fin['hv']:.4f} "
                   f"n_nd={fin['n_nd']} · trajetória {len(traj)} pts "
                   f"(IGD+ {traj[0]['igd_plus']:.3f}→{traj[-1]['igd_plus']:.3f})")
    except Exception as e:  # noqa: BLE001
        import traceback
        read_ok, msg = False, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    results.append(("lê a ① ponta-a-ponta: normaliza → métricas + trajetória",
                    (read_ok, msg)))

    # (6) normalização D69 = S.5 congelada (25 problemas; F1 bate com o front vivo).
    from src import experiment
    front_nadir = metrics.true_front_raw("BBOB_F1", 2000).max(axis=0)
    n_probs = len(metrics.F_MIN_MAX)
    tbl_ok = (n_probs == 25
              and set(metrics.F_MIN_MAX) == set(experiment.ALL_PROBLEMS)
              and np.allclose(nadir, front_nadir, rtol=1e-3))
    results.append((
        "normalização D69 = tabela S.5 (25 problemas; F1 nadir = front vivo)",
        (tbl_ok, f"|F_MIN_MAX|={n_probs}, F1 nadir S.5={nadir.tolist()} "
                 f"~ front {front_nadir.round(3).tolist()}")))

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartao")
    ap.add_argument("--exp", default="main")
    ap.add_argument("--alg", required=False)
    ap.add_argument("--problema", default="ZDT1")
    ap.add_argument("--semente", default="0")
    ap.add_argument("--dim", type=int, default=30)
    a = ap.parse_args()

    print(f"== Aceitação objetiva — cartão {a.cartao} "
          f"({a.exp}/{a.alg}/{a.problema}/{a.semente}) ==")

    # F0-02 = artefatos de inicialização (DoE/dataset/seeds — D87/D88/D90/D91).
    # Encanamento próprio (sem run); não cai no andaime genérico do F0-01.
    if a.cartao.startswith("F0-02"):
        ok, msg = check_f0_02()
        print(f"  [{'OK  ' if ok else 'FAIL'}] F0-02 (DoE/dataset/seeds): {msg}")
        print("  [INFO] CP-init COMPLETO (X da camada ① nos 2 stacks) = R1-00/F0-03 "
              "(corte declarado); metade MATLAB via scripts/check_doe_matlab.m.")
        print("\n  >>> " + ("VERDE (encanamento objetivo)" if ok
                            else "VERMELHO — pára-e-loga (D81)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(0 if ok else 1)

    # F0-03 = wrapper de FE + 3 camadas de export + gcs (D89/D57/D53/D58/§17.2).
    # Encanamento próprio: roda um STUB ponta-a-ponta num tempdir e afere tudo.
    if a.cartao.startswith("F0-03"):
        results = check_f0_03(exp=a.exp, problema=a.problema, semente=a.semente)
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("  [INFO] STUB (sem algoritmo real): prova só o ENCANAMENTO — FE/"
              "cache-hit/schemas/atômico/gcs-local/CP-init. GCS real = VM (§17.7).")
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # F0-04 = esqueleto da camada de métrica + âncora do smoke (D92 = 1,0433).
    # Encanamento próprio: import-gate + smoke HV + as 5 métricas + leitura da ①.
    if a.cartao.startswith("F0-04"):
        results = check_f0_04()
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("  [INFO] ESQUELETO (casca): as funções-núcleo + a ÂNCORA D92. A "
              "análise COMPLETA (agregação 30 sementes, testes §14, §15) = R4 "
              "(o autor refina/implementa — D100).")
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo) — FECHA a Fase 0"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # F0-01 é PURO andaime (sem run). Idem qualquer cartão chamado sem --alg:
    # valida-se só o encanamento comum e o veredito é o do andaime.
    if a.cartao.startswith("F0-01") or not a.alg:
        ok, msg = check_scaffold()
        print(f"  [{'OK  ' if ok else 'FAIL'}] andaime F0-01 (encanamento): {msg}")
        if not a.alg and not a.cartao.startswith("F0-01"):
            print("  (sem --alg: apenas o andaime foi validado; passe --alg "
                  "para checar um run.)")
        print("\n  >>> " + ("VERDE (encanamento objetivo)" if ok
                            else "VERMELHO — pára-e-loga (D81)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(0 if ok else 1)

    checks = [
        ("4 saídas válidas", check_outputs(a.exp, a.alg, a.problema, a.semente)),
        ("FE final = 31D-1", check_fe(a.exp, a.alg, a.problema, a.semente, a.dim)),
        ("DoE (CP-init)",    check_doe_hash(a.problema, a.semente)),
    ]
    fail = False
    for name, (ok, msg) in checks:
        mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
        print(f"  [{mark}] {name}: {msg}")
        if ok is False:
            fail = True
    print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                        else "VERDE (encanamento objetivo)"))
    print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
          "a posteriori — não entra aqui.")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
