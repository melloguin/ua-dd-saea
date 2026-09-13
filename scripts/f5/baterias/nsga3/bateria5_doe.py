"""Bateria 5 — U2 DoE bit-a-bit contra o artefato (D63/D88) + hash do sidecar. READ-ONLY."""
import json,os
import numpy as np,pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
probs=sorted(p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}'))
rows=[]
for prob in probs:
    base=f'{ROOT}/{prob}/42/exp_main_nsga3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    D=len([c for c in pd.read_parquet(base+'__real.parquet').columns if c.startswith('x')])
    init=11*D-1
    R=pd.read_parquet(base+'__real.parquet')
    xc=[f'x{i}' for i in range(D)]
    pq=f'{DOE}/{prob}/doe_{prob}_42.parquet'; mf=f'{DOE}/{prob}/doe_{prob}_42.manifest.json'
    A=pd.read_parquet(pq); dm=json.load(open(mf))
    Ax=A[[c for c in A.columns if c.startswith('x')]].values if any(c.startswith('x') for c in A.columns) else A.values
    dX=float(np.abs(Ax[:init].astype(np.float32)-R.iloc[:init][xc].values).max())
    h=dm.get('sha256') or dm.get('hash') or dm.get('doe_hash')
    rows.append(dict(prob=prob,D=D,init=init,linhas_doe=len(A),dX_max=dX,
        hash_sidecar=(h or '')[:16],hash_manifesto=man['doe_hash'][:16],
        hash_bate=(h==man['doe_hash']),ordem_igual=(dX==0.0),
        cols_doe=str(list(A.columns)[:4])))
T=pd.DataFrame(rows); T.to_csv('u2_doe_bit_a_bit.csv',index=False)
pd.set_option('display.width',220); print(T.to_string(index=False))
print('\ndX==0 em',int((T.dX_max==0).sum()),'/25 ; hash bate em',int(T.hash_bate.sum()),'/25')
