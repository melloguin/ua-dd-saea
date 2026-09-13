#!/usr/bin/env python
"""B9 — SANIDADE do B8: o 'gap' da grade e otimo real ou degeneracao numerica de R?
(a) mede cond(R) e sigma2 no argmax da grade; (b) conta as geracoes em que o fmincon
devolve theta == theta0 == 1 EXATO (single-start que nao andou); (c) refaz o gap so
sobre a regiao NAO-degenerada (cond(R) < 1e12).
"""
import json, itertools, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, ROOT)
from src import problems as PB
pr = PB.MMF1(); LB, UB = np.asarray(pr.xl, float), np.asarray(pr.xu, float)
CASES = {
    'T11_smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42',
    'R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42/exp_main_c238_MMF1_42',
}


def kern(theta, X):
    n = X.shape[0]; one = np.ones((n, 1))
    t1 = (X ** 2 * theta).sum(1)[:, None] @ one.T
    t2 = X * np.sqrt(theta)
    return np.exp(-(t1 + t1.T - 2 * (t2 @ t2.T))) + np.eye(n) * (10 + n) * np.finfo(float).eps


def lnL_full(theta, X, Y):
    n = X.shape[0]; one = np.ones((n, 1)); R = kern(theta, X)
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        return -1e8, np.inf, np.nan
    a = np.linalg.solve(L.T, np.linalg.solve(L, Y)); b = np.linalg.solve(L.T, np.linalg.solve(L, one))
    mu = float((one.T @ a).ravel()[0]) / float((one.T @ b).ravel()[0])
    r = Y - mu; c = np.linalg.solve(L.T, np.linalg.solve(L, r))
    s2 = float((r.T @ c).ravel()[0]) / n
    if not np.isfinite(s2) or s2 <= 0:
        return -1e8, np.inf, s2
    v = -0.5 * n * np.log(s2) - np.log(np.abs(np.diag(L))).sum()
    return v, float(np.linalg.cond(R)), s2


GRID = np.linspace(-3, 3, 25)
print('(b) o fmincon single-start ANDOU? (theta devolvido == theta0 == 1 EXATO)')
tab = []
for tag, b in CASES.items():
    recs = [json.loads(l) for l in open(f'{b}.jsonl')]
    gens = [r for r in recs if r.get('rec') == 'c238_gen']
    for j in range(2):
        n_par = sum(1 for r in gens if r['theta_min'][j] == 1.0 and r['theta_max'][j] == 1.0)
        n_teto = sum(1 for r in gens if max(r['theta_min'][j], r['theta_max'][j]) >= 1e3 * (1 - 1e-9))
        n_piso = sum(1 for r in gens if min(r['theta_min'][j], r['theta_max'][j]) <= 1e-3 * (1 + 1e-9))
        print('   %-10s obj%d: theta==theta0 EXATO em %2d/%d ; toca TETO 1e3 em %2d ; toca PISO 1e-3 em %2d'
              % (tag, j, n_par, len(gens), n_teto, n_piso))
        tab.append((tag, j, n_par, n_teto, n_piso, len(gens)))

print('\n(a)+(c) degeneracao de R no argmax da grade — 4 geracoes-amostra por run')
rows = []
for tag, b in CASES.items():
    recs = [json.loads(l) for l in open(f'{b}.jsonl')]
    gens = [r for r in recs if r.get('rec') == 'c238_gen']
    real = pq.read_table(f'{b}__real.parquet').to_pandas()
    Xall = real[['x0', 'x1']].to_numpy(np.float64); Fall = real[['f0', 'f1']].to_numpy(np.float64)
    for r in [gens[0], gens[9], gens[24], gens[-1]]:
        n = r['n_amostra']
        X = (Xall[:n] - LB) / (UB - LB)
        mn = np.array(r['norm_min']); rg = np.array(r['norm_range_efetivo'])
        Yn = (Fall[:n] - mn) / rg
        for j in range(2):
            Y = Yn[:, [j]]
            best = (-1e18, None, None, None); best_ok = (-1e18, None, None, None)
            for a1 in GRID:
                for a2 in GRID:
                    v, cnd, s2 = lnL_full(np.array([10 ** a1, 10 ** a2]), X, Y)
                    if v > best[0]:
                        best = (v, (a1, a2), cnd, s2)
                    if cnd < 1e12 and v > best_ok[0]:
                        best_ok = (v, (a1, a2), cnd, s2)
            pair = [r['theta_min'][j], r['theta_max'][j]]
            got = max(lnL_full(np.array(p, float), X, Y)[0] for p in set(itertools.permutations(pair)))
            cnd_log = lnL_full(np.array(pair, float), X, Y)[1]
            rows.append(dict(fonte=tag, g=r['geracao'], obj=j, n=n, lnL_log=r['lnL'][j], lnL_rec=got,
                             cond_log=cnd_log,
                             grid_max=best[0], grid_arg=best[1], grid_cond=best[2], grid_s2=best[3],
                             grid_ok=best_ok[0], grid_ok_arg=best_ok[1], grid_ok_cond=best_ok[2],
                             gap_bruto=best[0] - r['lnL'][j], gap_saudavel=best_ok[0] - r['lnL'][j]))
D = pd.DataFrame(rows)
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 30)
print(D[['fonte', 'g', 'obj', 'n', 'lnL_log', 'lnL_rec', 'cond_log', 'grid_max', 'grid_arg', 'grid_cond',
         'grid_s2', 'grid_ok', 'grid_ok_arg', 'grid_ok_cond', 'gap_bruto', 'gap_saudavel']].to_string(index=False))
D.to_csv(f'{ROOT}/f5/t11/baterias/c238/mle_sanidade.csv', index=False)
