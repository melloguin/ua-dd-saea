#!/usr/bin/env python
"""BATERIA 4 — c122: saude em escala (trajetorias 20-checkpoints + pisos + tempo).

Le SOMENTE insumos pre-computados da F5.2 (nao recomputa metrica).
"""
import json, os
import numpy as np
import pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/c122'
PISOS = ['moead', 'nsga2', 'nsga3', 'smsemoa']

m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
t = pd.read_csv(f'{F5}/tempo_f52d.csv')
main = m[m.exp == 'main']
c = main[main.alg == 'c122'].set_index('problema')

rows = []
for prob in c.index:
    r = {'problema': prob, 'igd_plus': c.loc[prob, 'igd_plus'],
         'hv': c.loc[prob, 'hv'], 'igd': c.loc[prob, 'igd'],
         'gd': c.loc[prob, 'gd'], 'n_nd': c.loc[prob, 'n_nd']}
    p = main[(main.problema == prob) & (main.alg.isin(PISOS))]
    if len(p):
        best = p.igd_plus.min()
        r['piso_melhor'] = best
        r['piso_alg'] = p.loc[p.igd_plus.idxmin(), 'alg']
        r['razao_vs_piso'] = r['igd_plus'] / best if best > 0 else np.nan
        r['bate_piso'] = bool(r['igd_plus'] <= best)
        r['dentro_ruido'] = bool(r['igd_plus'] <= best * 1.5898)
    # rank entre todos os algs do main nesse problema
    tot = main[main.problema == prob].sort_values('igd_plus')
    r['rank_igdplus'] = int(list(tot.alg).index('c122') + 1)
    r['n_algs'] = len(tot)
    # trajetoria
    tj = json.load(open(f'{F5}/trajetorias/main_c122_{prob}_42.json'))
    ser = [x['igd_plus'] for x in tj] if isinstance(tj, list) else tj['igd_plus']
    fes = [x['fe'] for x in tj] if isinstance(tj, list) else None
    v = np.array([x for x in ser if x is not None], dtype=float)
    d = np.diff(v)
    r['traj_n'] = len(v)
    r['traj_violacoes'] = int((d > 1e-12).sum())
    r['traj_max_subida'] = float(d.max()) if len(d) else np.nan
    r['traj_ini'] = float(v[0]); r['traj_fim'] = float(v[-1])
    r['traj_fe_ini'] = fes[0] if fes else None; r['traj_fe_fim'] = fes[-1] if fes else None
    r['traj_ganho'] = float(v[0] / v[-1]) if v[-1] > 0 else np.nan
    rows.append(r)

d = pd.DataFrame(rows)
d = d.merge(t[(t.alg == 'c122') & (t.exp == 'main')][['problema', 'maquina', 'wall_s']],
            on='problema', how='left')
d.to_csv(f'{OUT}/c122_saude_escala.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(d.to_string())
print()
print('bate melhor piso:', int(d.bate_piso.sum()), '/', len(d))
print('dentro do ruido O-18 (<=1,5898x):', int(d.dentro_ruido.sum()), '/', len(d))
print('rank medio IGD+:', round(d.rank_igdplus.mean(), 2), 'de', int(d.n_algs.max()))
print('violacoes de trajetoria:', int(d.traj_violacoes.sum()), 'em',
      int(d.traj_n.sum() - len(d)), 'transicoes')
print('h-core total:', round(d.wall_s.sum() / 3600, 2))
print('maquinas:', d.maquina.value_counts().to_dict())
