#!/usr/bin/env python
"""B4 — T1 da F5 (nao-perturbacao da sonda) agora VERIFICAVEL: par G-6 COM x SEM sonda.
Tres sinais exigidos pelo T11 §4.2-5: (i) ⑤ com sonda.desligada=true e n_blocos=0 no lado SEM;
(ii) ③ ENCOLHENDO (some o regime='sonda'); (iii) ① BIT-IDENTICA (sha256 do buffer float32).
"""
import json, hashlib
import numpy as np, pandas as pd, pyarrow.parquet as pq

C = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/c238/exp_main_c238_MMF1_42'
S = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/c238/exp_main_c238_MMF1_42'
K = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42'

mc = json.load(open(f'{C}.manifest.json')); ms = json.load(open(f'{S}.manifest.json'))
print('(i) ⑤ sonda:')
print('   COM:', {k: mc['sonda'][k] for k in ['desligada', 'n_blocos', 'n_linhas', 'S', 'k', 'n_falhas']})
print('   SEM:', {k: ms['sonda'][k] for k in ['desligada', 'n_blocos', 'n_linhas', 'S', 'k', 'n_falhas']} if ms.get('sonda') else ms.get('sonda'))
print('   campanha_id COM=%s SEM=%s' % (mc.get('campanha_id'), ms.get('campanha_id')))
print('   repo_hash  COM=%s SEM=%s  (iguais? %s)' % (mc.get('repo_hash'), ms.get('repo_hash'), mc.get('repo_hash') == ms.get('repo_hash')))

print('\n(ii) ③ encolhendo:')
for tag, b in [('COM', C), ('SEM', S)]:
    d = pq.read_table(f'{b}__surrogate.parquet').to_pandas()
    print('   %s shape=%s regimes=%s' % (tag, d.shape, d.regime.value_counts().to_dict()))

print('\n(iii) ① bit-identica:')
hs = {}
for tag, b in [('COM', C), ('SEM', S), ('SMOKE', K)]:
    t = pq.read_table(f'{b}__real.parquet').to_pandas()
    buf = np.ascontiguousarray(t[['x0', 'x1', 'f0', 'f1']].to_numpy(np.float32)).tobytes()
    hs[tag] = hashlib.sha256(buf).hexdigest()
    print('   %-6s n=%d sha256(X|F float32)=%s' % (tag, len(t), hs[tag]))
print('   COM == SEM ?', hs['COM'] == hs['SEM'], '  COM == SMOKE ?', hs['COM'] == hs['SMOKE'])
print('   hash do handoff §5 para c238: 43f533269741c82f  (prefixo bate? %s)' %
      hs['COM'].startswith('43f533269741c82f'))

print('\n(iv) ⑥ das duas pernas — censo + identidade dos eventos de geracao:')
import collections
ev = {}
for tag, b in [('COM', C), ('SEM', S)]:
    r = [json.loads(l) for l in open(f'{b}.jsonl')]
    ev[tag] = [x for x in r if x.get('rec') == 'c238_gen']
    print('   %-4s censo=%s' % (tag, dict(collections.Counter(x['rec'] for x in r))))
campos = ['eim_best', 'eim_mediana_pool', 'n_front', 'min_dist_infill', 'infill_sid', 'fe_treino_max']
for c in campos:
    a = np.array([x[c] for x in ev['COM']], float); b_ = np.array([x[c] for x in ev['SEM']], float)
    print('   %-18s max|delta| COM x SEM = %s' % (c, np.abs(a - b_).max()))
for c in ['theta_media', 'lnL', 'norm_min', 'norm_max', 'u_best', 's_best']:
    a = np.array([x[c] for x in ev['COM']], float); b_ = np.array([x[c] for x in ev['SEM']], float)
    print('   %-18s max|delta| COM x SEM = %s' % (c, np.abs(a - b_).max()))
print('\n(v) tempo: o custo da sonda')
print('   COM timing:', mc['timing'])
print('   SEM timing:', ms['timing'])
