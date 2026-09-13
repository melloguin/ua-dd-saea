# -*- coding: utf-8 -*- READ-ONLY. Quanto da eq.7-8 se realiza: razao dist_escolhido/dist_max do bloco + residuo.
import sys, json, glob
import numpy as np, pandas as pd
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e74'
ROOT='/Users/gmello/Documents/python_repos/mestrado'
def cells(c):
    if c=='s42':
        for d in sorted(glob.glob(f'{ROOT}/resultados_experimentos/e74/*/42')):
            p=d.split('/')[-2]; yield p, f'{d}/exp_main_e74_{p}_42'
    else:
        for p in ['MMF1','DTLZ2','ZDT1']:
            yield p, f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{p}_42'
def run(corpus):
    R=[]
    for prob,base in cells(corpus):
        real=pd.read_parquet(base+'__real.parquet')
        xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
        sur=pd.read_parquet(base+'__surrogate.parquet',columns=['regime','geracao','modelo_flag','pred_classe','sigma_0']+xc)
        sur=sur[(sur.regime=='online')&(sur.modelo_flag=='PNN(s1)')]
        blocks={int(g):b for g,b in sur.groupby('geracao')}
        Xr=real[xc].values.astype(np.float64)
        for r in (json.loads(l) for l in open(base+'.jsonl')):
            if r.get('rec')!='e74_gen' or r.get('estrategia')!=1 or r.get('aceito')!=1: continue
            b=blocks[int(r['geracao'])]
            s0=b['sigma_0'].values.astype(np.float64); cls=(b['pred_classe'].values=='nivel_1')
            Xb=b[xc].values.astype(np.float64)
            pos=int(np.argmin(np.abs(Xb-Xr[r['fe']-1]).max(axis=1)))
            S=np.where(cls)[0]
            maxS=s0[S].max() if len(S) else np.nan
            R.append(dict(corpus=corpus,problema=prob,ger=int(r['geracao']),n_desal=r['n_desalinhado'],
                razao_global=s0[pos]/s0.max() if s0.max()>0 else np.nan,
                razao_S=s0[pos]/maxS if maxS and maxS>0 else np.nan,
                argmaxS=int(len(S)>0 and pos==S[np.argmax(s0[S])]),
                argmax_g=int(pos==int(np.argmax(s0))), dist=s0[pos], dmax=s0.max()))
    return pd.DataFrame(R)
a=run('s42'); b=run('smoke')
pd.concat([a,b]).to_csv(f'{OUT}/eq78_razao.csv',index=False)
for nome,d in [('PRE s42 (25 cel)',a),('POS smoke (3 cel)',b)]:
    print('%-20s n=%4d  razao_global mediana %.4f (media %.4f, p10 %.3f)  razao_S mediana %.4f  argmax_S %.2f%%'%(
        nome,len(d),d.razao_global.median(),d.razao_global.mean(),d.razao_global.quantile(.1),d.razao_S.median(),100*d.argmaxS.mean()))
# residuo pos-fix: onde argmax_S falha, e por causa do 2o desalinhamento?
f=b[b.argmaxS==0]
print('\nPOS-fix: %d/%d falhas de argmax_S; n_desalinhado nessas: min %d mediana %.0f max %d'%(len(f),len(b),f.n_desal.min(),f.n_desal.median(),f.n_desal.max()))
print('POS-fix: blocos com n_desal==0: %d, argmax_S = %.2f%%'%((b.n_desal==0).sum(),100*b[b.n_desal==0].argmaxS.mean()))
print('POS-fix: blocos com n_desal>0 : %d, argmax_S = %.2f%%'%((b.n_desal>0).sum(),100*b[b.n_desal>0].argmaxS.mean()))
print('PRE : blocos com n_desal==0: %d, argmax_S = %.2f%%'%((a.n_desal==0).sum(),100*a[a.n_desal==0].argmaxS.mean()))
# so as 3 celulas comuns, PRE
a3=a[a.problema.isin(['MMF1','DTLZ2','ZDT1'])]
print('\nPRE nas MESMAS 3 celulas: n=%d razao_global mediana %.4f argmax_S %.2f%%'%(len(a3),a3.razao_global.median(),100*a3.argmaxS.mean()))
print('POS nas 3 celulas       : n=%d razao_global mediana %.4f argmax_S %.2f%%'%(len(b),b.razao_global.median(),100*b.argmaxS.mean()))
print('\npor celula (razao_global mediana):')
print(pd.concat([a3.assign(k='PRE'),b.assign(k='POS')]).groupby(['problema','k']).razao_global.median().to_string())
