"""T11/c149 — RE-MEDICAO da saude: sonda (regua Sobol) + ganho sobre o DoE.
Corrige a armadilha do `bloco` como STRING (achado do adversarial c149-A26)."""
import pandas as pd, numpy as np, json, os, glob
import pyarrow.parquet as pq
s=pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/sonda_f52e.csv')
c=s[s.alg=='c149'].copy()
print("dtype de `bloco`:",c.bloco.dtype," -> convertendo com to_numeric (armadilha do adversarial)")
c['bloco_n']=pd.to_numeric(c.bloco,errors='coerce')
print("NaN apos to_numeric:",int(c.bloco_n.isna().sum()))

def dwape(df,key):
    out=[]
    for (e,p,o),g in df.groupby(['exp','problema','obj']):
        g=g.sort_values(key)
        if len(g)<2: continue
        a,b=g.wape.iloc[0],g.wape.iloc[-1]
        if a and np.isfinite(a) and np.isfinite(b): out.append(((b-a)/abs(a)*100,e,p,o))
    return out

for key,nome in [('bloco','ORDEM LEXICOGRAFICA (errada)'),('bloco_n','ORDEM NUMERICA (correta)')]:
    for exp in ['main','batch']:
        d=dwape(c[c.exp==exp],key)
        v=[x[0] for x in d]
        print(f"  {nome:30s} {exp:6s} ΔWAPE 1º→último bloco: mediana={np.median(v):+7.2f}%  (n={len(v)} series)")

print("\n--- excluindo a celula contaminada (batch/ZDT4, A26) ---")
cc=c[~((c.exp=='batch')&(c.problema=='ZDT4'))]
for exp in ['main','batch']:
    v=[x[0] for x in dwape(cc[cc.exp==exp],'bloco_n')]
    print(f"  {exp:6s} ΔWAPE mediana={np.median(v):+7.2f}%  (n={len(v)})")

print("\n--- cobertura95 / correlacao no ULTIMO bloco (regua Sobol; regra 12: sem estratificada) ---")
for exp in ['main','batch']:
    d=c[c.exp==exp].sort_values('bloco_n').groupby(['problema','obj']).tail(1)
    dd=cc[cc.exp==exp].sort_values('bloco_n').groupby(['problema','obj']).tail(1)
    print(f"  {exp:6s} cobertura95 mediana={d.cobertura95.median():.3f} (s/ZDT4: {dd.cobertura95.median():.3f}) | corr mediana={d["corr"].median():.3f} (s/ZDT4: {dd["corr"].median():.3f}) | n_nan total={int(d.n_nan.sum())}")
print(f"\n  n_validas: {sorted(set(c.n_validas))} em {len(c)} medicoes | n_nan total={int(c.n_nan.sum())}")

# --- ganho sobre o DoE (IGD+) ---
print("\n=== GANHO DE IGD+ SOBRE O DoE (recomputado da ①) ===")
import sys; sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src import metrics as MET
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
res=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,'42')
    if not os.path.isdir(d): continue
    exp='batch' if lab.startswith('q10_') else 'main'
    prob=lab[4:] if lab.startswith('q10_') else lab
    P=glob.glob(d+'/*__real.parquet')[0]
    t=pq.read_table(P).to_pandas()
    M=len([x for x in t.columns if x.startswith('f') and x[1:].isdigit()])
    D=len([x for x in t.columns if x.startswith('x') and x[1:].isdigit()])
    F=t[[f'f{j}' for j in range(M)]].values.astype(float); n0=11*D-1
    try:
        a=MET.igd_plus(F[:n0],prob); b=MET.igd_plus(F,prob)
        res.append((exp,prob,a,b,(a-b)/a*100 if a else np.nan))
    except Exception as e:
        res.append((exp,prob,np.nan,np.nan,np.nan))
r=pd.DataFrame(res,columns=['exp','prob','igd_doe','igd_final','ganho_pct'])
r.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c149/ganho_doe_c149.csv',index=False)
for exp in ['main','batch']:
    g=r[r.exp==exp].ganho_pct.dropna()
    print(f"  {exp:6s} mediana={g.median():+6.2f}%  | ganho EXATAMENTE 0,00% em {int((g.abs()<1e-9).sum())}/{len(g)} celulas")
print("\n  celulas main com ganho 0:",sorted(r[(r.exp=='main')&(r.ganho_pct.abs()<1e-9)].prob.tolist()))
print("  celulas main com ganho >0:",[(p,round(v,1)) for p,v in r[(r.exp=='main')&(r.ganho_pct>1e-9)][['prob','ganho_pct']].values])
