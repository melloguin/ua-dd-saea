#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 6 (versão com projeção de colunas — rápida):
 (a) ⑦ das 45 células × {moead_media, b5m, b5r, e103}: IGD+/HV/fantasia (inclui o SWEEP,
     que não existe no transversal_offline_camada7.csv da F5.5);
 (b) μ da sonda posicional piso × b5m/b5r (mesmos 20.000 pontos) — DI-28;
 (c) turnover posicional da população por geração, por config.
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import json, os, glob, sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = REPO + '/f5/baterias/moead_media'
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics as MX  # noqa: E402

ALGS = ['moead_media', 'b5m', 'b5r', 'e103']
LABELS = sorted(os.listdir(RES + '/moead_media'))


def cnames(f):
    return pq.ParquetFile(f).schema.names


def fx(names, p):
    return sorted([c for c in names if c[0] == p and c[1:].isdigit()], key=lambda c: int(c[1:]))


# ── (a) ⑦ ─────────────────────────────────────────────────────────────
r7 = []
for label in LABELS:
    for alg in ALGS:
        g = glob.glob('%s/%s/%s/42/*__final.parquet' % (RES, alg, label))
        if not g:
            continue
        d7 = pd.read_parquet(g[0])
        prob = d7['problema'].iloc[0]
        F = d7[fx(d7.columns, 'f')].values.astype(float)
        nd = d7['nd_pos_real'].values.astype(bool)
        try:
            mm = MX.metrics_of_set(F[nd] if nd.any() else F, prob)
        except Exception as e:
            mm = {'igd_plus': np.nan, 'hv': np.nan, 'igd': np.nan, 'gd': np.nan, 'spacing': np.nan}
        r7.append({'label': label, 'alg': alg, 'problema': prob,
                   'n_final': len(d7), 'n_nd': int(nd.sum()), 'fantasia': float(nd.mean()),
                   'igd7': mm['igd_plus'], 'hv7': mm['hv'], 'gd7': mm['gd'],
                   'sp7': mm['spacing']})
    print('⑦ %-28s' % label, flush=True)
pd.DataFrame(r7).to_csv(OUT + '/camada7_45celulas.csv', index=False)

# ── (b) μ da sonda posicional ─────────────────────────────────────────
cm = []
for label in LABELS:
    store = {}
    for alg in ['moead_media', 'b5m', 'b5r']:
        g = glob.glob('%s/%s/%s/42/*__surrogate.parquet' % (RES, alg, label))
        if not g:
            continue
        nm = cnames(g[0])
        mu = sorted([c for c in nm if c.startswith('mu_')], key=lambda s: int(s.split('_')[1]))
        t = pq.read_table(g[0], columns=['regime'] + mu).to_pandas()
        s = t[t['regime'] == 'sonda'][mu].values.astype(float)[:20000]
        store[alg] = s
    P = store.get('moead_media')
    if P is None:
        continue
    for alg in ['b5m', 'b5r']:
        Q = store.get(alg)
        if Q is None or Q.shape != P.shape:
            continue
        for j in range(P.shape[1]):
            a, b = P[:, j], Q[:, j]
            cm.append({'label': label, 'vs': alg, 'obj': j,
                       'identico': bool(np.array_equal(a, b)),
                       'dmax': float(np.abs(a - b).max()),
                       'piso_colapso': bool(np.all(a == 0.0)),
                       'outro_colapso': bool(np.all(b == 0.0))})
    print('μ %-28s' % label, flush=True)
pd.DataFrame(cm).to_csv(OUT + '/mu_piso_vs_b5.csv', index=False)

# ── (c) turnover por config ───────────────────────────────────────────
tv = []
for label in LABELS:
    for alg in ALGS:
        g = glob.glob('%s/%s/%s/42/*__surrogate.parquet' % (RES, alg, label))
        if not g:
            continue
        nm = cnames(g[0])
        XC = fx(nm, 'x')
        t = pq.read_table(g[0], columns=['regime', 'geracao'] + XC).to_pandas()
        o = t[t['regime'] == 'offline']
        gg = o['geracao'].dropna().astype(int)
        if not len(gg):
            continue
        per = gg.value_counts()
        Np = int(per.mode().iloc[0])
        if per.nunique() != 1 or len(o) != Np * per.size:
            tv.append({'label': label, 'alg': alg, 'pop_variavel': True, 'N_pop': Np,
                       'n_ger': int(per.size)})
            continue
        A = o.sort_values('geracao', kind='stable')[XC].values.astype(np.float32)
        A = A.reshape(per.size, Np, len(XC))
        ch = (A[1:] != A[:-1]).any(axis=2).mean(axis=1)
        q = max(1, len(ch) // 4)
        tv.append({'label': label, 'alg': alg, 'pop_variavel': False, 'N_pop': Np,
                   'n_ger': int(per.size), 'turn_mean': float(ch.mean()),
                   'turn_med': float(np.median(ch)), 'turn_g2': float(ch[0]),
                   'turn_q1': float(ch[:q].mean()), 'turn_q4': float(ch[-q:].mean()),
                   'congeladas': int((ch == 0).sum()), 'n_trans': len(ch)})
    print('turn %-28s' % label, flush=True)
pd.DataFrame(tv).to_csv(OUT + '/turnover_por_config.csv', index=False)
print('FEITO')
