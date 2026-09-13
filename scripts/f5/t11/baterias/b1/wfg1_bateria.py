"""WFG1 (b1) — bateria de identidades sobre as camadas INTEGRAS + os 374 eventos
sobreviventes do ⑥. READ-ONLY. Espelha bateria_b1.py da F5."""
import json, math, numpy as np, pandas as pd
from scipy.stats import norm as _norm
P='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/WFG1/42'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
base=f'{P}/exp_main_b1_WFG1_42'
man=json.load(open(base+'.manifest.json'))
evs=[]
for l in open(base+'.jsonl'):
    try: evs.append(json.loads(l))
    except Exception: pass
hdr=[e for e in evs if e['rec']=='header'][0]; D,M=hdr['D'],hdr['M']
ge=[e for e in evs if e['rec']=='b1_gen']; guards=[e for e in evs if e['rec']=='guard']
real=pd.read_parquet(base+'__real.parquet').sort_values('fe_index').reset_index(drop=True)
pop=pd.read_parquet(base+'__pop.parquet'); tim=pd.read_parquet(base+'__timing.parquet')
xc=[f'x{i}' for i in range(D)]; fc=[f'f{i}' for i in range(M)]
F=real[fc].values.astype(np.float64); SID=real['solution_id'].values
XR=real[xc].values.astype(np.float32)
maxfe=31*D-1; n_init=int((real.fase=='init').sum()); cap=11*D-1+25
doe=pd.read_parquet(f'{DOE}/WFG1/doe_WFG1_42.parquet')
dX=np.abs(doe[xc].values.astype(np.float32)-XR[:len(doe)]).max()
dm=json.load(open(f'{DOE}/WFG1/doe_WFG1_42.manifest.json'))
print('U1 ①=%d (31D-1=%d) denso=%s sid_unico=%s | U2 init=%d (11D-1=%d) maxdX=%.1e hash_ok=%s'%(
    len(real),maxfe,(real.fe_index.values==np.arange(len(real))).all(),real.solution_id.is_unique,
    n_init,11*D-1,dX,dm.get('doe_hash')==man['doe_hash']))
dupX=len(real)-len(set(map(bytes,np.ascontiguousarray(XR))))
print('B13 dupX float32 na ①:',dupX)
n_iter=len(tim); print('U3 ④=%d  fit_series=%d  ③online gens=%d  ⑥ b1_gen=%d (%.1f%% do filme)'%(
    n_iter,len(man['fit_series']),443,len(ge),100*len(ge)/n_iter))
print('U10 ② gens=%d (esperado n_iter+1=%d)  linhas=%d'%(pop.geracao.nunique(),n_iter+1,len(pop)))
sz=pop.groupby('geracao').size(); print('   |②_g|=11D-1+(g-1) em %d/%d'%( (sz.values==np.arange(11*D-1,11*D-1+len(sz))).sum(),len(sz)))
gmax=pop.geracao.max(); last=pop[pop.geracao==gmax]
print('   dup na ultima ②=%d  cache_hits-1=%d'%(last.solution_id.duplicated().sum(),man['cache_hits']-1))
print('U7 ④ fit+busca<=geracao: %d/%d'%(int((tim.tempo_fit_s+tim.tempo_busca_s<=tim.tempo_geracao_s+1e-12).sum()),len(tim)))
ftm=np.array([e.get('fe_treino_max') for e in ge if e.get('fe_treino_max') is not None],float)
print('U8 fe_treino_max (⑥, %d pts) nao-monotonico: %d quedas'%(len(ftm),int((np.diff(ftm)<0).sum())))
rows=[]
for e in ge:
    g,fe=e['geracao'],e['fe']; na=e['n_arquivo']
    lam=np.array(e['lambda']); nmin=np.array(e['norm_min']); nmax=np.array(e['norm_max'])
    rng=np.where((nmax-nmin)==0,1.0,nmax-nmin)
    def probe(n):
        A=F[:n]; dmin=np.abs(A.min(0)-nmin).max()/max(np.abs(nmin).max(),1e-12)
        dmax=np.abs(A.max(0)-nmax).max()/max(np.abs(nmax).max(),1e-12)
        Fn=(A-nmin)/rng; pcv=(Fn*lam).max(1)+0.05*(Fn*lam).sum(1)
        return dmin,dmax,abs(pcv.min()-e['gbest'])
    a=probe(fe-1); b=probe(fe) if fe<=len(F) else (np.inf,)*3
    if sum(b)<sum(a)*0.5: dmin,dmax,dg=b; win='fe'
    else: dmin,dmax,dg=a; win='fe-1'
    mu,sg,gb=e['mu_best'],e['sigma_best'],e['gbest']
    z=(gb-mu)/sg if sg>0 else np.nan
    ei=(gb-mu)*_norm.cdf(z)+sg*_norm.pdf(z) if sg>0 else max(gb-mu,0)
    tgt=-e['ei_best']; rel=abs(ei-tgt)/max(abs(tgt),1e-300)
    H=99 if M==2 else 12
    rows.append(dict(g=g,fe=fe,d_gbest=dg,d_nmin=dmin,d_nmax=dmax,rel_ei=rel,win=win,
        sid_ok=(e['best_sid']==SID[fe-1]) if fe-1<len(SID) else None,
        sub_id=(e['n_treino']==e['n_subset']-e['n_dedup']), sub_ok=(e['n_subset']==min(na,cap)),
        ga_it_ok=(e['ga_iters']==math.ceil(10000/e['ga_pop'])), ga_pop_d=e['ga_pop']-2*na,
        na_ok=(na==11*D-1+g-1), th_lo=e['theta_min'],th_hi=e['theta_max'],
        mse=e.get('n_mse_neg',0),einan=e.get('n_ei_nan',0),ng=int(bool(e.get('nan_guard',0))),
        dgrid=np.abs(lam*H-np.round(lam*H)).max(), dmin_arq=e.get('dist_min_arquivo'),
        lam=tuple(np.round(lam,10))))
