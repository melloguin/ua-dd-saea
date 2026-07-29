"""Elo posicional forte: X da linha da ③ marcada com real_solution_id == X da ① naquele solution_id (bit-a-bit)
+ U11 erro de fantasia (mu vs f real do escolhido). 30 celulas."""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    m=json.load(open(p+".manifest.json")); hdr=json.loads(open(p+".jsonl").readline())
    D=hdr["D"];M=hdr["M"];q=m["q"]
    real=pq.read_table(p+"__real.parquet").to_pandas().set_index("solution_id")
    cols=["regime","real_solution_id"]+[f"x{j}" for j in range(D)]+[f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]+["geracao"]
    sur=pq.read_table(p+"__surrogate.parquet",columns=cols).to_pandas()
    sel=sur[(sur.regime=="online")&(sur.real_solution_id.notna())]
    sid=sel.real_solution_id.astype(int).values
    X3=sel[[f"x{j}" for j in range(D)]].values
    X1=real.loc[sid,[f"x{j}" for j in range(D)]].values
    dX=np.abs(X3-X1).max(1)
    F1=real.loc[sid,[f"f{j}" for j in range(M)]].values.astype(np.float64)
    MU=sel[[f"mu_{j}" for j in range(M)]].values.astype(np.float64)
    SG=sel[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)
    wape=np.abs(MU-F1).sum(0)/np.maximum(np.abs(F1).sum(0),1e-12)
    cob=(np.abs(MU-F1)<=1.96*SG).mean(0)
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,q=q,n=len(sel),
        X_bitexato=int((dX==0).sum()),dX_max=float(dX.max()),
        U11_wape_medio=float(wape.mean()),U11_wape=json.dumps([round(float(x),4) for x in wape]),
        U11_cob_medio=float(cob.mean()),
        x_min=float(X3.min()),x_max=float(X3.max())))
    print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,"link_X_c149.csv"),index=False)
