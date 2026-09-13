#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / passo 3 — os PESOS de decomposicao do b5m sao RECUPERAVEIS sem o log?
Reimplemento o simplex-lattice do desdeo (ReferenceVectors._create, creation
'Uniform' + normalizacao esferica) e as vizinhancas (MOEA_D.__init__:
distance_matrix + argsort[:, :20]) SEM importar o desdeo — so de M.
   lattice_res_options = [49, 13, 7, 5, 4, 3, 3, 3, 3]  (BaseEA.py:177)
Depois uso os pesos reconstruidos para reproduzir a A10 do relatorio
(contencao dos grupos de substituicao na vizinhanca de 20).
Saida: a25_pesos.csv
"""
import os, csv, itertools, numpy as np, pyarrow.parquet as pq
from scipy.special import comb
from scipy.spatial import distance_matrix

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A25"
LATT = [49, 13, 7, 5, 4, 3, 3, 3, 3]


def ref_vectors(M):
    """replica EXATA de ReferenceVectors._create('Uniform') + normalize()."""
    H = LATT[M - 2]
    nv = comb(H + M - 1, M - 1, exact=True)
    t1 = np.array(list(itertools.combinations(range(1, M + H), M - 1)))
    t2 = np.array([range(M - 1)] * nv)
    t = t1 - t2 - 1
    w = np.zeros((nv, M), dtype=int)
    w[:, 0] = t[:, 0]
    for i in range(1, M - 1):
        w[:, i] = t[:, i] - t[:, i - 1]
    w[:, -1] = H - t[:, -1]
    v = w / H
    return v / np.linalg.norm(v, axis=1)[:, None], H, nv


def vizinhancas(v, k=20):
    return np.argsort(distance_matrix(v, v), axis=1, kind="quicksort")[:, :k]


rows = []
tot_g = tot_ok = tot_ok2 = 0
for lab in sorted(d for d in os.listdir(ROOT) if not d.startswith(".")):
    d = os.path.join(ROOT, lab, "42")
    if not os.path.isdir(d):
        continue
    f = [x for x in os.listdir(d) if x.endswith("__surrogate.parquet")]
    if not f:
        continue
    t = pq.read_table(os.path.join(d, f[0]))
    cols = t.column_names
    xs = [c for c in cols if c.startswith("x") and c[1:].isdigit()]
    ms = [c for c in cols if c.startswith("mu_")]
    M = len(ms)
    g = np.asarray(t.column("geracao"))
    X = np.column_stack([np.asarray(t.column(c)) for c in xs])
    mask = np.array([gv is not None and gv == gv for gv in g])
    g = np.array([int(v) for v in g[mask]]); X = X[mask]
    gers = np.unique(g)
    pops = {gg: X[g == gg] for gg in gers}
    pop = pops[gers[0]].shape[0]
    V, H, nv = ref_vectors(M)
    biz = vizinhancas(V)
    sets1 = [set(r.tolist()) for r in biz]
    ngr = ok1 = ok2 = 0
    for a, b in zip(gers[:-1], gers[1:]):
        A, B = pops[a], pops[b]
        if A.shape != B.shape:
            continue
        dif = np.any(A != B, axis=1)
        if not dif.any():
            continue
        slots = np.where(dif)[0]
        novos = B[dif]
        uq, inv = np.unique(novos, axis=0, return_inverse=True)
        for j in range(len(uq)):
            grp = set(slots[inv == j].tolist())
            ngr += 1
            if any(grp <= s for s in sets1):
                ok1 += 1
            else:                       # 2-3 vizinhancas (aliasing float32)
                un = False
                for i1 in range(len(sets1)):
                    if not (grp & sets1[i1]):
                        continue
                    for i2 in range(len(sets1)):
                        if grp <= (sets1[i1] | sets1[i2]):
                            un = True; break
                    if un: break
                ok2 += un
    rows.append(dict(celula=lab, M=M, pop=pop, H_lattice=H, n_vetores=nv,
                     pop_bate_lattice=(pop == nv), grupos=ngr,
                     contidos_1viz=ok1,
                     frac_1viz=round(ok1 / ngr, 6) if ngr else None,
                     contidos_ate2viz=ok1 + ok2))
    tot_g += ngr; tot_ok += ok1; tot_ok2 += ok1 + ok2
    print("%-24s M=%d pop=%3d H=%2d nv=%3d bate=%s grupos=%6d 1viz=%.6f"
          % (lab, M, pop, H, nv, pop == nv, ngr, (ok1 / ngr) if ngr else float("nan")))

with open(os.path.join(OUT, "a25_pesos.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
    [w.writerow(r) for r in rows]
print("\nTOTAL grupos=%d  contidos em 1 vizinhanca=%d (%.6f)  ate 2 vizinhancas=%d (%.6f)"
      % (tot_g, tot_ok, tot_ok / tot_g, tot_ok2, tot_ok2 / tot_g))
print("celulas com pop == n_vetores_reconstruidos: %d/%d"
      % (sum(r["pop_bate_lattice"] for r in rows), len(rows)))
print("OK ->", os.path.join(OUT, "a25_pesos.csv"))
