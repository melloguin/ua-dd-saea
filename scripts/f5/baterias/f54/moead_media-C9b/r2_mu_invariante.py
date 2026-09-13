#!/usr/bin/env python3
# r2_mu_invariante.py — F5.4 / ataque adversarial a moead_media-C9b.
# Passo 2 do roteiro: o criterio "WAPE = 1,000 +- 1e-4" so enxerga o colapso
# para mu == 0. Um GP que degenera para uma CONSTANTE != 0 (comprimento de
# escala no bound SUPERIOR) passa invisivel. Reconto com criterio invariante a
# deslocamento/escala, direto na ③ (mu bruto da sonda), sem passar pelo CSV.
# READ-ONLY. Saida: r2_mu_invariante.csv + r2_mu_invariante.json
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = os.path.dirname(os.path.abspath(__file__))
CFGS = ['moead_media', 'b5m', 'b5r']
PROBS_OFF = ['BBOB_F1', 'BBOB_F17', 'BBOB_F22', 'BBOB_F37', 'BBOB_F49', 'BBOB_F5',
             'BBOB_F55', 'DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7', 'MMF1',
             'MMF11_L', 'MMF16_20', 'MMF4', 'WFG1', 'WFG2', 'WFG4', 'WFG5',
             'WFG9', 'ZDT1', 'ZDT3', 'ZDT4', 'ZDT6']
SWEEP = ['swap_small-lhs', 'swap_small-mvns', 'swap_medium-lhs', 'swap_medium-mvns']
PS = ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4']
CELLS = [(p, p) for p in PROBS_OFF] + [('%s_%s' % (s, p), p) for s in SWEEP for p in PS]

rows = []
gab = {}
for lab, prob in CELLS:
    if prob not in gab:
        g = pq.read_table('%s/sonda_%s.parquet' % (SND, prob)).to_pandas()
        fc = sorted([c for c in g.columns if c[0] == 'f' and c[1:].isdigit()],
                    key=lambda c: int(c[1:]))
        gab[prob] = g[fc].to_numpy(float)
    Fg = gab[prob]
    M = Fg.shape[1]
    for cfg in CFGS:
        d = '%s/%s/%s/42' % (RES, cfg, lab)
        f = [x for x in os.listdir(d) if x.endswith('__surrogate.parquet')][0]
        t = pq.read_table(os.path.join(d, f),
                          columns=['geracao'] + ['mu_%d' % j for j in range(M)],
                          filters=[('regime', '=', 'sonda')]).to_pandas()
        assert len(t) == 20000, (lab, cfg, len(t))
        for j in range(M):
            mu = t['mu_%d' % j].to_numpy(float)
            fv = Fg[:20000, j]
            ok = np.isfinite(mu)
            mu, fv = mu[ok], fv[ok]
            sdm, sdf = float(np.std(mu)), float(np.std(fv))
            wape = float(np.abs(mu - fv).sum() / max(np.abs(fv).sum(), 1e-12))
            corr = float(np.corrcoef(mu, fv)[0, 1]) if sdm > 0 else np.nan
            rows.append({
                'cel': lab, 'prob': prob, 'cfg': cfg, 'obj': j,
                'wape': wape, 'corr': corr,
                'mu_mean': float(mu.mean()), 'mu_std': sdm,
                'mu_min': float(mu.min()), 'mu_max': float(mu.max()),
                'f_mean': float(fv.mean()), 'f_std': sdf,
                'sd_rel': sdm / max(sdf, 1e-300),
                'mu_amp_rel': (float(mu.max() - mu.min()) /
                               max(float(fv.max() - fv.min()), 1e-300)),
                'mu_mean_rel': abs(float(mu.mean())) / max(abs(float(fv.mean())), 1e-300),
            })

df = pd.DataFrame(rows)
df['col_wape1'] = (df.wape - 1.0).abs() <= 1e-4                    # criterio do relatorio
df['col_inerte'] = df.sd_rel <= 1e-3                               # invariante shift+escala
df['col_inerte_frouxo'] = df.sd_rel <= 1e-2
df['col_const_naozero'] = df.col_inerte & (df.mu_mean_rel > 1e-3)  # degenera p/ constante != 0
df.to_csv(OUT + '/r2_mu_invariante.csv', index=False)

res = {'n_pares': int(len(df) / 3)}
for k in ['col_wape1', 'col_inerte', 'col_inerte_frouxo', 'col_const_naozero']:
    res[k] = {c: int(s[k].sum()) for c, s in df.groupby('cfg')}
res['discordancia_wape1_x_inerte'] = {
    c: {'so_wape1': int((s.col_wape1 & ~s.col_inerte).sum()),
        'so_inerte': int((~s.col_wape1 & s.col_inerte).sum()),
        'ambos': int((s.col_wape1 & s.col_inerte).sum())}
    for c, s in df.groupby('cfg')}
# mu identicamente zero?
df['mu_zero'] = (df.mu_max.abs() <= 1e-12) & (df.mu_min.abs() <= 1e-12)
res['mu_identicamente_zero'] = {c: int(s.mu_zero.sum()) for c, s in df.groupby('cfg')}
# controle: no colapso, mu == 0 (media a priori) nos 3 configs?
res['nos_colapsados_mu_mean_rel_mediana'] = {
    c: round(float(s.loc[s.col_wape1, 'mu_mean_rel'].median()), 8)
    for c, s in df.groupby('cfg')}
with open(OUT + '/r2_mu_invariante.json', 'w') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
