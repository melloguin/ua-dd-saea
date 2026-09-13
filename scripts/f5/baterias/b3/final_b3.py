import pandas as pd, numpy as np, json, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=F5+'/baterias/b3'
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
tot=0; ge=0; eq=0; pool_in=[]; pool_ap=[]; rows=[]
for pr in sorted(os.listdir(ROOT)):
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]; D,M=hdr['D'],hdr['M']
    gens=[x for x in recs if x['rec']=='b3_gen']
    xc=[f'x{j}' for j in range(D)]; sgc=[f'sigma_{j}' for j in range(M)]
    r=pd.read_parquet(b+'__real.parquet'); RX=r[xc].to_numpy().astype(np.float64)
    s=pd.read_parquet(b+'__surrogate.parquet'); on=s[s.regime=='online'].reset_index(drop=True)
    for g in gens:
        fe0=g['fe']-5; blk=on[on.geracao==g['geracao']]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True); idx=[i-1 for i in g['index']]
        SX=last.iloc[idx][xc].to_numpy().astype(np.float64); A=RX[:fe0]
        dd=np.sqrt(((SX[:,None,:]-A[None,:,:])**2).sum(-1)).min(1)
        lg=np.array(g['dist_min_arquivo'])
        tot+=len(lg); ge+=int((lg>=dd-1e-6).sum()); eq+=int((np.abs(lg-dd)<=1e-6*np.maximum(dd,1e-9)).sum())
        mm=(last[sgc].to_numpy().astype(np.float64)**2).mean(1)
        for i in idx: (pool_in if g['ramo']=='incerteza' else pool_ap).append(float((mm<mm[i]).mean()))
    # cauda do switch
    ramo=[g['ramo'] for g in gens]; n=len(ramo); h=n//2
    rows.append(dict(problema=pr,n=n,inc=sum(1 for x in ramo if x=='incerteza'),
        inc_1a_metade=sum(1 for x in ramo[:h] if x=='incerteza'),inc_2a_metade=sum(1 for x in ramo[h:] if x=='incerteza')))
print('dist_min_arquivo >= dmin(1):  %d/%d (%.1f%%)  | igualdade exata: %d (%.1f%%)'%(ge,tot,100*ge/tot,eq,100*eq/tot))
pi=np.array(pool_in); pa=np.array(pool_ap)
print('percentil meanMSE do selecionado -- ramo INCERTEZA: n=%d media %.3f mediana %.3f  P(>0.9)=%.3f'%(len(pi),pi.mean(),np.median(pi),(pi>0.9).mean()))
print('percentil meanMSE do selecionado -- ramo APD:       n=%d media %.3f mediana %.3f  P(>0.9)=%.3f'%(len(pa),pa.mean(),np.median(pa),(pa>0.9).mean()))
print('P(selecionado = argmax global de meanMSE) inc: %.3f | apd: %.3f'%((pi>=0.999).mean(),(pa>=0.999).mean()))
R=pd.DataFrame(rows); R['pct_inc']=(100*R.inc/R.n).round(1); R.to_csv(OUT+'/b3_switch_metades.csv',index=False)
pd.set_option('display.width',200); print(); print(R.to_string())
print('\ntotal ciclos:',R.n.sum(),'| incerteza:',R.inc.sum(),'(%.1f%%)'%(100*R.inc.sum()/R.n.sum()))
print('1a metade incerteza: %d/%d (%.1f%%) | 2a metade: %d/%d (%.1f%%)'%(
    R.inc_1a_metade.sum(),(R.n//2).sum(),100*R.inc_1a_metade.sum()/(R.n//2).sum(),
    R.inc_2a_metade.sum(),(R.n-R.n//2).sum(),100*R.inc_2a_metade.sum()/(R.n-R.n//2).sum()))
