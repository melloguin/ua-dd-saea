import json, glob, os, pandas as pd
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
rows=[]
for lab in ["q10_WFG9","q10_ZDT4"]:
    d=f"{R}/{lab}/42"
    objs=[json.loads(l) for l in open(glob.glob(d+"/*.jsonl")[0])]
    m=json.load(open([p for p in glob.glob(d+"/*.manifest.json") if not p.endswith("__final.manifest.json")][0]))
    pop=int(m["params"]["nsga2_interno"]["pop"])
    seq=[o for o in objs if o["rec"] in ("guard","decision")]
    pend=None
    for o in seq:
        if o["rec"]=="guard" and o["name"]=="lote_menor_que_q": pend=o
        elif o["rec"]=="guard" and o["name"]=="lote_completado_por" and pend is not None:
            rows.append(dict(cel=lab,pop=pop,n_front=pend["n_front"],n_lote=pend["n_lote"],q=pend["q"],
                n_completado=o["n_completado"],pool=o["n_pool_rank1mais"],valor=o["valor"]))
            pend=None
df=pd.DataFrame(rows); df["soma_ok"]=(df.n_lote+df.n_completado)==df.q
df["pool_ok"]=df.pool==(df["pop"]-df.n_front)
print(df.to_string(index=False))
print("\nPARES: %d | n_lote+n_completado==q: %d/%d | n_pool_rank1mais==pop-n_front: %d/%d | valor=='qmaximin': %d/%d"
      % (len(df),df.soma_ok.sum(),len(df),df.pool_ok.sum(),len(df),(df.valor=="qmaximin").sum(),len(df)))
print("n_front minimo:",df.n_front.min())
for lab in ["q10_WFG9","q10_ZDT4"]:
    m=json.load(open([p for p in glob.glob(f"{R}/{lab}/42/*.manifest.json") if not p.endswith("__final.manifest.json")][0]))
    ft=[json.loads(l) for l in open(glob.glob(f"{R}/{lab}/42/*.jsonl")[0])]
    f=[o for o in ft if o.get("rec")=="footer" and o.get("fe_final") is not None][0]
    print(f"  {lab}: footer n_lote_menor={f['n_lote_menor']} n_lote_completado={f['n_lote_completado']} (guards={len(df[df.cel==lab])})")
df.to_csv("t11_e81_di25_pares.csv",index=False)
