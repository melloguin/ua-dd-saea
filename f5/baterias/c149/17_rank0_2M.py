"""ASPECTO 2MD: o bloco online da ③ e um conjunto NAO-DOMINADO em [mu_z ; -sigma2_z] (res.X=rank-0)?
Amostra de geracoes por celula (todas onde G<=60; senao 25 espacadas)."""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
def n_dominados(F):
    n=len(F); dom=np.zeros(n,bool)
    for i in range(n):
        if dom[i]: continue
        le=(F[i]<=F).all(1); lt=(F[i]<F).any(1)
        dom|= (le&lt)
    return int(dom.sum())
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    hdr=json.loads(open(p+".jsonl").readline()); M=hdr["M"]
    dec=[json.loads(l) for l in open(p+".jsonl") if '"rec": "decision"' in l]
    G=len(dec)
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","transf_params"]+
        [f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]).to_pandas()
    on=sur[sur.regime=="online"]
    gs=list(range(1,G+1)) if G<=60 else sorted(set(np.linspace(1,G,25).round().astype(int)))
    tot=0;dm=0;dup=0;nrows=[]
    for g in gs:
        sub=on[on.geracao==g]
        tp=json.loads(sub.transf_params.iloc[0]); zm=np.array(tp["mean"]); zs=np.array(tp["std"])
        MUz=(sub[[f"mu_{j}" for j in range(M)]].values.astype(np.float64)-zm)/zs
        S2z=(sub[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)/zs)**2
        F=np.hstack([MUz,-S2z]).astype(np.float32).astype(np.float64)
        dm+=n_dominados(F); tot+=1; nrows.append(len(sub))
        dup+= len(sub)-len(np.unique(F,axis=0))
    rows.append(dict(exp=exp,prob=prob,M=M,G=G,gers_testadas=tot,
        n_gers_com_dominado=int(dm>0),soma_dominados=dm,soma_dup_2M=dup,
        n_min=int(min(nrows)),n_max=int(max(nrows))))
    print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,"rank0_2M_c149.csv"),index=False)
