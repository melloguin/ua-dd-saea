"""Saude em escala do b3: metricas vs pisos, rank, trajetorias 20-checkpoints,
sonda oficial (f52e), tempo de treino (Fig.9), separacao do switch."""
import pandas as pd, numpy as np, json, glob, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT=F5+'/baterias/b3'
met=pd.read_csv(F5+'/metricas_finais_f52c.csv'); mm=met[met.exp=='main'].copy()
pisos=['moead','nsga2','nsga3','smsemoa']
rows=[]
for pr in sorted(mm[mm.alg=='b3'].problema.unique()):
    sub=mm[mm.problema==pr]
    b=sub[sub.alg=='b3'].iloc[0]
    pi=sub[sub.alg.isin(pisos)]
    best=pi.loc[pi.igd_plus.idxmin()]
    rk=sub.sort_values('igd_plus').reset_index(drop=True)
    rank=int(rk.index[rk.alg=='b3'][0])+1
    hvpi=pi.loc[pi.hv.idxmax()]
    rows.append(dict(problema=pr,igd_b3=b.igd_plus,hv_b3=b.hv,igd_b1=float(sub[sub.alg=='b1'].igd_plus.iloc[0]) if (sub.alg=='b1').any() else np.nan,
        igd_melhor_piso=best.igd_plus,piso=best.alg,razao=b.igd_plus/best.igd_plus,
        hv_melhor_piso=hvpi.hv,hv_piso_alg=hvpi.alg,bate=bool(b.igd_plus<best.igd_plus),
        rank_igd=rank,n_algs=len(sub),n_nd=b.n_nd,igd_raw=b.igd,gd=b.gd,spacing=b.spacing))
M=pd.DataFrame(rows)
M.to_csv(OUT+'/b3_metricas_vs_pisos.csv',index=False)
pd.set_option('display.width',400); pd.set_option('display.max_columns',40)
print(M.to_string()); print('\nbate piso:',M.bate.sum(),'/',len(M),'| rank medio IGD+:',round(M.rank_igd.mean(),2),'de',M.n_algs.iloc[0])
print('vence b1 (ParEGO) em IGD+:', int((M.igd_b3<M.igd_b1).sum()),'/',int(M.igd_b1.notna().sum()))
# trajetorias
tr=[]
for pr in M.problema:
    f=f'{F5}/trajetorias/main_b3_{pr}_42.json'
    if not os.path.exists(f):
        g=glob.glob(f'{F5}/trajetorias/*b3_{pr}_42.json'); f=g[0] if g else None
    if f is None: tr.append(dict(problema=pr,erro='sem trajetoria')); continue
    j=json.load(open(f))
    ks=[k for k in j if isinstance(j[k],list)]
    ser=j.get('igd_plus') or j.get('igdplus') or j.get('igd+')
    if ser is None: tr.append(dict(problema=pr,chaves=str(list(j.keys()))[:120])); continue
    a=np.array(ser,dtype=float); v=int((np.diff(a)>1e-12).sum())
    tr.append(dict(problema=pr,n_cp=len(a),viol=v,primeiro=a[0],ultimo=a[-1],pior_salto=float(np.diff(a).max())))
T=pd.DataFrame(tr); T.to_csv(OUT+'/b3_trajetorias.csv',index=False); print('\n=== TRAJETORIAS ==='); print(T.to_string())
# sonda oficial
sd=pd.read_csv(F5+'/sonda_f52e.csv'); s3=sd[(sd.exp=='main')&(sd.alg=='b3')]
g=s3.groupby(['problema','bloco']).agg(wape=('wape','mean'),corr=('corr','mean'),cob=('cobertura95','mean'),ftm=('fe_treino_max','max')).reset_index()
res=[]
for pr,gg in g.groupby('problema'):
    gg=gg.sort_values('bloco')
    res.append(dict(problema=pr,nb=len(gg),wape_p=gg.wape.iloc[0],wape_u=gg.wape.iloc[-1],
        dWAPE=round(100*(gg.wape.iloc[-1]/gg.wape.iloc[0]-1),1),corr_p=gg['corr'].iloc[0],corr_u=gg['corr'].iloc[-1],
        cob_p=gg.cob.iloc[0],cob_u=gg.cob.iloc[-1],ftm_p=gg.ftm.iloc[0],ftm_u=gg.ftm.iloc[-1],
        wape_med=gg.wape.median(),wape_std=gg.wape.std()/max(gg.wape.mean(),1e-12)))
S=pd.DataFrame(res); S.to_csv(OUT+'/b3_sonda_resumo.csv',index=False)
print('\n=== SONDA (f52e, media por objetivo) ==='); print(S.round(4).to_string())
print('mediana dWAPE:',round(S.dWAPE.median(),1),'% | n cel WAPE piora:',int((S.dWAPE>0).sum()))
