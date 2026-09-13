"""s42(vm3/x86-Linux) x smoke-T11(Mac/Apple-M1) — caracterizacao da divergencia. READ-ONLY."""
import sys, os, json, glob, re, hashlib
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
import numpy as np, pandas as pd
from src import metrics as MT

S='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141/MMF1/42/exp_main_c141_MMF1_42'
K='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42'

print('=== 1. ①: onde a divergencia comeca ===')
a=pd.read_parquet(S+'__real.parquet'); b=pd.read_parquet(K+'__real.parquet')
xs=['x0','x1']; fs=['f0','f1']
d=np.abs(a[xs].values-b[xs].values).max(axis=1)
print(' init (21 pontos) IDENTICO:', bool((d[:21]==0).all()), ' max|dX| no init:',d[:21].max())
print(' 1a linha divergente: fe_index',int(np.argmax(d>0)),' (= 1o infill)  |dX|=%.4g'%d[np.argmax(d>0)])
print(' linhas identicas: %d/%d'%(int((d==0).sum()),len(d)))

print()
print('=== 2. o MODELO da geracao 1 (mesmo treino de 21 pontos) ===')
sa=pd.read_parquet(S+'__surrogate.parquet'); sb=pd.read_parquet(K+'__surrogate.parquet')
A=sa[sa.regime=='sonda'].iloc[:2000]; B=sb[sb.regime=='sonda'].iloc[:2000]
print(' bloco g=%s x g=%s ; fe_treino_max %s x %s'%(A.geracao.unique(),B.geracao.unique(),A.fe_treino_max.unique(),B.fe_treino_max.unique()))
print(' X do bloco identico:',np.array_equal(A[xs].values,B[xs].values))
import pyarrow.parquet as pq
sch=pq.read_schema(S+'__surrogate.parquet')
print(' dtype de mu_0 no parquet:',sch.field('mu_0').type,' (D53: float32)')
for c in ['mu_0','mu_1']:
    dd=np.abs(A[c].values.astype(np.float64)-B[c].values.astype(np.float64))
    print(' %s: identicas %d/2000  max|d|=%g'%(c,int((dd==0).sum()),dd.max()))
print(' => o modelo da g=1 concorda ate a RESOLUCAO float32 (~1,2e-7 rel). Abaixo disso o artefato nao resolve.')

print()
print('=== 3. a populacao da geracao 1 JA diverge macroscopicamente ===')
PA=sa[(sa.regime=='online')&(sa.geracao==1)][xs].values
PB=sb[(sb.regime=='online')&(sb.geracao==1)][xs].values
from scipy.spatial import cKDTree
dd,_=cKDTree(PB).query(PA)
print(' |P|=%d x %d ; pares (x0,x1) em comum: %d ; dist ao vizinho mais proximo: mediana %.4g max %.4g'%(
    len(PA),len(PB),len(set(map(tuple,PA))&set(map(tuple,PB))),np.median(dd),dd.max()))

print()
print('=== 4. CONTROLE: quantos infills IDENTICOS antes de divergir, por config MATLAB ===')
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments'
RE='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
out=[]
for man in sorted(glob.glob(SM+'/*/*/*.manifest.json')):
    bb=man[:-len('.manifest.json')]; m=json.load(open(man))
    nm=os.path.basename(bb).split('_'); alg=m.get('alg') or nm[2]; pb=m.get('problema') or '_'.join(nm[3:-1])
    g=glob.glob(f'{RE}/{alg}/{pb}/42/*__real.parquet')
    if not g: continue
    x=pd.read_parquet(g[0]); y=pd.read_parquet(bb+'__real.parquet')
    cx=[c for c in x.columns if re.fullmatch(r'x\d+',c)]
    if x.shape!=y.shape: out.append((alg,pb,'shape dif','','')); continue
    dd2=np.abs(x[cx].values-y[cx].values).max(axis=1)
    init=int((x['fase']=='init').sum())
    fd=int(np.argmax(dd2>0)) if (dd2>0).any() else -1
    out.append((alg,pb,'IDENTICA' if fd<0 else 'diverge',
                'todos' if fd<0 else str(fd-init), str(len(x)-init)))
print(' %-8s %-10s %-9s %-10s %s'%('alg','problema','①','infills identicos','de'))
for r in out: print(' %-8s %-10s %-9s %-10s %s'%r)

print()
print('=== 5. o RESULTADO muda? IGD+/HV/|ND| do main/c141/MMF1 nas duas maquinas ===')
ideal,nadir=MT.f_min_max('MMF1'); ref=MT.reference_set('MMF1')
refn=MT.normalize(ref,ideal,nadir)
for t,df in [('s42 (vm3, x86-Linux)',a),('smoke T11 (Mac, Apple M1)',b)]:
    F=df[fs].values.astype(np.float64)
    nd=MT.nondominated_front(F); Fn=MT.normalize(nd,ideal,nadir)
    print(' %-26s |ND|=%3d  IGD+=%.6f  HV=%.6f  spacing=%.6f'%(t,len(nd),MT.igd_plus(Fn,refn),MT.hv(Fn),MT.spacing(Fn)))
mf=pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/metricas_finais_f52c.csv')
r=mf[(mf.alg=='c141')&(mf.problema=='MMF1')&(mf.exp=='main')]
print(' F5.2c oficial (s42):', r[[c for c in r.columns if c in ('igd_plus','hv','n_nd','spacing','igd')]].to_dict('records'))
