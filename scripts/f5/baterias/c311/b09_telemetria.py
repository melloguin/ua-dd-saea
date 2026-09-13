"""B09 — reconciliação da telemetria do ⑥ com a ③ (DI-10 / S.7.1):
f_best[j] == min(mu_j) da população da geração 51i ?  n_front1 == |ND(mu)| ?
n_acumulado == sum(total_points_per_model) ?  + schema/dtypes da ③ e colunas de classificador.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

rows, cel = [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    mt = meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    D = len(xcols(real)); M = len(fcols(real)); N = len(real)
    bu = busca(sur); mus = mucols(bu)
    dec = [e for e in evs if e.get('rec') == 'decision']
    g = bu['geracao'].astype(int)
    hit_fb = hit_nf = hit_fb1 = hit_nf1 = 0; nac_ok = 0
    for i, e in enumerate(dec):
        gg = 51 * (i + 1)
        for off, tag in ((0, ''), (-1, '1')):
            sub = bu[g == gg + off]
            if not len(sub):
                continue
            MU = sub[mus].values.astype(np.float64)
            fb = MU.min(axis=0)
            nd = int(nd_mask(MU).sum())
            fbl = np.array(e['f_best'], float)
            ok_fb = bool(np.allclose(fb, fbl, rtol=1e-5, atol=1e-8))
            ok_nf = bool(nd == e['n_front1'])
            if tag == '':
                hit_fb += ok_fb; hit_nf += ok_nf
                rows.append(dict(**mt, M=M, it=i + 1, ger=gg, pop=len(sub),
                                 f_best_log=json.dumps(np.round(fbl, 6).tolist()),
                                 f_best_rec=json.dumps(np.round(fb, 6).tolist()),
                                 ok_fbest=ok_fb, nfront1_log=e['n_front1'], nfront1_rec=nd,
                                 ok_nfront1=ok_nf,
                                 f_best_neg=bool((fbl < 0).any())))
            else:
                hit_fb1 += ok_fb; hit_nf1 += ok_nf
        nac_ok += int(e.get('n_acumulado') == int(np.sum(e['total_points_per_model'])))
    cel.append(dict(**mt, M=M, N=N, n_dec=len(dec),
                    hit_fbest_51i=hit_fb, hit_nfront1_51i=hit_nf,
                    hit_fbest_51i_1=hit_fb1, hit_nfront1_51i_1=hit_nf1,
                    nacum_ok=nac_ok,
                    pred_tipo=';'.join(sorted(map(str, sur['pred_tipo'].dropna().unique()))[:3]),
                    pred_classe_nn=int(sur['pred_classe'].notna().sum()),
                    pred_score_nn=int(sur['pred_score'].notna().sum()),
                    pred_conf_nn=int(sur['pred_confianca'].notna().sum()),
                    modelo_flags=';'.join(sorted(map(str, sur['modelo_flag'].dropna().unique()))),
                    regimes=';'.join(sorted(map(str, sur['regime'].dropna().unique()))),
                    dtype_mu=str(sur[mus[0]].dtype), dtype_x=str(sur[xcols(sur)[0]].dtype),
                    transf=';'.join(sorted(map(str, sur['transf_tipo'].dropna().unique()))) or 'NULL'))
    print(label, 'fbest', hit_fb, '/', len(dec), 'nfront1', hit_nf, '/', len(dec))

r = pd.DataFrame(rows); c = pd.DataFrame(cel)
salva(r, 'b09_telemetria_iter.csv'); salva(c, 'b09_telemetria_cel.csv')
tot = c.n_dec.sum()
print('\ndecisões:', tot)
print('f_best == min(mu) da ger 51i :', int(c.hit_fbest_51i.sum()), f'({100*c.hit_fbest_51i.sum()/tot:.1f}%)',
      '| na ger 51i-1:', int(c.hit_fbest_51i_1.sum()))
print('n_front1 == |ND(mu)| na 51i  :', int(c.hit_nfront1_51i.sum()), f'({100*c.hit_nfront1_51i.sum()/tot:.1f}%)',
      '| na 51i-1:', int(c.hit_nfront1_51i_1.sum()))
print('n_acumulado == sum(tppm)     :', int(c.nacum_ok.sum()), '/', tot)
print('células com f_best negativo em alguma iteração:',
      int(r.groupby('label').f_best_neg.any().sum()))
print('\nschema:', c.pred_tipo.value_counts().to_dict(), '| pred_classe não-nulos:', int(c.pred_classe_nn.sum()),
      '| pred_score:', int(c.pred_score_nn.sum()), '| pred_confianca:', int(c.pred_conf_nn.sum()))
print('modelo_flags:', c.modelo_flags.value_counts().to_dict())
print('regimes:', c.regimes.value_counts().to_dict())
print('dtypes:', c.dtype_mu.value_counts().to_dict(), c.dtype_x.value_counts().to_dict())
print('transf:', c.transf.value_counts().to_dict())
