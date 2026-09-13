"""QUERY-JOIA c149: reconstrucao da regra D96 (HVI-greedy) a partir da ③ + ①.
Testa 2 hipoteses de ref: (A) ref=1.1 (nadir do ARQUIVO normalizado=1) ; (B) ref=1.1*nadir do FRONT-ND normalizado.
Confere: (i) hvi_escolhido do log == HVI recomputado do escolhido; (ii) o escolhido eh argmax do HVI;
(iii) no empate, o escolhido eh argmax de sigma2 agregada EM Z.
M=2: TODAS as iteracoes. M=3: amostra (pymoo HV exato)."""
import json,os,sys,numpy as np,pandas as pd,pyarrow.parquet as pq,collections
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"

def nd_mask(F):
    n=len(F); keep=np.ones(n,bool)
    order=np.lexsort(F.T[::-1])
    Fs=F[order]
    for i in range(n):
        if not keep[order[i]]: continue
        d=(Fs[i]<=Fs).all(1)&(Fs[i]<Fs).any(1)
        keep[order[d]]=False
    return keep

def hv2d(P,ref):
    if len(P)==0: return 0.0
    P=P[np.lexsort((P[:,1],P[:,0]))]
    hv=0.0; prev=ref[1]
    for a,b in P:
        if b<prev and a<ref[0]:
            hv+=(ref[0]-a)*(prev-b); prev=b
    return hv

def hvi2d_batch(P,ref,C):
    """P: front ND (n,2) minimizacao; ref (2,); C: candidatos (m,2). retorna HVI exclusivo de cada candidato."""
    m=len(C); out=np.zeros(m)
    P=P[(P[:,0]<ref[0])&(P[:,1]<ref[1])]
    if len(P):
        P=P[nd_mask(P)]
        P=P[np.argsort(P[:,0])]
    # escada: segmentos [L_i,R_i) com nivel lvl_i
    L=[-np.inf]; lvl=[ref[1]]
    for a,b in P:
        L.append(a); lvl.append(b)
    L=np.array(L); lvl=np.array(lvl)
    R=np.append(L[1:],ref[0]); R=np.minimum(R,ref[0])
    Lc=np.minimum(np.maximum(L,-1e18),ref[0])
    w=np.maximum(R-Lc,0.0)                      # comprimento do segmento (clip a ref0)
    # prefixos SUFIXO (do fim p/ o inicio)
    sw=np.concatenate([np.cumsum(w[::-1])[::-1],[0.0]])
    swl=np.concatenate([np.cumsum((w*lvl)[::-1])[::-1],[0.0]])
    a=C[:,0]; b=C[:,1]
    j=np.searchsorted(L,a,side="right")-1        # segmento que contem a
    j=np.clip(j,0,len(L)-1)
    # m(b): ultimo indice com lvl > b  (lvl decrescente)
    mb=np.searchsorted(-lvl,-b,side="left")-1    # lvl[0..mb] > b
    ok=(a<ref[0])&(b<ref[1])&(mb>=0)
    lo=np.minimum(j+1,mb+1); hi=mb+1
    seg_sum=np.where(ok,(swl[lo]-swl[hi])-b*(sw[lo]-sw[hi]),0.0)
    head=np.where(ok&(j<=mb),np.maximum(R[j]-np.maximum(a,Lc[j]),0.0)*np.maximum(lvl[j]-b,0.0),0.0)
    out=np.where(ok,head+seg_sum,0.0)
    return np.maximum(out,0.0)

from pymoo.indicators.hv import HV
def hvi_md(P,ref,C):
    ind=HV(ref_point=ref)
    base=ind(P) if len(P) else 0.0
    out=np.zeros(len(C))
    for i,c in enumerate(C):
        if (c>=ref).any(): out[i]=0.0; continue
        out[i]=ind(np.vstack([P,c]))-base if len(P) else ind(c[None,:])
    return out

cells=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"
    prob=lab[4:] if lab.startswith("q10_") else lab
    cells.append((exp,prob,lab,d))

