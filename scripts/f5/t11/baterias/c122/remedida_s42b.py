import json, os, glob
import numpy as np, pandas as pd
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122"
tot={"prio_ok":0,"prio_n":0,"qmax_ok":0,"qmax_n":0,"nref_dec_eq_N":0,"nref_dec_n":0,
     "q1":0,"q2":0,"q3":0,"qN":0,"top100_ok":0,"top100_n":0,"argmax_ok":0,"argmax_n":0}
rows=[]
for prob in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,prob,"42")
    if not os.path.isdir(d): continue
    base=glob.glob(os.path.join(d,"*.manifest.json"))[0][:-len(".manifest.json")]
    mf=json.load(open(base+".manifest.json")); N=int(mf["params"]["N_MU"])
    recs=[json.loads(l) for l in open(base+".jsonl")]
    dec=[r for r in recs if r.get("rec")=="decision"]
    s=pd.read_parquet(base+"__surrogate.parquet",columns=["regime","geracao","pred_score","real_solution_id"])
    on=s[s.regime=="online"]
    cnt=on.groupby("geracao").size()
    p_ok=q_ok=t_ok=a_ok=0; t_n=a_n=0
    for e in dec:
        cat=(e.get("motivo") or "").split("categoria=")[1].split(" ")[0]
        q1,q2,q3=e.get("n_q1"),e.get("n_q2"),e.get("n_q3")
        esp=("None" if q1 is None else ("Q1" if q1>0 else "Q2" if q2>0 else "Q3" if q3>0 else "None"))
        p_ok+= (esp==cat); tot["q"+cat[-1] if cat!="None" else "qN"]+=1
        if q1 is not None:
            sz={"Q1":q1,"Q2":q2,"Q3":q3}.get(cat,0)
            q_ok+= (e.get("n_cands")==min(sz,300))
        g=e["geracao"]; nc=e.get("n_cands") or 0
        t_n+=1; t_ok+= (int(cnt.get(g,0))==min(100,nc))
        tot["nref_dec_n"]+=1; tot["nref_dec_eq_N"]+= (e.get("n_ref")==N)
        ez=e.get("e_z_escolhido")
        if ez is not None:
            bl=on[on.geracao==g]
            esc=bl[bl.real_solution_id.notna()]
            if len(esc)==1:
                a_n+=1
                a_ok+= (abs(float(esc.pred_score.iloc[0])-float(bl.pred_score.max()))<1e-4
                        and abs(float(esc.pred_score.iloc[0])-ez)<1e-3)
    tot["prio_ok"]+=p_ok; tot["prio_n"]+=len(dec); tot["qmax_ok"]+=q_ok
    tot["qmax_n"]+=sum(1 for e in dec if e.get("n_q1") is not None)
    tot["top100_ok"]+=t_ok; tot["top100_n"]+=t_n; tot["argmax_ok"]+=a_ok; tot["argmax_n"]+=a_n
    rows.append(dict(prob=prob,prio=f"{p_ok}/{len(dec)}",qmax=f"{q_ok}/{sum(1 for e in dec if e.get('n_q1') is not None)}",
                     top100=f"{t_ok}/{t_n}",argmax=f"{a_ok}/{a_n}"))
    print(rows[-1])
print("TOTAIS:",tot)
pd.DataFrame(rows).to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c122/remedida_s42_identidades.csv",index=False)
