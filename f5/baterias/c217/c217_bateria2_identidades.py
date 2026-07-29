#!/usr/bin/env python
"""BATERIA 2 — as IDENTIDADES FECHADAS do c217 (query-joia).
  |P|(g)      = |②(g)| se g==1 (init, sem cap) senão min(N,|②(g)|)
  Pbest       = ceil(|P|/4)             Pworst = ceil(|P|/2) - ceil(|P|/4)
  n_best      = ceil(3/4*Pbest)         n_worst = ceil(3/4*Pworst)
  n_treino    = n_best+n_worst          n_pares = n_treino*(n_treino-1)   [todos x todos]
  n_Pmid      = 2*floor(|P|/8)+1        (janela ÍMPAR centrada na fronteira do corte) = lnum
  lote_max    = floor(lnum/2) = floor(|P|/8)
  |Dvalid|    = (Pbest-n_best) + (Pworst-n_worst)
  p+ , p- , contradicoes: p+*|Dvalid| e p-*|Dvalid| inteiros, e soma == |Dvalid|
Escreve c217_identidades.csv (por geração) + resumo no stdout.
"""
import os, json, math
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c217'
G = pd.read_pickle(f'{OUT}/c217_geracoes_pop.pkl')
N = 50

P = np.where(G.geracao == 1, G.pop_n, np.minimum(N, G.pop_n)).astype(float)
G['P'] = P
G['Pbest'] = np.ceil(P / 4)
G['Pworst'] = np.ceil(P / 2) - np.ceil(P / 4)
G['nb_pred'] = np.ceil(3 * G.Pbest / 4)
G['nw_pred'] = np.ceil(3 * G.Pworst / 4)
G['ntr_pred'] = G.nb_pred + G.nw_pred
G['npar_pred'] = G.ntr_pred * (G.ntr_pred - 1)
G['pmid_pred'] = 2 * np.floor(P / 8) + 1
G['lotemax_pred'] = np.floor(P / 8)
G['Dvalid'] = (G.Pbest - G.n_best) + (G.Pworst - G.n_worst)
G['k_mais'] = G.p_mais * G.Dvalid
G['k_menos'] = G.p_menos * G.Dvalid
G['soma_ok'] = np.isclose(G.k_mais + G.k_menos + G.n_contradicoes, G.Dvalid, atol=1e-6)
G['kint'] = np.isclose(G.k_mais, np.round(G.k_mais), atol=1e-6) & np.isclose(G.k_menos, np.round(G.k_menos), atol=1e-6)

tot = len(G)
def pc(m, nome):
    print(f'  {nome:52s} {int(m.sum()):5d}/{tot}  ({100*m.mean():6.3f}%)')

print(f'=== IDENTIDADES FECHADAS ({tot} gerações, 25 células) ===')
pc(G.nb_pred == G.n_best,   'n_best  == ceil(3/4*ceil(|P|/4))')
pc(G.nw_pred == G.n_worst,  'n_worst == ceil(3/4*(ceil(|P|/2)-ceil(|P|/4)))')
pc(G.ntr_pred == G.n_treino, 'n_treino == n_best+n_worst')
pc(G.npar_pred == G.n_pares_treino, 'n_pares == n_treino*(n_treino-1)  [todosxtodos]')
pc(G.pmid_pred == G.n_Pmid, 'n_Pmid  == 2*floor(|P|/8)+1  (= lnum)')
pc(G.soma_ok,               'p+*|Dv| + p-*|Dv| + contrad == |Dv|')
pc(G.kint,                  'p+*|Dv| e p-*|Dv| INTEIROS')
# regra tripla
est_pred = np.where(G.p_mais > G.delta, 1, np.where(G.p_menos > G.delta, 2, 3))
pc(est_pred == G.estado,    'estado == regra tripla (p+>d ->1; p->d ->2; else 3)')
# motivo legivel casa com a desigualdade
import re
def parse(m):
    a = re.search(r'Error1=([0-9.]+)', m); b = re.search(r'Error2=([0-9.]+)', m)
    c = re.search(r'estado (\d)', m)
    return (float(a.group(1)) if a else np.nan, float(b.group(1)) if b else np.nan, int(c.group(1)) if c else -1)
