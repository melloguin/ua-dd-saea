# -*- coding: utf-8 -*- READ-ONLY. REGUA SOBOL (regime='sonda') por cabeca: WAPE 1o/ultimo bloco + corr. Regra 12 respeitada.
import json
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT=f'{ROOT}/ua-dd-saea/f5/t11/baterias/e74'
rows=[]
for prob in ['MMF1','DTLZ2','ZDT1']:
    gab=pd.read_parquet(f'{ROOT}/ua-dd-saea/data/sonda/sonda_{prob}.parquet')
    fcg=[c for c in gab.columns if c.startswith('f') and c[1:].isdigit()]
    Fg=gab[fcg].values[:2000].astype(np.float64)
    for tag,base in [('PRE_s42',f'{ROOT}/resultados_experimentos/e74/{prob}/42/exp_main_e74_{prob}_42'),
                     ('POS_smoke',f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{prob}_42')]:
        s=pd.read_parquet(base+'__surrogate.parquet',columns=['regime','geracao','modelo_flag']+[f'mu_{i}' for i in range(Fg.shape[1])]+['sigma_0','pred_classe'])
        sd=s[s.regime=='sonda']
        for mf,g in sd.groupby('modelo_flag'):
            if mf=='PNN(s1)':
                rows.append(dict(problema=prob,corpus=tag,cabeca=mf,blocos=g.geracao.nunique(),wape_1=np.nan,wape_N=np.nan,corr_1=np.nan,corr_N=np.nan,mu_max=np.nan)); continue
            gers=sorted(g.geracao.dropna().unique())
            def wape(gr):
                b=g[g.geracao==gr]
                mu=b[[f'mu_{i}' for i in range(Fg.shape[1])]].values.astype(np.float64)
                w=[np.abs(mu[:,j]-Fg[:,j]).sum()/np.abs(Fg[:,j]).sum() for j in range(Fg.shape[1])]
                c=[np.corrcoef(mu[:,j],Fg[:,j])[0,1] for j in range(Fg.shape[1])]
                return float(np.median(w)), float(np.median(c)), float(np.abs(mu).max())
            w1,c1,_=wape(gers[0]); wN,cN,mx=wape(gers[-1])
            rows.append(dict(problema=prob,corpus=tag,cabeca=mf,blocos=len(gers),wape_1=w1,wape_N=wN,corr_1=c1,corr_N=cN,mu_max=mx,f_max=float(np.abs(Fg).max())))
df=pd.DataFrame(rows); df.to_csv(f'{OUT}/sonda_regua.csv',index=False)
pd.set_option('display.width',260)
print(df.to_string(index=False))
print()
p=df[df.cabeca!='PNN(s1)'].pivot_table(index=['problema','cabeca'],columns='corpus',values=['wape_N','corr_N'])
print(p.to_string())
