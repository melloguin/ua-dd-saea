"""SAUDE EM ESCALA c149: (a) IGD+ do DoE-so vs final (ganho atribuivel ao mecanismo);
(b) trajetorias 20 checkpoints (violacoes de monotonicidade); (c) posicao vs pisos;
(d) sonda F5.2e. Usa src/metrics.py OFICIAL (gate D92)."""
import os,sys,json,csv
import numpy as np, pandas as pd, pyarrow.parquet as pq
REPO="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0,REPO); os.chdir(REPO)
from src import metrics
v=metrics.hv_smoke_bbob_f1(); assert abs(v-1.04333)<5e-6, v
print("gate D92 OK %.5f"%v)
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT=REPO+"/f5/baterias/c149"
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
    m_doe=metrics.metrics_of_set(F[:n_init],prob)
    m_fin=metrics.metrics_of_set(F,prob)
    traj=json.load(open(f"{REPO}/f5/trajetorias/{exp}_c149_{prob}_42.json"))
    ip=np.array([t["igd_plus"] for t in traj]); fe=np.array([t["fe"] for t in traj])
    dif=np.diff(ip); viol=int((dif>1e-12).sum()); pior=float(dif.max())
    rows.append(dict(exp=exp,prob=prob,D=D,M=M,n_init=n_init,n_fe=len(F),
        igdp_doe=m_doe["igd_plus"],igdp_final=m_fin["igd_plus"],
        ganho_pct=100*(m_doe["igd_plus"]-m_fin["igd_plus"])/m_doe["igd_plus"] if m_doe["igd_plus"]>0 else 0.0,
        hv_doe=m_doe["hv"],hv_final=m_fin["hv"],nd_doe=m_doe["n_nd"],nd_final=m_fin["n_nd"],
        traj_viol=viol,traj_pior_salto=pior,traj_n=len(ip)-1,
        traj_ini=float(ip[0]),traj_fim=float(ip[-1]),
        melhora_traj_pct=100*(ip[0]-ip[-1])/ip[0] if ip[0]>0 else 0.0))
    print(rows[-1]["exp"],rows[-1]["prob"],"IGD+ DoE %.4f -> final %.4f (ganho %.2f%%) viol=%d"%(
        m_doe["igd_plus"],m_fin["igd_plus"],rows[-1]["ganho_pct"],viol),flush=True)
df=pd.DataFrame(rows); df.to_csv(OUT+"/saude_c149.csv",index=False)
print("\n=== resumo ganho sobre o DoE (main, 25) ===")
mm=df[df.exp=="main"].sort_values("ganho_pct")
print(mm[["prob","D","M","igdp_doe","igdp_final","ganho_pct","nd_doe","nd_final","traj_viol"]].to_string(index=False))
print("\n=== batch ===")
print(df[df.exp=="batch"][["prob","D","M","igdp_doe","igdp_final","ganho_pct","nd_doe","nd_final","traj_viol"]].to_string(index=False))
print("\nviolacoes totais:",df.traj_viol.sum(),"de",df.traj_n.sum(),"transicoes; pior salto",df.traj_pior_salto.max())
