#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 11: o BRACKET da identidade EIM sob quantizacao float32.
EIMe(x) = min_j ||EI^j(x)||_2 -> acrescentar pontos a frente so pode DIMINUIR o valor.
Logo, para qualquer frente admissivel entre a mais ENXUTA (weak-seq, duplicatas colapsadas)
e a mais LARGA (strict, so dominancia estrita remove), vale
        max_pool EIM(strict) <= EIM_verdadeiro <= max_pool EIM(weak).
Se `eim_best` do (6) cai nesse intervalo, a diferenca observada e explicada INTEIRAMENTE
pela perda de informacao do export float32 (D53) — nao por desvio de mecanismo.
Alem disso: censo do colapso float32 no ZDT6 (f1 = 1 - exp(-4x)sin^6(6 pi x) -> 1.0 exato)
e no DTLZ4 (alpha=100 -> sin(x^100 pi/2) -> subnormal/0).
Saidas: bracket_f32.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)
BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
ALVO = ["DTLZ4", "MMF11_L", "ZDT6"]


def nd_strict_mask(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y < Y[i]).all(1)).any():
            keep[i] = False
    return keep


rows = []
for prob in ALVO:
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    M = [r for r in recs if r.get("rec") == "header"][0]["M"]
    G = [r for r in recs if r.get("rec") == "c238_gen"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F32 = real[[f"f{i}" for i in range(M)]].values
    F = F32.astype(np.float64)
    cols = ["regime", "geracao"] + [f"mu_{i}" for i in range(M)] + [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))
    # censo de colapso
    uniq = len(pd.DataFrame(F).drop_duplicates())
    val, cts = np.unique(F32[:, 0], return_counts=True)
    top_tie = int(cts.max())
    n_sub = int((np.abs(F) < np.finfo(np.float32).tiny).sum() - (F == 0).sum())
    for r in G:
        Y = F[:r["n_amostra"]]
        wk = b2.nd_weak_seq(Y); sr = nd_strict_mask(Y)
        mn = np.array(r["norm_min"]); rg = np.array(r["norm_range_efetivo"])
        sub = grp[r["geracao"]]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        hi = float(b2.eim_euclidean(u, s, (Y[wk] - mn) / rg).max())
        lo = float(b2.eim_euclidean(u, s, (Y[sr] - mn) / rg).max())
        eb = r["eim_best"]
        rows.append(dict(problema=prob, geracao=r["geracao"], n_front_log=r["n_front"],
                         weak=int(wk.sum()), strict=int(sr.sum()), eim_best=eb,
                         eim_lo=lo, eim_hi=hi, dentro=bool(lo - 1e-12 <= eb <= hi + 1e-12),
                         larg_rel=(hi - lo) / max(abs(eb), 1e-300),
                         rel_hi=abs(hi - eb) / max(abs(eb), 1e-300),
                         uniq=uniq, top_tie=top_tie, n_sub=n_sub, n_lin=len(F)))
    print("OK", prob, f"linhas={len(F)} unicas={uniq} maior_empate_f0={top_tie} subnormais={n_sub}",
          flush=True)

A = pd.DataFrame(rows); A.to_csv(f"{OUT}/bracket_f32.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
g = A.groupby("problema")
print(pd.DataFrame(dict(n=g.size(), dentro=g.dentro.sum(),
                        larg_med=g.larg_rel.median(), larg_max=g.larg_rel.max(),
                        rel_hi_med=g.rel_hi.median(), rel_hi_max=g.rel_hi.max(),
                        uniq=g.uniq.first(), n_lin=g.n_lin.first(),
                        top_tie=g.top_tie.first(), n_sub=g.n_sub.first())).to_string())
