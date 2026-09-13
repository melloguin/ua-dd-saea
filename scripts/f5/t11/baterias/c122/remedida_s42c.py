import json, os, glob
import pandas as pd
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122"
T={"prio_ok":0,"prio_n":0,"qmax_ok":0,"qmax_n":0,"cat":{"Q1":0,"Q2":0,"Q3":0,"None":0},
   "dist_pool_null":0,"dist_n":0,"nref_dec_eq_N":0,"nref_dec_n":0,"snd_blocos":0,"snd_linhas":0}
rows=[]
for prob in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,prob,"42")
    if not os.path.isdir(d): continue
    base=glob.glob(os.path.join(d,"*.manifest.json"))[0][:-len(".manifest.json")]
    mf=json.load(open(base+".manifest.json")); N=int(mf["params"]["N_MU"])
    dec=[json.loads(l) for l in open(base+".jsonl")]
    dec=[r for r in dec if r.get("rec")=="decision"]
    p_ok=p_n=q_ok=q_n=0
    for e in dec:
        cat=e["motivo"].split("categoria=")[1].split(" ")[0]
        q1,q2,q3,nc=e["n_q1"],e["n_q2"],e["n_q3"],(e.get("n_cands") or 0)
        T["cat"][cat]+=1
        ramo=e["caminho"].split(":")[1]
        if ramo=="categorias":
            p_n+=1
            esp="Q1" if q1>0 else "Q2" if q2>0 else "Q3" if q3>0 else "None"
            p_ok+= (esp==cat)
            sz={"Q1":q1,"Q2":q2,"Q3":q3}[cat]; q_n+=1; q_ok+= (nc==min(sz,300))
        else:
            T["dist_n"]+=1
            T["dist_pool_null"]+= (e.get("n_acordo") is None and e.get("pool_scf_max") is None)
            q_n+=1; q_ok+= (nc==min(q1,300))
        T["nref_dec_n"]+=1; T["nref_dec_eq_N"]+= (e.get("n_ref")==N)
    T["prio_ok"]+=p_ok; T["prio_n"]+=p_n; T["qmax_ok"]+=q_ok; T["qmax_n"]+=q_n
    rows.append(dict(prob=prob,prio=f"{p_ok}/{p_n}",qmax=f"{q_ok}/{q_n}"))
print(pd.DataFrame(rows).to_string()); print(T)
