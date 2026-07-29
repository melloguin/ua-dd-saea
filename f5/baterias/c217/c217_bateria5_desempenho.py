#!/usr/bin/env python
"""BATERIA 5 — desempenho: trajetórias (20 checkpoints), posição vs pisos, rank no main,
tempo/máquina, comparação canônica (ordem intra-família DTLZ/WFG)."""
import os, json, glob
import numpy as np, pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/c217'
M = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
main = M[M.exp == 'main']
probs = sorted(main[main.alg == 'c217'].problema.unique())
PISOS = ['moead', 'nsga2', 'nsga3', 'smsemoa']

print('=== 1. TRAJETÓRIAS (20 checkpoints) ===')
rows = []
for p in probs:
    j = json.load(open(f'{F5}/trajetorias/main_c217_{p}_42.json'))
    v = np.array([c['igd_plus'] for c in j], dtype=float)
    d = np.diff(v)
    rows.append(dict(problema=p, n=len(v), viol=int((d > 1e-12).sum()), v0=v[0], vf=v[-1],
                     razao=v[-1] / v[0] if v[0] > 0 else np.nan))
TR = pd.DataFrame(rows); TR.to_csv(f'{OUT}/c217_trajetorias.csv', index=False)
print(TR.to_string())
print('transições:', int((TR.n - 1).sum()), '| violações:', int(TR.viol.sum()))
print('razão vf/v0: mediana %.4f  melhor %.4f (%s)  pior %.4f (%s)' %
      (TR.razao.median(), TR.razao.min(), TR.loc[TR.razao.idxmin(), 'problema'],
       TR.razao.max(), TR.loc[TR.razao.idxmax(), 'problema']))

print()
print('=== 2. POSIÇÃO vs PISOS e RANK no main (IGD+) ===')
rows = []
for p in probs:
    sub = main[main.problema == p]
    me = sub[sub.alg == 'c217'].igd_plus.iloc[0]
    pis = sub[sub.alg.isin(PISOS)][['alg', 'igd_plus']]
    best = pis.igd_plus.min()
    rk = sub.sort_values('igd_plus').reset_index(drop=True)
    rank = int(rk[rk.alg == 'c217'].index[0]) + 1
    rows.append(dict(problema=p, igdp=me, melhor_piso=best, piso_alg=pis.loc[pis.igd_plus.idxmin(), 'alg'],
                     razao=me / best, rank=rank, n_algs=len(sub),
                     hv=sub[sub.alg == 'c217'].hv.iloc[0], n_nd=sub[sub.alg == 'c217'].n_nd.iloc[0]))
V = pd.DataFrame(rows); V.to_csv(f'{OUT}/c217_vs_pisos.csv', index=False)
print(V.to_string())
print('bate o melhor piso (razão<1):', int((V.razao < 1).sum()), '/25')
print('dentro do piso de ruído IGD+ (razão<=1.5898):', int(((V.razao >= 1) & (V.razao <= 1.5898)).sum()))
print('claramente abaixo (razão>1.5898):', int((V.razao > 1.5898).sum()))
print('rank médio %.2f / %d' % (V['rank'].mean(), V.n_algs.iloc[0]))

print()
print('=== 3. TEMPO / MÁQUINA ===')
T = pd.read_csv(f'{F5}/tempo_f52d.csv')
t = T[(T.alg == 'c217')] if 'alg' in T.columns else T
print(t.columns.tolist())
tt = t[t.exp == 'main'] if 'exp' in t.columns else t
print(tt.to_string())

print()
print('=== 4. CANÔNICA — ordem intra-família ===')
paper_dtlz_m3 = {'DTLZ1': 2.9867e+1, 'DTLZ2': 6.9212e-2, 'DTLZ3': 6.7647e+1, 'DTLZ4': 7.8816e-2, 'DTLZ7': 1.9200e-1}
paper_wfg_m2 = {'WFG1': 1.1225e+0, 'WFG2': 1.9643e-1, 'WFG4': 8.9525e-2, 'WFG5': 1.1186e-2, 'WFG9': 1.3327e-1}
for nome, d in [('DTLZ m=3 d=15 (Tab.1)', paper_dtlz_m3), ('WFG m=2 d=21 (Tab.2)', paper_wfg_m2)]:
    ours = {k: float(main[(main.alg == 'c217') & (main.problema == k)].igd_plus.iloc[0]) for k in d}
    pp = sorted(d, key=d.get); oo = sorted(ours, key=ours.get)
    print(f'\n{nome}')
    print('  paper :', [(k, f'{d[k]:.4g}') for k in pp])
    print('  nosso :', [(k, f'{ours[k]:.4g}') for k in oo])
    print('  posições idênticas:', sum(1 for i, k in enumerate(pp) if oo[i] == k), '/', len(d))
    from scipy.stats import spearmanr
    print('  Spearman(rank paper, rank nosso) =', spearmanr([d[k] for k in d], [ours[k] for k in d]).statistic)
