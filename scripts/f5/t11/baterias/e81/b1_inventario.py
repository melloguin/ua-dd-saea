import json, collections, glob, os
import pandas as pd
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    js=glob.glob(d+"/*.jsonl"); mf=[p for p in glob.glob(d+"/*.manifest.json") if not p.endswith("__final.manifest.json")]
    assert len(js)==1 and len(mf)==1, (lab,js,mf)
    objs=[json.loads(l) for l in open(js[0])]
    c=collections.Counter(o.get("rec") for o in objs)
    m=json.load(open(mf[0]))
    hdr=[o for o in objs if o.get("rec")=="header"]; ftr=[o for o in objs if o.get("rec")=="footer"]
    # T11 instrumentation presence
    rows.append(dict(label=lab, linhas=len(objs), header=c.get("header",0), footer=c.get("footer",0),
        decision=c.get("decision",0), fit=c.get("fit",0), sonda=c.get("sonda",0), guard=c.get("guard",0),
        checkpoint=c.get("checkpoint",0),
        recs_outros=";".join(sorted(set(c)-{"header","footer","decision","fit","sonda","guard","checkpoint"})),
        campanha_id=m.get("campanha_id","<AUSENTE>"), repo_hash=("SIM" if m.get("repo_hash") else "<AUSENTE>"),
        schema_version=m.get("schema_version","<AUSENTE>"),
        tempo_aval_real_s=m.get("timing",{}).get("tempo_aval_real_s","<AUSENTE>"),
        executable=("SIM" if m.get("env",{}).get("executable") else "<AUSENTE>"),
        upload_status=("SIM" if "upload_status" in m else "<AUSENTE>"),
        created=m.get("created_at"), updated=m.get("updated_at"),
        status=m.get("status"), motivo=m.get("motivo_parada"), fe_final=m.get("fe_final"), maxfe=m.get("maxfe"),
        n_ger=m.get("n_geracoes"), q=m.get("q")))
df=pd.DataFrame(rows)
df.to_csv("t11_e81_inventario_s42.csv",index=False)
pd.set_option("display.width",250); pd.set_option("display.max_columns",50)
print(df[["label","linhas","header","footer","decision","guard","checkpoint","campanha_id","repo_hash","schema_version","tempo_aval_real_s","executable"]].to_string(index=False))
print("\n--- anomalias header/footer !=(1,2) ---")
print(df[(df.header!=1)|(df.footer!=2)][["label","header","footer","linhas","created","updated"]].to_string(index=False))
print("\n--- totais ---")
print("decisions:",df.decision.sum()," fits:",df.fit.sum()," sondas:",df.sonda.sum()," guards:",df.guard.sum()," checkpoints:",df.checkpoint.sum())
print("outros recs:", set(df.recs_outros))
