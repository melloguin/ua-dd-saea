"""Query-joia re-medida: index -> ultima sub-pop do ciclo na ③ -> sigma do selecionado."""
import json, os, numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
rows=[]
for prob in sorted(os.listdir(ROOT)):
    base=f'{ROOT}/{prob}/42/exp_main_b3_{prob}_42'
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    gens=[x for x in L if x.get('rec')=='b3_gen']
    hdr=[x for x in L if x.get('rec')=='header'][0]; M=hdr['M']
    s3=pd.read_parquet(base+'__surrogate.parquet')
    on=s3[s3.regime=='online']
    sig=[f'sigma_{j}' for j in range(M)]
    n_ok=0; n_tot=0; maxrel=0.0
    for g in gens:
        blk=on[on.geracao==g['geracao']]
        k=g['pop_por_w'][-1]
        last=blk.iloc[-k:]
        S=last[sig].to_numpy(float)
        sq=np.array(g['sigma_sel']['sqrtmse_por_objetivo'],float)
        if sq.ndim==1: sq=sq.reshape(len(g['index']),-1)
        for i,idx in enumerate(g['index']):
            n_tot+=1
            a=S[int(idx)-1]; b=sq[i]
            rel=np.max(np.abs(a-b)/np.maximum(np.abs(b),1e-12))
            maxrel=max(maxrel,rel)
            if rel<1e-5: n_ok+=1
    # saude da ③
    nan_sig=int(s3[sig].isna().sum().sum()); neg=int((s3[sig].to_numpy(float)<0).sum())
    mu=[f'mu_{j}' for j in range(M)]
    nan_mu=int(s3[mu].isna().sum().sum())
    zero_sig=int((s3[sig].to_numpy(float)==0).all(1).sum())
    rsid_on=float(on.real_solution_id.notna().mean())
    rows.append(dict(problema=prob,M=M,n_sel=n_tot,n_ok=n_ok,max_rel=maxrel,
                     linhas3=len(s3),linhas_online=len(on),
                     linhas_sonda=int((s3.regime=='sonda').sum()),
                     nan_sigma=nan_sig,sigma_negativo=neg,nan_mu=nan_mu,
                     linhas_sigma_zero=zero_sig,frac_rsid_online=rsid_on))
    print(rows[-1])
df=pd.DataFrame(rows); df.to_csv('joia_s42.csv',index=False)
print('\nTOTAL selecoes',df.n_sel.sum(),'OK',df.n_ok.sum(),'max_rel',df.max_rel.max())
print('linhas ③',df.linhas3.sum(),'online',df.linhas_online.sum(),'sonda',df.linhas_sonda.sum())
print('NaN sigma',df.nan_sigma.sum(),'sigma<0',df.sigma_negativo.sum(),'NaN mu',df.nan_mu.sum())
print('linhas sigma==0',df.linhas_sigma_zero.sum(), df[df.linhas_sigma_zero>0].problema.tolist())
