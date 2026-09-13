import json, sys, os
import pandas as pd, pyarrow.parquet as pq
S="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0"
m=json.load(open(S+".manifest.json"))
print("=== TOP-LEVEL KEYS ===")
print(sorted(m.keys()))
for k in ["campanha_id","repo_hash","status","motivo_parada","maxfe","fe_final","n_geracoes","created_at","updated_at","schema_version","schema","executable","host"]:
    if k in m: print(f"  {k} = {json.dumps(m[k])[:200]}")
print("=== env/timing/sonda ===")
for k in ["env","timing","sonda","fit_series"]:
    if k in m:
        v=m[k]
        print(f"  {k}: {json.dumps(v)[:600]}")
