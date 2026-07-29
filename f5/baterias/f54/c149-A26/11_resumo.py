import json, numpy as np, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
XC=[f"x{i}" for i in range(10)]
def zdt4(X):
    X=np.asarray(X,float); f1=X[:,0]
    g=1+10*(X.shape[1]-1)+np.sum(X[:,1:]**2-10*np.cos(4*np.pi*X[:,1:]),axis=1)
    return np.column_stack([f1,g*(1-np.sqrt(f1/g))])
p=f"{R}/q10_ZDT4/42/exp_batch_c149_ZDT4_42"
L1=pq.read_table(p+"__real.parquet").to_pandas().sort_values("solution_id")
L3=pq.read_table(p+"__surrogate.parquet").to_pandas()
J=[json.loads(l) for l in open(p+".jsonl")]
fit={r['geracao']:r for r in J if r['rec']=='fit'}
on=L3[L3.regime=="online"]
tp={g:json.loads(s) for g,s in on.groupby("geracao").transf_params.first().items()}
sb=on[on.real_solution_id.notna()].sort_values("real_solution_id")
Y3=np.vstack([L1[["f0","f1"]].values[:109], zdt4(sb[XC].values.astype(np.float64))])
Y1=L1[["f0","f1"]].values
def err(Y,src):
    e=[]
    for g in sorted(tp):
        n=fit[g]['n_treino']; A=Y[:n]
        e.append(max(np.abs(np.array(tp[g]['mean'])-A.mean(0)).max(),
                     np.abs(np.array(tp[g]['std'])-A.std(0)).max()))
    return np.array(e)
eA=err(Y3,"L3-own"); eB=err(Y1,"L1")
res={
 "L3_transf_vs_arquivo_reconstruido_do_PROPRIO_L3": {"max":float(eA.max()),"mediana":float(np.median(eA)),"gens_lt_5e-6":int((eA<5e-6).sum())},
 "L3_transf_vs_arquivo_da_camada1": {"max":float(eB.max()),"mediana":float(np.median(eB)),"gens_lt_5e-6":int((eB<5e-6).sum())},
 "n_geracoes":len(tp)}
json.dump(res,open("evidencia_selfconsistencia.json","w"),indent=1)
print(json.dumps(res,indent=1))
