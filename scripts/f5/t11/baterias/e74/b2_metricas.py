# -*- coding: utf-8 -*- READ-ONLY: metricas finais + trajetoria, s42 (PRE-DI45) x smoke T11 (POS-DI45)
import sys, os, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
import numpy as np, pandas as pd
from src import metrics as MET
ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e74'
rows=[]
for prob in ['MMF1','DTLZ2','ZDT1']:
    R=MET.reference_set(prob)
    for tag,base in [('s42_PRE',f'{ROOT}/resultados_experimentos/e74/{prob}/42/exp_main_e74_{prob}_42'),
                     ('smoke_POS',f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{prob}_42')]:
        d=pd.read_parquet(base+'__real.parquet')
        fc=[c for c in d.columns if c.startswith('f') and c[1:].isdigit()]
        F=d[fc].values.astype(np.float64)
        m=MET.metrics_of_set(F,prob,ref_norm=R); m['corpus']=tag; m['problema']=prob
        # trajetoria (5 checkpoints) para ver quando separa
        tr=MET.trajectory(F,d['fe_index'].values,prob,n_checkpoints=6,ref_norm=R)
        m['traj_igdp']=';'.join('%d:%.4f'%(t['fe'],t['igd_plus']) for t in tr)
        rows.append(m)
df=pd.DataFrame(rows)
df.to_csv(f'{OUT}/metricas_pre_pos.csv',index=False)
piv=df.pivot(index='problema',columns='corpus',values=['igd_plus','hv','n_nd','spacing'])
print(piv.to_string())
print()
for prob in ['MMF1','DTLZ2','ZDT1']:
    a=df[(df.problema==prob)&(df.corpus=='s42_PRE')].iloc[0]; b=df[(df.problema==prob)&(df.corpus=='smoke_POS')].iloc[0]
    print('%-8s IGD+ %.5f -> %.5f (%+.2f%%)   HV %.5f -> %.5f (%+.2f%%)  nND %d->%d'%(
        prob,a.igd_plus,b.igd_plus,100*(b.igd_plus-a.igd_plus)/a.igd_plus,a.hv,b.hv,
        100*(b.hv-a.hv)/a.hv if a.hv else float('nan'),a.n_nd,b.n_nd))
    print('   traj PRE :',a.traj_igdp); print('   traj POS :',b.traj_igdp)
