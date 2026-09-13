#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 9:
 (a) turnover posicional da população por geração, piso × b5m × b5r (prior: piso ~8,5%/ger
     vs b5m ~98%/ger);
 (b) IGD+/HV da ⑦ nas 20 células de SWEEP (o transversal da F5.5 só cobre as 25 off).
"""
import os, glob, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
REPO='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT=REPO+'/f5/baterias/moead_media'
sys.path.insert(0,REPO); os.chdir(REPO)
LABELS=sorted(os.listdir(RES+'/moead_media'))

tv=[]
for label in LABELS:
    for alg in ['moead_media','b5m','b5r']:
        g=glob.glob('%s/%s/%s/42/*__surrogate.parquet'%(RES,alg,label))
        if not g: continue
        nm=pq.ParquetFile(g[0]).schema.names
        XC=sorted([c for c in nm if c[0]=='x' and c[1:].isdigit()],key=lambda c:int(c[1:]))
        t=pq.read_table(g[0],columns=['regime','geracao']+XC).to_pandas()
        o=t[t['regime']=='offline']; gg=o['geracao'].dropna().astype(int)
        if not len(gg): continue
        per=gg.value_counts(); Np=int(per.mode().iloc[0])
        if per.nunique()!=1 or len(o)!=Np*per.size:
            tv.append({'label':label,'alg':alg,'pop_variavel':True,'N_pop':Np,'n_ger':int(per.size)}); continue
        A=o.sort_values('geracao',kind='stable')[XC].values.astype(np.float32).reshape(per.size,Np,len(XC))
        ch=(A[1:]!=A[:-1]).any(axis=2).mean(axis=1); q=max(1,len(ch)//4)
        tv.append({'label':label,'alg':alg,'pop_variavel':False,'N_pop':Np,'n_ger':int(per.size),
            'turn_mean':float(ch.mean()),'turn_med':float(np.median(ch)),'turn_g2':float(ch[0]),
            'turn_q1':float(ch[:q].mean()),'turn_q4':float(ch[-q:].mean()),
            'congeladas':int((ch==0).sum()),'n_trans':len(ch)})
    print('turn %s'%label,flush=True)
T=pd.DataFrame(tv); T.to_csv(OUT+'/turnover_por_config.csv',index=False)
print(T.groupby('alg').agg(n=('turn_mean','size'),media=('turn_mean','mean'),mediana=('turn_med','median'),
    g2=('turn_g2','mean'),q1=('turn_q1','mean'),q4=('turn_q4','mean'),
    congeladas=('congeladas','sum'),trans=('n_trans','sum')).round(4).to_string(),flush=True)

from src import metrics as MX
r7=[]
for label in [l for l in LABELS if l.startswith('swap_')]:
    for alg in ['moead_media','b5m','b5r','e103']:
        g=glob.glob('%s/%s/%s/42/*__final.parquet'%(RES,alg,label))
        if not g: continue
        d7=pd.read_parquet(g[0]); prob=d7['problema'].iloc[0]
        FC=sorted([c for c in d7.columns if c[0]=='f' and c[1:].isdigit()],key=lambda c:int(c[1:]))
        F=d7[FC].values.astype(float); nd=d7['nd_pos_real'].values.astype(bool)
        try: mm=MX.metrics_of_set(F[nd] if nd.any() else F, prob)
        except Exception: mm={'igd_plus':np.nan,'hv':np.nan}
        r7.append({'label':label,'alg':alg,'problema':prob,'n_final':len(d7),'n_nd':int(nd.sum()),
                   'fantasia':float(nd.mean()),'igd7':mm['igd_plus'],'hv7':mm['hv']})
    print('⑦sweep %s'%label,flush=True)
D=pd.DataFrame(r7); D.to_csv(OUT+'/camada7_sweep.csv',index=False)
p=D.pivot_table(index='label',columns='alg',values='igd7')
print(p.round(5).to_string())
print('piso < b5m em %d/%d'%((p.moead_media<p.b5m).sum(),len(p)))
