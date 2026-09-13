#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parte B: sonda escalar D47 (regua reconstruida por bloco) nas 23 celulas + join posicional."""
import json, os, sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq

BASE = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
SONDA = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
CELLS = ['BBOB_F1','BBOB_F5','BBOB_F17','BBOB_F22','BBOB_F37','BBOB_F49','BBOB_F55',
         'DTLZ1','DTLZ2','DTLZ3','DTLZ7','MMF1','MMF4','MMF11_L','MMF16_20',
         'WFG2','WFG4','WFG5','WFG9','ZDT1','ZDT3','ZDT4','ZDT6']

out = {}
for prob in CELLS:
    d = os.path.join(BASE, prob, '42'); pref = f'exp_main_b1_{prob}_42'
    man = json.load(open(os.path.join(d, pref+'.manifest.json')))
    art = pd.read_parquet(os.path.join(SONDA, f'sonda_{prob}.parquet'))
    xcols = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
    fcols = [c for c in art.columns if c.startswith('f') and c[1:].isdigit()]
    art_on = art.iloc[:2000]
    Xa = art_on[xcols].to_numpy(np.float64); Fa = art_on[fcols].to_numpy(np.float64)

    sp = os.path.join(d, pref+'__surrogate.parquet')
    cols = ['regime','geracao','mu_0','sigma_0','transf_params'] + xcols
    sur = pd.read_parquet(sp, columns=cols)
    sonda = sur[sur.regime=='sonda'].copy()
    sonda['g'] = sonda.geracao.astype(int)
    gens = sorted(sonda.g.unique())
    r = {'n_blocos': len(gens), 'nblocos_manifest': man['sonda']['n_blocos'],
         'blocos_ok_2000': int((sonda.groupby('g').size()==2000).sum()),
         'cadencia_ok': gens == sorted(man['sonda']['geracoes'])}
    maxdx = 0.0
    blocos = []
    for g in gens:
        b = sonda[sonda.g==g]
        if len(b)!=2000: continue
        Xs = b[xcols].to_numpy(np.float64)
        maxdx = max(maxdx, float(np.abs(Xs-Xa).max()))
        tp = b.transf_params.iloc[0]
        if isinstance(tp, str): tp = json.loads(tp)
        lam = np.array(tp['lambda'],np.float64); nm=np.array(tp['min'],np.float64); nx=np.array(tp['max'],np.float64)
        rng = np.where(nx-nm>0, nx-nm, 1.0)
        Fn = (Fa-nm)/rng
        pc = (Fn*lam).max(1)+0.05*(Fn*lam).sum(1)
        mu = b.mu_0.to_numpy(np.float64); sg = b.sigma_0.to_numpy(np.float64)
        wape = float(np.abs(mu-pc).sum()/max(np.abs(pc).sum(),1e-300))
        corr = float(np.corrcoef(mu,pc)[0,1]) if np.std(mu)>0 and np.std(pc)>0 else float('nan')
        cob = float((np.abs(mu-pc) <= 1.96*sg).mean())
        blocos.append((g,wape,corr,cob))
    r['maxdx_join'] = maxdx
    r['b_first'] = blocos[0]; r['b_last'] = blocos[-1]
    r['wape_first'], r['wape_last'] = blocos[0][1], blocos[-1][1]
    r['corr_first'], r['corr_last'] = blocos[0][2], blocos[-1][2]
    r['cob_first'], r['cob_last'] = blocos[0][3], blocos[-1][3]
    r['cob_min'] = min(b[3] for b in blocos); r['cob_med'] = float(np.median([b[3] for b in blocos]))
    r['wape_med'] = float(np.median([b[1] for b in blocos])); r['corr_med'] = float(np.median([b[2] for b in blocos]))
    out[prob] = r
    sys.stderr.write(prob+' ok\n')

# extra: DTLZ1 n_subset
ge=[]
with open(os.path.join(BASE,'DTLZ1','42','exp_main_b1_DTLZ1_42.jsonl')) as fh:
    for line in fh:
        e=json.loads(line)
        if e.get('rec')=='b1_gen': ge.append(e)
out['_DTLZ1_subset'] = {'n_subset_max': max(e['n_subset'] for e in ge),
                        'n_dedup_max': max(e['n_dedup'] for e in ge),
                        'gens_subset_no_cap': sum(1 for e in ge if e['n_subset']==101)}
print(json.dumps(out, indent=1, default=str))
