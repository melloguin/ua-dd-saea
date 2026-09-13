import json, pandas as pd, pyarrow.parquet as pq
base="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149/ZDT1/42/"
p=base+"exp_main_c149_ZDT1_42"
m=json.load(open(p+".manifest.json"))
print("MANIFEST KEYS:", list(m.keys()))
for k,v in m.items():
    s=json.dumps(v)
    print(f"--- {k} ({len(s)} chars)")
    if len(s)<3000: print(s)
    else: print(s[:2500],"...")
