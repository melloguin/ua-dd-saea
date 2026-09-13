import sys, os
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT
acc=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim=load(pb)
    M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    fsc=[f'f{i}' for i in range(M)]; mus=[f'mu_{i}' for i in range(M)]
    escala=np.abs(real[fsc].values.astype(np.float64)).max()      # escala da celula
    so=sur[sur.regime=='online']; m=so[so.real_solution_id.notna()].copy()
    if not len(m): continue
    m['sid']=m.real_solution_id.astype(int)
    fei=dict(zip(real.solution_id,real.fe_index)); m['fep']=m.sid.map(fei)
    ins=m[m.fep<=m.fe_treino_max]
    if not len(ins): continue
    fr=real.set_index('solution_id')[fsc]
    F=fr.loc[ins.sid][fsc].values.astype(np.float64); MU=ins[mus].values.astype(np.float64)
    e=np.abs(MU-F).ravel(); f=np.abs(F).ravel()
    acc.append(pd.DataFrame(dict(pb=pb,err=e,f=f,escala=escala)))
A=pd.concat(acc); A['rel']=A.err/A.escala
print('pares (linha,objetivo) in-sample: %d'%len(A))
print('  erro EXATAMENTE 0        : %d (%.3f%%)'%((A.err==0).sum(),100*(A.err==0).mean()))
NZ=A[A.err>0]
print('  nao-zero                 : %d'%len(NZ))
print('   |f| do ponto == 0.0 exato em %d deles (%.1f%%)'%((NZ.f==0).sum(),100*(NZ.f==0).mean()))
print('   erro/escala-da-celula: mediana %.3g  p95 %.3g  MAXIMO %.3g'%(NZ.rel.median(),NZ.rel.quantile(.95),NZ.rel.max()))
print('   fracao com erro/escala <= 1,19e-7 (eps-float32): %.4f'%(NZ.rel<=1.1920929e-7).mean())
print(NZ.groupby('pb').agg(n=('err','size'),rel_max=('rel','max'),escala=('escala','first')).to_string())
A.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t07b_residuo_relativo.csv',index=False)
