# -*- coding: utf-8 -*- READ-ONLY. WAPE MEDIANO sobre TODOS os blocos da regua Sobol (robusto ao ultimo bloco).
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT=f'{ROOT}/ua-dd-saea/f5/t11/baterias/e74'
rows=[]
for prob in ['MMF1','DTLZ2','ZDT1']:
    gab=pd.read_parquet(f'{ROOT}/ua-dd-saea/data/sonda/sonda_{prob}.parquet')
    fcg=[c for c in gab.columns if c.startswith('f') and c[1:].isdigit()]
    Fg=gab[fcg].values[:2000].astype(np.float64); M=Fg.shape[1]
    den=np.abs(Fg).sum(axis=0)
    for tag,base in [('PRE_s42',f'{ROOT}/resultados_experimentos/e74/{prob}/42/exp_main_e74_{prob}_42'),
                     ('POS_smoke',f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{prob}_42')]:
        s=pd.read_parquet(base+'__surrogate.parquet',columns=['regime','geracao','modelo_flag']+[f'mu_{i}' for i in range(M)])
        sd=s[(s.regime=='sonda')&(s.modelo_flag!='PNN(s1)')]
        for mf,g in sd.groupby('modelo_flag'):
            ws=[]
            for gr,b in g.groupby('geracao'):
                mu=b[[f'mu_{i}' for i in range(M)]].values.astype(np.float64)
                ws.append(np.median([np.abs(mu[:,j]-Fg[:,j]).sum()/den[j] for j in range(M)]))
            ws=np.array(ws)
            rows.append(dict(problema=prob,corpus=tag,cabeca=mf,n=len(ws),wape_med=np.median(ws),
                             wape_p90=np.quantile(ws,.9),wape_max=ws.max()))
df=pd.DataFrame(rows); df.to_csv(f'{OUT}/wape_mediana.csv',index=False)
p=df.pivot_table(index=['problema','cabeca'],columns='corpus',values=['wape_med','wape_p90'])
pd.set_option('display.width',200); print(p.to_string())
