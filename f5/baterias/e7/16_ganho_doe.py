import json,os,sys
import pandas as pd, numpy as np
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import metrics as MT
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
print("gate D92 HV smoke:",round(MT.hv_smoke_bbob_f1(),5))
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    hdr=json.loads(open(base+".jsonl").readline()); D=hdr['D']; M=hdr['M']; n0=11*D-1
    real=pd.read_parquet(base+"__real.parquet")
    F=real[[f"f{i}" for i in range(M)]].to_numpy(np.float64)
    ref=MT.reference_set(p)
    m_doe=MT.metrics_of_set(F[:n0],p,ref_norm=ref)
    m_fin=MT.metrics_of_set(F,p,ref_norm=ref)
    out.append(dict(problema=p,D=D,M=M,igd_doe=m_doe['igd_plus'],igd_fin=m_fin['igd_plus'],
        ganho=(m_doe['igd_plus']-m_fin['igd_plus'])/m_doe['igd_plus'] if m_doe['igd_plus'] else np.nan,
        nd_doe=m_doe['n_nd'],nd_fin=m_fin['n_nd'],hv_doe=m_doe['hv'],hv_fin=m_fin['hv']))
    print(p,round(out[-1]['ganho'],4),flush=True)
df=pd.DataFrame(out); df.to_csv("ganho_doe_e7.csv",index=False)
pd.set_option('display.width',250); print(df.round(4).to_string())
print("\nganho mediano sobre o DoE:",round(df.ganho.median(),4),"| celulas com ganho ~0:",int((df.ganho<1e-6).sum()),
      "| min",round(df.ganho.min(),4),"max",round(df.ganho.max(),4))
