"""F2 — interpolacao exata: quantas das 9.084 linhas in-sample tem erro EXATAMENTE 0?"""
import sys, os, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT
tot=0; zero=0; rows=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim=load(pb)
    D=len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])
    M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    fsc=[f'f{i}' for i in range(M)]; mus=[f'mu_{i}' for i in range(M)]
    so=sur[sur.regime=='online']
    m=so[so.real_solution_id.notna()].copy(); m['sid']=m.real_solution_id.astype(int)
    fei=dict(zip(real.solution_id,real.fe_index)); m['fep']=m.sid.map(fei)
    ins=m[m.fep<=m.fe_treino_max]
    if not len(ins): rows.append((pb,0,0,np.nan,np.nan)); continue
    fr=real.set_index('solution_id')[fsc]
    e=np.abs(ins[mus].values-fr.loc[ins.sid][fsc].values)
    z=int((e.max(axis=1)==0).sum())
    # os nao-zero: sao ciclos com dsmerge (modelo_hp.n != |① <= ftm|)?
    hpn={g['geracao']:g['modelo_hp']['n'] for g in ev if g['rec']=='c141_gen'}
    nao=ins[(e.max(axis=1)>0)]
    dsm=0
    for gg in nao.geracao.dropna().astype(int).unique():
        ftm=int(so[so.geracao==gg].fe_treino_max.iloc[0])
        if hpn.get(gg) != int((real.fe_index<=ftm).sum()): dsm+=1
    rows.append((pb,len(ins),z,float(e.max()),f'{len(nao.geracao.dropna().astype(int).unique())} ger nao-zero, {dsm} com modelo_hp.n != |①<=ftm|'))
    tot+=len(ins); zero+=z
df=pd.DataFrame(rows,columns=['pb','n_insample','erro_zero','erro_max','diag'])
print(df.to_string())
print()
print('TOTAL in-sample %d ; com |mu-f| EXATAMENTE 0: %d (%.2f%%) ; nao-zero: %d'%(tot,zero,100*zero/tot,tot-zero))
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t07_interpolacao.csv',index=False)

# --- adendo: os 200 residuos nao-zero, em ULP-float32 da propria magnitude ---
print(); print('=== os 200 nao-zero em ULP-float32 ===')
acc=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim=load(pb)
    M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    fsc=[f'f{i}' for i in range(M)]; mus=[f'mu_{i}' for i in range(M)]
    so=sur[sur.regime=='online']
    m=so[so.real_solution_id.notna()].copy()
    if not len(m): continue
    m['sid']=m.real_solution_id.astype(int)
    fei=dict(zip(real.solution_id,real.fe_index)); m['fep']=m.sid.map(fei)
    ins=m[m.fep<=m.fe_treino_max]
    if not len(ins): continue
    fr=real.set_index('solution_id')[fsc]
    F=fr.loc[ins.sid][fsc].values.astype(np.float64); MU=ins[mus].values.astype(np.float64)
    e=np.abs(MU-F); nz=e>0
    if nz.any():
        ulp=np.spacing(np.abs(F).astype(np.float32)).astype(np.float64)
        acc.append(pd.DataFrame(dict(pb=pb,err=e[nz],f=np.abs(F)[nz],ulp=ulp[nz])))
A=pd.concat(acc)
A['em_ulp']=A.err/A.ulp
print(' n=%d ; |f| mediana %.3g ; erro mediano %.3g ; erro/ULP-float32: mediana %.2f p95 %.2f max %.2f'%(
    len(A),A.f.median(),A.err.median(),A.em_ulp.median(),A.em_ulp.quantile(.95),A.em_ulp.max()))
print(' fracao com erro <= 2 ULP-float32: %.3f ; <= 8 ULP: %.3f'%((A.em_ulp<=2).mean(),(A.em_ulp<=8).mean()))
print(A.groupby('pb').agg(n=('err','size'),err_max=('err','max'),ulp_max=('em_ulp','max')).to_string())
