import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq,glob,datetime
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
d=f"{ROOT}/q10_ZDT4/42"; p=f"{d}/exp_batch_c149_ZDT4_42"
fits={}
for line in open(p+".jsonl"):
    dd=json.loads(line)
    if dd["rec"]=="fit": fits[dd["geracao"]]=(np.array(dd["z_mean"]),np.array(dd["z_std"]))
sur=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","transf_params","fe_treino_max"]).to_pandas()
on=sur[sur.regime=="online"]
tp={g:json.loads(s.transf_params.iloc[0]) for g,s in on.groupby("geracao")}
G=max(fits)
# lag?
for lag in [-3,-2,-1,0,1,2,3]:
    errs=[]
    for g in range(1,G+1):
        if g+lag in fits:
            zm,zs=fits[g+lag]
            errs.append(max(np.abs(np.array(tp[g]["mean"])-zm).max(),np.abs(np.array(tp[g]["std"])-zs).max()))
    print(f"lag={lag:+d}: n={len(errs)} err_med={np.median(errs):.4g} err_max={np.max(errs):.4g} nbate={sum(e<1e-5 for e in errs)}")
# melhor casamento global: para cada g da ③, qual iteracao do ⑥ minimiza o erro?
best=[]
Zm=np.array([fits[g][0] for g in range(1,G+1)]); Zs=np.array([fits[g][1] for g in range(1,G+1)])
for g in range(1,G+1):
    a=np.array(tp[g]["mean"]); b=np.array(tp[g]["std"])
    e=np.maximum(np.abs(Zm-a).max(1),np.abs(Zs-b).max(1))
    best.append((g,int(np.argmin(e))+1,float(e.min())))
bb=pd.DataFrame(best,columns=["g3","g6","err"])
print("\nmelhor casamento ③->⑥ (primeiros 15):"); print(bb.head(15).to_string(index=False))
print("n com err<1e-5:",int((bb.err<1e-5).sum()),"/",len(bb))
print("mtimes:")
for f in sorted(glob.glob(d+"/*")):
    print("  ",os.path.basename(f), datetime.datetime.fromtimestamp(os.path.getmtime(f)).isoformat(), os.path.getsize(f))
# ⑥ timestamps: primeira e ultima decision
ts=[json.loads(l)["ts"] for l in open(p+".jsonl") if '"decision"' in l]
print("⑥ decision ts:",ts[0],"->",ts[-1])
m=json.load(open(p+".manifest.json")); print("manifest created",m["created_at"],"updated",m["updated_at"],"tempo_total",m["timing"]["tempo_total_s"])
# outras celulas batch p/ contraste
for prob in ["ZDT1","WFG9"]:
    pp=f"{ROOT}/q10_{prob}/42/exp_batch_c149_{prob}_42"
    mm=json.load(open(pp+".manifest.json")); tt=[json.loads(l)["ts"] for l in open(pp+".jsonl") if '"decision"' in l]
    print(f"  q10_{prob}: dec {tt[0]} -> {tt[-1]} total={mm['timing']['tempo_total_s']}")
