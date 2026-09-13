"""Verificacao do campo NOVO `adapt_delta_V` (T11) — recomputo independente a
partir da ③ do smoke, contra o logado no ⑥. src/b3_instrument.m:126-161."""
import json, itertools, numpy as np, pandas as pd
from math import comb
P='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
def up(N,M):
    H1=1
    while comb(H1+M,M-1)<=N: H1+=1
    W=np.array(list(itertools.combinations(range(1,H1+M),M-1)),dtype=float)
    W=W-np.arange(0,M-1)[None,:]-1
    W=(np.hstack([W,np.full((len(W),1),H1)])-np.hstack([np.zeros((len(W),1)),W]))/H1
    return np.maximum(W,1e-6)
L=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
gens=[x for x in L if x.get('rec')=='b3_gen']
V0=up(100,2); M=2
s3=pd.read_parquet(P+'__surrogate.parquet'); on=s3[s3.regime=='online']
print('ciclo | n_logado | max|Δrel| recomputo | 1o dv logado | dv INTER-CICLO (nao logado)')
Vfim=None
for g in gens:
    blk=on[on.geracao==g['geracao']]; ppw=g['pop_por_w']
    ini=0; faixas=[]
    for w,k in enumerate(ppw,start=1):
        sub=blk.iloc[ini:ini+k]; ini+=k
        o=sub[[f'mu_{j}' for j in range(M)]].to_numpy(float)
        if w%2==0: faixas.append((w,o.max(0)-o.min(0)))
    rec=[np.linalg.norm(V0*(faixas[i][1]-faixas[i-1][1])[None,:]) for i in range(1,len(faixas))]
    log=np.array(g['adapt_delta_V'],float)
    rel=np.max(np.abs(np.array(rec)-log)/np.maximum(np.abs(log),1e-12)) if len(log)==len(rec) else float('nan')
    inter=np.linalg.norm(V0*(faixas[0][1]-Vfim)[None,:]) if Vfim is not None else np.nan
    print(f'{g["geracao"]:5d} | {len(log):8d} | {rel:18.3e} | {log[0]:12.5f} | {inter:12.5f}')
    Vfim=faixas[-1][1]
