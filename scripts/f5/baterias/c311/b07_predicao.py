"""B07 — TESTE DISCRIMINATIVO da REGRA DE PREDIÇÃO (§3.1 do paper):
"se o ponto cai em folha COM GP -> média posterior do GP; senão -> média da folha".
Reconstrói o CART e prediz a MÉDIA DA FOLHA nos 20.000 pontos da sonda; compara com o
μ logado, separando por σ-NaN (folha SEM GP) x σ válido (folha COM GP).
Assinatura se fiel: μ == média-da-folha nos pontos σ-NaN; μ != média-da-folha (GP) nos demais.
Mede também o nº de valores DISTINTOS de μ na região sem GP (= constante por partes).
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeRegressor
from lib_c311 import *

rows = []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    mt = meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    Xc = xcols(real); Fc = fcols(real); D = len(Xc); M = len(Fc); N = len(real)
    Nmin = 10 * D
    X = real[Xc].values.astype(np.float32)
    so = sonda(sur).iloc[:20000]
    Xs = so[Xc].values.astype(np.float32)
    mus = mucols(so); sgs = sigcols(so)
    dec = [e for e in evs if e.get('rec') == 'decision']
    nf = np.array(dec[-1]['n_folhas'], int); ng = np.array(dec[-1]['n_gps'], int)
    for j in range(M):
        y = real[Fc[j]].values.astype(np.float32)
        t = DecisionTreeRegressor(criterion='squared_error', min_samples_leaf=Nmin,
                                  max_depth=100, random_state=0).fit(X, y)
        pred = t.predict(Xs).astype(np.float64)
        mu = so[mus[j]].values.astype(np.float64)
        sg = so[sgs[j]].values.astype(np.float64)
        nanm = np.isnan(sg)
        esc = max(np.abs(y).max(), 1e-12)
        dif_nan = np.abs(mu[nanm] - pred[nanm]) if nanm.any() else np.array([])
        dif_gp = np.abs(mu[~nanm] - pred[~nanm]) if (~nanm).any() else np.array([])
        tolabs = 1.2e-7 * esc * 4
        rows.append(dict(**mt, D=D, M=M, N=N, Nmin=Nmin, obj=j,
                         n_folhas=int(nf[j]), n_gps=int(ng[j]),
                         folhas_sem_gp=int(nf[j] - ng[j]),
                         n_nan=int(nanm.sum()), nan_share=float(nanm.mean()),
                         mu_dist_nan=int(len(np.unique(mu[nanm]))) if nanm.any() else 0,
                         mu_dist_gp=int(len(np.unique(mu[~nanm]))) if (~nanm).any() else 0,
                         pred_dist=int(len(np.unique(pred))),
                         casa_nan=float((dif_nan <= tolabs).mean()) if len(dif_nan) else np.nan,
                         dmax_nan=float(dif_nan.max()) if len(dif_nan) else np.nan,
                         dmed_nan=float(np.median(dif_nan)) if len(dif_nan) else np.nan,
                         casa_gp=float((dif_gp <= tolabs).mean()) if len(dif_gp) else np.nan,
                         dmed_gp=float(np.median(dif_gp)) if len(dif_gp) else np.nan,
                         escala=float(esc), tolabs=float(tolabs),
                         mu_dist_le_folhas_sem_gp=bool((len(np.unique(mu[nanm])) if nanm.any() else 0)
                                                       <= nf[j] - ng[j])))
    print(label, 'ok')

r = pd.DataFrame(rows); salva(r, 'b07_predicao.csv')
print('\npares (célula,obj):', len(r))
sub = r[r.n_nan > 0]
print('pares com região SEM GP na sonda:', len(sub))
print('μ == média-da-folha nos pontos σ-NaN (fração média):', float(sub.casa_nan.mean()))
print('pares com casa_nan == 1.0:', int((sub.casa_nan >= 1.0).sum()), '/', len(sub))
print('pares com casa_nan >= 0.999:', int((sub.casa_nan >= 0.999).sum()), '/', len(sub))
print('μ distinto <= folhas sem GP:', int(sub.mu_dist_le_folhas_sem_gp.sum()), '/', len(sub))
sub2 = r[(r.n_nan < 20000)]
print('μ == média-da-folha nos pontos COM GP (fração média, esperado ~0):', float(sub2.casa_gp.mean()))
print(r.groupby('tier')[['nan_share', 'casa_nan', 'casa_gp', 'mu_dist_nan', 'folhas_sem_gp']].median().to_string())
