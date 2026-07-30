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


def fe_esperado_por_exp(exp, problema, semente, D, data_root=None, q=1):
    """FE final esperado por CÉLULA do grid — a fonte única do gate (D66/D90).

    Três regimes:
      - `main` (online principal) ⇒ **31D−1** (D21);
      - `batch` (online, q=10) ⇒ **11D−1 + 200·q** — o `q` vem do MANIFESTO
        (D66; delegado a `budget.maxfe_por_exp`, a MESMA fonte do runner);
      - `sweep-<tier>-<dist>` (offline) ⇒ o `n` do dataset DAQUELE tier, **lido
        do sidecar do artefato** (nunca hard-coded 2000/50000 — duplicar a
        constante criaria duas fontes da verdade). `off` = o principal (31D−1).

    Devolve `(n, origem)`; `(None, motivo)` se o sidecar do sweep faltar — o
    chamador reprova com mensagem honesta em vez de comparar contra um número
    inventado.
    """
    if exp == "batch":
        try:
            from src import budget as _bud
            n = _bud.maxfe_por_exp("batch", D, q)
        except Exception as e:                         # noqa: BLE001
            return None, f"orçamento batch indeterminado: {e}"
        return int(n), f"11D−1+200·q (D={D}, q={q}) = {int(n)}"
    tier, dist = naming.parse_sweep(exp)
    if tier is None:                       # main/off → o principal
        return maxfe(D), f"31D−1 (D={D})"
    t, d = naming.dataset_variant(exp)     # small/lhs reusa o principal
    data_root = data_root or os.path.join(ROOT, "data")
    side = naming.dataset_manifest_path(problema, semente, t, d,
                                        data_root=data_root)
    if not os.path.exists(side):
        return None, f"sidecar do dataset {tier}/{dist} ausente: {side}"
    with open(side, encoding="utf-8") as fh:
        meta = json.load(fh)
    n = meta.get("n_rows", meta.get("n"))
    if n is None:
        return None, f"sidecar sem n_rows/n: {side}"
    return int(n), f"|dataset {tier}/{dist}| = {int(n)} (sidecar)"


