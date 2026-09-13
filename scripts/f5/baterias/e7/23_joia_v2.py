import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
CEL=[]
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
    t=dict(problema=p,conv_ok=0,conv_n=0,inc_ok=0,inc_n=0,dupX_ciclos=0,ciclos=0,
           conv_popmin=0,conv_cru=0,inc_soma=0)
    for g in G:
        c=g['geracao']; blk=grp.get(c)
        if blk is None or len(blk)!=1900: continue
        pf=blk.iloc[-100:]
        Xp=pf[xc].to_numpy(np.float32); MU=pf[mc].to_numpy(np.float64); SG=pf[sc].to_numpy(np.float64)
        nrm=np.linalg.norm(MU,axis=1); sb=SG.mean(axis=1)
        ymin=np.array(g['ymin'],float)
        nrm_cru=np.linalg.norm(MU+ymin,axis=1)
        nrm_pm=np.linalg.norm(MU-MU.min(axis=0),axis=1)
        keys={Xr[n0+3*(c-1)+j].tobytes() for j in range(3) if n0+3*(c-1)+j<len(Xr)}
        if len(keys)!=3: continue
        t['ciclos']+=1
        kx=[Xp[i].tobytes() for i in range(100)]
        if len(set(kx))<100: t['dupX_ciclos']+=1
        if g['ramo']=='convergencia':
            t['conv_n']+=1
            t['conv_ok']+= (kx[int(np.argmin(nrm))] in keys)
            t['conv_cru']+= (kx[int(np.argmin(nrm_cru))] in keys)
            t['conv_popmin']+= (kx[int(np.argmin(nrm_pm))] in keys)
        else:
            t['inc_n']+=1
            t['inc_ok']+= (kx[int(np.argmax(sb))] in keys)
    CEL.append(t); print("ok",p,t['conv_ok'],"/",t['conv_n'],"|",t['inc_ok'],"/",t['inc_n'],flush=True)
df=pd.DataFrame(CEL); df.to_csv("queryjoia_v2_e7.csv",index=False)
pd.set_option('display.width',250); print(df.to_string())
print("\n=== IDENTIDADE (casamento por CONJUNTO de X; MC-dropout torna mu ambiguo em X duplicado) ===")
print("convergencia: argmin global de ||mu|| ESTA entre os 3 infills:",df.conv_ok.sum(),"/",df.conv_n.sum(),
      f"({100*df.conv_ok.sum()/df.conv_n.sum():.2f}%)")
print("incerteza:    argmax global de sigma-barra ESTA entre os 3 infills:",df.inc_ok.sum(),"/",df.inc_n.sum(),
      f"({100*df.inc_ok.sum()/df.inc_n.sum():.2f}%)")
print("REFUTADORES  -> translacao pelo MIN DA POP:",df.conv_popmin.sum(),"/",df.conv_n.sum(),
      f"({100*df.conv_popmin.sum()/df.conv_n.sum():.1f}%)  | espaco CRU (mu+ymin):",df.conv_cru.sum(),"/",df.conv_n.sum(),
      f"({100*df.conv_cru.sum()/df.conv_n.sum():.1f}%)")
print("ciclos com X duplicado na pop final:",df.dupX_ciclos.sum(),"/",df.ciclos.sum())
