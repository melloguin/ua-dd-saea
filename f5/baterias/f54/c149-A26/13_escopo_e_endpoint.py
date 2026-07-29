import os,glob,json,hashlib,numpy as np,pyarrow.parquet as pq,csv
MREPO="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments"
CONS="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
# ---------- (A) escopo: quantas celulas tem 2a execucao (manifesto MAC/data-antigo) divergente ----------
rows=[]
for mf in glob.glob(f"{MREPO}/*/*/*.manifest.json"):
    if "__final" in mf: continue
    b=os.path.basename(mf)[:-len(".manifest.json")]
    try: m=json.load(open(mf))
    except Exception: continue
    ex=m.get("env",{}).get("executable",""); host="MAC" if ex.startswith("/Users") else "VM"
    alg=m.get("alg"); prob=m.get("problema"); exp=m.get("exp"); sem=m.get("semente")
    lab=("q10_" if exp=="batch" else "")+str(prob)
    cons=f"{CONS}/{alg}/{lab}/{sem}/{b}.manifest.json"
    if not os.path.exists(cons):
        rows.append(dict(alg=alg,exp=exp,prob=prob,host=host,created=m.get("created_at"),estado="sem_consolidada")); continue
    mc=json.load(open(cons))
    same = (mc.get("created_at")==m.get("created_at"))
    if not same:
        rows.append(dict(alg=alg,exp=exp,prob=prob,host=host,created=m.get("created_at"),
                         created_cons=mc.get("created_at"),estado="DUPLA_EXECUCAO"))
print("[A] manifestos locais no repo:",len(glob.glob(f'{MREPO}/*/*/*.manifest.json')))
dup=[r for r in rows if r["estado"]=="DUPLA_EXECUCAO"]
print("    celulas com 2a execucao DIVERGENTE da consolidada:",len(dup))
for r in dup: print("     ",r)
print("    sem consolidada:",sum(1 for r in rows if r['estado']=='sem_consolidada'))
with open("escopo_dupla_execucao.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["alg","exp","prob","host","created","created_cons","estado"]); w.writeheader()
    for r in rows: w.writerow({k:r.get(k,"") for k in w.fieldnames})
# ---------- (B) endpoint: as duas execucoes concordam no resultado? ----------
def nd(Y):
    keep=np.ones(len(Y),bool)
    for i in range(len(Y)):
        if not keep[i]: continue
        dom=np.all(Y<=Y[i],1)&np.any(Y<Y[i],1)
        if dom.any(): keep[i]=False
    return keep
for nome,p in [("v6 (consolidada)",f"{CONS}/c149/q10_ZDT4/42/exp_batch_c149_ZDT4_42__real.parquet"),
               ("MAC 2026-07-24",f"{MREPO}/batch/c149/exp_batch_c149_ZDT4_42__real.parquet")]:
    R=pq.read_table(p).to_pandas().sort_values("solution_id")
    Y=R[["f0","f1"]].values.astype(float)
    k=nd(Y); k0=nd(Y[:109])
    setF={tuple(np.round(r,5)) for r in Y[k]}; set0={tuple(np.round(r,5)) for r in Y[:109][k0]}
    print(f"[B] {nome:18s} |ND_final|={k.sum():3d} |ND_DoE|={k0.sum():3d} ND_final==ND_DoE? {setF==set0} min f0={Y[:,0].min():.5f} min f1={Y[:,1].min():.4f}")
