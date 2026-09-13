"""sigma_dict: 'res.F da aquisicao = [mu_z, -sigma2_z] e RECONSTITUIVEL destas linhas'.
Confere acq_resF_mu_z_min/max e acq_resF_sigma2_z_max do ⑥ contra a ③ (front online da geracao). 30 celulas."""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    dec=[];hdr=None
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="decision": dec.append(dd)
        elif dd["rec"]=="header": hdr=dd
    M=hdr["M"]
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","transf_params"]+
        [f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]).to_pandas()
    on=sur[sur.regime=="online"]; grp=dict(list(on.groupby("geracao")))
    e_min=[];e_max=[];e_s2=[];ok=0;n=0;prim_falha=None
    for g in range(1,len(dec)+1):
        dd=dec[g-1]; sub=grp[g]
        tp=json.loads(sub.transf_params.iloc[0]); zm=np.array(tp["mean"]); zs=np.array(tp["std"])
        MUz=(sub[[f"mu_{j}" for j in range(M)]].values.astype(np.float64)-zm)/zs
        S2z=(sub[[f"sigma_{j}" for j in range(M)]].values.astype(np.float64)/zs)**2
        a=np.abs(MUz.min(0)-np.array(dd["acq_resF_mu_z_min"])).max()
        b=np.abs(MUz.max(0)-np.array(dd["acq_resF_mu_z_max"])).max()
        c=np.abs(S2z.max(0)-np.array(dd["acq_resF_sigma2_z_max"])).max()
        e_min.append(a);e_max.append(b);e_s2.append(c);n+=1
        good=max(a,b,c)<=1e-5
        ok+=good
        if not good and prim_falha is None: prim_falha=g
    rows.append(dict(exp=exp,prob=prob,M=M,n=n,ok=ok,
        e_min_max=float(np.max(e_min)),e_max_max=float(np.max(e_max)),e_s2_max=float(np.max(e_s2)),
        e_med=float(np.median(np.maximum(np.maximum(e_min,e_max),e_s2))),primeira_falha=prim_falha))
    print(rows[-1],flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,"resF_recon_c149.csv"),index=False)
