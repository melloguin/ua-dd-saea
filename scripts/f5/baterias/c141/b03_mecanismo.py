#!/usr/bin/env python
"""B03 — reconstrucao COMPLETA do mecanismo MMRAEA em TODAS as celulas/geracoes.

Tier-1 (livre de RBF, so dados logados):
  J1  nivel 1: |F1(mu_pool U F_arquivo) ∩ Ptot| == n_front1   (Alg.3 l.1-2)
  J2  Fit1: max SDE(mu[nivel1]) == fit1.max do ⑥              (Eq.7 + subset do nivel 2)
Tier-2 (com os 3 RBFs reconstruidos do arquivo ①):
  J3  mu_rec ~ mu_obs (identificacao do kernel MQ c=1 poly=0 mldivide)
  J4  n_front2 == |F1([-Fit1, Fit2, -Fit3])|                   (DI-18, sinais)
  J5  Q/U min/med/max == log                                   (Eq.8)
  J6  lote == |F1(Q,U) U argmax U|                             (Alg.3 l.13-16)
  J7  U_pool_max == max(sigma_0 da ③)  e  sigma_0 == U(pool)   (D45 sigma_0)
  J8  sigma_1 == std_{ddof=1}([Fit1,Fit2,Fit3]) do pool        (D45 sigma_1)
Saida: b03_mecanismo.csv (1 linha/geracao) + b03_resumo.csv (1 linha/celula)
"""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, sde, ranks_asc, QU

OUT = os.path.dirname(os.path.abspath(__file__))


