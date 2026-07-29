import pandas as pd, numpy as np, json, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=F5+'/baterias/b3'
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
# 1) dWAPE por objetivo (reconciliar com o +4% do RELATORIO_F5 5.5)
sd=pd.read_csv(F5+'/sonda_f52e.csv'); s3=sd[(sd.exp=='main')&(sd.alg=='b3')]
rr=[]
for (pr,ob),gg in s3.groupby(['problema','obj']):
    gg=gg.sort_values('bloco'); rr.append(dict(problema=pr,obj=ob,d=gg.wape.iloc[-1]/gg.wape.iloc[0]-1))
R=pd.DataFrame(rr)
print('dWAPE por (celula,objetivo): mediana %.1f%%  n=%d ; por celula(media obj): mediana %.1f%%'%(
    100*R.d.median(),len(R),100*R.groupby('problema').d.mean().median()))
print('quartis por (cel,obj):',np.round(100*R.d.quantile([.25,.5,.75]).values,1))
# 2..6
rows=[];ff=[]
for pr in sorted(os.listdir(ROOT)):
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]; D,M=hdr['D'],hdr['M']
    gens=[x for x in recs if x['rec']=='b3_gen']; guards=[x for x in recs if x['rec']=='guard']
    xc=[f'x{j}' for j in range(D)]; sgc=[f'sigma_{j}' for j in range(M)]
    r=pd.read_parquet(b+'__real.parquet'); RX=r[xc].to_numpy()
    s=pd.read_parquet(b+'__surrogate.parquet'); on=s[s.regime=='online'].reset_index(drop=True)
    Flag=np.array([g['Flag'] for g in gens]); dl=m['params']['delta']
    NumV1=np.array([g['NumV1'] for g in gens]); NumV2=np.array([g['NumV2'] for g in gens])
    ramo=np.array([g['ramo'] for g in gens])
    d=dict(problema=pr,D=D,M=M,n=len(gens),delta=dl)
    d['flag_gt0']=int((Flag>0).sum()); d['flag_gt_delta']=int((Flag>dl).sum())
    d['zona_cinza']=int(((Flag>0)&(Flag<=dl)).sum())
    d['V1_eq_prevV2']=int(sum(1 for i in range(1,len(gens)) if NumV1[i]==NumV2[i-1]))
    d['V1_med']=float(np.median(NumV1)); d['V2_med']=float(np.median(NumV2))
    d['V1_range']=f'{NumV1.min()}-{NumV1.max()}'; d['V2_range']=f'{NumV2.min()}-{NumV2.max()}'
    d['V1_const']=int(len(set(NumV1.tolist()))==1)
    # cache no init (c0)
    ch=[x['fe'] for x in guards if x['name']=='cache_hit']; ini=11*D-1
    d['c0']=sum(1 for f in ch if f<=ini); d['ch_tot']=len(ch); d['ch_fes']=str(ch[:3])
    # dist_min_arquivo: identidade com a (1) pre-ciclo
    ok=0; tot=0; mx=0.0
    for g in gens:
        fe0=g['fe']-5; blk=on[on.geracao==g['geracao']]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True); idx=[i-1 for i in g['index']]
        SX=last.iloc[idx][xc].to_numpy().astype(np.float64)
        A=RX[:fe0].astype(np.float64)
        if len(A)==0: continue
        dd=np.sqrt(((SX[:,None,:]-A[None,:,:])**2).sum(-1)).min(1)
        e=np.abs(dd-np.array(g['dist_min_arquivo']))/np.maximum(np.array(g['dist_min_arquivo']),1e-12)
        mx=max(mx,float(e.max())); ok+=int((e<1e-4).all()); tot+=1
    d['dmin_ok']=ok; d['dmin_n']=tot; d['dmin_maxrel']=mx
    # separacao do switch: percentil de meanMSE e de apd
    pin=[];pap=[];ain=[];aap=[]
    for g in gens:
        blk=on[on.geracao==g['geracao']]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True); idx=[i-1 for i in g['index']]
        mm=(last[sgc].to_numpy().astype(np.float64)**2).mean(1)
        pc=float(np.mean([(mm<mm[i]).mean() for i in idx]))
        (pin if g['ramo']=='incerteza' else pap).append(pc)
        (ain if g['ramo']=='incerteza' else aap).append(float(np.median(g['apd_sel'])))
    d['pct_inc']=float(np.mean(pin)) if pin else np.nan; d['pct_apd']=float(np.mean(pap)) if pap else np.nan
    d['apdmed_inc']=float(np.median(ain)) if ain else np.nan; d['apdmed_apd']=float(np.median(aap)) if aap else np.nan
    d['n_front1_p']=gens[0]['n_front1']; d['n_front1_u']=gens[-1]['n_front1']
    rows.append(d); print('.',end='',flush=True)
print()
E=pd.DataFrame(rows); E.to_csv(OUT+'/b3_extras.csv',index=False)
pd.set_option('display.width',420); pd.set_option('display.max_columns',50)
print(E.to_string())
print()
print('c0==1 em',(E.c0==1).sum(),'/25 ; c0==2 em',(E.c0==2).sum())
print('dist_min_arquivo fecha em',E.dmin_ok.sum(),'/',E.dmin_n.sum(),'ciclos; max err rel',E.dmin_maxrel.max())
print('NumV1==NumV2 do ciclo anterior:',E.V1_eq_prevV2.sum(),'de',int((E.n-1).sum()),'transicoes')
