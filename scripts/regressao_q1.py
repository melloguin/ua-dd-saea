# -*- coding: utf-8 -*-
# [DI-36/torre] Prova de regressão q=1 do T9, PRESERVADA como script permanente
# (vivia só no scratchpad da sessão — achado da auditoria). Uso:
#   <env-main>/bin/python scripts/regressao_q1.py <tempdir>
"""[T9] PROVA DE REGRESSÃO — o caminho q=1 (principal) tem de sair BIT-A-BIT
idêntico ao disco após a mudança batch-only. Re-roda main/MMF1/s0 (q=1) em
tempdir e compara ①real ②pop ③surrogate BIT-A-BIT + ④timing estrutural
(n_acumulado/geracao) contra data/experiments/main/*. Qualquer diff = FALHA.
"""
import os
import sys
import numpy as np
import pyarrow.parquet as pq

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
os.chdir(REPO)

TDREG = sys.argv[1]
DISK = os.path.join(REPO, "data")


def read(p):
    return pq.read_table(p).to_pandas()


def cmp_layer(alg, problema, sem, layer, exact_cols=None, struct_cols=None):
    run = f"exp_main_{alg}_{problema}_{sem}"
    a = read(f"{TDREG}/experiments/main/{alg}/{run}__{layer}.parquet")
    b = read(f"{DISK}/experiments/main/{alg}/{run}__{layer}.parquet")
    if list(a.columns) != list(b.columns):
        return f"COLUNAS DIFEREM: {list(a.columns)} != {list(b.columns)}"
    if len(a) != len(b):
        return f"N LINHAS DIFERE: {len(a)} != {len(b)}"
    cols = exact_cols if exact_cols is not None else list(a.columns)
    diffs = []
    for c in cols:
        va, vb = a[c].to_numpy(), b[c].to_numpy()
        if va.dtype.kind == "f":
            # bit-a-bit: NaN==NaN e valores idênticos ao último bit
            eq = np.array_equal(va, vb, equal_nan=True)
        else:
            eq = bool((va == vb).all())
        if not eq:
            n_diff = int((~((va == vb) | (
                (va != va) & (vb != vb) if va.dtype.kind == "f" else False))).sum())
            diffs.append(f"{c}({n_diff} linhas)")
    if diffs:
        return f"VALORES DIFEREM em: {', '.join(diffs)}"
    return None


def run_one(alg, runner_fn):
    problema, sem = "MMF1", 0
    print(f"\n===== {alg}/MMF1/main/s0 (q=1) =====")
    # limpa saída anterior no tempdir
    d = f"{TDREG}/experiments/main/{alg}"
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.startswith(f"exp_main_{alg}_MMF1_0"):
                os.remove(os.path.join(d, f))
    runner_fn("main", alg, problema, sem, data_root=TDREG)  # q=1 default
    ok = True
    # ① real, ② pop, ③ surrogate — BIT-A-BIT (todas as colunas)
    for layer in ("real", "pop", "surrogate"):
        r = cmp_layer(alg, problema, sem, layer)
        print(f"  ③②① {layer:10}: {'BIT-IDÊNTICO ✅' if r is None else 'DIFERE ❌ ' + r}")
        ok = ok and (r is None)
    # ④ timing — estrutural (n_acumulado/geracao), tempo_* variam por wall
    struct = [c for c in ("geracao", "n_acumulado", "run_id") ]
    r = cmp_layer(alg, problema, sem, "timing", exact_cols=struct)
    print(f"  ④ timing (estrut): {'IDÊNTICO ✅' if r is None else 'DIFERE ❌ ' + r}")
    ok = ok and (r is None)
    return ok


def main():
    from src.c262_qnehvi import run_c262
    from src.c154_jes import run_c154
    ok262 = run_one("c262", run_c262)
    ok154 = run_one("c154", run_c154)
    print("\n" + "=" * 50)
    if ok262 and ok154:
        print("PROVA DE REGRESSÃO ✅ — q=1 BIT-IDÊNTICO nos 2 (c262 + c154).")
        sys.exit(0)
    else:
        print(f"PROVA DE REGRESSÃO ❌ — c262 ok={ok262}, c154 ok={ok154}. PARE E DIAGNOSTIQUE.")
        sys.exit(1)


if __name__ == "__main__":
    main()
