"""Bateria 6 — papel de CONTROLE (regua): nsga3 x 4 pisos x 17 SA. READ-ONLY."""
import numpy as np,pandas as pd
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
m=pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
main=m[(m.exp=='main')&(m.erro.isna())].copy()
PISOS=['nsga2','nsga3','moead','smsemoa']
probs=sorted(main[main.alg=='nsga3'].problema.unique())
D={'BBOB_F1':10,'BBOB_F17':10,'BBOB_F22':10,'BBOB_F37':10,'BBOB_F49':10,'BBOB_F5':10,'BBOB_F55':10,
   'DTLZ1':7,'DTLZ2':12,'DTLZ3':12,'DTLZ4':12,'DTLZ7':22,'MMF1':2,'MMF11_L':2,'MMF16_20':20,'MMF4':2,
   'WFG1':22,'WFG2':22,'WFG4':22,'WFG5':22,'WFG9':22,'ZDT1':30,'ZDT3':30,'ZDT4':10,'ZDT6':10}
Mm={'DTLZ1':3,'DTLZ2':3,'DTLZ3':3,'DTLZ4':3,'DTLZ7':3,'MMF16_20':3}
rows=[]
for p in probs:
    sub=main[main.problema==p].set_index('alg')['igd_plus']
    if 'nsga3' not in sub.index: continue
    v=sub['nsga3']
    pis=sub.reindex(PISOS).dropna()
    sa=sub.drop(index=[a for a in PISOS if a in sub.index])
    rank_all=sub.rank().loc['nsga3']
    rows.append(dict(prob=p,D=D[p],M=Mm.get(p,2),igdp=v,
        rank_geral=int(rank_all),n_algs=len(sub),
        rank_piso=int(pis.rank().loc['nsga3']),n_pisos=len(pis),
        melhor_piso=pis.idxmin(),igdp_melhor_piso=pis.min(),
        pior_piso=pis.idxmax(),igdp_pior_piso=pis.max(),
        banda_razao=round(float(pis.max()/pis.min()),2),
        sa_melhores=int((sa<v).sum()),n_sa=len(sa),
        frac_sa_ganha=round(float((sa<v).mean()),3),
        melhor_sa=sa.idxmin(),igdp_melhor_sa=sa.min(),
        razao_nsga3_melhorSA=round(float(v/sa.min()),2),
        e7=sub.get('e7',np.nan),razao_e7=round(float(sub.get('e7',np.nan)/v),3),
        nsga2=sub.get('nsga2'),moead=sub.get('moead'),smsemoa=sub.get('smsemoa')))
T=pd.DataFrame(rows); T.to_csv('regua_pisos_nsga3.csv',index=False)
pd.set_option('display.width',300)
print(T[['prob','D','M','igdp','rank_geral','n_algs','rank_piso','melhor_piso','banda_razao','sa_melhores','n_sa','frac_sa_ganha','melhor_sa','razao_nsga3_melhorSA','e7','razao_e7']].to_string(index=False))
print('\nrank geral medio nsga3:',round(T.rank_geral.mean(),2),'/',T.n_algs.mode()[0])
print('rank medio entre os 4 pisos:',round(T.rank_piso.mean(),2))
print('nsga3 = melhor piso em',int((T.rank_piso==1).sum()),'/25 ; pior piso em',int((T.rank_piso==T.n_pisos).sum()),'/25')
print('SA que batem nsga3: mediana',T.sa_melhores.median(),'de',T.n_sa.mode()[0],'| media frac',round(T.frac_sa_ganha.mean(),3))
print('e7 (casado) melhor que nsga3 em',int((T.e7<T.igdp).sum()),'/25')
print('\nM=3 (N_ef=15):'); print(T[T.M==3][['prob','igdp','rank_piso','sa_melhores','frac_sa_ganha']].to_string(index=False))
print('\nM=2 (N_ef=20): rank_piso medio',round(T[T.M==2].rank_piso.mean(),2),'| M=3:',round(T[T.M==3].rank_piso.mean(),2))
print('frac_sa_ganha M=2',round(T[T.M==2].frac_sa_ganha.mean(),3),'| M=3',round(T[T.M==3].frac_sa_ganha.mean(),3))
# tabela piso x piso
piv=main[main.alg.isin(PISOS)].pivot_table(index='problema',columns='alg',values='igd_plus')
piv=piv.loc[probs]
print('\n=== IGD+ dos 4 pisos ==='); print(piv.round(4).to_string())
print('\nrank medio por piso:',piv.rank(axis=1).mean().round(2).to_dict())
piv.to_csv('pisos_igdplus.csv')
