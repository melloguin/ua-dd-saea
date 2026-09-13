import json
import numpy as np, pandas as pd
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); on=sur[sur.regime=='online']
real=pd.read_parquet(B+'__real.parquet')
X=real[['x0','x1']].values.astype(np.float64); fei=real.fe_index.values
print('=== B8 dist_min_arquivo: A1 e SUBCONJUNTO PRoPRIO do (1)? ===')
tol=1e-6
lin=[]
for k,r in enumerate(gens):
    g=r['geracao']; blk=on[on.geracao==g]; ppw=r['pop_por_w']; last=blk.iloc[-ppw[-1]:]
    ftm=r['fe_treino_max']
    cand=np.array([[last.iloc[i-1].x0,last.iloc[i-1].x1] for i in r['index']],dtype=np.float64)
    mask=fei<=ftm
    P=X[mask]
    d=np.sqrt(((P[None,:,:]-cand[:,None,:])**2).sum(axis=2))
    dall=d.min(axis=1)
    dlog=np.array(r['dist_min_arquivo'])
    ge=(dlog>=dall-tol).all()
    eq=int((np.abs(dlog-dall)<=tol).sum())
    # pontos PROVADAMENTE fora do A1: mais perto que o dmin logado
    fora=set()
    for i in range(len(cand)):
        idx=np.where(d[i]<dlog[i]-tol)[0]
        for j in idx: fora.add(int(fei[mask][j]))
    lin.append(dict(ciclo=g,n_disponivel=int(mask.sum()),dlog_ge_dall=bool(ge),n_igualdade=eq,
                    n_provado_fora=len(fora),provado_fora=sorted(fora)))
    print('  ciclo %d: |(1) disponivel|=%2d  dmin_logado>=dmin(1) %s  igualdade %d/5  fe_index PROVADOS fora do A1: %s'%(g,mask.sum(),ge,eq,sorted(fora)))
pd.DataFrame(lin).to_csv('b3_smoke_A1_exclusoes.csv',index=False)
print()
print('=== ordem lexicografica do Total (unique(All,rows)) e o alcance do ramo (a) ===')
doe=real[real.fase=='init'][['x0','x1']].values.astype(np.float64)
fed=real[real.fase=='init'].fe_index.values
ordem=np.lexsort((doe[:,1],doe[:,0]))
print('  Total(ciclo1) ordenado lex por dec: fe_index na ordem =',list(fed[ordem]))
print('  |Via|=18 => posicoes 19,20,21 INALCANCAVEIS pelo Next do ramo (a) => fe_index', list(fed[ordem][18:]))
print('  x0 desses:',[round(v,4) for v in doe[ordem][18:,0]])
# cruzar com o provado-fora do ciclo 2
c2=[l for l in lin if l['ciclo']==2][0]
print('  provados fora do A1 no ciclo 2:',c2['provado_fora'])
print('  intersecao com a cauda lex:',sorted(set(c2['provado_fora'])&set(int(v) for v in fed[ordem][18:])))
print()
print('=== U10 erro de fantasia dos infills (mu do escolhido vs f real) ===')
er=[]; otim=0; n=0
for r in gens:
    g=r['geracao']; blk=on[on.geracao==g]; ppw=r['pop_por_w']; last=blk.iloc[-ppw[-1]:]
    for k,idx in enumerate(r['index']):
        row=last.iloc[idx-1]
        xk=np.array([row.x0,row.x1],dtype=np.float32)
        m=np.where((real.x0.values.astype(np.float32)==xk[0])&(real.x1.values.astype(np.float32)==xk[1]))[0]
        if len(m)==0: continue
        f=real.iloc[m[0]][['f0','f1']].values.astype(np.float64)
        mu=np.array([row.mu_0,row.mu_1],dtype=np.float64)
        rel=np.abs(mu-f)/np.maximum(np.abs(f),1e-12)
        er.append(np.median(rel)); otim+= int((mu<f).mean()>0.5); n+=1
print('  n infills casados',n,' erro relativo mediano %.4f (min %.4f max %.4f)'%(np.median(er),min(er),max(er)),' fracao otimista %.3f'%(otim/n))
