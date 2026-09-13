"""QUERY-JOIA batch q=10 (D42): laco HVI-greedy SEQUENCIAL sem reposicao.
Hipoteses do estado do arquivo entre os picks: (S1) arquivo cresce com mu do pick anterior;
(S2) arquivo CONGELADO na iteracao (so remove o candidato escolhido)."""
import json,os,sys,numpy as np,pandas as pd,pyarrow.parquet as pq
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149")
from importlib.machinery import SourceFileLoader
mod=SourceFileLoader("qj","/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149/05_queryjoia_hvi.py")
# reimplementa localmente p/ nao rodar o script
def nd_mask(F):
    n=len(F); keep=np.ones(n,bool); order=np.lexsort(F.T[::-1]); Fs=F[order]
    for i in range(n):
        if not keep[order[i]]: continue
        d=(Fs[i]<=Fs).all(1)&(Fs[i]<Fs).any(1); keep[order[d]]=False
    return keep
def hvi2d_batch(P,ref,C):
    P=P[(P[:,0]<ref[0])&(P[:,1]<ref[1])]
    if len(P): P=P[nd_mask(P)]; P=P[np.argsort(P[:,0])]
    L=[-np.inf]; lvl=[ref[1]]
    for a,b in P: L.append(a); lvl.append(b)
    L=np.array(L); lvl=np.array(lvl)
    R=np.minimum(np.append(L[1:],ref[0]),ref[0]); Lc=np.minimum(np.maximum(L,-1e18),ref[0])
    w=np.maximum(R-Lc,0.0)
    sw=np.concatenate([np.cumsum(w[::-1])[::-1],[0.0]]); swl=np.concatenate([np.cumsum((w*lvl)[::-1])[::-1],[0.0]])
    a=C[:,0]; b=C[:,1]
    j=np.clip(np.searchsorted(L,a,side="right")-1,0,len(L)-1)
    mb=np.searchsorted(-lvl,-b,side="left")-1
    ok=(a<ref[0])&(b<ref[1])&(mb>=0)
    lo=np.minimum(j+1,mb+1); hi=mb+1
    seg=np.where(ok,(swl[lo]-swl[hi])-b*(sw[lo]-sw[hi]),0.0)
    head=np.where(ok&(j<=mb),np.maximum(R[j]-np.maximum(a,Lc[j]),0.0)*np.maximum(lvl[j]-b,0.0),0.0)
    return np.maximum(np.where(ok,head+seg,0.0),0.0)
from pymoo.indicators.hv import HV
def hvi_md(P,ref,C):
    ind=HV(ref_point=ref); base=ind(P) if len(P) else 0.0; out=np.zeros(len(C))
    for i,c in enumerate(C):
        if (c>=ref).any(): continue
        out[i]=(ind(np.vstack([P,c]))-base) if len(P) else ind(c[None,:])
    return out

ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
NM3=int(sys.argv[1]) if len(sys.argv)>1 else 15
res=[]
for prob in ["ZDT4","ZDT1","WFG9","DTLZ2","MMF16_20"]:
    p=f"{ROOT}/q10_{prob}/42/exp_batch_c149_{prob}_42"
    m=json.load(open(p+".manifest.json")); dec=[]; hdr=None
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="decision": dec.append(dd)
        elif dd["rec"]=="header": hdr=dd
    D=hdr["D"]; M=hdr["M"]; q=m["q"]; n_init=11*D-1; G=len(dec)
    real=pq.read_table(p+"__real.parquet").to_pandas()
    Fall=real[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id"]+
        [f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]+["transf_params"]).to_pandas()
    sur=sur[sur.regime=="online"]; grp=dict(list(sur.groupby("geracao")))
    gers=list(range(1,G+1)) if M==2 else sorted(set(np.linspace(1,G,NM3).round().astype(int)))
    st={"S1_pick1":0,"S1_lote":0,"S2_lote":0,"n":0,"err1":[],"S1_lote_pos":0,"S2_lote_pos":0,"npos":0}
    for g in gers:
        dd=dec[g-1]; sub=grp[g]
        MU=sub[[f"mu_{j}" for j in range(M)]].values.astype(np.float64)
        SG=sub[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)
        rsi=sub.real_solution_id.values
        lote=dd["lote_solution_ids"]
        idx=[int(np.where(rsi==s)[0][0]) for s in lote if (rsi==s).any()]
        if len(idx)!=q: continue
        narq=n_init+q*(g-1); A=Fall[:narq]
        lo=A.min(0); hi=A.max(0); rng=np.where(hi>lo,hi-lo,1.0)
        An=(A-lo)/rng; Cn=(MU-lo)/rng; ref=np.full(M,1.1)
        tp=json.loads(sub.transf_params.iloc[0]); zstd=np.array(tp["std"],float)
        s2z=((SG/zstd)**2).sum(1)
        hv=hvi2d_batch if M==2 else hvi_md
        # pick 1
        P=An[nd_mask(An)]
        H=hv(P,ref,Cn)
        st["err1"].append(abs(H[idx[0]]-dd["hvi_escolhido"]))
        st["S1_pick1"]+= (H[idx[0]]>=H.max()-1e-12)
        # laco sequencial
        for nome,cresce in [("S1",True),("S2",False)]:
            Pw=P.copy(); avail=np.ones(len(Cn),bool); okall=True; okpos=True
            for k in range(q):
                Hk=hv(Pw,ref,Cn); Hk=np.where(avail,Hk,-1)
                top=Hk.max(); emp=np.where(Hk>=top-1e-12)[0]
                if top<=0:  # empate total -> desempate sigma / fallback
                    cand=emp; s2=np.where(avail,s2z,-1)
                    smax=s2.max(); emp2=np.where(s2>=smax-1e-9*max(1,abs(smax)))[0]
                    pick_ok = idx[k] in set(emp2.tolist())
                else:
                    if len(emp)>1:
                        s2e=np.where(np.isin(np.arange(len(s2z)),emp),s2z,-1)
                        pick_ok = abs(s2z[idx[k]]-s2e.max())<=1e-6*max(1,abs(s2e.max()))
                    else:
                        pick_ok = idx[k]==int(np.argmax(Hk))
                    okpos &= pick_ok
                okall &= pick_ok
                avail[idx[k]]=False
                if cresce: Pw=np.vstack([Pw,Cn[idx[k]]]); Pw=Pw[nd_mask(Pw)]
            st[nome+"_lote"]+=okall
            if dd["n_hvi_pos"]>0: st[nome+"_lote_pos"]+=okpos
        if dd["n_hvi_pos"]>0: st["npos"]+=1
        st["n"]+=1
    r=dict(prob=prob,M=M,G=G,n=st["n"],npos=st["npos"],pick1_argmax=st["S1_pick1"],
        err1_med=float(np.median(st["err1"])),err1_max=float(np.max(st["err1"])),
        S1_lote=st["S1_lote"],S2_lote=st["S2_lote"],S1_lote_pos=st["S1_lote_pos"],S2_lote_pos=st["S2_lote_pos"])
    res.append(r); print(r,flush=True)
pd.DataFrame(res).to_csv(os.path.join(OUT,"queryjoia_batch_c149.csv"),index=False)
