#!/usr/bin/env python
"""T11 · smsemoa · BATERIA 3 — a QUERY-JOIA re-medida: monotonicidade do HV
populacional nos 4 pisos, mesmo DoE / mesmo N / mesmos operadores / mesmo ref.

Ref FIXO por problema = nadir da união das 4 ① + 1%. READ-ONLY.
"""
import json, os
import numpy as np, pandas as pd

R = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/smsemoa"
PISOS = ["smsemoa", "nsga2", "nsga3", "moead"]
PROBS = sorted(os.listdir(f"{R}/smsemoa"))


def hv(P, ref, rng):
    P = np.asarray(P, float)
    P = P[np.all(P <= ref, axis=1)]
    if len(P) == 0:
        return 0.0
    keep = np.ones(len(P), bool)
    for i in range(len(P)):
        if not keep[i]:
            continue
        d = np.all(P <= P[i], axis=1) & np.any(P < P[i], axis=1)
        if d.any():
            keep[i] = False
    P = P[keep]
    M = P.shape[1]
    if M == 2:
        o = P[np.argsort(P[:, 0])]
        h, prev = 0.0, ref[1]
        for x, y in o:
            if y < prev:
                h += (ref[0] - x) * (prev - y)
                prev = y
        return h
    lo = np.minimum(P.min(0), ref) - 1e-12
    S = rng.uniform(lo, ref, size=(120000, M))
    dom = np.zeros(len(S), bool)
    for p in P:
        dom |= np.all(S >= p, axis=1)
    return dom.mean() * float(np.prod(ref - lo))


rows, serie = [], {}
for prob in PROBS:
    F_all, dat = [], {}
    for alg in PISOS:
        p = f"{R}/{alg}/{prob}/42/exp_main_{alg}_{prob}_42"
        if not os.path.exists(p + "__real.parquet"):
            continue
        r1 = pd.read_parquet(p + "__real.parquet")
        r2 = pd.read_parquet(p + "__pop.parquet")
        fc = [c for c in r1.columns if c.startswith("f") and c[1:].isdigit()]
        dat[alg] = (r1.set_index("solution_id")[fc], r2)
        F_all.append(r1[fc].values)
    ref = np.vstack(F_all).max(0) * 1.0
    ref = ref + np.abs(ref) * 0.01 + 1e-9
    for alg, (fmap, r2) in dat.items():
        rng = np.random.default_rng(20260731)
        gs = sorted(r2["geracao"].dropna().astype(int).unique())
        hs = []
        for g in gs:
            sid = r2[r2["geracao"] == g]["solution_id"].astype(int).values
            hs.append(hv(fmap.loc[sid].values.astype(np.float64), ref, rng))
        hs = np.array(hs)
        d = np.diff(hs)
        base = np.maximum(np.abs(hs[:-1]), 1e-300)
        rel = d / base
        rows.append(dict(alg=alg, problema=prob, n_ger=len(gs), n_trans=len(d),
                         quedas=int((d < 0).sum()),
                         quedas_1pct=int((rel < -0.01).sum()),
                         pior_rel=float(rel.min()) if len(rel) else np.nan,
                         hv_g1=float(hs[0]), hv_gN=float(hs[-1]),
                         ganho=float(hs[-1] / hs[0] - 1) if hs[0] > 0 else np.nan))
        serie.setdefault(alg, {})[prob] = [float(x) for x in hs]

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/t11_b3_hv.csv", index=False)
json.dump(serie, open(f"{OUT}/t11_b3_serie_hv.json", "w"))

print("=== MONOTONICIDADE DO HV POPULACIONAL (ref fixo por problema, 4 pisos) ===")
g = df.groupby("alg").agg(trans=("n_trans", "sum"), quedas=("quedas", "sum"),
                          q1pct=("quedas_1pct", "sum"), pior=("pior_rel", "min"))
g["pct_quedas"] = (100 * g.quedas / g.trans).round(2)
g["pct_nao_decrescente"] = (100 * (1 - g.quedas / g.trans)).round(2)
print(g.loc[[a for a in PISOS if a in g.index]].to_string())
print()
s = df[df.alg == "smsemoa"]
print("smsemoa: células com queda:", s[s.quedas > 0][["problema", "n_trans", "quedas", "pior_rel"]].to_dict("records"))
print("smsemoa: ganho HV início→fim positivo em", int((s.ganho > 0).sum()), "/", len(s),
      "· mediana", round(float(s.ganho.median()) * 100, 1), "% · máx",
      s.loc[s.ganho.idxmax(), "problema"], round(float(s.ganho.max()) * 100, 1), "%",
      "· mín", s.loc[s.ganho.idxmin(), "problema"], round(float(s.ganho.min()) * 100, 1), "%")
