import pandas as pd, numpy as np, hashlib, json, glob, os, re
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments'
RE='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
rows=[]
for man in sorted(glob.glob(SM+'/*/*/*.manifest.json')):
    b=man[:-len('.manifest.json')]
    m=json.load(open(man))
    nm=os.path.basename(b)             # exp_main_<alg>_<prob>_<seed>
    parts=nm.split('_')
    alg=m.get('alg') or parts[2]
    pb=m.get('problema') or '_'.join(parts[3:-1])
    s42=glob.glob(f'{RE}/{alg}/{pb}/42/*__real.parquet')
    if not s42:
        rows.append((alg,pb,'SEM s42','','','','')); continue
    a=pd.read_parquet(s42[0]); c=pd.read_parquet(b+'__real.parquet')
    xs=[x for x in a.columns if re.fullmatch(r'x\d+',x)]
    ok = a.shape==c.shape and np.array_equal(a[xs].values,c[xs].values)
    m42=json.load(open(s42[0].replace('__real.parquet','.manifest.json')))
    n=min(len(a),len(c))
    d=np.abs(a[xs].values[:n]-c[xs].values[:n]).max(axis=1)
    firstdiff = int(np.argmax(d>0)) if (d>0).any() else -1
    rows.append((alg,pb,'X-IDENTICO' if ok else 'DIVERGE',
                 f"{m42.get('n_geracoes')}->{m.get('n_geracoes')}",
                 f"{m42.get('fe_final')}->{m.get('fe_final')}",
                 f"fe={firstdiff}", f"init={int((a['fase']=='init').sum())}"))
print('%-8s %-10s %-11s %-14s %-14s %-12s %s'%('alg','prob','veredito','n_ger 42->T11','fe_final','1a diverg','init'))
for r in rows: print('%-8s %-10s %-11s %-14s %-14s %-12s %s'%r)
