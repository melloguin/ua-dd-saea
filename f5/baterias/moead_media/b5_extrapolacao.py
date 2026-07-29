#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 5: extrapolação do μ fora do suporte.
O ⑥ grava `f_best` = melhor μ por objetivo na geração. Compara com o mínimo REAL
do dataset (①) e com o f REAL da população final (⑦): quanto o motor μ-only
"acredita" ter melhorado além do que o dataset comporta?
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import json, os, glob
import numpy as np
import pandas as pd

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/moead_media'


def cols(df, p):
    return sorted([c for c in df.columns if c[0] == p and c[1:].isdigit()], key=lambda c: int(c[1:]))


out = []
for label in sorted(os.listdir(RES)):
    d = '%s/%s/42' % (RES, label)
    mfp = [x for x in glob.glob(d + '/*.manifest.json') if '__final' not in x][0]
    m = json.load(open(mfp)); base = mfp[:-len('.manifest.json')]
    d1 = pd.read_parquet(base + '__real.parquet')
    d7 = pd.read_parquet(base + '__final.parquet')
    FC = cols(d1, 'f')
    fmin_ds = d1[FC].min().values.astype(float)
    fmin_7 = d7[cols(d7, 'f')].min().values.astype(float)
    fb = []
    for ln in open(base + '.jsonl', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get('rec') == 'decision':
            fb.append((r['geracao'], r['f_best']))
    fb.sort()
    g1 = np.array(fb[0][1], float); gN = np.array(fb[-1][1], float)
    for j in range(len(FC)):
        out.append({'label': label, 'problema': m['problema'], 'exp': m['exp'], 'obj': j,
                    'fbest_g1': g1[j], 'fbest_gN': gN[j],
                    'fmin_dataset': fmin_ds[j], 'fmin_real_final': fmin_7[j],
                    'abaixo_do_dataset': bool(gN[j] < fmin_ds[j]),
                    'gap_abs': float(fmin_ds[j] - gN[j]),
                    'gap_rel': float((fmin_ds[j] - gN[j]) / max(abs(fmin_ds[j]), 1e-12)),
                    'mu_negativo': bool(gN[j] < 0), 'f_ds_min_negativo': bool(fmin_ds[j] < 0)})
    print('%-28s ok' % label, flush=True)
D = pd.DataFrame(out)
D.to_csv(OUT + '/extrapolacao_fbest.csv', index=False)
print('\npares=%d · f_best final ABAIXO do mínimo do dataset em %d (%.1f%%)'
      % (len(D), D.abaixo_do_dataset.sum(), 100 * D.abaixo_do_dataset.mean()))
print('gap relativo (mediana) onde extrapola: %.3f' % D.loc[D.abaixo_do_dataset, 'gap_rel'].median())
print(D.nlargest(10, 'gap_rel')[['label', 'obj', 'fbest_gN', 'fmin_dataset', 'fmin_real_final', 'gap_rel']].to_string())
