"""Saude: regua Sobol (s42, 1.024 blocos) + metricas + trajetorias + smoke."""
import pandas as pd, numpy as np, json, glob, os
F='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/'
s=pd.read_csv(F+'sonda_f52e.csv'); c=s[(s.alg=='c141')&(s.exp=='main')].copy()
c['bloco']=pd.to_numeric(c.bloco,errors='coerce')
print('=== REGUA SOBOL (regime=sonda; regra 12: nenhum bloco estratificado existe em c141) ===')
print('blocos-objetivo:',len(c),' cobertura95 nao-nula:',int(c.cobertura95.notna().sum()),'(N/A por desenho — sigma nao e desvio preditivo)')
r=[]
for pb,g in c.groupby('problema'):
    nb=g.bloco.max()
    pri=g[g.bloco==g.bloco.min()]; ult=g[g.bloco==nb]
    r.append(dict(pb=pb,blocos=int(nb),wape_1=pri.wape.mean(),wape_n=ult.wape.mean(),
        d_wape=100*(ult.wape.mean()-pri.wape.mean())/max(pri.wape.mean(),1e-12),
        corr_1=pri['corr'].mean(),corr_n=ult['corr'].mean(),corr_med=g['corr'].median()))
R=pd.DataFrame(r).sort_values('d_wape')
print(R.to_string())
print(' ΔWAPE mediano 1o->ultimo bloco: %+.1f%%'%R.d_wape.median())
m=pd.read_csv(F+'metricas_finais_f52c.csv')
mc=m[(m.alg=='c141')&(m.exp=='main')]
print()
print('=== METRICAS (25 celulas) ===')
pis=m[(m.alg.isin(['nsga2','nsga3','smsemoa','moead']))&(m.exp=='main')]
alg_all=m[(m.exp=='main')]
tab=[]
for _,row in mc.iterrows():
    pb=row.problema; p=pis[pis.problema==pb]
    best=p.igd_plus.min(); who=p.loc[p.igd_plus.idxmin(),'alg'] if len(p) else None
    comp=alg_all[(alg_all.problema==pb)&alg_all.igd_plus.notna()]
    rank=int((comp.igd_plus<row.igd_plus).sum())+1
    tab.append(dict(pb=pb,igd_plus=row.igd_plus,hv=row.hv,n_nd=row.n_nd,piso=best,alg_piso=who,
                    razao=row.igd_plus/best if best else np.nan,rank=rank,de=len(comp)))
T=pd.DataFrame(tab); print(T.to_string())
print(' bate o melhor piso em %d/25 ; 1o lugar absoluto em %d ; rank medio %.2f'%(
    int((T.razao<1).sum()),int((T['rank']==1).sum()),T['rank'].mean()))
print()
print('=== TRAJETORIAS: monotonicidade ===')
vi=vh=tr=0
for p in glob.glob(F+'trajetorias/main_c141_*_42.json'):
    j=json.load(open(p))
    ks=list(j.keys()) if isinstance(j,dict) else None
    arr=j['checkpoints'] if isinstance(j,dict) and 'checkpoints' in j else j
    ig=[x.get('igd_plus') for x in arr] if isinstance(arr,list) else None
    hv=[x.get('hv') for x in arr] if isinstance(arr,list) else None
    if ig:
        ig=[x for x in ig if x is not None]; hv=[x for x in hv if x is not None]
        vi+=sum(1 for a,b in zip(ig,ig[1:]) if b>a+1e-12); vh+=sum(1 for a,b in zip(hv,hv[1:]) if b<a-1e-12)
        tr+=len(ig)-1
print(' violacoes IGD+ %d ; violacoes HV %d ; em %d transicoes (25 celulas)'%(vi,vh,tr))
