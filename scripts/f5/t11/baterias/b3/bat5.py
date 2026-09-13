import json
import numpy as np, pandas as pd
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); on=sur[sur.regime=='online']
real=pd.read_parquet(B+'__real.parquet')
N,M=100,2
def uniformpoint(N,M):
    assert M==2
    H1=1
    from math import comb
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.arange(1,H1+M).reshape(-1,1)-1.0   # nchoosek(1:H1+M-1,1)-1
    W=np.hstack([W, np.full((len(W),1),float(H1))])-np.hstack([np.zeros((len(W),1)),W])
    W=W/H1
    W=np.maximum(W,1e-6)
    return W
V0=uniformpoint(N,M); print('V0 shape',V0.shape,'linhas',len(V0))
def cosang(A,Bm):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300)
    Bn=Bm/np.maximum(np.linalg.norm(Bm,axis=1,keepdims=True),1e-300)
    c=np.clip(An@Bn.T,-1,1); return np.arccos(c)
def noactive(PopObj,V):
    P=PopObj-PopObj.min(axis=0,keepdims=True)
    A=cosang(P,V); assoc=A.argmin(axis=1)
    act=np.unique(assoc); return V.shape[0]-len(act), act, assoc

print('\n=== NOVO A: recomputo de NumV2 = NoActive(PopObj_final, V0) a partir da (3) ===')
okv2=0
for r in gens:
    blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']; last=blk.iloc[-ppw[-1]:]
    P=last[['mu_0','mu_1']].values.astype(np.float64)
    n2,_,_=noactive(P,V0)
    ok = (n2==r['NumV2']); okv2+=ok
    print('  ciclo %d  NumV2 logado %3d  recomputado %3d  %s'%(r['geracao'],r['NumV2'],n2,'OK' if ok else 'DIF'))
print('  fecha %d/%d'%(okv2,len(gens)))

print('\n=== NOVO B: recomputo de NumV1 = NoActive(A1Obj, V0) — SO no ciclo 1 (A1 = DoE) ===')
doe=real[real.fase=='init'][['f0','f1']].values.astype(np.float64)
n1,_,_=noactive(doe,V0)
print('  ciclo 1: NumV1 logado',gens[0]['NumV1'],' recomputado do DoE',n1, 'OK' if n1==gens[0]['NumV1'] else 'DIF')

print('\n=== NOVO C: adapt_delta_V recomputado da (3) ===')
passo=2
for r in gens:
    blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']
    off=0; faixas=[]
    for w,nw in enumerate(ppw,start=1):
        sub=blk.iloc[off:off+nw]; off+=nw
        if w%passo==0:
            P=sub[['mu_0','mu_1']].values.astype(np.float64)
            faixas.append(P.max(axis=0)-P.min(axis=0))
    dv=[]
    for k in range(1,len(faixas)):
        dV=V0*(faixas[k]-faixas[k-1])[None,:]
        dv.append(np.sqrt((dV**2).sum()))
    lg=r['adapt_delta_V']
    rel=np.abs(np.array(dv)-np.array(lg))/np.maximum(np.abs(np.array(lg)),1e-300)
    print('  ciclo %d  n=%d/%d  max erro relativo %.3e'%(r['geracao'],len(dv),len(lg),rel.max()))

print('\n=== NOVO D: APD recomputado (theta_APD = (21/20)^alpha) ===')
alpha=2
for r in gens:
    blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']
    off=0; faixa_last=None
    for w,nw in enumerate(ppw,start=1):
        sub=blk.iloc[off:off+nw]; off+=nw
        if w%passo==0:
            P=sub[['mu_0','mu_1']].values.astype(np.float64); faixa_last=P.max(axis=0)-P.min(axis=0)
        if w==len(ppw): last=sub
    V=V0*faixa_last[None,:]
    P=last[['mu_0','mu_1']].values.astype(np.float64)
    nva,va,_=noactive(P,V)
    Va=V[va,:]
    Ps=P-P.min(axis=0,keepdims=True)
    cs=cosang(Va,Va); np.fill_diagonal(cs,np.pi/2*0+np.arccos(0.0))  # cosine(eye)=0 -> acos(0)=pi/2
    gamma=cs.min(axis=1)
    Ang=cosang(Ps,Va); assoc=Ang.argmin(axis=1)
    theta=((len(ppw)+1)/len(ppw))**alpha
    APD=np.ones(len(Ps))
    nrm=np.sqrt((Ps**2).sum(axis=1))
    for i in np.unique(assoc):
        cur=np.where(assoc==i)[0]
        APD[cur]=(1+M*theta*Ang[cur,i]/gamma[i])*nrm[cur]
    got=APD[np.array(r['index'])-1]
    exp=np.array(r['apd_sel'])
    rel=np.abs(got-exp)/np.maximum(np.abs(exp),1e-300)
    print('  ciclo %d  NVa=%d |Va|=%d theta=%.6f  max erro rel apd_sel %.3e'%(r['geracao'],nva,len(va),theta,rel.max()))
