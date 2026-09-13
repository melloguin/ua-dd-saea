import json,os,glob
import pandas as pd, numpy as np
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
tr=[]
for f in sorted(glob.glob(f"{F5}/trajetorias/main_e7_*_42.json")):
    j=json.load(open(f)); p=os.path.basename(f).replace("main_e7_","").replace("_42.json","")
    ig=[c['igd_plus'] for c in j]; nd=[c['n_nd'] for c in j]; fe=[c['fe'] for c in j]
    viol=sum(1 for i in range(len(ig)-1) if ig[i+1]>ig[i]+1e-12)
    pior=max([ig[i+1]-ig[i] for i in range(len(ig)-1)]+[0.0])
    tr.append(dict(problema=p,n_ck=len(ig),viol=viol,pior_salto=pior,ig0=ig[0],ig1=ig[-1],
        melhora=(ig[0]-ig[-1])/ig[0] if ig[0] else np.nan,nd0=nd[0],nd1=nd[-1],fe_max=fe[-1]))
dt=pd.DataFrame(tr); dt.to_csv("trajetorias_e7.csv",index=False)
pd.set_option('display.width',250)
print("=== TRAJETORIAS (20 checkpoints) ==="); print(dt.round(4).to_string())
print("violacoes de monotonicidade:",dt.viol.sum(),"/",int((dt.n_ck-1).sum()),"| pior salto:",dt.pior_salto.max())
print("melhora 1o->ultimo: min",round(dt.melhora.min(),4),"max",round(dt.melhora.max(),4),"mediana",round(dt.melhora.median(),4))
# ganho sobre o DoE (endpoint honesto): IGD+ no checkpoint com fe<=11D-1 vs final
print()
# WAPE por objetivo (definicao oficial F5.2e): mediana das variacoes POR OBJETIVO
sn=pd.read_csv(f"{F5}/sonda_f52e.csv"); e=sn[(sn.alg=='e7')&(sn.exp=='main')]
d=[]
for (p,o),g in e.groupby(['problema','obj']):
    g=g.sort_values('bloco'); w0=g.wape.iloc[0]; w1=g.wape.iloc[-1]
    d.append(dict(problema=p,obj=o,w0=w0,w1=w1,dw=(w1-w0)/w0 if w0 else np.nan,
                  cob0=g.cobertura95.iloc[0],cob1=g.cobertura95.iloc[-1],corr1=g['corr'].iloc[-1]))
dd=pd.DataFrame(d); dd.to_csv("sonda_porobj_e7.csv",index=False)
print("=== SONDA por OBJETIVO (n=%d series) ==="%len(dd))
print("dWAPE mediana POR OBJETIVO:",round(dd.dw.median(),4),"| media:",round(dd.dw.mean(),4),"| melhoram:",int((dd.dw<0).sum()),"/",len(dd))
print("cobertura95 final mediana:",round(dd.cob1.median(),4),"| min:",round(dd.cob1.min(),4),"| max:",round(dd.cob1.max(),4))
print("corr final mediana:",round(dd.corr1.median(),4))
print(dd.sort_values('dw').round(4).head(8).to_string()); print(dd.sort_values('dw').round(4).tail(8).to_string())
