import json,os,sys
import pandas as pd, numpy as np
from sklearn.cluster import KMeans
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
CIC=[]; CEL=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    man=json.load(open(base+".manifest.json")); ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G)
    xc=[f"x{i}" for i in range(D)]; mc=[f"mu_{i}" for i in range(M)]; sc=[f"sigma_{i}" for i in range(M)]
    real=pd.read_parquet(base+"__real.parquet",columns=['solution_id','fase','fe_index']+xc+[f"f{i}" for i in range(M)])
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao','real_solution_id']+xc+mc+sc)
    on=sur[sur.regime=='online']
    del sur
    n0=11*D-1
    Xr=real[xc].to_numpy(np.float32); Fr=real[[f"f{i}" for i in range(M)]].to_numpy(np.float64)
    # indice de X (bytes) -> solution_id, para o casamento bit-a-bit
    key2sid={}
    for i in range(len(Xr)): key2sid.setdefault(Xr[i].tobytes(),[]).append(i)
    grp={g:d for g,d in on.groupby('geracao')}
    tot=dict(n_ciclos=0,inf_tot=0,inf_achados=0,
             conv_glob=0,conv_n=0,inc_glob=0,inc_n=0,
             conv_popmin=0,conv_cru=0,
             km_conv_ok=0,km_conv_n=0,km_inc_ok=0,km_inc_n=0,km3distintos=0,km_n=0,
             nf1_ok_pop=0,nf1_ok_arq=0,nf1_n=0, warm_inter=0, warm_n=0, blk1900=0)
    for g in G:
        c=g['geracao']; blk=grp.get(c)
        if blk is None: continue
        tot['n_ciclos']+=1
        if len(blk)==1900: tot['blk1900']+=1
        pf=blk.iloc[-100:]
        Xp=pf[xc].to_numpy(np.float32); MU=pf[mc].to_numpy(np.float64); SG=pf[sc].to_numpy(np.float64)
        nrm=np.linalg.norm(MU,axis=1); sbar=SG.mean(axis=1)
        ymin=np.array(g['ymin'],dtype=np.float64)
        nrm_cru=np.linalg.norm(MU+ymin,axis=1)
        nrm_popmin=np.linalg.norm(MU-MU.min(axis=0),axis=1)
        # infills do ciclo c
        sids=[n0+3*(c-1)+j for j in range(3)]
        sids=[s for s in sids if s<len(Xr)]
        pos=[]
        for s in sids:
            k=Xr[s].tobytes(); hit=[i for i in range(100) if Xp[i].tobytes()==k]
            pos.append(hit[0] if hit else -1)
        tot['inf_tot']+=len(sids); tot['inf_achados']+=sum(1 for v in pos if v>=0)
        posv=[v for v in pos if v>=0]
        rec=dict(problema=p,ciclo=c,ramo=g['ramo'],n_inf=len(sids),n_achados=len(posv))
        if len(posv)==3:
            if g['ramo']=='convergencia':
                tot['conv_n']+=1
                if int(np.argmin(nrm)) in posv: tot['conv_glob']+=1
                if int(np.argmin(nrm_popmin)) in posv: tot['conv_popmin']+=1
                if int(np.argmin(nrm_cru)) in posv: tot['conv_cru']+=1
                rec['rank_min']=int(np.sort(np.argsort(np.argsort(nrm))[posv])[0])
                rec['ranks']=sorted(np.argsort(np.argsort(nrm))[posv].tolist())
            else:
                tot['inc_n']+=1
                if int(np.argmax(sbar)) in posv: tot['inc_glob']+=1
                rec['rank_min']=int(np.sort(99-np.argsort(np.argsort(sbar))[posv])[0])
                rec['ranks']=sorted((99-np.argsort(np.argsort(sbar))[posv]).tolist())
            # reconstrucao k-means k=3 nos objetivos PREDITOS
            km=KMeans(n_clusters=3,n_init=10,random_state=0).fit(MU)
            lab=km.labels_
            tot['km_n']+=1
            labs=set(lab[posv])
            if len(labs)==3: tot['km3distintos']+=1
            ok=0
            for i in posv:
                cl=np.where(lab==lab[i])[0]
                if g['ramo']=='convergencia':
                    ok+= (i==cl[np.argmin(nrm[cl])])
                else:
                    ok+= (i==cl[np.argmax(sbar[cl])])
            rec['km_ok']=ok
            if g['ramo']=='convergencia':
                tot['km_conv_n']+=3; tot['km_conv_ok']+=ok
            else:
                tot['km_inc_n']+=3; tot['km_inc_ok']+=ok
        # n_front1: |ND| da pop final (mu) x |ND| do arquivo real
        def nd(Y):
            n=len(Y); dom=np.zeros(n,bool)
            for i in range(n):
                if dom[i]: continue
                le=(Y<=Y[i]).all(axis=1); lt=(Y<Y[i]).any(axis=1)
                if (le&lt).any(): dom[i]=True
            return int((~dom).sum())
        tot['nf1_n']+=1
        if nd(MU)==g['n_front1']: tot['nf1_ok_pop']+=1
        narq=n0+3*(c-1)
        if nd(Fr[:narq])==g['n_front1']: tot['nf1_ok_arq']+=1
        rec['nf1_log']=g['n_front1']; rec['nf1_pop']=nd(MU); rec['nf1_arq']=nd(Fr[:narq])
        # warm start: head(100) do ciclo c+1 vs tail(100) do ciclo c
        nb=grp.get(c+1)
        if nb is not None:
            tot['warm_n']+=1
            H=nb.iloc[:100][xc].to_numpy(np.float32)
            s1=set(H[i].tobytes() for i in range(100)); s2=set(Xp[i].tobytes() for i in range(100))
            inter=len(s1&s2); tot['warm_inter']+=inter
            rec['warm_inter']=inter
            rec['head_mean']=float(H.mean()); rec['head_std']=float(H.std())
        CIC.append(rec)
    tot['problema']=p; tot['D']=D; tot['M']=M; CEL.append(tot)
    print("ok",p,tot['conv_glob'],"/",tot['conv_n'],"|",tot['inc_glob'],"/",tot['inc_n'],flush=True)
dc=pd.DataFrame(CIC); dc.to_csv("queryjoia_ciclos_e7.csv",index=False)
de=pd.DataFrame(CEL); de.to_csv("queryjoia_celulas_e7.csv",index=False)
pd.set_option('display.width',300)
print(de[['problema','n_ciclos','inf_tot','inf_achados','conv_glob','conv_n','inc_glob','inc_n','conv_popmin','conv_cru','km3distintos','km_n','km_conv_ok','km_conv_n','km_inc_ok','km_inc_n','nf1_ok_pop','nf1_ok_arq','warm_inter','warm_n','blk1900']].to_string())
print("\nTOTAIS:")
for k in ['n_ciclos','inf_tot','inf_achados','conv_glob','conv_n','inc_glob','inc_n','conv_popmin','conv_cru','km3distintos','km_n','km_conv_ok','km_conv_n','km_inc_ok','km_inc_n','nf1_ok_pop','nf1_ok_arq','nf1_n','warm_inter','warm_n','blk1900']:
    print("  ",k,de[k].sum())
