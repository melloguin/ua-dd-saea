import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
FA=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']; n0=11*D-1
    G=[e for e in ev if e['rec']=='e7_gen']
    xc=[f"x{i}" for i in range(D)]; mc=[f"mu_{i}" for i in range(M)]; sc=[f"sigma_{i}" for i in range(M)]
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao']+xc+mc+sc)
    on=sur[sur.regime=='online']; del sur
    real=pd.read_parquet(base+"__real.parquet",columns=xc); Xr=real[xc].to_numpy(np.float32)
    grp={g:d for g,d in on.groupby('geracao')}
    for g in G:
        c=g['geracao']; blk=grp.get(c)
        if blk is None or len(blk)!=1900: continue
        pf=blk.iloc[-100:]
        Xp=pf[xc].to_numpy(np.float32); MU=pf[mc].to_numpy(np.float64); SG=pf[sc].to_numpy(np.float64)
        nrm=np.linalg.norm(MU,axis=1); sb=SG.mean(axis=1)
        pos=[]
        for j in range(3):
            s=n0+3*(c-1)+j
            if s>=len(Xr): continue
            h=[i for i in range(100) if Xp[i].tobytes()==Xr[s].tobytes()]
            pos+= [h[0]] if h else []
        if len(pos)!=3: continue
        if g['ramo']=='convergencia':
            k=int(np.argmin(nrm))
            if k in pos: continue
            best=nrm[pos].min(); gap=(best-nrm[k])/max(abs(nrm[k]),1e-300)
            FA.append(dict(problema=p,ciclo=c,ramo='convergencia',val_global=nrm[k],val_escolhido=best,
                gap_rel=gap,n_dup_X=int(sum(1 for i in range(100) if Xp[i].tobytes()==Xp[k].tobytes()))))
        else:
            k=int(np.argmax(sb))
            if k in pos: continue
            best=sb[pos].max(); gap=(sb[k]-best)/max(abs(sb[k]),1e-300)
            FA.append(dict(problema=p,ciclo=c,ramo='incerteza',val_global=sb[k],val_escolhido=best,
                gap_rel=gap,n_dup_X=int(sum(1 for i in range(100) if Xp[i].tobytes()==Xp[k].tobytes()))))
df=pd.DataFrame(FA); df.to_csv("falhas_joia_e7.csv",index=False)
pd.set_option('display.width',250)
print(df.to_string())
print("\nn falhas:",len(df),"| gap relativo: min",df.gap_rel.min(),"mediana",df.gap_rel.median(),"max",df.gap_rel.max())
print("com X duplicado na pop final:",int((df.n_dup_X>1).sum()))
