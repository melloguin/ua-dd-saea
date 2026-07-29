#!/usr/bin/env python
"""F5.4 / e103-A25 - fechamento: (a) o canonico eh o que o codigo de HOJE produz;
(b) censo do _bucket_raw; (c) o teorema da invariancia da razao de fantasia sob
duplicacao exata + a metrica que REALMENTE quebra (spacing).
"""
import glob
import hashlib
import json
import os
import sys
import datetime

import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, "data")
OUT = os.path.dirname(os.path.abspath(__file__))
BRAW = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/_old/_bucket_raw/experiments"
ESP = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103"

from scripts import final_eval as fe  # noqa: E402
from src import problems as _problems  # noqa: E402
from src import metrics as mt  # noqa: E402

print("=" * 96)
print("(a) O ⑦ CANONICO da celula-alvo eh EXATAMENTE o que o final_eval de hoje (com DI-41) produz?")
print("=" * 96)
can = pd.read_parquet(os.path.join(
    DATA, "experiments", "sweep-medium-lhs", "e103",
    "exp_sweep-medium-lhs_e103_ZDT4_42__final.parquet"))
cand = fe.read_final_candidates("sweep-medium-lhs", "e103", "ZDT4", 42, data_root=DATA)
F = fe.evaluate_final("ZDT4", cand["X"])
Xc = can[[f"x{j}" for j in range(10)]].to_numpy(np.float64)
Fc = can[[f"f{j}" for j in range(2)]].to_numpy(np.float64)
print("  n canonico:", len(can), "| n reconstruido:", len(cand["X"]))
print("  max|ΔX| (float32-view):", float(np.abs(Xc - cand["X"].astype(np.float32)).max()))
print("  max|Δf| (float32-view):", float(np.abs(Fc - F.astype(np.float32)).max()))
nd = np.zeros(len(F), bool)
nd[[int(i) for i in _problems._nds_filter(F.astype(np.float32).astype(np.float64))]] = True
print("  nd_pos_real gravado:", int(can.nd_pos_real.sum()), "| recomputado:", int(nd.sum()),
      "| identico:", bool(np.array_equal(can.nd_pos_real.to_numpy(), nd)))
print("  origem_linha 0..N-1 densa:", bool(np.array_equal(
    np.sort(can.origem_linha.to_numpy()), np.arange(len(can)))))
ok, msg = fe.check_final("sweep-medium-lhs", "e103", "ZDT4", 42, data_root=DATA)
print("  check_final(canonico):", "VERDE" if ok else "VERMELHO", "::", msg)

print()
print("=" * 96)
print("(b) censo do _bucket_raw (a fonte do espelho da F5) para o ⑦ do e103")
print("=" * 96)
rows = []
for exp in sorted(os.listdir(BRAW)):
    d = os.path.join(BRAW, exp, "e103")
    if not os.path.isdir(d):
        continue
    for p in sorted(glob.glob(os.path.join(d, "*__final.parquet"))):
        st = os.stat(p)
        pc = os.path.join(DATA, "experiments", exp, "e103", os.path.basename(p))
        rows.append(dict(exp=exp, arq=os.path.basename(p), n=len(pd.read_parquet(p)),
                         nlink=st.st_nlink,
                         mtime=datetime.datetime.fromtimestamp(st.st_mtime).strftime("%H:%M:%S"),
                         mesmo_inode_que_canonico=(os.path.exists(pc) and
                                                   os.stat(pc).st_ino == st.st_ino)))
b = pd.DataFrame(rows)
b.to_csv(os.path.join(OUT, "censo_bucket_raw_camada7.csv"), index=False)
print(f"  ⑦ do e103 no _bucket_raw: {len(b)} | com n != 100: "
      f"{b.loc[b.n != 100, 'arq'].tolist()}")
print(f"  desligadas do inode canonico: {b.loc[~b.mesmo_inode_que_canonico, 'arq'].tolist()}")
print(f"  mtimes distintos: {sorted(b.mtime.unique())[:3]} ... {sorted(b.mtime.unique())[-3:]}")

print()
print("=" * 96)
print("(c) invariancia: duplicar EXATAMENTE o conjunto muda a razao de fantasia?")
print("=" * 96)
esp = pd.read_parquet(glob.glob(os.path.join(ESP, "swap_medium-lhs_ZDT4", "42",
                                             "*__final.parquet"))[0])
Fe = esp[["f0", "f1"]].to_numpy(np.float64)
par, impar = Fe[0::2], Fe[1::2]
print("  ⑦ do espelho: n =", len(Fe), "| linhas pares == impares (bit a bit):",
      bool(np.array_equal(par, impar)))
nd200 = np.zeros(len(Fe), bool)
nd200[[int(i) for i in _problems._nds_filter(Fe)]] = True
nd100 = np.zeros(len(par), bool)
nd100[[int(i) for i in _problems._nds_filter(par)]] = True
print(f"  ND(200) = {nd200.sum()} | ND(100) = {nd100.sum()} | ND(200) == 2*ND(100): "
      f"{nd200.sum() == 2 * nd100.sum()}")
print(f"  fantasia 200 = {nd200.sum()/200:.6f} | fantasia 100 = {nd100.sum()/100:.6f} "
      f"| Δ = {abs(nd200.sum()/200 - nd100.sum()/100):.3e}")
m200, m100 = mt.metrics_of_set(Fe, "ZDT4"), mt.metrics_of_set(par, "ZDT4")
print("  metricas oficiais (200 vs 100):")
for k in ("igd", "igd_plus", "hv", "gd", "spacing"):
    print(f"    {k:9s} {m200[k]:>18.10f}  {m100[k]:>18.10f}   Δ = {abs(m200[k]-m100[k]):.3e}")
