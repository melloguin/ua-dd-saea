#!/usr/bin/env python
"""U10 — fechamento aritmetico entre camadas do smsemoa.
Identidade alvo:  N·(n_ger_logadas−1) = Σ Δfe(g) + cache_hits_evolucao_nas_logadas
e                 maxfe = fe(ultima geracao logada) + FE_da_geracao_fantasma
e                 cache_hits_total = (N+1 no seeding) + cache_hits_evolucao (logadas+fantasma)."""
import os, glob, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bateria_smsemoa import load_cell

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/smsemoa'
OUT = os.path.dirname(os.path.abspath(__file__))
PROBS = sorted(os.path.basename(p) for p in glob.glob(ROOT + '/*') if os.path.isdir(p))
rows = []
for p in PROBS:
    man, recs, real, pop, sur, tim = load_cell(p)
    D = len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])
    N = 20; init = 11 * D - 1; maxfe = 31 * D - 1
    gens = [x for x in recs if x.get('rec') == 'smsemoa_gen']
    guards = [x for x in recs if x.get('rec') == 'guard']
    ch = [g for g in guards if g['name'] == 'cache_hit']
    ch_seed = [g for g in ch if g['fe'] == init]
    fes = [g['fe'] for g in gens]
    dfe = np.diff(fes)
    fe_ult = fes[-1]
    # atribuicao por ORDEM no fluxo do (6): um cache_hit pertence a geracao cujo
    # evento smsemoa_gen vem DEPOIS dele (o guard e logado dentro do laco interno).
    # (o teste por fronteira de fe erra o empate fe==fe_ultima — caso MMF4)
    ch_log, ch_gho = [], []
    gi = 0
    seq = [x for x in recs if x.get('rec') in ('guard', 'smsemoa_gen')]
    for x in seq:
        if x['rec'] == 'smsemoa_gen':
            gi += 1
        elif x.get('name') == 'cache_hit' and x.get('fe', 0) > init:
            (ch_log if gi < len(gens) else ch_gho).append(x)
    deficit = int(N * (len(gens) - 1) - dfe.sum())
    slots_gho = (maxfe - fe_ult) + len(ch_gho)
    rows.append(dict(problema=p, D=D, N=N, init=init, maxfe=maxfe, n_ger=len(gens),
                     fe_ult_ger=fe_ult, sum_dfe=int(dfe.sum()), slots_esperados=N * (len(gens) - 1),
                     deficit_slots=deficit, ch_seeding=len(ch_seed), ch_logadas=len(ch_log),
                     ch_fantasma=len(ch_gho), ch_total=len(ch), ch_manifesto=man['cache_hits'],
                     U10_deficit_eq_ch=deficit == len(ch_log),
                     U10_seed_eq_Nmais1=len(ch_seed) == N + 1,
                     U10_ch_total=len(ch) == man['cache_hits'],
                     fe_fantasma=maxfe - fe_ult, slots_fantasma=slots_gho,
                     opt_rows=int((real.fase == 'opt').sum()), opt_esp=20 * D,
                     U10_opt_ok=int((real.fase == 'opt').sum()) == 20 * D,
                     U10_fe_fecha=(fe_ult + (maxfe - fe_ult)) == maxfe == len(real)))
df = pd.DataFrame(rows)
df.to_csv(OUT + '/diag_aritmetica.csv', index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 60)
print(df.to_string(index=False))
print()
for c in ['U10_deficit_eq_ch', 'U10_seed_eq_Nmais1', 'U10_ch_total', 'U10_opt_ok', 'U10_fe_fecha']:
    print(f'{c}: {int(df[c].sum())}/25')