r=pd.DataFrame(rows); n=len(r)
print('\n--- identidades sobre os %d eventos sobreviventes ---'%n)
print('F1 EI fechado rel<1e-6: %d/%d (max rel %.2e)'%((r.rel_ei<1e-6).sum(),n,r.rel_ei.max()))
print('B2 gbest abs<1e-6: %d/%d (max %.2e)'%((r.d_gbest<1e-6).sum(),n,r.d_gbest.max()))
print('B3 norm rel<1e-5: %d/%d (max %.2e) | janela fe (cache): %d'%(((r.d_nmin<1e-5)&(r.d_nmax<1e-5)).sum(),n,np.maximum(r.d_nmin,r.d_nmax).max(),(r.win=='fe').sum()))
print('F2 best_sid==infill: %d/%d'%(r.sid_ok.sum(),r.sid_ok.notna().sum()))
print('B5 n_treino=n_subset-n_dedup: %d/%d | n_subset=min(na,cap): %d/%d'%(r.sub_id.sum(),n,r.sub_ok.sum(),n))
print('B7 ga_iters=ceil(10000/ga_pop): %d/%d | ga_pop-2*na in %s'%(r.ga_it_ok.sum(),n,sorted(r.ga_pop_d.unique())))
print('B12 n_arquivo=11D-1+(g-1): %d/%d'%(r.na_ok.sum(),n))
print('B8 theta em [1e-5,20]: violacoes=%d (min %.2e max %.4f)'%(((r.th_lo<1e-5-1e-12)|(r.th_hi>20+1e-9)).sum(),r.th_lo.min(),r.th_hi.max()))
print('B6 guards: mse_neg=%d ei_nan=%d nan_guard=%d'%(r.mse.sum(),r.einan.sum(),r.ng.sum()))
print('B1 lambda no grid: max desvio %.2e | distintos=%d de N=%d | max repet=%d'%(r.dgrid.max(),r.lam.nunique(),man['params']['N_lambda'],r.lam.value_counts().max()))
print('B11 dist_min_arquivo==0: %d'%int((r.dmin_arq==0).sum()))
s3=pd.read_parquet(base+'__surrogate.parquet')
print('\nB4 ③: linhas=%d  mu_1/sigma_1 nulos=%s  literais=%s'%(len(s3),
    all(s3[c].isna().all() for c in s3.columns if c.startswith(('mu_','sigma_')) and c not in ('mu_0','sigma_0')),
    {c:s3[c].dropna().unique().tolist()[:2] for c in ['pred_tipo','modelo_flag','espaco_modelo','transf_tipo'] if c in s3}))
sd=s3[s3.regime=='sonda']; print('   sonda: linhas=%d blocos=%d todos 2000=%s'%(len(sd),sd.groupby('geracao').size().shape[0],(sd.groupby('geracao').size()==2000).all()))
print('   sigma_0: min=%.3e  negativos=%d  NaN=%d  mu NaN=%d'%(s3.sigma_0.min(),(s3.sigma_0<0).sum(),s3.sigma_0.isna().sum(),s3.mu_0.isna().sum()))
r.to_csv('wfg1_iters.csv',index=False)
