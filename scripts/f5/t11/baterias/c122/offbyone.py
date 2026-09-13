import json
B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
recs=[json.loads(l) for l in open(B+".jsonl")]
snd={r["geracao"]:r for r in recs if r.get("rec")=="sonda"}
dec={r["geracao"]:r for r in recs if r.get("rec")=="decision"}
eq_g=eq_gm1=0; n=0; dif=[]
for g,r in sorted(snd.items()):
    a=sorted(map(int,r["ref_ids"])); n+=1
    b=sorted(map(int,dec[g]["ref_ids"])) if g in dec else None
    c=sorted(map(int,dec[g-1]["ref_ids"])) if (g-1) in dec else None
    eq_g+= (a==b); eq_gm1+= (a==c)
    if a!=b: dif.append(g)
print("sonda(g).ref_ids == decision(g).ref_ids  :",eq_g,"/",n)
print("sonda(g).ref_ids == decision(g-1).ref_ids:",eq_gm1,"/",n,"(g=1 nao tem decision(0))")
print("blocos em que a leitura LITERAL da REGRA daria outro conjunto:",len(dif),"->",dif)
# quantos membros mudam
import numpy as np
d=[]
for g in dif:
    a=set(map(int,snd[g]["ref_ids"])); b=set(map(int,dec[g]["ref_ids"]))
    d.append(len(a^b))
print("membros trocados por bloco (simetrica):",d)
