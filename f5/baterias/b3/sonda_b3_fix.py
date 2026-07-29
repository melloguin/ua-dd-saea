import pandas as pd, numpy as np, json, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=F5+'/baterias/b3'
sd=pd.read_csv(F5+'/sonda_f52e.csv'); s=sd[(sd.exp=='main')&(sd.alg=='b3')].copy()
s['bloco']=s.bloco.astype(int)   # ATENCAO: bloco vem como string no CSV -> ordenacao lexicografica engana
g=s.groupby(['problema','bloco']).agg(wape=('wape','mean'),corr=('corr','mean'),cob=('cobertura95','mean'),
    ftm=('fe_treino_max','max'),nnan=('n_nan','sum')).reset_index()
res=[]
for pr,gg in g.groupby('problema'):
    gg=gg.sort_values('bloco')
    res.append(dict(problema=pr,nb=len(gg),wape_p=gg.wape.iloc[0],wape_u=gg.wape.iloc[-1],
        dWAPE=round(100*(gg.wape.iloc[-1]/gg.wape.iloc[0]-1),1),
        wape_min=gg.wape.min(),wape_max=gg.wape.max(),wape_cv=gg.wape.std()/gg.wape.mean(),
        corr_p=gg['corr'].iloc[0],corr_u=gg['corr'].iloc[-1],cob_p=gg.cob.iloc[0],cob_u=gg.cob.iloc[-1],
        cob_min=gg.cob.min(),ftm_p=int(gg.ftm.iloc[0]),ftm_u=int(gg.ftm.iloc[-1]),nnan=int(gg.nnan.sum())))
S=pd.DataFrame(res); S.to_csv(OUT+'/b3_sonda_resumo.csv',index=False)
pd.set_option('display.width',400); pd.set_option('display.max_columns',40)
print(S.round(4).to_string())
print('\nmediana dWAPE por celula: %.1f%% | por (cel,obj): %.1f%% | piora em %d/25 | CV mediano do WAPE %.3f'%(
    S.dWAPE.median(), 100*s.sort_values('bloco').groupby(['problema','obj']).wape.agg(lambda x: x.iloc[-1]/x.iloc[0]-1).median(),
    (S.dWAPE>0).sum(), S.wape_cv.median()))
print('cobertura mediana 1o bloco %.3f -> ultimo %.3f ; celulas com cob_u<0.90: %d ; sigma-NaN: %d'%(
    S.cob_p.median(),S.cob_u.median(),(S.cob_u<0.90).sum(),S.nnan.sum()))
print('corr mediana 1o %.3f -> ultimo %.3f'%(S.corr_p.median(),S.corr_u.median()))
print('fe_treino_max: constante por celula?', bool((S.ftm_p<S.ftm_u).all()))
