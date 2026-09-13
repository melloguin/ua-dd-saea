import sys,os,glob,numpy as np,pandas as pd,pyarrow.parquet as pq
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src import metrics as MET
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
res=[];cache={}
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,'42')
    if not os.path.isdir(d): continue
    exp='batch' if lab.startswith('q10_') else 'main'; prob=lab[4:] if lab.startswith('q10_') else lab
    t=pq.read_table(glob.glob(d+'/*__real.parquet')[0]).to_pandas()
    M=len([x for x in t.columns if x.startswith('f') and x[1:].isdigit()])
    D=len([x for x in t.columns if x.startswith('x') and x[1:].isdigit()])
    F=t[[f'f{j}' for j in range(M)]].values.astype(float); n0=11*D-1
    if prob not in cache: cache[prob]=MET.reference_set(prob)
    ref=cache[prob]
    a=MET.metrics_of_set(F[:n0],prob,ref_norm=ref)['igd_plus']; b=MET.metrics_of_set(F,prob,ref_norm=ref)['igd_plus']
    res.append((exp,prob,D,M,a,b,(a-b)/a*100 if a else np.nan)); print(exp,prob,round(a,6),round(b,6),flush=True)
r=pd.DataFrame(res,columns=['exp','prob','D','M','igd_doe','igd_final','ganho_pct'])
r.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c149/ganho_doe_c149.csv',index=False)
print("\n=== GANHO IGD+ SOBRE O DoE ===")
for exp in ['main','batch']:
    g=r[r.exp==exp].ganho_pct.dropna(); print(f"  {exp:6s} mediana={g.median():+6.2f}% | zero exato {int((g.abs()<1e-9).sum())}/{len(g)}")
print("  main zero:",sorted(r[(r.exp=='main')&(r.ganho_pct.abs()<1e-9)].prob.tolist()))
print("  main >0  :",sorted([(p,round(v,1)) for p,v in r[(r.exp=='main')&(r.ganho_pct>1e-9)][['prob','ganho_pct']].values],key=lambda x:-x[1]))
print("  batch    :",[(p,round(v,1)) for p,v in r[r.exp=='batch'][['prob','ganho_pct']].values])
