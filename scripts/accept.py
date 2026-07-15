#!/usr/bin/env python3
"""accept.py — runner de aceitação OBJETIVA por cartão (Higiene v5.2 / D97).

Verifica SÓ o "encanamento" — checagens automáticas que bloqueiam a bateria:
  FE final exato, as 4 saídas válidas, CP-init, hash do DoE. NÃO julga fidelidade
  (isso é análise MANUAL do autor, a posteriori — D97; §20 da SPEC).

Uso:  python scripts/accept.py {CARTAO} [--exp main] [--alg c217] [--problema DTLZ2] [--semente 0]
Sai 0 se tudo verde; !=0 caso contrário. É o teste que o cartão referencia.

NOTA: este é o esqueleto do runner (Fase 0 preenche as leituras reais dos parquets/manifesto,
conforme o schema §17.2 e a topologia §17.7). As funções `check_*` retornam (ok, msg).
"""
import argparse, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENTS = os.path.join(ROOT, "data", "experiments")


def maxfe(problema_dim):
    return 31 * problema_dim - 1


def find_run_dir(exp, alg):
    return os.path.join(EXPERIMENTS, exp, alg)  # §17.7 (com token {exp} — D55)


def check_outputs(exp, alg, problema, semente):
    """As 4 saídas: 3 parquets (__real/__pop/__surrogate) + __timing + .jsonl + manifesto."""
    base = f"exp_{exp}_{alg}_{problema}_{semente}"
    d = find_run_dir(exp, alg)
    need = [f"{base}__real.parquet", f"{base}__pop.parquet",
            f"{base}__surrogate.parquet", f"{base}__timing.parquet",
            f"{base}.jsonl"]
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
    base = f"exp_{exp}_{alg}_{problema}_{semente}"
    real = os.path.join(find_run_dir(exp, alg), f"{base}__real.parquet")
    if not os.path.exists(real):
        return False, "camada ① ausente"
    n = pq.read_table(real).num_rows
    want = maxfe(D)
    return (n == want), f"FE=${n} (esperado {want})"


def check_doe_hash(problema, semente):
    """CP-init parcial: o DoE parquet existe e tem hash registrado (D87/D88)."""
    doe = os.path.join(ROOT, "data", "doe", problema, f"doe_{problema}_{semente}.parquet")
    if not os.path.exists(doe):
        return False, f"DoE ausente: {doe}"
    return True, "DoE parquet presente (hash validado no manifesto)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartao")
    ap.add_argument("--exp", default="main")
    ap.add_argument("--alg", required=False)
    ap.add_argument("--problema", default="ZDT1")
    ap.add_argument("--semente", default="0")
    ap.add_argument("--dim", type=int, default=30)
    a = ap.parse_args()

    print(f"== Aceitação objetiva — cartão {a.cartao} ({a.exp}/{a.alg}/{a.problema}/{a.semente}) ==")
    if not a.alg:
        print("  (sem --alg: apenas valida o andaime; passe --alg para checar um run)")
        sys.exit(0)

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
    print("\n  >>> " + ("VERMELHO — pára-e-loga (D81)" if fail else "VERDE (encanamento objetivo)"))
    print("  Lembrete (D97): a fidelidade é validação MANUAL do autor, a posteriori — não entra aqui.")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
