import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
def nd(Y):
    n=len(Y); dom=np.zeros(n,bool)
    for i in range(n):
        le=(Y<=Y[i]).all(axis=1); lt=(Y<Y[i]).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return int((~dom).sum())
CEL=[]; ROWS=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G); n0=11*D-1
    xc=[f"x{i}" for i in range(D)]; mc=[f"mu_{i}" for i in range(M)]; sc=[f"sigma_{i}" for i in range(M)]
    fc=[f"f{i}" for i in range(M)]
    real=pd.read_parquet(base+"__real.parquet",columns=['solution_id','fase']+xc+fc)
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao','real_solution_id']+xc+mc+sc)
    on=sur[sur.regime=='online']; del sur
    Xr=real[xc].to_numpy(np.float32); Fr=real[fc].to_numpy(np.float64)
    grp={g:d for g,d in on.groupby('geracao')}
    t=dict(problema=p,D=D,M=M,h1=0,h2=0,h3=0,n=0,vor_conv=0,vor_conv_n=0,vor_inc=0,vor_inc_n=0,
           u11_num=0.0,u11_den=0.0,ea_melhora=0,ea_n=0,rsid_n=0,rsid_ok=0)
    for g in G:
        c=g['geracao']; blk=grp.get(c)
        if blk is None: continue
        pf=blk.iloc[-100:]
        Xp=pf[xc].to_numpy(np.float32); MU=pf[mc].to_numpy(np.float64); SG=pf[sc].to_numpy(np.float64)
        nrm=np.linalg.norm(MU,axis=1); sbar=SG.mean(axis=1)
        ymin=np.array(g['ymin'],dtype=np.float64)
        t['n']+=1
        t['h1']+= (nd(Fr[:n0+3*(c-1)])==g['n_front1'])
        t['h2']+= (nd(Fr[:min(n0+3*c,len(Fr))])==g['n_front1'])
        t['h3']+= (nd(MU)==g['n_front1'])
        sids=[n0+3*(c-1)+j for j in range(3)]; sids=[s for s in sids if s<len(Xr)]
        pos=[]
        for s in sids:
            k=Xr[s].tobytes(); hit=[i for i in range(100) if Xp[i].tobytes()==k]
            pos.append(hit[0] if hit else -1)
        posv=[v for v in pos if v>=0]
        # U11: erro de fantasia — mu do infill (des-transladado) vs f real
        for s,v in zip(sids,pos):
            if v<0: continue
            mu_cru=MU[v]+ymin
            t['u11_num']+=float(np.abs(mu_cru-Fr[s]).sum()); t['u11_den']+=float(np.abs(Fr[s]).sum())
        # real_solution_id gravado na linha certa?
        rs=pf['real_solution_id'].to_numpy()
        for s,v in zip(sids,pos):
            if v<0: continue
            t['rsid_n']+=1; t['rsid_ok']+= (not np.isnan(rs[v])) and int(rs[v])==s
        # Voronoi induzido pelos 3 infills (espaco dos objetivos preditos)
        if len(posv)==3:
            Cn=MU[posv]
            dist=((MU[:,None,:]-Cn[None,:,:])**2).sum(axis=2)
            lab=dist.argmin(axis=1)
            for j,i in enumerate(posv):
                cl=np.where(lab==j)[0]
                if g['ramo']=='convergencia':
                    t['vor_conv_n']+=1; t['vor_conv']+= (i==cl[np.argmin(nrm[cl])])
                else:
                    t['vor_inc_n']+=1; t['vor_inc']+= (i==cl[np.argmax(sbar[cl])])
        # o EA interno evolui? media de ||mu|| na 1a vs 19a janela de 100
        if len(blk)==1900:
            W=blk[mc].to_numpy(np.float64)
            a=np.linalg.norm(W[:100],axis=1).mean(); b=np.linalg.norm(W[-100:],axis=1).mean()
            t['ea_n']+=1; t['ea_melhora']+= (b<a)
            ROWS.append(dict(problema=p,ciclo=c,ramo=g['ramo'],w1=a,w19=b,delta=(b-a)/a if a else np.nan))
    t['u11_wape']=t['u11_num']/t['u11_den'] if t['u11_den'] else np.nan
    CEL.append(t); print("ok",p,flush=True)
de=pd.DataFrame(CEL); de.to_csv("nf1_voronoi_u11_e7.csv",index=False)
pd.DataFrame(ROWS).to_csv("ea_interno_e7.csv",index=False)
pd.set_option('display.width',300)
print(de.to_string())
print("\nTOTAIS: h1",de.h1.sum(),"h2",de.h2.sum(),"h3",de.h3.sum(),"/",de.n.sum())
print("Voronoi conv",de.vor_conv.sum(),"/",de.vor_conv_n.sum()," inc",de.vor_inc.sum(),"/",de.vor_inc_n.sum())
print("real_solution_id na linha certa:",de.rsid_ok.sum(),"/",de.rsid_n.sum())
print("U11 WAPE global:",round(de.u11_num.sum()/de.u11_den.sum(),4),"| mediana por celula:",round(de.u11_wape.median(),4))
print("EA interno melhora (||mu|| medio w19<w1):",de.ea_melhora.sum(),"/",de.ea_n.sum())
