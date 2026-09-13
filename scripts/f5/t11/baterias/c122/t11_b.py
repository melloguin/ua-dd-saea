import json
import numpy as np, pandas as pd
B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
recs=[json.loads(l) for l in open(B+".jsonl")]
snd=[r for r in recs if r.get("rec")=="sonda"]
est=[r for r in recs if r.get("rec")=="sonda_estratificada"]
dec=[r for r in recs if r.get("rec")=="decision"]
print("== SONDA rec[0]:",json.dumps({k:(v if k!="ref_ids" else v) for k,v in snd[0].items()},ensure_ascii=False)[:1200])
print()
print("== SONDA: n_ref por geracao:",[(r["geracao"],r.get("n_ref"),r.get("n_ref_nominal"),r.get("n_ref_truncada"),len(r.get("ref_ids") or [])) for r in snd])
print()
print("ref_ids SENTINELA? min/max de todos:", [ (min(r["ref_ids"]),max(r["ref_ids"])) for r in snd[:3]], "...")
allids=[i for r in snd for i in (r.get("ref_ids") or [])]
print("total ids sonda:",len(allids),"negativos:",sum(1 for i in allids if i<0),"distintos:",len(set(allids)))
print()
print("== ESTRAT rec[0]:",json.dumps(est[0],ensure_ascii=False)[:1000])
print("prevalencias:",[round(r.get("prevalencia_nd_no_bloco"),4) if r.get("prevalencia_nd_no_bloco") is not None else None for r in est])
print("n_pontos:",sorted(set(r["n_pontos"] for r in est)), "n_arquivo:",[r["n_arquivo"] for r in est][:6],"...")
print()
d0=dec[0]
print("== DECISION rec[0] chaves:",sorted(d0.keys()))
print("n_ref/n_ref_nominal:",[(r["geracao"],r.get("n_ref"),r.get("n_ref_nominal"),len(r.get("ref_ids") or [])) for r in dec[:6]],"...")
ids_dec=[i for r in dec for i in (r.get("ref_ids") or [])]
print("total ids decision:",len(ids_dec),"negativos:",sum(1 for i in ids_dec if i<0))
print("y_treino_dist_p[0]:",json.dumps(d0.get("y_treino_dist_p"),ensure_ascii=False))
print("y_treino_dist_s[0]:",json.dumps(d0.get("y_treino_dist_s"),ensure_ascii=False))
print("y_treino_dist_p ultimo:",json.dumps(dec[-1].get("y_treino_dist_p"),ensure_ascii=False))
