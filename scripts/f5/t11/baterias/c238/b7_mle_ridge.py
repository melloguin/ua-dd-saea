#!/usr/bin/env python
"""B7 — POR QUE o smoke diverge da rodada-42 ja na geracao 1, com o MESMO DoE.
Reimplementa a lnL concentrada de `GP_Train.m` (linhas 36-56) em float64 e a avalia nos
DOIS vetores theta logados (smoke x r42) sobre o MESMO conjunto de treino (o DoE, 21 pts).
Se a lnL for praticamente igual em theta muito diferentes => cume PLANO => nao-identificabilidade
=> o fmincon single-start e caotico sob perturbacao de ultimo bit (maquina/BLAS).
"""
import json, itertools, sys
import numpy as np, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, ROOT)
SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42/exp_main_c238_MMF1_42'

from src import problems as PB
pr = PB.MMF1()
lb, ub = np.asarray(pr.xl, float), np.asarray(pr.xu, float)
print('MMF1 bounds lb=%s ub=%s' % (lb, ub))


def lnL(theta, X, Y):
    """Concentrated_lnLikelihood de GP_Train.m (sinal invertido: aqui devolvo lnL, nao -lnL)."""
    n = X.shape[0]; one = np.ones((n, 1))
    t1 = (X ** 2 * theta).sum(1)[:, None] @ one.T
    t2 = X * np.sqrt(theta)
    R = np.exp(-(t1 + t1.T - 2 * (t2 @ t2.T))) + np.eye(n) * (10 + n) * np.finfo(float).eps
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        return -1e8
    a = np.linalg.solve(L.T, np.linalg.solve(L, Y))
    b = np.linalg.solve(L.T, np.linalg.solve(L, one))
    mu = float((one.T @ a).ravel()[0]) / float((one.T @ b).ravel()[0])
    r = Y - mu
    c = np.linalg.solve(L.T, np.linalg.solve(L, r))
    sig2 = float((r.T @ c).ravel()[0]) / n
    return -0.5 * n * np.log(sig2) - np.log(np.abs(np.diag(L))).sum()


out = {}
for tag, b in [('T11_smoke', SM), ('R42', R42)]:
    recs = [json.loads(l) for l in open(f'{b}.jsonl')]
    g1 = [r for r in recs if r.get('rec') == 'c238_gen'][0]
    real = pq.read_table(f'{b}__real.parquet').to_pandas().iloc[:g1['n_amostra']]
    Xr = real[['x0', 'x1']].to_numpy(np.float64)
    Fr = real[['f0', 'f1']].to_numpy(np.float64)
    X = (Xr - np.array(lb)) / (np.array(ub) - np.array(lb))
    mn = np.array(g1['norm_min']); rg = np.array(g1['norm_range_efetivo'])
    Yn = (Fr - mn) / rg
    out[tag] = dict(g1=g1, X=X, Y=Yn)
    print('\n### %s  n=%d' % (tag, len(X)))
    for j in range(2):
        pair = [g1['theta_min'][j], g1['theta_max'][j]]
        best = None
        for perm in set(itertools.permutations(pair)):
            v = lnL(np.array(perm, float), X, Yn[:, [j]])
            if best is None or abs(v - g1['lnL'][j]) < abs(best[1] - g1['lnL'][j]):
                best = (perm, v)
        print('   obj%d theta=%s  lnL_recomputada=%.9f  lnL_logada=%.9f  |D|=%.3g'
              % (j, np.round(best[0], 4), best[1], g1['lnL'][j], abs(best[1] - g1['lnL'][j])))

print('\n' + '=' * 88)
print('CRUZADO — a lnL do theta do OUTRO run, no MESMO conjunto de treino (obj0):')
Xs, Ys = out['T11_smoke']['X'], out['T11_smoke']['Y']
Xr, Yr = out['R42']['X'], out['R42']['Y']
print('   X identico entre os dois? max|D|=%.3g ; Y(obj0) identico? max|D|=%.3g'
      % (np.abs(Xs - Xr).max(), np.abs(Ys[:, 0] - Yr[:, 0]).max()))
ts = out['T11_smoke']['g1']; tr = out['R42']['g1']
for nome, th in [('theta do SMOKE', [ts['theta_min'][0], ts['theta_max'][0]]),
                 ('theta do R42  ', [tr['theta_min'][0], tr['theta_max'][0]])]:
    vals = [lnL(np.array(p, float), Xs, Ys[:, [0]]) for p in set(itertools.permutations(th))]
    print('   %s = %s  ->  lnL = %s' % (nome, np.round(th, 3), [round(v, 8) for v in vals]))

print('\nMAPA do cume (obj0): lnL sobre uma grade em log10(theta), mesmo treino do g=1')
grid = np.linspace(0, 3, 13)
best = -1e18
tab = []
for a in grid:
    lin = []
    for bq in grid:
        v = lnL(np.array([10 ** a, 10 ** bq]), Xs, Ys[:, [0]])
        lin.append(v); best = max(best, v)
    tab.append(lin)
tab = np.array(tab)
print('   log10(theta1)\\log10(theta2):', np.round(grid, 2))
for i, a in enumerate(grid):
    print('   %5.2f' % a, ' '.join('%8.3f' % v for v in tab[i]))
print('   max da grade = %.6f ; lnL logada (smoke) = %.6f ; (r42) = %.6f'
      % (best, ts['lnL'][0], tr['lnL'][0]))
sub = tab[(grid >= 2.5), :][:, (grid >= 2.5)]
print('   PLATO log10(theta)>=2.5 (theta>=316): lnL varia de %.6f a %.6f  (amplitude %.3g)'
      % (sub.min(), sub.max(), sub.max() - sub.min()))
