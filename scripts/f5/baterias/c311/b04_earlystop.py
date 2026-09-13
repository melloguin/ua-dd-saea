"""B04 — reconstrução EXATA da regra de early-stop do código (B15.8):
delta = total_points[counter] - sequence[counter-3], gatilho counter>5 (mínimo 6 iterações).
Testa a identidade contra `delta_total_point` logado, em todas as decisões das 54 células."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

rows, cel = [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real',))
    mt = meta(label, man)
    real = dfs['real']; D = len(xcols(real)); M = len(fcols(real)); N = len(real)
    dec = [e for e in evs if e.get('rec') == 'decision']
    I_eff = len(dec); I_max = math.ceil(N / (10 * D))
    seq = [float(np.sum(e['total_points_per_model'])) for e in dec]   # soma sobre objetivos
    seqm = [float(np.mean(e['total_points_per_model'])) for e in dec]
    logged = [e.get('delta_total_point') for e in dec]
    hits = {'lag3_soma': 0, 'lag3_media': 0, 'lag2_soma': 0, 'lag1_soma': 0}
    for i, e in enumerate(dec):
        it = i + 1
        cand = {}
        for nome, s in (('soma', seq), ('media', seqm)):
            for lag in (1, 2, 3):
                j = i - lag
                cand[f'lag{lag}_{nome}'] = (s[i] - s[j]) if j >= 0 else None
        for k in hits:
            if cand.get(k) is not None and logged[i] is not None and abs(cand[k] - logged[i]) < 1e-6:
                hits[k] += 1
        rows.append(dict(**mt, D=D, M=M, N=N, I_eff=I_eff, I_max=I_max, it=it,
                         total_pts=seq[i], logged=logged[i],
                         lag3_soma=cand['lag3_soma'], lag2_soma=cand['lag2_soma'],
                         lag3_media=cand['lag3_media'],
                         early_stop=e.get('early_stop'),
                         eh_ultima=(it == I_eff), it_maior_5=(it > 5),
                         chega_Imax=(I_eff == I_max)))
    es = [bool(e.get('early_stop')) for e in dec]
    cel.append(dict(**mt, D=D, M=M, N=N, I_eff=I_eff, I_max=I_max,
                    n_true=sum(es), idx_true=';'.join(str(i + 1) for i, v in enumerate(es) if v),
                    true_na_ultima=(es[-1] if es else None),
                    corte=(I_eff < I_max),
                    delta_ultimo=logged[-1],
                    logged_unicos=';'.join(sorted({str(x) for x in logged})[:6]),
                    hits_lag3_soma=hits['lag3_soma'], hits_lag3_media=hits['lag3_media'],
                    hits_lag2_soma=hits['lag2_soma'], hits_lag1_soma=hits['lag1_soma'],
                    n_dec=I_eff, seq=';'.join(str(int(x)) for x in seq[:12])))
r = pd.DataFrame(rows); c = pd.DataFrame(cel)
salva(r, 'b04_earlystop_iter.csv'); salva(c, 'b04_earlystop_cel.csv')
print('\n--- identidade da regra (só iterações com lag disponível) ---')
for k in ['lag1_soma', 'lag2_soma', 'lag3_soma', 'lag3_media']:
    n = int(c['hits_' + k].sum()) if 'hits_' + k in c else 0
    print(k, n, '/', len(r))
print('\n--- early_stop=True ---')
print(c[c.n_true > 0][['label', 'tier', 'N', 'D', 'I_eff', 'I_max', 'n_true', 'idx_true',
                       'true_na_ultima', 'corte', 'delta_ultimo']].to_string())
print('\n--- células sem early_stop ---')
print(c[c.n_true == 0].groupby('tier').size().to_dict())
print('\nmenor I_eff observado:', c.I_eff.min(), ' — nenhuma célula parou antes de 6?',
      bool(((c.I_eff >= 6) | (c.I_eff == c.I_max)).all()))
print('\n--- delta logado por tier ---')
print(r.groupby('tier')['logged'].describe().to_string())