MAXITER_M3=int(sys.argv[1]) if len(sys.argv)>1 else 20
res=[]; det=[]
for exp,prob,lab,d in cells:
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    m=json.load(open(p+".manifest.json")); D=None
    dec=[]; hdr=None
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="decision": dec.append(dd)
        elif dd["rec"]=="header": hdr=dd
    D=hdr["D"]; M=hdr["M"]; q=m["q"]; n_init=11*D-1
    real=pq.read_table(p+"__real.parquet").to_pandas()
    Fall=real[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    sur=pq.read_table(p+"__surrogate.parquet",
        columns=["regime","geracao","real_solution_id"]+[f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]+["transf_params"]).to_pandas()
    sur=sur[sur.regime=="online"]
    G=len(dec)
    gers=list(range(1,G+1)) if M==2 else sorted(set(np.linspace(1,G,MAXITER_M3).round().astype(int)))
    grp=dict(list(sur.groupby("geracao")))
    okA=okB=0; argA=argB=0; tie_ok=0; tie_n=0; nchk=0; errA=[]; errB=[]
    tie_falha=[]
    for g in gers:
        dd=dec[g-1]; sub=grp[g]
        MU=sub[[f"mu_{j}" for j in range(M)]].values.astype(np.float64)
        SG=sub[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)
        sel=np.where(sub.real_solution_id.notna().values)[0]
        if len(sel)!=q: continue
        narq=n_init+q*(g-1)
        A=Fall[:narq]
        lo=A.min(0); hi=A.max(0); rng=np.where(hi>lo,hi-lo,1.0)
        An=(A-lo)/rng
        Pn=An[nd_mask(An)]
        Cn=(MU-lo)/rng
        tp=json.loads(sub.transf_params.iloc[0]); zstd=np.array(tp["std"],float)
        s2z=((SG/zstd)**2).sum(1)
        for hyp,ref in [("A",np.full(M,1.1)),("B",1.1*Pn.max(0))]:
            if hyp=="B" and (ref<=0).any(): ref=np.maximum(ref,1e-9)
            H = hvi2d_batch(Pn,ref,Cn) if M==2 else hvi_md(Pn,ref,Cn)
            hsel=H[sel[0]]
            err=abs(hsel-dd["hvi_escolhido"])
            isarg = hsel>=H.max()-1e-12
            if hyp=="A": errA.append(err); okA+= (err<=1e-6+1e-4*abs(dd["hvi_escolhido"])); argA+=isarg; HA=H
            else: errB.append(err); okB+= (err<=1e-6+1e-4*abs(dd["hvi_escolhido"])); argB+=isarg
        # desempate: entre os empatados no topo do HVI(A), o escolhido eh argmax sigma2_z?
        top=HA.max(); emp=np.where(HA>=top-1e-12)[0]
        if len(emp)>1 and dd["caminho"].endswith("desempate_sigma"):
            tie_n+=1
            s2e=s2z[emp]; best=emp[np.argmax(s2e)]
            if abs(s2z[sel[0]]-s2e.max())<=1e-4*max(1,s2e.max()): tie_ok+=1
            else: tie_falha.append((g,float(s2z[sel[0]]),float(s2e.max())))
        nchk+=1
    res.append(dict(exp=exp,prob=prob,D=D,M=M,q=q,G=G,n_check=nchk,
        hvi_okA=okA,hvi_okB=okB,argmax_A=argA,argmax_B=argB,
        errA_med=float(np.median(errA)) if errA else None, errA_max=float(np.max(errA)) if errA else None,
        errB_med=float(np.median(errB)) if errB else None,
        tie_n=tie_n,tie_ok=tie_ok,tie_falha=json.dumps(tie_falha[:5])))
    print(f"[{exp}/{prob}] M={M} chk={nchk} hipA ok={okA} argmax={argA} errmed={np.median(errA):.3e} errmax={np.max(errA):.3e} | hipB ok={okB} argmax={argB} | desempate {tie_ok}/{tie_n}",flush=True)

pd.DataFrame(res).to_csv(os.path.join(OUT,"queryjoia_hvi_c149.csv"),index=False)
print("SALVO")
