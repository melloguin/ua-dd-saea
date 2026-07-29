#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_pisos7.py — F5.3b/e103 · POSICAO vs os demais offline pela camada ⑦
(o endpoint real do regime offline, DI-08), ja que as metricas da ① EMPATAM por
desenho (D69).  Usa src/metrics.py (oficial) com gate D92.  READ-ONLY.
Saida: f5/baterias/e103/pisos_via7_e103.csv
"""
import os, sys, json, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics  # noqa: E402

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)

ALGS = ['e103', 'c311', 'b5r', 'b5m', 'moead_media', 'treed_media']
rows = []
probs = sorted(os.listdir(os.path.join(RES, 'e103')))
probs = [p for p in probs if not p.startswith('swap_')]
for prob in probs:
    R = metrics.reference_set(prob)
    for alg in ALGS:
        d = os.path.join(RES, alg, prob, '42')
        if not os.path.isdir(d):
            continue
        ff = glob.glob(os.path.join(d, '*__final.parquet'))
        if not ff:
            rows.append(dict(problema=prob, alg=alg, erro='sem ⑦'))
            continue
        fin = pq.read_table(ff[0]).to_pandas()
        fc = [c for c in fin.columns if c.startswith('f') and c[1:].isdigit()]
        fc = sorted(fc, key=lambda s: int(s[1:]))
        m_all = metrics.metrics_of_set(fin[fc].values, prob, ref_norm=R)
        nd = fin['nd_pos_real'].values if 'nd_pos_real' in fin.columns else np.ones(len(fin), bool)
        m_nd = metrics.metrics_of_set(fin[fc].values[nd], prob, ref_norm=R)
        rows.append(dict(problema=prob, alg=alg, n_final=len(fin), n_nd=int(nd.sum()),
                         fantasia=float(nd.mean()),
                         igd_plus_7=m_all['igd_plus'], hv_7=m_all['hv'],
                         igd_plus_7_nd=m_nd['igd_plus'], hv_7_nd=m_nd['hv']))
    print('ok', prob, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'pisos_via7_e103.csv'), index=False)
piv = df.pivot_table(index='problema', columns='alg', values='igd_plus_7')
piv = piv[[a for a in ALGS if a in piv.columns]]
piv['rank_e103'] = piv.rank(axis=1).e103
print('\n--- IGD+ da ⑦ (todos os finais avaliados no real) por alg offline ---')
print(piv.round(5).to_string())
print('\nrank medio e103: %.2f de %d algs; vence em %d/%d problemas'
      % (piv.rank_e103.mean(), piv.shape[1] - 1,
         int((piv.rank_e103 == 1).sum()), len(piv)))
