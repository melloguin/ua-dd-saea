import json,os,sys
import pandas as pd, numpy as np
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
import src.problems as SP
from src.experiment import PROBLEM_CLASSES
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    hdr=json.loads(open(base+".jsonl").readline()); D=hdr['D']
    prob=getattr(SP,PROBLEM_CLASSES[p])(); xl=np.asarray(prob.xl,float); xu=np.asarray(prob.xu,float)
    xc=[f"x{i}" for i in range(D)]
    sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime']+xc)
    on=sur[sur.regime=='online'][xc].to_numpy(np.float64)
    real=pd.read_parquet(base+"__real.parquet",columns=xc).to_numpy(np.float64)
    tol=1e-5*np.maximum(1.0,np.abs(xu-xl))
    r=dict(problema=p,D=D,xl0=xl[0],xu0=xu[0],
        on_fora=int(((on<xl-tol)|(on>xu+tol)).sum()),on_n=on.size,
        real_fora=int(((real<xl-tol)|(real>xu+tol)).sum()),real_n=real.size,
        on_min=float((on-xl).min()),on_max=float((xu-on).min()),
        frac_no_bound=float(((np.abs(on-xl)<1e-6)|(np.abs(on-xu)<1e-6)).mean()))
    out.append(r); print(p,r['on_fora'],r['real_fora'],round(r['frac_no_bound'],4),flush=True)
    del sur
df=pd.DataFrame(out); df.to_csv("bounds_e7.csv",index=False)
pd.set_option('display.width',250); print(df.to_string())
print("\nTOT fora dos bounds: ③online",df.on_fora.sum(),"/",df.on_n.sum(),"| ①",df.real_fora.sum(),"/",df.real_n.sum())
print("fracao de coordenadas EXATAMENTE no bound (③ online):",round(float((df.frac_no_bound*df.on_n).sum()/df.on_n.sum()),4))
