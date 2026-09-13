#!/usr/bin/env python
"""Parte 4 — as CORRECOES da T11 no `moead`, medidas.

(a) smoke T11 x s42 da MESMA celula (main/moead/DTLZ2/42): identidade das 4
    camadas + do ⑥ modulo ts  -> prova de NAO-PERTURBACAO (o moead nao tem par G-6).
(b) gates de proveniencia nas 25 celulas s42 (modo campanha) x o smoke.
(c) D88 com a regra EXATA do MATLAB (sortrows[FrontNo,-CrowdDis,idx]).
(d) a flag `frente1_excede_pop` nos 4 pisos (N_nominal x N_efetivo).
READ-ONLY. Nada e escrito fora desta pasta (o shadow-root e symlink em tempdir).
"""
import json, os, sys, subprocess, tempfile
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
SMOKE = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab'
OUT = f'{REPO}/f5/t11/baterias/moead'
sys.path.insert(0, REPO)
sys.path.insert(0, f'{REPO}/scripts')

# ── (a) smoke x s42, mesma celula ────────────────────────────────────────────
A = f'{SMOKE}/experiments/main/moead/exp_main_moead_DTLZ2_42'
B = f'{RES}/moead/DTLZ2/42/exp_main_moead_DTLZ2_42'
print('=== (a) smoke T11 x s42 — main/moead/DTLZ2/42')
for lay in ['real', 'pop', 'surrogate', 'timing']:
    a = pd.read_parquet(A + f'__{lay}.parquet')
    b = pd.read_parquet(B + f'__{lay}.parquet')
    ig = []
    for c in a.columns:
        if a[c].dtype.kind in 'fiub':
            ig.append(bool(np.array_equal(a[c].values, b[c].values, equal_nan=True)))
        else:
            ig.append(bool((a[c].astype(str) == b[c].astype(str)).all()))
    print(f'  {lay:10s} smoke{a.shape} s42{b.shape} colunas identicas {sum(ig)}/{len(ig)}'
          f'  {[c for c,k in zip(a.columns,ig) if not k]}')


def strip(f):
    out = []
    for l in open(f):
        if not l.strip():
            continue
        d = json.loads(l)
        d.pop('ts', None)
        if str(d.get('rec', '')).endswith('_gen'):
            d.pop('tempo_geracao_s', None)
        out.append(json.dumps(d, sort_keys=True))
    return out


sa, sb = strip(A + '.jsonl'), strip(B + '.jsonl')
print(f'  ⑥ (sem ts/tempo): iguais={sa==sb} · {len(sa)} x {len(sb)} linhas')

# ── (b) gates ────────────────────────────────────────────────────────────────
import gates_proveniencia as G  # noqa: E402
print('\n=== (b) gates de proveniencia (modo campanha)')
tmp = tempfile.mkdtemp()
d = f'{tmp}/experiments/main/moead'
os.makedirs(d)
probs = sorted(p for p in os.listdir(f'{RES}/moead')
               if os.path.isdir(f'{RES}/moead/{p}'))
for p in probs:
    for f in os.listdir(f'{RES}/moead/{p}/42'):
        os.symlink(f'{RES}/moead/{p}/42/{f}', f'{d}/{f}')
import collections
agg = collections.Counter()
for p in probs:
    for n, ok, det in G.gates_de_proveniencia('main', 'moead', p, 42, tmp, modo='campanha'):
        agg[(n, ok)] += 1
for (n, ok), c in sorted(agg.items()):
    print(f'  s42  {n:20s} {str(ok):5s} {c}/{len(probs)}')
for n, ok, det in G.gates_de_proveniencia('main', 'moead', 'DTLZ2', 42, SMOKE, modo='campanha'):
    print(f'  SMOKE {n:20s} {str(ok):5s} {str(det)[:90]}')
