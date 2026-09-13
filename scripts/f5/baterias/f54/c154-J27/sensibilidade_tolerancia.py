"""F5.4 — c154-J27: a conclusao sobrevive a QUALQUER criterio de tolerancia?

Varre rtol de 1e-13 a 1e-3 no teste A (pares de linhas bit-identicas em x/mu/sigma
tem de ter alpha identico sob a permutacao correta) e reporta H1 x H0 x nulo.
Tambem reporta o teste B (Spearman, LIVRE de tolerancia) por celula.
"""
import json
import os
import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
OUT = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(11)
TOLS = [1e-13, 1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-6, 1e-4, 1e-3]

pairs = []      # (alpha_p, alpha_q) sob H1 ; (alpha_p0, alpha_q0) sob H0 ; nulo
for prob in sorted(os.listdir(ROOT)):
    b = os.path.join(ROOT, prob, "42")
    if not os.path.isdir(b):
        continue
    jl = [f for f in os.listdir(b) if f.endswith(".jsonl")][0]
    sg = [f for f in os.listdir(b) if f.endswith("__surrogate.parquet")][0]
    recs = [json.loads(l) for l in open(os.path.join(b, jl))]
    on = pd.read_parquet(os.path.join(b, sg)).query("regime=='online'")
    xc = [c for c in on.columns if c[0] == "x" and c[1:].isdigit()]
    mc = [c for c in on.columns if c.startswith("mu_")]
    sc = [c for c in on.columns if c.startswith("sigma_")]
    for r in recs:
        if r.get("rec") != "decision":
            continue
        a = np.array(r["acqf_todos_restarts"], dtype=float)
        R = len(a)
        blk = on[on.geracao == r["it"]]
        if len(blk) != R:
            continue
        best = int(np.argmax(np.where(np.isfinite(a), a, -np.inf)))
        p1 = [k for k in range(R) if k != best] + [best]
        X = blk[xc].to_numpy(np.float32)
        MS = np.hstack([blk[mc].to_numpy(np.float32), blk[sc].to_numpy(np.float32)])
        key = [X[i].tobytes() + MS[i].tobytes() for i in range(R)]
        dup = [(i, j) for i in range(R) for j in range(i + 1, R) if key[i] == key[j]]
        if not dup:
            continue
        head = p1[:-1].copy()
        RNG.shuffle(head)
        pr = list(head) + [p1[-1]]
        for (i, j) in dup:
            pairs.append((prob,
                          a[p1[i]], a[p1[j]],
                          a[i], a[j],
                          a[pr[i]], a[pr[j]]))

P = pd.DataFrame(pairs, columns=["problema", "h1p", "h1q", "h0p", "h0q",
                                 "nlp", "nlq"])


def rel(p, q):
    den = np.maximum(np.maximum(np.abs(p), np.abs(q)), 1e-300)
    return np.abs(p - q) / den


P["r_h1"] = rel(P.h1p, P.h1q)
P["r_h0"] = rel(P.h0p, P.h0q)
P["r_nl"] = rel(P.nlp, P.nlq)
P.to_csv(os.path.join(OUT, "j27_pares_duplicados.csv"), index=False)
n = len(P)
print(f"pares de linhas bit-identicas (x+mu+sigma) no c154: {n}")
print(f"{'rtol':>8} | {'H1 (perm real)':>16} | {'H0 (ingenua)':>14} | {'nulo':>10}")
for t in TOLS:
    print(f"{t:8.0e} | {(P.r_h1<=t).mean()*100:15.2f}% | "
          f"{(P.r_h0<=t).mean()*100:13.2f}% | {(P.r_nl<=t).mean()*100:9.2f}%")
print("\nquantis do |dalpha| relativo:")
print(P[["r_h1", "r_h0", "r_nl"]].describe(
    percentiles=[.5, .9, .99]).to_string())
print("\npor celula (H1 <= 1e-8):")
print(P.groupby("problema").apply(
    lambda g: pd.Series({"n": len(g),
                         "H1%": (g.r_h1 <= 1e-8).mean() * 100,
                         "H0%": (g.r_h0 <= 1e-8).mean() * 100,
                         "nulo%": (g.r_nl <= 1e-8).mean() * 100}),
    include_groups=False).to_string())
