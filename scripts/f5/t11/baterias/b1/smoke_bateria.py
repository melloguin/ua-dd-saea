"""Bateria de identidades do mecanismo sobre o SMOKE T11 (codigo de hoje) —
mesma logica da bateria_b1.py da F5. READ-ONLY."""
import json, math, numpy as np, pandas as pd
from scipy.stats import norm as _norm
CASOS={'SMOKE-T11':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1',
       'G6-COM':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b1',
       'G6-SEM':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/b1',
       'S42':'/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42'}
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
for tag,P in CASOS.items():
    base=f'{P}/exp_main_b1_MMF1_42'
    man=json.load(open(base+'.manifest.json'))
    raw=open(base+'.jsonl').read().splitlines(); evs=[]; ruins=0
    for l in raw:
        if not l.strip(): continue
        try: evs.append(json.loads(l))
        except Exception: ruins+=1
    hdr=[e for e in evs if e['rec']=='header'][0]; D,M=hdr['D'],hdr['M']
    ftr=[e for e in evs if e['rec']=='footer']; ge=[e for e in evs if e['rec']=='b1_gen']
    gu=[e for e in evs if e['rec']=='guard']; so=[e for e in evs if e['rec']=='sonda']
    real=pd.read_parquet(base+'__real.parquet').sort_values('fe_index').reset_index(drop=True)
    tim=pd.read_parquet(base+'__timing.parquet'); pop=pd.read_parquet(base+'__pop.parquet')
    s3=pd.read_parquet(base+'__surrogate.parquet')
    xc=[f'x{i}' for i in range(D)]; fc=[f'f{i}' for i in range(M)]
    F=real[fc].values.astype(float); SID=real.solution_id.values
    XR=real[xc].values.astype(np.float32)
    doe=pd.read_parquet(f'{DOE}/MMF1/doe_MMF1_42.parquet')
    dX=np.abs(doe[xc].values.astype(np.float32)-XR[:len(doe)]).max()
    dm=json.load(open(f'{DOE}/MMF1/doe_MMF1_42.manifest.json'))
    cap=11*D-1+25; n_iter=len(ge); res={}
    ok_ei=ok_gb=ok_nm=ok_sub=ok_ga=ok_na=ok_sid=0; thlo=1e9; thhi=-1e9; mse=ein=ng=0; cachez=0
    for e in ge:
        fe=e['fe']; na=e['n_arquivo']; g=e['geracao']
        lam=np.array(e['lambda']); nmin=np.array(e['norm_min']); nmax=np.array(e['norm_max'])
        rng=np.where((nmax-nmin)==0,1.0,nmax-nmin)
        def probe(n):
            A=F[:n]; a=np.abs(A.min(0)-nmin).max()/max(abs(nmin).max(),1e-12)
            b=np.abs(A.max(0)-nmax).max()/max(abs(nmax).max(),1e-12)
            Fn=(A-nmin)/rng; pc=(Fn*lam).max(1)+0.05*(Fn*lam).sum(1)
            return a,b,abs(pc.min()-e['gbest'])
        p0=probe(fe-1); p1=probe(fe) if fe<=len(F) else (np.inf,)*3
        dmin,dmax,dg=(p1 if sum(p1)<sum(p0)*0.5 else p0)
        mu,sg,gb=e['mu_best'],e['sigma_best'],e['gbest']
        z=(gb-mu)/sg; ei=(gb-mu)*_norm.cdf(z)+sg*_norm.pdf(z); tgt=-e['ei_best']
        ok_ei+= abs(ei-tgt)/max(abs(tgt),1e-300)<1e-6
        ok_gb+= dg<1e-6; ok_nm+= (dmin<1e-5 and dmax<1e-5)
        ok_sub+= (e['n_treino']==e['n_subset']-e['n_dedup']) and (e['n_subset']==min(na,cap))
        ok_ga += (e['ga_iters']==math.ceil(10000/e['ga_pop'])) and (e['ga_pop']-2*na in (0,-2))
        ok_na += (na==11*D-1+g-1)
        ok_sid+= (e['best_sid']==SID[fe-1]) if fe-1<len(SID) else 0
        thlo=min(thlo,e['theta_min']); thhi=max(thhi,e['theta_max'])
        mse+=e.get('n_mse_neg',0); ein+=e.get('n_ei_nan',0); ng+=int(bool(e.get('nan_guard',0)))
        cachez+= (e.get('dist_min_arquivo')==0)
    from collections import Counter
    gn=Counter(g['name'] for g in gu); c0=sum(1 for g in gu if g['name']=='cache_hit' and g.get('fe')==1)
    esp={1}|{x for x in range(2,n_iter+1) if x%2==0}|{n_iter}
    print('=== %s ==='%tag)
    print(' ⑥ linhas=%d malformadas=%d footer=%s | ①=%d (31D-1=%d) init=%d dX=%.1e hash=%s'%(
        len(raw),ruins,bool(ftr),len(real),31*D-1,(real.fase=='init').sum(),dX,dm['doe_hash']==man['doe_hash']))
    print(' n_iter=%d cache=%d c0=%d ledger(%d=%d+%d-%d)=%s | ②gens=%d(=n+1:%s) ④=%d ③on=%d ③sonda=%d blocos=%d'%(
        n_iter,gn.get('cache_hit',0),c0,n_iter,31*D-1-(11*D-1),gn.get('cache_hit',0),c0,
        n_iter==(31*D-1-(11*D-1))+gn.get('cache_hit',0)-c0,pop.geracao.nunique(),pop.geracao.nunique()==n_iter+1,
        len(tim),(s3.regime=='online').sum(),(s3.regime=='sonda').sum(),s3[s3.regime=='sonda'].geracao.nunique()))
    print(' F1 EI=%d/%d | B2 gbest=%d | B3 norm=%d | B5 subset=%d | B7 GA=%d | B12 n_arq=%d | F2 sid=%d/%d'%(
        ok_ei,n_iter,ok_gb,ok_nm,ok_sub,ok_ga,ok_na,ok_sid,n_iter-cachez))
    print(' B8 theta=[%.1e,%.4f] | B6 mse_neg=%d ei_nan=%d nan_guard=%d sig<0=%d sig NaN=%d mu NaN=%d'%(
        thlo,thhi,mse,ein,ng,(s3.sigma_0<0).sum(),s3.sigma_0.isna().sum(),s3.mu_0.isna().sum()))
    print(' U4 cadencia manif==formula: %s (%d blocos) | U7 fit+busca<=ger: %d/%d | B11 dist0=%d (cache-c0=%d)'%(
        set(man['sonda']['geracoes'])==esp,len(man['sonda']['geracoes']),
        int((tim.tempo_fit_s+tim.tempo_busca_s<=tim.tempo_geracao_s+1e-12).sum()),len(tim),
        cachez,gn.get('cache_hit',0)-c0))
    print(' ⑤ schema=%s campanha_id=%s repo_hash=%s | D47 mu_1/sig_1 nulos=%s | regimes=%s'%(
        man.get('schema_version'),man.get('campanha_id','<AUSENTE>'),(man.get('repo_hash') or '<VAZIO>')[:12],
        all(s3[c].isna().all() for c in s3.columns if c.startswith(('mu_','sigma_')) and c not in ('mu_0','sigma_0')),
        sorted(s3.regime.unique())))
