#!/usr/bin/env python
"""BATERIA b5m #6 — QUERY-JOIA ESTRUTURAL: a VIZINHANCA do MOEA/D nos dados.

O ProbMOEAD substitui, para CADA offspring, apenas indices dentro da vizinhanca
do subproblema i (`self.neighborhoods[i,:]` = os 20 vetores de referencia mais
proximos, calculados 1x no __init__ sobre o lattice Das-Dennis NAO adaptado).
Se isso e verdade, entao: em qualquer transicao de geracao, o conjunto de SLOTS
que passaram a conter um MESMO X novo tem de caber DENTRO de uma unica
vizinhanca de 20.

Aqui reconstruimos o lattice (simplex-lattice do ReferenceVectors._create,
lattice_res_options=[49,13,...]) e as vizinhancas EXATAMENTE como o codigo
vendorizado, e testamos a contencao em TODAS as transicoes de TODAS as celulas.

Saida: b5m_vizinhanca.csv
"""
import glob, itertools, json, os, sys
import numpy as np, pandas as pd
from scipy.special import comb
from scipy.spatial import distance_matrix

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b5m'
LATT = [49, 13, 7, 5, 4, 3, 3, 3, 3]
N_NEIGH = 20


def ref_vectors(M):
    lr = LATT[M - 2]
    nv = int(comb(lr + M - 1, M - 1, exact=True))
    t1 = np.array(list(itertools.combinations(range(1, M + lr), M - 1)))
    t2 = np.array([range(M - 1)] * nv)
    t = t1 - t2 - 1
    w = np.zeros((nv, M), dtype=int)
    w[:, 0] = t[:, 0]
    for i in range(1, M - 1):
        w[:, i] = t[:, i] - t[:, i - 1]
    w[:, -1] = lr - t[:, -1]
    V = w / lr
    n2 = np.linalg.norm(V, axis=1)
    n2[n2 == 0] = np.finfo(float).eps
    return V / n2[:, None], nv


rows = []
labs = [os.path.basename(os.path.dirname(d))
        for d in sorted(glob.glob(os.path.join(RES, 'b5m', '*', '42')))]
for lab in labs:
    st = glob.glob(os.path.join(RES, 'b5m', lab, '42', '*.jsonl'))[0][:-6]
    h = json.loads(open(st + '.jsonl').readline())
    D, M = h['D'], h['M']
    V, nv = ref_vectors(M)
    NB = np.argsort(distance_matrix(V, V), axis=1, kind='quicksort')[:, :N_NEIGH]
    nbsets = [frozenset(r.tolist()) for r in NB]
    c3 = pd.read_parquet(st + '__surrogate.parquet')
    b = c3[c3.regime == 'offline']
    n = int(b.geracao.max()); pop = len(b) // n
    X = b[[f'x{i}' for i in range(D)]].values.reshape(n, pop, D)
    grupos = ok = falha = maxsz = 0
    tam = []
    for g in range(1, n):
        ch = np.nonzero((X[g] != X[g - 1]).any(axis=1))[0]
        if len(ch) == 0:
            continue
        # agrupa os slots que passaram a conter o MESMO X (mesmo offspring)
        vals, inv = np.unique(X[g][ch], axis=0, return_inverse=True)
        for k in range(len(vals)):
            sl = set(ch[inv == k].tolist())
            grupos += 1
            tam.append(len(sl))
            maxsz = max(maxsz, len(sl))
            if any(sl <= s for s in nbsets):
                ok += 1
            else:
                falha += 1
    rows.append(dict(label=lab, M=M, pop=pop, n_vetores=nv, n_ger=n,
                     grupos=grupos, contidos=ok, fora=falha,
                     tam_max=maxsz, tam_medio=float(np.mean(tam)) if tam else 0.0,
                     tam_p95=float(np.percentile(tam, 95)) if tam else 0.0,
                     grupos_multi=int(sum(1 for t in tam if t > 1))))
    print('%-26s vetores=%3d grupos=%7d contidos=%7d fora=%d tam_max=%d tam_med=%.2f'
          % (lab, nv, grupos, ok, falha, maxsz, rows[-1]['tam_medio']), flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b5m_vizinhanca.csv'), index=False)
print()
print('TOTAL grupos de substituicao:', int(df.grupos.sum()))
print('contidos numa unica vizinhanca de 20:', int(df.contidos.sum()),
      '(%.4f%%)' % (100 * df.contidos.sum() / max(1, df.grupos.sum())))
print('fora:', int(df.fora.sum()))
print('tamanho maximo de grupo observado:', int(df.tam_max.max()), '(teto = n_neighbors = 20)')
print('grupos com >1 slot (substituicao multi-vizinho):', int(df.grupos_multi.sum()),
      '(%.2f%%)' % (100 * df.grupos_multi.sum() / max(1, df.grupos.sum())))
print('celulas 100%% contidas:', int((df.fora == 0).sum()), '/', len(df))
print('pop == n_vetores:', int((df['pop'] == df.n_vetores).sum()), '/', len(df))
