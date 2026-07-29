#!/usr/bin/env python
"""F5.4 / b5m-A8 — IMPACTO: a ablacao D77 (A14/J1) sobrevive sem as celulas
contaminadas pelo congelamento mecanico (b5m E piso)?  Saida: A8_05_impacto_ablacao.txt
"""
import pandas as pd, numpy as np
from scipy.stats import wilcoxon

d = pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b5m/b5m_endpoint7.csv')
f = pd.read_csv('A8_slots_face.csv')
mec = f[(f.amp_zero_em_alguma_ger > 0) & (f.congeladas_trans > 0)]
par = f[(f.n_mortos > 0) & (f.n_mortos < f['pop'])]
afet = sorted(set(mec.label) | set(par.label))
print('celulas MECANICAS por config:'); print(mec[['alg', 'label', 'congeladas_trans']].to_string())
print('\nceluas com slots mortos (parcial):'); print(par[['alg', 'label', 'n_mortos']].to_string())
print('\nUNIAO de celulas contaminadas:', len(afet)); print(afet)

p = d.pivot_table(index='label', columns='alg', values='sigma_nn_med')[['b5m', 'moead_media']].dropna()


def teste(x, tag):
    a, b = x.b5m.values, x.moead_media.values
    m = a != b
    st, pv = wilcoxon(a[m], b[m])
    print('%-28s n=%2d  b5m<piso em %2d/%2d  razao mediana=%.3f  Wilcoxon p=%.4f'
          % (tag, len(x), int((a < b).sum()), len(x), np.median(a / b), pv))


teste(p, 'TODAS as 45 (analista)')
teste(p.drop(index=[l for l in afet if l in p.index]), 'excluindo contaminadas')
q = d.pivot_table(index='label', columns='alg', values='igd_plus')[['b5m', 'moead_media']].dropna()


def teste2(x, tag):
    a, b = x.b5m.values, x.moead_media.values
    st, pv = wilcoxon(a, b)
    print('%-28s n=%2d  b5m melhor em %2d/%2d  mediana b5m=%.4f piso=%.4f  p=%.4f'
          % (tag, len(x), int((a < b).sum()), len(x), np.median(a), np.median(b), pv))


teste2(q, 'IGD+ TODAS as 45')
teste2(q.drop(index=[l for l in afet if l in q.index]), 'IGD+ excluindo contaminadas')
