"""Bateria b1 - parte 4b: POR QUE o argmax-EI do pool final != best logado em ~1/4 das
iteracoes. Hipotese: ei_best = MIN de e0_trace sobre TODAS as geracoes internas do GA
(rastreamento elitista), enquanto a (3) grava so a POPULACAO FINAL (DEF-C2).
Testa: match(pool) <=> ei_best == ultimo valor de e0_trace.
Alem disso: nao-greedy EXATO no subconjunto casado + percentis.
Saida: b1_joia_diag.csv
"""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])
joia = pd.read_csv(f'{OUT}/b1_joia_iter.csv')
joia['match'] = (joia.d_mu < 1e-5) & (joia.d_sg < 1e-5)

rows = []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    sub = joia[joia.problema == p].set_index('geracao')
    r = []
    for e in ge:
        e0 = e['e0_trace']
        last_eq = abs(e0[-1] - e['ei_best']) <= 1e-12 * max(abs(e['ei_best']), 1e-30)
        argmin_pos = int(np.argmin(e0))
        r.append(dict(problema=p, geracao=e['geracao'], last_eq=last_eq,
                      argmin_pos=argmin_pos, n_e0=len(e0),
                      pos_rel=argmin_pos / max(len(e0) - 1, 1),
                      match=bool(sub.loc[e['geracao'], 'match']),
                      nao_greedy=bool(sub.loc[e['geracao'], 'nao_greedy']),
                      perc_mu=float(sub.loc[e['geracao'], 'perc_mu']),
                      perc_sg=float(sub.loc[e['geracao'], 'perc_sg']),
                      mu_sel=float(sub.loc[e['geracao'], 'mu_sel']),
                      mu_min=float(sub.loc[e['geracao'], 'mu_min']),
                      mu_best_log=e['mu_best']))
    d = pd.DataFrame(r)
    ct = pd.crosstab(d.last_eq, d['match'])
    m = d[d['match']]
    rows.append(dict(problema=p, n=len(d), n_match=int(d['match'].sum()),
                     n_last_eq=int(d.last_eq.sum()),
                     concord=int((d.last_eq == d['match']).sum()),
                     pos_rel_med=float(d.pos_rel.median()),
                     ng_match=float(m.nao_greedy.mean()) if len(m) else np.nan,
                     n_ng_match=int(m.nao_greedy.sum()) if len(m) else 0, n_m=len(m),
                     perc_mu_med_m=float(m.perc_mu.median()) if len(m) else np.nan,
                     perc_sg_med_m=float(m.perc_sg.median()) if len(m) else np.nan,
                     # criterio "havia mu menor no pool final" (independe de casar)
                     ng_pool=float((d.mu_min < d.mu_best_log - 1e-6 * np.maximum(np.abs(d.mu_best_log), 1)).mean())))
    print(f'{p:10s} n={len(d):4d} match={int(d["match"].sum()):4d} last_eq={int(d.last_eq.sum()):4d} '
          f'concord={int((d.last_eq==d["match"]).sum()):4d} NG|match={m.nao_greedy.mean() if len(m) else np.nan:.3f} '
          f'percmu|match={m.perc_mu.median() if len(m) else np.nan:.3f} percsg|match={m.perc_sg.median() if len(m) else np.nan:.3f}')
    d.to_csv(f'{OUT}/_tmp_{p}.csv', index=False)

df = pd.DataFrame(rows); df.to_csv(f'{OUT}/b1_joia_diag.csv', index=False)
allr = pd.concat([pd.read_csv(f'{OUT}/_tmp_{p}.csv') for p in probs])
allr.to_csv(f'{OUT}/b1_joia_diag_iter.csv', index=False)
for p in probs:
    os.remove(f'{OUT}/_tmp_{p}.csv')
print()
print('TOTAL n', len(allr), 'match', allr['match'].sum(), 'last_eq', allr.last_eq.sum(),
      'concordancia last_eq<->match', (allr.last_eq == allr['match']).sum())
print(pd.crosstab(allr.last_eq, allr['match']))
m = allr[allr['match']]
print('\nSUBCONJUNTO CASADO (n=%d):' % len(m))
print('  nao-greedy:', m.nao_greedy.sum(), '/', len(m), '=', round(m.nao_greedy.mean(), 4))
print('  percentil de mu do escolhido: mediana', m.perc_mu.median(), 'media', round(m.perc_mu.mean(), 4))
print('  percentil de sigma do escolhido: mediana', m.perc_sg.median(), 'media', round(m.perc_sg.mean(), 4))
print('  percentil sigma | nao-greedy:', m.loc[m.nao_greedy, 'perc_sg'].median(),
      ' | greedy:', m.loc[~m.nao_greedy, 'perc_sg'].median())
print('  percentil mu | nao-greedy:', m.loc[m.nao_greedy, 'perc_mu'].median(),
      ' | greedy:', m.loc[~m.nao_greedy, 'perc_mu'].median())
print('\nposicao relativa do argmin(e0_trace): mediana', allr.pos_rel.median(),
      ' frac no ultimo passo', (allr.pos_rel == 1).mean())
print('criterio "havia mu menor no pool final" (todas):',
      round(float((allr.mu_min < allr.mu_best_log - 1e-6 * np.maximum(np.abs(allr.mu_best_log), 1)).mean()), 4))
