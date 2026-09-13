import json, sys
import numpy as np, pandas as pd
B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
mf=json.load(open(B+".manifest.json"))
print("== MANIFESTO chaves:", sorted(mf.keys()))
print("status",mf.get("status"),"motivo",mf.get("motivo_parada"),"fe_final",mf.get("fe_final"),"maxfe",mf.get("maxfe"),"n_ger",mf.get("n_geracoes"))
print("campanha_id" in json.dumps(mf), mf.get("campanha_id"))
print("SONDA:",json.dumps(mf.get("sonda"),ensure_ascii=False)[:600])
print("SIGMA keys:",list(mf.get("sigma_dict",{}).keys()))
print("REGRA_DO_ROTULO presente:", "REGRA_DO_ROTULO" in mf.get("sigma_dict",{}))
print("PARAMS keys:",list(mf.get("params",{}).keys()))
recs=[json.loads(l) for l in open(B+".jsonl")]
from collections import Counter
print("== JSONL recs:",Counter(r.get("rec") for r in recs))
