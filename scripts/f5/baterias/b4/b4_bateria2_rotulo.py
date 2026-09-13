#!/usr/bin/env python
"""B4 - Bateria 2: prova da REGRA DE ROTULO (query-joia) + hipotese do empate float32.
Testa 5 regras candidatas contra o rr logado, em TODAS as geracoes das 25 celulas.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])

rows = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    real = pd.read_parquet(base + '__real.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet', columns=['regime', 'geracao', 'real_solution_id'])
    on = sur[sur.regime == 'online']
    fc = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    F = real[fc].to_numpy(np.float64)
    init = int((real.fase == 'init').sum())
    arc = np.array(list(range(init)) + [int(v) for v in on.real_solution_id.to_numpy()])
    for r in gens:
        nA = int(r['n_treino']); ids = arc[:nA]; Fa = F[ids]; R = F[np.array(r['ref_ids'], int)]
        n1log = int(round(r['rr'] * nA))
        le = np.ones(nA, bool); lt = np.ones(nA, bool)
        for j in range(len(R)):
            le &= (Fa <= R[j]).any(axis=1)
            lt &= (Fa < R[j]).any(axis=1)
        domw = np.zeros(nA, bool); doms = np.zeros(nA, bool); ndom = np.ones(nA, bool)
        for j in range(len(R)):
            domw |= (Fa <= R[j]).all(axis=1)
            doms |= ((Fa <= R[j]).all(axis=1) & (Fa < R[j]).any(axis=1))
            ndom &= ~(((R[j] <= Fa).all(axis=1)) & ((R[j] < Fa).any(axis=1)))
        rows.append(dict(problema=prob, geracao=r['geracao'], nA=nA, n1log=n1log,
                         n1_le=int(le.sum()), n1_lt=int(lt.sum()), n1_domw=int(domw.sum()),
                         n1_doms=int(doms.sum()), n1_ndom=int(ndom.sum()),
                         n_empate=int((le & ~lt).sum())))
    print('ok', prob)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/b4_regra_rotulo.csv', index=False)
tot = len(df)
print('\ngeracoes totais:', tot)
for c in ['n1_le', 'n1_lt', 'n1_domw', 'n1_doms', 'n1_ndom']:
    print(f'  regra {c:9s}: match exato {int((df[c]==df.n1log).sum())}/{tot} '
          f'({100*(df[c]==df.n1log).mean():.1f}%)')
sand = ((df.n1_lt <= df.n1log) & (df.n1log <= df.n1_le))
print('\nSANDUICHE n1_lt <= n1_log <= n1_le :', int(sand.sum()), '/', tot,
      f'({100*sand.mean():.2f}%)')
print('gerações fora do sanduiche:')
print(df[~sand].groupby('problema').size().to_string() if (~sand).any() else '  nenhuma')
print('\npor problema (match da regra <=, e do sanduiche):')
g = df.groupby('problema').apply(lambda d: pd.Series({
    'n_gen': len(d), 'match_le': int((d.n1_le == d.n1log).sum()),
    'sand': int(((d.n1_lt <= d.n1log) & (d.n1log <= d.n1_le)).sum()),
    'delta_le_med': float((d.n1_le - d.n1log).median()),
    'empate_med': float(d.n_empate.median()),
    'frac_n1log': float((d.n1log / d.nA).median())}), include_groups=False)
print(g.to_string())
