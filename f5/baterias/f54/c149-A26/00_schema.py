import pyarrow.parquet as pq, json, os
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
for cell,pref in [("q10_ZDT4","exp_batch_c149_ZDT4_42"),("ZDT4","exp_main_c149_ZDT4_42")]:
    for lay in ["real","pop","surrogate","timing"]:
        p=f"{R}/{cell}/42/{pref}__{lay}.parquet"
        t=pq.read_schema(p); md=pq.ParquetFile(p).metadata
        print(cell,lay,md.num_rows,"rows |",list(t.names))
    print()
# jsonl record types
from collections import Counter
for cell,pref in [("q10_ZDT4","exp_batch_c149_ZDT4_42"),("ZDT4","exp_main_c149_ZDT4_42")]:
    c=Counter(); first={}
    for line in open(f"{R}/{cell}/42/{pref}.jsonl"):
        d=json.loads(line); c[d.get("rec")]+=1
        first.setdefault(d.get("rec"),d)
    print(cell,dict(c))
    for k,v in first.items():
        print("   ",k,"->",sorted(v.keys()))
