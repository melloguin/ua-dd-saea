#!/usr/bin/env python
"""B2 — ONDE o smoke T11 diverge da rodada-42 (mesma celula main/c238/MMF1/42)."""
import json
import numpy as np, pandas as pd

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42'
B = 'exp_main_c238_MMF1_42'

sa = pd.read_parquet(f'{SM}/{B}__real.parquet'); sb = pd.read_parquet(f'{R42}/{B}__real.parquet')
ma = json.load(open(f'{SM}/{B}.manifest.json')); mb = json.load(open(f'{R42}/{B}.manifest.json'))
ra = [json.loads(l) for l in open(f'{SM}/{B}.jsonl')]; rb = [json.loads(l) for l in open(f'{R42}/{B}.jsonl')]

print('repo_hash smoke=%s  r42=%s' % (ma['repo_hash'], mb['repo_hash']))
print('algo_version smoke=%s  r42=%s' % (ma['algo_version'], mb['algo_version']))
print('env smoke=%s' % ma['env']); print('env r42  =%s' % mb['env'])
print('doe_hash igual?', ma['doe_hash'] == mb['doe_hash'])
print('sonda x_hash igual?', ma['sonda']['x_hash'] == mb['sonda']['x_hash'],
      ' f_hash igual?', ma['sonda']['f_hash'] == mb['sonda']['f_hash'])

cols = ['x0', 'x1', 'f0', 'f1']
A = sa[cols].to_numpy(np.float64); Bb = sb[cols].to_numpy(np.float64)
d = np.abs(A - Bb).max(axis=1)
print('\n① max|delta| por fe_index — primeiros 30:')
for i in range(30):
    print('   fe=%2d fase=%-5s delta=%.6g' % (i, sa['fase'][i], d[i]))
nz = np.nonzero(d > 0)[0]
print('  primeiro fe_index com delta>0:', nz[0] if len(nz) else None, ' (init = 0..20)')
print('  init (0..20) identico?', bool((d[:21] == 0).all()))
print('  n de fe com delta>0:', len(nz), 'de', len(d))

# a 1a geracao de otimizacao
ga = [r for r in ra if r['rec'] == 'c238_gen']; gb = [r for r in rb if r['rec'] == 'c238_gen']
print('\n⑥ geracao 1 — smoke x r42 (o fit inicial é sobre o MESMO DoE):')
for k in ['n_amostra', 'n_treino', 'n_front', 'theta_min', 'theta_max', 'theta_media', 'lnL',
          'norm_min', 'norm_max', 'eim_best', 'u_best', 's_best', 'min_dist_infill', 'infill_sid']:
    print('   %-16s smoke=%s\n   %-16s r42  =%s' % (k, ga[0][k], '', gb[0][k]))

print('\n⑥ delta por geracao (eim_best, theta_media[0], lnL[0]):')
for i in range(len(ga)):
    print('   g=%2d  d_eim=%.6g  d_theta0=%.6g  d_lnL0=%.6g  d_nfront=%d' % (
        i + 1, abs(ga[i]['eim_best'] - gb[i]['eim_best']),
        abs(ga[i]['theta_media'][0] - gb[i]['theta_media'][0]),
        abs(ga[i]['lnL'][0] - gb[i]['lnL'][0]),
        ga[i]['n_front'] - gb[i]['n_front']))

# sonda: o bloco g=1 usa o GP treinado no DoE identico
sua = pd.read_parquet(f'{SM}/{B}__surrogate.parquet'); sub = pd.read_parquet(f'{R42}/{B}__surrogate.parquet')
qa = sua[(sua.regime == 'sonda') & (sua.geracao == 1)].reset_index(drop=True)
qb = sub[(sub.regime == 'sonda') & (sub.geracao == 1)].reset_index(drop=True)
print('\n③ sonda bloco g=1 (GP treinado no DoE IDENTICO):')
for c in ['x0', 'x1', 'mu_0', 'mu_1', 'sigma_0', 'sigma_1']:
    print('   %-8s max|delta| = %.6g' % (c, np.abs(qa[c].to_numpy(np.float64) - qb[c].to_numpy(np.float64)).max()))
print('   mu_0 smoke[:3]=', qa['mu_0'].to_numpy()[:3], ' r42[:3]=', qb['mu_0'].to_numpy()[:3])
