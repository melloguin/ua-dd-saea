"""T01 — A FÓRMULA DO EARLY-STOP, LIDA NO CÓDIGO E RECONSTRUÍDA DO DADO.

O que a F5 (v1.1) deixou no TETO T: a fórmula interna de `delta_total_point`.
9 famílias de candidatos x 3 âncoras x 4 lags deram no máximo 5,4% de acerto.

O que a leitura de código da T11 revelou (READ-ONLY):
  algorithms/c311_TGPR-MO/desdeo_problem/surrogatemodels/surrogate_treedGP.py:45-49
      def addGPs(self, X_solutions):
          Y_solution_leaf = self.regr.apply(X_solutions)
          unique_solutions, _ = np.unique(Y_solution_leaf, return_counts=True)
          unique_solutions = np.setdiff1d(unique_solutions, self.error_leaves)
          self.total_point_gps = unique_solutions.size      # <<< CONTA FOLHAS, NÃO PONTOS
  src/c311_tgprmo.py:620-637
          total_points_all += models[i].total_point_gps     # ACUMULADOR (soma j E soma t)
          total_points_all_sequence = append(seq, total_points_all)
          if evolver._iteration_counter > 5:
              delta = total_points_all - total_points_all_sequence[_iteration_counter - 3]
  desdeo_emo/EAs/BaseEA.py:66  `_iteration_counter += 1` no FIM de iterate()

  ⇒ com C(k) = Σ_{t<=k} c(t) e c(t) = Σ_j |folhas visitadas sem GP na iteração t|:
       delta(k) = C(k) - C(k-2) = c(k) + c(k-1)        (janela de 2, k>5)
       delta(k) = 1 (sentinela)                         (k<=5)

Esta bateria PREVÊ delta(k) a partir da árvore CART reconstruída + a população da
geração 51k-1 da ③ e compara com o `delta_total_point` LOGADO no ⑥.
READ-ONLY sobre resultados_experimentos/. Escreve só nesta pasta.
"""
import sys, os, json
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311')
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeRegressor
import lib_c311 as L

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'

rows, cel = [], []
for label, d, pref in L.celulas():
    man, evs, dfs = L.carrega(d, pref, camadas=('real', 'surrogate'))
    mt = L.meta(label, man)
    real, sur = dfs['real'], dfs['surrogate']
    Xc = L.xcols(real); Fc = L.fcols(real)
    D, M, N = len(Xc), len(Fc), len(real)
    Nmin = 10 * D
    X = real[Xc].values.astype(np.float32)
    bu = L.busca(sur); g = bu['geracao'].astype(int)
    dec = [e for e in evs if e.get('rec') == 'decision']
    I = len(dec)
    delta_log = np.array([e['delta_total_point'] for e in dec], float)
    es_log = np.array([bool(e['early_stop']) for e in dec])
    tppm_log = np.array([e['total_points_per_model'] for e in dec], float)

    # populações das gerações 51k-1 (a âncora provada em C4 e agora confirmada no fonte:
    # _current_gen_count = 51(k-1)+50 = 51k-1 no instante do addGPs)
    pops = {}
    for k in range(1, I + 1):
        sub = bu[g == 51 * k - 1]
        pops[k] = sub[Xc].values.astype(np.float32) if len(sub) else None

    # c(k) = Σ_j |folhas visitadas pela pop(51k-1) que ainda NÃO têm GP|
    c = np.zeros(I); tppm_pred = np.zeros((I, M))
    for j in range(M):
        y = real[Fc[j]].values.astype(np.float32)
        t = DecisionTreeRegressor(criterion='squared_error', min_samples_leaf=Nmin,
                                  max_depth=100, random_state=0).fit(X, y)
        imp = t.tree_.impurity; nsm = t.tree_.n_node_samples
        G = []
        for k in range(1, I + 1):
            P = pops[k]
            if P is not None and len(P):
                fol = np.unique(t.apply(P))
                cand = [int(x) for x in fol if int(x) not in G]
                c[k - 1] += len(cand)                       # <<< a grandeza do vendor
                if cand:
                    G.append(int(max(cand, key=lambda q: imp[q])))
            tppm_pred[k - 1, j] = sum(nsm[l] for l in G)

    C = np.cumsum(c)
    delta_pred = np.ones(I)                                  # sentinela para k<=5
    for k in range(6, I + 1):
        delta_pred[k - 1] = C[k - 1] - C[k - 3]              # = c(k)+c(k-1)

    elig = np.arange(1, I + 1) > 5                           # iterações onde delta é real
    hit = np.abs(delta_pred - delta_log) < 0.5
    linha = dict(**mt, D=D, M=M, N=N, I_eff=I,
                 n_elig=int(elig.sum()),
                 hit_elig=int((hit & elig).sum()),
                 hit_sentinela=int((hit & ~elig).sum()),
                 n_sentinela=int((~elig).sum()),
                 early_stop_disparou=bool(es_log.any()),
                 delta_zero_log=int((delta_log == 0).sum()),
                 delta_zero_pred=int((delta_pred == 0).sum()),
                 tppm_hit=int((np.abs(tppm_pred - tppm_log) < 0.5).sum()),
                 tppm_pares=I * M)
    cel.append(linha)
    for k in range(I):
        rows.append(dict(**mt, it=k + 1, elegivel=bool(elig[k]),
                         delta_log=float(delta_log[k]), delta_pred=float(delta_pred[k]),
                         c_k=float(c[k]), C_k=float(C[k]),
                         early_stop=bool(es_log[k]), casa=bool(hit[k])))
    print('%-28s I=%-4d elig=%-4d hit=%-4d  (sent %d/%d)  tppm %d/%d' %
          (label, I, linha['n_elig'], linha['hit_elig'],
           linha['hit_sentinela'], linha['n_sentinela'],
           linha['tppm_hit'], linha['tppm_pares']))

r = pd.DataFrame(rows); ce = pd.DataFrame(cel)
r.to_csv(os.path.join(OUT, 't01_delta_iter.csv'), index=False)
ce.to_csv(os.path.join(OUT, 't01_delta_cel.csv'), index=False)
ne, he = int(ce.n_elig.sum()), int(ce.hit_elig.sum())
ns, hs = int(ce.n_sentinela.sum()), int(ce.hit_sentinela.sum())
print('\n== FÓRMULA delta(k) = c(k) + c(k-1) ==')
print('iterações ELEGÍVEIS (k>5): %d | acerto EXATO: %d (%.1f%%)' % (ne, he, 100 * he / ne))
print('iterações k<=5 (sentinela=1): %d | acerto: %d (%.1f%%)' % (ns, hs, 100 * hs / ns))
print('TOTAL 604 decisões: acerto %d (%.1f%%)' % (he + hs, 100 * (he + hs) / (ne + ns)))
print('células 100%% nas elegíveis:', int((ce.hit_elig == ce.n_elig).sum()), '/', len(ce))
print('tppm (controle C6):', int(ce.tppm_hit.sum()), '/', int(ce.tppm_pares.sum()))
