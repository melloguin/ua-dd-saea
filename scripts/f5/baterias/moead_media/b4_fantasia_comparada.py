#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 4: o erro de fantasia COMPARADO (μ da população
final × f REAL da ⑦), piso μ × b5m/b5r (σ) × e103, nas 45 células pareadas.
A pergunta da ablação: σ na seleção protege contra a extrapolação otimista do GP?
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import json, os, glob
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = REPO + '/f5/baterias/moead_media'
ALGS = ['moead_media', 'b5m', 'b5r', 'e103']
LABELS = sorted(os.listdir(RES + '/moead_media'))


def cols(df, p):
    return sorted([c for c in df.columns if c[0] == p and c[1:].isdigit()], key=lambda c: int(c[1:]))


out = []
for label in LABELS:
    for alg in ALGS:
        d = '%s/%s/%s/42' % (RES, alg, label)
        if not os.path.isdir(d):
            continue
        mfp = [x for x in glob.glob(d + '/*.manifest.json') if '__final' not in x]
        if not mfp:
            continue
        m = json.load(open(mfp[0])); base = mfp[0][:-len('.manifest.json')]
        if not os.path.exists(base + '__final.parquet'):
            continue
        d7 = pd.read_parquet(base + '__final.parquet')
        d3 = pd.read_parquet(base + '__surrogate.parquet')
        MU = sorted([c for c in d3.columns if c.startswith('mu_')], key=lambda s: int(s.split('_')[1]))
        ofl = d3[d3['regime'] == 'offline']
        if not len(ofl) or 'origem_linha' not in d7.columns:
            continue
        gmax = int(ofl['geracao'].dropna().astype(int).max())
        last = ofl[ofl['geracao'] == gmax].reset_index(drop=True)
        try:
            U = last.loc[d7['origem_linha'].values, MU].values.astype(float)
        except Exception:
            continue
        F = d7[cols(d7, 'f')].values.astype(float)
        if U.shape != F.shape:
            continue
        for j in range(F.shape[1]):
            out.append({'label': label, 'alg': alg, 'problema': m['problema'],
                        'exp': m['exp'], 'obj': j,
                        'pct_otimista': float((U[:, j] < F[:, j]).mean()),
                        'vies_med': float(np.median(U[:, j] - F[:, j])),
                        'wape_final': float(np.abs(U[:, j] - F[:, j]).sum() /
                                            max(np.abs(F[:, j]).sum(), 1e-12)),
                        'mu_neg_pct': float((U[:, j] < 0).mean()),
                        'f_neg_pct': float((F[:, j] < 0).mean()),
                        'origem_ger': gmax})
        print('%-28s %-12s ok' % (label, alg), flush=True)
D = pd.DataFrame(out)
D.to_csv(OUT + '/fantasia_comparada.csv', index=False)
print(D.groupby('alg').agg(n=('obj', 'size'), pct_otim_med=('pct_otimista', 'median'),
                           pct_otim_mean=('pct_otimista', 'mean'),
                           wape_fin_med=('wape_final', 'median'),
                           mu_neg=('mu_neg_pct', 'median')).to_string())
