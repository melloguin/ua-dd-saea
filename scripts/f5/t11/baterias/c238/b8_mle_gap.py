#!/usr/bin/env python
"""B8 — o GAP do MLE single-start, geracao a geracao: lnL logada x maximo de uma grade
13x13 em log10(theta) sobre a caixa legal [1e-3,1e3]^2, no MESMO conjunto de treino.
Quantifica o efeito de `fmincon sqp single-start MaxFunEvals=20D` (bundle: 'sujeito a
otimo local') contra o `boxmin` do DACE que o paper usa.
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


def lnL(theta, X, Y):
    n = X.shape[0]; one = np.ones((n, 1))
    t1 = (X ** 2 * theta).sum(1)[:, None] @ one.T
    t2 = X * np.sqrt(theta)
    R = np.exp(-(t1 + t1.T - 2 * (t2 @ t2.T))) + np.eye(n) * (10 + n) * np.finfo(float).eps
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        return -1e8
    a = np.linalg.solve(L.T, np.linalg.solve(L, Y)); b = np.linalg.solve(L.T, np.linalg.solve(L, one))
    mu = float((one.T @ a).ravel()[0]) / float((one.T @ b).ravel()[0])
    r = Y - mu; c = np.linalg.solve(L.T, np.linalg.solve(L, r))
    s2 = float((r.T @ c).ravel()[0]) / n
    if not np.isfinite(s2) or s2 <= 0:
        return -1e8
    return -0.5 * n * np.log(s2) - np.log(np.abs(np.diag(L))).sum()


GRID = np.linspace(-3, 3, 25)
rows = []
for tag, b in CASES.items():
    recs = [json.loads(l) for l in open(f'{b}.jsonl')]
    gens = [r for r in recs if r.get('rec') == 'c238_gen']
    real = pq.read_table(f'{b}__real.parquet').to_pandas()
    Xall = real[['x0', 'x1']].to_numpy(np.float64); Fall = real[['f0', 'f1']].to_numpy(np.float64)
    for r in gens:
        n = r['n_amostra']
        X = (Xall[:n] - LB) / (UB - LB)
        mn = np.array(r['norm_min']); rg = np.array(r['norm_range_efetivo'])
        Yn = (Fall[:n] - mn) / rg
        for j in range(2):
            Y = Yn[:, [j]]
            # lnL no theta logado (par exato para D=2: {theta_min, theta_max})
            pair = [r['theta_min'][j], r['theta_max'][j]]
            cand = [lnL(np.array(p, float), X, Y) for p in set(itertools.permutations(pair))]
            got = min(cand, key=lambda v: abs(v - r['lnL'][j]))
            best = -1e18; barg = None
            for a1 in GRID:
                for a2 in GRID:
                    v = lnL(np.array([10 ** a1, 10 ** a2]), X, Y)
                    if v > best:
                        best, barg = v, (a1, a2)
            rows.append(dict(fonte=tag, geracao=r['geracao'], obj=j, n=n,
                             lnL_log=r['lnL'][j], lnL_rec=got, err_rec=abs(got - r['lnL'][j]),
                             lnL_grid=best, gap=best - r['lnL'][j],
                             log10th_grid1=barg[0], log10th_grid2=barg[1],
                             th_min=r['theta_min'][j], th_max=r['theta_max'][j],
                             sat_piso=int(min(pair) <= 1e-3 * 1.000001),
                             sat_teto=int(max(pair) >= 1e3 * 0.999999)))
D = pd.DataFrame(rows)
D.to_csv(f'{ROOT}/f5/t11/baterias/c238/mle_gap.csv', index=False)
pd.set_option('display.width', 220)
print('reproducao da lnL (erro do meu recomputo vs o log): max=%.3g mediana=%.3g' % (D.err_rec.max(), D.err_rec.median()))
print()
for tag in CASES:
    d = D[D.fonte == tag]
    print('### %s' % tag)
    for j in range(2):
        s = d[d.obj == j]
        print('  obj%d: gap(grade-log) mediana=%.3f  min=%.3f  max=%.3f  ; gap>1 nat em %d/%d ; gap>10 nats em %d/%d'
              % (j, s.gap.median(), s.gap.min(), s.gap.max(),
                 int((s.gap > 1).sum()), len(s), int((s.gap > 10).sum()), len(s)))
        print('        theta logado: saturado no TETO 1e3 em %d/%d ; no PISO 1e-3 em %d/%d ; theta_media final=%.4g'
              % (s.sat_teto.sum(), len(s), s.sat_piso.sum(), len(s), (s.th_min.iloc[-1] + s.th_max.iloc[-1]) / 2))
        print('        argmax da GRADE (log10 theta) mediana = (%.2f, %.2f)'
              % (s.log10th_grid1.median(), s.log10th_grid2.median()))
        print('        lnL logada: %.3f -> %.3f (max da trajetoria %.3f)' % (s.lnL_log.iloc[0], s.lnL_log.iloc[-1], s.lnL_log.max()))
    print()
