import json, hashlib
import pandas as pd, numpy as np
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
man=json.load(open(B+'.manifest.json'))
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); tim=pd.read_parquet(B+'__timing.parquet')
real=pd.read_parquet(B+'__real.parquet'); pop=pd.read_parquet(B+'__pop.parquet')
gab='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
g=pd.read_parquet(gab)
print('gabarito cols',list(g.columns),'shape',g.shape)
import os
h=hashlib.sha256(open(gab,'rb').read()).hexdigest()
print('x_hash manifest', man['sonda']['x_hash'])
gm=gab.replace('.parquet','.manifest.json')
if os.path.exists(gm): print('gab manifest', json.dumps(json.load(open(gm)))[:500])
sb=sur[sur.regime=='sonda']
print()
print('=== U5 join posicional sonda x gabarito ===')
xc=['x0','x1']; gxc=[c for c in g.columns if c.startswith('x')]; gfc=[c for c in g.columns if c.startswith('f')]
for gg,blk in sb.groupby('geracao'):
    A=blk[xc].values.astype(np.float64); Bx=g[gxc].values.astype(np.float64)[:len(A)]
    print(' bloco',gg,'n',len(A),'max|dX|',np.abs(A-Bx.astype(np.float32).astype(np.float64)).max())
print()
print('=== U6 WAPE/cobertura por bloco (espaco CRU, transf NULL) ===')
print('transf_tipo', sur.transf_tipo.unique(), 'espaco_modelo', sur.espaco_modelo.unique(), 'pred_tipo', sur.pred_tipo.unique(), 'modelo_flag', sur.modelo_flag.unique())
F=g[gfc].values.astype(np.float64)[:2000]
rows=[]
for gg,blk in sb.groupby('geracao'):
    mu=blk[['mu_0','mu_1']].values.astype(np.float64); sg=blk[['sigma_0','sigma_1']].values.astype(np.float64)
    for j in range(2):
        w=np.abs(mu[:,j]-F[:,j]).sum()/np.abs(F[:,j]).sum()
        cov=(np.abs(mu[:,j]-F[:,j])<=1.96*sg[:,j]).mean()
        cor=np.corrcoef(mu[:,j],F[:,j])[0,1]
        rows.append(dict(bloco=int(gg),obj=j,WAPE=w,cob=cov,corr=cor,nan_sigma=int(np.isnan(sg[:,j]).sum()),sigma0=int((sg[:,j]==0).sum())))
df=pd.DataFrame(rows); print(df.to_string(index=False))
df.to_csv('b3_smoke_sonda.csv',index=False)
print()
print('ΔWAPE 1º->último por objetivo:')
for j in range(2):
    a=df[(df.obj==j)&(df.bloco==df.bloco.min())].WAPE.iloc[0]; b=df[(df.obj==j)&(df.bloco==df.bloco.max())].WAPE.iloc[0]
    print('  obj',j,round(a,4),'->',round(b,4),' Δ%=',round(100*(b-a)/a,1))
print()
print('=== U7 timing ===')
tim2=tim.copy()
viol=(tim2.tempo_fit_s+tim2.tempo_busca_s > tim2.tempo_geracao_s).sum()
print('fit+busca <= tempo_geracao violacoes:',viol,'/',len(tim2))
v2=(tim2.tempo_fit_s+tim2.tempo_busca_s+tim2.tempo_pred_sonda_s > tim2.tempo_geracao_s)
print('fit+busca+sonda > tempo_geracao nas geracoes:', list(tim2.geracao[v2].values))
print('sonda declarada nas geracoes:', man['sonda']['geracoes'])
print()
print('=== U8 fe_treino_max ===')
fem=[r['fe_treino_max'] for r in gens]; fe=[r['fe'] for r in gens]
print('fe   ',fe); print('ftmax',fem)
print('monotonico', all(fem[i]<fem[i+1] for i in range(len(fem)-1)))
print('ftmax[k] == fe[k-1]-1 ?', [ (fem[k]==fe[k-1]-1) for k in range(1,len(fe))])
print()
print('=== U9 reconciliacao ===')
guards=[r for r in recs if r['rec']=='guard']
footer=[r for r in recs if r['rec']=='footer'][0]
from collections import Counter
print('guards', Counter(x['name'] for x in guards), 'manifest.cache_hits',man['cache_hits'],'footer',footer['cache_hits'])
print('2 pop: geracoes',sorted(pop.geracao.unique()),'n por ger',pop.groupby('geracao').size().to_dict())
print('esperado |2_g| = 11D-1+5(g-1):',[21+5*(k-1) for k in sorted(pop.geracao.unique())])
dfe=[fe[0]-21]+[fe[i]-fe[i-1] for i in range(1,len(fe))]
print('Δfe por ciclo', dfe, 'soma',sum(dfe), '5*n_ciclos',5*len(gens))
print('ledger: 5*n - sum(dfe) =', 5*len(gens)-sum(dfe), ' cache-hits de ciclo (total - c0) =', man['cache_hits']-1)
