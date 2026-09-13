#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 3:
 (a) trajetórias 20-checkpoints: violações de monotonicidade do IGD+;
 (b) DETERMINISMO POR RE-RUN: off/{p} × swap_small-lhs/{p} usam o MESMO dataset
     (ds_{p}_42.parquet = tier small, dist lhs) => são DOIS RUNS INDEPENDENTES do
     mesmo (alg, problema, semente, dataset). Bit-identidade prova o RNG (D62/DI-28.3).
 (c) erro de fantasia detalhado (μ da ③ última geração × f real da ⑦).
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import json, os, glob
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media'
TRJ = REPO + '/f5/trajetorias'
OUT = REPO + '/f5/baterias/moead_media'


def cols(df, p):
    return sorted([c for c in df.columns if c[0] == p and c[1:].isdigit()], key=lambda c: int(c[1:]))


# ── (a) trajetórias ────────────────────────────────────────────────────
tr = []
for f in sorted(glob.glob(TRJ + '/*_moead_media_*_42.json')):
    d = json.load(open(f))
    ig = [c['igd_plus'] for c in d]
    viol = sum(1 for a, b in zip(ig, ig[1:]) if b > a + 1e-12)
    tr.append({'arquivo': os.path.basename(f), 'n_ckpt': len(d), 'igd_ini': ig[0],
               'igd_fim': ig[-1], 'viol': viol, 'transicoes': len(ig) - 1,
               'fe_ini': d[0]['fe'], 'fe_fim': d[-1]['fe'],
               'nnd_fim': d[-1]['n_nd']})
T = pd.DataFrame(tr)
T.to_csv(OUT + '/trajetorias_moead_media.csv', index=False)
print('TRAJETÓRIAS: %d arquivos · %d transições · violações=%d · checkpoints únicos=%s'
      % (len(T), T.transicoes.sum(), T.viol.sum(), sorted(T.n_ckpt.unique())))

# ── (b) determinismo por re-run ────────────────────────────────────────
det = []
for p in ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4']:
    a = glob.glob('%s/%s/42/*' % (RES, p))
    b = glob.glob('%s/swap_small-lhs_%s/42/*' % (RES, p))
    row = {'problema': p}
    for suf in ['__real', '__surrogate', '__final', '__timing']:
        fa = [x for x in a if x.endswith(suf + '.parquet')][0]
        fb = [x for x in b if x.endswith(suf + '.parquet')][0]
        da, db = pd.read_parquet(fa), pd.read_parquet(fb)
        num = [c for c in da.columns if da[c].dtype.kind in 'fiub']
        same = da.shape == db.shape and all(
            np.array_equal(da[c].values, db[c].values) or
            (np.isnan(da[c].values.astype(float)).all() and np.isnan(db[c].values.astype(float)).all())
            for c in num)
        # comparação NaN-safe coluna a coluna
        dmax = 0.0
        for c in num:
            va = da[c].values.astype(float); vb = db[c].values.astype(float)
            mk = ~(np.isnan(va) | np.isnan(vb))
            if mk.any():
                dmax = max(dmax, float(np.abs(va[mk] - vb[mk]).max()))
        row[suf + '_shape'] = (da.shape == db.shape)
        row[suf + '_dmax'] = dmax
        row[suf + '_bit'] = bool(same)
    ma = json.load(open([x for x in a if x.endswith('.manifest.json') and '__final' not in x][0]))
    mb = json.load(open([x for x in b if x.endswith('.manifest.json') and '__final' not in x][0]))
    row['nger_igual'] = (ma['n_geracoes'] == mb['n_geracoes'])
    row['hash_igual'] = (ma['doe_hash'] == mb['doe_hash'])
    row['sigma_dict_igual'] = (ma['sigma_dict'] == mb['sigma_dict'])
    row['wall_off'] = ma['timing']['tempo_total_s']; row['wall_sweep'] = mb['timing']['tempo_total_s']
    det.append(row)
    print('DETERMINISMO %-10s bit=%s/%s/%s/%s' % (
        p, row['__real_bit'], row['__surrogate_bit'], row['__final_bit'], row['__timing_bit']))
pd.DataFrame(det).to_csv(OUT + '/determinismo_rerun.csv', index=False)

# ── (c) erro de fantasia detalhado ─────────────────────────────────────
fant = []
for label in sorted(os.listdir(RES)):
    d = '%s/%s/42' % (RES, label)
    mfp = [x for x in glob.glob(d + '/*.manifest.json') if '__final' not in x][0]
    m = json.load(open(mfp)); base = mfp[:-len('.manifest.json')]
    d3 = pd.read_parquet(base + '__surrogate.parquet')
    d7 = pd.read_parquet(base + '__final.parquet')
    last = d3[(d3['regime'] == 'offline') & (d3['geracao'] == m['n_geracoes'])].reset_index(drop=True)
    MU = sorted([c for c in d3.columns if c.startswith('mu_')], key=lambda s: int(s.split('_')[1]))
    F = d7[cols(d7, 'f')].values.astype(float)
    U = last.loc[d7['origem_linha'].values, MU].values.astype(float)
    for j in range(F.shape[1]):
        fant.append({'label': label, 'problema': m['problema'], 'exp': m['exp'], 'obj': j,
                     'mu_med': float(np.median(U[:, j])), 'f_med': float(np.median(F[:, j])),
                     'vies_med': float(np.median(U[:, j] - F[:, j])),
                     'abs_med': float(np.median(np.abs(U[:, j] - F[:, j]))),
                     'wape_final': float(np.abs(U[:, j] - F[:, j]).sum() / max(np.abs(F[:, j]).sum(), 1e-12)),
                     'pct_otimista': float((U[:, j] < F[:, j]).mean()),
                     'mu_colapso0': bool(np.all(U[:, j] == 0.0))})
pd.DataFrame(fant).to_csv(OUT + '/fantasia_final.csv', index=False)
print('FANTASIA: %d pares célula×objetivo' % len(fant))
