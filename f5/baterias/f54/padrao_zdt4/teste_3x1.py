#!/usr/bin/env python
"""Teste 3x1 global: X da linha da (3) marcada com real_solution_id == X da linha
correspondente da (1). Roda nas 666 celulas. READ-ONLY."""
import os, glob, csv, sys
import numpy as np
import pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/padrao_zdt4/teste_3x1.csv"

rows = []
for cell in sorted(glob.glob(os.path.join(ROOT, "*", "*", "42"))):
    alg, label = cell.split(os.sep)[-3], cell.split(os.sep)[-2]
    sur = glob.glob(os.path.join(cell, "*__surrogate.parquet"))
    rea = glob.glob(os.path.join(cell, "*__real.parquet"))
    r = {"alg": alg, "label": label}
    if not sur or not rea:
        r["veredito"] = "SEM_CAMADA"
        rows.append(r); continue
    try:
        sch = pq.ParquetFile(sur[0]).schema_arrow
        cols = [c for c in sch.names]
        if "real_solution_id" not in cols:
            r["veredito"] = "SEM_real_solution_id"; rows.append(r); continue
        xs = [c for c in cols if c.startswith("x") and c[1:].isdigit()]
        t = pq.read_table(sur[0], columns=["real_solution_id"] + xs).to_pandas()
        sel = t[t.real_solution_id.notna()]
        rt = pq.read_table(rea[0], columns=["solution_id"] + xs).to_pandas()
        rmap = rt.set_index("solution_id")
        sids = sel.real_solution_id.to_numpy()
        Xs = sel[xs].to_numpy(dtype=np.float64)
        idx = rmap.index.to_numpy()
        pos = {v: i for i, v in enumerate(idx)}
        Xr_all = rmap[xs].to_numpy(dtype=np.float64)
        hit = np.array([pos.get(s, -1) for s in sids])
        ok_idx = hit >= 0
        r["n_sel"] = int(len(sel))
        r["n_sem_id"] = int((~ok_idx).sum())
        if ok_idx.sum() == 0:
            r["veredito"] = "IDS_AUSENTES"; rows.append(r); continue
        d = np.abs(Xs[ok_idx] - Xr_all[hit[ok_idx]])
        per = d.max(axis=1)
        r["n_bit_identicos"] = int((per == 0).sum())
        r["n_testados"] = int(ok_idx.sum())
        r["max_dX"] = float(per.max())
        r["frac_ok"] = r["n_bit_identicos"] / r["n_testados"]
        r["veredito"] = "OK" if r["frac_ok"] == 1.0 else "FALHA"
    except Exception as e:
        r["veredito"] = "ERRO"; r["erro"] = str(e)[:200]
    rows.append(r)
    if r.get("veredito") not in ("OK", "SEM_CAMADA", "SEM_real_solution_id"):
        print("!!", alg, label, r, file=sys.stderr)

keys = []
for x in rows:
    for k in x:
        if k not in keys: keys.append(k)
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
import collections
print(collections.Counter(x.get("veredito") for x in rows), file=sys.stderr)
