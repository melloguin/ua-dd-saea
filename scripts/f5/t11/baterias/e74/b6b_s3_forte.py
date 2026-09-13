# -*- coding: utf-8 -*- READ-ONLY. A11 v2: reconstrucao FIEL ao Local_infill.m
#  RefPoint = argmax CrowdingDistance(front1) COM inf->0 ; y_treino = N (n_treino) vizinhos em OBJETIVOS
import json
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
def front_mask(F):
    n=len(F); dom=np.zeros(n,bool)
    for i in range(n):
        le=(F<=F[i]).all(axis=1); lt=(F<F[i]).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return ~dom
def crowd(F):
    n,m=F.shape; d=np.zeros(n)
    for j in range(m):
        o=np.argsort(F[:,j],kind='stable'); d[o[0]]=d[o[-1]]=np.inf
        rng=F[o[-1],j]-F[o[0],j]
        if rng>0 and n>2: d[o[1:-1]]+= (F[o[2:],j]-F[o[:-2],j])/rng
    return d
def run(prob, base, tag):
    real=pd.read_parquet(base+'__real.parquet')
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    fc=[c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    M=len(fc)
    sur=pd.read_parquet(base+'__surrogate.parquet',columns=['regime','geracao','modelo_flag','sigma_0']+xc+[f'mu_{i}' for i in range(M)])
    s3=sur[(sur.regime=='online')&(sur.modelo_flag=='RBF-local(s3)')]
    blk={int(g):b for g,b in s3.groupby('geracao')}
    Xr=real[xc].values.astype(np.float64); Fr=real[fc].values.astype(np.float64)
    ok=tot=inside=nf=0
    for r in (json.loads(l) for l in open(base+'.jsonl')):
        if r.get('rec')!='e74_gen' or r.get('estrategia')!=3 or r.get('aceito')!=1: continue
        b=blk.get(int(r['geracao']))
        if b is None: continue
        nA=r['arquivo']-r['aceito']; FA=Fr[:nA]
        m1=front_mask(FA); idx1=np.where(m1)[0]
        cd=crowd(FA[idx1]); cd=np.where(np.isinf(cd),0.0,cd)     # <- inf->0 (Local_infill.m:15)
        ref=idx1[int(np.argmax(cd))]
        N=int(r['n_treino'])
        d=np.linalg.norm(FA-FA[ref],axis=1); nb=np.argsort(d,kind='stable')[:N]
        ytr=FA[nb]
        mu=b[[f'mu_{i}' for i in range(M)]].values.astype(np.float64)
        f1=front_mask(np.vstack([ytr,mu]))[len(ytr):]
        s0=b.sigma_0.values.astype(np.float64)
        pos=int(np.argmin(np.abs(b[xc].values.astype(np.float64)-Xr[r['fe']-1]).max(axis=1)))
        mem=np.where(f1)[0]; tot+=1; nf+= int(len(mem)==r['n_front'])
        if len(mem):
            ok+= int(pos==mem[int(np.argmax(s0[mem]))]); inside+= int(pos in mem)
    print('%-10s %-8s FORTE %d/%d = %.2f%% | dentro %d/%d | n_front bate %d/%d'%(tag,prob,ok,tot,100*ok/tot if tot else np.nan,inside,tot,nf,tot))
    return np.array([ok,tot,inside,nf])
for tag,pat in [('POS_smoke',f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_%s_42'),
                ('PRE_s42',  f'{ROOT}/resultados_experimentos/e74/%s/42/exp_main_e74_%s_42')]:
    T=np.zeros(4,int)
    for p in ['MMF1','DTLZ2','ZDT1']:
        base=pat%p if tag=='POS_smoke' else pat%(p,p)
        T+=run(p,base,tag)
    print('  >> %s TOTAL %d/%d = %.2f%% | dentro %d | n_front %d\n'%(tag,T[0],T[1],100*T[0]/T[1],T[2],T[3]))
