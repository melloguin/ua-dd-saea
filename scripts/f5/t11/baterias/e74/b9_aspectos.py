# -*- coding: utf-8 -*- READ-ONLY. A9(D74) A17(quotas) A18(spreads) A19(sigma_dict) A22(cadencia) no SMOKE pos-DI45.
import json
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
def one(prob, base, tag):
    real=pd.read_parquet(base+'__real.parquet')
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    fc=[c for c in real.columns if c.startswith('f') and c[1:].isdigit()]; M=len(fc)
    sur=pd.read_parquet(base+'__surrogate.parquet',columns=['regime','geracao','modelo_flag','sigma_0','pred_score','pred_classe']+xc)
    on=sur[sur.regime=='online']
    Fr=real[fc].values.astype(np.float64); Xr=real[xc].values.astype(np.float64)
    ev=[json.loads(l) for l in open(base+'.jsonl')]
    gen=[r for r in ev if r.get('rec')=='e74_gen']
    o=dict(corpus=tag,problema=prob)
    # A9 D74: Ymin/Ymax = min/max do FRONT-1 do arquivo PRE-FE
    e9=[]; 
    for r in gen:
        if r['estrategia']!=2 or r.get('range0') is not False: continue
        nA=r['arquivo']-r['aceito']; FA=Fr[:nA]
        dom=np.zeros(nA,bool)
        for i in range(nA):
            le=(FA<=FA[i]).all(axis=1); lt=(FA<FA[i]).any(axis=1)
            if (le&lt).any(): dom[i]=True
        F1=FA[~dom]
        e9.append((np.abs(F1.min(axis=0)-np.array(r['Ymin']))/np.maximum(np.abs(r['Ymin']),1e-12)).max())
        e9.append((np.abs(F1.max(axis=0)-np.array(r['Ymax']))/np.maximum(np.abs(r['Ymax']),1e-12)).max())
    o['A9_relmax']=float(np.max(e9)) if e9 else np.nan; o['A9_n']=len(e9)//2
    # A17 quotas + identidade n_por_nivel_pop <-> histograma da ③
    s1=on[on.modelo_flag=='PNN(s1)']; blk={int(g):b for g,b in s1.groupby('geracao')}
    ok=tot=0; quotas=[]
    for r in gen:
        if r['estrategia']!=1: continue
        b=blk.get(int(r['geracao']))
        if b is None: continue
        h=[int((b.pred_classe==f'nivel_{k}').sum()) for k in (1,2,3,4)]
        tot+=1; ok+= int(h==list(r['n_por_nivel_pop']))
        quotas.append(tuple(r['n_por_nivel_pop']))
    o['A17_ident']=f'{ok}/{tot}'
    from collections import Counter
    o['A17_top_quota']=str(Counter(quotas).most_common(3))
    # A18 spread PNN: spr = max(pdist2(X,X))/sqrt(2n) — usa os blocos no-op (③ = conjunto de treino)
    errs=[]
    for r in gen:
        if r['estrategia']!=1 or r['count']!=0: continue
        b=blk.get(int(r['geracao']))
        if b is None: continue
        X=b[xc].values.astype(np.float64)
        from scipy.spatial.distance import pdist
        s=pdist(X).max()/np.sqrt(2*len(X))
        errs.append(abs(s-r['spr'])/r['spr'])
    o['A18_pnn_relmax']=float(np.max(errs)) if errs else np.nan; o['A18_n']=len(errs)
    # A19 sigma_dict: sigma_0(escolhido) == telemetria do ⑥
    difs={1:[],2:[],3:[]}
    for r in gen:
        if r['aceito']!=1: continue
        mf={1:'PNN(s1)',2:'RBF-global(s2)',3:'RBF-local(s3)'}[r['estrategia']]
        b=on[(on.geracao==r['geracao'])&(on.modelo_flag==mf)]
        if not len(b): continue
        pos=int(np.argmin(np.abs(b[xc].values.astype(np.float64)-Xr[r['fe']-1]).max(axis=1)))
        tel={1:r.get('cand_dist_dec'),2:r.get('hv_gain'),3:r.get('cand_eucli')}[r['estrategia']]
        if tel is None: continue
        tel=tel[0] if isinstance(tel,list) else tel
        difs[r['estrategia']].append(abs(b.sigma_0.values.astype(np.float64)[pos]-tel))
    for k in (1,2,3): o[f'A19_s{k}_max']=float(np.max(difs[k])) if difs[k] else np.nan
    # A22 cadencia por cabeca (indice de slot) + estratificada
    son=[r for r in ev if r.get('rec')=='sonda']; est=[r for r in ev if r.get('rec')=='sonda_estratificada']
    o['A22_sonda_blocos']=len(son); o['A22_estrat_blocos']=len(est)
    o['A22_falhas']=sum(1 for r in son if not r.get('ok',True))+sum(1 for r in est if not r.get('ok',True))
    return o
rows=[]
for p in ['MMF1','DTLZ2','ZDT1']:
    rows.append(one(p,f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{p}_42','POS_smoke'))
    rows.append(one(p,f'{ROOT}/resultados_experimentos/e74/{p}/42/exp_main_e74_{p}_42','PRE_s42'))
df=pd.DataFrame(rows); pd.set_option('display.width',300); pd.set_option('display.max_columns',40)
df.to_csv(f'{ROOT}/ua-dd-saea/f5/t11/baterias/e74/aspectos.csv',index=False)
print(df.T.to_string())
