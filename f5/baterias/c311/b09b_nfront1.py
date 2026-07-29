"""B09b — diagnóstico dos 38 desencontros de n_front1: regra "vetores DISTINTOS"
x população selecionada (③, DEF-C2) x pool pré-seleção."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *
r = pd.read_csv(os.path.join(OUT, 'b09_telemetria_iter.csv'))
b = r[~r.ok_nfront1].copy()
out = []
for lab, gg in b.groupby('label'):
    d = f'/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c311/{lab}/42'
    pref = [x[:-len('.manifest.json')] for x in os.listdir(d)
            if x.endswith('.manifest.json') and '__final' not in x][0]
    man, evs, dfs = carrega(d, pref, camadas=('real', 'surrogate'))
    bu = busca(dfs['surrogate']); mus = mucols(bu); g = bu['geracao'].astype(int)
    dec = [e for e in evs if e.get('rec') == 'decision']
    for _, row in gg.iterrows():
        it = int(row.it); e = dec[it - 1]
        sub = bu[g == 51 * it]; MU = sub[mus].values.astype(np.float64)
        uni = np.unique(MU, axis=0)
        out.append(dict(label=lab, tier=row.tier, it=it, pop=len(MU), unicos=len(uni),
                        log=e['n_front1'], nd_todos=int(nd_mask(MU).sum()),
                        nd_unicos=int(nd_mask(uni).sum()),
                        casa_unicos=bool(int(nd_mask(uni).sum()) == e['n_front1']),
                        degenerado=bool(len(uni) == 1)))
o = pd.DataFrame(out); salva(o, 'b09b_nfront1_misses.csv')
print('misses', len(o))
print('casam pela regra "vetores DISTINTOS":', int(o.casa_unicos.sum()))
print('degenerados (μ constante na população):', int(o.degenerado.sum()))
print('restantes (log > ND recomputado, 1-4):', int((~o.casa_unicos & ~o.degenerado).sum()))
print(o.groupby('label')[['casa_unicos', 'degenerado']].sum().to_string())
