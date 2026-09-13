import pandas as pd, numpy as np, json, glob, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=F5+'/baterias/b3'
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
probs=sorted(os.listdir(ROOT))
tr=[]
for pr in probs:
    j=json.load(open(f'{F5}/trajetorias/main_b3_{pr}_42.json'))
    a=np.array([c['igd_plus'] for c in j]); fe=np.array([c['fe'] for c in j])
    hv=np.array([c['hv'] for c in j]); nd=np.array([c['n_nd'] for c in j])
    d=np.diff(a); v=int((d>1e-12).sum())
    tr.append(dict(problema=pr,n_cp=len(a),viol_igd=v,igd_0=a[0],igd_f=a[-1],
        pior_salto=float(d.max()),ganho=float(a[0]/a[-1]) if a[-1]>0 else np.nan,
        hv_f=hv[-1],nd_f=int(nd[-1]),viol_hv=int((np.diff(hv)<-1e-12).sum()),fe_f=int(fe[-1])))
T=pd.DataFrame(tr); T.to_csv(OUT+'/b3_trajetorias.csv',index=False)
pd.set_option('display.width',300)
print('=== TRAJETORIAS (20 checkpoints) ==='); print(T.round(4).to_string())
print('total violacoes IGD+:',T.viol_igd.sum(),'em',int((T.n_cp-1).sum()),'transicoes | celulas com 0 violacoes:',int((T.viol_igd==0).sum()),'/',len(T))
print('violacoes HV (queda):',T.viol_hv.sum())
# sonda oficial
sd=pd.read_csv(F5+'/sonda_f52e.csv'); s3=sd[(sd.exp=='main')&(sd.alg=='b3')]
print('\nlinhas sonda b3:',len(s3),'| celulas:',s3.problema.nunique())
g=s3.groupby(['problema','bloco']).agg(wape=('wape','mean'),corr=('corr','mean'),cob=('cobertura95','mean'),ftm=('fe_treino_max','max'),nval=('n_validas','sum'),nnan=('n_nan','sum')).reset_index()
res=[]
for pr,gg in g.groupby('problema'):
    gg=gg.sort_values('bloco')
    res.append(dict(problema=pr,nb=len(gg),wape_p=gg.wape.iloc[0],wape_u=gg.wape.iloc[-1],
        dWAPE_pct=round(100*(gg.wape.iloc[-1]/gg.wape.iloc[0]-1),1),corr_p=gg['corr'].iloc[0],corr_u=gg['corr'].iloc[-1],
        cob_p=gg.cob.iloc[0],cob_u=gg.cob.iloc[-1],wape_cv=gg.wape.std()/max(gg.wape.mean(),1e-12),
        ftm_p=int(gg.ftm.iloc[0]),ftm_u=int(gg.ftm.iloc[-1]),nnan=int(gg.nnan.sum())))
S=pd.DataFrame(res); S.to_csv(OUT+'/b3_sonda_resumo.csv',index=False)
print('\n=== SONDA f52e (media dos objetivos) ==='); print(S.round(4).to_string())
print('mediana dWAPE:',round(S.dWAPE_pct.median(),1),'% | piora em',int((S.dWAPE_pct>0).sum()),'/',len(S),
      '| cobertura mediana 1o',round(S.cob_p.median(),3),'ultimo',round(S.cob_u.median(),3),'| sigma-NaN total',S.nnan.sum())
# Fig.9: tempo de treino constante
ft=[]
for pr in probs:
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    t=pd.read_parquet(b+'__timing.parquet')
    y=t.tempo_fit_s.to_numpy(); x=np.arange(1,len(y)+1)
    sl=np.polyfit(x,y,1)[0]
    ft.append(dict(problema=pr,n=len(y),fit_med=float(np.median(y)),fit_cv=float(y.std()/y.mean()),
        slope_por_ciclo=float(sl),slope_rel_pct=float(100*sl*len(y)/np.median(y)),
        fit_p=float(y[0]),fit_u=float(y[-1]),n_treino=int(t.n_acumulado.iloc[0]),
        frac_fit=float(t.tempo_fit_s.sum()/t.tempo_geracao_s.sum()),
        frac_busca=float(t.tempo_busca_s.sum()/t.tempo_geracao_s.sum())))
FT=pd.DataFrame(ft); FT.to_csv(OUT+'/b3_fig9_tempo_treino.csv',index=False)
print('\n=== FIG.9 tempo de treino ==='); print(FT.round(4).to_string())
print('mediana |slope rel| ao longo do run:',round(FT.slope_rel_pct.abs().median(),2),'%')
