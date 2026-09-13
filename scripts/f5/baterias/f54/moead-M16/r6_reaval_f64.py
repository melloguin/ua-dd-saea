#!/usr/bin/env python
"""
F5.4 / moead-M16 — a prova de que o "resgate em float64" do analista era IMPOSSIVEL
nestas 16 geracoes, e por que funcionou nas 14 do DTLZ4.

ZDT1: `f1 = X[:,0]` (src/problems.py:308) — o 1o objetivo E a 1a variavel.
ZDT3 idem; DTLZ7: f_i = x_i para i<M. Como a ① grava X em float32 (D53), duas
solucoes float64-distintas cujo x0 colide em float32 tem f0 IDENTICO em qualquer
reavaliacao feita a partir da ① — a informacao ja foi destruida no X.
No DTLZ4 a perda e no F (underflow denormal) e F e funcao NAO-LINEAR de X, logo
reavaliar RESTAURA a resolucao. Dai a bifurcacao 14 x 16 do analista.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
import src.problems as P

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"

CASOS = [("ZDT1", g) for g in (5, 6, 7, 8, 9, 10, 34)] + \
        [("ZDT3", 34), ("ZDT6", 3), ("MMF11_L", 3), ("DTLZ3", 18)] + \
        [("DTLZ7", g) for g in (9, 16, 17, 18, 19, 27, 30)] + \
        [("DTLZ4", g) for g in (1, 2, 3, 16, 17)]


def nd(F):
    n = len(F); keep = np.ones(n, bool)
    for j in range(n):
        m = np.all(F <= F[j], 1) & np.any(F < F[j], 1); m[j] = False
        if m.any(): keep[j] = False
    return int(keep.sum())


def build(prob, D, M):
    for name in dir(P):
        o = getattr(P, name)
        if isinstance(o, type) and name.upper() == prob.upper().replace("_L", "_L"):
            pass
    # roteador simples pelo nome exato da classe
    mapa = {"MMF11_L": "MMF11_L"}
    cls = getattr(P, mapa.get(prob, prob), None)
    if cls is None:
        return None
    try:
        return cls(n_var=D)
    except TypeError:
        try:
            return cls(n_var=D, n_obj=M)
        except TypeError:
            return cls()


rows = []
for prob, ger in CASOS:
    d = os.path.join(RES, prob, "42"); base = f"exp_main_moead_{prob}_42"
    pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
    real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    xc = sorted([c for c in real.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    r = real.set_index("solution_id")
    recs = [json.loads(l) for l in open(os.path.join(d, base + ".jsonl"))]
    rec = [x for x in recs if x.get("rec") == "moead_gen" and x["geracao"] == ger][0]
    sids = pop.loc[pop["geracao"] == ger, "solution_id"].to_numpy()
    F32 = np.vstack([r.loc[int(s), fc].to_numpy(np.float64) for s in sids])
    X32 = np.vstack([r.loc[int(s), xc].to_numpy(np.float64) for s in sids])
    pr = build(prob, len(xc), len(fc))
    if pr is None:
        print(f"{prob}: classe nao encontrada"); continue
    out = {}
    pr._evaluate(X32, out)
    F64 = np.asarray(out["F"], np.float64)
    rows.append(dict(problema=prob, ger=ger, log=int(rec["n_front1"]),
                     nd_f32_da_camada1=nd(F32),
                     nd_f64_reaval_de_X_f32=nd(F64),
                     resgatou=(nd(F64) == int(rec["n_front1"])),
                     max_dif_F=float(np.abs(F64 - F32).max())))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "r6_reaval_f64.csv"), index=False)
print(df.to_string(index=False))
print("\nresgatados pelo float64:", int(df.resgatou.sum()), "/", len(df))
