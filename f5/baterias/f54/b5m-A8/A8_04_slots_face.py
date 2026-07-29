#!/usr/bin/env python
"""F5.4 / b5m-A8 — TESTE ESTRUTURAL DOS SLOTS MORTOS (a prediccao mais dura).

Se o congelamento vem de `ReferenceVectors.adapt` zerando linhas de `values`
(porque a amplitude da fitness e 0 nos objetivos J), entao o conjunto de slots
que MORREM (nunca mais mudam, enquanto o resto da populacao segue mudando) tem
de ser EXATAMENTE uma FACE do lattice:

        S = { i : suporte(v_i) contido em J }

Isso e falsificavel e sem parametro livre: tomo J* = uniao dos suportes dos
vetores mortos e exijo S == {i : supp(v_i) ⊆ J*}. Com M=3 ha so 2^3-1 = 7 faces
possiveis entre 105 vetores; acertar por acaso e improvavel.

Controle negativo: celulas sem degeneracao nao podem ter slot morto isolado.
Roda em b5m E no piso moead_media (que usa o MESMO adapt com selecao por media).
"""
import glob, json, os
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A8'


def lattice(H, M):
    nv = comb(H + M - 1, M - 1)
    t1 = np.array(list(combinations(range(1, M + H), M - 1)))
    t2 = np.array([list(range(M - 1))] * nv)
    t = t1 - t2 - 1
    w = np.zeros((nv, M), dtype=int)
    w[:, 0] = t[:, 0]
    for i in range(1, M - 1):
        w[:, i] = t[:, i] - t[:, i - 1]
    w[:, -1] = H - t[:, -1]
    return w / H


LAT = {2: lattice(49, 2), 3: lattice(13, 3)}
rows = []
labs = sorted(os.path.basename(os.path.dirname(d))
              for d in glob.glob(os.path.join(RES, 'b5m', '*', '42')))
for alg in ('b5m', 'moead_media'):
    for lab in labs:
        d = os.path.join(RES, alg, lab, '42')
        js = glob.glob(d + '/*.jsonl')
        if not js:
            continue
        st = js[0][:-6]
        h = json.loads(open(st + '.jsonl').readline())
        D, M = h['D'], h['M']
        b = pd.read_parquet(st + '__surrogate.parquet')
        b = b[b.regime == 'offline']
        n = int(b.geracao.max()); pop = len(b) // n
        X = b[['x%d' % i for i in range(D)]].values.reshape(n, pop, D)
        MU = b[['mu_%d' % j for j in range(M)]].values.astype(np.float64).reshape(n, pop, M)
        chg = (X[1:] != X[:-1]).any(axis=2)                # (n-1, pop)
        vivos = chg.any(axis=1)
        onset = int(np.nonzero(vivos)[0][-1]) + 2 if vivos.any() else 1
        # slots mortos = nunca mudam ANTES do congelamento geral (janela util)
        jan = chg[:onset - 1] if onset > 1 else chg[:0]
        mortos = np.where(~jan.any(axis=0))[0] if jan.shape[0] else np.arange(pop)
        V = LAT[M]
        if len(mortos) and len(mortos) < pop:
            Jstar = sorted(set(np.where(V[mortos] > 0)[1].tolist()))
            face = np.where((V[:, [j for j in range(M) if j not in Jstar]] == 0).all(axis=1))[0]
            bate = set(face.tolist()) == set(mortos.tolist())
        else:
            Jstar, face, bate = None, np.array([]), None
        amp = MU.max(axis=1) - MU.min(axis=1)
        rows.append(dict(alg=alg, label=lab, M=M, pop=pop, n_ger=n, onset=onset,
                         congeladas_trans=n - onset,
                         n_mortos=len(mortos), mortos=str(mortos.tolist()[:16]),
                         J_star=str(Jstar), n_face=len(face), face_bate=bate,
                         amp_zero_em_alguma_ger=int((amp == 0).all(axis=1).sum()),
                         amp_min_global=float(amp.sum(axis=1).min())))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'A8_slots_face.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
sel = df[(df.n_mortos > 0) & (df.n_mortos < df['pop'])]
print('==== celulas com SLOTS MORTOS isolados (degeneracao PARCIAL) ====')
print(sel[['alg', 'label', 'M', 'onset', 'congeladas_trans', 'n_mortos',
           'mortos', 'J_star', 'n_face', 'face_bate']].to_string())
print('\nface_bate: %d/%d' % (int(sel.face_bate.sum()), len(sel)))
print('\n==== congelamento TOTAL (todos os slots) ====')
tot = df[df.n_mortos == df['pop']]
print(tot[['alg', 'label', 'onset', 'congeladas_trans',
           'amp_zero_em_alguma_ger']].to_string())
print('\n==== b5m: transicoes congeladas por celula (terminal) ====')
d5 = df[(df.alg == 'b5m') & (df.congeladas_trans > 0)]
print(d5[['label', 'n_ger', 'onset', 'congeladas_trans',
          'amp_zero_em_alguma_ger', 'amp_min_global']].to_string())
print('TOTAL transicoes congeladas b5m = %d de %d transicoes (%d celulas)'
      % (df[df.alg == 'b5m'].congeladas_trans.sum(),
         (df[df.alg == 'b5m'].n_ger - 1).sum(), len(d5)))
print('TOTAL geracoes arquivadas b5m = %d' % df[df.alg == 'b5m'].n_ger.sum())
print('\nTOTAL transicoes congeladas piso = %d (%d celulas)'
      % (df[df.alg == 'moead_media'].congeladas_trans.sum(),
         int((df[df.alg == 'moead_media'].congeladas_trans > 0).sum())))
