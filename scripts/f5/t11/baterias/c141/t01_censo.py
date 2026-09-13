"""t01 — censo comparativo do smoke T11 c141/MMF1 contra a celula homologa da rodada-42.
READ-ONLY. Escreve so em f5/t11/baterias/c141/."""
import json, glob, os, sys
import pandas as pd, numpy as np, pyarrow.parquet as pq

T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141/MMF1/42'
BASE = 'exp_main_c141_MMF1_42'

def load(root):
    d = {}
    d['man'] = json.load(open(f'{root}/{BASE}.manifest.json'))
    for lay, suf in [('real','__real'),('pop','__pop'),('sur','__surrogate'),('tim','__timing')]:
        d[lay] = pd.read_parquet(f'{root}/{BASE}{suf}.parquet')
    ev = [json.loads(l) for l in open(f'{root}/{BASE}.jsonl') if l.strip()]
    d['ev'] = ev
    return d

A = load(T11); B = load(R42)

out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

for tag, d in [('T11', A), ('R42', B)]:
    m = d['man']
    P(f"== {tag} ==")
    P(' schema_version', m.get('schema_version'), 'campanha_id', m.get('campanha_id'),
      'repo_hash', (m.get('repo_hash') or '')[:12], 'algo_version', m.get('algo_version'))
    P(' status', m['status'], 'maxfe', m['maxfe'], 'fe_final', m['fe_final'],
      'n_ger', m['n_geracoes'], 'cache_hits', m['cache_hits'], 'doe_hash', m['doe_hash'][:16])
    P(' env', m['env'])
    P(' timing', m['timing'])
    P(' params', m['params'])
    P(' sigma_dict keys', list(m['sigma_dict'].keys()))
    s = m['sonda']
    P(' sonda', {k: v for k, v in s.items() if k != 'geracoes'})
    P(' sonda.geracoes', s.get('geracoes'))
    P(' fit_series n=', len(m['fit_series']), 'n_acum', [f['n_acumulado'] for f in m['fit_series']])
    P(' camadas: real', d['real'].shape, 'pop', d['pop'].shape, 'sur', d['sur'].shape, 'tim', d['tim'].shape)
    from collections import Counter
    P(' ev recs', Counter(e.get('rec') for e in d['ev']))
    P(' real cols', list(d['real'].columns))
    P(' sur cols', list(d['sur'].columns))
    P(' tim cols', list(d['tim'].columns))
    P(' pop cols', list(d['pop'].columns))
    # regimes
    if 'regime' in d['sur'].columns:
        P(' sur regimes', d['sur']['regime'].value_counts().to_dict())
    P('')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't01_censo.txt'), 'w').write('\n'.join(out))