pp = G.motivo.map(parse)
G['m_e1'] = [x[0] for x in pp]; G['m_e2'] = [x[1] for x in pp]; G['m_st'] = [x[2] for x in pp]
pc((G.m_st == G.estado), 'motivo(texto) declara o MESMO estado')
pc(np.isclose(G.m_e1, G.p_mais, atol=5e-5) & np.isclose(G.m_e2, G.p_menos, atol=5e-5), 'motivo(texto) declara os MESMOS p+/p-')
# lote
m12 = G.estado.isin([1, 2])
print(f'  lote<=floor(|P|/8) nos estados 1/2:             {int((G.loc[m12,"lote"]<=G.loc[m12,"lotemax_pred"]).sum())}/{int(m12.sum())}')
print(f'  lote==1 no estado 3:                            {int((G.loc[~m12,"lote"]==1).sum())}/{int((~m12).sum())}')
print(f'  lote==floor(|P|/8) nos estados 1/2:             {int((G.loc[m12,"lote"]==G.loc[m12,"lotemax_pred"]).sum())}/{int(m12.sum())}')
print('  eventos estado 1/2 com lote != lotemax:')
print(G.loc[m12 & (G.lote != G.lotemax_pred), ['problema','geracao','P','estado','lote','lotemax_pred','p_mais','p_menos','Dvalid']].to_string())
# granularidade
print()
print('  distribuição |Dvalid|:', G.Dvalid.value_counts().sort_index().to_dict())
st = G[G.P == 50]
print(f'  gerações com |P|=50 (steady): {len(st)}; |Dvalid|==6 em {int((st.Dvalid==6).sum())}')
print(f'  gerações |P|<50 (ramp):       {int((G.P<50).sum())} em {G[G.P<50].problema.nunique()} células')
print(f'  gerações gen1 |P|=init:       {int((G.geracao==1).sum())}')
# estados
print()
print('  estados:', G.estado.value_counts().to_dict())
print('  células com >=1 disparo st1/st2:', G[m12].problema.nunique())
print(G[m12].groupby(['problema','estado']).size().to_string())
print()
print('  st1: k_mais/Dvalid =', sorted(set(zip(G[G.estado==1].k_mais.astype(int), G[G.estado==1].Dvalid.astype(int)))))
print('  st2: k_menos/Dvalid =', sorted(set(zip(G[G.estado==2].k_menos.astype(int), G[G.estado==2].Dvalid.astype(int)))))
print('  paridade das gerações de disparo: par=%d ímpar=%d' % (int((G[m12].geracao % 2 == 0).sum()), int((G[m12].geracao % 2 == 1).sum())))
# fe_treino_max
print()
q = G.sort_values(['problema','geracao']).groupby('problema').fe_treino_max.apply(lambda s: int((np.diff(s.to_numpy())<0).sum()))
print('  quedas de fe_treino_max por célula:', q.to_dict())
print('  total quedas:', int(q.sum()), '| células com queda:', int((q>0).sum()))
print('  fe_treino_max < arc_size em', int((G.fe_treino_max < G.arc_size).sum()), '/', tot)
print('  fe_treino_max >= n_treino  em', int((G.fe_treino_max >= G.n_treino).sum()), '/', tot)
# arc / fe
print()
print('  arc_size == fe  em', int((G.arc_size==G.fe).sum()), '/', tot)
print('  arc_size(g) == |②(g)| + lote(g)?', int((G.arc_size == G.pop_n + G.lote).sum()), '/', tot)
G.to_pickle(f'{OUT}/c217_identidades.pkl')
G.drop(columns=['f_best','motivo']).to_csv(f'{OUT}/c217_identidades.csv', index=False)
print('\nsalvo c217_identidades.csv/.pkl')
