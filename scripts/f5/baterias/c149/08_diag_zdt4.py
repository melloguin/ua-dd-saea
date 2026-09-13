import json,numpy as np,pandas as pd,pyarrow.parquet as pq,sys
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149")
from _hvlib import nd_mask, hvi2d_batch, hvi_md
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
for lab,exp,prob in [("q10_ZDT4","batch","ZDT4"),("ZDT4","main","ZDT4"),("q10_WFG9","batch","WFG9")]:
    p=f"{ROOT}/{lab}/42/exp_{exp}_c149_{prob}_42"
    m=json.load(open(p+".manifest.json")); dec=[];hdr=None
    for line in open(p+".jsonl"):
        d=json.loads(line)
        if d["rec"]=="decision": dec.append(d)
        elif d["rec"]=="header": hdr=d
    D=hdr["D"];M=hdr["M"];q=m["q"];n_init=11*D-1
    real=pq.read_table(p+"__real.parquet").to_pandas(); Fall=real[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id","mu_0","mu_1"]).to_pandas()
    sur=sur[sur.regime=="online"]; grp=dict(list(sur.groupby("geracao")))
    print(f"### {exp}/{prob}")
    npos_ok=0;n=0;errs=[]
    for g in range(1,len(dec)+1):
        dd=dec[g-1]; sub=grp[g]; MU=sub[["mu_0","mu_1"]].values.astype(np.float64)
        rsi=sub.real_solution_id.values; s0=dd["solution_id"]
        w=np.where(rsi==s0)[0]
        if len(w)!=1: continue
        narq=n_init+q*(g-1); A=Fall[:narq]; lo=A.min(0);hi=A.max(0);rng=np.where(hi>lo,hi-lo,1.0)
        An=(A-lo)/rng; Cn=(MU-lo)/rng; P=An[nd_mask(An)]
        H=hvi2d_batch(P,np.full(2,1.1),Cn)
        npos=int((H>1e-12).sum()); npos_ok+= (npos==dd["n_hvi_pos"]); n+=1
        errs.append(abs(H[w[0]]-dd["hvi_escolhido"]))
        if g<=6 or (abs(H[w[0]]-dd["hvi_escolhido"])>1e-4 and g<40):
            print(f"  g={g} log_hvi={dd['hvi_escolhido']:.6f} recomp={H[w[0]]:.6f} n_hvi_pos log={dd['n_hvi_pos']} recomp={npos} range_f={rng} nND={len(P)}")
    print(f"  -> n_hvi_pos bate {npos_ok}/{n}; err med {np.median(errs):.3e} max {np.max(errs):.3e}")
