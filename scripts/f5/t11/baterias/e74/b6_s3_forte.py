# -*- coding: utf-8 -*- READ-ONLY. A11: identidade FORTE da s3 (argmax do Eucli RESTRITO ao front do NDSort([y_treino; mu_off]))
import json, sys
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT=f'{ROOT}/ua-dd-saea/f5/t11/baterias/e74'
def front1(F):
    n=len(F); dom=np.zeros(n,bool)
    for i in range(n):
        if dom[i]: continue
        le=(F<=F[i]).all(axis=1); lt=(F<F[i]).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return ~dom
def crowd(F):
    n,m=F.shape; d=np.zeros(n)
    for j in range(m):
        o=np.argsort(F[:,j]); d[o[0]]=d[o[-1]]=np.inf
        rng=F[o[-1],j]-F[o[0],j]
        if rng>0: d[o[1:-1]]+= (F[o[2:],j]-F[o[:-2],j])/rng
    return d
def run(prob, base, tag):
    real=pd.read_parquet(base+'__real.parquet')
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    fc=[c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    sur=pd.read_parquet(base+'__surrogate.parquet',
        columns=['regime','geracao','modelo_flag','sigma_0']+xc+[f'mu_{i}' for i in range(len(fc))])
    s3=sur[(sur.regime=='online')&(sur.modelo_flag=='RBF-local(s3)')]
    blk={int(g):b for g,b in s3.groupby('geracao')}
    Xr=real[xc].values.astype(np.float64); Fr=real[fc].values.astype(np.float64)
    ok=tot=inside=0; nf_ok=0
    for r in (json.loads(l) for l in open(base+'.jsonl')):
        if r.get('rec')!='e74_gen' or r.get('estrategia')!=3 or r.get('aceito')!=1: continue
        b=blk.get(int(r['geracao']))
        if b is None: continue
        nA=r['arquivo']-r['aceito']            # arquivo PRE-FE
        FA=Fr[:nA]
        m1=front1(FA); idx1=np.where(m1)[0]
        cd=crowd(FA[idx1]); ref=idx1[int(np.argmax(cd))]
        k=int(r['k_local_efetivo'])
        dd=np.linalg.norm(FA-FA[ref],axis=1); nb=np.argsort(dd,kind='stable')[:k]
        ytr=FA[nb]
        mu=b[[f'mu_{i}' for i in range(len(fc))]].values.astype(np.float64)
        allF=np.vstack([ytr,mu]); f1=front1(allF)[len(ytr):]
        s0=b.sigma_0.values.astype(np.float64)
        pos=int(np.argmin(np.abs(b[xc].values.astype(np.float64)-Xr[r['fe']-1]).max(axis=1)))
        mem=np.where(f1)[0]; tot+=1
        if len(mem):
            ok+= int(pos==mem[int(np.argmax(s0[mem]))]); inside+= int(pos in mem)
        nf_ok+= int(len(mem)==r['n_front'])
    print('%-10s %-10s  identidade FORTE %d/%d = %.2f%%  | escolhido DENTRO do front %d/%d | n_front bate %d/%d'%(
        tag,prob,ok,tot,100*ok/tot if tot else np.nan,inside,tot,nf_ok,tot))
    return ok,tot,inside,nf_ok
tot_=[0,0,0,0]
for p in ['MMF1','DTLZ2','ZDT1']:
    a=run(p,f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{p}_42','POS_smoke')
    tot_=[x+y for x,y in zip(tot_,a)]
print('POS_smoke TOTAL: %d/%d = %.2f%% | dentro %d | n_front %d'%(tot_[0],tot_[1],100*tot_[0]/tot_[1],tot_[2],tot_[3]))
tot2=[0,0,0,0]
for p in ['MMF1','DTLZ2','ZDT1']:
    a=run(p,f'{ROOT}/resultados_experimentos/e74/{p}/42/exp_main_e74_{p}_42','PRE_s42')
    tot2=[x+y for x,y in zip(tot2,a)]
print('PRE_s42   TOTAL: %d/%d = %.2f%% | dentro %d | n_front %d'%(tot2[0],tot2[1],100*tot2[0]/tot2[1],tot2[2],tot2[3]))
