#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 5 — desempenho do smoke (IGD+ oficial D70) e faixa-guia entre os
configs que rodaram a MESMA célula MMF1/42 (mesmo DoE, mesmo orçamento 61 FEs).
⚠ 1 semente × 61 FEs: FAIXA-GUIA, nunca veredito de qualidade."""
import os, sys, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
import src.metrics as MT

D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main'
OUT  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c217'

ideal, nadir = MT.reference_bounds('MMF1')
R = MT.reference_set('MMF1', 5000)
print('ref set MMF1:', R.shape, 'ideal/nadir:', ideal, nadir)

res = []
for p in sorted(glob.glob(os.path.join(D_EV, '*/exp_main_*_MMF1_42__real.parquet'))):
    alg = os.path.basename(p).split('_')[2]
    df = pq.read_table(p).to_pandas()
    F = df[[c for c in df.columns if c[0]=='f' and c[1:].isdigit()]].values.astype('float64')
    A = MT.nondominated_front(MT.normalize(F, ideal, nadir))
    res.append(dict(alg=alg, n_FE=len(df), n_ND=len(A),
                    igd_plus=MT.igd_plus(A, R), igd=MT.igd(A, R),
                    hv=MT.hv(A), spacing=MT.spacing(A)))
d = pd.DataFrame(res).sort_values('igd_plus').reset_index(drop=True)
d['rank'] = d.index + 1
print()
print(d.to_string(index=False))
c = d[d.alg == 'c217']
print('\nc217: IGD+ = %.5f  (rank %d/%d)  · razao vs melhor = %.3fx' % (
      c.igd_plus.iloc[0], int(c['rank'].iloc[0]), len(d), c.igd_plus.iloc[0]/d.igd_plus.min()))

# trajetória do c217 (IGD+ x FE)
p = os.path.join(D_EV, 'c217/exp_main_c217_MMF1_42__real.parquet')
df = pq.read_table(p).to_pandas().sort_values('fe_index')
F = df[[c_ for c_ in df.columns if c_[0]=='f' and c_[1:].isdigit()]].values.astype('float64')
tr = []
for k in range(21, len(F)+1, 4):
    A = MT.nondominated_front(MT.normalize(F[:k], ideal, nadir))
    tr.append((k, MT.igd_plus(A, R)))
tr = pd.DataFrame(tr, columns=['FE', 'igd_plus'])
mono = int((np.diff(tr.igd_plus.values) <= 1e-12).sum())
print('\ntrajetoria c217: %d checkpoints · monotonica nao-crescente %d/%d · %.4f -> %.4f (%.3fx)' % (
      len(tr), mono, len(tr)-1, tr.igd_plus.iloc[0], tr.igd_plus.iloc[-1],
      tr.igd_plus.iloc[-1]/tr.igd_plus.iloc[0]))
d.to_csv(os.path.join(OUT, 'c217_t11_desempenho_mmf1.csv'), index=False)
tr.to_csv(os.path.join(OUT, 'c217_t11_trajetoria.csv'), index=False)
