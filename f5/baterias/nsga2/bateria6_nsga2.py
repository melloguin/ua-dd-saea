#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BATERIA 6 — agregados finais do relatório + contraste com os outros 3 pisos."""
import json, os, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'
CAR = pd.read_csv(f'{RAIZ}/ua-dd-saea/claude_code_context/artifacts/characteristics.csv').set_index('problema')
PROBS = [p for p in sorted(os.listdir(f'{DADOS}/nsga2')) if not p.startswith('.')]

tot = dict(fe=0, gens=0, pop=0, ch=0, ch_seed=0, ch_prole=0, slots=0, init=0)
gerD = []
for prob in PROBS:
    b = f'{DADOS}/nsga2/{prob}/42/exp_main_nsga2_{prob}_42'
    man = json.load(open(b + '.manifest.json'))
    recs = [json.loads(l) for l in open(b + '.jsonl')]
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    ch = [x for x in recs if x.get('name') == 'cache_hit']
    D = int(CAR.loc[prob, 'D']); n_init = 11 * D - 1
    real = pq.read_table(b + '__real.parquet').to_pandas()
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    seed_blk = sum(1 for g in ch if g['fe'] == n_init)
    tot['fe'] += man['maxfe']; tot['gens'] += len(gens); tot['pop'] += len(pop)
    tot['ch'] += len(ch); tot['ch_seed'] += seed_blk; tot['ch_prole'] += len(ch) - seed_blk
    tot['slots'] += (len(gens) - 1) * 20; tot['init'] += n_init
    gerD.append((prob, D, len(gens), len(gens) == D + 1))
print('AGREGADOS (25 células):', tot)
print('n_geracoes == D+1 em %d/25' % sum(1 for _, _, _, ok in gerD if ok))
print('  detalhe:', [(p, D, g) for p, D, g, _ in gerD][:8], '...')
print('FE total = %d · init total = %d (%.1f%%) · infill = %d'
      % (tot['fe'], tot['init'], 100 * tot['init'] / tot['fe'], tot['fe'] - tot['init']))

print('\n=== contraste entre os 4 pisos (cache-hit de prole = clone-hazard, D89) ===')
rows = []
for alg in ['nsga2', 'nsga3', 'moead', 'smsemoa']:
    for prob in PROBS:
        b = f'{DADOS}/{alg}/{prob}/42/exp_main_{alg}_{prob}_42'
        if not os.path.exists(b + '.manifest.json'):
            continue
        man = json.load(open(b + '.manifest.json'))
        recs = [json.loads(l) for l in open(b + '.jsonl')]
        ev = [x['rec'] for x in recs]
        gname = [e for e in set(ev) if e.endswith('_gen') or e == 'decision']
        gens = [x for x in recs if x['rec'] in gname]
        ch = [x for x in recs if x.get('name') == 'cache_hit']
        D = int(CAR.loc[prob, 'D']); n_init = 11 * D - 1
        seed_blk = sum(1 for g in ch if g['fe'] == n_init)
        Nef = man['params'].get('N_efetivo')
        rows.append(dict(alg=alg, problema=prob, D=D, M=int(CAR.loc[prob, 'M']),
                         N_nom=man['params'].get('N_nominal'), N_ef=Nef, n_gens=len(gens),
                         ch_total=len(ch), ch_seed=seed_blk, ch_prole=len(ch) - seed_blk,
                         slots=(len(gens) - 1) * (Nef or 20),
                         taxa=(len(ch) - seed_blk) / max(1, (len(gens) - 1) * (Nef or 20)),
                         evento='|'.join(sorted(set(gname)))))
dfp = pd.DataFrame(rows); dfp.to_csv(f'{OUT}/contraste_pisos.csv', index=False)
pd.set_option('display.width', 320, 'display.max_columns', 60)
print(dfp.groupby('alg').agg(celulas=('taxa', 'size'), ch_prole=('ch_prole', 'sum'),
                             slots=('slots', 'sum'), taxa_glob=('ch_prole', 'sum'),
                             n_gens=('n_gens', 'sum')).assign(
    taxa=lambda d: d.ch_prole / d.slots).to_string())
print('\nN_efetivo por alg × M:')
print(dfp.pivot_table(index='alg', columns='M', values='N_ef', aggfunc=lambda s: sorted(set(s))).to_string())
print('\nZDT1 (o caso citado no bundle §3.2 ponto 5):')
print(dfp[dfp.problema == 'ZDT1'][['alg', 'N_ef', 'n_gens', 'ch_total', 'ch_seed', 'ch_prole', 'slots', 'taxa']].to_string())
print('\ngerações por alg (D=12 DTLZ2, M=3 — o caso do bundle §6.3):')
print(dfp[dfp.problema == 'DTLZ2'][['alg', 'N_nom', 'N_ef', 'n_gens']].to_string())
