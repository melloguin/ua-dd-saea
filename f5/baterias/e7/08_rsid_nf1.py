import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
def ndm(Y):
    n=len(Y); dom=np.zeros(n,bool)
    for i in range(n):
        le=(Y<=Y[i]).all(axis=1); lt=(Y<Y[i]).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return ~dom
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']; n0=11*D-1
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G)
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao','real_solution_id'])
    on=sur[sur.regime=='online']; sd=sur[sur.regime=='sonda']
    nrs=int(on.real_solution_id.notna().sum()); nun=int(on.real_solution_id.nunique())
    # por ciclo, quantos rsid distintos e se sao exatamente os 3 do ciclo
    ok=0
    for g in G:
        c=g['geracao']; b=on[on.geracao==c]
        u=set(int(v) for v in b.real_solution_id.dropna().unique())
        esp=set(s for s in (n0+3*(c-1)+j for j in range(3)) if s<31*D-1)
        ok+= (u==esp)
    out.append(dict(problema=p,D=D,C=C,n_rsid_linhas=nrs,n_rsid_unicos=nun,esperado_unicos=3*C,
                    ciclos_conjunto_exato=ok, rsid_sonda=int(sd.real_solution_id.notna().sum())))
    print(p,nrs,nun,3*C,ok,flush=True)
df=pd.DataFrame(out); df.to_csv("rsid_e7.csv",index=False)
pd.set_option('display.width',250); print(df.to_string())
print("\nTOT linhas com rsid:",df.n_rsid_linhas.sum(),"| unicos:",df.n_rsid_unicos.sum(),"| esperado:",df.esperado_unicos.sum(),
      "| ciclos com conjunto EXATO:",df.ciclos_conjunto_exato.sum(),"/",df.C.sum(),"| rsid na sonda:",df.rsid_sonda.sum())
