#!/usr/bin/env python
"""B07 — U11 refinado (erro de fantasia SO nos pontos que viraram FE depois) + ledger de FEs
(init + Σlote − cache_hits + lote_final = fe_final) + assinatura do hard_stop/overshoot."""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT

OUT = os.path.dirname(os.path.abspath(__file__))
rows, det = [], []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]
    ftr = [e for e in ev if e.get('rec') == 'footer'][0]
    D, M = h['D'], h['M']
    fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]
    xc = [f'x{i}' for i in range(D)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    hs = [e for e in ev if e.get('rec') == 'guard' and e['name'] == 'hard_stop']
    ch = [e for e in ev if e.get('rec') == 'guard' and e['name'] == 'cache_hit']
    on = sur[sur.regime == 'online']
    ridx = real.set_index('solution_id')
    fei = real.set_index('solution_id').fe_index

    inf = on[on.real_solution_id.notna()].copy()
    inf['sid'] = inf.real_solution_id.astype(int)
    inf['fe_sol'] = fei.loc[inf.sid].values
    fetm = {g['geracao']: g['fe_treino_max'] for g in gens}
    inf['fetm'] = inf.geracao.map(fetm)
    fut = inf[inf.fe_sol > inf.fetm]        # ponto que AINDA nao estava no arquivo -> fantasia real
    pas = inf[inf.fe_sol <= inf.fetm]       # ponto JA no arquivo -> interpolacao

    def stats(d, lab):
        if not len(d):
            return {}
        mu = d[mc].values.astype(np.float64)
        fr = ridx.loc[d.sid, fc].values.astype(np.float64)
        e = mu - fr
        return {f'{lab}_n': len(d), f'{lab}_mae': float(np.median(np.abs(e))),
                f'{lab}_wape': float(np.abs(e).sum() / np.abs(fr).sum()),
                f'{lab}_otim': float((e < 0).mean()), f'{lab}_maxabs': float(np.abs(e).max())}

    r = dict(problema=pb, D=D, M=M, n_rsid=len(inf), n_fut=len(fut), n_pas=len(pas))
    r.update(stats(fut, 'fut')); r.update(stats(pas, 'pas'))
    # ledger
    somalote = sum(g['lote'] for g in gens)
    r['init'] = 11 * D - 1
    r['soma_lote'] = somalote
    r['cache'] = len(ch)
    r['fe_final'] = man['fe_final']
    r['lote_final'] = man['fe_final'] - (11 * D - 1) - somalote + len(ch)
    r['ledger_ok'] = 1 <= r['lote_final'] <= 2 * man['params']['N_subpop']
    r['hard_stop'] = len(hs)
    r['hs_fe'] = hs[0]['fe'] if hs else None
    r['hs_igual_maxfe'] = (hs[0]['fe'] == man['maxfe']) if hs else None
    r['termino'] = ftr.get('termino')
    r['cache_init'] = sum(1 for e in ch if e['fe'] <= 11 * D - 1)
    rows.append(r)
    print('ok', pb, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b07_fantasia_ledger.csv'), index=False)
pd.set_option('display.width', 320, 'display.max_columns', 100)
print(df.round(4).to_string())
print()
print('TOT rsid=%d  futuros=%d  passados=%d' % (df.n_rsid.sum(), df.n_fut.sum(), df.n_pas.sum()))
print('interpolacao (pas) MAE mediano global: %.3e' % df.pas_mae.median())
print('fantasia (fut) MAE mediano global: %.3e ; otimista mediano %.3f' % (df.fut_mae.median(), df.fut_otim.median()))
print('ledger fecha em', df.ledger_ok.sum(), '/', len(df), ' | lote_final', df.lote_final.min(), '-', df.lote_final.max())
print('hard_stop com fe==maxfe:', df.hs_igual_maxfe.sum(), '/', df.hard_stop.sum())
print('cache_hit no init (c0):', df.cache_init.tolist())
