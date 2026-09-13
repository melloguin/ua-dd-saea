"""B8 re-medido: dist_min_arquivo (log, vs A1) >= dmin contra a ① inteira ate fe_prev."""
import json,os,numpy as np,pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
tot=0;ok=0;eq=0;maxviol=0.0
for prob in sorted(os.listdir(ROOT)):
    base=f'{ROOT}/{prob}/42/exp_main_b3_{prob}_42'
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    gens=[x for x in L if x.get('rec')=='b3_gen']
    hdr=[x for x in L if x.get('rec')=='header'][0]; D=hdr['D']; M=hdr['M']
    real=pd.read_parquet(base+'__real.parquet')
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    X=real[xc].to_numpy(float)
    s3=pd.read_parquet(base+'__surrogate.parquet'); s3=s3[s3.regime=='online']
    xs3=[c for c in s3.columns if c.startswith('x') and c[1:].isdigit()]
    fe_prev=11*D-1
    for g in gens:
        blk=s3[s3.geracao==g['geracao']]; k=g['pop_por_w'][-1]; last=blk.iloc[-k:]
        Xs=last.iloc[[int(i)-1 for i in g['index']]][xs3].to_numpy(float)
        arq=X[:fe_prev]
        dm=np.sqrt(((arq[None,:,:]-Xs[:,None,:])**2).sum(2)).min(1)
        log=np.array(g['dist_min_arquivo'],float)
        tot+=len(log)
        rel=(log-dm)/np.maximum(np.abs(dm),1e-12)
        ok+=int((rel>=-1e-6).sum()); eq+=int((np.abs(rel)<1e-6).sum())
        maxviol=max(maxviol,float(max(0,-(rel.min()))))
        fe_prev=g['fe']
print(f'B8: {ok}/{tot} satisfazem dist_min_log >= dmin(①); igualdade exata em {eq} ({eq/tot:.1%}); pior violacao relativa {maxviol:.3g}')
