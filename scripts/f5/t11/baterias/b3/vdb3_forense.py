"""VD-b3 FORENSE: qual ramo do UpdataArchive roda? Reconstrucao do ciclo 1.
Codigo: algorithms/_PlatEMO/.../K-RVEA/UpdataArchive.m:41 -> ramo (a) sse size(Via,1) > NI-mu.
Ramo (a) = BUG (indexa Total (solucoes) com posicao em Via (vetores)).
"""
import json, os, itertools, numpy as np, pandas as pd
from math import comb
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'

def uniform_point_nbi(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.array(list(itertools.combinations(range(1,H1+M),M-1)),dtype=float)
    W=W-np.arange(0,M-1)[None,:]-1
    W=(np.hstack([W,np.full((len(W),1),H1)])-np.hstack([np.zeros((len(W),1)),W]))/H1
    if H1<M:
        H2=0
        while comb(H1+M-1,M-1)+comb(H2+M,M-1)<=N: H2+=1
        if H2>0:
            W2=np.array(list(itertools.combinations(range(1,H2+M),M-1)),dtype=float)
            W2=W2-np.arange(0,M-1)[None,:]-1
            W2=(np.hstack([W2,np.full((len(W2),1),H2)])-np.hstack([np.zeros((len(W2),1)),W2]))/H2
            W=np.vstack([W,W2/2+1/(2*M)])
    W=np.maximum(W,1e-6)
    return W,len(W)

def angles(A,B):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300)
    Bn=B/np.maximum(np.linalg.norm(B,axis=1,keepdims=True),1e-300)
    c=np.clip(An@Bn.T,-1,1)
    return np.arccos(c)

def noactive(PopObj,V):
    P=PopObj-PopObj.min(0,keepdims=True)
    a=angles(P,V).argmin(1)
    return len(V)-len(np.unique(a)), np.unique(a)

res=[]
for prob in sorted(os.listdir(ROOT)):
    base=f'{ROOT}/{prob}/42/exp_main_b3_{prob}_42'
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[x for x in L if x.get('rec')=='header'][0]
    gens=[x for x in L if x.get('rec')=='b3_gen']
    D,M,Nreq=hdr['D'],hdr['M'],hdr['N_vetores']
    NI=11*D-1; mu=5
    V0,N=uniform_point_nbi(Nreq,M)
    r=dict(problema=prob,D=D,M=M,N=N,NI=NI,NI_mu=NI-mu,
           ramo_a_estrutural=(NI-mu)<N)   # size(Via,1)<=N; se NI-mu>=N => impossivel
    if not r['ramo_a_estrutural']:
        r['ciclo1_size_Via']=None; r['ciclo1_ramo']='(b) ESTRUTURAL'
        res.append(r); continue
    # ---- reconstrucao do ciclo 1
    real=pd.read_parquet(base+'__real.parquet')
    fc=[c for c in real.columns if c.startswith('f') and c!='fe_index' and c!='fase']
    xc=[c for c in real.columns if c.startswith('x')]
    A1=real[real.fase=='init']
    A1Obj=A1[fc].to_numpy(float); A1Dec=A1[xc].to_numpy(float)
    g1=gens[0]
    s3=pd.read_parquet(base+'__surrogate.parquet')
    on=s3[(s3.regime=='online')&(s3.geracao==1)]
    k=g1['pop_por_w'][-1]; last=on.iloc[-k:]
    muc=[f'mu_{j}' for j in range(M)]
    PopObj=last[muc].to_numpy(float)
    V=V0*(PopObj.max(0)-PopObj.min(0))[None,:]
    # New: X dos selecionados -> ①
    xs3=[c for c in s3.columns if c.startswith('x') and c[1:].isdigit()]
    Xsel=last.iloc[[int(i)-1 for i in g1['index']]][xs3].to_numpy(np.float32)
    key={tuple(np.float32(v)):i for i,v in enumerate(real[xc].to_numpy(np.float32))}
    idxs=[key.get(tuple(x)) for x in Xsel]
    r['new_encontrados']=sum(1 for i in idxs if i is not None)
    NewObj=real.iloc[[i for i in idxs if i is not None]][fc].to_numpy(float)
    NewDec=real.iloc[[i for i in idxs if i is not None]][xc].to_numpy(np.float32)
    # active de New contra V (adaptado)
    _,active=noactive(NewObj,V)
    Vi=np.delete(V,active,axis=0)
    # Total = A1 \ New
    newset={tuple(x) for x in NewDec}
    mask=np.array([tuple(np.float32(x)) not in newset for x in A1Dec])
    TotalObj=A1Obj[mask]
    P=TotalObj-TotalObj.min(0,keepdims=True)
    assoc=angles(P,Vi).argmin(1)
    nvia=len(np.unique(assoc))
    r['ciclo1_len_Total']=int(mask.sum()); r['ciclo1_size_Vi']=len(Vi)
    r['ciclo1_size_Via']=int(nvia)
    r['ciclo1_ramo']='(a) BUG' if nvia>NI-mu else '(b) ok'
    res.append(r)
df=pd.DataFrame(res); df.to_csv('vdb3_forense.csv',index=False)
pd.set_option('display.width',220)
print(df.to_string(index=False))
