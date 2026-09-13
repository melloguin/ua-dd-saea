"""CONTROLE: para cada par (main/P, q10_P) do c149, a geracao 1 e IDENTICA por construcao
(mesmo DoE de 11D-1, mesmas sementes internas, q so age a partir de g=2).
Se as duas execucoes sao do mesmo ambiente numerico, o bloco de SONDA g=1 da (3) tem de ser
BIT-IDENTICO entre main e batch."""
import json, numpy as np, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
pairs=[("ZDT1","q10_ZDT1"),("ZDT4","q10_ZDT4"),("DTLZ2","q10_DTLZ2"),("WFG9","q10_WFG9"),("MMF16_20","q10_MMF16_20")]
print(f"{'problema':12s} {'mu bit-igual':>13s} {'sig bit-igual':>13s} {'max|dmu|':>11s} {'rel_med(mu)':>12s} {'L6 val_mse g1 igual':>20s} {'L6 acq g1 igual':>16s}")
for pm,pb in pairs:
    A=pq.read_table(f"{R}/{pm}/42/exp_main_c149_{pm}_42__surrogate.parquet").to_pandas()
    B=pq.read_table(f"{R}/{pb}/42/exp_batch_c149_{pm}_42__surrogate.parquet").to_pandas()
    a=A[(A.regime=="sonda")&(A.geracao==1)].reset_index(drop=True)
    b=B[(B.regime=="sonda")&(B.geracao==1)].reset_index(drop=True)
    M=[c for c in A.columns if c.startswith("mu_")]; S=[c for c in A.columns if c.startswith("sigma_")]
    dmu=np.abs(a[M].values.astype(np.float64)-b[M].values.astype(np.float64))
    dsg=np.abs(a[S].values.astype(np.float64)-b[S].values.astype(np.float64))
    rel=np.median(dmu/np.maximum(np.abs(a[M].values.astype(np.float64)),1e-12))
    Ja=[json.loads(l) for l in open(f"{R}/{pm}/42/exp_main_c149_{pm}_42.jsonl")]
    Jb=[json.loads(l) for l in open(f"{R}/{pb}/42/exp_batch_c149_{pm}_42.jsonl")]
    fa=[r for r in Ja if r['rec']=='fit' and r['geracao']==1][0]
    fb=[r for r in Jb if r['rec']=='fit' and r['geracao']==1][0]
    da=[r for r in Ja if r['rec']=='decision' and r['geracao']==1][0]
    db=[r for r in Jb if r['rec']=='decision' and r['geracao']==1][0]
    acq_eq=all(da[k]==db[k] for k in ['acq_resF_mu_z_min','acq_resF_mu_z_max','acq_resF_sigma2_z_max','mu_sel_nat','sigma2_agg_sel_z','solution_id','seed_nsga2'])
    print(f"{pm:12s} {np.mean(dmu==0)*100:12.2f}% {np.mean(dsg==0)*100:12.2f}% {dmu.max():11.3e} {rel:12.3e} {str(fa['val_mse']==fb['val_mse']):>20s} {str(acq_eq):>16s}")
