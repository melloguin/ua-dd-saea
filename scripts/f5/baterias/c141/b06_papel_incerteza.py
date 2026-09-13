#!/usr/bin/env python
"""B06 — o PAPEL da incerteza (G4/G5): quantas vezes o argmax-U (Pb) e um ponto EXTRA
fora da frente ND de (Q,U) (Pa), i.e. quantas FEs foram gastas *por causa da incerteza*.
Tambem: perfil por bloco da sonda para as celulas de divergencia numerica do RBF."""
import json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT, sde, ranks_asc, QU

OUT = os.path.dirname(os.path.abspath(__file__))
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'


def pd2(A, B):
    return np.maximum((A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T, 0.0)


def f1i(F):
    le = (F[:, None, :] <= F[None, :, :]).all(-1)
    lt = (F[:, None, :] < F[None, :, :]).any(-1)
    return np.where(~(le & lt).any(0))[0]


def nd_levels(F):
    le = (F[:, None, :] <= F[None, :, :]).all(-1)
    lt = (F[:, None, :] < F[None, :, :]).any(-1)
    d = le & lt
    n = len(F); lvl = np.zeros(n, int); alive = np.ones(n, bool); cur = 1
    while alive.any():
        sub = np.where(alive)[0]
        nd = sub[~d[np.ix_(sub, sub)].any(0)]
        lvl[nd] = cur; alive[nd] = False; cur += 1
    return lvl


rows, sondarows = [], []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]
    D, M = h['D'], h['M']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    on = sur[sur.regime == 'online']; og = {g: d for g, d in on.groupby('geracao')}
    nPa, nPb_extra, ok4, nciclo = [], 0, 0, 0
    for g in gens:
        P = og[g['geracao']]; mu = P[mc].values.astype(np.float64)
        m = (real.fe_index <= g['fe_treino_max']).values
        X = real.loc[m, xc].values.astype(np.float64); F = real.loc[m, fc].values.astype(np.float64)
        Phi = np.sqrt(pd2(X, X) + 1.0)
        FitA = sde(F); FNA = nd_levels(F).astype(float)
        try:
            W = np.linalg.solve(Phi, np.column_stack([FitA, FNA]))
        except np.linalg.LinAlgError:
            W = np.linalg.lstsq(Phi, np.column_stack([FitA, FNA]), rcond=None)[0]
        Pr = np.sqrt(pd2(P[xc].values.astype(np.float64), X) + 1.0) @ W
        fitpred, fnpred = Pr[:, 0], Pr[:, 1]
        allF = np.vstack([mu, F]); f1 = f1i(allF); idx1 = f1[f1 < len(mu)]
        if len(idx1) < 2:
            continue
        fit1 = sde(mu[idx1])
        Z = np.column_stack([-fit1, fnpred[idx1], -fitpred[idx1]])
        f2 = f1i(Z)
        R1 = ranks_asc(-fit1[f2]); R2 = ranks_asc(fnpred[idx1][f2]); R3 = ranks_asc(-fitpred[idx1][f2])
        Q, U = QU(R1, R2, R3)
        fa = f1i(np.column_stack([Q, U]).astype(float))
        amax = int(np.argmax(U))
        extra = amax not in set(fa.tolist())
        nPa.append(len(fa)); nPb_extra += int(extra); nciclo += 1
        ok4 += int(len(f2) == g['n_front2'])
    rows.append(dict(problema=pb, n_ciclos=nciclo, Pa_med=float(np.median(nPa)) if nPa else np.nan,
                     Pa_min=int(min(nPa)) if nPa else -1, Pa_max=int(max(nPa)) if nPa else -1,
                     Pb_extra=nPb_extra, Pb_extra_pct=100.0 * nPb_extra / max(nciclo, 1), n_front2_ok=ok4))

    # --- perfil da sonda por bloco (WAPE/spearman/amplitude) ---
    so = sur[sur.regime == 'sonda']
    gab = pd.read_parquet(os.path.join(SND, f'sonda_{pb}.parquet'))
    gfc = [c for c in gab.columns if c.startswith('f') and c[1:].isdigit()]
    Fg = gab[gfc].values.astype(np.float64)[:2000]
    for gnum, blk in so.groupby('geracao'):
        mu = blk[mc].values.astype(np.float64)
        for j in range(M):
            sondarows.append(dict(problema=pb, geracao=gnum, obj=j,
                                  wape=float(np.abs(mu[:, j] - Fg[:, j]).sum() / np.abs(Fg[:, j]).sum()),
                                  mae=float(np.abs(mu[:, j] - Fg[:, j]).mean()),
                                  mae_ref=float(np.abs(Fg[:, j] - Fg[:, j].mean()).mean()),
                                  sp=float(spearmanr(mu[:, j], Fg[:, j]).statistic),
                                  pe=float(np.corrcoef(mu[:, j], Fg[:, j])[0, 1]),
                                  mu_min=float(mu[:, j].min()), mu_max=float(mu[:, j].max()),
                                  f_min=float(Fg[:, j].min()), f_max=float(Fg[:, j].max())))
    print('ok', pb, flush=True)

df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'b06_incerteza.csv'), index=False)
ds = pd.DataFrame(sondarows); ds.to_csv(os.path.join(OUT, 'b06_sonda_detalhe.csv'), index=False)
pd.set_option('display.width', 300, 'display.max_columns', 100)
print(df.to_string())
print('\nTOTAL ciclos=%d  Pb_extra=%d (%.1f%%)' % (df.n_ciclos.sum(), df.Pb_extra.sum(),
                                                  100 * df.Pb_extra.sum() / df.n_ciclos.sum()))
print('\n--- sonda: pior spearman por celula ---')
print(ds.groupby('problema').agg(sp_min=('sp', 'min'), sp_med=('sp', 'median'),
                                 mae_ratio=('mae', 'max'), mu_min=('mu_min', 'min'),
                                 mu_max=('mu_max', 'max'), f_max=('f_max', 'max')).round(4).to_string())
