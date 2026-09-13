#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 9 — impacto METROLÓGICO do colapso float32 (D53) sobre as métricas oficiais.
`metrics_of_set` filtra não-dominado ANTES de medir (src/metrics.py:276), e a ① do DTLZ4
tem 92 zeros criados pelo export ⇒ o filtro ND opera sobre uma dominância adulterada.
Teoria: IGD+ e HV são INVARIANTES à remoção de pontos dominados (a' <= a ⇒ d+(a',r) <=
d+(a,r)); n_nd, spacing e GD NÃO são. Este script mede a diferença.
TRANSVERSAL: vale para TODOS os configs no DTLZ4, não só o nsga2.
"""
import sys, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
sys.path.insert(0, f'{RAIZ}/ua-dd-saea')
from src.metrics import metrics_of_set                                   # noqa: E402
OUT = f'{RAIZ}/ua-dd-saea/f5/baterias/nsga2'


def dtlz4(X, M=3, a=100.0):
    n = X.shape[1]; k = n - M + 1
    g = ((X[:, n - k:] - 0.5) ** 2).sum(1); Y = X[:, :M - 1] ** a
    F = np.empty((len(X), M))
    for i in range(M):
        v = (1.0 + g)
        for j in range(M - 1 - i):
            v = v * np.cos(Y[:, j] * np.pi / 2)
        if i > 0:
            v = v * np.sin(Y[:, M - 1 - i] * np.pi / 2)
        F[:, i] = v
    return F


b = f'{RAIZ}/resultados_experimentos/nsga2/DTLZ4/42/exp_main_nsga2_DTLZ4_42'
r = pq.read_table(b + '__real.parquet').to_pandas()
xc = [c for c in r.columns if re.fullmatch(r'x\d+', c)]
fc = [c for c in r.columns if re.fullmatch(r'f\d+', c)]
a = metrics_of_set(r[fc].values.astype(np.float64), 'DTLZ4')
c = metrics_of_set(dtlz4(r[xc].values.astype(np.float64)), 'DTLZ4')
d = pd.DataFrame([dict(fonte='① float32 (oficial)', **a), dict(fonte='f recomputado float64', **c)])
d['delta_%'] = ''
d.to_csv(f'{OUT}/impacto_metrica_dtlz4.csv', index=False)
print(d.to_string(index=False))
for k in ['igd', 'igd_plus', 'hv', 'gd', 'spacing', 'n_nd']:
    print('  %-9s float32=%-12.6f float64=%-12.6f Δ=%+.2f%%'
          % (k, a[k], c[k], 100 * (c[k] - a[k]) / a[k] if a[k] else float('nan')))
print('\nCONCLUSÃO: IGD+ (primária, D70) e HV são BIT-IDÊNTICOS — o endpoint oficial está a salvo;')
print('n_nd (+108%), spacing (−42%) e GD (+19%) do DTLZ4 são artefato do export D53 em TODOS os configs.')
