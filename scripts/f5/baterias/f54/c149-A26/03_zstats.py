import json, numpy as np, pandas as pd, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
XC=[f"x{i}" for i in range(10)]
def zdt4(X):
    X=np.asarray(X,float); f1=X[:,0]
    g=1+10*(X.shape[1]-1)+np.sum(X[:,1:]**2-10*np.cos(4*np.pi*X[:,1:]),axis=1)
    return np.column_stack([f1, g*(1-np.sqrt(f1/g))])
p=f"{R}/q10_ZDT4/42/exp_batch_c149_ZDT4_42"
L1=pq.read_table(p+"__real.parquet").to_pandas()
L3=pq.read_table(p+"__surrogate.parquet").to_pandas()
L6=[json.loads(l) for l in open(p+".jsonl")]
fits={r['geracao']:r for r in L6 if r['rec']=='fit'}
on=L3[L3.regime=="online"]
tp={g:json.loads(s) for g,s in on.groupby("geracao").transf_params.first().items()}

# z-stats from L1 (the archive of the "official" run)
Y1=L1.sort_values("solution_id")[["f0","f1"]].values
def zstats(Y,n,ddof=0):
    A=Y[:n]; return A.mean(0), A.std(0,ddof=ddof)
print("=== z_mean/z_std: L6.fit  vs  recomputed from L1 archive prefix ===")
errs=[]
for g in sorted(fits):
    n=fits[g]['n_treino']; m,s=zstats(Y1,n)
    e=max(np.abs(np.array(fits[g]['z_mean'])-m).max(), np.abs(np.array(fits[g]['z_std'])-s).max())
    errs.append(e)
print(f"  max err over 200 gens (ddof=0): {max(errs):.3e}   (g=1 {errs[0]:.2e}, g=2 {errs[1]:.2e}, g=200 {errs[-1]:.2e})")
m,s=zstats(Y1,109,ddof=1); print("  ddof=1 check g=1:", np.abs(np.array(fits[1]['z_std'])-s).max())

print("\n=== z_mean/z_std: L3.transf_params vs recomputed from L1 archive prefix ===")
e3=[]
for g in sorted(tp):
    n=fits[g]['n_treino']; m,s=zstats(Y1,n)
    e3.append(max(np.abs(np.array(tp[g]['mean'])-m).max(), np.abs(np.array(tp[g]['std'])-s).max()))
print(f"  max err: {max(e3):.4f} | g=1 {e3[0]:.2e} g=2 {e3[1]:.4f} g=200 {e3[-1]:.4f}")

print("\n=== SELF-CONSISTENCY of L3: archive built from L3's OWN flagged X (analytic ZDT4) ===")
sb=on[on.real_solution_id.notna()].sort_values("real_solution_id")
X3=sb[XC].values.astype(np.float64)
F3=zdt4(X3)
Ydoe=Y1[:109]
Y3=np.vstack([Ydoe,F3])
print("  archive rows:",Y3.shape)
e4=[];
for g in sorted(tp):
    n=fits[g]['n_treino']; m,s=zstats(Y3,n)
    e4.append(max(np.abs(np.array(tp[g]['mean'])-m).max(), np.abs(np.array(tp[g]['std'])-s).max()))
e4=np.array(e4)
print(f"  max err: {e4.max():.6f} | median {np.median(e4):.2e} | g=1 {e4[0]:.2e} g=2 {e4[1]:.2e} g=200 {e4[-1]:.2e}")
print(f"  gens with err<1e-4: {(e4<1e-4).sum()}/200 ; <5e-6: {(e4<5e-6).sum()}/200")
# how good is the mu prediction of the L3 flagged rows vs analytic f (U11 style)
mu=sb[["mu_0","mu_1"]].values
wape=np.abs(mu-F3).sum(0)/np.abs(F3).sum(0)
print("  WAPE(mu vs analytic f) of L3 flagged:",wape)
# same for L1/main-official picks vs L6 mu_sel
