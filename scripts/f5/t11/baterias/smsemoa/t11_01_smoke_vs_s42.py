#!/usr/bin/env python
"""T11/smsemoa — bateria 1: o smoke T11 reproduz BIT-A-BIT a celula da s42?
READ-ONLY. Compara main/smsemoa/DTLZ2/42 (s42, pre-T11) x evidencia_T11/smoke_matlab.
"""
import json, os, hashlib
import pandas as pd, numpy as np

S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/smsemoa/DTLZ2/42/'
SMK = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/smsemoa/'
STEM = 'exp_main_smsemoa_DTLZ2_42'


def h(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()[:16]


print('=== 1. CAMADAS PARQUET: hash de conteudo ===')
for lay in ['real', 'pop', 'surrogate', 'timing']:
    a = pd.read_parquet(S42 + f'{STEM}__{lay}.parquet')
    b = pd.read_parquet(SMK + f'{STEM}__{lay}.parquet')
    same_cols = list(a.columns) == list(b.columns)
    same_shape = a.shape == b.shape
    eq = None
    if same_cols and same_shape:
        try:
            eq = a.equals(b)
        except Exception as e:
            eq = f'err {e}'
    print(f'{lay:10s} s42={a.shape} smoke={b.shape} cols_iguais={same_cols} equals={eq} h42={h(a)} hT11={h(b)}')

print()
print('=== 2. ①: X e f bit-a-bit ===')
a = pd.read_parquet(S42 + f'{STEM}__real.parquet')
b = pd.read_parquet(SMK + f'{STEM}__real.parquet')
xc = [c for c in a.columns if c.startswith('x')]
fc = [c for c in a.columns if c.startswith('f') and c not in ('fase', 'fe_index')]
print('cols X:', len(xc), 'cols f:', fc)
print('max|dX| =', np.abs(a[xc].values - b[xc].values).max())
print('max|df| =', np.abs(a[fc].values - b[fc].values).max())
print('solution_id identico:', (a['solution_id'].values == b['solution_id'].values).all())
print('fase identica:', (a['fase'].values == b['fase'].values).all())

print()
print('=== 3. ②: populacao geracao a geracao ===')
a2 = pd.read_parquet(S42 + f'{STEM}__pop.parquet')
b2 = pd.read_parquet(SMK + f'{STEM}__pop.parquet')
print('cols', list(a2.columns))
print('shapes', a2.shape, b2.shape)
for c in a2.columns:
    if a2[c].dtype.kind in 'fiu':
        d = np.abs(np.nan_to_num(a2[c].values.astype(float)) - np.nan_to_num(b2[c].values.astype(float))).max()
        print(f'  {c:20s} max|delta|={d}')

print()
print('=== 4. ⑥: eventos de geracao ===')
LA = [json.loads(l) for l in open(S42 + f'{STEM}.jsonl')]
LB = [json.loads(l) for l in open(SMK + f'{STEM}.jsonl')]
ga = [r for r in LA if r.get('rec') == 'smsemoa_gen']
gb = [r for r in LB if r.get('rec') == 'smsemoa_gen']
print('n_gen', len(ga), len(gb))
difs = 0
for x, y in zip(ga, gb):
    for k in ['geracao', 'fe', 'n_pop', 'n_front1', 'ideal', 'nadir_pop', 'nadir_front1', 'f_best']:
        if x.get(k) != y.get(k):
            difs += 1
            print('  DIFERE', x['geracao'], k, x.get(k), y.get(k))
print('campos de geracao divergentes:', difs)
gua = [r for r in LA if r.get('rec') == 'guard']
gub = [r for r in LB if r.get('rec') == 'guard']
print('guards', len(gua), len(gub), 'iguais(sid,x_key,fe,name):',
      [(g['name'], g['solution_id'], g['x_key'], g['fe']) for g in gua] ==
      [(g['name'], g['solution_id'], g['x_key'], g['fe']) for g in gub])

print()
print('=== 5. header/footer: diff de chaves ===')
ha = [r for r in LA if r['rec'] == 'header'][0]
hb = [r for r in LB if r['rec'] == 'header'][0]
print('header chaves s42:', sorted(ha.keys()))
print('header novas T11:', sorted(set(hb) - set(ha)), '| removidas:', sorted(set(ha) - set(hb)))
print('header valores diferentes (ex ts):', [k for k in ha if k != 'ts' and ha[k] != hb.get(k)])
fa = [r for r in LA if r['rec'] == 'footer'][0]
fb = [r for r in LB if r['rec'] == 'footer'][0]
print('footer chaves s42:', sorted(fa.keys()))
print('footer novas T11:', sorted(set(fb) - set(fa)), '| removidas:', sorted(set(fa) - set(fb)))
print('footer valores diferentes:', [(k, fa[k], fb.get(k)) for k in fa if k != 'ts' and fa[k] != fb.get(k)])

print()
print('=== 6. ⑤: diff de chaves ===')
ma = json.load(open(S42 + f'{STEM}.manifest.json'))
mb = json.load(open(SMK + f'{STEM}.manifest.json'))
print('manifest novas T11:', sorted(set(mb) - set(ma)), '| removidas:', sorted(set(ma) - set(mb)))
for k in ma:
    if k in ('paths', 'created_at', 'updated_at', 'timing', 'params'):
        continue
    if ma[k] != mb.get(k):
        print('  DIFERE', k, repr(ma[k])[:80], '->', repr(mb.get(k))[:80])
print('params novas:', sorted(set(mb['params']) - set(ma['params'])),
      '| removidas:', sorted(set(ma['params']) - set(mb['params'])))
for k in ma['params']:
    if ma['params'][k] != mb['params'].get(k):
        print('  params.DIFERE', k)
