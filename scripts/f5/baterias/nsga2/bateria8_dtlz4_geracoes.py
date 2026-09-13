#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 8 — (a) DTLZ4: recomputar f em float64 A PARTIR DO MESMO X da ① restaura o
n_front1 do ⑥ em TODAS as 13 gerações (prova de que o desvio é 100% do export D53);
(b) régua com o piso de ruído entre máquinas (O-18) aplicado.
"""
import json, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'


def nd_sort(F):
    n = len(F); fr = np.zeros(n, int); rest = np.arange(n); k = 1
    while len(rest):
        Fr = F[rest]; dom = np.zeros(len(rest), bool)
        for i in range(len(rest)):
            if np.any(np.all(Fr <= Fr[i], 1) & np.any(Fr < Fr[i], 1)):
                dom[i] = True
        fr[rest[~dom]] = k; rest = rest[dom]; k += 1
    return fr


def dtlz4(X, M=3, a=100.0):
    n = X.shape[1]; k = n - M + 1
    g = ((X[:, n - k:] - 0.5) ** 2).sum(1); Y = X[:, :M - 1] ** a
    F = np.empty((len(X), M))
    for i in range(M):
        v = (1.0 + g)
        for j in range(M - 1 - i):
            v = v * np.cos(Y[:, j] * np.pi / 2)
        if i > 0:
            v = v * np.sin(Y[:, M - 1 - i] * np.pi / 2)
        F[:, i] = v
    return F


b = f'{RAIZ}/resultados_experimentos/nsga2/DTLZ4/42/exp_main_nsga2_DTLZ4_42'
real = pq.read_table(b + '__real.parquet').to_pandas()
pop = pq.read_table(b + '__pop.parquet').to_pandas()
xc = [c for c in real.columns if re.fullmatch(r'x\d+', c)]
fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
F64 = dtlz4(real[xc].values.astype(np.float64))
m32 = real.set_index('solution_id')[fc]
m64 = {s: v for s, v in zip(real.solution_id, F64)}
gens = [x for x in [json.loads(l) for l in open(b + '.jsonl')] if x['rec'] == 'nsga2_gen']
rows = []
for i, (g, v) in enumerate(pop.groupby('geracao')):
    s = v.solution_id.tolist(); log = gens[i]['n_front1']
    a = int((nd_sort(m32.loc[s].values.astype(np.float64)) == 1).sum())
    c = int((nd_sort(np.array([m64[x] for x in s])) == 1).sum())
    rows.append(dict(geracao=g, log=log, nf1_f32=a, nf1_f64=c, ok32=a == log, ok64=c == log))
d = pd.DataFrame(rows); d.to_csv(f'{OUT}/dtlz4_geracoes.csv', index=False)
print(d.to_string())
print('DTLZ4: n_front1 bate com a ① float32 em %d/13 ; com f recomputado em float64 em %d/13'
      % (d.ok32.sum(), d.ok64.sum()))

print('\n=== (b) régua com o piso de ruído entre máquinas (O-18: IGD+ <= 58,98%) ===')
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv'); m = m[m.exp == 'main']
t = pd.read_csv(f'{F5}/tempo_f52d.csv'); t = t[t.exp == 'main']
maq = t.groupby('alg').maquina.agg(lambda s: '|'.join(sorted(set(s)))).to_dict()
piv = m.pivot_table(index='problema', columns='alg', values='igd_plus')
PIS = ['nsga2', 'nsga3', 'moead', 'smsemoa']
FLOOR = 1.5898
rows = []
for prob in piv.index:
    lin = piv.loc[prob].dropna()
    if 'nsga2' not in lin: continue
    v = lin['nsga2']
    sa = lin.drop([p for p in PIS if p in lin.index])
    rows.append(dict(problema=prob, igd_nsga2=v, n_SA=len(sa),
                     SA_bate_piso=int((sa < v).sum()),
                     SA_bate_piso_alem_do_ruido=int((sa < v / FLOOR).sum()),
                     SA_pior_que_piso=int((sa > v).sum()),
                     SA_pior_alem_do_ruido=int((sa > v * FLOOR).sum()),
                     SA_mesma_maquina_vm3=int(sum(1 for a in sa.index if maq.get(a) == 'vm3'))))
dr = pd.DataFrame(rows); dr.to_csv(f'{OUT}/regua_ruido_nsga2.csv', index=False)
pd.set_option('display.width', 300, 'display.max_columns', 40)
print(dr.to_string())
print('\nTOTAL comparações SA×nsga2 = %d · SA melhor = %d (%.1f%%) · SA melhor ALÉM do ruído = %d (%.1f%%)'
      % (dr.n_SA.sum(), dr.SA_bate_piso.sum(), 100 * dr.SA_bate_piso.sum() / dr.n_SA.sum(),
         dr.SA_bate_piso_alem_do_ruido.sum(), 100 * dr.SA_bate_piso_alem_do_ruido.sum() / dr.n_SA.sum()))
print('SA PIOR que o piso = %d (%.1f%%) · pior ALÉM do ruído = %d (%.1f%%)'
      % (dr.SA_pior_que_piso.sum(), 100 * dr.SA_pior_que_piso.sum() / dr.n_SA.sum(),
         dr.SA_pior_alem_do_ruido.sum(), 100 * dr.SA_pior_alem_do_ruido.sum() / dr.n_SA.sum()))
print('máquina por alg:', maq)
