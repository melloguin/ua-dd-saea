import json
import numpy as np, pandas as pd
from math import comb
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
R42='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42/exp_main_b3_MMF1_42'
G6='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b3/exp_main_b3_MMF1_42'
a=pd.read_parquet(SM+'__real.parquet'); b=pd.read_parquet(R42+'__real.parquet'); c=pd.read_parquet(G6+'__real.parquet')
cols=['x0','x1','f0','f1']
print('=== (1) smoke x rodada-42 (mesma celula, mesma semente) ===')
eq=(a[cols].values==b[cols].values).all(axis=1)
print('  linhas bit-identicas em float32:',int(eq.sum()),'/',len(a),'  primeira divergente:', None if eq.all() else int(np.where(~eq)[0][0]))
print('  fe_index divergentes:',list(a.fe_index.values[~eq]))
print('  smoke linha 60:',a.iloc[60][cols].to_dict()); print('  r42   linha 60:',b.iloc[60][cols].to_dict())
print('=== (1) smoke x g6_com ===')
print('  bit-identicas:',int((a[cols].values==c[cols].values).all(axis=1).sum()),'/',len(a))
print()
print('=== robustez da discriminacao do ramo do UpdataArchive (|Via| vs NI-mu=16) ===')
recs=[json.loads(l) for l in open(SM+'.jsonl')]; gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(SM+'__surrogate.parquet'); on=sur[sur.regime=='online']
N,M=100,2
def up(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.arange(1,H1+M).reshape(-1,1)-1.0
    W=np.hstack([W,np.full((len(W),1),float(H1))])-np.hstack([np.zeros((len(W),1)),W]); return np.maximum(W/H1,1e-6)
V0=up(N,M)
def ca(A,Bm):
    An=A/np.maximum(np.linalg.norm(A,axis=1,keepdims=True),1e-300); Bn=Bm/np.maximum(np.linalg.norm(Bm,axis=1,keepdims=True),1e-300)
    return np.arccos(np.clip(An@Bn.T,-1,1))
r=gens[0]; blk=on[on.geracao==1]; ppw=r['pop_por_w']; off=0; fl=None
for w,nw in enumerate(ppw,start=1):
    sub=blk.iloc[off:off+nw]; off+=nw
    if w%2==0:
        P=sub[['mu_0','mu_1']].values.astype(np.float64); fl=P.max(axis=0)-P.min(axis=0)
A1=a[a.fase=='init'][['f0','f1']].values.astype(np.float64)
New=a[(a.fe_index>=21)&(a.fe_index<26)][['f0','f1']].values.astype(np.float64)
for pert in [0,1e-6,1e-4,1e-2,5e-2]:
    for sgn in ([1] if pert==0 else [1,-1]):
        f=fl*(1+sgn*pert); V=V0*f[None,:]
        Q=New-New.min(axis=0,keepdims=True); act=np.unique(ca(Q,V).argmin(axis=1))
        Vi=np.delete(V,act,axis=0)
        P2=A1-A1.min(axis=0,keepdims=True); via=len(np.unique(ca(P2,Vi).argmin(axis=1)))
        print('  faixa*(1%+.0e): |active|=%d |Via|=%2d -> ramo %s'%(sgn*pert,len(act),via,'(a)' if via>16 else '(b)'))
