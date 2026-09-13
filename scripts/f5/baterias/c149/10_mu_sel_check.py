"""DI-10 query-joia estrita: mu_sel_nat/std_ensemble_sel/sigma2_agg do ⑥ == linha da ③ do escolhido? (30 celulas)"""
import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    m=json.load(open(p+".manifest.json")); dec=[];hdr=None
    for line in open(p+".jsonl"):
        dd=json.loads(line)
        if dd["rec"]=="decision": dec.append(dd)
        elif dd["rec"]=="header": hdr=dd
    D=hdr["D"];M=hdr["M"];q=m["q"];n_init=11*D-1
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id"]+
        [f"mu_{j}" for j in range(M)]+[f"sigma_{j}" for j in range(M)]+["transf_params"]).to_pandas()
    sur=sur[sur.regime=="online"]; grp=dict(list(sur.groupby("geracao")))
    real=pq.read_table(p+"__real.parquet").to_pandas()
    X=real[[f"x{j}" for j in range(D)]].values.astype(np.float64)
    okmu=0; oksig=0; oks2=0; okx=0; n=0; dmu=[]; dsig=[]; ds2=[]; dx=[]
    for g in range(1,len(dec)+1):
        dd=dec[g-1]; sub=grp[g]
        w=np.where(sub.real_solution_id.values==dd["solution_id"])[0]
        if len(w)!=1: continue
        w=int(w[0]); n+=1
        mu3=sub[[f"mu_{j}" for j in range(M)]].values[w].astype(float)
        sg3=sub[[f"sigma_{j}" for j in range(M)]].values[w].astype(float)
        tp=json.loads(sub.transf_params.iloc[0]); zstd=np.array(tp["std"],float)
        e=np.abs(mu3-np.array(dd["mu_sel_nat"])).max(); dmu.append(e); okmu+= e<=5e-4+1e-4*np.abs(mu3).max()
        e2=np.abs(sg3-np.array(dd["std_ensemble_sel"])).max(); dsig.append(e2); oksig+= e2<=5e-4+1e-4*np.abs(sg3).max()
        s2=float(((sg3/zstd)**2).sum()); e3=abs(s2-dd["sigma2_agg_sel_z"]); ds2.append(e3); oks2+= e3<=5e-4+1e-4*abs(s2)
        # X do escolhido: ③ vs ① (bit-a-bit)
        x3=sub[[c for c in sub.columns if c.startswith("x")]].values[w] if any(c.startswith("x") for c in sub.columns) else None
        rows.append(dict(exp=exp,prob=prob,D=D,M=M,q=q,n=n,mu_ok=okmu,sig_ok=oksig,s2_ok=oks2,
        dmu_med=float(np.median(dmu)),dmu_max=float(np.max(dmu)),dsig_max=float(np.max(dsig)),ds2_max=float(np.max(ds2))))
    r=rows[-1] if rows else None
    rows=[x for x in rows if x is not r]  # so o ultimo
    rows.append(r)
    print(f"[{exp}/{prob}] n={n} mu_ok={okmu} sig_ok={oksig} s2_ok={oks2} dmu_med={np.median(dmu):.2e} dmu_max={np.max(dmu):.2e} dsig_max={np.max(dsig):.2e} ds2_max={np.max(ds2):.2e}",flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT,"mu_sel_check_c149.csv"),index=False)
