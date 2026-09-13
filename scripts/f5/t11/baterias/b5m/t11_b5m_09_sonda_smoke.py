"""Regua Sobol no SMOKE T11 (off/b5m/MMF1/s0) vs a MESMA regua na s42 (MMF1/s42)."""
import numpy as np, pandas as pd, pyarrow.parquet as pq, glob, json, os
DATA="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data"
def bloco(base):
    sg=pq.read_table(base+"__surrogate.parquet").to_pandas()
    so=sg[sg.regime=="sonda"]
    xs=[c for c in sg.columns if c.startswith("x")]; mus=[c for c in sg.columns if c.startswith("mu_")]
    sis=[c for c in sg.columns if c.startswith("sigma_")]
    m=json.load(open(base+".manifest.json"))
    S=pq.read_table(os.path.join(DATA,"sonda","sonda_%s.parquet"%m["problema"])).to_pandas()
    fs=[c for c in S.columns if c.startswith("f")][:len(mus)]
    sx=[c for c in S.columns if c.startswith("x")][:len(xs)]
    dX=float(np.abs(S[sx].values[:len(so)].astype(np.float32)-so[xs].values.astype(np.float32)).max())
    out=[]
    for j,(mu,si,f) in enumerate(zip(mus,sis,fs)):
        M=so[mu].values.astype(float); Sg=so[si].values.astype(float); F=S[f].values[:len(so)].astype(float)
        out.append(dict(obj=j, wape=float(np.abs(M-F).sum()/np.abs(F).sum()),
                        corr=float(np.corrcoef(M,F)[0,1]), cob95=float((np.abs(M-F)<=1.96*Sg).mean()),
                        sigma_nan=int(np.isnan(Sg).sum()), n=len(so)))
    return dX, pd.DataFrame(out), m
for tag, base in [("smoke T11 MMF1/s0","/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/off/b5m/exp_off_b5m_MMF1_0"),
                  ("s42 MMF1/s42", glob.glob("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m/MMF1/42/*__surrogate.parquet")[0][:-len("__surrogate.parquet")])]:
    dX,df,m=bloco(base)
    print("== %-20s join posicional max|ΔX|=%.3g  n_pontos=%d  wall=%.1f s"%(tag,dX,df.n.iloc[0],m["timing"]["tempo_total_s"]))
    print(df.round(6).to_string(index=False))
