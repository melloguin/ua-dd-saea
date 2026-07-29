import json, numpy as np, pandas as pd, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
XC=[f"x{i}" for i in range(10)]
LO=np.array([0.]+[-5.]*9); HI=np.array([1.]+[5.]*9)
for cell,pref,q in [("q10_ZDT4","exp_batch_c149_ZDT4_42",10),("q10_ZDT1","exp_batch_c149_ZDT1_42",10),("ZDT4","exp_main_c149_ZDT4_42",1)]:
    p=f"{R}/{cell}/42/{pref}"
    L1=pq.read_table(p+"__real.parquet").to_pandas().sort_values("solution_id")
    L4=pq.read_table(p+"__timing.parquet").to_pandas()
    J=[json.loads(l) for l in open(p+".jsonl")]
    dec={r['geracao']:r for r in J if r['rec']=='decision'}
    fit={r['geracao']:r for r in J if r['rec']=='fit'}
    D=len([c for c in L1.columns if c.startswith("x")])
    lo=LO[:D] if cell.endswith("ZDT4") else None
    X=L1[[f"x{i}" for i in range(D)]].values
    n0=int((L1.fase=="init").sum())
    # dist_min_arquivo of pick1 vs archive, in normalized space
    errs=[];  errs_nat=[]
    if cell.endswith("ZDT4"):
        Xn=(X-LO)/(HI-LO)
    else:
        Xn=X  # ZDT1 already [0,1]
    for g in sorted(dec):
        sid=dec[g]['solution_id']; n=n0+q*(g-1)
        d=np.sqrt(((Xn[:n]-Xn[sid])**2).sum(1)).min()
        errs.append(abs(d-dec[g]['dist_min_arquivo']))
        dn=np.sqrt(((X[:n]-X[sid])**2).sum(1)).min()
        errs_nat.append(abs(dn-dec[g]['dist_min_arquivo']))
    print(f"[{cell}] dist_min_arquivo(L6) vs recomputed from L1 X: max err NORM={max(errs):.3e}  NATIVE={min(max(errs_nat),9e9):.3e}")
    # mu_sel_nat vs f real of the pick
    mus=np.array([dec[g]['mu_sel_nat'] for g in sorted(dec)])
    sids=np.array([dec[g]['solution_id'] for g in sorted(dec)])
    F=L1.set_index("solution_id")[["f0","f1"]].loc[sids].values
    print(f"          WAPE(mu_sel_nat vs f real of pick) = {np.abs(mus-F).sum(0)/np.abs(F).sum(0)}")
    # f_best
    fb=np.array([dec[g]['f_best'] for g in sorted(dec)])
    Y=L1[["f0","f1"]].values
    rec=np.array([Y[:n0+q*(g-1)].min(0) for g in sorted(dec)])
    print(f"          f_best(L6) vs min of L1 archive prefix: max err={np.abs(fb-rec).max():.3e}")
    # L4 vs L6
    ef=max(abs(L4.set_index('geracao').tempo_fit_s[g]-dec[g]['tempo_fit_s']) for g in sorted(dec))
    en=max(abs(L4.set_index('geracao').n_acumulado[g]-fit[g]['n_treino']) for g in sorted(dec))
    print(f"          L4 vs L6: max|dt_fit|={ef:.2e}  max|dn|={en}")
    # L2 vs L1
    L2=pq.read_table(p+"__pop.parquet").to_pandas()
    sz=L2.groupby("geracao").size(); exp=np.array([n0+q*g for g in sorted(dec)])
    print(f"          L2 sizes match n0+q*g: {bool((sz.values==exp).all())}  total={len(L2)}")
