import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    hdr=json.loads(open(base+".jsonl").readline()); D=hdr['D']; M=hdr['M']; n0=11*D-1
    ev=[json.loads(l) for l in open(base+".jsonl")]
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G)
    xc=[f"x{i}" for i in range(D)]
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao']+xc)
    on=sur[sur.regime=='online']; del sur
    pop=pd.read_parquet(base+"__pop.parquet")
    grp={g:d[xc].to_numpy(np.float32) for g,d in on.groupby('geracao')}
    i_tail=0; i_full=0; n=0
    for c in range(1,C):
        A=grp.get(c); B=grp.get(c+1)
        if A is None or B is None: continue
        n+=1
        H={B[i].tobytes() for i in range(100)}
        i_tail+=len(H&{A[i].tobytes() for i in range(len(A)-100,len(A))})
        i_full+=len(H&{A[i].tobytes() for i in range(len(A))})
    # ② solution_id denso por geracao
    ok=0; g_n=0
    for g,b in pop.groupby('geracao'):
        g_n+=1; ok+= (sorted(b.solution_id.tolist())==list(range(n0+3*(g-1))))
    out.append(dict(problema=p,D=D,n_fronteiras=n,inter_tail=i_tail,inter_full=i_full,
                    pop_gers=g_n,pop_denso_ok=ok))
    print(p,i_tail,i_full,ok,"/",g_n,flush=True)
df=pd.DataFrame(out); df.to_csv("warm_pop_e7.csv",index=False)
print("\nintersecao head(c+1) x tail(c):",df.inter_tail.sum(),"| x BLOCO INTEIRO(c) [1900 linhas]:",df.inter_full.sum(),
      "em",df.n_fronteiras.sum(),"fronteiras")
print("② solution_id denso 0..n-1 por geracao:",df.pop_denso_ok.sum(),"/",df.pop_gers.sum())
