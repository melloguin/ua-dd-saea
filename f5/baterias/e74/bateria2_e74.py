#!/usr/bin/env python
"""BATERIA 2 e74/CLMEA — QUERY-JOIA: identidade da selecao de infill nas 3 estrategias.
Para cada bloco de estrategia: acha o infill aceito (①, fe_index=fe-1) DENTRO do bloco de
100 candidatos da ③ (match bit-a-bit em X) e testa se e' o argmax do pseudo-sigma_0 da
estrategia (s1=dist_dec, s2=HV_gain, s3=Eucli). Tambem: U11 (fantasia mu vs f real),
identidades de telemetria (cand_dist_dec/hv_gain/cand_eucli vs a ③).
Escreve: e74_joia.csv (por bloco) e e74_joia_resumo.csv
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))
res = []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(base + '__real.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    sur = sur[sur.regime == 'online']
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    Xr = real[xc].to_numpy(np.float32)
    Fr = real[fc].to_numpy(np.float32)
    blocks = {g: d for g, d in sur.groupby('geracao')}
    for ev in gens:
        g = ev['geracao']; est = ev['estrategia']
        blk = blocks.get(g)
        if blk is None:
            res.append(dict(problema=pr, geracao=g, est=est, aceito=ev['aceito'], bloco=0)); continue
        Xb = blk[xc].to_numpy(np.float32)
        s0 = blk['sigma_0'].to_numpy(np.float64)
        mu = blk[[f'mu_{j}' for j in range(M)]].to_numpy(np.float64)
        n_val = int(np.isfinite(s0).sum())
        amax = int(np.nanargmax(s0)) if n_val > 0 else -1
        r = dict(problema=pr, D=D, M=M, geracao=g, est=est, aceito=ev['aceito'],
                 slot=ev['slot_perdido'], bloco=len(blk), n_sigma_val=n_val,
                 n_mu_val=int(np.isfinite(mu[:, 0]).sum()),
                 sig_max=(float(np.nanmax(s0)) if n_val else np.nan),
                 tel=float(ev.get('cand_dist_dec', ev.get('hv_gain', ev.get('cand_eucli', np.nan))) or 0.0))
        if ev['aceito'] == 1:
            fi = ev['fe'] - 1
            xi = Xr[fi]
            d = np.abs(Xb - xi).max(axis=1)
            pos = int(np.argmin(d))
            r['dX_max'] = float(d[pos])
            r['achado'] = bool(d[pos] == 0.0)
            r['pos'] = pos
            r['is_argmax'] = bool(pos == amax)
            r['sig_do_escolhido'] = float(s0[pos]) if np.isfinite(s0[pos]) else np.nan
            # rank do escolhido (1 = maior sigma)
            ss = s0.copy(); ss[~np.isfinite(ss)] = -np.inf
            r['rank_sigma'] = int((ss > ss[pos]).sum() + 1)
            # U11 fantasia
            if np.isfinite(mu[pos, 0]):
                r['abs_err_mu'] = float(np.abs(mu[pos] - Fr[fi].astype(np.float64)).mean())
                r['f_real_norm'] = float(np.abs(Fr[fi].astype(np.float64)).mean())
        res.append(r)
    print(pr, 'ok', flush=True)

df = pd.DataFrame(res)
df.to_csv(f'{OUT}/e74_joia.csv', index=False)
ac = df[df.aceito == 1]
print('\n=== QUERY-JOIA (blocos com infill aceito) ===')
r = ac.groupby('est').agg(n=('achado', 'size'), achado=('achado', 'sum'),
                          argmax=('is_argmax', 'sum'), dXmax=('dX_max', 'max'),
                          rank_med=('rank_sigma', 'median'), rank_p95=('rank_sigma', lambda s: s.quantile(.95)))
r['pct_achado'] = 100 * r.achado / r.n
r['pct_argmax'] = 100 * r.argmax / r.n
print(r.to_string())
print('\npor problema x estrategia (pct argmax):')
t = ac.pivot_table(index='problema', columns='est', values='is_argmax', aggfunc=lambda s: 100 * s.mean())
n = ac.pivot_table(index='problema', columns='est', values='is_argmax', aggfunc='size')
print(pd.concat([t.round(1).add_prefix('pct_s'), n.add_prefix('n_s')], axis=1).to_string())
print('\n=== identidade telemetria vs ③ (|sig_max - telemetria|) ===')
ac2 = ac.dropna(subset=['sig_max'])
ac2 = ac2.assign(dif=(ac2.sig_max - ac2.tel).abs())
print(ac2.groupby('est').dif.describe().to_string())
print('\n=== U11 fantasia (|mu-f| media por objetivo, so s2/s3/boot) ===')
print(ac.dropna(subset=['abs_err_mu']).groupby(['problema', 'est']).abs_err_mu.median().unstack().round(3).to_string())
print('\n=== blocos sem sigma valido / mu valido ===')
print(df.groupby('est').agg(blocos=('bloco', 'size'), sem_sigma=('n_sigma_val', lambda s: int((s == 0).sum())),
                            sig_val_med=('n_sigma_val', 'median')).to_string())
ac.groupby(['problema', 'est']).agg(n=('is_argmax', 'size'), argmax=('is_argmax', 'sum'),
                                    achado=('achado', 'sum')).to_csv(f'{OUT}/e74_joia_resumo.csv')
