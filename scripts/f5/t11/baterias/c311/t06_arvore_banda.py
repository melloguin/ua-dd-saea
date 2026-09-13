"""T06 — C1/C2 (árvore CART reconstruída: n_folhas + profundidade) e F4 (banda
[N_min, 2N_min-1] dos incrementos de `total_points_per_model`). Re-medição.
READ-ONLY. Escreve só nesta pasta."""
import sys, os
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311')
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeRegressor
import lib_c311 as L

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'
par, inc = [], []
for label, d, pref in L.celulas():
    man, evs, dfs = L.carrega(d, pref, camadas=('real',))
    mt = L.meta(label, man); real = dfs['real']
    Xc, Fc = L.xcols(real), L.fcols(real); D, M, N = len(Xc), len(Fc), len(real)
    Nmin = 10 * D
    X = real[Xc].values.astype(np.float32)
    dec = [e for e in evs if e.get('rec') == 'decision']
    nf_log = np.array(dec[-1]['n_folhas']); pf_log = np.array(dec[-1]['profundidade'])
    tp = np.array([e['total_points_per_model'] for e in dec], float)
    for j in range(M):
        y = real[Fc[j]].values.astype(np.float32)
        t = DecisionTreeRegressor(criterion='squared_error', min_samples_leaf=Nmin,
                                  max_depth=100, random_state=0).fit(X, y)
        nf = int(t.get_n_leaves()); pf = int(t.get_depth())
        folhas = t.tree_.n_node_samples[t.tree_.children_left == -1]
        par.append(dict(**mt, obj=j, D=D, N=N, Nmin=Nmin,
                        n_folhas_log=int(nf_log[j]), n_folhas_rec=nf,
                        prof_log=int(pf_log[j]), prof_rec=pf,
                        teto_folhas=N // Nmin,
                        folhas_grandes=int((folhas > 2 * Nmin - 1).sum()),
                        folhas_pequenas=int((folhas < Nmin).sum()),
                        maior_folha=int(folhas.max())))
        s = tp[:, j]
        dif = np.diff(np.concatenate([[0.0], s]))
        for i, v in enumerate(dif):
            if v > 0:
                inc.append(dict(**mt, obj=j, it=i + 1, incremento=float(v), Nmin=Nmin,
                                na_banda=bool(Nmin <= v <= 2 * Nmin - 1)))
p = pd.DataFrame(par); q = pd.DataFrame(inc)
p.to_csv(os.path.join(OUT, 't06_arvore.csv'), index=False)
q.to_csv(os.path.join(OUT, 't06_incrementos.csv'), index=False)
print('pares (célula, objetivo):', len(p))
print('C1  n_folhas reconstruído == logado : %d/%d' % ((p.n_folhas_log == p.n_folhas_rec).sum(), len(p)))
print('C2  profundidade reconstr. == logada: %d/%d  (máx observada %d; teto declarado 100)'
      % ((p.prof_log == p.prof_rec).sum(), len(p), p.prof_rec.max()))
print('    n_folhas <= floor(N/Nmin)       : %d/%d' % ((p.n_folhas_rec <= p.teto_folhas).sum(), len(p)))
print('    folhas ABAIXO de N_min          : %d pares com alguma' % (p.folhas_pequenas > 0).sum())
print('    pares com folha > 2N_min-1      : %d' % (p.folhas_grandes > 0).sum())
print('\nF4  incrementos positivos: %d | na banda [N_min, 2N_min-1]: %d (%.2f%%)'
      % (len(q), q.na_banda.sum(), 100 * q.na_banda.mean()))
print('    FORA da banda:')
print(q[~q.na_banda][['label', 'obj', 'it', 'incremento', 'Nmin']].to_string(index=False))
print('\n    folhas grandes das células citadas (tamanhos reconstruídos):')
for lab, o in [('swap_medium-mvns_ZDT4', 0), ('swap_big-mvns_DTLZ2', 2), ('swap_big-mvns_DTLZ2', 1),
               ('DTLZ4', 1)]:
    r = p[(p.label == lab) & (p.obj == o)]
    if len(r):
        print('      %-24s obj%d  maior_folha=%d  n_grandes=%d  banda=[%d,%d]'
              % (lab, o, r.maior_folha.iloc[0], r.folhas_grandes.iloc[0],
                 r.Nmin.iloc[0], 2 * r.Nmin.iloc[0] - 1))
