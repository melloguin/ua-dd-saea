"""Robustez do veredito do ciclo 1: perturbacao relativa da faixa (V=V0*faixa)
e dos objetivos, dentro/acima do ruido de armazenamento float32 (~1e-7)."""
import json, itertools, numpy as np, pandas as pd
from math import comb
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
def up(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.array(list(itertools.combinations(range(1,H1+M),M-1)),dtype=float)
    W=W-np.arange(0,M-1)[None,:]-1
    W=(np.hstack([W,np.full((len(W),1),H1)])-np.hstack([np.zeros((len(W),1)),W]))/H1
    return np.maximum(W,1e-6)
def ang(A,B):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300)
    Bn=B/np.maximum(np.linalg.norm(B,axis=1,keepdims=True),1e-300)
    return np.arccos(np.clip(An@Bn.T,-1,1))
rng=np.random.default_rng(3)
for prob,D,M,Nreq in [('MMF1',2,2,100),('MMF4',2,2,100),('MMF11_L',2,2,100),('DTLZ1',7,3,91)]:
    base=f'{ROOT}/{prob}/42/exp_main_b3_{prob}_42'
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    g=[x for x in L if x.get('rec')=='b3_gen'][0]
    NI=11*D-1; V0=up(Nreq,M)
    real=pd.read_parquet(base+'__real.parquet')
    fc=[f'f{j}' for j in range(M)]; xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    F=real[fc].to_numpy(float); X32=real[xc].to_numpy(np.float32)
    key={tuple(v):i for i,v in enumerate(X32)}
    s3=pd.read_parquet(base+'__surrogate.parquet'); s3=s3[(s3.regime=='online')&(s3.geracao==1)]
    k=g['pop_por_w'][-1]; last=s3.iloc[-k:]
    xs3=[c for c in s3.columns if c.startswith('x') and c[1:].isdigit()]
    P0=last[[f'mu_{j}' for j in range(M)]].to_numpy(float)
    faixa=P0.max(0)-P0.min(0)
    ids=[key.get(tuple(x)) for x in last.iloc[[int(i)-1 for i in g['index']]][xs3].to_numpy(np.float32)]
    ids=[i for i in ids if i is not None]
    res={}
    for eps in [0.0,1e-7,1e-5,1e-3,1e-2,5e-2]:
        cnt=[]
        for t in range(40 if eps>0 else 1):
            f=faixa*(1+eps*rng.standard_normal(M))
            V=V0*f[None,:]
            NewObj=F[ids]; P=NewObj-NewObj.min(0,keepdims=True)
            Vi=np.delete(V,np.unique(ang(P,V).argmin(1)),axis=0)
            sel=np.array([i for i in range(NI) if i not in ids])
            T=F[sel]; Pt=T-T.min(0,keepdims=True)
            cnt.append(len(np.unique(ang(Pt,Vi).argmin(1))))
        res[eps]=(min(cnt),max(cnt))
    print(prob,'limiar NI-mu =',NI-5,' size(Via) por eps:',{f'{e:g}':v for e,v in res.items()})
