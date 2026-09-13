import json, collections
import pandas as pd, pyarrow.parquet as pq
S="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0"
objs=[json.loads(l) for l in open(S+".jsonl")]
print("linhas jsonl:", len(objs))
c=collections.Counter(o.get("rec") for o in objs)
print("rec:", dict(c))
hdr=[o for o in objs if o.get("rec")=="header"]; ftr=[o for o in objs if o.get("rec")=="footer"]
print("\n=== HEADER (%d) ===" % len(hdr))
print(json.dumps({k:(v if not isinstance(v,(dict,list)) else f"<{type(v).__name__} len={len(v)}>") for k,v in hdr[0].items()}, indent=1)[:2500])
print("\n=== FOOTERS (%d) ===" % len(ftr))
for f in ftr: print(" ", json.dumps(f)[:700])
dec=[o for o in objs if o.get("rec")=="decision"]
print("\n=== DECISION[0] keys ===", sorted(dec[0].keys()))
print(json.dumps(dec[0])[:2200])
fit=[o for o in objs if o.get("rec")=="fit"]
print("\n=== FIT[0] ===", json.dumps(fit[0])[:1500])
snd=[o for o in objs if o.get("rec")=="sonda"]
print("\n=== SONDA[0] ===", json.dumps(snd[0])[:900])
grd=[o for o in objs if o.get("rec")=="guard"]
print("\n=== GUARD (%d) ===" % len(grd))
for g in grd[:4]: print(" ", json.dumps(g)[:400])
