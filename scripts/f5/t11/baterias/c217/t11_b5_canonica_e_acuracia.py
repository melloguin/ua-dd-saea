# -*- coding: utf-8 -*-
"""T11/c217 — BATERIA 5: comparacao canonica + acuracia do classificador. READ-ONLY."""
import os
import numpy as np, pandas as pd
from scipy.stats import spearmanr

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = os.path.join(RAIZ, 'ua-dd-saea/f5/t11/baterias/c217')
G = pd.read_pickle(os.path.join(OUT, 't11_c217_s42_geracoes.pkl'))

# ---- acuracia por amostra = p+ + 0.5*(contrad/|Dv|)  (num par contraditorio 1 das 2 direcoes acerta)
def ceilf(x): return int(np.ceil(x - 1e-12))
G = G[G.P.notna()].copy()
G['Pb'] = G.P.map(lambda p: ceilf(p/4)); G['Pw'] = G.P.map(lambda p: ceilf(p/2)-ceilf(p/4))
G['Dv'] = (G.Pb - G.n_best) + (G.Pw - G.n_worst)
G['acc'] = G.p_mais + 0.5*(G.nc/G.Dv)
fam = G.problema.str.replace(r'\d.*', '', regex=True).str.rstrip('_')
G['familia'] = np.where(G.problema.str.startswith('BBOB'), 'BBOB',
                np.where(G.problema.str.startswith('DTLZ'), 'DTLZ',
                np.where(G.problema.str.startswith('WFG'), 'WFG',
                np.where(G.problema.str.startswith('ZDT'), 'ZDT', 'MMF'))))
print('== ACURACIA POR AMOSTRA (p+ + 0,5*contrad/|Dv|) ==')
print('  global (%d ger, 25 celulas): %.4f' % (len(G), G.acc.mean()))
print(G.groupby('familia').acc.agg(['size', 'mean']).round(4).to_string())
for p in ('DTLZ2', 'DTLZ3'):
    print('  %-6s: %.4f' % (p, G[G.problema == p].acc.mean()))
print('  contradicao TOTAL (p+=p-=0) em %d/%d geracoes (%.1f%%)'
      % (((G.p_mais == 0) & (G.p_menos == 0)).sum(), len(G),
         100*((G.p_mais == 0) & (G.p_menos == 0)).sum()/len(G)))

# ---- canonica
met = pd.read_csv(os.path.join(RAIZ, 'ua-dd-saea/f5/metricas_finais_f52c.csv'))
n = met[(met.alg == 'c217') & (met.exp == 'main')].set_index('problema').igd_plus
paper_dtlz = dict(DTLZ2=6.9212e-2, DTLZ4=7.8816e-2, DTLZ7=1.9200e-1, DTLZ1=2.9867e+1, DTLZ3=6.7647e+1)
paper_wfg = dict(WFG4=8.9525e-2, WFG5=1.1186e-1, WFG9=1.3327e-1, WFG2=1.9643e-1, WFG1=1.1225)
for nome, pv in (('DTLZ', paper_dtlz), ('WFG', paper_wfg)):
    ks = list(pv); a = np.array([pv[k] for k in ks]); b = np.array([n[k] for k in ks])
    ra, rb = np.argsort(np.argsort(a))+1, np.argsort(np.argsort(b))+1
    print('\n== %s: paper=%s' % (nome, dict(zip(ks, np.round(a, 5)))))
    print('   nosso IGD+ =%s' % dict(zip(ks, np.round(b, 4))))
    print('   posicoes paper=%s nosso=%s -> iguais %d/5 ; Spearman rho=%.3f'
          % (list(ra), list(rb), int((ra == rb).sum()), spearmanr(a, b).statistic))
    print('   razao nosso/paper: %s' % dict(zip(ks, np.round(b/a, 3))))
