import json
import numpy as np, pandas as pd
from math import comb
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); on=sur[sur.regime=='online']
real=pd.read_parquet(B+'__real.parquet')
N,M=100,2
def uniformpoint(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.arange(1,H1+M).reshape(-1,1)-1.0
    W=np.hstack([W,np.full((len(W),1),float(H1))])-np.hstack([np.zeros((len(W),1)),W]); W=W/H1
    return np.maximum(W,1e-6)
V0=uniformpoint(N,M)
def cosang(A,Bm):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300)
    Bn=Bm/np.maximum(np.linalg.norm(Bm,axis=1,keepdims=True),1e-300)
    return np.arccos(np.clip(An@Bn.T,-1,1))
def noactive(P,V):
    Q=P-P.min(axis=0,keepdims=True); A=cosang(Q,V); a=A.argmin(axis=1)
    u=np.unique(a); return V.shape[0]-len(u),u,a
passo=2; alpha=2
def apd_recompute(last_mu,V,theta):
    P=last_mu; nva,va,_=noactive(P,V); Va=V[va,:]
    Ps=P-P.min(axis=0,keepdims=True)
    cs=cosang(Va,Va); np.fill_diagonal(cs,np.arccos(0.0)); gamma=cs.min(axis=1)
    Ang=cosang(Ps,Va); assoc=Ang.argmin(axis=1)
    APD=np.ones(len(Ps)); nrm=np.sqrt((Ps**2).sum(axis=1))
    for i in np.unique(assoc):
        cur=np.where(assoc==i)[0]; APD[cur]=(1+M*theta*Ang[cur,i]/gamma[i])*nrm[cur]
    return APD
print('=== CONTROLE do recomputo do APD (a identidade DISCRIMINA?) ===')
variants={'theta=(21/20)^2 + V adaptada (declarado)':None,
          'theta=1.0 (sem penalidade crescente)':'th1',
          'theta=(20/20)^2=1':'th1b',
          'theta=(21/20)^1':'th_alpha1',
          'V0 SEM adaptacao':'v0'}
res={k:[] for k in variants}
for r in gens:
    blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']; off=0; faixa_last=None; last=None
    for w,nw in enumerate(ppw,start=1):
        sub=blk.iloc[off:off+nw]; off+=nw
        if w%passo==0:
            P=sub[['mu_0','mu_1']].values.astype(np.float64); faixa_last=P.max(axis=0)-P.min(axis=0)
        if w==len(ppw): last=sub
    mu=last[['mu_0','mu_1']].values.astype(np.float64)
    Vad=V0*faixa_last[None,:]
    exp=np.array(r['apd_sel']); idx=np.array(r['index'])-1
    for k,tag in variants.items():
        if tag=='v0': A=apd_recompute(mu,V0,(21/20)**2)
        elif tag=='th1' or tag=='th1b': A=apd_recompute(mu,Vad,1.0)
        elif tag=='th_alpha1': A=apd_recompute(mu,Vad,(21/20)**1)
        else: A=apd_recompute(mu,Vad,(21/20)**2)
        res[k].append((np.abs(A[idx]-exp)/np.maximum(np.abs(exp),1e-300)).max())
for k,v in res.items(): print('  %-42s max erro rel = %.3e' % (k, max(v)))

print('\n=== KEnvironmentalSelection: 1 solucao por vetor ATIVO (estrutura do RVEA) ===')
tot=0; ok=0
for r in gens:
    blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']; off=0; V=V0.copy()
    for w,nw in enumerate(ppw,start=1):
        sub=blk.iloc[off:off+nw]; off+=nw
        P=sub[['mu_0','mu_1']].values.astype(np.float64)
        _,u,a=noactive(P,V)     # V vigente NO momento da selecao da geracao w
        tot+=1; ok+= (len(np.unique(a))==nw)
        if w%passo==0: V=V0*(P.max(axis=0)-P.min(axis=0))[None,:]
print('  sub-populacoes com |unique(associate)| == |pop_w| (1 por vetor):', ok,'/',tot)

print('\n=== VD-b3: discriminacao do ramo do UpdataArchive (ciclo 1, onde A1 e CONHECIDO) ===')
NI=21; mu_=5
A1obj=real[real.fase=='init'][['f0','f1']].values.astype(np.float64)
A1dec=real[real.fase=='init'][['x0','x1']].values.astype(np.float64)
r=gens[0]
blk=on[on.geracao==1]; ppw=r['pop_por_w']; off=0; faixa_last=None
for w,nw in enumerate(ppw,start=1):
    sub=blk.iloc[off:off+nw]; off+=nw
    if w%passo==0:
        P=sub[['mu_0','mu_1']].values.astype(np.float64); faixa_last=P.max(axis=0)-P.min(axis=0)
V=V0*faixa_last[None,:]
new=real[(real.fe_index>=21)&(real.fe_index<r['fe'])]
Newobj=new[['f0','f1']].values.astype(np.float64); Newdec=new[['x0','x1']].values.astype(np.float64)
print('  |New| =',len(new),' fe_index',list(new.fe_index.values))
_,active,_=noactive(Newobj,V)
Vi=np.delete(V,active,axis=0)
print('  |active(New,V)| =',len(active),'  |Vi| =',len(Vi))
Tot=A1obj  # Total apos remover os New (ciclo 1: A1 = DoE, disjunto dos New)
P=Tot-Tot.min(axis=0,keepdims=True)
Ang=cosang(P,Vi); assoc=Ang.argmin(axis=1); Via=np.unique(assoc)
print('  |Total| =',len(Tot),'  size(Via,1) =',len(Via),'   NI-mu =',NI-mu_)
print('  RAMO =', '(a) kmeans(Via, NI-mu)  <-- o ramo COM o bug de indice' if len(Via)>NI-mu_ else '(b) kmeans(Total.objs, NI-mu)  <-- o ramo ~ Alg.4 do paper')
