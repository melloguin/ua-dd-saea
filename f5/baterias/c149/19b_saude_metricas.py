"""SAUDE c149 (v2, ref_norm reusado por problema): IGD+ do DoE-so vs final + trajetorias."""
import os,sys,json
import numpy as np, pandas as pd, pyarrow.parquet as pq
REPO="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0,REPO); os.chdir(REPO)
from src import metrics
v=metrics.hv_smoke_bbob_f1(); assert abs(v-1.04333)<5e-6, v
print("gate D92 OK %.5f"%v,flush=True)
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT=REPO+"/f5/baterias/c149"
CACHE={}
def refn(prob):
    if prob not in CACHE: CACHE[prob]=metrics.reference_set(prob)
    return CACHE[prob]
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    hdr=json.loads(open(p+".jsonl").readline()); D=hdr["D"];M=hdr["M"]
    real=pq.read_table(p+"__real.parquet").to_pandas()
    F=real[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    n_init=int((real.fase=="init").sum())
    R=refn(prob)
    a=metrics.metrics_of_set(F[:n_init],prob,ref_norm=R)
    b=metrics.metrics_of_set(F,prob,ref_norm=R)
    traj=json.load(open(f"{REPO}/f5/trajetorias/{exp}_c149_{prob}_42.json"))
    ip=np.array([t["igd_plus"] for t in traj]); dif=np.diff(ip)
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,n_init=n_init,n_fe=len(F),
        igdp_doe=a["igd_plus"],igdp_final=b["igd_plus"],
        ganho_pct=100*(a["igd_plus"]-b["igd_plus"])/a["igd_plus"] if a["igd_plus"]>0 else 0.0,
        hv_doe=a["hv"],hv_final=b["hv"],nd_doe=a["n_nd"],nd_final=b["n_nd"],
        igd_doe=a["igd"],igd_final=b["igd"],
        traj_viol=int((dif>1e-12).sum()),traj_pior=float(dif.max()),traj_n=len(ip)-1,
        traj_ini=float(ip[0]),traj_fim=float(ip[-1])))
    print("%-6s %-10s IGD+ DoE %.5f -> final %.5f (ganho %+.2f%%) |ND| %d->%d viol=%d"%(
        exp,prob,a["igd_plus"],b["igd_plus"],rows[-1]["ganho_pct"],a["n_nd"],b["n_nd"],rows[-1]["traj_viol"]),flush=True)
df=pd.DataFrame(rows); df.to_csv(OUT+"/saude_c149.csv",index=False)
print("\nviolacoes de monotonicidade:",df.traj_viol.sum(),"de",df.traj_n.sum(),"transicoes; pior salto",df.traj_pior.max())
print("ganho mediano sobre o DoE: main %.2f%% | batch %.2f%%"%(df[df.exp=='main'].ganho_pct.median(),df[df.exp=='batch'].ganho_pct.median()))
print("celulas com ganho ZERO (<1e-9):",df[df.ganho_pct.abs()<1e-9][["exp","prob"]].to_dict("records"))
