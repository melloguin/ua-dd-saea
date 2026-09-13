import sys,os,json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'); os.chdir('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
import numpy as np, pandas as pd
from src import metrics, standalone_harness as H
RES='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
out=[]
for prob in ["DTLZ2","MMF16_20","WFG9","ZDT1","ZDT4"]:
    xl,_=H._bounds(prob); D=len(xl); po=H._instantiate(prob); M=int(po.n_obj); n_init=11*D-1
    row={'problema':prob,'D':D}
    for alg in ['sobol_batch','e81','c149']:
        f=f'{RES}/{alg}/q10_{prob}/42/exp_batch_{alg}_{prob}_42__real.parquet'
        r=pd.read_parquet(f)
        F=r[[f'f{j}' for j in range(M)]].to_numpy().astype(np.float64)
        row[f'{alg}_doe']=metrics.metrics_of_set(F[:n_init],prob)['igd_plus']
        row[f'{alg}_fim']=metrics.metrics_of_set(F,prob)['igd_plus']
        row[f'{alg}_ganho%']=100*(row[f'{alg}_doe']-row[f'{alg}_fim'])/row[f'{alg}_doe']
    out.append(row); print(prob,'ok',flush=True)
d=pd.DataFrame(out); pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(d.to_string())
d.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/sobol_batch/ganho_sobre_doe.csv',index=False)
