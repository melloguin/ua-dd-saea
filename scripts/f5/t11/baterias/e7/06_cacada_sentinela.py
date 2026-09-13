#!/usr/bin/env python
"""T11/e7 — CACADA DE SENTINELA (o padrao do c217: campo presente, dado sentinela).
Varre TODOS os campos do (6) nas 25 celulas da s42 + os 2 smokes T11 e classifica
cada campo: constante? sentinela (-1/NaN/None/string)? variavel? READ-ONLY."""
import json, os
from collections import defaultdict
import numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'

def varre(bases, rotulo):
    campos = defaultdict(lambda: {'n': 0, 'nulos': 0, 'nan': 0, 'menos1': 0, 'vals': set(), 'str': set()})
    ntot = 0
    for base in bases:
        for ln in open(base + '.jsonl'):
            e = json.loads(ln)
            if e.get('rec') != 'e7_gen':
                continue
            ntot += 1
            plano = {}
            for k, v in e.items():
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        plano[f'{k}.{k2}'] = v2
                else:
                    plano[k] = v
            for k, v in plano.items():
                c = campos[k]; c['n'] += 1
                if v is None:
                    c['nulos'] += 1; continue
                if isinstance(v, str):
                    c['str'].add(v[:60]); continue
                if isinstance(v, list):
                    arr = np.array(v, float)
                    if np.isnan(arr).any():
                        c['nan'] += 1
                    if (arr == -1).all():
                        c['menos1'] += 1
                    if len(c['vals']) < 6:
                        c['vals'].add(tuple(np.round(arr, 6).tolist())[:4])
                    continue
                if isinstance(v, bool):
                    c['vals'].add(v); continue
                f = float(v)
                if np.isnan(f):
                    c['nan'] += 1
                if f == -1:
                    c['menos1'] += 1
                if len(c['vals']) < 6:
                    c['vals'].add(round(f, 8))
    print(f'\n===== {rotulo}: {ntot} eventos e7_gen, {len(campos)} campos =====')
    linhas = []
    for k in sorted(campos):
        c = campos[k]
        distinct = len(c['vals']) + len(c['str'])
        vered = 'VARIAVEL'
        if c['nulos'] == c['n']:
            vered = '🔴 SEMPRE NULO'
        elif c['menos1'] == c['n']:
            vered = '🔴 SENTINELA -1 (padrao c217)'
        elif c['nan'] == c['n']:
            vered = '🔴 SEMPRE NaN'
        elif c['str'] and not c['vals']:
            vered = ('🟠 STRING CONSTANTE' if len(c['str']) == 1 else 'STRING (varia)')
        elif distinct == 1:
            vered = '🟡 CONSTANTE (1 valor)'
        elif distinct <= 3:
            vered = f'quase-constante ({distinct})'
        amostra = sorted(c['str'])[:1] if c['str'] else sorted((str(x) for x in c['vals']))[:3]
        linhas.append((k, c['n'], c['nulos'], c['nan'], c['menos1'], vered, amostra))
        print(f'{k:34s} n={c["n"]:5d} null={c["nulos"]:5d} nan={c["nan"]:4d} m1={c["menos1"]:4d}  {vered:32s} {amostra}')
    return linhas

s42 = [f'{ROOT}/{p}/42/exp_main_e7_{p}_42' for p in sorted(d for d in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{d}'))]
smoke = [f'{EV}/smoke_matlab/experiments/main/e7/exp_main_e7_MMF11_L_42',
         f'{EV}/g6_com/experiments/main/e7/exp_main_e7_MMF1_42']
a = varre(s42, 's42 (25 celulas)')
b = varre(smoke, 'smoke T11 (2 celulas)')
json.dump({'s42': a, 'smoke': b}, open(f'{OUT}/sentinelas_e7.json', 'w'), indent=1, default=str)
