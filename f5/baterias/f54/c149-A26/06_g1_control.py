import json, numpy as np, pandas as pd, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
XC=[f"x{i}" for i in range(10)]
def L(cell,pref):
    p=f"{R}/{cell}/42/{pref}"
    return pq.read_table(p+"__surrogate.parquet").to_pandas(), [json.loads(l) for l in open(p+".jsonl")]
S_b,J_b=L("q10_ZDT4","exp_batch_c149_ZDT4_42")
S_m,J_m=L("ZDT4","exp_main_c149_ZDT4_42")
d_b={r['geracao']:r for r in J_b if r['rec']=='decision'}
d_m={r['geracao']:r for r in J_m if r['rec']=='decision'}
f_b={r['geracao']:r for r in J_b if r['rec']=='fit'}
f_m={r['geracao']:r for r in J_m if r['rec']=='fit'}
print("=== g=1 determinism control (main v5 vs batch v6, identical DoE+seeds) ===")
print(" seed_nsga2  main",d_m[1]['seed_nsga2']," batch",d_b[1]['seed_nsga2'])
for k in ['acq_resF_mu_z_min','acq_resF_mu_z_max','acq_resF_sigma2_z_max','hvi_escolhido','n_front_acq','n_hvi_pos','n_empatados','mu_sel_nat','sigma2_agg_sel_z','solution_id','caminho']:
    print(f"  L6 {k:22s} main={d_m[1][k]}  batch={d_b[1][k]}")
print("  L6 fit val_mse main[:3]",[round(v,6) for v in f_m[1]['val_mse'][:3]],"batch[:3]",[round(v,6) for v in f_b[1]['val_mse'][:3]])
print("  L6 fit val_mse EQUAL?",f_m[1]['val_mse']==f_b[1]['val_mse'])
print("  L6 fit z_mean main",f_m[1]['z_mean'],"batch",f_b[1]['z_mean'])

ob=S_b[(S_b.regime=="online")&(S_b.geracao==1)].reset_index(drop=True)
om=S_m[(S_m.regime=="online")&(S_m.geracao==1)].reset_index(drop=True)
print("\n=== g=1 L3 front: batch vs main, row-by-row ===")
print("  rows",len(ob),len(om))
for c in XC+["mu_0","mu_1","sigma_0","sigma_1"]:
    d=np.abs(ob[c].values.astype(float)-om[c].values.astype(float))
    print(f"   {c:8s} max|d|={d.max():.6e}  frac_exact={np.mean(d==0):.4f}")
# set-level: are the fronts the same SET?
A=ob[XC].values; B=om[XC].values
ka={tuple(r) for r in A}; kb={tuple(r) for r in B}
print("  set intersection of X:",len(ka&kb),"of",len(ka),len(kb))
print("  transf_params g1: batch",ob.transf_params.iloc[0],"| main",om.transf_params.iloc[0])

# probe block g=1
pb=S_b[(S_b.regime=="sonda")&(S_b.geracao==1)].reset_index(drop=True)
pm=S_m[(S_m.regime=="sonda")&(S_m.geracao==1)].reset_index(drop=True)
print("\n=== g=1 SONDA block (same fixed 2000 pts, same model if same run-state) ===")
print("  rows",len(pb),len(pm))
dx=np.abs(pb[XC].values.astype(float)-pm[XC].values.astype(float)).max()
print("  max|dX| probe pts:",dx)
for c in ["mu_0","mu_1","sigma_0","sigma_1"]:
    d=np.abs(pb[c].values.astype(float)-pm[c].values.astype(float))
    print(f"   {c:8s} max|d|={d.max():.6e} median|d|={np.median(d):.3e} frac_exact={np.mean(d==0):.4f} rel_med={np.median(d/np.maximum(np.abs(pm[c].values.astype(float)),1e-12)):.3e}")
