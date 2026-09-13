"""PROVA FINAL: a (3) consolidada pertence a (1) do run do MAC (2026-07-24), nao a (1) da v6."""
import numpy as np, pyarrow.parquet as pq, json
XC=[f"x{i}" for i in range(10)]
CON="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149/q10_ZDT4/42/exp_batch_c149_ZDT4_42"
MAC="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/batch/c149/exp_batch_c149_ZDT4_42"
S=pq.read_table(CON+"__surrogate.parquet").to_pandas()
s=S[(S.regime=="online")&(S.real_solution_id.notna())].sort_values("real_solution_id")
sid=s.real_solution_id.astype(int).values; X3=s[XC].values
for nome,path in [("(1) v6 (consolidada)",CON),("(1) MAC 2026-07-24",MAC)]:
    R=pq.read_table(path+"__real.parquet").to_pandas().set_index("solution_id")
    X1=R.loc[sid,XC].values
    d=np.abs(X3-X1)
    print(f"  X da (3) vs {nome:24s}: bit-exato {int((d.max(1)==0).sum())}/{len(sid)}  max|dX|={d.max():.6f}")
# tambem: transf_params da (3) vs z_mean/z_std do (6) do MAC
J=[json.loads(l) for l in open(MAC+".jsonl")]
fit={r['geracao']:r for r in J if r['rec']=='fit'}
dec={r['geracao']:r for r in J if r['rec']=='decision'}
on=S[S.regime=="online"]
tp={g:json.loads(x) for g,x in on.groupby("geracao").transf_params.first().items()}
e=[max(np.abs(np.array(tp[g]['mean'])-np.array(fit[g]['z_mean'])).max(),
       np.abs(np.array(tp[g]['std'])-np.array(fit[g]['z_std'])).max()) for g in sorted(tp)]
print(f"  transf_params(3) vs z_*(6-MAC): max={max(e):.3e} mediana={np.median(e):.3e} em {len(e)} geracoes")
# acq_resF do (6) MAC reconstituido da (3)
ok=0; errs=[]
for g in sorted(dec)[:200]:
    sub=on[on.geracao==g]; t=tp[g]
    mu=sub[["mu_0","mu_1"]].values.astype(np.float64); sg=sub[["sigma_0","sigma_1"]].values.astype(np.float64)
    m=np.array(t['mean']); sd=np.array(t['std'])
    muz=(mu-m)/sd; s2z=(sg/sd)**2
    e1=np.abs(muz.max(0)-np.array(dec[g]['acq_resF_mu_z_max'])).max()
    e2=np.abs(muz.min(0)-np.array(dec[g]['acq_resF_mu_z_min'])).max()
    e3=np.abs(s2z.max(0)-np.array(dec[g]['acq_resF_sigma2_z_max'])).max()
    errs.append(max(e1,e2,e3)); ok+= max(e1,e2,e3)<5.7e-6
print(f"  acq_resF(6-MAC) reconstituido da (3): {ok}/200 geracoes com erro<=5,7e-6 (max={max(errs):.2e})")
# lote de 10: solution_ids do (6) MAC vs real_solution_id da (3)
bad=0
for g in sorted(dec):
    a=sorted(dec[g]['lote_solution_ids']); b=sorted(on[(on.geracao==g)&(on.real_solution_id.notna())].real_solution_id.astype(int).tolist())
    bad+= (a!=b)
print(f"  lote_solution_ids(6-MAC) == real_solution_id(3) em {200-bad}/200 geracoes")
