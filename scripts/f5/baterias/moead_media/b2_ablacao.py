#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 2: a ABLAÇÃO D77 (piso μ × b5m/b5r σ) + e103/c311.
Endpoint = ⑦ (nd_pos_real / f REAL) nas 45 células pareadas. Também:
  · μ da sonda lado a lado (mesmos 20.000 pontos) — 'mesma especificação, treino independente' (DI-28)
  · colapso do GP (μ ≡ 0 = média a priori) por config
  · turnover posicional da população por geração (σ empurra ou não?)
READ-ONLY nos dados. Escreve só em f5/baterias/moead_media/.
"""
import json, os, glob, sys
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = REPO + '/f5/baterias/moead_media'
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics as MX  # noqa: E402

ALGS = ['moead_media', 'b5m', 'b5r', 'e103', 'c311']
LABELS = sorted(os.listdir(RES + '/moead_media'))


def cols(df, p):
    return sorted([c for c in df.columns if c[0] == p and c[1:].isdigit()], key=lambda c: int(c[1:]))


rows, mus, turn = [], [], []
for label in LABELS:
    for alg in ALGS:
        d = '%s/%s/%s/42' % (RES, alg, label)
        if not os.path.isdir(d):
            continue
        mfp = [p for p in glob.glob(d + '/*.manifest.json') if '__final' not in p]
        if not mfp:
            continue
        m = json.load(open(mfp[0]))
        base = mfp[0][:-len('.manifest.json')]
        r = {'label': label, 'alg': alg, 'problema': m['problema'], 'exp': m['exp'],
             'n_ger': m['n_geracoes'], 'wall_s': m['timing']['tempo_total_s'],
             't_fit': m['timing']['tempo_fit_surrogate_s'],
             't_busca': m['timing']['tempo_busca_s']}
        # ⑦
        f7 = base + '__final.parquet'
        if os.path.exists(f7):
            d7 = pd.read_parquet(f7)
            F = d7[cols(d7, 'f')].values.astype(float)
            nd = d7['nd_pos_real'].values.astype(bool)
            r['n_final'] = len(d7); r['n_nd'] = int(nd.sum())
            r['fantasia'] = float(nd.mean())
            try:
                mm = MX.metrics_of_set(F[nd] if nd.any() else F, m['problema'])
                r['igd7'] = mm['igd_plus']; r['hv7'] = mm['hv']; r['igd7_igd'] = mm['igd']
                r['gd7'] = mm['gd']; r['sp7'] = mm['spacing']
            except Exception as e:
                r['igd7'] = np.nan; r['hv7'] = np.nan; r['erro'] = str(e)[:80]
        # ③: sonda μ/σ + turnover
        f3 = base + '__surrogate.parquet'
        if os.path.exists(f3):
            d3 = pd.read_parquet(f3)
            XC = cols(d3, 'x')
            MU = [c for c in d3.columns if c.startswith('mu_')]
            SI = [c for c in d3.columns if c.startswith('sigma_')]
            son = d3[d3['regime'] == 'sonda']
            r['n_sonda'] = len(son); r['n_blocos_sonda'] = int(son['geracao'].nunique(dropna=False))
            r['sigma_nan_pct'] = float(d3[SI].isna().all(axis=1).mean()) if SI else np.nan
            if len(son):
                blk = son.iloc[:20000] if len(son) >= 20000 else son
                for j, c in enumerate(sorted(MU, key=lambda s: int(s.split('_')[1]))):
                    v = blk[c].values.astype(float)
                    mus.append({'label': label, 'alg': alg, 'obj': j,
                                'mu_min': float(v.min()), 'mu_max': float(v.max()),
                                'mu_mean': float(v.mean()),
                                'colapso_zero': bool(np.all(v == 0.0)),
                                'n': len(v)})
            ofl = d3[d3['regime'] == 'offline']
            g = ofl['geracao'].dropna().astype(int)
            if len(g):
                per = g.value_counts()
                Np = int(per.mode().iloc[0])
                if per.nunique() == 1 and len(ofl) == Np * per.size:
                    A = ofl.sort_values('geracao', kind='stable')[XC].values.astype(np.float32)
                    A = A.reshape(per.size, Np, len(XC))
                    ch = (A[1:] != A[:-1]).any(axis=2).mean(axis=1)
                    r['N_pop'] = Np
                    r['turn_mean'] = float(ch.mean()); r['turn_med'] = float(np.median(ch))
                    r['turn_q1'] = float(ch[:max(1, len(ch) // 4)].mean())
                    r['turn_q4'] = float(ch[-max(1, len(ch) // 4):].mean())
                    r['gers_congeladas'] = int((ch == 0).sum()); r['n_transicoes'] = len(ch)
                    turn.append({'label': label, 'alg': alg,
                                 'turn_mean': float(ch.mean()),
                                 'congeladas': int((ch == 0).sum()), 'n': len(ch)})
        rows.append(r)
        print('%-28s %-12s ok' % (label, alg), flush=True)

df = pd.DataFrame(rows)
df.to_csv(OUT + '/bateria2_ablacao_camada7.csv', index=False)
pd.DataFrame(mus).to_csv(OUT + '/mu_sonda_por_config.csv', index=False)
pd.DataFrame(turn).to_csv(OUT + '/turnover_por_config.csv', index=False)

# ── μ posicional: piso × b5m × b5r nos MESMOS 20.000 pontos ────────────
cmp_rows = []
for label in LABELS:
    ref = None
    store = {}
    for alg in ['moead_media', 'b5m', 'b5r']:
        f3 = glob.glob('%s/%s/%s/42/*__surrogate.parquet' % (RES, alg, label))
        if not f3:
            continue
        d3 = pd.read_parquet(f3[0], columns=None)
        son = d3[d3['regime'] == 'sonda']
        MU = sorted([c for c in d3.columns if c.startswith('mu_')], key=lambda s: int(s.split('_')[1]))
        store[alg] = son.iloc[:20000][MU].values.astype(float)
    if 'moead_media' not in store:
        continue
    P = store['moead_media']
    for alg in ['b5m', 'b5r']:
        if alg not in store or store[alg].shape != P.shape:
            continue
        Q = store[alg]
        for j in range(P.shape[1]):
            a, b = P[:, j], Q[:, j]
            cmp_rows.append({'label': label, 'vs': alg, 'obj': j,
                             'dmax': float(np.abs(a - b).max()),
                             'identico': bool(np.array_equal(a, b)),
                             'rel_med': float(np.median(np.abs(a - b) / np.maximum(np.abs(b), 1e-12))),
                             'piso_colapso': bool(np.all(a == 0.0)),
                             'outro_colapso': bool(np.all(b == 0.0))})
    print('mu-cmp %-28s ok' % label, flush=True)
pd.DataFrame(cmp_rows).to_csv(OUT + '/mu_piso_vs_b5.csv', index=False)
print('\nFEITO')
