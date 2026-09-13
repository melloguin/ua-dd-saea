#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_extra.py — F5.3b/e103 · fechos finais:
 (a) identidade FECHADA do gate: KFlag == [#objetivos 100%-confiaveis >= M-1]  (query-joia)
 (b) objetivo degenerado do Kriging (sigma->0, WAPE->0) com digitos exatos
 (c) empate por desenho das metricas da (1) entre os 5 algs offline (D69)
 (d) sweep: mais dado -> melhor?  (dataset x endpoint (7) x KFlag x tier/dist)
 (e) contabilidade do orcamento interno (10.000 avaliacoes-surrogate)
READ-ONLY.  Saidas em f5/baterias/e103/.
"""
import os, sys, json, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')

# ---------- (a) identidade fechada do gate 3sigma ----------
lin = []
for lab in sorted(os.listdir(os.path.join(RES, 'e103'))):
    d = os.path.join(RES, 'e103', lab, '42')
    if not os.path.isdir(d):
        continue
    mf = [f for f in glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json')) if '__final' not in f]
    base = os.path.basename(mf[0])[:-len('.manifest.json')]
    prob = base.split('_e103_')[1][:-len('_42')]
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
    M = hdr['M']
    for x in sorted([r for r in recs if r.get('rec') == 'e103_gen'], key=lambda r: r['geracao']):
        ms = x.get('margem_3sigma_stats') or {}
        tot = ms.get('n_pares_total')
        po = ms.get('n_pares_ok_por_objetivo') or []
        n100 = sum(1 for v in po if v == tot)
        lin.append(dict(label=lab, problema=prob, M=M, geracao=x['geracao'], kflag=x['kflag'],
                        n_obj_100pct=n100, criterio=int(n100 >= M - 1),
                        pares_ok=ms.get('n_pares_ok'), pares_total=tot,
                        n_julgados=x['n_julgados'],
                        pares_eq_n2=int(tot == x['n_julgados'] ** 2),
                        frac_ok=(ms.get('n_pares_ok') / tot) if tot else np.nan,
                        estrito_M=int(min(po) == tot) if po else None))
g = pd.DataFrame(lin)
g['bate'] = (g.criterio == g.kflag).astype(int)
g.to_csv(os.path.join(OUT, 'gate3sigma_identidade_e103.csv'), index=False)
print('(a) IDENTIDADE DO GATE  KFlag == [#obj 100%% confiaveis >= M-1] : %d/%d geracoes'
      % (int(g.bate.sum()), len(g)))
print('    n_pares_total == n_julgados^2 : %d/%d' % (int(g.pares_eq_n2.sum()), len(g)))
print('    contrafactual ESTRITO (IBEA-MS-NT: exige TODOS os M): Kriging em %d/%d geracoes'
      % (int(g.estrito_M.sum()), len(g)))
print('    celulas em que o estrito MUDARIA a escolha:',
      sorted(g.groupby('label').apply(lambda t: (t.estrito_M != t.kflag).any())[lambda s: s].index.tolist()))

# ---------- (b) objetivo degenerado ----------
deg = []
for lab in sorted(os.listdir(os.path.join(RES, 'e103'))):
    d = os.path.join(RES, 'e103', lab, '42')
    if not os.path.isdir(d):
        continue
    mf = [f for f in glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json')) if '__final' not in f]
    base = os.path.basename(mf[0])[:-len('.manifest.json')]
    prob = base.split('_e103_')[1][:-len('_42')]
    man = json.load(open(os.path.join(d, base + '.manifest.json')))
    recs = [json.loads(l) for l in open(os.path.join(d, base + '.jsonl'), encoding='utf-8')
            if l.strip() and l.strip()[0] == '{' and l.strip()[-1] == '}']
    hdr = [x for x in recs if x.get('rec') == 'header'][0]
    D, M = hdr['D'], hdr['M']
    sur = pq.read_table(os.path.join(d, base + '__surrogate.parquet')).to_pandas()
    son = sur[(sur.regime == 'sonda') & (sur.modelo_flag == 'Kriging-DACE')]
    gab = pq.read_table(os.path.join(REPO, 'data', 'sonda', 'sonda_%s.parquet' % prob)).to_pandas()
    for j in range(M):
        mu = son['mu_%d' % j].values.astype(np.float64)
        ft = gab['f%d' % j].values.astype(np.float64)[:len(mu)]
        sg = son['sigma_%d' % j].values.astype(np.float64)
        deg.append(dict(label=lab, problema=prob, D=D, M=M, obj=j,
                        wape=float(np.abs(mu - ft).sum() / np.abs(ft).sum()),
                        err_max=float(np.abs(mu - ft).max()),
                        sigma_med=float(np.median(sg)), sigma_max=float(sg.max()),
                        # o objetivo e' "degenerado" (interpolado exato) se sigma ~ 0
                        degenerado=int(np.median(sg) < 1e-10)))
dg = pd.DataFrame(deg)
dg.to_csv(os.path.join(OUT, 'objetivo_degenerado_e103.csv'), index=False)
kf = g.groupby('label').kflag.max()
dgc = dg.groupby('label').degenerado.sum().rename('n_obj_degenerado').to_frame()
dgc['M'] = dg.groupby('label').M.first()
dgc['kflag'] = kf
dgc['criterio_degenerado'] = (dgc.n_obj_degenerado >= dgc.M - 1).astype(int)
print('\n(b) DEGENERESCENCIA  [#obj com sigma~0 >= M-1] == KFlag : %d/45 celulas'
      % int((dgc.criterio_degenerado == dgc.kflag).sum()))
print(dgc.to_string())

# ---------- (c) empate por desenho na (1) entre os algs offline (D69) ----------
met = pd.read_csv(os.path.join(REPO, 'f5', 'metricas_finais_f52c.csv'))
offalgs = ['e103', 'c311', 'b5r', 'b5m', 'moead_media', 'treed_media']
sub = met[(met.exp == 'off') & (met.alg.isin(offalgs))]
piv = sub.pivot_table(index='problema', columns='alg', values='igd_plus')
piv = piv[[c for c in offalgs if c in piv.columns]]
piv['spread_max'] = piv.max(axis=1) - piv.min(axis=1)
piv.to_csv(os.path.join(OUT, 'empate_D69_off_e103.csv'))
print('\n(c) EMPATE D69 na (1): problemas com spread ZERO entre os %d algs offline: %d/%d  (max spread %.3g)'
      % (piv.shape[1] - 1, int((piv.spread_max == 0).sum()), len(piv), piv.spread_max.max()))

# ---------- (d) sweep ----------
ep = pd.read_csv(os.path.join(OUT, 'endpoint_e103.csv'))
sw = ep[ep.label.str.startswith('swap_')].copy()
sw['prob'] = sw.label.str.split('_').str[-1]
sw['tier2'] = sw.label.str.extract(r'swap_(\w+?)-')[0]
sw['dist2'] = sw.label.str.extract(r'-(\w+?)_')[0]
sw = sw[['prob', 'tier2', 'dist2', 'n_dataset', 'modelo', 'igd_dataset', 'igd_final',
         'ganho_igd', 'fantasia', 'nd_pos_real', 'center_num', 'frac_pares_ok_med',
         't_fit_krig', 't_fit_rbfn']]
sw.sort_values(['prob', 'dist2', 'n_dataset']).to_csv(os.path.join(OUT, 'sweep_e103.csv'), index=False)
print('\n(d) SWEEP (ordenado por problema/dist/n):')
print(sw.sort_values(['prob', 'dist2', 'n_dataset']).round(5).to_string(index=False))

# ---------- (e) contabilidade do orcamento interno ----------
cel = pd.read_csv(os.path.join(OUT, 'bateria_e103_celulas.csv'))
print('\n(e) ORCAMENTO INTERNO')
print('    geracoes por celula (unicas):', sorted(cel.n_geracoes.unique()))
print('    candidatos gerados = 99 ger x 100 offspring =', 99 * 100,
      ' | nominal do paper: 10.000  | deficit:', 10000 - 99 * 100)
print('    n_julgados na ger 1 == n_dataset+100 :',
      int((cel.A_njulg_g1 == cel.n_dataset + 100).sum()), '/45')
print('    n_julgados nas gers 2..99 == 200 :',
      int(cel.A_njulg_uniq_g2p.eq('[200]').sum()), '/45')
print('    linhas da (3) offline == 2 x 100 x 99 == 19.800 :', int(cel.U10_opt_ok.sum()), '/45')
