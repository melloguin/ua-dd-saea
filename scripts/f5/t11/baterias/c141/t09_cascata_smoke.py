"""A CASCATA do MMRAEA reconstruida do ZERO no dado POS-T11 (smoke MMF1, 10 ciclos).
Mesmas identidades J1-J7 da F5, agora sobre o codigo de HOJE."""
import sys, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import rbf_fit, rbf_pred, front1, sde, nd_levels
K='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42'
man=json.load(open(K+'.manifest.json')); ev=[json.loads(l) for l in open(K+'.jsonl') if l.strip()]
real=pd.read_parquet(K+'__real.parquet'); sur=pd.read_parquet(K+'__surrogate.parquet')
gen=[e for e in ev if e['rec']=='c141_gen']; so=sur[sur.regime=='online']
xs=['x0','x1']; fs=['f0','f1']; mus=['mu_0','mu_1']
res=[]
for g in gen:
    gg=g['geracao']; sub=so[so.geracao==gg]
    ftm=int(sub.fe_treino_max.iloc[0])
    tr=real[real.fe_index<=ftm]
    X=tr[xs].values.astype(np.float64); Y=tr[fs].values.astype(np.float64)
    A=Y                                       # arquivo VERDADEIRO
    W=rbf_fit(X,Y)
    P=sub[xs].values.astype(np.float64)
    MUlog=sub[mus].values.astype(np.float64)
    MUrec=rbf_pred(P,X,W)
    # J1 kernel
    err_mu=np.median(np.abs(MUrec-MUlog))/max(np.abs(MUlog).mean(),1e-12)
    # J2 nivel1 com arquivo VERDADEIRO x PREDITO
    def n1(Arch):
        U=np.vstack([MUlog,Arch]); f1=front1(U); return int((f1<len(MUlog)).sum()), f1[f1<len(MUlog)]
    nv, idxv = n1(A)
    npd,_    = n1(rbf_pred(X,X,W))
    # J3 Fit1 (SDE) sobre o conjunto P do nivel 1 (hipotese arquivo verdadeiro)
    fit1max=np.nan
    if len(idxv)>1:
        fit1max=float(np.nanmax(sde(MUlog[idxv])))
    # J4 sigma_0 = U de ranks do pool ; teto 2(2N-1)
    N=man['params']['N_subpop']
    res.append(dict(g=gg,n_treino=len(X),n_pool=len(sub),
        n1_log=g['n_front1'],n1_verdadeiro=nv,n1_predito=npd,
        ok_v=int(nv==g['n_front1']),ok_p=int(npd==g['n_front1']),
        fit1max_log=g['fit1']['max'],fit1max_rec=fit1max,
        rel_fit1=abs(fit1max-g['fit1']['max'])/max(abs(g['fit1']['max']),1e-30) if fit1max==fit1max else np.nan,
        erro_mu_rel=err_mu,
        Upool_log=g['U_pool_max'],s0max=float(sub.sigma_0.max()),teto=2*(2*N-1),
        lote=g['lote'],nivel=g['nivel'],n_front2=g['n_front2'],
        rcond=1.0/np.linalg.cond(np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1)+1.0))))
df=pd.DataFrame(res)
pd.set_option('display.width',250)
print(df.to_string())
print()
print('J1 kernel MQ c=1 poly=0 sem scaling: erro relativo mediano por ciclo  min %.2g  mediana %.2g  max %.2g'%(df.erro_mu_rel.min(),df.erro_mu_rel.median(),df.erro_mu_rel.max()))
print('J2 nivel1: arquivo VERDADEIRO acerta %d/%d ; arquivo PREDITO acerta %d/%d'%(df.ok_v.sum(),len(df),df.ok_p.sum(),len(df)))
print('J3 Fit1(SDE) max: erro relativo mediano %.3g ; <1e-5 em %d/%d'%(df.rel_fit1.median(),int((df.rel_fit1<1e-5).sum()),int(df.rel_fit1.notna().sum())))
print('J4 sigma_0: max por ciclo <= teto %d em %d/%d ; U_pool_max(⑥)==max(sigma_0)(③) em %d/%d'%(
    df.teto.iloc[0],int((df.s0max<=df.teto).sum()),len(df),int((df.Upool_log==df.s0max).sum()),len(df)))
print('   sigma_0 max da CELULA = %d (teto = %d)'%(so.sigma_0.max(),df.teto.iloc[0]))
print('J5 cascata: niveis',df.nivel.value_counts().to_dict(),' lote total',int(df.lote.sum()),' + init %d + lote_final = %d'%(21,man['fe_final']))
print('J6 rcond: min %.3g ; ciclos < 1e-12: %d/%d'%(df.rcond.min(),int((df.rcond<1e-12).sum()),len(df)))
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t09_cascata_smoke.csv',index=False)
