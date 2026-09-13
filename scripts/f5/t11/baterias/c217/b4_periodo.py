#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 4 — o PERÍODO do emparelhamento posicional-cíclico, lido do próprio
pred_score. Refuta o null ingênuo da b3 (permutação destrói a autocorrelação
espacial de Sobol) trocando-o por um VARREDURA DE PERÍODO: se RBFNNPC.m:59-62
vale, a variância entre classes de resíduo tem de PICAR em m == n_Pmid.
Só períodos ÍMPARES entram (Sobol é base-2: períodos pares têm artefato)."""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT  = os.path.join(REPO, 'f5/t11/baterias/c217')
B = os.path.join(D_EV, 'smoke_matlab/experiments/main/c217/exp_main_c217_MMF1_42')

rows = [json.loads(l) for l in open(B + '.jsonl') if l.strip()]
gen  = {r['geracao']: r for r in rows if r.get('rec') == 'c217_gen'}
sur  = pq.read_table(B + '__surrogate.parquet').to_pandas()
sb   = sur[sur.regime == 'sonda']
CAND = [m for m in range(3, 30) if m % 2 == 1]

def stat(s, m):
    """V(m) normalizada: var das médias de classe × S / (sigma²·(m-1))."""
    j = np.arange(len(s)); r = (j + 1) % m
    mu = np.array([s[r == k].mean() for k in range(m)])
    v = mu.var(ddof=0) * m / (m - 1)
    return v * len(s) / max(s.var(ddof=0), 1e-12)

res = []
for g, blk in sb.groupby('geracao'):
    s = blk.pred_score.values.astype(float)
    n = int(gen[int(g)]['n_Pmid'])
    vs = {m: stat(s, m) for m in CAND}
    ordem = sorted(CAND, key=lambda m: -vs[m])
    res.append(dict(g=int(g), n=n, rank_de_n=ordem.index(n)+1, argmax=ordem[0],
                    V_n=vs[n], V_2o=vs[ordem[1] if ordem[0] == n else ordem[0]],
                    razao=vs[n]/max(vs[ordem[1] if ordem[0] == n else ordem[0]], 1e-12)))
df = pd.DataFrame(res)
print('======== varredura de período (22 blocos, m ímpar 3..29) ========')
print('argmax(V) == n_Pmid                    : %d/%d' % (int((df.argmax == df.n).sum()), len(df)))
print('n_Pmid entre os 3 primeiros            : %d/%d' % (int((df.rank_de_n <= 3).sum()), len(df)))
print('rank mediano de n_Pmid (de 14 cands)   : %.1f' % df.rank_de_n.median())
print('razao V(n)/V(2o melhor) mediana        : %.2f' % df.razao.median())
print('V(n) mediana / V(m!=n) mediana         : %.2f / %.2f' % (
      df.V_n.median(), np.median([stat(sb[sb.geracao == r.g].pred_score.values.astype(float), m)
                                  for r in df.itertuples() for m in CAND if m != r.n])))
print()
print(df.to_string(index=False))
df.to_csv(os.path.join(OUT, 'c217_t11_periodo.csv'), index=False)
