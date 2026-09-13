import json, glob, os
A=json.load(open("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81/MMF1/42/exp_main_e81_MMF1_42.manifest.json"))
B=json.load(open("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0.manifest.json"))
print("=== TOP-LEVEL: s42 x smoke (valores escalares) ===")
for k in sorted(set(A)|set(B)):
    va,vb=A.get(k,"<CHAVE AUSENTE>"),B.get(k,"<CHAVE AUSENTE>")
    if isinstance(va,(dict,list)) or isinstance(vb,(dict,list)): continue
    if va!=vb: print(f"  {k:22s} s42={json.dumps(va)[:80]:45s} smoke={json.dumps(vb)[:80]}")
print("\n=== nota train_Yvar presente na s42? ===")
t=A["params"].get("train_Yvar","")
print(" s42  :", t)
print(" smoke:", B["params"].get("train_Yvar",""))
print("\n=== o mesmo texto nas 30 celulas da s42? ===")
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
tx=set(); sd=set(); sel=set()
for lab in sorted(os.listdir(R)):
    p=[q for q in glob.glob(f"{R}/{lab}/42/*.manifest.json") if not q.endswith("__final.manifest.json")]
    if not p: continue
    m=json.load(open(p[0])); tx.add(m["params"].get("train_Yvar")); sd.add(m["sigma_dict"].get("selecao")); sel.add(m["params"].get("receita"))
print(" train_Yvar distintos:",len(tx)," receita distintas:",len(sel)," selecao distintas:",len(sd))
print("\n=== CHECKPOINT (rec novo do smoke, G5) ===")
S="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0.jsonl"
for o in [json.loads(l) for l in open(S)]:
    if o.get("rec")=="checkpoint": print(" ", json.dumps(o))
