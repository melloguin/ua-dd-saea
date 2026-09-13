#!/usr/bin/env python
"""T11/e7 — T1 RESOLVIDO? Par COM x SEM sonda (g6). Prova de nao-perturbacao do RNG.
READ-ONLY. Saida: g6_e7.json"""
import json, hashlib, sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'
res = {}

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

paths = {l: f'{B}/{l}/experiments/main/e7/exp_main_e7_MMF1_42' for l in ('g6_com', 'g6_sem')}

# camada (1) real
r = {l: pd.read_parquet(p + '__real.parquet') for l, p in paths.items()}
res['real_sha256'] = {l: sha(p + '__real.parquet') for l, p in paths.items()}
res['real_bit_identico_arquivo'] = res['real_sha256']['g6_com'] == res['real_sha256']['g6_sem']
res['real_shape'] = {l: list(d.shape) for l, d in r.items()}
res['real_cols'] = list(r['g6_com'].columns)
num = [c for c in r['g6_com'].columns if pd.api.types.is_numeric_dtype(r['g6_com'][c])]
res['real_max_abs_diff'] = {c: float(np.nanmax(np.abs(
    r['g6_com'][c].to_numpy(float) - r['g6_sem'][c].to_numpy(float)))) for c in num}

# camada (3) surrogate
s = {l: pd.read_parquet(p + '__surrogate.parquet') for l, p in paths.items()}
res['sur_shape'] = {l: list(d.shape) for l, d in s.items()}
res['sur_regimes'] = {l: d['regime'].value_counts().to_dict() for l, d in s.items()}
bc = {l: d[d.regime == 'online'].reset_index(drop=True) for l, d in s.items()}
res['sur_online_shape'] = {l: list(d.shape) for l, d in bc.items()}
if bc['g6_com'].shape == bc['g6_sem'].shape:
    numc = [c for c in bc['g6_com'].columns if pd.api.types.is_numeric_dtype(bc['g6_com'][c])]
    dd = {}
    for c in numc:
        a = bc['g6_com'][c].to_numpy(float); b = bc['g6_sem'][c].to_numpy(float)
        m = ~(np.isnan(a) & np.isnan(b))
        dd[c] = float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else None
    res['sur_online_max_abs_diff'] = dd
    res['sur_online_bit_identico'] = all((v == 0.0) for v in dd.values() if v is not None)

# camada (2) pop
p2 = {l: pd.read_parquet(p + '__pop.parquet') for l, p in paths.items()}
res['pop_sha256'] = {l: sha(p + '__pop.parquet') for l, p in paths.items()}
res['pop_bit_identico'] = res['pop_sha256']['g6_com'] == res['pop_sha256']['g6_sem']
res['pop_shape'] = {l: list(d.shape) for l, d in p2.items()}

# (6) eventos
for l, p in paths.items():
    ev = [json.loads(x) for x in open(p + '.jsonl')]
    tp = {}
    for e in ev:
        tp[e.get('rec', '?')] = tp.get(e.get('rec', '?'), 0) + 1
    res.setdefault('jsonl_recs', {})[l] = tp
    g = [e for e in ev if e.get('rec') == 'e7_gen']
    res.setdefault('e7_gen_n', {})[l] = len(g)
    res.setdefault('e7_gen_chave', {})[l] = {
        'ramo': [e.get('ramo') for e in g],
        'Ratio': [e.get('Ratio') for e in g],
        'RatioOld': [e.get('RatioOld') for e in g],
        'f_best': [e.get('f_best') for e in g],
        'ymin': [e.get('ymin') for e in g],
        'n_front1': [e.get('n_front1') for e in g],
    }
    res.setdefault('manifest', {})[l] = json.load(open(p + '.manifest.json'))

a, b = res['e7_gen_chave']['g6_com'], res['e7_gen_chave']['g6_sem']
res['e7_gen_identico'] = {k: (a[k] == b[k]) for k in a}

# campos NOVOS T11 no manifesto
for l in paths:
    m = res['manifest'][l]
    res.setdefault('campos_t11', {})[l] = {
        'campanha_id': m.get('campanha_id'), 'repo_hash': (m.get('repo_hash') or '')[:16],
        'schema_versao': m.get('schema_versao') or m.get('versao_schema'),
        'chaves_topo': sorted(m.keys()),
    }
del res['manifest']

json.dump(res, open(f'{OUT}/g6_e7.json', 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in res.items() if k not in ('real_max_abs_diff', 'sur_online_max_abs_diff', 'e7_gen_chave')}, indent=1, default=str))
print('real_max_abs_diff  ->', {k: v for k, v in res['real_max_abs_diff'].items()})
print('sur_online_maxdiff ->', res.get('sur_online_max_abs_diff'))
print('e7_gen_identico    ->', res['e7_gen_identico'])
