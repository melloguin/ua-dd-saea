#!/usr/bin/env python
"""
F5.4 / moead-M16 — fecha o lado NEGATIVO do bracket (log = recomputo - 1).

O limite inferior `lo` do r2 (ND padrao sobre a ① float32) so e valido se NAO
existirem dois `solution_id` DISTINTOS com a LINHA de objetivos bit-identica em
float32. Quando existem, em float64 um deles pode dominar o outro -> o MATLAB
conta 1 a MENOS. Este script procura exatamente esses grupos nas 5 geracoes
moead com delta = -1 (e nas 4 dos outros pisos, como controle).
"""
import json, os
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"

CASOS = [("moead", "DTLZ3", 18), ("moead", "DTLZ7", 30), ("moead", "MMF11_L", 3),
         ("moead", "ZDT1", 34), ("moead", "ZDT3", 34),
         ("nsga2", "MMF4", 2), ("nsga3", "MMF16_20", 2), ("nsga3", "MMF4", 2),
         ("smsemoa", "MMF11_L", 3)]


def nd_possivel(F):
    n = len(F); keep = np.ones(n, bool)
    for j in range(n):
        m = np.all(F <= F[j], axis=1) & np.any(F < F[j], axis=1); m[j] = False
        if m.any(): keep[j] = False
    return keep


out = []
for alg, prob, ger in CASOS:
    d = os.path.join(RES, alg, prob, "42")
    base = f"exp_main_{alg}_{prob}_42"
    pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
    real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    Fmap = {int(s): real.loc[i, fc].to_numpy(np.float64)
            for i, s in zip(real.index, real["solution_id"].to_numpy())}
    recs = [json.loads(l) for l in open(os.path.join(d, base + ".jsonl"))]
    r = [x for x in recs if x.get("rec", "").endswith("_gen") and x.get("geracao") == ger][0]
    sids = pop.loc[pop["geracao"] == ger, "solution_id"].to_numpy()
    F = np.vstack([Fmap[int(s)] for s in sids])
    nd = nd_possivel(F)
    # grupos de LINHA f32 identica com sids DIFERENTES
    grupos = {}
    for i, (s, f) in enumerate(zip(sids, F)):
        grupos.setdefault(tuple(f.tolist()), []).append((i, int(s)))
    colis = []
    for k, v in grupos.items():
        sset = {s for _, s in v}
        if len(sset) > 1:
            nd_no_grupo = sum(1 for i, _ in v if nd[i])
            colis.append(dict(objs=k, sids=sorted(sset), n_slots=len(v),
                              n_nd=nd_no_grupo))
    out.append(dict(alg=alg, problema=prob, ger=ger, log=int(r["n_front1"]),
                    lo=int(nd.sum()),
                    n_colisoes_linha_inteira=len(colis),
                    excesso_nd=sum(c["n_nd"] - 1 for c in colis if c["n_nd"] >= 1),
                    detalhe=colis))
    print(f"--- {alg} {prob} g{ger}: log={int(r['n_front1'])} lo={int(nd.sum())} "
          f"colisoes_f32_linha_inteira={len(colis)}")
    for c in colis:
        print(f"      sids {c['sids']} slots={c['n_slots']} nd_no_grupo={c['n_nd']} "
              f"objs={c['objs']}")

pd.DataFrame([{k: v for k, v in o.items() if k != "detalhe"} for o in out]).to_csv(
    os.path.join(OUT, "r3_delta_negativo.csv"), index=False)
