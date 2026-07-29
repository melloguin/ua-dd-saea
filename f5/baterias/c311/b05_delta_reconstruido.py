"""B05 — TESTE DISCRIMINATIVO do early-stop: reconstruir `delta_total_point` a partir
da ③, usando σ-NaN como marcador de "solução em folha SEM GP" (DI-16.9).

V_g = nº de pares (indivíduo, objetivo) da população da geração g com sigma NÃO-NaN
      (= soluções que caem em folha COM GP, somadas sobre os M objetivos).
Hipótese do código (B15.8): delta_i = V(g_i) - V(g_{i-2}), sentinela 1.0 para i<=5,
early_stop <=> delta==0.
Testam-se as gerações-âncora 51i, 51i-1, 51(i-1)+1 e os lags 1,2,3.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

rows, cel = [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    mt = meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    D = len(xcols(real)); M = len(fcols(real)); N = len(real)
    bu = busca(sur); sg = sigcols(bu)
    dec = [e for e in evs if e.get('rec') == 'decision']
    I_eff = len(dec)
    g = bu['geracao'].astype(float)
    # V por geração (soma sobre objetivos de σ não-NaN) e P (tamanho da população)
    ok = (~bu[sg].isna()).sum(axis=1)
    V = ok.groupby(g).sum()
    P = g.groupby(g).size()
    logged = [e.get('delta_total_point') for e in dec]
    es = [bool(e.get('early_stop')) for e in dec]
    cands = {}
    for anc, off in (('51i', 0), ('51i-1', -1), ('51i-50', -50)):
        seq = []
        for i in range(1, I_eff + 1):
            gg = 51 * i + off
            seq.append(float(V.get(gg, np.nan)))
        for lag in (1, 2, 3):
            v = []
            for i in range(I_eff):
                v.append(seq[i] - seq[i - lag] if i - lag >= 0 else np.nan)
            cands[f'{anc}_lag{lag}'] = v
    best = {}
    for k, v in cands.items():
        hit = sum(1 for i in range(I_eff)
                  if i + 1 > 5 and logged[i] is not None and not np.isnan(v[i])
                  and abs(v[i] - logged[i]) < 1e-6)
        tot = sum(1 for i in range(I_eff) if i + 1 > 5)
        best[k] = (hit, tot)
    for i in range(I_eff):
        rows.append(dict(**mt, M=M, N=N, it=i + 1, logged=logged[i], early=es[i],
                         V_51i=float(V.get(51 * (i + 1), np.nan)),
                         P_51i=float(P.get(51 * (i + 1), np.nan)),
                         **{k: (None if np.isnan(v[i]) else float(v[i])) for k, v in cands.items()}))
    cel.append(dict(**mt, M=M, N=N, I_eff=I_eff,
                    sentinela_ok=all((logged[i] == 1.0) for i in range(min(5, I_eff))),
                    sentinela_viol=sum(1 for i in range(I_eff) if (i + 1 <= 5) != (logged[i] == 1.0 and i + 1 <= 5)),
                    es_iff_zero=all((es[i] == (logged[i] == 0.0)) for i in range(I_eff)),
                    **{('hit_' + k): best[k][0] for k in best},
                    n_pos5=sum(1 for i in range(I_eff) if i + 1 > 5)))
    print(label, {k: best[k] for k in ['51i_lag2', '51i-1_lag2', '51i-50_lag2', '51i_lag3']})

r = pd.DataFrame(rows); c = pd.DataFrame(cel)
salva(r, 'b05_delta_iter.csv'); salva(c, 'b05_delta_cel.csv')
tot = c.n_pos5.sum()
print('\niterações com it>5:', tot)
for k in sorted([x for x in c.columns if x.startswith('hit_')]):
    print(k, int(c[k].sum()), '/', tot, f'{100*c[k].sum()/max(tot,1):.1f}%')
print('sentinela it<=5 == 1.0 em', int(c.sentinela_ok.sum()), '/54')
print('early_stop <=> delta==0 em', int(c.es_iff_zero.sum()), '/54')
