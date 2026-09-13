"""T11/b4 — bateria 1: censo do que EXISTE em cada corpus (s42 x smoke).
READ-ONLY. Escreve so em f5/t11/baterias/b4/.
"""
import json, glob, os, sys
from collections import Counter
import pandas as pd

S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
SMOKE = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4'

CAMPOS_NOVOS_MANIF = ['campanha_id', 'repo_hash', 'schema_version']
CAMPOS_NOVOS_SIGMA = ['REGRA_DO_ROTULO', 'p0_p1', 'pred_confianca', 'cobertura_3']
CAMPOS_NOVOS_GEN = ['y_treino_dist', 'n_front1', 'f_best', 'dist_min_arquivo',
                    'guard_randperm', 'ref_ids', 'n_refs', 'modelo_hp']

rows = []
probs = sorted(os.listdir(S42))
for p in probs:
    mf = f'{S42}/{p}/42/exp_main_b4_{p}_42.manifest.json'
    jl = f'{S42}/{p}/42/exp_main_b4_{p}_42.jsonl'
    m = json.load(open(mf))
    recs = [json.loads(l) for l in open(jl)]
    cnt = Counter(r.get('rec') for r in recs)
    gens = [r for r in recs if r.get('rec') == 'b4_gen']
    sd = m.get('sigma_dict', {}) or {}
    r = dict(corpus='s42', problema=p, n_gen=len(gens),
             n_sonda=cnt.get('sonda', 0), n_sonda_estrat=cnt.get('sonda_estratificada', 0))
    for c in CAMPOS_NOVOS_MANIF:
        r['manif_' + c] = c in m
    for c in CAMPOS_NOVOS_SIGMA:
        r['sigma_' + c] = c in sd
    for c in CAMPOS_NOVOS_GEN:
        r['gen_' + c] = sum(1 for g in gens if c in g)
    # ref_ids sentinela?
    ri = [g.get('ref_ids') for g in gens if 'ref_ids' in g]
    r['ref_ids_sentinela'] = sum(1 for x in ri if x and all(v == -1 for v in x))
    r['ref_ids_reais'] = sum(1 for x in ri if x and not all(v == -1 for v in x))
    r['ref_ids_len6'] = sum(1 for x in ri if x and len(x) == 6)
    rows.append(r)

# smoke
mf = f'{SMOKE}/exp_main_b4_MMF1_42.manifest.json'
jl = f'{SMOKE}/exp_main_b4_MMF1_42.jsonl'
m = json.load(open(mf)); recs = [json.loads(l) for l in open(jl)]
cnt = Counter(r.get('rec') for r in recs)
gens = [r for r in recs if r.get('rec') == 'b4_gen']
sd = m.get('sigma_dict', {}) or {}
r = dict(corpus='smokeT11', problema='MMF1', n_gen=len(gens),
         n_sonda=cnt.get('sonda', 0), n_sonda_estrat=cnt.get('sonda_estratificada', 0))
for c in CAMPOS_NOVOS_MANIF: r['manif_' + c] = c in m
for c in CAMPOS_NOVOS_SIGMA: r['sigma_' + c] = c in sd
for c in CAMPOS_NOVOS_GEN: r['gen_' + c] = sum(1 for g in gens if c in g)
ri = [g.get('ref_ids') for g in gens if 'ref_ids' in g]
r['ref_ids_sentinela'] = sum(1 for x in ri if x and all(v == -1 for v in x))
r['ref_ids_reais'] = sum(1 for x in ri if x and not all(v == -1 for v in x))
r['ref_ids_len6'] = sum(1 for x in ri if x and len(x) == 6)
rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/t11_b4_censo.csv', index=False)
pd.set_option('display.width', 250, 'display.max_columns', 60)
s = df[df.corpus == 's42']
print('=== S42 (25 celulas) — agregado ===')
for c in df.columns:
    if c in ('corpus', 'problema'): continue
    v = s[c]
    if v.dtype == bool:
        print(f'  {c:32s} True em {int(v.sum())}/{len(v)}')
    else:
        print(f'  {c:32s} soma={v.sum()} min={v.min()} max={v.max()}')
print()
print('=== SMOKE T11 ===')
print(df[df.corpus == 'smokeT11'].T.to_string())
