import json, glob
A=json.load(open("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81/MMF1/42/exp_main_e81_MMF1_42.manifest.json"))
B=json.load(open("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0.manifest.json"))
def dif(a,b,pre=""):
    out=[]
    for k in sorted(set(a)|set(b)):
        va,vb=a.get(k,"<AUSENTE>"),b.get(k,"<AUSENTE>")
        if isinstance(va,dict) and isinstance(vb,dict): out+=dif(va,vb,pre+k+".")
        elif va!=vb: out.append((pre+k,va,vb))
    return out
for nome in ["params","sigma_dict"]:
    print(f"===== {nome}: s42(MMF1/42) x smoke T11(MMF1/0) =====")
    d=dif(A.get(nome,{}),B.get(nome,{}))
    if not d: print("  IDENTICOS (byte a byte)")
    for k,va,vb in d: print(f"  {k}\n     s42  : {json.dumps(va)[:300]}\n     smoke: {json.dumps(vb)[:300]}")
print("\n===== chaves de manifesto novas no smoke =====")
print(" so no smoke:", sorted(set(B)-set(A)))
print(" so na s42  :", sorted(set(A)-set(B)))
print("\n===== timing =====")
print(" s42  :", json.dumps(A.get("timing")))
print(" smoke:", json.dumps(B.get("timing")))
print("\n===== sigma_dict do smoke (integral) =====")
print(json.dumps(B.get("sigma_dict"), indent=1, ensure_ascii=False)[:3000])
print("\n===== params do smoke (integral) =====")
print(json.dumps(B.get("params"), indent=1, ensure_ascii=False)[:2500])
