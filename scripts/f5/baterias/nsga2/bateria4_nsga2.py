#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 4 — fechamento da prova do float32-collapse + contexto de máquina/tempo/pisos.
(F) NDSort com dominância SEM-EMPATE: se o colapso float32 é a causa única do desvio de
    n_front1, ignorar as relações de dominância que dependem de um empate EXATO deve
    RESTAURAR o n_front1 logado pelo ⑥ (float64) em 100% das gerações;
(G) o caso +1 do MMF4 (o par X duplicado sobe o n_front1 recomputado);
(H) máquinas/tempo dos 4 pisos (piso de ruído O-18) e custo;
(I) monotonia do ideal por objetivo em TODAS as transições + estagnação.
"""
import json, os, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'
CARACT = pd.read_csv(f'{RAIZ}/ua-dd-saea/claude_code_context/artifacts/characteristics.csv').set_index('problema')
PROBS = [p for p in sorted(os.listdir(f'{DADOS}/nsga2')) if not p.startswith('.')]


def nd_sort(F, sem_empate=False):
    n = len(F); front = np.zeros(n, int); resto = np.arange(n); k = 1
    while len(resto):
        Fr = F[resto]; dom = np.zeros(len(resto), bool)
        for i in range(len(resto)):
            le = np.all(Fr <= Fr[i], 1); lt = np.any(Fr < Fr[i], 1)
            cand = le & lt
            if sem_empate:
                # descarta dominações que só existem por um empate EXATO (candidatas a
                # artefato do arredondamento float32 do export D53)
                cand = cand & ~np.any(Fr == Fr[i], 1)
            if np.any(cand):
                dom[i] = True
        front[resto[~dom]] = k; resto = resto[dom]; k += 1
    return front


print('=== (F) NDSort sem-empate restaura o n_front1 do ⑥ ? ===')
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
    eq_std = eq_se = 0; delta_se = []
    for i, g in enumerate(sorted(gl)):
        F = fmap.loc[gl[g]].values.astype(np.float64)
        log = gens[i]['n_front1']
        a = int((nd_sort(F) == 1).sum()); c = int((nd_sort(F, True) == 1).sum())
        eq_std += (a == log); eq_se += (c == log); delta_se.append(c - log)
    rows.append(dict(problema=prob, gers=len(gens), nf1_std_eq=eq_std, nf1_semempate_eq=eq_se,
                     se_delta_min=min(delta_se), se_delta_max=max(delta_se),
                     se_enquadra=all(d >= 0 for d in delta_se)))
dfF = pd.DataFrame(rows); dfF.to_csv(f'{OUT}/prova_semempate_nsga2.csv', index=False)
pd.set_option('display.width', 300, 'display.max_columns', 60)
print(dfF.to_string())
print('TOTAIS: gerações=%d · igual com NDSort padrão=%d (%.1f%%) · igual ignorando empates=%d (%.1f%%)'
      % (dfF.gers.sum(), dfF.nf1_std_eq.sum(), 100 * dfF.nf1_std_eq.sum() / dfF.gers.sum(),
         dfF.nf1_semempate_eq.sum(), 100 * dfF.nf1_semempate_eq.sum() / dfF.gers.sum()))

print('\n=== (G) MMF4: o par duplicado e a geração com +1 ===')
b = f'{DADOS}/nsga2/MMF4/42/exp_main_nsga2_MMF4_42'
real = pq.read_table(b + '__real.parquet').to_pandas()
pop = pq.read_table(b + '__pop.parquet').to_pandas()
fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
fmap = real.set_index('solution_id')[fc]
recs = [json.loads(l) for l in open(b + '.jsonl')]
gens = [x for x in recs if x['rec'] == 'nsga2_gen']
for i, (g, v) in enumerate(pop.groupby('geracao')):
    sids = v['solution_id'].tolist()
    F = fmap.loc[sids].values.astype(np.float64)
    print('  ger %d: log=%d recomp=%d  contém {19,30}? %s' %
          (g, gens[i]['n_front1'], int((nd_sort(F) == 1).sum()), {19, 30}.issubset(set(sids))))

print('\n=== (H) máquinas e tempo dos 4 pisos ===')
t = pd.read_csv(f'{F5}/tempo_f52d.csv')
tp = t[(t.exp == 'main') & (t.alg.isin(['nsga2', 'nsga3', 'moead', 'smsemoa']))]
print(tp.groupby('alg').agg(celulas=('wall_s', 'size'), maquinas=('maquina', lambda s: '|'.join(sorted(set(s)))),
                            wall_med=('wall_s', 'median'), wall_soma=('wall_s', 'sum')).to_string())
print('\ntotal main de TODOS os algs (h-core): %.2f · nsga2: %.4f h-core (%.3f%%)'
      % (t[t.exp == 'main'].wall_s.sum() / 3600, tp[tp.alg == 'nsga2'].wall_s.sum() / 3600,
         100 * tp[tp.alg == 'nsga2'].wall_s.sum() / t[t.exp == 'main'].wall_s.sum()))
tm = t[t.exp == 'main']
print('máquina de cada alg no main:'); print(tm.groupby('alg').maquina.agg(lambda s: '|'.join(sorted(set(s)))).to_string())

print('\n=== (I) monotonia do ideal e estagnação ===')
rows = []
for prob in PROBS:
    b = f'{DADOS}/nsga2/{prob}/42/exp_main_nsga2_{prob}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl')]
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    I = np.array([g['ideal'] for g in gens], float)
    d = np.diff(I, axis=0)
    M = I.shape[1]
    rows.append(dict(problema=prob, M=M, transicoes=d.shape[0] * M,
                     viol=int((d > 0).sum()), estagnadas=int((d == 0).sum()),
                     melhoras=int((d < 0).sum()),
                     frac_estag=float((d == 0).mean())))
dfI = pd.DataFrame(rows); dfI.to_csv(f'{OUT}/monotonia_ideal_nsga2.csv', index=False)
print(dfI.to_string())
print('TOTAL transições(ger×obj)=%d · violações=%d · estagnadas=%d (%.1f%%) · melhoras=%d'
      % (dfI.transicoes.sum(), dfI.viol.sum(), dfI.estagnadas.sum(),
         100 * dfI.estagnadas.sum() / dfI.transicoes.sum(), dfI.melhoras.sum()))
