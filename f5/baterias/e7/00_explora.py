import json, glob, os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
p="ZDT1"
base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
man=json.load(open(base+".manifest.json"))
print("MANIFEST keys:", list(man.keys()))
for k in ["status","maxfe","fe_final","n_geracoes","cache_hits","timing","sonda","upload_status"]:
    if k in man: print(" ",k,"=",json.dumps(man[k])[:600])
print("PARAMS:", json.dumps(man.get("params"),indent=0)[:2500])
print("SIGMA:", json.dumps(man.get("sigma_dict"),indent=0)[:2500])
