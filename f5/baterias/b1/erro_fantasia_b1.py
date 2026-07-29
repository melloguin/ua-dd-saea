"""Erro de fantasia ESCALAR do infill, corrigido: usa best_sid -> (1) (vale tambem nas
iteracoes cache-hit) e a regua (lambda,min,max) da PROPRIA iteracao. + n_pool_ga."""
import json, os
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs=sorted([p for p in os.listdir(ROOT) if not p.startswith(('_','.')) and p!='WFG1'])
rows=[];cells=[]
for p in probs:
    base=f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    evs=[json.loads(l) for l in open(base+'.jsonl')]
    hdr=[e for e in evs if e['rec']=='header'][0]; ge=[e for e in evs if e['rec']=='b1_gen']
    D,M=hdr['D'],hdr['M']
    real=pd.read_parquet(base+'__real.parquet').sort_values('fe_index')
    fc=[f'f{i}' for i in range(M)]
    Fmap=dict(zip(real.solution_id.values, real[fc].values.astype(np.float64)))
    npg_ok=0
    for e in ge:
        lam=np.array(e['lambda']); mn=np.array(e['norm_min']); mx=np.array(e['norm_max'])
        rng=np.where(mx-mn==0,1.0,mx-mn)
        f=Fmap[e['best_sid']]; fn=(f-mn)/rng
        pc=float((fn*lam).max()+0.05*(fn*lam).sum())
        rows.append(dict(problema=p,geracao=e['geracao'],mu_best=e['mu_best'],pc_real=pc,
                         err=e['mu_best']-pc, abserr=abs(e['mu_best']-pc), gbest=e['gbest'],
                         sigma_best=e['sigma_best'],
                         dentro_2s=abs(e['mu_best']-pc)<=1.96*e['sigma_best'],
                         melhorou=pc<e['gbest']))
        npg_ok += int(e.get('n_pool_ga')==e['ga_pop'])
    d=pd.DataFrame([r for r in rows if r['problema']==p])
    cells.append(dict(problema=p,n=len(d),err_med=float(d.abserr.median()),
                      err_rel_med=float((d.abserr/d.pc_real.abs().clip(lower=1e-12)).median()),
                      otimista=float((d.err<0).mean()),dentro2s=float(d.dentro_2s.mean()),
                      melhorou=float(d.melhorou.mean()),npg_ok=npg_ok))
    print(f"{p:10s} |err|med={d.abserr.median():.4f} otimista={(d.err<0).mean():.3f} "
          f"dentro2sigma={d.dentro_2s.mean():.3f} melhorou_gbest={d.melhorou.mean():.3f} n_pool_ga==ga_pop {npg_ok}/{len(ge)}")
pd.DataFrame(rows).to_csv(f'{OUT}/b1_fantasia_iter.csv',index=False)
cd=pd.DataFrame(cells); cd.to_csv(f'{OUT}/b1_fantasia.csv',index=False)
print(); print('otimista: mediana',cd.otimista.median(),'min',cd.otimista.min(),'max',cd.otimista.max())
print('|err| mediano por celula:',cd.err_med.min(),'-',cd.err_med.max(),'mediana',cd.err_med.median())
print('dentro de 2sigma:',cd.dentro2s.median(), 'min',cd.dentro2s.min(),'max',cd.dentro2s.max())
print('infill melhorou o gbest em (mediana):',cd.melhorou.median(),'min',cd.melhorou.min(),'max',cd.melhorou.max())
print('n_pool_ga==ga_pop total:',cd.npg_ok.sum(),'/',cd.n.sum())
