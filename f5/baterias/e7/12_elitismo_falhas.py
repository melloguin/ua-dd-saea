import json,os,sys
import pandas as pd, numpy as np
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
import src.problems as SP
from src.experiment import PROBLEM_CLASSES
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
CEL=[]; FAIL=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']; n0=11*D-1
    G=[e for e in ev if e['rec']=='e7_gen']
    prob=getattr(SP,PROBLEM_CLASSES[p])(); xl=np.asarray(prob.xl,float); xu=np.asarray(prob.xu,float)
    xc=[f"x{i}" for i in range(D)]; mc=[f"mu_{i}" for i in range(M)]; sc=[f"sigma_{i}" for i in range(M)]
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao','real_solution_id']+xc+mc+sc)
    on=sur[sur.regime=='online']; del sur
    real=pd.read_parquet(base+"__real.parquet",columns=xc)
    Xr=real[xc].to_numpy(np.float32)
    t=dict(problema=p,D=D,M=M,jan_soma=0,jan_n=0,jan_max=0,linhas_tag=0,
           head_unif_ks=[],pf_dom=0,pf_n=0,sig_cv=0.0,sig_cv_n=0)
    for g in G:
        c=g['geracao']; blk=on[on.geracao==c]
        if len(blk)!=1900: continue
        rs=blk['real_solution_id'].to_numpy()
        idx=np.arange(len(blk)); w=idx//100
        for j in range(3):
            s=n0+3*(c-1)+j
            if s>=len(Xr): continue
            m=(~np.isnan(rs))&(rs==s)
            t['jan_n']+=1; nj=len(set(w[m].tolist())); t['jan_soma']+=nj; t['jan_max']=max(t['jan_max'],nj)
            t['linhas_tag']+=int(m.sum())
        # head(100) uniforme? KS vs U(xl,xu) na 1a coordenada
        H=blk.iloc[:100][xc].to_numpy(np.float64)
        u=((H-xl)/(xu-xl)).ravel()
        u=np.sort(u); n=len(u)
        ks=float(np.max(np.abs(np.arange(1,n+1)/n-u)))
        t['head_unif_ks'].append(ks)
        # pop final: fracao dominada (em mu) -> a pop final do AR-MOEA e' selecionada
        MU=blk.iloc[-100:][mc].to_numpy(np.float64)
        dom=0
        for i in range(100):
            le=(MU<=MU[i]).all(axis=1); lt=(MU<MU[i]).any(axis=1)
            dom+=int((le&lt).any())
        t['pf_dom']+=dom; t['pf_n']+=100
        SG=blk.iloc[-100:][sc].to_numpy(np.float64)
        t['sig_cv']+=float((SG.std(axis=0)/SG.mean(axis=0)).mean()); t['sig_cv_n']+=1
    t['jan_media']=t['jan_soma']/t['jan_n'] if t['jan_n'] else np.nan
    t['head_ks_med']=float(np.median(t['head_unif_ks'])); t.pop('head_unif_ks')
    t['sig_cv_med']=t['sig_cv']/t['sig_cv_n'] if t['sig_cv_n'] else np.nan
    CEL.append(t); print("ok",p,round(t['jan_media'],2),round(t['head_ks_med'],4),flush=True)
df=pd.DataFrame(CEL); df.to_csv("elitismo_e7.csv",index=False)
pd.set_option('display.width',260); print(df.to_string())
print("\njanelas internas por infill: media",round(df.jan_soma.sum()/df.jan_n.sum(),3),"max",df.jan_max.max(),
      "| linhas taggeadas",df.linhas_tag.sum(),"em",df.jan_n.sum(),"infills")
print("KS(head100 vs U) mediana global:",round(df.head_ks_med.median(),4),"(1,36/sqrt(100D) e' o critico 5%)")
print("pop final: fracao DOMINADA em mu:",round(df.pf_dom.sum()/df.pf_n.sum(),4))
print("CV de sigma dentro da pop final (mediana das celulas):",round(df.sig_cv_med.median(),4))
