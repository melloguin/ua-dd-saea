"""B11 — A QUERY-JOIA do c311: reconstruir a ESCOLHA DA FOLHA (Alg. 1 l.13-16 do paper /
"argmax impurity de treino entre folhas visitadas sem GP" do código) e prever a
sequência `total_points_per_model` iteração a iteração.

Regra reconstruída, por objetivo j:
  G_j = {} ; para i = 1..I_eff:
     folhas_visitadas = unique(tree_j.apply(X_pop(g_i)))
     candidatas = folhas_visitadas \\ G_j
     se candidatas != {}: escolhida = argmax_{c in candidatas} impurity(c)  [MSE de treino]
     G_j += {escolhida} ; tppm_pred_j(i) = Σ_{l in G_j} n_node_samples(l)
Compara tppm_pred com o LOGADO no ⑥. Âncoras de população testadas: g=51i e g=51i-1.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeRegressor
from lib_c311 import *

rows, cel = [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    mt = meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    Xc = xcols(real); Fc = fcols(real); D = len(Xc); M = len(Fc); N = len(real)
    Nmin = 10 * D
    X = real[Xc].values.astype(np.float32)
    bu = busca(sur); g = bu['geracao'].astype(int)
    dec = [e for e in evs if e.get('rec') == 'decision']; I = len(dec)
    tppm_log = np.array([e['total_points_per_model'] for e in dec], float)   # I x M
    ngps_log = np.array([e['n_gps'] for e in dec], float)
    res = {}
    for off, tag in ((0, 'g51i'), (-1, 'g51i_1')):
        pops = {}
        for i in range(1, I + 1):
            sub = bu[g == 51 * i + off]
            pops[i] = sub[Xc].values.astype(np.float32) if len(sub) else None
        pred_tp = np.zeros((I, M)); pred_ng = np.zeros((I, M))
        for j in range(M):
            y = real[Fc[j]].values.astype(np.float32)
            t = DecisionTreeRegressor(criterion='squared_error', min_samples_leaf=Nmin,
                                      max_depth=100, random_state=0).fit(X, y)
            imp = t.tree_.impurity; nsm = t.tree_.n_node_samples
            G = []
            for i in range(1, I + 1):
                P = pops[i]
                if P is not None and len(P):
                    fol = np.unique(t.apply(P))
                    cand = [int(c) for c in fol if int(c) not in G]
                    if cand:
                        G.append(int(max(cand, key=lambda c: imp[c])))
                pred_tp[i - 1, j] = sum(nsm[l] for l in G)
                pred_ng[i - 1, j] = len(G)
        res[tag] = (pred_tp, pred_ng)
    linha = dict(**mt, D=D, M=M, N=N, Nmin=Nmin, I_eff=I, n_pares=I * M)
    for tag, (ptp, png) in res.items():
        linha[f'hit_tppm_{tag}'] = int((np.abs(ptp - tppm_log) < 0.5).sum())
        linha[f'hit_ngps_{tag}'] = int((np.abs(png - ngps_log) < 0.5).sum())
        linha[f'hit_tppm_it1_{tag}'] = int((np.abs(ptp[0] - tppm_log[0]) < 0.5).sum())
        linha[f'hit_tppm_final_{tag}'] = int((np.abs(ptp[-1] - tppm_log[-1]) < 0.5).sum())
        linha[f'erro_rel_{tag}'] = float(np.median(np.abs(ptp - tppm_log) / np.maximum(tppm_log, 1)))
    cel.append(linha)
    ptp = res['g51i_1'][0]; png = res['g51i_1'][1]
    pA = res['g51i'][0]
    for i in range(I):
        for j in range(M):
            rows.append(dict(**mt, it=i + 1, obj=j, tppm_log=float(tppm_log[i, j]),
                             tppm_pred=float(ptp[i, j]), ngps_log=float(ngps_log[i, j]),
                             ngps_pred=float(png[i, j]),
                             tppm_pred_g51i=float(pA[i, j]),
                             casa=bool(abs(ptp[i, j] - tppm_log[i, j]) < 0.5)))
    print(label, 'tppm hit', linha['hit_tppm_g51i'], '/', I * M,
          '| g51i-1', linha['hit_tppm_g51i_1'], '| ngps', linha['hit_ngps_g51i'])

r = pd.DataFrame(rows); c = pd.DataFrame(cel)
salva(r, 'b11_folha_iter.csv'); salva(c, 'b11_folha_cel.csv')
tot = int(c.n_pares.sum())
print('\npares (iteração, objetivo):', tot)
for tag in ['g51i', 'g51i_1']:
    print(f'tppm reconstruído == logado [{tag}]:', int(c['hit_tppm_' + tag].sum()),
          f'({100*c["hit_tppm_"+tag].sum()/tot:.1f}%)  | n_gps:', int(c['hit_ngps_' + tag].sum()),
          f'({100*c["hit_ngps_"+tag].sum()/tot:.1f}%)')
print('células com 100% de acerto (tppm, g51i):', int((c.hit_tppm_g51i == c.n_pares).sum()), '/ 54')
print('1ª iteração (a escolha inicial) acerta:', int(c.hit_tppm_it1_g51i.sum()), '/', int(c.M.sum()))
print('última iteração (cobertura final) acerta:', int(c.hit_tppm_final_g51i.sum()), '/', int(c.M.sum()))
print(c.groupby('tier').apply(lambda x: pd.Series({
    'pares': x.n_pares.sum(), 'hit': x.hit_tppm_g51i.sum(),
    'pct': 100 * x.hit_tppm_g51i.sum() / x.n_pares.sum()})).to_string())
