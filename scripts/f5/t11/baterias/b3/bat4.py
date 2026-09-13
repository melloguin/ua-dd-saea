import json
import pandas as pd, numpy as np
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
man=json.load(open(B+'.manifest.json'))
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); real=pd.read_parquet(B+'__real.parquet')
on=sur[sur.regime=='online']
print('=== F1 query-joia: index -> ultima sub-pop da 3 -> sigma ===')
maxrel=0; n=0; det=[]
for r in gens:
    g=r['geracao']; blk=on[on.geracao==g]
    ppw=r['pop_por_w']; assert len(blk)==sum(ppw), (g,len(blk),sum(ppw))
    last=blk.iloc[-ppw[-1]:]
    for k,idx in enumerate(r['index']):
        row=last.iloc[idx-1]
        got=np.array([row.sigma_0,row.sigma_1],dtype=np.float64)
        exp=np.array(r['sigma_sel']['sqrtmse_por_objetivo'][k],dtype=np.float64)
        rel=np.abs(got-exp)/np.maximum(np.abs(exp),1e-300)
        maxrel=max(maxrel,rel.max()); n+=1
        det.append((g,k,idx,rel.max()))
print('selecoes',n,'max erro RELATIVO',maxrel)
print('piores:',sorted(det,key=lambda t:-t[3])[:3])
print('index range', min(min(r['index']) for r in gens), max(max(r['index']) for r in gens), 'pop_por_w[-1]', [r['pop_por_w'][-1] for r in gens])
print()
print('=== F2 criterio_meanMSE == media das VARIANCIAS ===')
m=0
for r in gens:
    for k,c in enumerate(r['sigma_sel']['criterio_meanMSE']):
        s=np.array(r['sigma_sel']['sqrtmse_por_objetivo'][k],dtype=np.float64)
        rec=(s**2).mean()
        m=max(m, abs(rec-c)/max(abs(c),1e-300))
print('max erro relativo criterio vs media(sigma^2):',m)
r=gens[0]; s=np.array(r['sigma_sel']['sqrtmse_por_objetivo'][0])
print('exemplo g1 k0: sigma=',list(s),' media(var)=',(s**2).mean(),' logado=',r['sigma_sel']['criterio_meanMSE'][0],
      ' media(sigma)=',s.mean(),' sqrt(media var)=',np.sqrt((s**2).mean()), ' razao criterio/media_sigma=',(s**2).mean()/s.mean())
print()
print('=== F3 cadeia selecao -> avaliacao real (por bytes float32) ===')
key=lambda a: a.astype(np.float32).tobytes()
mapa={}
for i,row in real.iterrows():
    mapa.setdefault(key(np.array([row.x0,row.x1])),[]).append(int(row.fe_index))
nf=0; nova=0; pre=0
fe_prev=21
for r in gens:
    g=r['geracao']; blk=on[on.geracao==g]; ppw=r['pop_por_w']; last=blk.iloc[-ppw[-1]:]
    for idx in r['index']:
        row=last.iloc[idx-1]
        k=key(np.array([row.x0,row.x1]))
        if k not in mapa: nf+=1
        else:
            hits=mapa[k]
            if any(fe_prev<=h<r['fe'] for h in hits): nova+=1
            else: pre+=1
    fe_prev=r['fe']
print('nao encontrados',nf,' abrem linha nova',nova,' linha pre-existente',pre,' total',nf+nova+pre)
print()
print('=== F4 ramo x sigma/APD ===')
from collections import Counter
print('ramos', Counter(r['ramo'] for r in gens))
print('Flag por ciclo', [r['Flag'] for r in gens], 'delta', gens[0]['delta'])
print('NumV1',[r['NumV1'] for r in gens]); print('NumV2',[r['NumV2'] for r in gens])
ok=all( (r['ramo']=='APD') == (r['Flag']<=r['delta']) for r in gens)
print('ramo == (Flag<=delta ? APD : incerteza):', ok, ' em', len(gens))
ok2=all(r['Flag']==r['NumV2']-r['NumV1'] for r in gens)
print('Flag == NumV2-NumV1:', ok2)
# percentil do meanMSE do selecionado dentro da ultima sub-pop
pcs=[]
for r in gens:
    g=r['geracao']; blk=on[on.geracao==g]; ppw=r['pop_por_w']; last=blk.iloc[-ppw[-1]:]
    mm=((last[['sigma_0','sigma_1']].values.astype(np.float64))**2).mean(axis=1)
    for c in r['sigma_sel']['criterio_meanMSE']:
        pcs.append((mm<c).mean())
print('percentil meanMSE do selecionado (ramo APD, n=%d): media %.3f mediana %.3f  P(>0.9)=%.3f'%(len(pcs),np.mean(pcs),np.median(pcs),np.mean(np.array(pcs)>0.9)))
print()
print('=== B5 operando do switch: NumV1[k] == NumV2[k-1]? ===')
eq=sum(1 for k in range(1,len(gens)) if gens[k]['NumV1']==gens[k-1]['NumV2'])
print('coincidencias', eq, '/', len(gens)-1)
print()
print('=== B7 |A1| fixo ===')
print('n_treino',[r['n_treino'] for r in gens],'arquivo',[r['arquivo'] for r in gens],'NI',11*2-1)
print('modelo_hp n',[r['modelo_hp']['n'] for r in gens])
print('tempo_fit_s',[round(r['tempo_fit_s'],5) for r in gens])
print()
print('=== B10 sigma export ===')
sg=sur[['sigma_0','sigma_1']].values.astype(np.float64); mu=sur[['mu_0','mu_1']].values.astype(np.float64)
print('linhas 3',len(sur),'sigma negativos',int((sg<0).sum()),'sigma NaN',int(np.isnan(sg).sum()),'mu NaN',int(np.isnan(mu).sum()),'sigma==0',int((sg==0).sum()))
print('pred_classe/score/confianca nulos:', sur.pred_classe.isna().all(), sur.pred_score.isna().all(), sur.pred_confianca.isna().all())
print()
print('=== B12/B3 guardas ===')
print('nzero_updata',[r['nzero_updata'] for r in gens],'n_vetores_vazios',[r['n_vetores_vazios'] for r in gens])
print('u_alvo/u_efetivo',[(r['u_alvo'],r['u_efetivo']) for r in gens])
print('lote',[r['lote'] for r in gens], 'len(index)',[len(r['index']) for r in gens])
print()
print('=== B2 wmax ===')
print('len(pop_por_w)',[len(r['pop_por_w']) for r in gens])
tot=[sum(r['pop_por_w']) for r in gens]; obs=[len(on[on.geracao==r['geracao']]) for r in gens]
print('sum(pop_por_w)',tot,'linhas online por ciclo',obs,'iguais',tot==obs)
print()
print('=== B9 real_solution_id por sub-populacao ===')
frac=[]
for r in gens:
    g=r['geracao']; blk=on[on.geracao==g]; ppw=r['pop_por_w']; o=0; fr=[]
    for w,nw in enumerate(ppw):
        sub=blk.iloc[o:o+nw]; o+=nw
        fr.append(sub.real_solution_id.notna().mean())
    frac.append(fr)
fa=np.array(frac)
print('fracao rsid nao-nulo: 1a sub-pop mediana %.3f  20a %.3f  total %.3f'%(np.median(fa[:,0]),np.median(fa[:,-1]),on.real_solution_id.notna().mean()))
