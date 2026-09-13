import json, pandas as pd, pyarrow.parquet as pq, collections
base="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149/ZDT1/42/"
p=base+"exp_main_c149_ZDT1_42"
for lay in ["real","pop","surrogate","timing"]:
    f=pq.ParquetFile(p+f"__{lay}.parquet")
    print(f"=== {lay}: {f.metadata.num_rows} linhas")
    print("   cols:", [c for c in f.schema_arrow.names])
    print("   types:", {n:str(t) for n,t in zip(f.schema_arrow.names, f.schema_arrow.types)})
print("=== JSONL eventos")
cnt=collections.Counter(); first={}
for line in open(p+".jsonl"):
    line=line.strip()
    if not line: continue
    try: d=json.loads(line)
    except Exception as e: cnt["__PARSE_FAIL__"]+=1; continue
    k=d.get("rec", d.get("evento","?"))
    cnt[k]+=1
    if k not in first: first[k]=d
for k,v in cnt.most_common():
    print(f"--- {k}: {v}")
    print("   ", json.dumps(first[k])[:1400])
