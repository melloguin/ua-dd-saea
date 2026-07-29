import json,numpy as np,pandas as pd,pyarrow.parquet as pq,sys
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149")
from _hvlib import nd_mask, hvi2d_batch
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
p=f"{ROOT}/q10_ZDT4/42/exp_batch_c149_ZDT4_42"
m=json.load(open(p+".manifest.json")); dec=[];hdr=None
for line in open(p+".jsonl"):
    d=json.loads(line)
    if d["rec"]=="decision": dec.append(d)
    elif d["rec"]=="header": hdr=d
print("n_retries",m["n_retries"],"created",m["created_at"],"updated",m["updated_at"],"status",m["status"])
D=hdr["D"];M=2;q=10;n_init=11*D-1
real=pq.read_table(p+"__real.parquet").to_pandas(); F=real[["f0","f1"]].values.astype(np.float64)
sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id","mu_0","mu_1","sigma_0","sigma_1","transf_params","fe_treino_max"]).to_pandas()
sur=sur[sur.regime=="online"]; grp=dict(list(sur.groupby("geracao")))
for g in [2,3,4,5,7,9,20,50,100,199]:
    dd=dec[g-1]; sub=grp[g]; MU=sub[["mu_0","mu_1"]].values.astype(np.float64)
    w=int(np.where(sub.real_solution_id.values==dd["solution_id"])[0][0])
    print(f"g={g} alvo hvi={dd['hvi_escolhido']:.6f} npos={dd['n_hvi_pos']} ftm={sub.fe_treino_max.iloc[0]} mu_sel_nat_log={dd['mu_sel_nat']} mu_sel_③={MU[w]}")
    for nome,narq in [("q(g-1)",n_init+q*(g-1)),("q(g-2)",n_init+q*(g-2)),("so init",n_init),("q*g",n_init+q*g),("ftm+1",int(sub.fe_treino_max.iloc[0])+1)]:
        if narq<1 or narq>len(F): continue
        A=F[:narq]; lo=A.min(0);hi=A.max(0);rng=np.where(hi>lo,hi-lo,1.0)
        An=(A-lo)/rng; Cn=(MU-lo)/rng; P=An[nd_mask(An)]
        H=hvi2d_batch(P,np.full(2,1.1),Cn)
        print(f"    {nome:8s} n={narq} hvi_sel={H[w]:.6f} npos={int((H>1e-12).sum())} argmax={int(np.argmax(H))==w}")
