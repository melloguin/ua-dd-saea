import json, os, glob
import numpy as np, pandas as pd
B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
mf=json.load(open(B+".manifest.json"))
print("== SMOKE: declaracoes que sobraram NOMINAIS ==")
print(" manifest.sonda.n_ref =",mf["sonda"]["n_ref"], "| referencia:",mf["sonda"]["referencia"])
print(" sigma_dict['regime=sonda'] =",mf["sigma_dict"]["regime=sonda"])
print(" timing:",json.dumps(mf["timing"],ensure_ascii=False))
print(" n_retries:",mf.get("n_retries"),"fallback:",mf.get("fallback_ativado"),"schema:",mf.get("schema_version"),"repo_hash:",mf.get("repo_hash"))
# ③ online do smoke: TOP-100 + argmax
recs=[json.loads(l) for l in open(B+".jsonl")]
dec=[r for r in recs if r.get("rec")=="decision"]
s=pd.read_parquet(B+"__surrogate.parquet",columns=["regime","geracao","pred_score","real_solution_id"])
on=s[s.regime=="online"]; cnt=on.groupby("geracao").size()
t=a=an=0
for e in dec:
    g=e["geracao"]; nc=e.get("n_cands") or 0
    t+= (int(cnt.get(g,0))==min(100,nc))
    ez=e.get("e_z_escolhido")
    if ez is not None:
        bl=on[on.geracao==g]; esc=bl[bl.real_solution_id.notna()]
        if len(esc)==1:
            an+=1; a+= (abs(float(esc.pred_score.iloc[0])-float(bl.pred_score.max()))<1e-4)
print("\n== SMOKE mecanismo: TOP-100 %d/%d · argmax %d/%d"%(t,len(dec),a,an))
print("   Q por categoria:",pd.Series([e['motivo'].split('categoria=')[1].split(' ')[0] for e in dec]).value_counts().to_dict())
print("   pool 7000 ok:",sum(1 for e in dec if e.get('n_acordo') is not None and e['n_acordo']+e['n_desacordo']==7000),
      "/",sum(1 for e in dec if e.get('n_acordo') is not None))
# s42: n_retries / tempo_aval_real
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122"
rt=[];tv=[]
for p in sorted(os.listdir(R)):
    b=glob.glob(f"{R}/{p}/42/*.manifest.json")
    if not b: continue
    m=json.load(open(b[0]))
    rt.append(m.get("n_retries")); tv.append((m["timing"] or {}).get("tempo_aval_real_s"))
print("\n== s42: n_retries distintos:",sorted(set(rt)),"| tempo_aval_real_s nao-nulo em",sum(1 for x in tv if x),"/",len(tv))
print("   soma tempo_aval_real_s = %.4f s ; total = %.1f s"%(sum(x for x in tv if x),sum(json.load(open(glob.glob(f'{R}/{p}/42/*.manifest.json')[0]))["timing"]["tempo_total_s"] for p in sorted(os.listdir(R)) if glob.glob(f'{R}/{p}/42/*.manifest.json'))))
