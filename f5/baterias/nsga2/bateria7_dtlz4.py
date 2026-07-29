#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 7 — prova DECISIVA do DTLZ4: recomputar f em float64 a partir do X float64 do
artefato do DoE restaura a estrutura de dominância que o export float32 (D53) destruiu,
e reproduz BIT-A-BIT a seleção D88 logada pelo ⑥.
"""
import json, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = f'{RAIZ}/ua-dd-saea/f5/baterias/nsga2'
b = f'{RAIZ}/resultados_experimentos/nsga2/DTLZ4/42/exp_main_nsga2_DTLZ4_42'
doep = f'{RAIZ}/ua-dd-saea/data/doe/DTLZ4/doe_DTLZ4_42.parquet'


def nd_sort(F):
    n = len(F); front = np.zeros(n, int); resto = np.arange(n); k = 1
    while len(resto):
        Fr = F[resto]; dom = np.zeros(len(resto), bool)
        for i in range(len(resto)):
            if np.any(np.all(Fr <= Fr[i], 1) & np.any(Fr < Fr[i], 1)):
                dom[i] = True
        front[resto[~dom]] = k; resto = resto[dom]; k += 1
    return front


def crowding(F, front):
    n, M = F.shape; cd = np.zeros(n)
    for f in np.unique(front):
        idx = np.where(front == f)[0]; Fi = F[idx]; d = np.zeros(len(idx))
        for j in range(M):
            o = np.argsort(Fi[:, j], kind='stable')
            fmin, fmax = Fi[o[0], j], Fi[o[-1], j]
            d[o[0]] = np.inf; d[o[-1]] = np.inf
            if fmax - fmin > 0 and len(idx) > 2:
                d[o[1:-1]] += (Fi[o[2:], j] - Fi[o[:-2], j]) / (fmax - fmin)
        cd[idx] = d
    return cd


def dtlz4(X, M=3, alpha=100.0):
    n = X.shape[1]; k = n - M + 1
    g = ((X[:, n - k:] - 0.5) ** 2).sum(1)
    Y = X[:, :M - 1] ** alpha
    F = np.empty((len(X), M))
    for i in range(M):
        v = (1.0 + g)
        for j in range(M - 1 - i):
            v = v * np.cos(Y[:, j] * np.pi / 2)
        if i > 0:
            v = v * np.sin(Y[:, M - 1 - i] * np.pi / 2)
        F[:, i] = v
    return F


doe = pq.read_table(doep).to_pandas()
dxc = [c for c in doe.columns if re.fullmatch(r'x\d+', c)]
X64 = doe[dxc].values.astype(np.float64)
real = pq.read_table(b + '__real.parquet').to_pandas()
pop = pq.read_table(b + '__pop.parquet').to_pandas()
fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
ini = real[real.fase == 'init']
F32 = ini[fc].values                      # float32 gravado na ①
F64 = dtlz4(X64)                          # recomputo em float64

print('validação da fórmula: max|float32(F64) − F32| = %.3e ; iguais bit-a-bit em %d/%d valores'
      % (np.abs(F64.astype(np.float32) - F32).max(),
         int((F64.astype(np.float32) == F32).sum()), F32.size))
print('menor |f| não-nulo em float64 = %.3e  → abaixo do menor normal float32 (1,18e-38) em %d valores'
      % (np.abs(F64[F64 != 0]).min(), int((np.abs(F64) < 1.18e-38).sum())))
print('zeros EXATOS: float64 = %d ; float32 (①) = %d  → o export criou %d zeros'
      % (int((F64 == 0).sum()), int((F32 == 0).sum()), int((F32 == 0).sum() - (F64 == 0).sum())))

fr64 = nd_sort(F64); fr32 = nd_sort(F32.astype(np.float64))
recs = [json.loads(l) for l in open(b + '.jsonl')]
sr = [x for x in recs if x['rec'] == 'seeding'][0]
print('\n            n_frentes  n_frente1')
print('  ⑥ (MATLAB float64):  %2d        %2d' % (sr['n_frentes'], sr['n_frente1']))
print('  recomputo float64 :  %2d        %2d   %s' %
      (fr64.max(), (fr64 == 1).sum(),
       'IDÊNTICO' if (fr64.max() == sr['n_frentes'] and (fr64 == 1).sum() == sr['n_frente1']) else 'DIFERE'))
print('  recomputo float32 :  %2d        %2d   (a ① perdeu a informação)' % (fr32.max(), (fr32 == 1).sum()))

cd = crowding(F64, fr64)
ordem = np.lexsort((np.arange(len(F64)), -cd, fr64))
sel = np.sort(ordem[:20])
sid = ini['solution_id'].values
sel_sids = set(sid[sel].tolist())
g1 = set(pop.loc[pop.geracao == pop.geracao.min(), 'solution_id'].tolist())
print('\nseleção D88 (NDSort+crowding, desempate por índice) recomputada em float64:')
print('  |seleção ∩ ②(g=1)| = %d/20   → %s' % (len(sel_sids & g1),
      'BIT-A-BIT' if sel_sids == g1 else 'DIVERGE: ' + str(sorted(sel_sids ^ g1))))
self32 = np.sort(np.lexsort((np.arange(len(F32)), -crowding(F32.astype(np.float64), fr32),
                             fr32))[:20])
print('  (a mesma seleção sobre a ① float32 acertaria só %d/20)'
      % len(set(sid[self32].tolist()) & g1))
pd.DataFrame(dict(solution_id=sid, front64=fr64, cd64=cd, front32=fr32,
                  sel64=[s in sel_sids for s in sid], pop_g1=[s in g1 for s in sid])
             ).to_csv(f'{OUT}/dtlz4_float64_vs_float32.csv', index=False)
