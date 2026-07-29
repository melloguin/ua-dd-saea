"""B06 — TESTE DISCRIMINATIVO da ÁRVORE: reconstrói o CART por objetivo a partir do
dataset (①) com os hiperparâmetros declarados (criterion=squared_error/MSE,
min_samples_leaf=10D, max_depth=100) e compara com o LOGADO (n_folhas, profundidade).
Mede também a banda de tamanho de folha [N_min, 2N_min-1] e os NÓS PUROS (empates
float32) que a violam.
⚠ sklearn do venv de análise != sklearn do run (1.1.2) — o teste é de ESTRUTURA
(nº de folhas, profundidade, banda), não bit-a-bit.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeRegressor
from lib_c311 import *

rows, folhas_rows = [], []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref, camadas=('real',))
    mt = meta(label, man)
    real = dfs['real']
    Xc = xcols(real); Fc = fcols(real); D = len(Xc); M = len(Fc); N = len(real)
    Nmin = 10 * D
    X = real[Xc].values.astype(np.float32)
    dec = [e for e in evs if e.get('rec') == 'decision']
    nf_log = np.array(dec[0]['n_folhas'], int)
    pr_log = np.array(dec[0]['profundidade'], int)
    for j in range(M):
        y = real[Fc[j]].values.astype(np.float32)
        t = DecisionTreeRegressor(criterion='squared_error', min_samples_leaf=Nmin,
                                  max_depth=100, random_state=0).fit(X, y)
        leaf = t.apply(X)
        vals, cnts = np.unique(leaf, return_counts=True)
        nl = len(vals); dep = int(t.get_depth())
        # empates float32 em y (nó puro: sklearn não divide nó com variância 0)
        uy, cy = np.unique(y, return_counts=True)
        rows.append(dict(**mt, D=D, M=M, N=N, Nmin=Nmin, obj=j,
                         n_folhas_log=int(nf_log[j]), n_folhas_rec=nl,
                         prof_log=int(pr_log[j]), prof_rec=dep,
                         teto_folhas=math.floor(N / Nmin),
                         folha_min=int(cnts.min()), folha_max=int(cnts.max()),
                         n_folhas_acima_banda=int((cnts > 2 * Nmin - 1).sum()),
                         n_folhas_abaixo=int((cnts < Nmin).sum()),
                         empate_max=int(cy.max()), n_y_unicos=int(len(uy)),
                         frac_y_unicos=float(len(uy) / N),
                         empates_ge_Nmin=int((cy >= Nmin).sum()),
                         pts_em_empates_ge_Nmin=int(cy[cy >= Nmin].sum()),
                         ok_nfolhas=bool(nl == nf_log[j]), ok_prof=bool(dep == pr_log[j])))
        for v, c in zip(vals, cnts):
            folhas_rows.append(dict(**mt, obj=j, Nmin=Nmin, leaf=int(v), n=int(c),
                                    acima=bool(c > 2 * Nmin - 1)))
    print(label, 'nfolhas log', nf_log.tolist(), 'rec', [r['n_folhas_rec'] for r in rows[-M:]])

r = pd.DataFrame(rows); salva(r, 'b06_arvore.csv')
salva(pd.DataFrame(folhas_rows), 'b06_folhas.csv')
print('\npares (célula,obj):', len(r))
print('n_folhas reconstruído == logado:', int(r.ok_nfolhas.sum()), '/', len(r))
print('profundidade reconstruída == logada:', int(r.ok_prof.sum()), '/', len(r))
print('|Δn_folhas| distribuição:', (r.n_folhas_rec - r.n_folhas_log).abs().value_counts().to_dict())
print('folhas acima da banda (2Nmin-1):', int(r.n_folhas_acima_banda.sum()),
      'em', int((r.n_folhas_acima_banda > 0).sum()), 'pares')
print('\npor dist:')
print(r.groupby('dist')[['empate_max', 'frac_y_unicos', 'n_folhas_acima_banda']].describe().T.to_string())
