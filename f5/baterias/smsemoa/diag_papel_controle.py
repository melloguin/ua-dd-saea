#!/usr/bin/env python
"""Papel de CONTROLE (regua) do piso smsemoa + saude em escala.
(a) posicao do smsemoa no main (IGD+ e HV) vs os 3 outros pisos e vs as configs SA;
(b) trajetorias de 20 checkpoints — violacoes de monotonicidade do IGD+;
(c) tempo/maquina."""
import os, json, glob
import numpy as np, pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = os.path.dirname(os.path.abspath(__file__))
PISOS = ['nsga2', 'nsga3', 'moead', 'smsemoa']

m = pd.read_csv(F5 + '/metricas_finais_f52c.csv')
main = m[m.exp == 'main'].copy()
probs = sorted(main.loc[main.alg == 'smsemoa', 'problema'].unique())
main = main[main.problema.isin(probs)]
algs = sorted(main.alg.unique())
print('configs no main:', len(algs), algs)
print('celulas main:', len(main))

# --- rank de IGD+ (menor = melhor) por problema, entre TODAS as configs presentes ---
main['rank_igd'] = main.groupby('problema').igd_plus.rank(method='min')
main['n_no_prob'] = main.groupby('problema').igd_plus.transform('size')
main['rank_hv'] = main.groupby('problema').hv.rank(method='min', ascending=False)
sm = main[main.alg == 'smsemoa'].set_index('problema')

# --- entre os 4 pisos ---
pis = main[main.alg.isin(PISOS)].copy()
pis['rank_piso_igd'] = pis.groupby('problema').igd_plus.rank(method='min')
pis['rank_piso_hv'] = pis.groupby('problema').hv.rank(method='min', ascending=False)
tab = pis.pivot(index='problema', columns='alg', values='igd_plus')
tab['melhor_piso'] = tab[PISOS].idxmin(axis=1)
tab['smsemoa_rank'] = pis[pis.alg == 'smsemoa'].set_index('problema').rank_piso_igd
tabhv = pis.pivot(index='problema', columns='alg', values='hv')
tabhv['melhor_piso_hv'] = tabhv[PISOS].idxmax(axis=1)
tab['razao_ao_melhor'] = tab['smsemoa'] / tab[PISOS].min(axis=1)
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 200)
print('\n=== IGD+ dos 4 pisos ===')
print(tab.round(5).to_string())
print('\nmelhor piso (IGD+) contagem:', tab.melhor_piso.value_counts().to_dict())
print('melhor piso (HV)  contagem:', tabhv.melhor_piso_hv.value_counts().to_dict())
print('rank do smsemoa entre pisos (IGD+):', tab.smsemoa_rank.value_counts().sort_index().to_dict(),
      '| media', round(tab.smsemoa_rank.mean(), 2))

# --- smsemoa vs SA-MOEA ---
sa = main[~main.alg.isin(PISOS)]
res = []
for p in probs:
    s = sm.loc[p]
    sub = sa[sa.problema == p]
    res.append(dict(problema=p, igd_sms=s.igd_plus, rank_global=int(s.rank_igd), n_configs=int(s.n_no_prob),
                    rank_hv=int(s.rank_hv), n_sa=len(sub),
                    sa_pior_que_piso=int((sub.igd_plus > s.igd_plus).sum()),
                    sa_melhor=int((sub.igd_plus < s.igd_plus).sum()),
                    melhor_sa=sub.loc[sub.igd_plus.idxmin(), 'alg'] if len(sub) else None,
                    igd_melhor_sa=sub.igd_plus.min() if len(sub) else np.nan))
r = pd.DataFrame(res)
r['razao_sms_melhorSA'] = r.igd_sms / r.igd_melhor_sa
print('\n=== smsemoa (piso) vs as configs SA ===')
print(r.round(4).to_string(index=False))
print('\nrank global medio do smsemoa (IGD+):', round(r.rank_global.mean(), 2), 'de', r.n_configs.max())
print('SA piores que o piso: total', int(r.sa_pior_que_piso.sum()), 'de', int(r.n_sa.sum()),
      f'({100*r.sa_pior_que_piso.sum()/r.n_sa.sum():.1f}%)')
print('problemas em que o piso bate TODAS as SA:', list(r.loc[r.sa_melhor == 0, 'problema']))
r.to_csv(OUT + '/diag_papel_controle.csv', index=False)
tab.to_csv(OUT + '/diag_pisos_igd.csv')

# --- trajetorias ---
tr = []
for p in probs:
    j = json.load(open(f'{F5}/trajetorias/main_smsemoa_{p}_42.json'))
    ig = np.array([x['igd_plus'] for x in j])
    hv = np.array([x['hv'] for x in j])
    nd = np.array([x['n_nd'] for x in j])
    fe = np.array([x['fe'] for x in j])
    tr.append(dict(problema=p, n_ckpt=len(j), viol_igd=int((np.diff(ig) > 1e-12).sum()),
                   viol_hv=int((np.diff(hv) < -1e-12).sum()),
                   viol_nd=int((np.diff(nd) < 0).sum()),
                   igd_ini=ig[0], igd_fim=ig[-1], ganho=1 - ig[-1] / ig[0] if ig[0] else np.nan,
                   fe_ini=int(fe[0]), fe_fim=int(fe[-1]), nd_fim=int(nd[-1])))
t = pd.DataFrame(tr)
t.to_csv(OUT + '/diag_trajetorias.csv', index=False)
print('\n=== trajetorias (20 checkpoints) ===')
print(t.round(4).to_string(index=False))
print('Σ transicoes:', int((t.n_ckpt - 1).sum()), '| Σ violacoes IGD+:', int(t.viol_igd.sum()),
      '| Σ violacoes HV:', int(t.viol_hv.sum()), '| Σ violacoes |ND|:', int(t.viol_nd.sum()))

# --- tempo ---
tp = pd.read_csv(F5 + '/tempo_f52d.csv')
tps = tp[(tp.alg == 'smsemoa')]
print('\n=== tempo ===')
print('maquinas:', tps.maquina.value_counts().to_dict())
print('wall total (h-core):', round(tps.wall_s.sum() / 3600, 4), '| mediana s:', round(tps.wall_s.median(), 2),
      '| max', round(tps.wall_s.max(), 2), tps.loc[tps.wall_s.idxmax(), 'problema'])
tpp = tp[tp.alg.isin(PISOS) & (tp.exp == 'main')]
print(tpp.groupby('alg').wall_s.agg(['sum', 'median']).round(2).to_string())
