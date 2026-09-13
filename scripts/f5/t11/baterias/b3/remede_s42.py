"""RE-MEDICAO T11 do corpus s42 do b3 (25 celulas). READ-ONLY."""
import json, glob, os, numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
out=[]
for prob in sorted(os.listdir(ROOT)):
    d=f'{ROOT}/{prob}/42'
    base=f'{d}/exp_main_b3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    L=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[x for x in L if x.get('rec')=='header'][0]
    ftr=[x for x in L if x.get('rec')=='footer']
    gens=[x for x in L if x.get('rec')=='b3_gen']
    guards=[x for x in L if x.get('rec')=='guard']
    sond=[x for x in L if x.get('rec')=='sonda']
    D,M,N=hdr['D'],hdr['M'],hdr['N_vetores']
    real=pd.read_parquet(base+'__real.parquet')
    tim=pd.read_parquet(base+'__timing.parquet')
    r={'problema':prob,'D':D,'M':M,'N':N,'maxfe':man['maxfe'],'fe_final':man['fe_final'],
       'n_linhas_1':len(real),'n_init':(real.fase=='init').sum(),'esperado_init':11*D-1,
       'ok_fe':len(real)==31*D-1 and man['fe_final']==31*D-1,
       'fe_index_denso':bool((real.fe_index.to_numpy()==np.arange(len(real))).all()),
       'sid_unicos':real.solution_id.nunique()==len(real),
       'termino':ftr[0]['termino'] if ftr else None,'status':man['status'],
       'n_ciclos':len(gens),'cache_hits':man['cache_hits'],
       'n_cachehit_guard':sum(1 for g in guards if g['name']=='cache_hit'),
       'c0':sum(1 for g in guards if g['name']=='cache_hit' and g.get('fe')==1),
       'hard_stop':sum(1 for g in guards if g['name']=='hard_stop'),
       'n_blocos_sonda':len(sond),'sonda_manif':man['sonda']['n_blocos'],
       'tem_campanha_id':'campanha_id' in man,'tem_desligada':'desligada' in man.get('sonda',{}),
       'tem_adapt_dv':any('adapt_delta_V' in g for g in gens),
       'tem_params':'params' in man,'tem_sigma_dict':'sigma_dict' in man,
      }
    # invariantes de ciclo
    delta=0.05*N
    ok_flag=all(g['Flag']==g['NumV2']-g['NumV1'] for g in gens)
    ok_ramo=all(g['ramo']==('APD' if g['Flag']<=delta else 'incerteza') for g in gens)
    ok_delta=all(abs(g['delta']-delta)<1e-9 for g in gens)
    r['ok_Flag']=ok_flag; r['ok_ramo']=ok_ramo; r['ok_delta']=ok_delta
    r['n_incerteza']=sum(1 for g in gens if g['ramo']=='incerteza')
    r['ok_wmax20']=all(len(g['pop_por_w'])==20 for g in gens)
    r['ok_u']=all(g['u_alvo']==5 and g['u_efetivo']==5 for g in gens)
    r['nzero_tot']=sum(g['nzero_updata'] for g in gens)
    r['nvet_vazios_tot']=sum(g['n_vetores_vazios'] for g in gens)
    r['ok_ntreino']=all(g['n_treino']==11*D-1 and g['arquivo']==11*D-1 for g in gens)
    # criterio_meanMSE == media das variancias
    errs=[]
    for g in gens:
        ss=g['sigma_sel']; cm=np.array(ss['criterio_meanMSE'],float)
        sq=np.array(ss['sqrtmse_por_objetivo'],float)
        if sq.ndim==1: sq=sq.reshape(len(cm),-1)
        rec=(sq**2).mean(1)
        with np.errstate(divide='ignore',invalid='ignore'):
            e=np.abs(rec-cm)/np.maximum(np.abs(cm),1e-300)
        errs.append(np.nanmax(e))
    r['max_err_meanMSE']=float(np.nanmax(errs)); r['n_sel']=sum(len(g['index']) for g in gens)
    # NumV1(k) vs NumV2(k-1)
    tr=sum(1 for a,b in zip(gens,gens[1:]) if b['NumV1']==a['NumV2'])
    r['transicoes']=len(gens)-1; r['NumV1_eq_NumV2ant']=tr
    # fe_treino_max monotonico e == fe_anterior-1
    ftm=[g['fe_treino_max'] for g in gens]
    r['ftm_monotonico']=all(b>a for a,b in zip(ftm,ftm[1:]))
    fes=[11*D-1]+[g['fe'] for g in gens[:-1]]
    r['ftm_eq_feprev_menos1']=all(f==fp-1 for f,fp in zip(ftm,fes))
    # timing
    r['n_timing']=len(tim)
    r['viol_timing']=int(((tim.tempo_fit_s+tim.tempo_busca_s)>tim.tempo_geracao_s).sum())
    # cadencia da sonda
    G=len(gens)+(1 if r['hard_stop']>0 else 0)
    esp=sorted(set([1]+[g for g in range(2,G+1) if g%2==0]+[G]))
    r['cadencia_ok']=(sorted(man['sonda']['geracoes'])==esp)
    r['G']=G
    # resto do orcamento
    r['resto']=man['maxfe']-gens[-1]['fe']
    r['hs_sse_resto']= (r['hard_stop']>0)==(r['resto']>0)
    out.append(r)
df=pd.DataFrame(out)
df.to_csv('remede_s42.csv',index=False)
pd.set_option('display.width',250,'display.max_columns',60)
print(df[['problema','D','M','N','n_ciclos','n_incerteza','resto','hard_stop','hs_sse_resto','cadencia_ok','ok_Flag','ok_ramo','ok_wmax20','ok_u','nzero_tot','max_err_meanMSE','viol_timing','ftm_monotonico','transicoes','NumV1_eq_NumV2ant']].to_string(index=False))
print('\n=== agregados ===')
print('celulas',len(df),'ciclos',df.n_ciclos.sum(),'selecoes',df.n_sel.sum())
for c in ['ok_fe','fe_index_denso','sid_unicos','ok_Flag','ok_ramo','ok_delta','ok_wmax20','ok_u','ok_ntreino','ftm_monotonico','ftm_eq_feprev_menos1','cadencia_ok','hs_sse_resto','tem_params','tem_sigma_dict','tem_campanha_id','tem_desligada','tem_adapt_dv']:
    print(f'  {c}: {df[c].sum()}/{len(df)}')
print('  nzero total',df.nzero_tot.sum(),' n_vet_vazios',df.nvet_vazios_tot.sum())
print('  viol_timing total',df.viol_timing.sum(),' max err meanMSE',df.max_err_meanMSE.max())
print('  c0=1 em',(df.c0==1).sum(),'/25 ; cache_hits guard==manifesto',(df.n_cachehit_guard==df.cache_hits).sum())
print('  ciclos incerteza',df.n_incerteza.sum(),'de',df.n_ciclos.sum())
print('  transicoes NumV1==NumV2ant',df.NumV1_eq_NumV2ant.sum(),'de',df.transicoes.sum())
