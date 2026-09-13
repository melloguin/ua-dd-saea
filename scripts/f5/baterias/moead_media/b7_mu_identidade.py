#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 7: identidade do μ da sonda entre o piso e o par
de ablação (b5m/b5r) nos MESMOS 20.000 pontos Sobol. DI-28 diz 'mesma ESPECIFICAÇÃO,
treino INDEPENDENTE' — este script mede quanto do μ é, de fato, idêntico.
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import os, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/moead_media'
LABELS = sorted(os.listdir(RES + '/moead_media'))
rows = []
for label in LABELS:
    st = {}
    for alg in ['moead_media', 'b5m', 'b5r']:
        g = glob.glob('%s/%s/%s/42/*__surrogate.parquet' % (RES, alg, label))
        if not g:
            continue
        nm = pq.ParquetFile(g[0]).schema.names
        mu = sorted([c for c in nm if c.startswith('mu_')], key=lambda s: int(s.split('_')[1]))
        t = pq.read_table(g[0], columns=['regime'] + mu).to_pandas()
        st[alg] = t[t['regime'] == 'sonda'][mu].values.astype(np.float64)[:20000]
    P = st.get('moead_media')
    if P is None:
        continue
    for alg in ['b5m', 'b5r']:
        Q = st.get(alg)
        if Q is None or Q.shape != P.shape:
            continue
        for j in range(P.shape[1]):
            a, b = P[:, j], Q[:, j]
            esc = max(abs(b).max(), 1e-30)
            rows.append({'label': label, 'vs': alg, 'obj': j,
                         'identico_bit': bool(np.array_equal(a, b)),
                         'dmax': float(np.abs(a - b).max()),
                         'dmax_rel': float(np.abs(a - b).max() / esc),
                         'piso_colapso': bool(np.abs(a).max() < 1e-6 * esc),
                         'outro_colapso': bool(np.abs(b).max() < 1e-6 * max(abs(a).max(), 1e-30))})
    print(label, flush=True)
D = pd.DataFrame(rows)
D.to_csv(OUT + '/mu_identidade_piso_vs_b5.csv', index=False)
for v in ['b5m', 'b5r']:
    s = D[D.vs == v]
    print('%s: pares=%d · μ BIT-IDÊNTICO em %d (%.1f%%) · dmax_rel mediano=%.3e · '
          'só o piso colapsa em %d · só o outro colapsa em %d'
          % (v, len(s), s.identico_bit.sum(), 100 * s.identico_bit.mean(),
             s.dmax_rel.median(), int((s.piso_colapso & ~s.outro_colapso).sum()),
             int((~s.piso_colapso & s.outro_colapso).sum())))
    ni = s[~s.identico_bit]
    print('   nos %d NÃO idênticos: dmax_rel mediana=%.3e ; com colapso de um dos lados=%d'
          % (len(ni), ni.dmax_rel.median(), int((ni.piso_colapso | ni.outro_colapso).sum())))
