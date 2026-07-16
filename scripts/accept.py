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

def check_outputs(exp, alg, problema, semente):
    """As 4 saídas: 3 parquets (__real/__pop/__surrogate) + __timing + .jsonl."""
    d = naming.run_dir(exp, alg, data_root=os.path.join(ROOT, "data"))
    need = naming.output_filenames(exp, alg, problema, semente)
    missing = [n for n in need if not os.path.exists(os.path.join(d, n))]
    if missing:
        return False, f"saídas faltando: {missing} (em {d})"
    return True, "4 saídas + jsonl presentes"


def check_fe(exp, alg, problema, semente, D):
    """FE final = 31D-1 EXATO — nº de linhas DISTINTAS da camada ① (D89)."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None, "pyarrow ausente — skip (instalar no env)"
    real = naming.layer_path(exp, alg, problema, semente, "real",
                             data_root=os.path.join(ROOT, "data"))
    if not os.path.exists(real):
        return False, "camada ① ausente"
    n = pq.read_table(real).num_rows
    want = maxfe(D)
    return (n == want), f"FE={n} (esperado {want})"


def check_doe_hash(problema, semente):
    """CP-init (parte objetiva do harness, D87/D88): o DoE parquet existe E o
    hash do ARRAY DECODIFICADO bate com o do sidecar. Consome `src.naming`
    (fonte única do caminho) e `src.doe` (re-hash). Se `pyarrow`/`numpy` não
    estiverem no interpretador, cai p/ checagem de existência (skip do re-hash)."""
    from src import naming
    doe_p = naming.doe_path(problema, semente, data_root=os.path.join(ROOT, "data"))
    man_p = naming.doe_manifest_path(problema, semente, data_root=os.path.join(ROOT, "data"))
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
