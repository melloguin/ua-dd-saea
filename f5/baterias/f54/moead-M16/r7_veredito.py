#!/usr/bin/env python
"""
F5.4 / moead-M16 — VEREDITO: bracket float32 CORRIGIDO, 469/469.

Limite SUPERIOR  hi : ND usando so dominancia CERTA (F32[i,m] < F32[j,m] em TODO m).
Limite INFERIOR  lo': ND padrao f32 MENOS o excesso dos grupos de LINHA f32
                      identica com solution_ids DISTINTOS (em float64 um pode
                      dominar o outro -> D57 item 3 / R4#1 do CONTRATO).
Se log(n_front1) in [lo', hi] em 469/469, nao sobra NENHUMA geracao inexplicada.
Roda tambem nos outros 3 pisos (controle transversal).
"""
import json, os
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"


def nd_possivel(F):
    n = len(F); k = np.ones(n, bool)
    for j in range(n):
        m = np.all(F <= F[j], 1) & np.any(F < F[j], 1); m[j] = False
        if m.any(): k[j] = False
    return k


def nd_certo(F):
    n = len(F); k = np.ones(n, bool)
    for j in range(n):
        m = np.all(F < F[j], 1); m[j] = False
        if m.any(): k[j] = False
    return k


linhas = []
for alg, rec in [("moead", "moead_gen"), ("nsga2", "nsga2_gen"),
                 ("nsga3", "nsga3_gen"), ("smsemoa", "smsemoa_gen")]:
    raiz = os.path.join(RES, alg)
    for prob in sorted(os.listdir(raiz)):
        d = os.path.join(raiz, prob, "42"); base = f"exp_main_{alg}_{prob}_42"
        if not os.path.exists(os.path.join(d, base + "__pop.parquet")):
            continue
        pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
        real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
        fc = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()],
                    key=lambda c: int(c[1:]))
        Fmap = {int(s): real.loc[i, fc].to_numpy(np.float64)
                for i, s in zip(real.index, real["solution_id"].to_numpy())}
        for r in [x for x in (json.loads(l) for l in open(os.path.join(d, base + ".jsonl")))
                  if x.get("rec") == rec]:
            g = r["geracao"]
            sids = pop.loc[pop["geracao"] == g, "solution_id"].to_numpy()
            if not len(sids): continue
            F = np.vstack([Fmap[int(s)] for s in sids])
            keep, cert = nd_possivel(F), nd_certo(F)
            lo, hi = int(keep.sum()), int(cert.sum())
            # correcao do limite inferior: grupos de linha f32 identica c/ sids distintos
            grp = {}
            for i, s in enumerate(sids):
                grp.setdefault(tuple(F[i].tolist()), []).append((i, int(s)))
            corte = 0
            for v in grp.values():
                if len({s for _, s in v}) < 2: continue
                nd_slots = [(i, s) for i, s in v if keep[i]]
                if not nd_slots: continue
                cnt = {}
                for _, s in nd_slots: cnt[s] = cnt.get(s, 0) + 1
                corte += sum(cnt.values()) - max(cnt.values())   # pior caso f64
            lo2 = lo - corte
            log = int(r["n_front1"])
            linhas.append(dict(alg=alg, problema=prob, ger=g, log=log,
                               lo_f32=lo, lo_corrigido=lo2, hi=hi,
                               explicado=bool(lo2 <= log <= hi),
                               divergia=(log != lo)))

T = pd.DataFrame(linhas)
T.to_csv(os.path.join(OUT, "r7_veredito.csv"), index=False)
print(T.groupby("alg").agg(geracoes=("log", "size"),
                           divergiam_do_recomputo_f32=("divergia", "sum"),
                           explicadas_por_float32=("explicado", "sum"),
                           INEXPLICADAS=("explicado", lambda s: int((~s).sum()))
                           ).to_string())
print("\nTOTAL:", len(T), "geracoes |", int(T.divergia.sum()),
      "divergencias |", int((~T.explicado).sum()), "INEXPLICADAS")
m = T[T.alg == "moead"]
print("\nMOEAD:", len(m), "geracoes |", int(m.divergia.sum()), "divergencias |",
      int((~m.explicado).sum()), "INEXPLICADAS ->",
      f"{100*m.explicado.mean():.1f}% explicado por float32 (D53/D57/R4#1)")
