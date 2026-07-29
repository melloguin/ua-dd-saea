#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 5 — teste DECISIVO do float32-collapse (bracket) + fecho do relatório.
(J) bracket: front1_f32 <= n_front1(⑥,float64) <= front1_f32 + |S|, onde S = pontos cujos
    dominadores TODOS dependem de um empate EXATO em >=1 objetivo (i.e. relações que só
    existem porque o export D53 arredondou para float32).
(K) resumo agregado de todos os números do relatório.
"""
import json, os, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'
PROBS = [p for p in sorted(os.listdir(f'{DADOS}/nsga2')) if not p.startswith('.')]


def nd_sort(F):
    n = len(F); front = np.zeros(n, int); resto = np.arange(n); k = 1
    while len(resto):
        Fr = F[resto]; dom = np.zeros(len(resto), bool)
        for i in range(len(resto)):
            if np.any(np.all(Fr <= Fr[i], 1) & np.any(Fr < Fr[i], 1)):
                dom[i] = True
        front[resto[~dom]] = k; resto = resto[dom]; k += 1
    return front


rows = []
for prob in PROBS:
    b = f'{DADOS}/nsga2/{prob}/42/exp_main_nsga2_{prob}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl')]
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    real = pq.read_table(b + '__real.parquet').to_pandas()
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
    fmap = real.set_index('solution_id')[fc]
    gl = {g: v['solution_id'].tolist() for g, v in pop.groupby('geracao')}
    ok = 0; falhas = []
    for i, g in enumerate(sorted(gl)):
        F = fmap.loc[gl[g]].values.astype(np.float64)
        fr = nd_sort(F); f1 = int((fr == 1).sum()); log = gens[i]['n_front1']
        S = 0
        for j in np.where(fr >= 2)[0]:
            doms = np.where(np.all(F <= F[j], 1) & np.any(F < F[j], 1))[0]
            if len(doms) and all(np.any(F[d] == F[j]) for d in doms):
                S += 1
        if f1 <= log <= f1 + S:
            ok += 1
        else:
            falhas.append((g, f1, log, S))
    rows.append(dict(problema=prob, gers=len(gens), bracket_ok=ok,
                     falhas=len(falhas), det=str(falhas[:3])))
df = pd.DataFrame(rows); df.to_csv(f'{OUT}/prova_bracket_nsga2.csv', index=False)
pd.set_option('display.width', 300, 'display.max_columns', 60, 'display.max_colwidth', 70)
print(df.to_string())
print('\nTOTAL: gerações=%d · bracket fecha em %d (%.2f%%) · falhas=%d'
      % (df.gers.sum(), df.bracket_ok.sum(), 100 * df.bracket_ok.sum() / df.gers.sum(), df.falhas.sum()))
