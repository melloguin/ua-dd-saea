"""Os 200 residuos nao-zero sao os ciclos MAL-CONDICIONADOS? (mldivide sem ridge)"""
import sys, os, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT
out=[]
for pb in ['DTLZ2','DTLZ4','DTLZ7','MMF1','MMF16_20','ZDT4','ZDT3','DTLZ3']:
    man,ev,real,pop,sur,tim=load(pb)
    D=len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])
    M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    fsc=[f'f{i}' for i in range(M)]; mus=[f'mu_{i}' for i in range(M)]; xs=[f'x{i}' for i in range(D)]
    so=sur[sur.regime=='online']
    m=so[so.real_solution_id.notna()].copy(); m['sid']=m.real_solution_id.astype(int)
    fei=dict(zip(real.solution_id,real.fe_index)); m['fep']=m.sid.map(fei)
    ins=m[m.fep<=m.fe_treino_max].copy()
    if not len(ins): continue
    fr=real.set_index('solution_id')[fsc]
    e=np.abs(ins[mus].values-fr.loc[ins.sid][fsc].values).max(axis=1)
    ins['err']=e
    per=ins.groupby(ins.geracao.astype(int)).err.max()
    rc={}
    for g in per.index:
        ftm=int(so[so.geracao==g].fe_treino_max.iloc[0])
        X=real[real.fe_index<=ftm][xs].values.astype(np.float64)
        Phi=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1)+1.0)
        rc[g]=1.0/np.linalg.cond(Phi)
    z=[rc[g] for g in per.index if per[g]==0]; nz=[rc[g] for g in per.index if per[g]>0]
    out.append(dict(pb=pb,n_ger=len(per),ger_zero=len(z),ger_naozero=len(nz),
        rcond_med_zero=float(np.median(z)) if z else np.nan,
        rcond_med_naozero=float(np.median(nz)) if nz else np.nan,
        rcond_min_naozero=float(np.min(nz)) if nz else np.nan,
        err_max=float(per.max())))
df=pd.DataFrame(out); print(df.to_string())
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t08_rcond_residuo.csv',index=False)
zz=df.rcond_med_zero.dropna(); nn=df.rcond_med_naozero.dropna()
print()
print('1/cond mediano das geracoes com residuo ZERO   : %.3g'%np.median(zz))
print('1/cond mediano das geracoes com residuo NAO-ZERO: %.3g'%np.median(nn))
