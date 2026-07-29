import json, pyarrow.parquet as pq
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
p="ZDT1"; base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
for lay in ["__real","__pop","__surrogate","__timing"]:
    sch=pq.read_schema(base+lay+".parquet")
    md=pq.ParquetFile(base+lay+".parquet").metadata
    print(lay, md.num_rows, "rows"); print("  ", [f"{n}:{t}" for n,t in zip(sch.names,sch.types)][:40])
sur=pd.read_parquet(base+"__surrogate.parquet")
print("\nregime counts:", sur.regime.value_counts().to_dict())
print(sur.head(3).T)
print("transf_params sample:", sur.transf_params.iloc[0], "|", sur.transf_params.iloc[-1])
ev=[json.loads(l) for l in open(base+".jsonl")]
from collections import Counter
print("\nrec counts:", Counter(e['rec'] for e in ev))
g=[e for e in ev if e['rec']=='e7_gen']
print("gen0 keys:", list(g[0].keys()))
print("gen0:", json.dumps({k:v for k,v in g[0].items() if k not in ('modelo_hp',)})[:1500])
print("modelo_hp:", json.dumps(g[0]['modelo_hp'])[:900])
print("footer:", json.dumps([e for e in ev if e['rec']=='footer'])[:1200])
print("guards:", json.dumps([e for e in ev if e['rec']=='guard'])[:600])
print("header:", json.dumps([e for e in ev if e['rec']=='header'])[:1500])
print("sonda ev:", json.dumps([e for e in ev if e['rec']=='sonda'][:1])[:600])
