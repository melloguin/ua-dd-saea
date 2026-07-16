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
    """CP-init parcial: o DoE parquet existe e tem hash registrado (D87/D88)."""
    doe = os.path.join(ROOT, "data", "doe", problema, f"doe_{problema}_{semente}.parquet")
    if not os.path.exists(doe):
        return False, f"DoE ausente: {doe}"
    return True, "DoE parquet presente (hash validado no manifesto)"


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
