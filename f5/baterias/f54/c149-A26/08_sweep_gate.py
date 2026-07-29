"""Gate proposto (F5.7): X da linha ③ marcada com real_solution_id  ==  X da linha ① `s`.
Varre TODAS as células da campanha que tenham surrogate com real_solution_id."""
import os, glob, numpy as np, pyarrow.parquet as pq, csv, sys, traceback, time
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
out=[]
cells=sorted(glob.glob(f"{ROOT}/*/*/*/*__surrogate.parquet"))
print("surrogate files:",len(cells)); sys.stdout.flush()
t0=time.time()
for i,sp in enumerate(cells):
    rp=sp.replace("__surrogate.parquet","__real.parquet")
    parts=sp.split("/"); alg=parts[-4]; label=parts[-3]; seed=parts[-2]
    rec=dict(alg=alg,label=label,seed=seed)
    try:
        smd=pq.ParquetFile(sp).metadata
        rec["n3"]=smd.num_rows
        if smd.num_rows==0: rec["status"]="empty_L3"; out.append(rec); continue
        cols=set(pq.read_schema(sp).names)
        xs=sorted([c for c in cols if c.startswith("x") and c[1:].isdigit()],key=lambda c:int(c[1:]))
        use=["real_solution_id"]+xs[:3]
        if "real_solution_id" not in cols: rec["status"]="no_rsid"; out.append(rec); continue
        S=pq.read_table(sp,columns=use).to_pandas()
        S=S[S.real_solution_id.notna()]
        rec["n_flag"]=len(S)
        if len(S)==0: rec["status"]="no_flagged"; out.append(rec); continue
        Rt=pq.read_table(rp,columns=["solution_id"]+xs[:3]).to_pandas()
        A=Rt.set_index("solution_id")
        sid=S.real_solution_id.astype("int64").values
        miss=~np.isin(sid,A.index.values)
        rec["sid_fora_L1"]=int(miss.sum())
        keep=~miss
        X3=S[xs[:3]].values[keep].astype(np.float64)
        X1=A.loc[sid[keep],xs[:3]].values.astype(np.float64)
        d=np.abs(X3-X1)
        rec["n_cmp"]=int(keep.sum())
        rec["frac_exact"]=float(np.mean(d.max(1)==0))
        rec["frac_1e6"]=float(np.mean(d.max(1)<1e-6))
        rec["max_dX"]=float(d.max())
        rec["status"]="OK" if rec["frac_1e6"]>0.999 else "MISMATCH"
    except Exception as e:
        rec["status"]="ERR:"+type(e).__name__; rec["err"]=str(e)[:120]
    out.append(rec)
    if i%50==0: print(f"  {i}/{len(cells)} {time.time()-t0:.0f}s"); sys.stdout.flush()
keys=["alg","label","seed","status","n3","n_flag","n_cmp","sid_fora_L1","frac_exact","frac_1e6","max_dX","err"]
with open("sweep_gate_L3xL1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
    for r in out: w.writerow({k:r.get(k,"") for k in keys})
from collections import Counter
print(Counter(r["status"] for r in out))
print("MISMATCHES:")
for r in out:
    if r["status"]=="MISMATCH": print("  ",r["alg"],r["label"],r["seed"],r.get("frac_1e6"),r.get("max_dX"),r.get("n_cmp"))
