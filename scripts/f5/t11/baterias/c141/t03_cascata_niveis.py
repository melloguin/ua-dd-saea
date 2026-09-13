"""Cascata: distribuicao do nivel de saida e do lote nas 1.967 iteracoes da s42."""
import sys, os, json
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT
from collections import Counter
tot=Counter(); lotes=Counter(); n2f1=0; n2=0; ramoQU=0; ng=0
per=[]
for pb in sorted(os.listdir(ROOT)):
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim=load(pb)
    gen=[e for e in ev if e['rec']=='c141_gen']; ng+=len(gen)
    c=Counter(g['nivel'] for g in gen); tot+=c
    lotes+=Counter(g['lote'] for g in gen)
    s2=[g for g in gen if g['nivel']==2]; n2+=len(s2)
    n2f1+=sum(1 for g in s2 if g['n_front2']==1)
    ramoQU+=sum(1 for g in gen if g.get('ramo_QU'))
    per.append(dict(pb=pb,n=len(gen),nivel1=c.get(1,0),nivel2=c.get(2,0),nivel3=c.get(3,0),
        lote_max=max(g['lote'] for g in gen),lote_gt5=sum(1 for g in gen if g['lote']>5),
        nfront1_med=float(np.median([g['n_front1'] for g in gen])),
        nfront2_med=float(np.median([g['n_front2'] for g in gen])),
        upool_max=max(g['U_pool_max'] for g in gen)))
print('ciclos totais',ng)
print('nivel de saida:',dict(sorted(tot.items())))
print('saidas nivel 2 =',n2,' com n_front2==1 =',n2f1)
print('ramo_QU=true em',ramoQU,'/',ng,'= %.2f%%'%(100*ramoQU/ng))
print('distribuicao do lote:',dict(sorted(lotes.items())))
print('lote>5:',sum(v for k,v in lotes.items() if k>5),' lote==0:',lotes.get(0,0))
df=pd.DataFrame(per); df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t03_cascata.csv',index=False)
print(df.to_string())
