#!/usr/bin/env python
"""B08 — diagnosticos discriminativos (rodados inline durante a analise, consolidados aqui):
 D1  identificacao do kernel: MQ c=1 poly=0 x 7 alternativas (+ MQ c=1 com cauda linear)
 D2  arquivo VERDADEIRO x arquivo PREDITO no nivel 1 (teste discriminativo do bundle x paper)
 D3  sigma_1: std ddof=1 (MATLAB) x ddof=0
 D4  residuo do nivel 1 explicado por EMPATES exatos em float32
 D5  regras alternativas de deduplicacao no nivel 1 (R1 bruto vence)
Saidas: b08_kernel.csv · b08_arquivo.csv · b08_sigma1.csv · b03_nivel1_empates.csv · b08_regras.csv
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT, sde, ranks_asc, QU

OUT = os.path.dirname(os.path.abspath(__file__))


def pd2(A, B):
    return np.maximum((A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T, 0.0)


def f1n(F):
    le = (F[:, None, :] <= F[None, :, :]).all(-1)
    lt = (F[:, None, :] < F[None, :, :]).any(-1)
    return ~(le & lt).any(0)


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


def phi(r2, kind):
    if kind == 'MQ_c1':   return np.sqrt(r2 + 1.0)
    if kind == 'MQ_c0.5': return np.sqrt(r2 + 0.25)
    if kind == 'MQ_c2':   return np.sqrt(r2 + 4.0)
    if kind == 'IMQ_c1':  return 1 / np.sqrt(r2 + 1.0)
    if kind == 'gauss':   return np.exp(-r2)
    if kind == 'cubic':   return r2 ** 1.5
    if kind == 'linear':  return np.sqrt(r2)
    if kind == 'TPS':
        r = np.sqrt(r2); o = np.zeros_like(r); m = r > 0; o[m] = r2[m] * np.log(r[m]); return o


# ---------------- D1 kernel ----------------
KER = ['MQ_c1', 'MQ_c0.5', 'MQ_c2', 'IMQ_c1', 'gauss', 'cubic', 'linear', 'TPS']
rows = []
for pb, gsel in [('DTLZ2', [1, 20, 40]), ('ZDT1', [1, 50, 150]), ('MMF1', [1, 6]),
                 ('WFG4', [1, 40, 100]), ('BBOB_F1', [10, 40]), ('MMF16_20', [10, 60])]:
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]; D, M = h['D'], h['M']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]
    on = sur[sur.regime == 'online']
    for gn in gsel:
        gg = [e for e in ev if e.get('rec') == 'c141_gen' and e['geracao'] == gn]
        if not gg: continue
        g = gg[0]
        m = (real.fe_index <= g['fe_treino_max']).values
        X = real.loc[m, xc].values.astype(np.float64); F = real.loc[m, fc].values.astype(np.float64)
        P = on[on.geracao == gn]; Xp = P[xc].values.astype(np.float64); obs = P[mc].values.astype(np.float64)
        d2 = pd2(X, X); d2p = pd2(Xp, X)
        r = dict(problema=pb, geracao=gn, n=len(X), escala=float(np.median(np.abs(obs))))
        for k in KER:
            try:
                W = np.linalg.solve(phi(d2, k), F); e = np.abs(phi(d2p, k) @ W - obs)
                r[k + '_max'] = float(e.max()); r[k + '_med'] = float(np.median(e))
            except Exception:
                r[k + '_max'] = np.nan; r[k + '_med'] = np.nan
        n = len(X)
        A = np.zeros((n + D + 1, n + D + 1)); A[:n, :n] = np.sqrt(d2 + 1.0)
        A[:n, n] = 1; A[:n, n + 1:] = X; A[n, :n] = 1; A[n + 1:, :n] = X.T
        rhs = np.zeros((n + D + 1, M)); rhs[:n] = F
        W = np.linalg.lstsq(A, rhs, rcond=None)[0]
        e = np.abs(np.sqrt(d2p + 1.0) @ W[:n] + W[n] + Xp @ W[n + 1:] - obs)
        r['MQ_c1_poly1_max'] = float(e.max()); r['MQ_c1_poly1_med'] = float(np.median(e))
        rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'b08_kernel.csv'), index=False)
print('D1 kernel ok')

# ---------------- D2/D3/D4/D5 em TODAS as celulas ----------------
arq, sig, emp, reg = [], [], [], []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]; D, M = h['D'], h['M']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    on = sur[sur.regime == 'online']; og = {g: d for g, d in on.groupby('geracao')}
    a = b = 0
    r1 = r2 = r3 = r4 = 0
    for g in gens:
        m = (real.fe_index <= g['fe_treino_max']).values
        X = real.loc[m, xc].values.astype(np.float64); F = real.loc[m, fc].values.astype(np.float64)
        P = og[g['geracao']]; mu = P[mc].values.astype(np.float64)
        Phi = np.sqrt(pd2(X, X) + 1.0)
        # D2
        nd = f1n(np.vstack([mu, F])); n1 = int(nd[:len(mu)].sum()); a += (n1 == g['n_front1'])
        try:
            Wf = np.linalg.solve(Phi, F); Fp = Phi @ Wf
        except np.linalg.LinAlgError:
            Fp = F
        ndp = f1n(np.vstack([mu, Fp])); b += (int(ndp[:len(mu)].sum()) == g['n_front1'])
        # D4 empates
        A = np.vstack([mu, F]); ip = np.where(nd[:len(mu)])[0]
        eq = (A[:, None, :] == A[None, :, :]).all(-1); np.fill_diagonal(eq, False)
        emp.append(dict(problema=pb, geracao=g['geracao'], log=g['n_front1'], rec=n1,
                        dif=n1 - g['n_front1'], n_emp=int(eq[ip].any(1).sum())))
        # D5 regras
        R1 = n1
        R2 = len(np.unique(mu[ip], axis=0))
        eqA = np.array([bool((F == mu[i]).all(1).any()) for i in ip]) if len(ip) else np.array([], bool)
        R3 = int((~eqA).sum())
        _, first = np.unique(A, axis=0, return_index=True)
        keep = np.zeros(len(A), bool); keep[first] = True
        R4 = int((nd & keep)[:len(mu)].sum())
        r1 += (R1 == g['n_front1']); r2 += (R2 == g['n_front1'])
        r3 += (R3 == g['n_front1']); r4 += (R4 == g['n_front1'])
        # D3 sigma_1
        FitA = sde(F); FNA = nd_levels(F).astype(float)
        try:
            W = np.linalg.solve(Phi, np.column_stack([FitA, FNA]))
        except np.linalg.LinAlgError:
            W = np.linalg.lstsq(Phi, np.column_stack([FitA, FNA]), rcond=None)[0]
        Pr = np.sqrt(pd2(P[xc].values.astype(np.float64), X) + 1.0) @ W
        T = np.column_stack([sde(mu), Pr[:, 1], Pr[:, 0]])
        s1 = P.sigma_1.values.astype(np.float64)
        sig.append(dict(problema=pb, geracao=g['geracao'],
                        rel_ddof1=float(np.median(np.abs(s1 - T.std(1, ddof=1)) / (np.abs(s1) + 1e-12))),
                        rel_ddof0=float(np.median(np.abs(s1 - T.std(1, ddof=0)) / (np.abs(s1) + 1e-12)))))
    arq.append(dict(problema=pb, n=len(gens), arquivo_verdadeiro=a, arquivo_predito=b))
    reg.append(dict(problema=pb, n=len(gens), R1_bruto=r1, R2_uniqueMU=r2, R3_semEmpArquivo=r3, R4_uniqueGlobal=r4))
    print('ok', pb, flush=True)

pd.DataFrame(arq).to_csv(os.path.join(OUT, 'b08_arquivo.csv'), index=False)
pd.DataFrame(sig).to_csv(os.path.join(OUT, 'b08_sigma1.csv'), index=False)
pd.DataFrame(emp).to_csv(os.path.join(OUT, 'b03_nivel1_empates.csv'), index=False)
pd.DataFrame(reg).to_csv(os.path.join(OUT, 'b08_regras.csv'), index=False)
da = pd.DataFrame(arq); dr = pd.DataFrame(reg); de = pd.DataFrame(emp); ds = pd.DataFrame(sig)
print('\nD2 arquivo VERDADEIRO %d x PREDITO %d de %d' % (da.arquivo_verdadeiro.sum(), da.arquivo_predito.sum(), da.n.sum()))
print('D3 sigma_1 rel mediana ddof1=%.2e  ddof0=%.3f' % (ds.rel_ddof1.median(), ds.rel_ddof0.median()))
f = de[de.dif != 0]
print('D4 residuo nivel1: %d/%d falhas; explicadas por empate exato: %d (%.1f%%)' %
      (len(f), len(de), (f.dif.abs() <= f.n_emp).sum(), 100 * (f.dif.abs() <= f.n_emp).mean()))
print('D5 regras: R1=%d R2=%d R3=%d R4=%d de %d' % (dr.R1_bruto.sum(), dr.R2_uniqueMU.sum(),
                                                    dr.R3_semEmpArquivo.sum(), dr.R4_uniqueGlobal.sum(), dr.n.sum()))
