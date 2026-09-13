import json,os,glob
import pandas as pd, numpy as np
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
# ---------- SONDA ----------
sn=pd.read_csv(f"{F5}/sonda_f52e.csv"); e=sn[(sn.alg=='e7')&(sn.exp=='main')].copy()
rows=[]
for (p),g in e.groupby('problema'):
    b0=g.bloco.min(); b1=g.bloco.max()
    w0=g[g.bloco==b0].wape.mean(); w1=g[g.bloco==b1].wape.mean()
    rows.append(dict(problema=p,n_blocos=g.bloco.nunique(),M=g.obj.nunique(),
        wape_1=w0,wape_last=w1,dwape=(w1-w0)/w0 if w0 else np.nan,
        cob_1=g[g.bloco==b0].cobertura95.mean(),cob_last=g[g.bloco==b1].cobertura95.mean(),
        corr_last=g[g.bloco==b1]['corr'].mean(),
        n_nan=g.n_nan.sum(),n_validas_min=g.n_validas.min()))
ds=pd.DataFrame(rows).sort_values('dwape')
ds.to_csv("sonda_e7.csv",index=False)
pd.set_option('display.width',260)
print("=== SONDA (por celula) ==="); print(ds.round(4).to_string())
print("\nDELTA WAPE mediano:",round(ds.dwape.median(),4)," | melhoram:",int((ds.dwape<0).sum()),"/25")
print("cobertura95 mediana (ultimo bloco):",round(ds.cob_last.median(),4)," (1o bloco:",round(ds.cob_1.median(),4),")")
print("cobertura95 global (todas 2705 medicoes):",round(e.cobertura95.median(),4),"| corr mediana final:",round(ds.corr_last.median(),4))
print("n_nan total:",e.n_nan.sum(),"| n_validas min:",e.n_validas.min(),"| medicoes:",len(e))
# ---------- METRICAS + PISOS ----------
mt=pd.read_csv(f"{F5}/metricas_finais_f52c.csv"); mt=mt[mt.exp=='main']
PISOS=['moead','nsga2','nsga3','smsemoa']
rr=[]
for p in sorted(mt[mt.alg=='e7'].problema.unique()):
    me=mt[(mt.alg=='e7')&(mt.problema==p)].iloc[0]
    pis=mt[(mt.alg.isin(PISOS))&(mt.problema==p)]
    best=pis.igd_plus.min(); who=pis.loc[pis.igd_plus.idxmin(),'alg'] if len(pis) else None
    sub=mt[mt.problema==p]
    rk=int((sub.igd_plus<me.igd_plus).sum())+1
    rr.append(dict(problema=p,igd_plus=me.igd_plus,hv=me.hv,igd=me.igd,n_nd=me.n_nd,
        piso_best=best,piso_who=who,ganho=(best-me.igd_plus)/best if best else np.nan,
        bate=me.igd_plus<best, rank=rk, n_algs=len(sub)))
dm=pd.DataFrame(rr); dm.to_csv("metricas_e7.csv",index=False)
print("\n=== IGD+ vs PISOS ==="); print(dm.round(4).to_string())
print("bate melhor piso:",int(dm.bate.sum()),"/25 | rank medio:",round(dm['rank'].mean(),2),"de",dm.n_algs.max())
der=dm[~dm.bate].copy(); der['perda']=-der.ganho
print("derrotas dentro do piso de ruido (<=58,98%):",int((der.perda<=0.5898).sum()),"/",len(der))
print("derrotas conclusivas:",der[der.perda>0.5898][['problema','igd_plus','piso_best','perda']].round(4).to_string())
print("vitorias conclusivas (>58,98%):",dm[dm.bate&(dm.ganho>0.5898)][['problema','ganho']].round(4).to_string())
# rank entre SA (exclui pisos e sobol)
SA=[a for a in mt.alg.unique() if a not in PISOS+['sobol_batch','moead_media','treed_media']]
rs=[]
for p in sorted(mt[mt.alg=='e7'].problema.unique()):
    sub=mt[(mt.problema==p)&(mt.alg.isin(SA))]
    me=sub[sub.alg=='e7'].igd_plus.iloc[0]
    rs.append(int((sub.igd_plus<me).sum())+1)
print("rank medio entre SA:",round(np.mean(rs),2),"de",len(SA))
# ---------- TRAJETORIAS ----------
tr=[]
for f in sorted(glob.glob(f"{F5}/trajetorias/main_e7_*_42.json")):
    j=json.load(open(f)); p=os.path.basename(f).replace("main_e7_","").replace("_42.json","")
    ig=[c['igd_plus'] for c in j['checkpoints']] if isinstance(j,dict) and 'checkpoints' in j else None
    if ig is None:
        ks=[k for k in (j.keys() if isinstance(j,dict) else []) ]
        print("  formato:",ks[:8]); break
    viol=sum(1 for i in range(len(ig)-1) if ig[i+1]>ig[i]+1e-12)
    pior=max([ig[i]-ig[i+1] for i in range(len(ig)-1)]+[0])
    tr.append(dict(problema=p,n=len(ig),viol=viol,ig0=ig[0],ig1=ig[-1],melhora=(ig[0]-ig[-1])/ig[0] if ig[0] else np.nan,
                   pior_salto=min([ig[i+1]-ig[i] for i in range(len(ig)-1)]+[0])))
dt=pd.DataFrame(tr); dt.to_csv("trajetorias_e7.csv",index=False)
print("\n=== TRAJETORIAS ==="); print(dt.round(4).to_string())
print("violacoes:",dt.viol.sum(),"/",int((dt.n-1).sum()),"transicoes | melhora min/max:",round(dt.melhora.min(),4),round(dt.melhora.max(),4))
# ---------- TEMPO ----------
tp=pd.read_csv(f"{F5}/tempo_f52d.csv"); t7=tp[(tp.alg=='e7')]
print("\n=== TEMPO ===")
print("maquinas:",t7.maquina.value_counts().to_dict(),"| wall total h:",round(t7.wall_s.sum()/3600,2))
print(t7.sort_values('wall_s',ascending=False).head(5).to_string())
