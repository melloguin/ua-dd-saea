import json,os,hashlib,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
pb=f"{ROOT}/q10_ZDT4/42/exp_batch_c149_ZDT4_42__surrogate.parquet"
pm=f"{ROOT}/ZDT4/42/exp_main_c149_ZDT4_42__surrogate.parquet"
print("bytes batch:",os.path.getsize(pb)," main:",os.path.getsize(pm))
def sha(f):
    h=hashlib.sha256()
    with open(f,'rb') as fh:
        for c in iter(lambda: fh.read(1<<20), b''): h.update(c)
    return h.hexdigest()[:16]
print("sha batch",sha(pb),"main",sha(pm))
B=pq.read_table(pb).to_pandas(); Mn=pq.read_table(pm).to_pandas()
print("linhas",len(B),len(Mn))
print("iguais col a col?", all(B.columns==Mn.columns))
for c in ["x0","x1","mu_0","mu_1","sigma_0","transf_params","real_solution_id","fe_treino_max","geracao","regime"]:
    if len(B)==len(Mn):
        if B[c].dtype==object: eq=(B[c].fillna("_")==Mn[c].fillna("_")).mean()
        else: eq=np.isclose(B[c].values,Mn[c].values,equal_nan=True).mean()
        print(f"  {c}: igual em {eq*100:.2f}%")
# transf_params do batch bate com o fit do MAIN?
fits={}
for line in open(f"{ROOT}/ZDT4/42/exp_main_c149_ZDT4_42.jsonl"):
    d=json.loads(line)
    if d["rec"]=="fit": fits[d["geracao"]]=(np.array(d["z_mean"]),np.array(d["z_std"]))
errs=[]
for (reg,g),sub in B.groupby(["regime","geracao"]):
    tp=json.loads(sub.transf_params.iloc[0]); zm,zs=fits[g]
    errs.append(max(np.abs(np.array(tp["mean"])-zm).max(),np.abs(np.array(tp["std"])-zs).max()))
print("③ do q10_ZDT4 vs fit do MAIN/ZDT4: err max =",max(errs))
# real_solution_id do batch: quantos e quais
sb=B[(B.regime=="online")&(B.real_solution_id.notna())]
print("③ q10_ZDT4: n flagged",len(sb),"por geracao:",sb.groupby("geracao").size().unique(),"sid range",sb.real_solution_id.min(),sb.real_solution_id.max())
sm=Mn[(Mn.regime=="online")&(Mn.real_solution_id.notna())]
print("③ main/ZDT4: n flagged",len(sm),"sid range",sm.real_solution_id.min(),sm.real_solution_id.max())
# fe_treino_max
print("fe_treino_max batch por ger:",B[B.regime=="online"].groupby("geracao").fe_treino_max.first().values[:6],"... main:",Mn[Mn.regime=="online"].groupby("geracao").fe_treino_max.first().values[:6])
