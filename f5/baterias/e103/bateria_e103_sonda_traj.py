#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_sonda_traj.py — F5.3b/e103 · regua da sonda SEPARADA POR MODELO
(Kriging-DACE mu+sigma  x  RBFN mu, sigma NULL — DI-16.12-analogo), trajetorias de
20 checkpoints, decay dos membros do dataset e cruzamento com sonda_f52e.csv.
READ-ONLY nos dados.  Saidas em f5/baterias/e103/.
"""
import os, sys, json, glob, math
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')


def cells():
    out = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, '42')
        if not os.path.isdir(d):
            continue
        mf = [f for f in glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json'))
              if '__final' not in f]
        base = os.path.basename(mf[0])[:-len('.manifest.json')]
        exp = base.split('_e103_')[0][len('exp_'):]
        prob = base.split('_e103_')[1][:-len('_42')]
        out.append((lab, exp, prob, d, base))
    return out


rows, traj_rows, decay_rows = [], [], []
for lab, exp, prob, d, base in cells():
    man = json.load(open(os.path.join(d, base + '.manifest.json')))
    recs = []
    for line in open(os.path.join(d, base + '.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    hdr = [x for x in recs if x.get('rec') == 'header'][0]
    gens = sorted([x for x in recs if x.get('rec') == 'e103_gen'], key=lambda x: x['geracao'])
    D, M, n_ds = hdr['D'], hdr['M'], hdr['n_dataset']
    tier, dist = man['dataset']['tier'], man['dataset']['dist']
    xc = ['x%d' % i for i in range(D)]
    fc = ['f%d' % i for i in range(M)]
    muc = ['mu_%d' % i for i in range(M)]

    sur = pq.read_table(os.path.join(d, base + '__surrogate.parquet')).to_pandas()
    son = sur[sur['regime'] == 'sonda']
    gab = pq.read_table(os.path.join(REPO, 'data', 'sonda', 'sonda_%s.parquet' % prob)).to_pandas()
    GF = gab[fc].values.astype(np.float64)
    GX = gab[xc].values.astype(np.float32)

    for mflag in ['Kriging-DACE', 'RBFN']:
        blk = son[son['modelo_flag'] == mflag]
        MU = blk[muc].values.astype(np.float64)
        SG = blk[['sigma_%d' % j for j in range(M)]].values.astype(np.float64)
        dX = float(np.abs(blk[xc].values.astype(np.float32) - GX[:len(blk)]).max())
        for j in range(M):
            mu, ft, sg = MU[:, j], GF[:len(MU), j], SG[:, j]
            fin = np.isfinite(mu) & np.isfinite(ft)
            den = np.abs(ft[fin]).sum()
            wape = float(np.abs(mu[fin] - ft[fin]).sum() / den) if den > 0 else np.nan
            corr = float(np.corrcoef(mu[fin], ft[fin])[0, 1]) if fin.sum() > 2 else np.nan
            val = np.isfinite(sg)
            cov = float((np.abs(mu[val] - ft[val]) <= 1.96 * sg[val]).mean()) if val.sum() else np.nan
            rows.append(dict(label=lab, exp=exp, problema=prob, D=D, M=M, n_dataset=n_ds,
                             tier=tier, dist=dist, modelo=mflag, obj=j,
                             wape=wape, corr=corr, cobertura95=cov,
                             n_sigma_validas=int(val.sum()), n=len(mu), dX_gabarito=dX,
                             sigma_med=float(np.nanmedian(sg)) if val.sum() else np.nan,
                             sigma_max=float(np.nanmax(sg)) if val.sum() else np.nan,
                             mu_min=float(np.nanmin(mu)), mu_max=float(np.nanmax(mu)),
                             f_min=float(ft.min()), f_max=float(ft.max())))

    # trajetoria de 20 checkpoints (pre-computada F5.2c)
    tj = os.path.join(REPO, 'f5', 'trajetorias', '%s_e103_%s_42.json' % (exp, prob))
    if os.path.exists(tj):
        T = json.load(open(tj))
        ig = [t['igd_plus'] for t in T]
        viol = int(sum(1 for a, b in zip(ig, ig[1:]) if b > a + 1e-12))
        traj_rows.append(dict(label=lab, exp=exp, problema=prob, n_ckpt=len(T),
                              igd0=ig[0], igdN=ig[-1], violacoes=viol,
                              fe0=T[0]['fe'], feN=T[-1]['fe'],
                              nnd0=T[0]['n_nd'], nndN=T[-1]['n_nd']))

    # decay dos membros do dataset na populacao selecionada (② / n_ds_membros)
    for x in gens:
        decay_rows.append(dict(label=lab, problema=prob, D=D, M=M, tier=tier, dist=dist,
                               geracao=x['geracao'], n_ds_membros=x['n_ds_membros'],
                               kflag=x['kflag']))
    print('ok', lab, flush=True)

pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sonda_por_modelo_e103.csv'), index=False)
pd.DataFrame(traj_rows).to_csv(os.path.join(OUT, 'trajetorias_e103.csv'), index=False)
pd.DataFrame(decay_rows).to_csv(os.path.join(OUT, 'decay_dataset_e103.csv'), index=False)
print('linhas:', len(rows), len(traj_rows), len(decay_rows))