def pdist2(A, B):
    return np.maximum(((A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T), 0.0)


def dommat(F):
    """matriz booleana dom[i,j] = i domina j (minimizacao)."""
    le = (F[:, None, :] <= F[None, :, :]).all(-1)
    lt = (F[:, None, :] < F[None, :, :]).any(-1)
    return le & lt


def front1_idx(F):
    d = dommat(F)
    return np.where(~d.any(0))[0]


def nd_levels(F):
    d = dommat(F)
    n = len(F)
    lvl = np.zeros(n, int)
    alive = np.ones(n, bool)
    cur = 1
    while alive.any():
        sub = np.where(alive)[0]
        dd = d[np.ix_(sub, sub)]
        nd = sub[~dd.any(0)]
        lvl[nd] = cur
        alive[nd] = False
        cur += 1
    return lvl


GRID = None
rows = []
t0 = time.time()
probs = sorted(os.listdir('/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141'))
for pb in probs:
    man, ev, real, pop, sur, tim = load(pb)
    hdr = [e for e in ev if e.get('rec') == 'header'][0]
    D, M = hdr['D'], hdr['M']
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    mc = [f'mu_{i}' for i in range(M)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    on = sur[sur.regime == 'online']
    Xall = real[xc].values.astype(np.float64)
    Fall = real[fc].values.astype(np.float64)
    fe_index = real.fe_index.values
    on_g = {g: d for g, d in on.groupby('geracao')}
    for g in gens:
        gn = g['geracao']
        m = fe_index <= g['fe_treino_max']
        X, F = Xall[m], Fall[m]
        P = on_g.get(gn)
        if P is None or len(P) == 0:
            continue
        Xp = P[xc].values.astype(np.float64)
        mu = P[mc].values.astype(np.float64)

        # ---------- Tier-1 ----------
        allF = np.vstack([mu, F])
        f1 = front1_idx(allF)
        idx1 = f1[f1 < len(mu)]
        n_front1_rec = len(idx1)
        fit1_lvl1 = sde(mu[idx1]) if len(idx1) > 1 else np.array([np.nan])
        fit1max_rec = np.nanmax(fit1_lvl1)
        fit1max_log = g['fit1']['max'] if isinstance(g.get('fit1'), dict) else np.nan

        # ---------- 3 RBFs ----------
        FitA = sde(F)
        FNA = nd_levels(F).astype(float)
        Phi = np.sqrt(pdist2(X, X) + 1.0)
        Y = np.column_stack([F, FitA, FNA])
        try:
            W = np.linalg.solve(Phi, Y)
            solved = True
        except np.linalg.LinAlgError:
            W = np.linalg.lstsq(Phi, Y, rcond=None)[0]
            solved = False
        Pp = np.sqrt(pdist2(Xp, X) + 1.0)
        Pred = Pp @ W
        mu_rec = Pred[:, :M]
        fitpred = Pred[:, M]
        fnpred = Pred[:, M + 1]
        dmu = np.abs(mu_rec - mu)
        esc = np.median(np.abs(mu)) + 1e-12

        # ---------- niveis 2 e 3 ----------
        fit2 = fnpred[idx1]
        fit3 = fitpred[idx1]
        Z = np.column_stack([-fit1_lvl1, fit2, -fit3])
        f2 = front1_idx(Z)
        R1 = ranks_asc(-fit1_lvl1[f2]); R2 = ranks_asc(fit2[f2]); R3 = ranks_asc(-fit3[f2])
        Q, U = QU(R1, R2, R3)
        QUm = np.column_stack([Q, U]).astype(float)
        fa = front1_idx(QUm)
        sel = set(fa.tolist()) | {int(np.argmax(U))}

        # ---------- pool completo (sigma) ----------
        fit1_pool = sde(mu)
        R1p = ranks_asc(-fit1_pool); R2p = ranks_asc(fnpred); R3p = ranks_asc(-fitpred)
        Qp, Up = QU(R1p, R2p, R3p)
        s0 = P.sigma_0.values.astype(np.float64)
        s1 = P.sigma_1.values.astype(np.float64)
        s1rec = np.column_stack([fit1_pool, fnpred, fitpred]).std(axis=1, ddof=1)
        s1rec0 = np.column_stack([fit1_pool, fnpred, fitpred]).std(axis=1, ddof=0)

        def stat(d, k):
            return d[k] if isinstance(d, dict) else np.nan
        rows.append(dict(
            problema=pb, D=D, M=M, geracao=gn, n_treino=len(X), lote_log=g['lote'],
            nivel=g['nivel'], ramo_QU=g['ramo_QU'],
            n_front1_log=g['n_front1'], n_front1_rec=n_front1_rec,
            n_front2_log=g['n_front2'], n_front2_rec=len(f2),
            lote_rec=len(sel),
            fit1max_log=fit1max_log, fit1max_rec=fit1max_rec,
            fit1min_log=stat(g.get('fit1'), 'min'), fit1min_rec=float(fit1_lvl1[f2].min()) if len(f2) else np.nan,
            fit1med_log=stat(g.get('fit1'), 'med'), fit1med_rec=float(np.median(fit1_lvl1[f2])) if len(f2) else np.nan,
            fit2med_log=stat(g.get('fit2'), 'med'), fit2med_rec=float(np.median(fit2[f2])) if len(f2) else np.nan,
            fit3med_log=stat(g.get('fit3'), 'med'), fit3med_rec=float(np.median(fit3[f2])) if len(f2) else np.nan,
            Qmin_log=stat(g.get('Q'), 'min'), Qmin_rec=int(Q.min()) if len(Q) else -1,
            Qmax_log=stat(g.get('Q'), 'max'), Qmax_rec=int(Q.max()) if len(Q) else -1,
            Umin_log=stat(g.get('U'), 'min'), Umin_rec=int(U.min()) if len(U) else -1,
            Umax_log=stat(g.get('U'), 'max'), Umax_rec=int(U.max()) if len(U) else -1,
            Upool_log=g['U_pool_max'], Upool_rec=int(Up.max()),
            s0_obsmax=float(np.nanmax(s0)), s0_eq=float((s0 == Up).mean()),
            s0_corr=float(np.corrcoef(s0, Up)[0, 1]) if np.std(s0) > 0 else np.nan,
            s0_int=float((s0 == np.round(s0)).mean()), s0_max_teorico=2 * (len(mu) - 1),
            s1_relmed=float(np.median(np.abs(s1 - s1rec) / (np.abs(s1) + 1e-12))),
            s1_relmed_ddof0=float(np.median(np.abs(s1 - s1rec0) / (np.abs(s1) + 1e-12))),
            dmu_max=float(dmu.max()), dmu_med=float(np.median(dmu)),
            dmu_med_rel=float(np.median(dmu) / esc),
            rcond=float(1.0 / np.linalg.cond(Phi)), solved=solved,
            n_pool=len(mu), fe_treino_max=g['fe_treino_max'], hp_n=g['modelo_hp']['n'],
        ))
    print(f'{pb}: {len([r for r in rows if r["problema"]==pb])} gens  ({time.time()-t0:.0f}s)', flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b03_mecanismo.csv'), index=False)

df['J1'] = df.n_front1_log == df.n_front1_rec
df['J2'] = np.isclose(df.fit1max_log, df.fit1max_rec, rtol=1e-6, atol=1e-12)
df['J4'] = df.n_front2_log == df.n_front2_rec
df['J5'] = (df.Qmin_log == df.Qmin_rec) & (df.Qmax_log == df.Qmax_rec) & \
           (df.Umin_log == df.Umin_rec) & (df.Umax_log == df.Umax_rec)
df['J6'] = df.lote_log == df.lote_rec
df['J7'] = df.Upool_log == df.Upool_rec
res = df.groupby('problema').agg(
    n=('geracao', 'size'), J1=('J1', 'sum'), J2=('J2', 'sum'), J4=('J4', 'sum'),
    J5=('J5', 'sum'), J6=('J6', 'sum'), J7=('J7', 'sum'),
    s0_eq=('s0_eq', 'mean'), s0_corr=('s0_corr', 'mean'),
    s1_rel=('s1_relmed', 'median'), s1_rel0=('s1_relmed_ddof0', 'median'),
    dmu_med_rel=('dmu_med_rel', 'median'), rcond_min=('rcond', 'min'),
).reset_index()
res.to_csv(os.path.join(OUT, 'b03_resumo.csv'), index=False)
pd.set_option('display.width', 250, 'display.max_columns', 60)
print(res.to_string())
print('\nTOTAIS: n=%d J1=%d J2=%d J4=%d J5=%d J6=%d J7=%d' % (
    len(df), df.J1.sum(), df.J2.sum(), df.J4.sum(), df.J5.sum(), df.J6.sum(), df.J7.sum()))
