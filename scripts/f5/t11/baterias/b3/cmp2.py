import json
import pandas as pd, numpy as np
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
R42='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42/exp_main_b3_MMF1_42'
ma=json.load(open(SM+'.manifest.json')); mb=json.load(open(R42+'.manifest.json'))
print('smoke timing keys', ma['timing'])
print('r42   timing keys', mb['timing'])
print('smoke sonda', {k:v for k,v in ma['sonda'].items()})
print('r42   sonda', {k:v for k,v in mb['sonda'].items()})
print('smoke params', ma['params']); print('r42 params', mb['params'])
print('smoke sigma_dict', ma['sigma_dict']); print('r42 sigma_dict', mb['sigma_dict'])
print('r42 top-level keys - smoke:', sorted(set(mb)-set(ma)), ' smoke - r42:', sorted(set(ma)-set(mb)))
print()
a=[json.loads(l) for l in open(SM+'.jsonl')]; b=[json.loads(l) for l in open(R42+'.jsonl')]
print('smoke guards', [r for r in a if r['rec']=='guard'])
print('r42 guards  ', [r for r in b if r['rec']=='guard'])
print('smoke sonda gen', [r['geracao'] for r in a if r['rec']=='sonda'])
print('r42   sonda gen', [r['geracao'] for r in b if r['rec']=='sonda'])
print()
# 3 online comparison
sa=pd.read_parquet(SM+'__surrogate.parquet'); sb=pd.read_parquet(R42+'__surrogate.parquet')
print('cols', list(sa.columns))
oa=sa[sa.regime=='online'].reset_index(drop=True); ob=sb[sb.regime=='online'].reset_index(drop=True)
print('online rows', len(oa), len(ob))
xc=[c for c in sa.columns if c.startswith('x')]
mc=[c for c in sa.columns if c.startswith('mu')]
sc=[c for c in sa.columns if c.startswith('sigma')]
print('x cols',xc,'mu',mc,'sigma',sc)
n=min(len(oa),len(ob))
for grp in [xc,mc,sc]:
    A=oa[grp].values[:n].astype(float); B=ob[grp].values[:n].astype(float)
    d=np.abs(A-B); den=np.maximum(np.abs(B),1e-30)
    print(grp[0][:5], 'maxabs',d.max(),'maxrel',(d/den).max(),'n iguais bit', int((A==B).all(axis=1).sum()),'/',n)
