import json, hashlib, os
import pandas as pd, numpy as np
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
man=json.load(open(B+'.manifest.json'))
real=pd.read_parquet(B+'__real.parquet')
xc=['x0','x1']
doedir='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/'
d=pd.read_parquet(doedir+'doe_MMF1_42.parquet')
dm=json.load(open(doedir+'doe_MMF1_42.manifest.json'))
print('doe cols',list(d.columns),'shape',d.shape)
print('doe manifest', json.dumps(dm)[:600])
A=real[real.fase=='init'][xc].values.astype(np.float64)
dc=[c for c in d.columns if c.startswith('x')]
Bx=d[dc].values.astype(np.float64)
print('max|dX| (1)x artefato:', np.abs(A-Bx).max(), '  EXATO?', (A==Bx).all())
print('max|dX| artefato->float32:', np.abs(A-Bx.astype(np.float32).astype(np.float64)).max())
h=hashlib.sha256(open(doedir+'doe_MMF1_42.parquet','rb').read()).hexdigest()
print('sha256 arquivo', h, 'manifest.doe_hash', man['doe_hash'], 'igual', h==man['doe_hash'])
print('doe manifest hash field', {k:v for k,v in dm.items() if 'hash' in k.lower()})
bb=[tuple(r) for r in Bx]; print('dup no DoE float64', len(bb)-len(set(bb)))
bb32=[tuple(r) for r in Bx.astype(np.float32)]; print('dup no DoE float32', len(bb32)-len(set(bb32)))
print()
print('=== dupX na (1) ===')
v=[tuple(r) for r in real[xc].values]
from collections import Counter
c=Counter(v)
for k,n in c.items():
    if n>1:
        idx=[i for i,t in enumerate(v) if t==k]
        print('X float32 repetido', k, 'linhas', idx)
        print(real.iloc[idx][['solution_id','x0','x1','f0','f1','fe_index','fase']])
