"""B-11/G-2: linhas malformadas no ⑥ das 25 celulas s42 + sigma_2 + n_retries."""
import os, json, glob
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141'
bad=tot=0; rows=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    st=os.path.join(ROOT,pb,'42',f'exp_main_c141_{pb}_42')
    nb=0; n=0; h=f=0
    for l in open(st+'.jsonl'):
        if not l.strip(): continue
        n+=1
        try:
            e=json.loads(l)
            if e.get('rec')=='header': h+=1
            if e.get('rec')=='footer': f+=1
        except Exception: nb+=1
    man=json.load(open(st+'.manifest.json'))
    sur=pd.read_parquet(st+'__surrogate.parquet')
    so=sur[sur.regime=='online']
    M=len([c for c in pd.read_parquet(st+'__real.parquet').columns if c.startswith('f') and c[1:].isdigit()])
    s2 = ('sigma_2' in sur.columns)
    s2nan = float(np.isnan(so['sigma_2'].values).mean()) if s2 else np.nan
    rows.append(dict(pb=pb,M=M,linhas=n,malformadas=nb,header=h,footer=f,
                     n_retries=man.get('n_retries'),status=man['status'],
                     tem_sigma_2=s2,sigma_2_nan_frac=s2nan))
    bad+=nb; tot+=n
d=pd.DataFrame(rows); print(d.to_string())
print()
print('TOTAL linhas ⑥ %d ; MALFORMADAS %d ; header==1 em %d/25 ; footer==1 em %d/25 ; n_retries!=0 em %d'%(
    tot,bad,int((d.header==1).sum()),int((d.footer==1).sum()),int((d.n_retries!=0).sum())))
print('sigma_2: presente em %d/25 celulas ; nas M=3 fracao NaN: %s'%(int(d.tem_sigma_2.sum()),
      sorted(set(d[d.M==3].sigma_2_nan_frac.round(4)))))
d.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t11_jsonl.csv',index=False)
