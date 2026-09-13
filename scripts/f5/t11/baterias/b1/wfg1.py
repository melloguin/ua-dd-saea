import json,os,numpy as np,pandas as pd
P='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/WFG1/42'
f=[x for x in os.listdir(P) if x.endswith('.jsonl')][0]
base=f[:-6]
tot=0;ruins=0;recs=[];badidx=[]
for i,l in enumerate(open(f'{P}/{f}')):
    tot+=1
    try: recs.append(json.loads(l))
    except Exception: ruins+=1; badidx.append(i)
print('⑥ linhas=%d  ruins=%d  parseadas=%d'%(tot,ruins,len(recs)))
from collections import Counter
print('rec:',Counter(r.get('rec') for r in recs))
g=[r['geracao'] for r in recs if r.get('rec')=='b1_gen']
print('b1_gen n=%d  min=%d max=%d  faltando=%d'%(len(g),min(g),max(g),max(g)-len(g)))
falt=sorted(set(range(1,max(g)+1))-set(g))
print('geracoes ausentes: n=%d  primeira=%s ultima=%s  contiguo=%s'%(len(falt),falt[0] if falt else None,falt[-1] if falt else None, falt==list(range(falt[0],falt[-1]+1)) if falt else True))
print('posicao das linhas ruins: primeira=%d ultima=%d (de %d)'%(badidx[0],badidx[-1],tot))
print('footer presente:', any(r.get('rec')=='footer' for r in recs), ' header:',any(r.get('rec')=='header' for r in recs))
for suf,exp in [('__real',None),('__pop',None),('__surrogate',None),('__timing',None)]:
    d=pd.read_parquet(f'{P}/{base}{suf}.parquet'); print(suf,d.shape)
m=json.load(open(f'{P}/{base}.manifest.json'))
print('manifest: status=%s fe_final=%s maxfe=%s n_geracoes=%s cache_hits=%s'%(m['status'],m['fe_final'],m['maxfe'],m['n_geracoes'],m['cache_hits']))
print('fit_series len=',len(m.get('fit_series',[])))
t=pd.read_parquet(f'{P}/{base}__timing.parquet')
print('④ geracoes:',t.geracao.min(),t.geracao.max(),len(t), 'unicas',t.geracao.nunique())
r1=pd.read_parquet(f'{P}/{base}__real.parquet')
D=22; print('① linhas=%d esperado 31D-1=%d ; init=%d esperado 11D-1=%d'%(len(r1),31*D-1,(r1.fase=='init').sum(),11*D-1))
s3=pd.read_parquet(f'{P}/{base}__surrogate.parquet')
print('③ regimes:',s3.regime.value_counts().to_dict())
on=s3[s3.regime=='online']; print('③ online geracoes unicas=',on.geracao.nunique())
sd=s3[s3.regime=='sonda']; print('③ sonda blocos=',sd.geracao.nunique() if 'geracao' in sd else '?', 'linhas=',len(sd))
p2=pd.read_parquet(f'{P}/{base}__pop.parquet'); print('② geracoes=',p2.geracao.nunique(),'linhas=',len(p2))
