"""transf_params da ③ (por geracao, online E sonda) == z_mean/z_std do evento `fit` do ⑥? (DEF-C3) — 30 celulas"""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    fits={}
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="fit": fits[dd["geracao"]]=(np.array(dd["z_mean"]),np.array(dd["z_std"]))
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","transf_params"]).to_pandas()
    eo=[];es=[];nuni=0
    for (reg,g),sub in sur.groupby(["regime","geracao"]):
        nuni+= sub.transf_params.nunique()!=1
        tp=json.loads(sub.transf_params.iloc[0])
        zm,zs=fits[g]
        e=max(np.abs(np.array(tp["mean"])-zm).max(),np.abs(np.array(tp["std"])-zs).max())
        (eo if reg=="online" else es).append(e)
    rows.append(dict(exp=exp,prob=prob,n_online=len(eo),n_sonda=len(es),
        err_online_max=float(np.max(eo)),err_sonda_max=float(np.max(es)),
        n_transf_nao_unico=int(nuni)))
    print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,"transf_check_c149.csv"),index=False)
