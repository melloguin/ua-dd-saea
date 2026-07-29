"""(a) fallback_aleatorio: o escolhido esta DENTRO do conjunto sigma2-maximo empatado?
(b) geometria: os escolhidos por desempate/fallback estao nos CANTOS do box? (fracao de coords no bound)"""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq,sys
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149")
from _hvlib import nd_mask, hvi2d_batch, hvi_md
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    if exp=="batch": continue
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    hdr=json.loads(open(p+".jsonl").readline()); D=hdr["D"];M=hdr["M"]
    dec=[json.loads(l) for l in open(p+".jsonl") if '"rec": "decision"' in l]
    real=pq.read_table(p+"__real.parquet").to_pandas()
    XC=[f"x{j}" for j in range(D)]
    X=real[XC].values.astype(np.float64)
    lo=X.min(0); hi=X.max(0)  # aprox dos bounds pelo DoE LHS-maximin (cobre o box)
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id","transf_params"]+
        [f"sigma_{j}" for j in range(M)]).to_pandas()
    on=sur[sur.regime=="online"]; grp=dict(list(on.groupby("geracao")))
    fb_ok=0;fb_n=0;ds_ok=0;ds_n=0
    frac_bound={"hvi":[], "desempate_sigma":[], "fallback_aleatorio":[]}
    for g in range(1,len(dec)+1):
        dd=dec[g-1]; cam=dd["caminho"].split(":")[-1]; sub=grp[g]
        w=np.where(sub.real_solution_id.values==dd["solution_id"])[0]
        if len(w)!=1: continue
        w=int(w[0])
        tp=json.loads(sub.transf_params.iloc[0]); zs=np.array(tp["std"],float)
        s2=((sub[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)/zs)**2).sum(1)
        smax=s2.max(); emp=np.where(s2>=smax-1e-9*max(1,abs(smax)))[0]
        if cam=="fallback_aleatorio":
            fb_n+=1; fb_ok+= (w in set(emp.tolist()))
        elif cam=="desempate_sigma":
            ds_n+=1; ds_ok+= abs(s2[w]-smax)<=1e-6*max(1,abs(smax))
        xs=X[int(dd["solution_id"])]
        rel=np.minimum(np.abs(xs-lo),np.abs(xs-hi))/np.maximum(hi-lo,1e-12)
        frac_bound.setdefault(cam,[]).append(float((rel<1e-3).mean()))
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,
        fb_n=fb_n,fb_ok=fb_ok,ds_n=ds_n,ds_ok=ds_ok,
        cantos_hvi=float(np.mean(frac_bound["hvi"])) if frac_bound["hvi"] else None,
        cantos_desemp=float(np.mean(frac_bound["desempate_sigma"])) if frac_bound["desempate_sigma"] else None,
        cantos_fb=float(np.mean(frac_bound["fallback_aleatorio"])) if frac_bound["fallback_aleatorio"] else None))
    print(rows[-1],flush=True)
df=pd.DataFrame(rows); df.to_csv(OUT+"/fallback_cantos_c149.csv",index=False)
print("\nTOTAIS main: desempate_sigma %d/%d ; fallback_aleatorio dentro do conjunto sigma2-max %d/%d"%(
    df.ds_ok.sum(),df.ds_n.sum(),df.fb_ok.sum(),df.fb_n.sum()))
print("fracao media de coords NO BOUND: hvi %.3f | desempate %.3f | fallback %.3f"%(
    np.nanmean(df.cantos_hvi),np.nanmean(df.cantos_desemp),np.nanmean(df.cantos_fb)))
