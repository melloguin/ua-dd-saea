#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead_populacao.py — o teste do prior "REGRIDE vs DoE".
O IGD+ oficial (D69) lê o ARQUIVO ① e portanto NUNCA pode regredir (monótono por
construção). A regressão que o prior descreve só é observável na POPULAÇÃO — que no
MOEA/D com T=2 colapsa em clones. Mede, para os 4 pisos ONLINE:
  P1  IGD+/HV da população FINAL (②(último)) × da população SEMEADA (②(1)) × do DoE inteiro
  P2  o mesmo para nsga2/nsga3/smsemoa (contraste do casamento §3.2)
Métrica OFICIAL src/metrics.py, ref set calculado 1× por problema.
"""
import json, os, sys
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
sys.path.insert(0, REPO); os.chdir(REPO)
from src import metrics                                    # noqa: E402

v = metrics.hv_smoke_bbob_f1(); assert abs(v - 1.04333) < 5e-6
print('gate D92 OK: %.5f' % v, flush=True)

ALGS = ['moead', 'nsga2', 'nsga3', 'smsemoa']
PROBS = sorted(p for p in os.listdir(os.path.join(RES, 'moead')) if not p.startswith('.'))
rows = []
for prob in PROBS:
    RN = metrics.reference_set(prob)
    for alg in ALGS:
        base = os.path.join(RES, alg, prob, '42', 'exp_main_%s_%s_42' % (alg, prob))
        if not os.path.exists(base + '__real.parquet'):
            continue
        real = pd.read_parquet(base + '__real.parquet')
        pop = pd.read_parquet(base + '__pop.parquet')
        fc = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))
        F = real[fc].to_numpy(np.float64)
        s2r = {int(s): i for i, s in enumerate(real['solution_id'].to_numpy())}
        gs = sorted(pop['geracao'].unique())
        p1 = pop[pop['geracao'] == gs[0]]['solution_id'].to_numpy()
        pf = pop[pop['geracao'] == gs[-1]]['solution_id'].to_numpy()
        m_doe = metrics.metrics_of_set(F[real['fase'] == 'init'], prob, ref_norm=RN)
        m_p1 = metrics.metrics_of_set(F[[s2r[int(s)] for s in p1]], prob, ref_norm=RN)
        m_pf = metrics.metrics_of_set(F[[s2r[int(s)] for s in pf]], prob, ref_norm=RN)
        m_arq = metrics.metrics_of_set(F, prob, ref_norm=RN)
        rows.append(dict(problema=prob, alg=alg, n_ger=len(gs), N=len(p1),
                         igd_doe=m_doe['igd_plus'], igd_pop1=m_p1['igd_plus'],
                         igd_popF=m_pf['igd_plus'], igd_arq=m_arq['igd_plus'],
                         hv_popF=m_pf['hv'], nd_popF=m_pf['n_nd'],
                         unicos_popF=len(set(pf.tolist())),
                         reg_vs_doe=m_pf['igd_plus'] > m_doe['igd_plus'],
                         reg_vs_semeada=m_pf['igd_plus'] > m_p1['igd_plus'],
                         raz_popF_doe=m_pf['igd_plus'] / m_doe['igd_plus'],
                         raz_popF_pop1=m_pf['igd_plus'] / m_p1['igd_plus']))
    print(' ', prob, 'ok', flush=True)

df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'moead_populacao_vs_doe.csv'), index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 200)
print(df[df.alg == 'moead'].round(4).to_string())
print('\n=== REGRESSÃO DA POPULAÇÃO ===')
for a in ALGS:
    d = df[df.alg == a]
    print('%-8s regride vs DoE inteiro: %2d/%d | regride vs população SEMEADA: %2d/%d | razão popF/pop1 mediana %.3f | únicos na pop final: med %.1f de %d'
          % (a, d.reg_vs_doe.sum(), len(d), d.reg_vs_semeada.sum(), len(d),
             d.raz_popF_pop1.median(), d.unicos_popF.median(), d.N.median()))
print()
piv = df.pivot_table(index='problema', columns='alg', values='raz_popF_doe')
print(piv.round(3).to_string())
