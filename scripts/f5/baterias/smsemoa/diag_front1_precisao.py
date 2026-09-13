#!/usr/bin/env python
"""Dissecacao do desvio n_front1 (log MATLAB float64 x recomputo sobre a (1) float32).
Hipotese: o export float32 (D53) cria EMPATES exatos em coordenadas que em float64 eram
estritamente diferentes; empate em 1 coordenada torna o par COMPARAVEL -> frente-1 encolhe.
Teste: nd_sort 'fragil' (dominancia fraca, o que MATLAB faz nos numeros float64 sem empate)
x nd_sort 'estrito' (empate em qualquer coordenada => incomparavel) — o log deve ficar
ENTRE os dois, e o estrito deve RECUPERAR o valor logado."""
import json, os, glob, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bateria_smsemoa import nd_sort, load_cell

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/smsemoa'
OUT = os.path.dirname(os.path.abspath(__file__))
PROBS = sorted(os.path.basename(p) for p in glob.glob(ROOT + '/*') if os.path.isdir(p))


def front1_strict(F):
    """Frente-1 sob dominancia ESTRITA (j domina i sse f_j < f_i em TODAS as coords)."""
    n = F.shape[0]
    dom = np.zeros(n, dtype=bool)
    for i in range(n):
        dom[i] = np.any(np.all(F < F[i], axis=1))
    return int((~dom).sum())


def front1_weak(F):
    return int((nd_sort(F) == 1).sum())


def pares_com_empate(F):
    n = F.shape[0]
    c = 0
    for i in range(n):
        for j in range(i + 1, n):
            if np.any(F[i] == F[j]):
                c += 1
    return c


rows = []
for p in PROBS:
    man, recs, real, pop, sur, tim = load_cell(p)
    gens = [x for x in recs if x.get('rec') == 'smsemoa_gen']
    fcols = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))
    F = real[fcols].values.astype(np.float64)
    popmap = {int(g): np.array(v.tolist()) for g, v in pop.groupby('geracao')['solution_id']}
    for g in gens:
        Fp = F[popmap[g['geracao']]]
        w = front1_weak(Fp)
        s = front1_strict(Fp)
        log = int(g['n_front1'])
        # quantos valores de coordenada aparecem repetidos na populacao
        emp = sum(len(Fp[:, k]) - len(np.unique(Fp[:, k])) for k in range(Fp.shape[1]))
        rows.append(dict(problema=p, geracao=g['geracao'], log=log, fraco=w, estrito=s,
                         entre=bool(w <= log <= s), estrito_bate=bool(s == log),
                         fraco_bate=bool(w == log), coord_repetidas=emp,
                         pares_empate=pares_com_empate(Fp)))
df = pd.DataFrame(rows)
df.to_csv(OUT + '/diag_front1_precisao.csv', index=False)
print('geracoes:', len(df))
print('fraco == log :', int(df.fraco_bate.sum()))
print('estrito == log:', int(df.estrito_bate.sum()))
print('log dentro de [fraco, estrito]:', int(df.entre.sum()))
print()
sub = df[~df.fraco_bate]
print('--- as', len(sub), 'geracoes divergentes no criterio fraco ---')
print(sub.to_string(index=False))
print()
print('coord repetidas (media por geracao) nas divergentes:', sub.coord_repetidas.mean(),
      '| nas concordantes:', df[df.fraco_bate].coord_repetidas.mean())
