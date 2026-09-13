import json, os, numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
rows=[]; cel=[]
for prob in sorted(x for x in os.listdir(ROOT) if os.path.isdir(f"{ROOT}/{x}")):
    p=f"{ROOT}/{prob}/42"
    if not os.path.isdir(p): continue
    jl=[f for f in os.listdir(p) if f.endswith('.jsonl')]
    if not jl: continue
    D=None; ruins=0; gens=[]
    for l in open(f'{p}/{jl[0]}'):
        l=l.strip()
        if not l: continue
        try: r=json.loads(l)
        except Exception: ruins+=1; continue
        if r.get('rec')=='header': D=r['D']; M=r['M']
        if r.get('rec')=='b1_gen': gens.append(r)
    nDoE=11*D-1
    for r in gens:
        e0=r.get('e0_trace') or []
        e0=np.asarray(e0,dtype=float)
        n_tr=r['n_treino']; n_ar=r['n_arquivo']
        # massa esperada de pais-DoE no ramo crossover da 1a geracao interna:
        # indices ~ min(U1,U2) uniformes em 1..n_tr  => P(idx<=k)=1-((n_tr-k)/n_tr)^2
        k=min(nDoE,n_tr)
        p_doe=1-((n_tr-k)/n_tr)**2
        rows.append(dict(problema=prob,D=D,M=M,geracao=r['geracao'],
            n_treino=n_tr,n_arquivo=n_ar,ga_iters=r['ga_iters'],ga_pop=r['ga_pop'],
            e0_len=len(e0), e0_const=bool(len(e0)>0 and np.nanmax(e0)==np.nanmin(e0)),
            e0_arg0=bool(len(e0)>0 and int(np.nanargmin(e0))==0),
            e0_ganho=float(e0[0]-np.nanmin(e0)) if len(e0) else np.nan,
            ei_best=r['ei_best'],
            inalcancavel=n_ar-n_tr, frac_inalc=(n_ar-n_tr)/n_ar, p_doe=p_doe, nDoE=nDoE))
    cel.append(dict(problema=prob,D=D,M=M,n_gen=len(gens),ruins=ruins))
d=pd.DataFrame(rows); c=pd.DataFrame(cel)
d.to_csv('b1_torneio_iters.csv',index=False)
print(c.to_string())
print('\nTOTAL iteracoes lidas:',len(d),' (celulas:',d.problema.nunique(),')')
ok=d[d.problema!='WFG1']
print('\n=== ERRATA 16 / e0_trace — s42 SEM WFG1 (n=%d) ==='%len(ok))
print('e0_trace CONSTANTE (global): %d/%d = %.1f%%'%(ok.e0_const.sum(),len(ok),100*ok.e0_const.mean()))
print('"1a geracao venceu" (argmin e0 == 0): %d/%d = %.1f%%'%(ok.e0_arg0.sum(),len(ok),100*ok.e0_arg0.mean()))
both=(ok.e0_arg0&ok.e0_const).sum()
print('1a venceu E e0 constante: %d  => 1a venceu com melhora real: %d (%.2f%% do total)'%(both,ok.e0_arg0.sum()-both,100*(ok.e0_arg0.sum()-both)/len(ok)))
print('=> "inerte" no criterio T11: %.2f%%'%(100*(1-(ok.e0_arg0.sum()-both)/len(ok))))
print('\npor celula (frac 1a-venceu | frac e0 const | ga_iters medio):')
g=ok.groupby('problema').agg(n=('geracao','size'),D=('D','first'),ga_it=('ga_iters','median'),
    f_arg0=('e0_arg0','mean'),f_const=('e0_const','mean'),f_ambos=('e0_arg0',lambda s:0))
g['f_arg0_real']=ok.groupby('problema').apply(lambda x:((x.e0_arg0)&(~x.e0_const)).mean())
g['frac_inalc']=ok.groupby('problema')['frac_inalc'].mean()
g['p_doe']=ok.groupby('problema')['p_doe'].mean()
print(g.drop(columns=['f_ambos']).sort_values('D').to_string(float_format=lambda v:'%.3f'%v))
print('\n=== EXPOSICAO ESTRUTURAL do torneio (todas as %d iteracoes) ==='%len(ok))
print('frac do arquivo INALCANCAVEL como pai-crossover na 1a ger interna: mediana %.3f  min %.3f  max %.3f'%(ok.frac_inalc.median(),ok.frac_inalc.min(),ok.frac_inalc.max()))
print('P(pai da 1a ger interna ser ponto do DoE): mediana %.4f  min %.4f  max %.4f'%(ok.p_doe.median(),ok.p_doe.min(),ok.p_doe.max()))
print('iteracoes com n_treino <= nDoE (=> 100%% dos pais sao DoE):',int((ok.n_treino<=ok.nDoE).sum()))
print('\npeso relativo da 1a geracao interna: 1/ga_iters — mediana %.4f; por D:'%(1/ok.ga_iters).median())
print(ok.groupby('D').ga_iters.median().to_string())
