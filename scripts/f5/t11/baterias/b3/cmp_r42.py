import json, hashlib, sys
import pandas as pd, numpy as np
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
R42='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42/exp_main_b3_MMF1_42'
def recs(p):
    return [json.loads(l) for l in open(p+'.jsonl')]
a=recs(SM); b=recs(R42)
import collections
print('smoke recs', collections.Counter(r['rec'] for r in a))
print('r42   recs', collections.Counter(r['rec'] for r in b))
ga=[r for r in a if r['rec']=='b3_gen']; gb=[r for r in b if r['rec']=='b3_gen']
print('n b3_gen', len(ga), len(gb))
# campos
ka=set(); kb=set()
for r in ga: ka|=set(r.keys())
for r in gb: kb|=set(r.keys())
print('SO no smoke:', sorted(ka-kb))
print('SO na r42  :', sorted(kb-ka))
# comparar campos comuns numericos por geracao
for f in ['fe','n_treino','arquivo','u_efetivo','NumV1','NumV2','Flag','ramo','lote','index','pop_por_w','nzero_updata','n_vetores_vazios','fe_treino_max','apd_sel','n_front1','f_best','dist_min_arquivo']:
    difs=[]
    for x,y in zip(ga,gb):
        va=x.get(f); vb=y.get(f)
        if isinstance(va,list):
            same = (len(va)==len(vb)) and all(np.isclose(p,q,rtol=1e-12,atol=0) if isinstance(p,float) else p==q for p,q in zip(va,vb))
        else:
            same = (va==vb) or (isinstance(va,float) and isinstance(vb,float) and np.isclose(va,vb,rtol=1e-12))
        if not same: difs.append((x['geracao'],va,vb))
    print('%-18s idênticos %d/%d' % (f, len(ga)-len(difs), len(ga)), ('' if not difs else ('ex: '+str(difs[:2])[:220])))
# sigma_sel
d=0
for x,y in zip(ga,gb):
    if x['sigma_sel']['criterio_meanMSE']!=y['sigma_sel']['criterio_meanMSE']: d+=1
print('sigma_sel.criterio_meanMSE idênticos %d/%d'%(len(ga)-d,len(ga)))
# footer
fa=[r for r in a if r['rec']=='footer'][0]; fb=[r for r in b if r['rec']=='footer'][0]
print('footer smoke', fa); print('footer r42  ', fb)
# parquets
for lay in ['real','pop','surrogate','timing']:
    da=pd.read_parquet(SM+'__%s.parquet'%lay); db=pd.read_parquet(R42+'__%s.parquet'%lay)
    print(lay, 'shape', da.shape, db.shape, 'cols iguais', list(da.columns)==list(db.columns))
    print('   so_smoke', sorted(set(da.columns)-set(db.columns)), 'so_r42', sorted(set(db.columns)-set(da.columns)))
