"""B10 — custo de predição: taxa da BUSCA (loop 1-ponto-por-linha) x taxa da SONDA
(predict_batch novo, DI-16.13/C311-12) + âncora J de escalabilidade (@50k) +
invariante de timing com tolerância ULP-float32."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *
rows = []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate', 'timing'))
    mt = meta(label, man); real, sur, tim = dfs['real'], dfs['surrogate'], dfs['timing']
    D = len(xcols(real)); M = len(fcols(real)); N = len(real)
    bu = busca(sur); son = [e for e in evs if e.get('rec') == 'sonda']
    dec = [e for e in evs if e.get('rec') == 'decision']; I = len(dec)
    n_build = int((bu['geracao'].astype(int) <= 51 * I).sum())
    n_final = len(bu) - n_build
    t_busca_build = float(tim['tempo_busca_s'].sum())
    t_sonda = sum(float(e.get('tempo_pred_sonda_s') or 0) for e in son)
    fb = tim['tempo_fit_s'].values + tim['tempo_busca_s'].values
    tg = tim['tempo_geracao_s'].values
    ulp = np.abs(tg) * 1.2e-7 + 1e-9
    rows.append(dict(**mt, D=D, M=M, N=N, I_eff=I,
                     n_pred_build=n_build * M, n_pred_sonda=40000 * M,
                     t_busca_build=t_busca_build, t_sonda=t_sonda,
                     us_por_pred_build=1e6 * t_busca_build / max(n_build * M, 1),
                     us_por_pred_sonda=1e6 * t_sonda / (40000 * M),
                     t_sonda_bloco=';'.join(f"{float(e.get('tempo_pred_sonda_s') or 0):.4f}" for e in son),
                     fit_total=float(tim['tempo_fit_s'].sum()),
                     wall=man['timing']['tempo_total_s'],
                     igual_exato=int((np.abs(fb - tg) <= 1e-12).sum()),
                     viol_1e6=int((fb - tg > 1e-6).sum()),
                     viol_ulp=int((fb - tg > ulp).sum()),
                     n_linhas=len(tim)))
r = pd.DataFrame(rows); salva(r, 'b10_tempo_sonda.csv')
print('linhas de ④ totais:', int(r.n_linhas.sum()))
print('tempo_geracao_s == fit+busca (|Δ|<=1e-12):', int(r.igual_exato.sum()), '/', int(r.n_linhas.sum()))
print('violações c/ tol 1e-6:', int(r.viol_1e6.sum()), '| c/ tolerância ULP-float32:', int(r.viol_ulp.sum()))
print()
print('taxa de predição (µs/ponto-objetivo), mediana por tier:')
print(r.groupby('tier')[['us_por_pred_build', 'us_por_pred_sonda']].median().to_string())
print('speedup sonda/busca (mediana):', float((r.us_por_pred_build / r.us_por_pred_sonda).median()),
      '| min', float((r.us_por_pred_build / r.us_por_pred_sonda).min()),
      '| max', float((r.us_por_pred_build / r.us_por_pred_sonda).max()))
print()
print('--- ÂNCORA J: tier big (N=50.000) ---')
print(r[r.tier == 'big'][['label', 'D', 'M', 'I_eff', 'fit_total', 't_busca_build', 't_sonda', 'wall']].round(3).to_string())
print('fit_total big: min %.2f max %.2f mediana %.2f' % (r[r.tier=='big'].fit_total.min(),
      r[r.tier=='big'].fit_total.max(), r[r.tier=='big'].fit_total.median()))
