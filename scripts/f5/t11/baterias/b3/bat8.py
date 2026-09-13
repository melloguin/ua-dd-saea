import json, hashlib
import numpy as np, pandas as pd
C='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b3/exp_main_b3_MMF1_42'
S='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/b3/exp_main_b3_MMF1_42'
print('=== U5 NAO-PERTURBACAO DA SONDA (par G-6 com x sem) ===')
mc=json.load(open(C+'.manifest.json')); ms=json.load(open(S+'.manifest.json'))
print('COM sonda:', {k:mc['sonda'].get(k) for k in ['desligada','n_blocos','n_linhas','geracoes','S']})
print('SEM sonda:', {k:ms['sonda'].get(k) for k in ['desligada','n_blocos','n_linhas','geracoes','S']})
print('fe_final/maxfe/n_ger/cache_hits COM', mc['fe_final'],mc['maxfe'],mc['n_geracoes'],mc['cache_hits'])
print('fe_final/maxfe/n_ger/cache_hits SEM', ms['fe_final'],ms['maxfe'],ms['n_geracoes'],ms['cache_hits'])
rc=pd.read_parquet(C+'__real.parquet'); rs=pd.read_parquet(S+'__real.parquet')
print('(1) shape', rc.shape, rs.shape)
hc=hashlib.sha256(pd.util.hash_pandas_object(rc,index=False).values.tobytes()).hexdigest()
hs=hashlib.sha256(pd.util.hash_pandas_object(rs,index=False).values.tobytes()).hexdigest()
print('(1) hash COM',hc[:16],' SEM',hs[:16],' IDENTICA:',hc==hs)
print('(1) bit-a-bit em X e f:', (rc[['x0','x1','f0','f1']].values==rs[['x0','x1','f0','f1']].values).all())
sc=pd.read_parquet(C+'__surrogate.parquet'); ss=pd.read_parquet(S+'__surrogate.parquet')
print('(3) linhas COM',len(sc),'SEM',len(ss),' regimes COM',sc.regime.value_counts().to_dict(),' SEM',ss.regime.value_counts().to_dict())
oc=sc[sc.regime=='online'].reset_index(drop=True); os_=ss[ss.regime=='online'].reset_index(drop=True)
print('(3) online COM',len(oc),'SEM',len(os_))
cols=['x0','x1','mu_0','mu_1','sigma_0','sigma_1']
if len(oc)==len(os_):
    A=oc[cols].values.astype(np.float64); Bv=os_[cols].values.astype(np.float64)
    print('(3) online bit-a-bit em',cols,':',(A==Bv).all(),' max|d|',np.abs(A-Bv).max())
# jsonl decisoes
def gg(p): return [json.loads(l) for l in open(p+'.jsonl') if json.loads(l).get('rec')=='b3_gen']
gc=gg(C); gs=gg(S)
print('n b3_gen COM',len(gc),'SEM',len(gs))
for f in ['fe','NumV1','NumV2','Flag','ramo','index','pop_por_w','n_treino','fe_treino_max','apd_sel','dist_min_arquivo','adapt_delta_V']:
    d=sum(1 for a,b in zip(gc,gs) if a.get(f)!=b.get(f))
    print('  %-18s identicos %d/%d'%(f,len(gc)-d,len(gc)))
d=sum(1 for a,b in zip(gc,gs) if a['sigma_sel']!=b['sigma_sel'])
print('  sigma_sel          identicos %d/%d'%(len(gc)-d,len(gc)))
print('  3 sinais G-6: (i) desligada SEM =',ms['sonda'].get('desligada'),' (ii) n_blocos', mc['sonda']['n_blocos'],'->',ms['sonda']['n_blocos'],' (iii) (3) encolheu',len(sc),'->',len(ss))
print('  tempo_aval_real_s COM',mc['timing'].get('tempo_aval_real_s'),' SEM',ms['timing'].get('tempo_aval_real_s'))