def n_dataset_esperado(exp, problema, semente, D, data_root=None):
    """Compat. [T7-sweep]: alias offline de `fe_esperado_por_exp` (q ignorado)."""
    return fe_esperado_por_exp(exp, problema, semente, D, data_root=data_root)


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
    """FE final = 31D-1 EXATO — nº de linhas DISTINTAS da camada ① (D89).

    O D é DERIVADO das colunas `x0..x{D-1}` da própria camada ① (a fonte da verdade
    do run); o argumento `--dim` é apenas FALLBACK. Isso elimina o footgun de um
    `--dim` errado (default 30) produzir um veredito falso — o gate tem que ser
    confiável na bateria automática (M8)."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None, "pyarrow ausente — skip (instalar no env)"
    data_root = data_root or os.path.join(ROOT, "data")
    # [T7-sweep/T6-batch] a expectativa é POR CÉLULA: 31D−1 no principal,
    # |dataset do tier| no sweep (sidecar), 11D−1+200q no batch (q do manifesto).
    # Sem isto um run sweep-medium (n=2000) ou batch (FE=2021) correto seria
    # reprovado por um gate que só sabia 31D−1.
    q_run, _man = 1, {}
    manp = naming.manifest_path(exp, alg, problema, semente, data_root=data_root)
    if os.path.exists(manp):
        try:
            with open(manp, encoding="utf-8") as _fh:
                _man = json.load(_fh)
            q_run = int(_man.get("q", 1) or 1)
        except Exception:                              # noqa: BLE001
            q_run, _man = 1, {}
    # [DI-38] Aborto SANCIONADO (teto de wall / cache-cap): o FE final é MENOR
    # que o orçamento POR DESENHO — a curva parcial é o entregável. Checa ANTES
    # da camada ①: no rito BoTorch o aborto por teto não grava parquets (a ①
    # ausente é por desenho, não falha — DI-38a). Fonte ÚNICA do skip (antes
    # vivia só no cartão do e81 e o gate genérico reprovaria exatamente as
    # células que a DI-37.1 sanciona).
    # [B-06] a lista vem do ARTEFATO `artifacts/motivos_parada.json` (fonte única)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from gates_proveniencia import motivo_e_sancionado as _sancionado
    if _man.get("status") == "failed" and _sancionado(_man.get("motivo_parada")):
        return None, (f"SKIP — aborto sancionado ({_man.get('motivo_parada')}): "
                      f"fe_final={_man.get('fe_final')} por desenho; "
                      f"a curva parcial é o entregável")
    real = naming.layer_path(exp, alg, problema, semente, "real",
                             data_root=data_root)
    if not os.path.exists(real):
        return False, "camada ① ausente"
    tbl = pq.read_table(real)
    n = tbl.num_rows
    d_data = sum(1 for c in tbl.column_names
                 if len(c) > 1 and c[0] == "x" and c[1:].isdigit())
    if d_data:                       # D do próprio run (não confia no --dim)
        D = d_data
    want, origem = fe_esperado_por_exp(exp, problema, semente, D,
                                       data_root=data_root, q=q_run)
    if want is None:
        return False, f"expectativa de FE indeterminada — {origem}"
    return (n == want), f"FE={n} (esperado {want} · {origem})"


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


# ── Checagem do cartão R2-00-harness (infra BoTorch — contrato N.1/§22.3) ───

def _r2_00_gcs_smoke(exp, alg, problema, semente, data_root):
    """SMOKE GCS REAL — o deferido do F0-03 (§17.7/§22.3): exercita o dual-write
    contra o bucket DE VERDADE (ADC do Mac) e LIMPA os blobs de teste ao fim.

      1. `gcs.mirror_run` sobe as 4 camadas + jsonl + manifesto do run stubpy.
      2. Byte-identidade: sha256(blob baixado) == sha256(arquivo local), blob a
         blob (a prova "local+bucket byte-idêntico" do piloto §22.3).
      3. Sync de pendentes: deleta 1 blob e `gcs.sync_pending` o re-sobe.
      4. DELETE de TODOS os blobs de teste (finally — nada de lixo no bucket;
         o versionamento retém non-current por 7d, sem custo relevante).

    Retorna (ok|None, msg). None = lib gcs ausente (skip — rode onde ela exista)."""
    import hashlib
    from src import gcs as _gcs
    try:
        from google.cloud import storage
    except ImportError:
        return None, "google-cloud-storage ausente neste env — smoke pulado"
    client = storage.Client(project=_gcs.PROJECT)
    bucket = client.bucket(_gcs.BUCKET)
    plan = _gcs.plan_targets(exp, alg, problema, semente,
                             enable_bucket=True, data_root=data_root)
    # A lista de limpeza vem do PLANO (todos os blobs possíveis), não do
    # progresso do loop — um mirror_run que estoura no MEIO já subiu blobs que
    # nunca entrariam numa lista "do que eu conferi"; o finally cobre todos.
    all_blobs = sorted({t["blob"] for t in plan.values() if t["blob"]})

    def _cleanup_verified():
        """Deleta todos os blobs do plano e VERIFICA pós-delete. Retorna a
        lista de resíduos (vazia = limpeza comprovada)."""
        for b in all_blobs:
            try:
                bucket.blob(b).delete()
            except Exception:  # noqa: BLE001 — ausente é ok; verificação abaixo
                pass
        residuo = []
        for b in all_blobs:
            try:
                if bucket.blob(b).exists():
                    residuo.append(b)
            except Exception:  # noqa: BLE001 — não conseguiu verificar ≠ limpo
                residuo.append(b + " (não verificado)")
        return residuo

    done = False
    try:
        _gcs.mirror_run(exp, alg, problema, semente, data_root=data_root,
                        prune_bucket_only=False, client=client)
        n_checked = 0
        for art, tgt in plan.items():
            local, blob = tgt["local"], tgt["blob"]
            if blob is None or not os.path.exists(local):
                continue
            with open(local, "rb") as fh:
                h_local = hashlib.sha256(fh.read()).hexdigest()
            h_blob = hashlib.sha256(
                bucket.blob(blob).download_as_bytes()).hexdigest()
            if h_local != h_blob:
                return False, f"blob != local em '{art}' ({blob})"
            n_checked += 1
        if n_checked < 6:   # 4 camadas + jsonl + manifesto
            return False, f"só {n_checked}/6 artefatos espelhados"
        # sync de pendentes: derruba 1 blob e confere o re-upload idempotente.
        probe = plan["timing"]["blob"]
        bucket.blob(probe).delete()
        r = _gcs.sync_pending([(exp, alg, problema, semente)],
                              data_root=data_root, client=client)
        if r["resent"] < 1 or not _gcs.blob_exists(probe, client=client):
            return False, f"sync_pending não re-subiu o blob derrubado ({r})"
        # limpeza VERIFICADA (a mensagem só afirma o que foi conferido).
        residuo = _cleanup_verified()
        done = True
        if residuo:
            return False, (f"checks OK mas limpeza INCOMPLETA — resíduo no "
                           f"bucket: {residuo}")
        return True, (f"{n_checked} blobs byte-idênticos (sha256) · "
                      f"sync_pending re-subiu {r['resent']} · "
                      f"{len(all_blobs)} blobs deletados (verificado "
                      f"pós-delete)")
    finally:
        if not done:                     # backstop p/ falha/return antecipado
            _cleanup_verified()


def check_r2_00(exp="main", problema="MMF1", semente=0, gcs_smoke=False):
    """Encanamento objetivo do cartão R2-00-harness (contrato N.1/§22.3 — infra
    transversal BoTorch; SEM algoritmo, SEM fidelidade D97):

      1. BoTorch OFICIAL == 0.18.1 (N.2.3; fork do device = 'Unknown' PROIBIDO).
      2. STUB `stubpy` ponta-a-ponta VIA `experiment.run` (o wiring do despacho
         lazy) num tempdir: DoE CARREGADO do artefato (D63) → 20D infills torch
         → hard-stop natural (D61).
      3. FE final = 31D−1 EXATO (D89) + cache-hit = 0 FE (por U repetida, por X
         nativa e pós-esgotamento) + hard-stop.
      4. 4 saídas presentes + schema §17.2 EXATO (D/M re-derivados do problema
         canônico — anti-circular) + float32 (D53) + escrita atômica + run
         pronto p/ o skip do despachante (D58).
      5. CP-init por-run: manifest['doe_hash'] = sidecar do DoE (D87/D88).
      6. Pinning D79/N.1.1 (threads=1, float64, CPU) registrado e em vigor.
      7. RNG global salvo/restaurado em volta de pymoo.minimize (N.1.3).
      8. Sementes L.10/D62/D91 = fórmula do seeds.json RE-DERIVADA independente
         no gate (anti-tautologia; trunc 32b).
      9. Adapter §5.5: −f (maximização) + Standardize de Y + [0,1]↔nativo.
     10. jsonl §17.5.1 (header/decisions/guards D89/timing/footer) + manifesto
         com env N.2.3/L.18 (botorch/scipy) e fit_series §17.6.
     11. plan_targets bucket: dual-write planejado; stubpy NÃO é bucket-only.
     12. (--gcs-smoke) o smoke GCS REAL deferido do F0-03, com limpeza.

    Roda num tempdir (não polui `data/`); o DoE é pré-materializado ali pelo
    GERADOR F0-02 (`doe.ensure_doe`) — o RUNNER só carrega (D63)."""
    alg = "stubpy"
    results = []
    try:
        import botorch
        import torch  # noqa: F401
        from src import experiment as _exp
        from src import export as _export, gcs as _gcs, doe as _doe
        from src import manifest as _man
        from src import botorch_harness as _bh
    except Exception as e:  # noqa: BLE001 — import-gate do stack R2
        return [("import do stack R2 (botorch/torch/harness)",
                 (False, f"{type(e).__name__}: {e}"))]

    # (1) contrato N.1: BoTorch OFICIAL 0.18.1 (o fork tem __version__='Unknown').
    v = botorch.__version__
    results.append(("BoTorch OFICIAL == 0.18.1 (N.2.3 — fork 'Unknown' PROIBIDO)",
                    (v == "0.18.1", f"botorch=={v}")))

    with tempfile.TemporaryDirectory() as dr:
        # DoE pré-materializado pelo GERADOR (F0-02); o runner só CARREGA (D63).
        side = _doe.ensure_doe(problema, int(semente), data_root=dr)
        pre_done = _export.run_done(exp, alg, problema, semente, data_root=dr)

        # (2) o STUB ponta-a-ponta VIA experiment.run (prova o wiring).
        try:
            info = _exp.run(alg, problema, int(semente), exp=exp, data_root=dr)
        except Exception as e:  # noqa: BLE001 — qualquer erro = VERMELHO
            import traceback
            return results + [("STUB stubpy ponta-a-ponta via experiment.run",
                               (False, f"{type(e).__name__}: {e}\n"
                                       f"{traceback.format_exc()}"))]
        D, mfe = info["D"], info["maxfe"]
        # Âncora INDEPENDENTE do runner: D/M vêm do problema canônico (A2) —
        # um adapter com M errado não valida o próprio schema (anti-circular).
        prob_ref = _exp._instantiate_problem(problema)
        D_indep, M_indep = int(prob_ref.n_var), int(prob_ref.n_obj)
        results.append(("wiring: experiment.run → _DISPATCH_LOADERS['stubpy'] "
                        "+ D/M do runner = problema canônico",
                        ("stubpy" in _exp.ALGORITHM_DISPATCH
                         and D == D_indep and info["M"] == M_indep,
                         f"dispatch cacheado={sorted(_exp.ALGORITHM_DISPATCH)}, "
                         f"D={D}=={D_indep}, M={info['M']}=={M_indep}")))

        # (3) FE exato + cache-hit (0 FE ×3) + hard-stop (D89/D21/D61).
        results.append(("FE final = 31D−1 exato (D89)",
                        check_fe(exp, alg, problema, semente, D, data_root=dr)))
        ok_ch = (info["cache_hit_zero_fe_unit"]
                 and info["cache_hit_zero_fe_native"]
                 and info["cache_hit_post_exhaust"]
                 and info["cache_hits"] >= 3
                 and info["hard_stopped"] and info["fe_final"] == mfe)
        results.append(("cache-hit = 0 FE (U repetida·X nativa·pós-esgot.) + "
                        "hard-stop (D89/D21/D61)",
                        (ok_ch, f"hits={info['cache_hits']} "
                                f"unit={info['cache_hit_zero_fe_unit']} "
                                f"nativa={info['cache_hit_zero_fe_native']} "
                                f"pós={info['cache_hit_post_exhaust']} "
                                f"hard_stop={info['hard_stopped']} "
                                f"fe={info['fe_final']}=={mfe}")))

        # (4) 4 saídas + schema §17.2 + atômico + skip (D53/D58).
        results.append(("4 saídas presentes (§17.7)",
                        check_outputs(exp, alg, problema, semente,
                                      data_root=dr)))
        results.append(("schema §17.2 (①②③+timing) + float32 (D53)",
                        _check_export_schema(exp, alg, problema, semente,
                                             D_indep, M_indep, dr)))
        rundir = naming.run_dir(exp, alg, data_root=dr)
        tmps = [f for f in os.listdir(rundir) if f.endswith(".tmp")]
        post_done = _export.run_done(exp, alg, problema, semente, data_root=dr)
        # (o SKIP em si é do despachante — aqui prova-se que o run fecha
        # "pronto" no sentido D58, a pré-condição do skip.)
        results.append(("escrita atômica (0 .tmp) + run pronto p/ o skip do "
                        "despachante (D58)",
                        ((not tmps and post_done and not pre_done),
                         f"tmp={tmps}, run_done pre={pre_done} "
                         f"post={post_done}")))

        # (5) CP-init por-run: manifesto = sidecar do DoE (D87/D88).
        man = _man.read_manifest(
            naming.manifest_path(exp, alg, problema, semente, data_root=dr))
        cp_ok = (man is not None and info["cp_init_ok"]
                 and man.get("doe_hash") == side["doe_hash"]
                 and man.get("fe_final") == mfe)
        results.append(("CP-init por-run: manifest doe_hash = sidecar (D87/D88)",
                        (cp_ok, f"manifest={str(man and man.get('doe_hash'))[:16]}… "
                                f"sidecar={str(side['doe_hash'])[:16]}… "
                                f"fe_final={man and man.get('fe_final')}")))

        # (6) pinning D79/N.1.1: threads=1 + float64 + CPU + env vars.
        pin = info["pinning"]
        pin_ok = (pin.get("torch_num_threads") == 1
                  and pin.get("default_dtype") == "torch.float64"
                  and pin.get("device") == "cpu"
                  and all(pin.get(vv) == "1" for vv in _bh.D79_THREAD_VARS))
        results.append(("pinning D79/N.1.1 (threads=1 · float64 · CPU · env=1)",
                        (pin_ok, f"{pin}")))

        # (7) N.1.3 + (8) L.10/D62/D91 + (9) adapter §5.5.
        results.append(("RNG global preservado em volta de pymoo.minimize "
                        "(N.1.3)", (info["rng_guard_ok"],
                                    f"rng_guard_ok={info['rng_guard_ok']}")))
        # [DI-32/T5 · D-17] Prova MECÂNICA independente (molde R3-00): o item
        # acima é AUTO-RELATO do runner — seria VERDE mesmo com
        # preserve_global_rng = pass. O probe exercita a guarda de verdade
        # (2 níveis + sentinela de versão do pymoo).
        results.append(("RNG guard: prova mecânica independente (D-17)",
                        _r3_rng_guard_probe(problema)))
        # Âncora INDEPENDENTE: re-materializa a fórmula do seeds.json direto
        # do numpy (não pelas funções do harness — anti-tautologia): uma
        # inversão na tupla do harness reprovaria aqui.
        import numpy as _np
        want_seeds = [
            int(_np.random.SeedSequence(
                (int(semente), _bh.STUBPY_ALG_ID, k, 0))
                .generate_state(1, dtype=_np.uint64)[0]) & 0xFFFFFFFF
            for k in (1, 2, 3)]
        results.append(("sementes por iteração = fórmula do seeds.json "
                        "re-derivada independente (L.10/D62/D91, trunc 32b)",
                        (info["seed_det_ok"]
                         and list(info["seeds_used_head"]) == want_seeds,
                         f"seeds[:3]={info['seeds_used_head']} == "
                         f"re-derivadas={want_seeds}")))
        results.append(("adapter §5.5: −f (maximização) + Standardize(Y) + "
                        "[0,1]↔nativo",
                        (info["sign_ok"] and info["standardize_ok"],
                         f"sign_ok={info['sign_ok']} "
                         f"standardize_ok={info['standardize_ok']}")))

        # (10) jsonl §17.5.1 + manifesto env (N.2.3/L.18) + fit_series (§17.6).
        # Parsing BLINDADO (jsonl malformado ⇒ FAIL com diagnóstico, não crash)
        # + contagem de guards cache_hit (≥3: U repetida, X nativa, pós-esgot.)
        # + cruzamento do cache_hits com o manifesto EM DISCO (anti-autorrelato).
        jp = naming.jsonl_path(exp, alg, problema, semente, data_root=dr)
        try:
            with open(jp, encoding="utf-8") as fh:
                recs = [json.loads(ln) for ln in fh]
            kinds = [r.get("rec") for r in recs]
            guards = {r.get("name") for r in recs if r.get("rec") == "guard"}
            n_ch_guards = sum(1 for r in recs if r.get("rec") == "guard"
                              and r.get("name") == "cache_hit")
            footer = recs[-1] if recs else {}
            jsonl_ok = (bool(recs) and kinds[0] == "header"
                        and "decision" in kinds and "timing" in kinds
                        and {"cache_hit", "hard_stop"} <= guards
                        and n_ch_guards >= 3
                        and footer.get("rec") == "footer"
                        and footer.get("status") == "ok"
                        and footer.get("fe_final") == mfe
                        and footer.get("cp_init") is True
                        and footer.get("cache_hits") == info["cache_hits"]
                        and (man or {}).get("cache_hits") == info["cache_hits"])
            jsonl_msg = (f"recs={len(recs)}, guards={sorted(guards)}, "
                         f"cache_hit_guards={n_ch_guards}, "
                         f"footer_status={footer.get('status')}, "
                         f"cache_hits jsonl/manifesto/runner="
                         f"{footer.get('cache_hits')}/"
                         f"{(man or {}).get('cache_hits')}/{info['cache_hits']}")
        except Exception as e:  # noqa: BLE001 — jsonl ilegível = FAIL, não crash
            jsonl_ok = False
            jsonl_msg = f"jsonl ilegível: {type(e).__name__}: {e}"
        results.append(("jsonl §17.5.1: header·decisions·guards D89 (≥3 "
                        "cache_hit)·timing·footer(ok, fe, cp_init)",
                        (jsonl_ok, jsonl_msg)))
        env_man = (man or {}).get("env", {})
        env_ok = (env_man.get("botorch") == v
                  and bool(env_man.get("scipy"))
                  and bool(env_man.get("botorch_record_sha256"))
                  and bool((man or {}).get("fit_series")))
        results.append(("manifesto: env N.2.3/L.18 (botorch+hash, scipy) + "
                        "fit_series §17.6",
                        (env_ok, f"botorch={env_man.get('botorch')} "
                                 f"scipy={env_man.get('scipy')} "
                                 f"fit_series={len((man or {}).get('fit_series', []))} pts")))

        # (11) plano de destinos bucket (PURO): dual-write; stubpy ≠ bucket-only.
        plan_b = _gcs.plan_targets(exp, alg, problema, semente,
                                   enable_bucket=True, data_root=dr)
        plan_ok = (all(t["blob"] for t in plan_b.values())
                   and not _gcs.is_bucket_only(alg)
                   and not any(t["bucket_only"] for t in plan_b.values()))
        results.append(("plan_targets bucket: dual-write completo; stubpy não "
                        "é bucket-only (D58)",
                        (plan_ok, f"{len(plan_b)} artefatos planejados")))

        # (12) SMOKE GCS REAL (opt-in — o deferido do F0-03), com limpeza.
        # Exceção (auth/rede) vira FAIL com o relatório dos demais checks
        # preservado — nunca traceback cru; a limpeza best-effort do finally
        # interno já rodou antes da exceção propagar.
        if gcs_smoke:
            try:
                smoke = _r2_00_gcs_smoke(exp, alg, problema, semente, dr)
            except Exception as e:  # noqa: BLE001 — rede/credencial: FAIL
                smoke = (False, f"exceção no smoke: {type(e).__name__}: {e} "
                                f"(limpeza best-effort executada no finally; "
                                f"confira o prefixo experiments/main/stubpy/)")
            results.append(("SMOKE GCS real: dual-write byte-idêntico + sync + "
                            "delete verificado (§17.7/§22.3)", smoke))

    return results


# ── Checagem do cartão R3-c149 (LBN-MOBO, ONLINE — regressor μ/σ) ──────────

def check_r3_c149(exp="main", problema="MMF1", semente=0, data_root=None):
    """Gate objetivo do R3-c149 (LBN-MOBO, ONLINE) — o run JÁ TEM de existir.

    Mesmo desenho do `check_r3_c122` (branch ADITIVO, precedente autorizado):
    AFERE um run gravado, não re-roda. Diferenças por ser REGRESSOR (DEF-C1):
      - ③: `pred_tipo='valor'` em TODAS as linhas; `mu_*`/`sigma_*`
        PREENCHIDOS (busca E sonda); `pred_score`/`pred_classe` NULOS;
      - ③: `espaco_modelo='cru'` + `transf_tipo='zscore'` + `transf_params`
        com mean/std POR ITERAÇÃO (DEF-C3 — o modelo opera em z);
      - ③-BUSCA: `real_solution_id` preenchido em EXATAMENTE 1 linha por
        geração (o escolhido do HVI-greedy; q=1).
    O resto espelha o c122: FE=31D−1 EXATO, CP-init, fases init/opt, blocos
    de sonda ×2000 na ORDEM do artefato, `fe_treino_max` sem nulos,
    `real_solution_id` NULL na sonda, ④ 4 tempos sem NULL, ⑤ manifesto.
    Nada disto é fidelidade (D97).
    """
    from src import naming as _naming
    out = []
    data_root = data_root or os.path.join(ROOT, "data")
    alg = "c149"
    try:
        import numpy as _np
        import pyarrow.parquet as _pq
    except ImportError:
        return [("pyarrow/numpy", (None, "ausentes no env — skip"))]

    out.append(("saídas", check_outputs(exp, alg, problema, semente,
                                        data_root=data_root)))
    ok_real = os.path.exists(_naming.layer_path(exp, alg, problema, semente,
                                                "real", data_root=data_root))
    if not ok_real:
        out.append(("run presente", (False, f"① ausente — rode primeiro: "
                                            f"run_c149('{exp}','c149',"
                                            f"'{problema}',{semente})")))
        return out

    real = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "real", data_root=data_root))
    D = sum(1 for c in real.column_names
            if len(c) > 1 and c[0] == "x" and c[1:].isdigit())
    out.append(("FE exato (①)", check_fe(exp, alg, problema, semente, D,
                                         data_root=data_root)))
    out.append(("CP-init (DoE bit-a-bit)",
                check_doe_hash(problema, semente, data_root=data_root)))

    fases = real.column("fase").to_pylist()
    n_init = 11 * D - 1
    ok = (fases[:n_init] == ["init"] * n_init
          and all(f == "opt" for f in fases[n_init:]))
    out.append(("① fases init/opt", (ok, f"{fases.count('init')} init "
                                         f"(esperado {n_init}) + "
                                         f"{fases.count('opt')} opt")))

    surr = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "surrogate", data_root=data_root))
    reg = _np.asarray(surr.column("regime").to_pylist())
    n_snd = int((reg == "sonda").sum())
    ok = n_snd > 0 and n_snd % 2000 == 0
    out.append(("③ blocos de sonda ×2000",
                (ok, f"{n_snd} linhas 'sonda' = {n_snd / 2000:g} blocos; "
                     f"{int((reg == 'online').sum())} linhas de busca")))

    # ordem do artefato: o join com o gabarito é POSICIONAL (R4 regra 5)
    from src import standalone_harness as _sh
    snd_art = _sh.load_sonda(problema, regime="online", data_root=data_root)
    xs = _np.column_stack([surr.column(f"x{i}").to_numpy() for i in range(D)])
    idx = _np.where(reg == "sonda")[0]
    ok_ordem = True
    b = 0
    for b in range(len(idx) // 2000):
        bloco = xs[idx[b * 2000:(b + 1) * 2000]]
        if not _np.allclose(bloco, snd_art["X"].astype(bloco.dtype),
                            rtol=0, atol=1e-5):
            ok_ordem = False
            break
    out.append(("③ sonda na ORDEM do artefato",
                (ok_ordem, "todos os blocos batem posicionalmente com "
                           "data/sonda/ (join posicional, R4 regra 5)"
                 if ok_ordem else f"bloco {b} FORA de ordem — a R4 casaria "
                                  f"predição com o gabarito ERRADO")))

    ftm = surr.column("fe_treino_max").to_pylist()
    out.append(("③ fe_treino_max sem nulos",
                (all(v is not None for v in ftm),
                 f"min={min((v for v in ftm if v is not None), default='∅')} "
                 f"max={max((v for v in ftm if v is not None), default='∅')}")))

    rsid = surr.column("real_solution_id").to_pylist()
    snd_nulo = all(rsid[i] is None or (isinstance(rsid[i], float)
                                       and _np.isnan(rsid[i])) for i in idx)
    out.append(("③ sonda com real_solution_id NULL",
                (snd_nulo, "as 2000×N linhas de sonda não apontam o ① "
                           "(nenhuma foi avaliada) — correto")))

    # regressor (DEF-C1): pred_tipo='valor'; μ E σ preenchidos em TODAS as
    # linhas (busca + sonda); score/classe nulos. Checa TODAS as colunas μ/σ
    # (o check do c122 só olhava mu_0 — cobertura ilusória, achado da recon).
    tipos = set(surr.column("pred_tipo").to_pylist())
    M_cols = sum(1 for c in surr.column_names
                 if c.startswith("mu_") and c[3:].isdigit())
    mu_ok = sig_ok = True
    for j in range(M_cols):
        for col, flag in ((f"mu_{j}", "mu"), (f"sigma_{j}", "sigma")):
            vals = surr.column(col).to_pylist()
            algum_nulo = any(v is None or (isinstance(v, float)
                                           and _np.isnan(v)) for v in vals)
            if algum_nulo and flag == "mu":
                mu_ok = False
            if algum_nulo and flag == "sigma":
                sig_ok = False
    score = surr.column("pred_score").to_pylist()
    classe = surr.column("pred_classe").to_pylist()
    ok = (tipos == {"valor"} and mu_ok and sig_ok
          and all(v is None for v in score)
          and all(v is None for v in classe))
    out.append(("③ regressor μ/σ (DEF-C1)",
                (ok, f"pred_tipo={tipos}, mu_0..mu_{M_cols-1}/sigma_* sem "
                     f"NULL, score/classe NULOS (σ = desvio entre as K=10 "
                     f"redes — ver sigma_dict)")))

    # DEF-C3: o modelo opera em z ⇒ espaco/transf declarados em toda linha
    esp = set(surr.column("espaco_modelo").to_pylist())
    ttip = set(surr.column("transf_tipo").to_pylist())
    tpar = surr.column("transf_params").to_pylist()
    linhas_busca = _np.where(reg == "online")[0]
    par_busca_ok = all(tpar[i] for i in linhas_busca)
    ok = (esp == {"cru"} and "zscore" in ttip and par_busca_ok)
    out.append(("③ z-score declarado (DEF-C3)",
                (ok, f"espaco_modelo={esp}, transf_tipo={ttip}, "
                     f"transf_params presente nas {len(linhas_busca)} linhas "
                     f"de busca")))

    # [T6-batch] EXATAMENTE q real_solution_id por geração de BUSCA — o q vem
    # do MANIFESTO (principal=1 por D41; batch=10 por D66). O gate era
    # hard-coded em 1 e reprovava um run de batch correto (2000 escolhidos =
    # 10/geração). Mesma generalização do check do e81.
    _mq = _naming.manifest_path(exp, alg, problema, semente,
                                data_root=data_root or os.path.join(ROOT, "data"))
    q_run = 1
    if os.path.exists(_mq):
        try:
            with open(_mq, encoding="utf-8") as _fh:
                q_run = int(json.load(_fh).get("q", 1) or 1)
        except Exception:                              # noqa: BLE001
            q_run = 1
    ger = surr.column("geracao").to_pylist()
    por_ger: dict = {}
    for i in linhas_busca:
        if rsid[i] is not None and not (isinstance(rsid[i], float)
                                        and _np.isnan(rsid[i])):
            por_ger[ger[i]] = por_ger.get(ger[i], 0) + 1
    gers_busca = {ger[i] for i in linhas_busca}
    ok = all(por_ger.get(g, 0) == q_run for g in gers_busca)
    out.append((f"③ |lote|=q={q_run} (escolhidos/geração)",
                (ok, f"{len(gers_busca)} gerações de busca, "
                     f"{sum(por_ger.values())} escolhidos "
                     f"(cache-hit aponta a solução preexistente — D89)")))

    tim = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                            "timing", data_root=data_root))
    faltando = [c for c in ("tempo_fit_s", "tempo_busca_s",
                            "tempo_pred_sonda_s", "tempo_geracao_s")
                if any(v is None for v in tim.column(c).to_pylist())]
    out.append(("④ timing v5.2.1 completa",
                (not faltando, f"{tim.num_rows} gerações × 4 colunas de tempo"
                 if not faltando else f"colunas com NULL: {faltando}")))

    with open(_naming.manifest_path(exp, alg, problema, semente,
                                    data_root=data_root),
              encoding="utf-8") as fh:
        man = json.load(fh)
    tblk = man.get("timing") or {}
    ok = (all(k in tblk for k in ("tempo_total_s", "tempo_fit_surrogate_s",
                                  "tempo_busca_s", "tempo_aval_real_s"))
          and bool(man.get("sigma_dict")) and bool(man.get("sonda"))
          and (man.get("sonda") or {}).get("regime") == "online")
    out.append(("⑤ manifesto (timing+sigma_dict+sonda.regime)",
                (ok, f"timing={sorted(tblk)}; sigma_dict="
                     f"{len(man.get('sigma_dict') or {})} chaves; "
                     f"sonda.n_blocos={(man.get('sonda') or {}).get('n_blocos')}"
                     f"; regime={(man.get('sonda') or {}).get('regime')}")))
    return out


def check_r3_e81(exp="main", problema="MMF1", semente=0, data_root=None):
    """Gate objetivo do R3-e81 (qPOTS, ONLINE) — o run JÁ TEM de existir.

    Mesmo desenho do `check_r3_c149`/`check_r3_c122` (branch ADITIVO): AFERE um
    run gravado, não re-roda (um run de ZDT1 custa horas). O e81 é REGRESSOR
    (DEF-C1), então herda os checks de μ/σ do c149; o que é PRÓPRIO dele:
      - ③-BUSCA: `real_solution_id` preenchido em EXATAMENTE `q` linhas por
        geração — o lote do maximin (`q` lido do manifesto; 1 no principal,
        10 no `exp=batch`);
      - ⑤: `params` tem de declarar os kwargs OBRIGATÓRIOS do `qpots()`
        (`nystrom=0`, `ngen=10`, `dim`, `q`) e o dtype float64 (N.2.2) — são
        os itens do checklist §22.4·3.5 que sobrevivem no dado;
      - ⑤: `sigma_dict` tem de declarar `n_baseline` como NÃO-APLICÁVEL
        (P6/DI-16.6 — o qPOTS não tem baseline nem prune);
      - ⑥: o `.jsonl` tem de carregar `n_train` (NUNCA `n_baseline`) e o
        `assert |lote|==q` por geração.
    O resto espelha o c149. Nada disto é fidelidade (D97).
    """
    from src import naming as _naming
    out = []
    data_root = data_root or os.path.join(ROOT, "data")
    alg = "e81"
    try:
        import numpy as _np
        import pyarrow.parquet as _pq
    except ImportError:
        return [("pyarrow/numpy", (None, "ausentes no env — skip"))]

    out.append(("saídas", check_outputs(exp, alg, problema, semente,
                                        data_root=data_root)))
    ok_real = os.path.exists(_naming.layer_path(exp, alg, problema, semente,
                                                "real", data_root=data_root))
    if not ok_real:
        out.append(("run presente", (False, f"① ausente — rode primeiro: "
                                            f"run_e81('{exp}','e81',"
                                            f"'{problema}',{semente})")))
        return out

    real = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "real", data_root=data_root))
    D = sum(1 for c in real.column_names
            if len(c) > 1 and c[0] == "x" and c[1:].isdigit())

    with open(_naming.manifest_path(exp, alg, problema, semente,
                                    data_root=data_root),
              encoding="utf-8") as fh:
        man = json.load(fh)
    q = int(man.get("q", 1))
    abortado = man.get("status") == "failed"

    # Num aborto sancionado (teto de wall / cache-cap) o FE final é MENOR que
    # 31D−1 por desenho — a curva parcial É o entregável (o cartão diz que
    # abortar por teto é DADO, não falha). O check de FE exato só se aplica
    # ao run que fechou o orçamento.
    if abortado:
        out.append(("FE exato (①)",
                    (None, f"SKIP — run abortado ({man.get('motivo_parada')}): "
                           f"fe_final={man.get('fe_final')} < {31 * D - 1} por "
                           f"desenho; a curva parcial é o entregável")))
    else:
        out.append(("FE exato (①)", check_fe(exp, alg, problema, semente, D,
                                             data_root=data_root)))
    out.append(("CP-init (DoE bit-a-bit)",
                check_doe_hash(problema, semente, data_root=data_root)))

    fases = real.column("fase").to_pylist()
    n_init = 11 * D - 1
    ok = (fases[:n_init] == ["init"] * n_init
          and all(f == "opt" for f in fases[n_init:]))
    out.append(("① fases init/opt", (ok, f"{fases.count('init')} init "
                                         f"(esperado {n_init}) + "
                                         f"{fases.count('opt')} opt")))

    surr = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "surrogate", data_root=data_root))
    reg = _np.asarray(surr.column("regime").to_pylist())
    n_snd = int((reg == "sonda").sum())
    ok = n_snd > 0 and n_snd % 2000 == 0
    out.append(("③ blocos de sonda ×2000",
                (ok, f"{n_snd} linhas 'sonda' = {n_snd / 2000:g} blocos; "
                     f"{int((reg == 'online').sum())} linhas de busca")))

    # ordem do artefato: o join com o gabarito é POSICIONAL (R4 regra 5)
    from src import standalone_harness as _sh
    snd_art = _sh.load_sonda(problema, regime="online", data_root=data_root)
    xs = _np.column_stack([surr.column(f"x{i}").to_numpy() for i in range(D)])
    idx = _np.where(reg == "sonda")[0]
    ok_ordem = True
    b = 0
    for b in range(len(idx) // 2000):
        bloco = xs[idx[b * 2000:(b + 1) * 2000]]
        if not _np.allclose(bloco, snd_art["X"].astype(bloco.dtype),
                            rtol=0, atol=1e-5):
            ok_ordem = False
            break
    out.append(("③ sonda na ORDEM do artefato",
                (ok_ordem, "todos os blocos batem posicionalmente com "
                           "data/sonda/ (join posicional, R4 regra 5)"
                 if ok_ordem else f"bloco {b} FORA de ordem — a R4 casaria "
                                  f"predição com o gabarito ERRADO")))

    ftm = surr.column("fe_treino_max").to_pylist()
    out.append(("③ fe_treino_max sem nulos",
                (all(v is not None for v in ftm),
                 f"min={min((v for v in ftm if v is not None), default='∅')} "
                 f"max={max((v for v in ftm if v is not None), default='∅')} "
                 f"(treino = dataset INTEIRO ⇒ monotônico)")))

    rsid = surr.column("real_solution_id").to_pylist()
    snd_nulo = all(rsid[i] is None or (isinstance(rsid[i], float)
                                       and _np.isnan(rsid[i])) for i in idx)
    out.append(("③ sonda com real_solution_id NULL",
                (snd_nulo, "as 2000×N linhas de sonda não apontam o ① "
                           "(nenhuma foi avaliada) — correto")))

    # regressor (DEF-C1): pred_tipo='valor'; μ E σ preenchidos em TODAS as
    # linhas (busca + sonda); score/classe nulos. TODAS as colunas μ/σ.
    tipos = set(surr.column("pred_tipo").to_pylist())
    M_cols = sum(1 for c in surr.column_names
                 if c.startswith("mu_") and c[3:].isdigit())
    mu_ok = sig_ok = True
    for j in range(M_cols):
        for col, flag in ((f"mu_{j}", "mu"), (f"sigma_{j}", "sigma")):
            vals = surr.column(col).to_pylist()
            algum_nulo = any(v is None or (isinstance(v, float)
                                           and _np.isnan(v)) for v in vals)
            if algum_nulo and flag == "mu":
                mu_ok = False
            if algum_nulo and flag == "sigma":
                sig_ok = False
    score = surr.column("pred_score").to_pylist()
    classe = surr.column("pred_classe").to_pylist()
    ok = (tipos == {"valor"} and mu_ok and sig_ok
          and all(v is None for v in score)
          and all(v is None for v in classe))
    out.append(("③ regressor μ/σ (DEF-C1)",
                (ok, f"pred_tipo={tipos}, mu_0..mu_{M_cols-1}/sigma_* sem "
                     f"NULL, score/classe NULOS (σ = desvio da posterior do "
                     f"GP des-padronizado — ver sigma_dict)")))

    # σ do GP tem de ser > 0 (é VAR-GP, não pseudo-σ): σ ≡ 0 denunciaria
    # posterior colapsada ou des-padronização perdida.
    sig0 = _np.asarray([v for v in surr.column("sigma_0").to_pylist()
                        if v is not None], dtype=float)
    ok = sig0.size > 0 and float(sig0.min()) >= 0.0 and float(sig0.max()) > 0.0
    out.append(("③ σ do GP não-degenerado",
                (ok, f"sigma_0 ∈ [{sig0.min():.3g}, {sig0.max():.3g}]")))

    # DEF-C3: o modelo opera em z ⇒ espaço/transf declarados em TODA linha
    # (o gate é set-equality: 1 NULL reprova). `transf_params` tem de ser um
    # OBJETO JSON — uma string aqui denunciaria duplo-encode (o hazard do
    # kwarg `c3=`, achado desta sessão).
    esp = set(surr.column("espaco_modelo").to_pylist())
    ttip = set(surr.column("transf_tipo").to_pylist())
    tpar = surr.column("transf_params").to_pylist()
    linhas_busca = _np.where(reg == "online")[0]
    par_busca_ok = all(tpar[i] for i in linhas_busca)
    try:
        amostra = json.loads(tpar[0]) if tpar and tpar[0] else None
        sem_duplo = isinstance(amostra, dict)
    except (TypeError, ValueError):
        sem_duplo = False
    ok = (esp == {"cru"} and "zscore" in ttip and par_busca_ok and sem_duplo)
    out.append(("③ z-score declarado (DEF-C3)",
                (ok, f"espaco_modelo={esp}, transf_tipo={ttip}, "
                     f"transf_params em TODAS as linhas e decodifica para "
                     f"{'dict (sem duplo-encode)' if sem_duplo else 'NÃO-dict — DUPLO-ENCODE'}")))

    # q do lote: EXATAMENTE q `real_solution_id` por geração de BUSCA
    ger = surr.column("geracao").to_pylist()
    por_ger: dict = {}
    for i in linhas_busca:
        if rsid[i] is not None and not (isinstance(rsid[i], float)
                                        and _np.isnan(rsid[i])):
            por_ger[ger[i]] = por_ger.get(ger[i], 0) + 1
    gers_busca = {ger[i] for i in linhas_busca}
    ok = all(por_ger.get(g, 0) == q for g in gers_busca)
    out.append((f"③ |lote|=q={q} (escolhidos/geração)",
                (ok, f"{len(gers_busca)} gerações de busca, "
                     f"{sum(por_ger.values())} escolhidos "
                     f"(cache-hit aponta a solução preexistente — D89)")))

    tim = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                            "timing", data_root=data_root))
    faltando = [c for c in ("tempo_fit_s", "tempo_busca_s",
                            "tempo_pred_sonda_s", "tempo_geracao_s")
                if any(v is None for v in tim.column(c).to_pylist())]
    out.append(("④ timing v5.2.1 completa",
                (not faltando, f"{tim.num_rows} gerações × 4 colunas de tempo"
                 if not faltando else f"colunas com NULL: {faltando}")))

    # ④ n_acumulado = o TREINO (DI-16.6): tem de crescer de 11D−1 em diante
    na = [v for v in tim.column("n_acumulado").to_pylist() if v is not None]
    ok = bool(na) and na[0] == n_init and all(
        na[i] <= na[i + 1] for i in range(len(na) - 1))
    out.append(("④ n_acumulado = TREINO (monotônico)",
                (ok, f"{na[0] if na else '?'} → {na[-1] if na else '?'} "
                     f"(começa em 11D−1={n_init}; o qPOTS não poda)")))

    tblk = man.get("timing") or {}
    sd = man.get("sigma_dict") or {}
    pr = man.get("params") or {}
    ok = (all(k in tblk for k in ("tempo_total_s", "tempo_fit_surrogate_s",
                                  "tempo_busca_s", "tempo_aval_real_s"))
          and bool(sd) and bool(man.get("sonda"))
          and (man.get("sonda") or {}).get("regime") == "online")
    out.append(("⑤ manifesto (timing+sigma_dict+sonda.regime)",
                (ok, f"timing={sorted(tblk)}; sigma_dict={len(sd)} chaves; "
                     f"sonda.n_blocos={(man.get('sonda') or {}).get('n_blocos')}"
                     f"; regime={(man.get('sonda') or {}).get('regime')}")))

    # ⑤ os kwargs OBRIGATÓRIOS do checklist §22.4·3.5, no dado
    kw = pr.get("qpots_kwargs") or {}
    ok = (int(kw.get("nystrom", -1)) == 0 and int(kw.get("ngen", -1)) == 10
          and int(kw.get("dim", -1)) == D and int(kw.get("q", -1)) == q
          and "float64" in str(pr.get("torch_default_dtype", "")))
    out.append(("⑤ params: kwargs qpots + dtype (§22.4·3.5)",
                (ok, f"nystrom={kw.get('nystrom')} ngen={kw.get('ngen')} "
                     f"dim={kw.get('dim')} q={kw.get('q')}; dtype declarado="
                     f"{str(pr.get('torch_default_dtype'))[:24]}…")))

    ok = "n_baseline" in sd and "NAO SE APLICA" in str(sd["n_baseline"]).upper()
    out.append(("⑤ sigma_dict: n_baseline N/A (P6/DI-16.6)",
                (ok, "o qPOTS não tem baseline nem prune — o maximin é vs o "
                     "dataset INTEIRO; o campo equivalente é `n_train`"
                 if ok else "sigma_dict não declara n_baseline como N/A")))

    # ⑥ jsonl: DI-10 + os campos S.7 do e81
    jpath = _naming.jsonl_path(exp, alg, problema, semente,
                               data_root=data_root)
    gens, faltas, lote_ok, tem_nb = 0, set(), True, False
    with open(jpath, encoding="utf-8") as fh:
        for linha in fh:
            r = json.loads(linha)
            if r.get("rec") != "decision":
                continue
            gens += 1
            for campo in ("n_train", "fe", "f_best", "n_front1", "modelo_hp",
                          "tempo_fit_s", "tempo_busca_s", "draws_thompson",
                          "n_front_acq", "assert_lote_eq_q", "seed_nsga2",
                          "nystrom", "ngen"):
                if campo not in r:
                    faltas.add(campo)
            if r.get("assert_lote_eq_q") is not True:
                lote_ok = False
            if "n_baseline" in r:
                tem_nb = True
    ok = gens > 0 and not faltas and lote_ok and not tem_nb
    out.append(("⑥ jsonl: DI-10 + S.7 do e81",
                (ok, f"{gens} eventos de decisão; campos ausentes="
                     f"{sorted(faltas) or 'nenhum'}; |lote|==q em todas="
                     f"{lote_ok}; usa n_train e NÃO n_baseline="
                     f"{not tem_nb} (P6/DI-16.6)")))
    return out


# ── Checagem do cartão R3-00-harness (infra transversal standalone + ⑦) ────

def check_r3_c122(exp="main", problema="MMF1", semente=0, data_root=None):
    """Gate objetivo do R3-c122 (θ-DEA-DP, ONLINE) — o run JÁ TEM de existir.

    Difere do `check_r3_00` de propósito: aquele RODA o stub (segundos); este
    AFERE um run já gravado, porque um run real do c122 leva de 50 s (MMF1) a
    horas (ZDT1) — re-rodar dentro do gate o tornaria inutilizável.

    O que prova (nada disto é fidelidade — D97):
      1. as 4 saídas + jsonl + manifesto existem;
      2. **FE = 31D−1 EXATO**, D derivado da própria ① (não do `--dim`);
      3. CP-init: `doe_hash` do manifesto == hash do artefato do DoE, e as
         `11D−1` primeiras linhas da ① em fase `init`;
      4. ③ v5.2.1: `regime` POR LINHA (sonda × online na MESMA tabela), blocos
         de sonda de **2.000** na ORDEM do artefato, `fe_treino_max` sem nulos,
         `real_solution_id` NULL nas linhas de sonda;
      5. ③-BUSCA: `pred_tipo='score'` com `pred_score` preenchido e
         `mu_*`/`sigma_*` NULOS (o c122 é par-a-par — μ/σ significam outra
         coisa e envenenariam a leitura da R4), ≤ TOP_BUSCA linhas por geração;
      6. ④ v5.2.1 COMPLETA: as 4 colunas de tempo sem nulos indevidos;
      7. manifesto com bloco `timing` + `sigma_dict` + bloco `sonda`.
    """
    from src import naming as _naming
    out = []
    data_root = data_root or os.path.join(ROOT, "data")
    alg = "c122"
    try:
        import numpy as _np
        import pyarrow.parquet as _pq
    except ImportError:
        return [("pyarrow/numpy", (None, "ausentes no env — skip"))]

    out.append(("saídas", check_outputs(exp, alg, problema, semente,
                                        data_root=data_root)))
    ok_real = os.path.exists(_naming.layer_path(exp, alg, problema, semente,
                                                "real", data_root=data_root))
    if not ok_real:
        out.append(("run presente", (False, f"① ausente — rode primeiro: "
                                            f"run_c122('{exp}','c122',"
                                            f"'{problema}',{semente})")))
        return out

    real = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "real", data_root=data_root))
    D = sum(1 for c in real.column_names
            if len(c) > 1 and c[0] == "x" and c[1:].isdigit())
    out.append(("FE exato (①)", check_fe(exp, alg, problema, semente, D,
                                         data_root=data_root)))
    out.append(("CP-init (DoE bit-a-bit)",
                check_doe_hash(problema, semente, data_root=data_root)))

    fases = real.column("fase").to_pylist()
    n_init = 11 * D - 1
    ok = (fases[:n_init] == ["init"] * n_init
          and all(f == "opt" for f in fases[n_init:]))
    out.append(("① fases init/opt", (ok, f"{fases.count('init')} init "
                                         f"(esperado {n_init}) + "
                                         f"{fases.count('opt')} opt")))

    surr = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                             "surrogate", data_root=data_root))
    reg = _np.asarray(surr.column("regime").to_pylist())
    n_snd = int((reg == "sonda").sum())
    ok = n_snd > 0 and n_snd % 2000 == 0
    out.append(("③ blocos de sonda ×2000",
                (ok, f"{n_snd} linhas 'sonda' = {n_snd / 2000:g} blocos; "
                     f"{int((reg == 'online').sum())} linhas de busca")))

    # ordem do artefato: o join com o gabarito é POSICIONAL (R4 regra 5)
    from src import standalone_harness as _sh
    snd_art = _sh.load_sonda(problema, regime="online", data_root=data_root)
    xs = _np.column_stack([surr.column(f"x{i}").to_numpy() for i in range(D)])
    idx = _np.where(reg == "sonda")[0]
    ok_ordem = True
    for b in range(len(idx) // 2000):
        bloco = xs[idx[b * 2000:(b + 1) * 2000]]
        if not _np.allclose(bloco, snd_art["X"].astype(bloco.dtype),
                            rtol=0, atol=1e-5):
            ok_ordem = False
            break
    out.append(("③ sonda na ORDEM do artefato",
                (ok_ordem, "todos os blocos batem posicionalmente com "
                           "data/sonda/ (join posicional, R4 regra 5)"
                 if ok_ordem else f"bloco {b} FORA de ordem — a R4 casaria "
                                  f"predição com o gabarito ERRADO")))

    ftm = surr.column("fe_treino_max").to_pylist()
    out.append(("③ fe_treino_max sem nulos",
                (all(v is not None for v in ftm),
                 f"min={min((v for v in ftm if v is not None), default='∅')} "
                 f"max={max((v for v in ftm if v is not None), default='∅')}")))

    rsid = surr.column("real_solution_id").to_pylist()
    snd_nulo = all(rsid[i] is None or (isinstance(rsid[i], float)
                                       and _np.isnan(rsid[i])) for i in idx)
    out.append(("③ sonda com real_solution_id NULL",
                (snd_nulo, "as 2000×N linhas de sonda não apontam o ① "
                           "(nenhuma foi avaliada) — correto")))

    tipos = set(surr.column("pred_tipo").to_pylist())
    mus = surr.column("mu_0").to_pylist() if "mu_0" in surr.column_names else []
    mu_nulo = all(v is None or (isinstance(v, float) and _np.isnan(v))
                  for v in mus)
    score = surr.column("pred_score").to_pylist()
    ok = (tipos == {"score"} and mu_nulo
          and all(v is not None for v in score))
    out.append(("③ score par-a-par (DEF-C1)",
                (ok, f"pred_tipo={tipos}, pred_score preenchido, "
                     f"mu_*/sigma_* NULOS (o c122 não produz μ/σ)")))

    tim = _pq.read_table(_naming.layer_path(exp, alg, problema, semente,
                                            "timing", data_root=data_root))
    faltando = [c for c in ("tempo_fit_s", "tempo_busca_s",
                            "tempo_pred_sonda_s", "tempo_geracao_s")
                if any(v is None for v in tim.column(c).to_pylist())]
    out.append(("④ timing v5.2.1 completa",
                (not faltando, f"{tim.num_rows} gerações × 4 colunas de tempo"
                 if not faltando else f"colunas com NULL: {faltando}")))

    with open(_naming.manifest_path(exp, alg, problema, semente,
                                    data_root=data_root), encoding="utf-8") as fh:
        man = json.load(fh)
    tblk = man.get("timing") or {}
    ok = (all(k in tblk for k in ("tempo_total_s", "tempo_fit_surrogate_s",
                                  "tempo_busca_s", "tempo_aval_real_s"))
          and bool(man.get("sigma_dict")) and bool(man.get("sonda")))
    out.append(("⑤ manifesto (timing+sigma_dict+sonda)",
                (ok, f"timing={sorted(tblk)}; sigma_dict="
                     f"{len(man.get('sigma_dict') or {})} chaves; "
                     f"sonda.n_blocos={(man.get('sonda') or {}).get('n_blocos')}")))
    return out


def check_r3_00(exp="off", problema="MMF1", semente=0, data_root=None):
    """Encanamento objetivo do R3-00-harness (contrato N.2 + DI-08).

    Roda o STUB OFFLINE `stubr3` num tempdir (dataset/sonda linkados do repo) e
    afere o contrato da Rodada 3 — SEM algoritmo e SEM fidelidade (D97):

      1. wiring `experiment.run` → dispatch lazy (stack `standalone`);
      2. regime OFFLINE: FE final = 31D−1 EXATO **e** = |dataset| (o orçamento
         É o dataset, D90), tudo em fase `init`;
      3. ① bit-exata ao artefato + CP-init `x_hash` **E** `f_hash` (o CP
         offline é mais forte que o online, que só cobre X);
      4. violação de regime (FE na busca) levanta `OfflineBudgetViolation`;
      5. cache-hit = 0 FE (D89) mesmo com o saldo esgotado;
      6. 4+1 saídas + schemas §17.2 EXATOS (incl. a ⑦ do DI-08) + float32/zstd;
      7. ③ v5.2.1: `regime` POR LINHA (sonda × busca na MESMA tabela) e
         `fe_treino_max` sem nulos;
      8. ④ v5.2.1 COMPLETA: `tempo_busca_s`/`tempo_pred_sonda_s`/
         `tempo_geracao_s` preenchidos;
      9. sonda: 2000 linhas na ordem do artefato, hash conferido, ZERO FE;
     10. ⑦ presente, consistente e RECONSTITUÍVEL da ③ (o invariante que a
         prova deste cartão descobriu);
     11. manifesto com bloco `timing` (§17.6 obrigatório), `sigma_dict`
         (DEF-C4) e o CP offline;
     12. pinning D79 e guarda de RNG N.2.3 (contra `pymoo.minimize` REAL);
     13. subprocess-por-venv (D79/N.2) resolve o env de cada config do R3 pelo
         `envs.json` e executa de verdade no interpretador-alvo.
    """
    import shutil
    import numpy as np
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
    from src import experiment as _exp
    from src import export as _export
    from src import standalone_harness as _sh

    ALG = _sh.STUB_ALG
    results = []
    semente = int(semente)
    repo_data = data_root or os.path.join(ROOT, "data")

    # Âncoras INDEPENDENTES do runner (anti-circular — precedente R2-00).
    prob_obj = _exp._instantiate_problem(problema)
    D_indep, M_indep = int(prob_obj.n_var), int(prob_obj.n_obj)
    n_ds_indep = maxfe(D_indep)                     # 31D−1 (o dataset, D90)

    with tempfile.TemporaryDirectory() as dr:
        for sub in ("datasets", "sonda"):
            shutil.copytree(os.path.join(repo_data, sub),
                            os.path.join(dr, sub))
        try:
            ev = _exp.run(ALG, problema, semente, exp=exp, data_root=dr)
            results.append(("wiring experiment.run → dispatch lazy "
                            "(stack standalone)", (True, f"run OK: {ALG}")))
        except Exception as exc:  # noqa: BLE001
            results.append(("wiring experiment.run → dispatch lazy",
                            (False, f"{type(exc).__name__}: {exc}")))
            return results

        results.append((
            "dispatch R3 registrado em _DISPATCH_LOADERS",
            (_exp._DISPATCH_LOADERS.get(ALG) ==
             ("src.standalone_harness", "run_stubr3", "standalone"),
             f"{ALG} → {_exp._DISPATCH_LOADERS.get(ALG)}")))

        # (2) FE = 31D−1 = |dataset|, e o orçamento nasce esgotado.
        results.append(("FE final = 31D−1 EXATO **e** = |dataset| (D90 — o "
                        "orçamento É o dataset)",
                        (ev["fe_final"] == n_ds_indep
                         and ev["maxfe"] == n_ds_indep
                         and ev["n_dataset"] == n_ds_indep,
                         f"fe={ev['fe_final']} maxfe={ev['maxfe']} "
                         f"n_ds={ev['n_dataset']} (esperado {n_ds_indep}, "
                         f"D={D_indep})")))
        results.append(("FE do artefato (①) — nº de linhas",
                        check_fe(exp, ALG, problema, semente, D_indep,
                                 data_root=dr)))

        # (3) ① bit-exata ao dataset + CP-init x_hash E f_hash.
        real = pq.read_table(naming.layer_path(exp, ALG, problema, semente,
                                               "real", data_root=dr))
        fases = set(real.column("fase").to_pylist())
        # [T7-sweep] o gate carrega a MESMA variante que o runner (do token
        # exp). Aqui o exp é sempre 'off' (o stub roda em tempdir), então
        # dataset_variant devolve (None, None) e o comportamento é o de antes.
        _t_ds, _d_ds = naming.dataset_variant(exp)
        ds = _sh.load_dataset(problema, semente, tier=_t_ds, dist=_d_ds,
                              data_root=dr)
        Xr = np.column_stack([np.asarray(real.column(f"x{j}"), dtype=np.float64)
                              for j in range(D_indep)])
        Fr = np.column_stack([np.asarray(real.column(f"f{j}"), dtype=np.float64)
                              for j in range(M_indep)])
        bitex = (np.array_equal(Xr, ds["X"].astype(np.float32).astype(np.float64))
                 and np.array_equal(Fr, ds["F"].astype(np.float32).astype(np.float64)))
        results.append(("① = o DATASET bit-a-bit (pós-cast float32 D53) · "
                        "fase toda `init`",
                        (bitex and fases == {"init"},
                         f"bit-exata={bitex} fases={sorted(fases)}")))
        man = json.load(open(naming.manifest_path(exp, ALG, problema, semente,
                                                  data_root=dr),
                             encoding="utf-8"))
        cpo = man.get("cp_init_offline") or {}
        results.append(("CP-init OFFLINE: x_hash **E** f_hash == sidecar do "
                        "dataset (mais forte que o CP online — D90)",
                        (bool(ev["cp_init_ok"])
                         and cpo.get("x_hash") == ds["x_hash"]
                         and cpo.get("f_hash") == ds["f_hash"],
                         f"x={str(cpo.get('x_hash'))[:16]}… "
                         f"f={str(cpo.get('f_hash'))[:16]}…")))

        # (4)(5) violação de regime e cache-hit.
        bud, _ = _sh.load_offline_budget(problema, semente, data_root=dr)
        try:
            with _sh.offline_guard(alg=ALG, problema=problema):
                bud.evaluate(np.full(D_indep, 0.123456789),
                             lambda x: np.zeros(M_indep))
            viol = (False, "NÃO levantou — o regime offline não está guardado")
        except _sh.OfflineBudgetViolation:
            viol = (True, "FE na busca ⇒ OfflineBudgetViolation (pára-e-loga)")
        results.append(("violação de regime OFFLINE é exceção própria, não "
                        "término natural (≠ D61)", viol))
        fe0 = bud.fe
        bud.evaluate(ds["X"][0], lambda x: None)
        results.append(("cache-hit = 0 FE mesmo com saldo esgotado (D89)",
                        (bud.fe == fe0 and bud.cache_hits >= 1,
                         f"fe {fe0}→{bud.fe}, cache_hits={bud.cache_hits}")))

        # (6) 4+1 saídas e schemas exatos.
        results.append(("4 saídas obrigatórias + jsonl (§17.7)",
                        check_outputs(exp, ALG, problema, semente,
                                      data_root=dr)))
        results.append(("schema §17.2 (①②③+timing) + float32 (D53)",
                        _check_export_schema_r3(exp, ALG, problema, semente,
                                                D_indep, M_indep, dr)))
        fpath = naming.final_path(exp, ALG, problema, semente, data_root=dr)
        got = pq.read_schema(fpath).remove_metadata()
        results.append(("⑦ `__final.parquet` presente + schema DI-08 EXATO",
                        (os.path.exists(fpath)
                         and got.equals(_sh.final_schema(D_indep, M_indep),
                                        check_metadata=False),
                         f"{os.path.basename(fpath)}: {got.names}")))

        # (7) ③ v5.2.1 — regime por linha + fe_treino_max.
        surr = pq.read_table(naming.layer_path(exp, ALG, problema, semente,
                                               "surrogate", data_root=dr))
        regs = surr.column("regime").to_pylist()
        n_sonda = regs.count("sonda")
        n_busca = len(regs) - n_sonda
        n_ftm_null = pc.sum(pc.is_null(surr.column("fe_treino_max"))).as_py()
        results.append(("③ v5.2.1: `regime` POR LINHA (sonda × busca na MESMA "
                        "tabela) + `fe_treino_max` sem nulos (DI-09/A1)",
                        (n_sonda > 0 and n_busca > 0 and n_ftm_null == 0,
                         f"sonda={n_sonda} busca={n_busca} "
                         f"fe_treino_max nulos={n_ftm_null}")))

        # (8) ④ v5.2.1 completa.
        tm = pq.read_table(naming.layer_path(exp, ALG, problema, semente,
                                             "timing", data_root=dr))
        nulos = {c: pc.sum(pc.is_null(tm.column(c))).as_py()
                 for c in ("tempo_busca_s", "tempo_pred_sonda_s",
                           "tempo_geracao_s")}
        results.append(("④ v5.2.1 COMPLETA desde o nascimento: busca/sonda/"
                        "geração preenchidos (§17.6 expandida)",
                        (all(v == 0 for v in nulos.values()) and tm.num_rows > 0,
                         f"{tm.num_rows} linhas, nulos={nulos}")))

        # (9) sonda: ordem do artefato + hash + ZERO FE.
        # [DI-13.5] o tamanho depende do REGIME: online lê a fatia de S_online
        # (2.000); offline lê o artefato INTEIRO (20.000) — o STUB do R3-00 é
        # offline. O check é contra o que o loader devolve p/ o regime, não
        # contra um literal.
        sonda = _sh.load_sonda(problema, regime="offline", data_root=dr)
        idx_s = [i for i, r in enumerate(regs) if r == "sonda"]
        Xs = np.column_stack([np.asarray(surr.column(f"x{j}"),
                                         dtype=np.float64)[idx_s]
                              for j in range(D_indep)])
        ordem_ok = np.array_equal(
            Xs, sonda["X"].astype(np.float32).astype(np.float64))
        results.append(("sonda §17.2.2: S do REGIME na ORDEM do artefato (join "
                        "posicional — R4 regra 5), hash conferido, ZERO FE",
                        (n_sonda == sonda["S"] and ordem_ok
                         and ev["fe_final"] == n_ds_indep,
                         f"S={n_sonda} (esperado {sonda['S']}, regime=offline) "
                         f"ordem_preservada={ordem_ok} "
                         f"FE inalterado={ev['fe_final']}")))

        # (10) ⑦ reconstituível da ③ — o invariante.
        results.append(("⑦ consistente e RECONSTITUÍVEL da ③ (o f reproduz "
                        "problems.py; o X bate com a última geração)",
                        _check_final_layer(exp, ALG, problema, semente, dr)))

        # (11) manifesto.
        tb = man.get("timing") or {}
        results.append(("manifesto: bloco `timing` §17.6 OBRIGATÓRIO + "
                        "`sigma_dict` (DEF-C4) + regime offline",
                        (all(tb.get(k) is not None for k in
                             ("tempo_total_s", "tempo_fit_surrogate_s",
                              "tempo_busca_s", "tempo_aval_real_s"))
                         and bool(man.get("sigma_dict"))
                         and man.get("regime") == "offline"
                         and man.get("status") == "ok",
                         f"timing={tb} sigma_dict={bool(man.get('sigma_dict'))} "
                         f"regime={man.get('regime')}")))
        tmps = [f for f in os.listdir(naming.run_dir(exp, ALG, data_root=dr))
                if f.endswith(".tmp")]
        results.append(("escrita ATÔMICA — nenhum `.tmp` residual (D58)",
                        (not tmps, f"residuais={tmps}")))

    # (12) pinning D79 + guarda de RNG N.2.3.
    pin = _sh.pin_runtime()
    results.append(("pinning D79/N.1.1 (threads=1 nas 4 vars; torch opcional)",
                    (all(pin.get(v) == "1" for v in _sh.D79_THREAD_VARS),
                     f"{ {v: pin.get(v) for v in _sh.D79_THREAD_VARS} }")))
    results.append(("guarda de RNG N.2.3 contra `pymoo.minimize` REAL "
                    "(re-semeia np.random/random globais)",
                    _r3_rng_guard_probe(problema)))

    # (13) subprocess-por-venv (D79/N.2) — o mecanismo que separa b5 × c311.
    results.append(("subprocess-por-venv: envs.json resolve o env dos 6 "
                    "configs R3 (b5×c311 NUNCA co-importados — N.1.2)",
                    _r3_env_resolution()))
    results.append(("subprocess-por-venv EXECUTA de verdade (pin D79 no "
                    "FILHO, protocolo de resultado)",
                    _r3_subprocess_probe(problema, semente, repo_data)))
    return results


def check_r3_b5(alg, exp="off", problema="MMF1", semente=0, data_root=None):
    """[R3-b5] Afere o run OFFLINE JÁ GRAVADO de b5r (mode 7 · Prob-RVEA_v3) ou
    b5m (mode 72 · Prob-MOEA/D) — encanamento objetivo (D97: fidelidade é do
    autor, a posteriori). ADITIVO: LÊ o que o runner persistiu, NÃO re-roda (o
    run leva minutos). Contrato N.2 / regime offline:

      1. as 6-7 camadas presentes (⑦ __final OBRIGATÓRIA — D-12/DI-21);
      2. FE final = 31D−1 = |dataset| (D90); ① = o dataset bit-a-bit, fase `init`;
      3. CP-init OFFLINE (x_hash **E** f_hash == sidecar) do manifesto;
      4. ② VAZIA por construção é ACEITÁVEL (DI-16.17) — NÃO exigimos não-vazia;
      5. ③ `regime` POR LINHA: sonda (S=20000, geracao NULL, fe_treino_max set) +
         busca (geracao inteira, fe_treino_max=n_ds−1, real_solution_id NULL —
         DI-16.17); espaco_modelo ∈ {cru}; μ_*/σ_* preenchidos (regressor prob.);
      6. ④ ≥1 linha com tempo_fit_s NÃO-nulo (b5 NÃO é piso) + tempo_busca_s;
      7. ⑤ manifesto: timing §17.6 + sigma_dict (DEF-C4) + sonda + regime offline
         + status ok;
      8. ⑦ presente e RECONSTITUÍVEL da ③ (última geração) — DI-16.16/DI-08.
    """
    import numpy as np
    import pyarrow.parquet as pq
    from src import experiment as _exp
    from src import standalone_harness as _sh

    if alg not in ("b5r", "b5m"):
        return [("cartão R3-b5 só afere --alg=b5r|b5m", (False, f"alg={alg!r}"))]
    results = []
    semente = int(semente)
    dr = data_root or os.path.join(ROOT, "data")

    prob_obj = _exp._instantiate_problem(problema)
    D, M = int(prob_obj.n_var), int(prob_obj.n_obj)
    # [T7-sweep] |dataset| POR CÉLULA: 31D−1 no principal, n do tier no sweep
    # (lido do sidecar). O gate tem de aferir contra o que o run REALMENTE leu.
    n_ds, _origem_n = n_dataset_esperado(exp, problema, semente, D,
                                         data_root=dr)
    if n_ds is None:
        return [("expectativa de |dataset| do sweep", (False, _origem_n))]

    # (1) camadas presentes (⑦ é OBRIGATÓRIA no offline).
    layers = {L: naming.layer_path(exp, alg, problema, semente, L, data_root=dr)
              for L in ("real", "pop", "surrogate", "timing", "final")}
    manp = naming.manifest_path(exp, alg, problema, semente, data_root=dr)
    faltam = [L for L, p in layers.items() if not os.path.exists(p)]
    if not os.path.exists(manp):
        faltam.append("manifest")
    if faltam:
        return [("as 6-7 camadas presentes (rode o b5 ANTES do accept)",
                 (False, f"faltam: {faltam} — pasta {os.path.dirname(manp)}"))]
    results.append(("6-7 camadas presentes (①②③④⑤ + ⑦ __final — D-12)",
                    (True, "todas presentes")))

    man = json.load(open(manp, encoding="utf-8"))
    # [T7-sweep] o gate carrega a MESMA variante que o runner (do token exp) —
    # se carregasse o principal, um run de sweep seria comparado bit-a-bit
    # contra o dataset errado e reprovaria (ou pior, passaria por engano).
    _t_ds, _d_ds = naming.dataset_variant(exp)
    ds = _sh.load_dataset(problema, semente, tier=_t_ds, dist=_d_ds,
                          data_root=dr)

    # (2) ① = dataset bit-exato + fase `init` + FE=31D−1.
    real = pq.read_table(layers["real"])
    Xr = np.column_stack([np.asarray(real.column(f"x{j}"), dtype=np.float64)
                          for j in range(D)])
    Fr = np.column_stack([np.asarray(real.column(f"f{j}"), dtype=np.float64)
                          for j in range(M)])
    bitex = (np.array_equal(Xr, ds["X"].astype(np.float32).astype(np.float64))
             and np.array_equal(Fr, ds["F"].astype(np.float32).astype(np.float64)))
    fases = set(real.column("fase").to_pylist())
    results.append(("FE final = 31D−1 = |dataset| (D90) · ① = o dataset bit-a-bit "
                    "(pós-cast float32) · fase toda `init`",
                    (real.num_rows == n_ds and bitex and fases == {"init"},
                     f"rows={real.num_rows} (esperado {n_ds}) bitex={bitex} "
                     f"fases={sorted(fases)}")))

    # (3) CP-init OFFLINE (o mais forte — X E F).
    cpo = man.get("cp_init_offline") or {}
    results.append(("CP-init OFFLINE: x_hash **E** f_hash == sidecar do dataset (D90)",
                    (cpo.get("x_hash") == ds["x_hash"]
                     and cpo.get("f_hash") == ds["f_hash"],
                     f"x={str(cpo.get('x_hash'))[:12]}… f={str(cpo.get('f_hash'))[:12]}…")))

    # (4) ② VAZIA é ACEITÁVEL (DI-16.17) — NÃO exigimos não-vazia.
    pop = pq.read_table(layers["pop"])
    results.append(("② membership: schema válido; VAZIA por construção é "
                    "ACEITÁVEL (DI-16.17 — init LHS ≠ dataset)",
                    (set(pop.schema.names) >= {"algoritmo", "problema",
                     "semente", "geracao", "solution_id"},
                     f"rows={pop.num_rows} (vazia OK)")))

    # (5) ③ regime POR LINHA (sonda × busca).
    surr = pq.read_table(layers["surrogate"])
    reg = surr.column("regime").to_pylist()
    ger = surr.column("geracao").to_pylist()
    ftm = surr.column("fe_treino_max").to_pylist()
    esp = set(v for v in surr.column("espaco_modelo").to_pylist()
              if v not in (None, ""))
    rsid = surr.column("real_solution_id").to_pylist()
    idx_s = [i for i, r in enumerate(reg) if r == "sonda"]
    idx_b = [i for i, r in enumerate(reg) if r == "offline"]
    sonda_art = _sh.load_sonda(problema, regime="offline", data_root=dr)
    ok_sonda = (len(idx_s) == sonda_art["S"]
                and all(ger[i] is None for i in idx_s)
                and all(ftm[i] is not None for i in idx_s))
    results.append(("③ sonda OFFLINE: S=20000 · geracao NULL (DI-13.5) · "
                    "fe_treino_max sem nulo",
                    (ok_sonda, f"n_sonda={len(idx_s)} (esperado {sonda_art['S']}) "
                     f"geracao_all_null={all(ger[i] is None for i in idx_s)}")))
    gb = [ger[i] for i in idx_b]
    # [DI-31] contiguidade 1..N (mesmo endurecimento que a DI-29 deu ao c311;
    # o b5 é single-fase, então basta o conjunto ser {1..max}).
    gset_b = set(g for g in gb if g is not None)
    ok_busca = (len(idx_b) > 0
                and all(g is not None for g in gb)
                and gset_b == set(range(1, max(gset_b) + 1))
                and all(int(ftm[i]) == n_ds - 1 for i in idx_b)
                and all(rsid[i] is None for i in idx_b)
                and esp <= {"cru"})
    ger_rng = f"{min(gb)}..{max(gb)}" if gb else "∅"   # guarda ③-vazia [DI-29]
    results.append(("③ busca: geracao inteira CONTÍGUA 1..N · fe_treino_max=n_ds−1 · "
                    "real_solution_id NULL (② vazia — DI-16.17) · espaco_modelo∈{cru}",
                    (ok_busca, f"n_busca={len(idx_b)} "
                     f"ger∈[{ger_rng}] espaco={esp} "
                     f"rsid_all_null={all(rsid[i] is None for i in idx_b)}")))
    mucols = [c for c in surr.schema.names if c.startswith("mu_")]
    sgcols = [c for c in surr.schema.names if c.startswith("sigma_")]
    # [DI-31] μ_*/σ_* não-nulos em TODA a ③-busca (antes só a 1ª linha idx_b[0]).
    ok_musg = (len(mucols) == M and len(sgcols) == M and bool(idx_b)
               and all(surr.column(c)[i].as_py() is not None
                       for c in mucols + sgcols for i in idx_b))
    results.append(("③ regressor probabilístico: μ_* E σ_* preenchidos (M cada) "
                    "em TODA a ③-busca",
                    (ok_musg, f"mu_*={len(mucols)} sigma_*={len(sgcols)} M={M} "
                     f"n_busca={len(idx_b)}")))

    # (6) ④ timing — b5 NÃO é piso ⇒ tempo_fit_s NÃO-nulo.
    tim = pq.read_table(layers["timing"])
    tfit = tim.column("tempo_fit_s").to_pylist()
    tbus = tim.column("tempo_busca_s").to_pylist()
    results.append(("④ timing: ≥1 linha · tempo_fit_s NÃO-nulo (b5 não é piso) · "
                    "tempo_busca_s preenchido",
                    (tim.num_rows >= 1 and all(v is not None for v in tfit)
                     and all(v is not None for v in tbus),
                     f"rows={tim.num_rows} tempo_fit_s={[round(v, 3) for v in tfit if v is not None]} "
                     f"tempo_busca_s={[round(v, 2) for v in tbus if v is not None]}")))

    # (7) ⑤ manifesto.
    tb = man.get("timing") or {}
    results.append(("⑤ manifesto: timing §17.6 + sigma_dict (DEF-C4) + sonda + "
                    "regime offline + status ok",
                    (all(tb.get(k) is not None for k in
                         ("tempo_total_s", "tempo_fit_surrogate_s",
                          "tempo_busca_s", "tempo_aval_real_s"))
                     and bool(man.get("sigma_dict")) and bool(man.get("sonda"))
                     and man.get("regime") == "offline"
                     and man.get("status") == "ok",
                     f"sigma_dict={bool(man.get('sigma_dict'))} "
                     f"sonda={bool(man.get('sonda'))} regime={man.get('regime')} "
                     f"status={man.get('status')}")))

    # (8) ⑦ reconstituível da ③ (o invariante DI-16.16 — delega ao final_eval).
    results.append(("⑦ __final presente e RECONSTITUÍVEL da ③ (última geração) — "
                    "DI-16.16/DI-08",
                    _check_final_layer(exp, alg, problema, semente, dr)))
    return results


def check_r3_c311(exp="off", problema="MMF1", semente=0, data_root=None):
    """[R3-c311] Afere o run OFFLINE JÁ GRAVADO do TGPR-MO (treed-GP/GPy) —
    encanamento objetivo (D97: fidelidade é do autor, a posteriori). ADITIVO: LÊ
    o que o runner persistiu, NÃO re-roda. Molde: `check_r3_b5`. Diferenças c311:

      • ③ sonda = **2 BLOCOS** (treedGP_build + treedGP_final, DI-16.12), cada
        S=20000 ⇒ 40000 linhas, TODAS geracao NULL;
      • ③ busca: contador `geracao` ÚNICO 1..N atravessando as 2 fases (C311-11);
        modelo_flag ∈ {treedGP_build, treedGP_final};
      • ④ = 1 linha por RETREINO de construção (C311-09; ≥1 basta aqui).
    Resto = idem b5 (regime offline): 6-7 camadas (⑦ OBRIGATÓRIA), FE=31D−1=|dataset|,
    ① = dataset bit-a-bit, CP-init x_hash E f_hash, ② vazia aceitável (DI-16.17),
    μ_*/σ_* preenchidos, ⑤ manifesto completo, ⑦ reconstituível da ③.
    """
    import numpy as np
    import pyarrow.parquet as pq
    from src import experiment as _exp
    from src import standalone_harness as _sh

    alg = "c311"
    results = []
    semente = int(semente)
    dr = data_root or os.path.join(ROOT, "data")

    prob_obj = _exp._instantiate_problem(problema)
    D, M = int(prob_obj.n_var), int(prob_obj.n_obj)
    # [T7-sweep] |dataset| POR CÉLULA: 31D−1 no principal, n do tier no sweep
    # (lido do sidecar). O gate tem de aferir contra o que o run REALMENTE leu.
    n_ds, _origem_n = n_dataset_esperado(exp, problema, semente, D,
                                         data_root=dr)
    if n_ds is None:
        return [("expectativa de |dataset| do sweep", (False, _origem_n))]

    # (1) camadas presentes (⑦ é OBRIGATÓRIA no offline).
    layers = {L: naming.layer_path(exp, alg, problema, semente, L, data_root=dr)
              for L in ("real", "pop", "surrogate", "timing", "final")}
    manp = naming.manifest_path(exp, alg, problema, semente, data_root=dr)
    faltam = [L for L, p in layers.items() if not os.path.exists(p)]
    if not os.path.exists(manp):
        faltam.append("manifest")
    if faltam:
        return [("as 6-7 camadas presentes (rode o c311 ANTES do accept)",
                 (False, f"faltam: {faltam} — pasta {os.path.dirname(manp)}"))]
    results.append(("6-7 camadas presentes (①②③④⑤ + ⑦ __final — D-12)",
                    (True, "todas presentes")))

    man = json.load(open(manp, encoding="utf-8"))
    # [T7-sweep] o gate carrega a MESMA variante que o runner (do token exp) —
    # se carregasse o principal, um run de sweep seria comparado bit-a-bit
    # contra o dataset errado e reprovaria (ou pior, passaria por engano).
    _t_ds, _d_ds = naming.dataset_variant(exp)
    ds = _sh.load_dataset(problema, semente, tier=_t_ds, dist=_d_ds,
                          data_root=dr)

    # (2) ① = dataset bit-exato + fase `init` + FE=31D−1.
    real = pq.read_table(layers["real"])
    Xr = np.column_stack([np.asarray(real.column(f"x{j}"), dtype=np.float64)
                          for j in range(D)])
    Fr = np.column_stack([np.asarray(real.column(f"f{j}"), dtype=np.float64)
                          for j in range(M)])
    bitex = (np.array_equal(Xr, ds["X"].astype(np.float32).astype(np.float64))
             and np.array_equal(Fr, ds["F"].astype(np.float32).astype(np.float64)))
    fases = set(real.column("fase").to_pylist())
    results.append(("FE final = 31D−1 = |dataset| (D90) · ① = o dataset bit-a-bit "
                    "(pós-cast float32) · fase toda `init`",
                    (real.num_rows == n_ds and bitex and fases == {"init"},
                     f"rows={real.num_rows} (esperado {n_ds}) bitex={bitex} "
                     f"fases={sorted(fases)}")))

    # (3) CP-init OFFLINE (o mais forte — X E F).
    cpo = man.get("cp_init_offline") or {}
    results.append(("CP-init OFFLINE: x_hash **E** f_hash == sidecar do dataset (D90)",
                    (cpo.get("x_hash") == ds["x_hash"]
                     and cpo.get("f_hash") == ds["f_hash"],
                     f"x={str(cpo.get('x_hash'))[:12]}… f={str(cpo.get('f_hash'))[:12]}…")))

    # (4) ② VAZIA é ACEITÁVEL (DI-16.17).
    pop = pq.read_table(layers["pop"])
    results.append(("② membership: schema válido; VAZIA por construção é "
                    "ACEITÁVEL (DI-16.17 — init LHS ≠ dataset)",
                    (set(pop.schema.names) >= {"algoritmo", "problema",
                     "semente", "geracao", "solution_id"},
                     f"rows={pop.num_rows} (vazia OK)")))

    # (5) ③ regime POR LINHA: 2 blocos de sonda (DI-16.12) + contador C311-11.
    surr = pq.read_table(layers["surrogate"])
    reg = surr.column("regime").to_pylist()
    ger = surr.column("geracao").to_pylist()
    ftm = surr.column("fe_treino_max").to_pylist()
    esp = set(v for v in surr.column("espaco_modelo").to_pylist()
              if v not in (None, ""))
    rsid = surr.column("real_solution_id").to_pylist()
    mflag = surr.column("modelo_flag").to_pylist()
    idx_s = [i for i, r in enumerate(reg) if r == "sonda"]
    idx_b = [i for i, r in enumerate(reg) if r == "offline"]
    sonda_art = _sh.load_sonda(problema, regime="offline", data_root=dr)
    S = sonda_art["S"]
    n_build = sum(1 for i in idx_s if mflag[i] == "treedGP_build")
    n_final = sum(1 for i in idx_s if mflag[i] == "treedGP_final")
    ok_sonda = (len(idx_s) == 2 * S and n_build == S and n_final == S
                and all(ger[i] is None for i in idx_s)
                and all(ftm[i] is not None for i in idx_s))
    results.append(("③ sonda OFFLINE: 2 BLOCOS treedGP_build+treedGP_final (DI-16.12) "
                    "· S=20000 cada · geracao NULL (DI-13.5) · fe_treino_max sem nulo",
                    (ok_sonda, f"n_sonda={len(idx_s)} (esperado {2*S}) "
                     f"build={n_build} final={n_final} "
                     f"ger_all_null={all(ger[i] is None for i in idx_s)}")))
    gb = [ger[i] for i in idx_b]
    flags_b = set(mflag[i] for i in idx_b)
    # [DI-29] Endurecido pós-auditoria do fechamento 21/21: o check anunciava o
    # contador ÚNICO C311-11 mas só aferia min==1 — um reset do contador na fase
    # final, um buraco de geração ou a ausência de uma das 2 fases passariam
    # VERDE. Agora o check defende o que anuncia (contíguo 1..N + AMBAS as fases).
    gset = set(g for g in gb if g is not None)
    ok_busca = (len(idx_b) > 0 and all(g is not None for g in gb)
                and gset == set(range(1, max(gset) + 1))
                and flags_b == {"treedGP_build", "treedGP_final"}
                and all(int(ftm[i]) == n_ds - 1 for i in idx_b)
                and all(rsid[i] is None for i in idx_b)
                and esp <= {"cru"})
    ger_rng = f"{min(gb)}..{max(gb)}" if gb else "∅"
    results.append(("③ busca: contador geracao ÚNICO E CONTÍGUO 1..N atravessando "
                    "as 2 fases (C311-11) · modelo_flag == {treedGP_build,"
                    "treedGP_final} · fe_treino_max=n_ds−1 · real_solution_id NULL "
                    "(② vazia) · espaco∈{cru}",
                    (ok_busca, f"n_busca={len(idx_b)} ger∈[{ger_rng}] "
                     f"flags={sorted(flags_b)} espaco={esp}")))
    mucols = [c for c in surr.schema.names if c.startswith("mu_")]
    sgcols = [c for c in surr.schema.names if c.startswith("sigma_")]
    # [DI-31] μ_*/σ_* não-nulos em TODA a ③-busca (antes só idx_b[0]). No c311 o σ
    # é NaN nas folhas só-árvore, mas NaN≠NULL (é finito no schema): a checagem é
    # de NÃO-NULO, que vale em toda a busca.
    ok_musg = (len(mucols) == M and len(sgcols) == M and bool(idx_b)
               and all(surr.column(c)[i].as_py() is not None
                       for c in mucols + sgcols for i in idx_b))
    results.append(("③ regressor probabilístico: μ_* E σ_* preenchidos (M cada) "
                    "em TODA a ③-busca",
                    (ok_musg, f"mu_*={len(mucols)} sigma_*={len(sgcols)} M={M} "
                     f"n_busca={len(idx_b)}")))

    # (6) ④ timing — c311 NÃO é piso ⇒ tempo_fit_s não-nulo; 1 linha por retreino.
    tim = pq.read_table(layers["timing"])
    tfit = tim.column("tempo_fit_s").to_pylist()
    tbus = tim.column("tempo_busca_s").to_pylist()
    results.append(("④ timing: ≥1 linha (1 por RETREINO de construção — C311-09) · "
                    "tempo_fit_s NÃO-nulo (c311 não é piso) · tempo_busca_s preenchido",
                    (tim.num_rows >= 1 and all(v is not None for v in tfit)
                     and all(v is not None for v in tbus),
                     f"rows={tim.num_rows} tempo_fit_s={[round(v, 3) for v in tfit if v is not None]}")))

    # (7) ⑤ manifesto.
    tb = man.get("timing") or {}
    results.append(("⑤ manifesto: timing §17.6 + sigma_dict (DEF-C4) + sonda + "
                    "regime offline + status ok",
                    (all(tb.get(k) is not None for k in
                         ("tempo_total_s", "tempo_fit_surrogate_s",
                          "tempo_busca_s", "tempo_aval_real_s"))
                     and bool(man.get("sigma_dict")) and bool(man.get("sonda"))
                     and man.get("regime") == "offline"
                     and man.get("status") == "ok",
                     f"sigma_dict={bool(man.get('sigma_dict'))} "
                     f"sonda={bool(man.get('sonda'))} regime={man.get('regime')} "
                     f"status={man.get('status')}")))

    # (8) ⑦ reconstituível da ③ (o invariante DI-16.16 — delega ao final_eval).
    results.append(("⑦ __final presente e RECONSTITUÍVEL da ③ (última geração) — "
                    "DI-16.16/DI-08",
                    _check_final_layer(exp, alg, problema, semente, dr)))
    return results


def check_r3_piso_off(exp="off", problema="MMF1", semente=0, data_root=None):
    """[R3-piso-off] Afere o run OFFLINE JÁ GRAVADO do piso MOEA/D-média
    (moead_media, mode 12 = Gen-MOEA/D PBI) — a ablação cirúrgica do b5 ("b5 sem
    σ"). Encanamento objetivo (D97: fidelidade é do autor, a posteriori).
    ADITIVO: LÊ o que o runner persistiu, NÃO re-roda. Molde: `check_r3_b5`.
    Diferenças do PISO (vs b5):

      • ③ **σ_* = NULL em TODA a ③** (busca E sonda) — DI-16.1: o piso reporta SÓ
        μ ("b5 sem σ"); μ_* preenchido;
      • ④ = **1 LINHA** (treino ÚNICO) com tempo_fit_s NÃO-nulo — o piso OFFLINE
        TREINA um GP (DI-16.1), ao contrário dos 4 pisos ONLINE;
      • N = o LATTICE do b5m (DI-16.4): a pop da última geração = 50 (M=2) /
        105 (M=3), NÃO 100.
    Resto = idem b5 (regime offline): 1 bloco de sonda S=20000 geracao-NULL, 6-7
    camadas (⑦ OBRIGATÓRIA), FE=31D−1=|dataset|, ① = dataset bit-a-bit, CP-init
    x_hash E f_hash, ② vazia aceitável (DI-16.17), ⑤ manifesto completo, ⑦
    reconstituível da ③ (DI-16.16).
    """
    import numpy as np
    import pyarrow.parquet as pq
    from src import experiment as _exp
    from src import standalone_harness as _sh

    alg = "moead_media"
    results = []
    semente = int(semente)
    dr = data_root or os.path.join(ROOT, "data")

    prob_obj = _exp._instantiate_problem(problema)
    D, M = int(prob_obj.n_var), int(prob_obj.n_obj)
    # [T7-sweep] |dataset| POR CÉLULA: 31D−1 no principal, n do tier no sweep
    # (lido do sidecar). O gate tem de aferir contra o que o run REALMENTE leu.
    n_ds, _origem_n = n_dataset_esperado(exp, problema, semente, D,
                                         data_root=dr)
    if n_ds is None:
        return [("expectativa de |dataset| do sweep", (False, _origem_n))]

    # (1) camadas presentes (⑦ é OBRIGATÓRIA no offline).
    layers = {L: naming.layer_path(exp, alg, problema, semente, L, data_root=dr)
              for L in ("real", "pop", "surrogate", "timing", "final")}
    manp = naming.manifest_path(exp, alg, problema, semente, data_root=dr)
    faltam = [L for L, p in layers.items() if not os.path.exists(p)]
    if not os.path.exists(manp):
        faltam.append("manifest")
    if faltam:
        return [("as 6-7 camadas presentes (rode o piso-off ANTES do accept)",
                 (False, f"faltam: {faltam} — pasta {os.path.dirname(manp)}"))]
    results.append(("6-7 camadas presentes (①②③④⑤ + ⑦ __final — D-12)",
                    (True, "todas presentes")))

    man = json.load(open(manp, encoding="utf-8"))
    # [T7-sweep] o gate carrega a MESMA variante que o runner (do token exp) —
    # se carregasse o principal, um run de sweep seria comparado bit-a-bit
    # contra o dataset errado e reprovaria (ou pior, passaria por engano).
    _t_ds, _d_ds = naming.dataset_variant(exp)
    ds = _sh.load_dataset(problema, semente, tier=_t_ds, dist=_d_ds,
                          data_root=dr)

    # (2) ① = dataset bit-exato + fase `init` + FE=31D−1.
    real = pq.read_table(layers["real"])
    Xr = np.column_stack([np.asarray(real.column(f"x{j}"), dtype=np.float64)
                          for j in range(D)])
    Fr = np.column_stack([np.asarray(real.column(f"f{j}"), dtype=np.float64)
                          for j in range(M)])
    bitex = (np.array_equal(Xr, ds["X"].astype(np.float32).astype(np.float64))
             and np.array_equal(Fr, ds["F"].astype(np.float32).astype(np.float64)))
    fases = set(real.column("fase").to_pylist())
    results.append(("FE final = 31D−1 = |dataset| (D90) · ① = o dataset bit-a-bit "
                    "(pós-cast float32) · fase toda `init`",
                    (real.num_rows == n_ds and bitex and fases == {"init"},
                     f"rows={real.num_rows} (esperado {n_ds}) bitex={bitex} "
                     f"fases={sorted(fases)}")))

    # (3) CP-init OFFLINE (o mais forte — X E F).
    cpo = man.get("cp_init_offline") or {}
    results.append(("CP-init OFFLINE: x_hash **E** f_hash == sidecar do dataset (D90)",
                    (cpo.get("x_hash") == ds["x_hash"]
                     and cpo.get("f_hash") == ds["f_hash"],
                     f"x={str(cpo.get('x_hash'))[:12]}… f={str(cpo.get('f_hash'))[:12]}…")))

    # (4) ② VAZIA é ACEITÁVEL (DI-16.17).
    pop = pq.read_table(layers["pop"])
    results.append(("② membership: schema válido; VAZIA por construção é "
                    "ACEITÁVEL (DI-16.17 — init LHS ≠ dataset)",
                    (set(pop.schema.names) >= {"algoritmo", "problema",
                     "semente", "geracao", "solution_id"},
                     f"rows={pop.num_rows} (vazia OK)")))

    # (5) ③ regime POR LINHA: 1 bloco de sonda + σ NULL em TODA a ③ (DI-16.1).
    surr = pq.read_table(layers["surrogate"])
    reg = surr.column("regime").to_pylist()
    ger = surr.column("geracao").to_pylist()
    ftm = surr.column("fe_treino_max").to_pylist()
    esp = set(v for v in surr.column("espaco_modelo").to_pylist()
              if v not in (None, ""))
    rsid = surr.column("real_solution_id").to_pylist()
    mflag = surr.column("modelo_flag").to_pylist()
    idx_s = [i for i, r in enumerate(reg) if r == "sonda"]
    idx_b = [i for i, r in enumerate(reg) if r == "offline"]
    sonda_art = _sh.load_sonda(problema, regime="offline", data_root=dr)
    S = sonda_art["S"]
    ok_sonda = (len(idx_s) == S
                and all(ger[i] is None for i in idx_s)
                and all(ftm[i] is not None for i in idx_s)
                and all(mflag[i] == _MODELO_FLAG_PISO for i in idx_s))
    results.append(("③ sonda OFFLINE: 1 BLOCO S=20000 · geracao NULL (DI-13.5) · "
                    "fe_treino_max sem nulo · modelo_flag único",
                    (ok_sonda, f"n_sonda={len(idx_s)} (esperado {S}) "
                     f"geracao_all_null={all(ger[i] is None for i in idx_s)}")))
    gb = [ger[i] for i in idx_b]
    # [DI-31] contiguidade 1..N (antes só min==1; buraco de geração passava VERDE).
    gset_b = set(g for g in gb if g is not None)
    ok_busca = (len(idx_b) > 0
                and all(g is not None for g in gb)
                and gset_b == set(range(1, max(gset_b) + 1))
                and all(int(ftm[i]) == n_ds - 1 for i in idx_b)
                and all(rsid[i] is None for i in idx_b)
                and esp <= {"cru"})
    ger_rng = f"{min(gb)}..{max(gb)}" if gb else "∅"   # guarda ③-vazia [DI-29]
    results.append(("③ busca: geracao inteira CONTÍGUA 1..N · fe_treino_max=n_ds−1 · "
                    "real_solution_id NULL (② vazia — DI-16.17) · espaco_modelo∈{cru}",
                    (ok_busca, f"n_busca={len(idx_b)} ger∈[{ger_rng}] "
                     f"espaco={esp} rsid_all_null={all(rsid[i] is None for i in idx_b)}")))
    # μ_* preenchido · σ_* NULL em TODA a ③ — o piso é "b5 sem σ" (DI-16.1).
    mucols = [c for c in surr.schema.names if c.startswith("mu_")]
    sgcols = [c for c in surr.schema.names if c.startswith("sigma_")]
    ok_mu = (len(mucols) == M
             and all(surr.column(c).null_count == 0 for c in mucols))
    ok_sigma_null = (len(sgcols) == M
                     and all(surr.column(c).null_count == surr.num_rows
                             for c in sgcols))
    results.append(("③ piso 'b5 sem σ' (DI-16.1): μ_* preenchido (M) · "
                    "σ_* = NULL em TODA a ③ (busca E sonda)",
                    (ok_mu and ok_sigma_null,
                     f"mu_*={len(mucols)} (sem nulo? {ok_mu}) "
                     f"sigma_*={len(sgcols)} (todos NULL? {ok_sigma_null})")))
    # N = o lattice do b5m (DI-16.4): a pop da última geração = 50 (M=2)/105 (M=3).
    N_exp = {2: 50, 3: 105}.get(M)
    gmax = max(gb) if gb else 0
    n_lastgen = sum(1 for i in idx_b if ger[i] == gmax)
    results.append(("N = o lattice do b5m (DI-16.4): pop da última geração = "
                    "50 (M=2) / 105 (M=3), NÃO 100",
                    (None if N_exp is None else (n_lastgen == N_exp),
                     f"N(pop última ger {gmax})={n_lastgen} esperado={N_exp} (M={M})")))

    # (6) ④ timing — o piso OFFLINE TREINA (DI-16.1) ⇒ tempo_fit_s NÃO-nulo; 1 LINHA.
    tim = pq.read_table(layers["timing"])
    tfit = tim.column("tempo_fit_s").to_pylist()
    tbus = tim.column("tempo_busca_s").to_pylist()
    results.append(("④ timing: 1 LINHA (treino único) · tempo_fit_s NÃO-nulo (o "
                    "piso OFFLINE treina um GP — DI-16.1) · tempo_busca_s preenchido",
                    (tim.num_rows == 1 and all(v is not None for v in tfit)
                     and all(v is not None for v in tbus),
                     f"rows={tim.num_rows} (esperado 1) "
                     f"tempo_fit_s={[round(v, 3) for v in tfit if v is not None]} "
                     f"tempo_busca_s={[round(v, 2) for v in tbus if v is not None]}")))

    # (7) ⑤ manifesto.
    tb = man.get("timing") or {}
    results.append(("⑤ manifesto: timing §17.6 + sigma_dict (DEF-C4) + sonda + "
                    "regime offline + status ok",
                    (all(tb.get(k) is not None for k in
                         ("tempo_total_s", "tempo_fit_surrogate_s",
                          "tempo_busca_s", "tempo_aval_real_s"))
                     and bool(man.get("sigma_dict")) and bool(man.get("sonda"))
                     and man.get("regime") == "offline"
                     and man.get("status") == "ok",
                     f"sigma_dict={bool(man.get('sigma_dict'))} "
                     f"sonda={bool(man.get('sonda'))} regime={man.get('regime')} "
                     f"status={man.get('status')}")))

    # (8) ⑦ reconstituível da ③ (o invariante DI-16.16 — delega ao final_eval).
    results.append(("⑦ __final presente e RECONSTITUÍVEL da ③ (última geração) — "
                    "DI-16.16/DI-08",
                    _check_final_layer(exp, alg, problema, semente, dr)))
    return results


#: modelo_flag canônico do piso (espelha src.piso_offline._MODELO_FLAG; o accept
#: NÃO importa o runner do env_b5 — declara a constante para checar a ③).
_MODELO_FLAG_PISO = "moead_media/MOEAD-PBI+GPR-media"


def _check_export_schema_r3(exp, alg, problema, semente, D, M, data_root):
    """Como `_check_export_schema`, mas sem exigir a coexistência μ+classe na
    ③ (aquilo é do STUB do F0-03/R2-00; os configs offline da R3 são
    regressores puros — C1 continua satisfeito com μ). Reusa os schemas
    schema-as-code de `src.export`."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
    from src import export
    want = {"real": export.real_schema(D, M), "pop": export.pop_schema(),
            "surrogate": export.surrogate_schema(D, M),
            "timing": export.timing_schema()}
    for layer, sch in want.items():
        p = naming.layer_path(exp, alg, problema, semente, layer,
                              data_root=data_root)
        got = pq.read_schema(p).remove_metadata()
        if not got.equals(sch, check_metadata=False):
            return False, (f"schema da camada {layer} diverge do §17.2 "
                           f"(esperado {sch.names}, obtido {got.names})")
    surr = pq.read_table(naming.layer_path(exp, alg, problema, semente,
                                           "surrogate", data_root=data_root))
    n_mu = surr.num_rows - pc.sum(pc.is_null(surr.column("mu_0"))).as_py()
    if n_mu == 0:
        return False, "③ sem nenhuma linha de regressor (μ preenchido) — C1"
    real_sch = pq.read_schema(naming.layer_path(exp, alg, problema, semente,
                                                "real", data_root=data_root))
    if (real_sch.field("x0").type != pa.float32()
            or real_sch.field("f0").type != pa.float32()):
        return False, "camada ① não está em float32 (D53)"
    return True, (f"schemas §17.2 exatos (①②③+timing) · ③ com μ ({n_mu} "
                  f"linhas) · float32 (D53)")


def _check_final_layer(exp, alg, problema, semente, data_root):
    """Delega ao `check_final` do `scripts/final_eval.py` (fonte única do
    check da ⑦ — o gate não reimplementa a regra do DI-08)."""
    import importlib.util
    p = os.path.join(ROOT, "scripts", "final_eval.py")
    spec = importlib.util.spec_from_file_location("_final_eval", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_final(exp, alg, problema, semente, data_root=data_root)


def _r3_rng_guard_probe(problema):
    """N.2.3 — a guarda de RNG, provada em DOIS níveis.

    ⚠ Por que dois: MEDIDO nesta sessão, `pymoo 0.6.2` (env-main) **não
    desloca** `np.random`/`random` — nem com `seed=`, nem sem. Rodar só a
    prova "contra o pymoo real" daria VERDE mesmo que `preserve_global_rng`
    fosse um `pass`. A premissa do contrato R3 item 3 vale para o **pymoo
    ANTIGO** dos venvs `env_b5`/`env_c311`, que é onde b5/c311 rodam.

    (a) MECÂNICA: perturba ao máximo dentro da guarda e exige restauração
        bit-a-bit — é este o teste que tem conteúdo aqui;
    (b) INTEGRAÇÃO: roda um NSGA-II REAL pelo embrulho e confere o estado,
        registrando de passagem o comportamento desta versão do pymoo.
    """
    try:
        import random
        import numpy as np
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from src import experiment as _exp
        from src import standalone_harness as _sh
    except ImportError as exc:
        return None, f"pymoo ausente — skip ({exc})"

    # (a) prova mecânica
    np.random.seed(7)
    random.seed(7)
    np_b, py_b = np.random.get_state(), random.getstate()
    with _sh.preserve_global_rng():
        np.random.seed(999999)          # exatamente o que o pymoo antigo faz
        random.seed(999999)
        np.random.random(50)
    mec = (np.array_equal(np_b[1], np.random.get_state()[1])
           and np_b[2:] == np.random.get_state()[2:]
           and py_b == random.getstate())

    # (b) integração com o culpado nominal
    prob = _exp._instantiate_problem(problema)
    np_c, py_c = np.random.get_state(), random.getstate()
    _sh.guarded_pymoo_minimize(prob, NSGA2(pop_size=8), ("n_gen", 2),
                               seed=1, verbose=False)
    integ = (np.array_equal(np_c[1], np.random.get_state()[1])
             and py_c == random.getstate())

    import pymoo
    return (mec and integ,
            f"(a) restauração bit-a-bit sob perturbação máxima={mec} · "
            f"(b) NSGA-II real sob o embrulho={integ} · nota: pymoo "
            f"{pymoo.__version__} não desloca os globais — a guarda é para o "
            f"pymoo antigo de env_b5/env_c311 (N.2.3)")


def _r3_env_resolution():
    """Cada um dos 6 configs R3 resolve para um interpretador via `envs.json`,
    e b5* × c311 caem em ENVS DISTINTOS (N.1.2 — o achado nº 1 do contrato)."""
    from src import standalone_harness as _sh
    alvos = ("c122", "c149", "e81", "b5r", "b5m", "c311", "moead_media")
    mapa = {}
    for alg in alvos:
        try:
            mapa[alg] = _sh.interpreter_for_alg(alg)[0]
        except KeyError as exc:
            return False, f"{alg}: {exc}"
    if mapa["b5r"] == mapa["c311"]:
        return False, (f"b5r e c311 no MESMO env ({mapa['b5r']}) — N.1.2 exige "
                       f"venvs distintos (desdeo_* vendorizado homônimo)")
    # ⚠ A tabela sozinha é verdadeira por construção — seria verde mesmo que
    # ninguém jamais chamasse `run_in_venv`. O que importa é o MECANISMO:
    # (a) os 4 configs de overlay estão marcados como venv-only, e
    # (b) a sentinela de colisão realmente ABORTA quando dois overlays de
    #     raízes diferentes aparecem no mesmo processo.
    if not {"b5r", "b5m", "moead_media", "c311"} <= set(_sh.VENV_ONLY_ALGS):
        return False, (f"VENV_ONLY_ALGS não cobre os 4 configs de overlay: "
                       f"{sorted(_sh.VENV_ONLY_ALGS)} — o roteamento de "
                       f"`experiment.run` não os protegeria (N.1.2)")
    _sh._OVERLAY_SEEN.clear()
    try:
        _sh._OVERLAY_SEEN["desdeo_emo"] = "/raiz/b5"
        import types
        falso = types.ModuleType("desdeo_emo")
        falso.__file__ = "/raiz/c311/desdeo_emo/__init__.py"
        sys.modules["desdeo_emo"] = falso
        try:
            _sh.assert_overlay_coerente()
            return False, ("a sentinela de colisão de overlay NÃO disparou "
                           "com dois `desdeo_emo` de raízes distintas (N.1.2)")
        except RuntimeError:
            pass
    finally:
        sys.modules.pop("desdeo_emo", None)
        _sh._OVERLAY_SEEN.clear()
    return True, (f"{mapa} · b5*={mapa['b5r']} ≠ c311={mapa['c311']} · "
                  f"VENV_ONLY_ALGS roteia os 4 · sentinela de colisão ABORTA")


def _r3_subprocess_probe(problema, semente, repo_data):
    """O mecanismo D79/N.2 roda DE VERDADE: despacha o STUB no interpretador
    resolvido pelo `envs.json` (env-main, o único provisionado no Mac) e
    confere que o filho devolveu o resultado e nasceu com o pin de threads."""
    import shutil
    from src import experiment as _exp
    from src import standalone_harness as _sh
    try:
        _, interp = _sh.interpreter_for_alg("c122")     # env-main
    except KeyError as exc:
        return False, f"resolução de env falhou: {exc}"
    if not os.path.exists(interp):
        return None, f"interpretador ausente — skip ({interp})"
    with tempfile.TemporaryDirectory() as dr:
        for sub in ("datasets", "sonda"):
            shutil.copytree(os.path.join(repo_data, sub),
                            os.path.join(dr, sub))
        r = _sh.run_in_venv(_sh.STUB_ALG, problema, semente, exp="off",
                            data_root=dr, interpreter=interp, timeout=600)
        if not r.get("ok"):
            return False, (f"filho falhou (rc={r['returncode']}): "
                           f"{str(r.get('traceback'))[-400:]}")
        # ⚠ Exigir ÂNCORAS VINDAS DE DENTRO DO FILHO. Sem isto o check era
        # tautológico: dava VERDE com o pin D79 quebrado no filho (provado —
        # `OMP_NUM_THREADS=8` passava) e com o resultado vazio. E é justamente
        # o subprocesso com env limpo que o módulo declara ser o pinning
        # AUTORITATIVO da bateria.
        res = r.get("result") or {}
        prob_obj = _exp._instantiate_problem(problema)
        fe_esperado = maxfe(int(prob_obj.n_var))
        pin = res.get("pin_filho") or ""
        pin_ok = pin and all(f"{v}=1" in pin for v in _sh.D79_THREAD_VARS)
        fe_ok = res.get("fe_final") == fe_esperado
        iso_ok = bool(res.get("isolated_filho"))
        if not (pin_ok and fe_ok and iso_ok):
            return False, (f"evidência do filho insuficiente: pin={pin!r} "
                           f"(ok={pin_ok}) · fe_final={res.get('fe_final')} "
                           f"(esperado {fe_esperado}) · isolated={iso_ok}")
        return True, (f"run completo no subprocesso ({os.path.basename(interp)}"
                      f"), fe_final={res['fe_final']} · pin lido DENTRO do "
                      f"filho: {pin} · `-I` ativo")


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
    ap.add_argument("--gcs-smoke", action="store_true",
                    help="[R2-00] roda também o smoke GCS REAL (rede; deleta "
                         "os blobs de teste ao fim).")
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

    # R2-00 = infra transversal BoTorch (contrato N.1/§22.3). Encanamento
    # próprio: roda o STUB `stubpy` via experiment.run num tempdir e afere o
    # contrato; --gcs-smoke liga o smoke REAL (deferido do F0-03), com limpeza.
    if a.cartao.startswith("R2-00"):
        if a.alg not in (None, "stubpy"):
            print(f"  [FAIL] o STUB do R2-00 é 'stubpy' (nunca 'stub' — os "
                  f"artefatos MATLAB do R1-00 usam esse token): --alg={a.alg!r}")
            sys.exit(2)
        results = check_r2_00(exp=a.exp, problema=a.problema,
                              semente=int(a.semente), gcs_smoke=a.gcs_smoke)
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("  [INFO] STUB stubpy (sem algoritmo real): prova só o "
              "ENCANAMENTO do contrato N.1 — c262/c154 são os cartões "
              "seguintes. Sem --gcs-smoke o bucket não é tocado.")
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # R3-00 = infra transversal standalone (contrato N.2/§22.4) + a camada ⑦
    # do DI-08. Encanamento próprio: roda o STUB OFFLINE `stubr3` via
    # experiment.run num tempdir e afere o contrato da Rodada 3.
    # ⚠ TEM de vir ANTES do catch-all abaixo: `or not a.alg` engoliria este
    # cartão (que não exige --alg) e devolveria o VERDE do andaime F0-01.
    if a.cartao.startswith("R3-00"):
        if a.alg not in (None, "stubr3"):
            print(f"  [FAIL] o STUB do R3-00 é 'stubr3' (nunca 'stub', do "
                  f"R1-00 MATLAB, nem 'stubpy', do R2-00): --alg={a.alg!r}")
            sys.exit(2)
        # O STUB é OFFLINE: o token de experimento canônico do regime é `off`
        # (D55). O default do parser é `main` (herdado dos cartões online), so
        # remapeamos e AVISAMOS — um cabeçalho que diga `main` e uma saída que
        # caia em `off` seria exatamente o tipo de silêncio que a D55 fecha.
        exp_r3 = a.exp if a.exp != "main" else "off"
        if exp_r3 != a.exp:
            print(f"  [INFO] exp remapeado {a.exp!r} → {exp_r3!r}: o STUB do "
                  f"R3-00 é OFFLINE (token canônico do regime — D55).")
        results = check_r3_00(exp=exp_r3, problema=a.problema,
                              semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("  [INFO] STUB stubr3 (sem algoritmo real): prova só o "
              "ENCANAMENTO do contrato N.2 + DI-08 — c122/b5r/b5m/c311/c149/"
              "e81/piso-off são os cartões seguintes.")
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # R3-c122 = θ-DEA-DP (1º algoritmo da Rodada 3, ONLINE). Afere o run JÁ
    # EXECUTADO (não re-roda: um run de ZDT1 leva horas) contra o contrato
    # v5.2.1 — FE exato, CP-init, 4 camadas + jsonl + manifesto, sonda e ③.
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00).
    if a.cartao.startswith("R3-c122"):
        if a.alg not in (None, "c122"):
            print(f"  [FAIL] cartão R3-c122 só afere --alg=c122: {a.alg!r}")
            sys.exit(2)
        results = check_r3_c122(exp=a.exp, problema=a.problema,
                                semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # R3-c149 = LBN-MOBO (2º algoritmo da Rodada 3, ONLINE). Afere o run JÁ
    # EXECUTADO (não re-roda) contra o contrato v5.2.1 — molde do R3-c122.
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00).
    if a.cartao.startswith("R3-c149"):
        if a.alg not in (None, "c149"):
            print(f"  [FAIL] cartão R3-c149 só afere --alg=c149: {a.alg!r}")
            sys.exit(2)
        results = check_r3_c149(exp=a.exp, problema=a.problema,
                                semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # R3-e81 = qPOTS (3º algoritmo da Rodada 3, ONLINE). Afere o run JÁ
    # EXECUTADO (não re-roda) contra o contrato v5.2.1 — molde do R3-c149,
    # + os checks PRÓPRIOS do cartão (kwargs obrigatórios do qpots(), dtype
    # float64, n_baseline N/A, n_train no jsonl, |lote|==q).
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00).
    if a.cartao.startswith("R3-e81"):
        if a.alg not in (None, "e81"):
            print(f"  [FAIL] cartão R3-e81 só afere --alg=e81: {a.alg!r}")
            sys.exit(2)
        results = check_r3_e81(exp=a.exp, problema=a.problema,
                               semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # [R3-b5] Prob-RVEA (b5r, mode 7) / Prob-MOEA/D (b5m, mode 72), OFFLINE.
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00: o
    # `or not a.alg` engoliria e devolveria o VERDE do andaime F0-01). Afere o
    # run JÁ GRAVADO (o runner roda por minutos — o accept não re-executa).
    if a.cartao.startswith("R3-b5"):
        if a.alg not in ("b5r", "b5m"):
            print(f"  [FAIL] cartão R3-b5 só afere --alg=b5r|b5m: {a.alg!r}")
            sys.exit(2)
        # b5 é OFFLINE: o token canônico do regime é `off` (idem R3-00).
        exp_b5 = a.exp if a.exp != "main" else "off"
        if a.exp == "main":
            print(f"  [INFO] exp remapeado {a.exp!r} → {exp_b5!r}: b5 é offline "
                  "(o run vive em off/{b5r,b5m}/).")
        results = check_r3_b5(a.alg, exp=exp_b5, problema=a.problema,
                              semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # [R3-c311] TGPR-MO (treed-GP/GPy), OFFLINE, env PRÓPRIO `env_c311`.
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00/b5: o
    # `or not a.alg` engoliria e devolveria o VERDE do andaime F0-01). Afere o
    # run JÁ GRAVADO (o runner roda por minutos — o accept não re-executa).
    if a.cartao.startswith("R3-c311"):
        if a.alg not in ("c311",):
            print(f"  [FAIL] cartão R3-c311 só afere --alg=c311: {a.alg!r}")
            sys.exit(2)
        # c311 é OFFLINE: o token canônico do regime é `off` (idem R3-00/b5).
        exp_c311 = a.exp if a.exp != "main" else "off"
        if a.exp == "main":
            print(f"  [INFO] exp remapeado {a.exp!r} → {exp_c311!r}: c311 é offline "
                  "(o run vive em off/c311/).")
        results = check_r3_c311(exp=exp_c311, problema=a.problema,
                                semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
        print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
              "a posteriori — não entra aqui.")
        sys.exit(1 if fail else 0)

    # [R3-piso-off] Piso MOEA/D-média (moead_media, mode 12), OFFLINE, env `env_b5`
    # (o MESMO do b5). A ablação cirúrgica do b5 ("b5 sem σ").
    # ⚠ TEM de vir ANTES do catch-all abaixo (mesma armadilha do R3-00/b5/c311: o
    # `or not a.alg` engoliria e devolveria o VERDE do andaime F0-01). Afere o
    # run JÁ GRAVADO (o runner roda por minutos — o accept não re-executa).
    if a.cartao.startswith("R3-piso-off"):
        if a.alg not in (None, "moead_media"):
            print(f"  [FAIL] cartão R3-piso-off só afere --alg=moead_media "
                  f"(ou sem --alg): {a.alg!r}")
            sys.exit(2)
        # piso-off é OFFLINE: token canônico do regime = `off` (idem R3-00/b5/c311).
        exp_piso = a.exp if a.exp != "main" else "off"
        if a.exp == "main":
            print(f"  [INFO] exp remapeado {a.exp!r} → {exp_piso!r}: o piso-off é "
                  "offline (o run vive em off/moead_media/).")
        results = check_r3_piso_off(exp=exp_piso, problema=a.problema,
                                    semente=int(a.semente))
        fail = False
        for name, (ok, msg) in results:
            mark = "SKIP" if ok is None else ("OK  " if ok else "FAIL")
            print(f"  [{mark}] {name}: {msg}")
            if ok is False:
                fail = True
        print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                            else "VERDE (encanamento objetivo)"))
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
    # [DI-41] NENHUM check pôde rodar (ex.: pyarrow/numpy ausentes no
    # interpretador) ⇒ INCONCLUSIVO, nunca VERDE. Antes, "tudo SKIP" saía 0 e o
    # `portao.py` — que lê o exit code — pintava a varredura INTEIRA de verde
    # sem ter checado UMA linha de parquet (falso-VERDE). Rode com o env_main.
    inconclusivo = all(ok is None for _, (ok, _m) in checks)
    if inconclusivo:
        print("\n  >>> INCONCLUSIVO — nenhum check pôde rodar (dependências "
              "ausentes?). NÃO é verde: rode com o interpretador do env_main.")
        sys.exit(2)
    print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail
                        else "VERDE (encanamento objetivo)"))
    print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, "
          "a posteriori — não entra aqui.")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
