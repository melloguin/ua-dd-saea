"""VD-b3: exposicao do ramo (a) em TODOS os ciclos das 4 celulas alcancaveis.
Ciclo 1 = EXATO (A1 = DoE). Ciclos >=2: A1 nao e logado -> Monte Carlo sobre
composicoes ADMISSIVEIS de A1 (21 ou 76 pontos de ①[:fe], contendo os 5 ultimos
infills, que sao imunes a poda por construcao do Alg.4/codigo :70)."""
import json, os, itertools, numpy as np, pandas as pd
from math import comb
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
def uniform_point_nbi(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.array(list(itertools.combinations(range(1,H1+M),M-1)),dtype=float)
    W=W-np.arange(0,M-1)[None,:]-1
    W=(np.hstack([W,np.full((len(W),1),H1)])-np.hstack([np.zeros((len(W),1)),W]))/H1
    return np.maximum(W,1e-6),len(W)
def ang(A,B):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300)
    Bn=B/np.maximum(np.linalg.norm(B,axis=1,keepdims=True),1e-300)
    return np.arccos(np.clip(An@Bn.T,-1,1))
rng=np.random.default_rng(7)
rows=[]
for prob,D,M,Nreq in [('MMF1',2,2,100),('MMF4',2,2,100),('MMF11_L',2,2,100),('DTLZ1',7,3,91)]:
    base=f'{ROOT}/{prob}/42/exp_main_b3_{prob}_42'
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    gens=[x for x in L if x.get('rec')=='b3_gen']
    NI=11*D-1; mu=5; V0,N=uniform_point_nbi(Nreq,M)
    real=pd.read_parquet(base+'__real.parquet')
    fc=[f'f{j}' for j in range(M)]; xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    F=real[fc].to_numpy(float); X32=real[xc].to_numpy(np.float32)
    key={tuple(v):i for i,v in enumerate(X32)}
    s3=pd.read_parquet(base+'__surrogate.parquet'); s3=s3[s3.regime=='online']
    xs3=[c for c in s3.columns if c.startswith('x') and c[1:].isdigit()]
    muc=[f'mu_{j}' for j in range(M)]
    fe_prev=NI
    for g in gens:
        blk=s3[s3.geracao==g['geracao']]; k=g['pop_por_w'][-1]; last=blk.iloc[-k:]
        PopObj=last[muc].to_numpy(float)
        V=V0*(PopObj.max(0)-PopObj.min(0))[None,:]
        Xsel=last.iloc[[int(i)-1 for i in g['index']]][xs3].to_numpy(np.float32)
        ids=[key.get(tuple(x)) for x in Xsel]; ids=[i for i in ids if i is not None]
        NewObj=F[ids]
        P=NewObj-NewObj.min(0,keepdims=True)
        active=np.unique(ang(P,V).argmin(1))
        Vi=np.delete(V,active,axis=0)
        pool=np.arange(fe_prev)           # candidatos "velhos" disponiveis ate o inicio do ciclo
        def size_via(sel):
            T=F[sel]; P=T-T.min(0,keepdims=True)
            return len(np.unique(ang(P,Vi).argmin(1)))
        if g['geracao']==1:
            sv=size_via(np.arange(NI)[~np.isin(np.arange(NI),ids)])
            rows.append(dict(problema=prob,ciclo=1,modo='EXATO',size_Via=sv,limiar=NI-mu,
                             ramo_a=sv>NI-mu,frac_ramo_a=float(sv>NI-mu)))
        else:
            svs=[]
            for _ in range(120):
                velhos=[i for i in pool if i not in ids]
                sel=rng.choice(velhos,size=min(NI,len(velhos)),replace=False)
                svs.append(size_via(sel))
            svs=np.array(svs)
            rows.append(dict(problema=prob,ciclo=g['geracao'],modo='MC120',size_Via=float(svs.mean()),
                             limiar=NI-mu,ramo_a=bool((svs>NI-mu).mean()>0.5),
                             frac_ramo_a=float((svs>NI-mu).mean())))
        fe_prev=g['fe']
df=pd.DataFrame(rows); df.to_csv('vdb3_mc.csv',index=False)
pd.set_option('display.width',200)
print(df.to_string(index=False))
print('\n=== resumo por celula ===')
print(df.groupby('problema').agg(ciclos=('ciclo','count'),frac_ramo_a_media=('frac_ramo_a','mean'),
      size_Via_med=('size_Via','mean'),limiar=('limiar','first')).to_string())
