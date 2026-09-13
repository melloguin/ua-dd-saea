"""Bateria de fidelidade b3 (K-RVEA) — F5.3b. Executa em TODAS as 25 celulas main/42.
Saida: b3_aspectos_por_celula.csv (1 linha/celula) + b3_ciclos.csv (1 linha/ciclo).
READ-ONLY sobre dados/artefatos. Escreve so em f5/baterias/b3/.
"""
import pandas as pd, json, numpy as np, os, sys
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SONDA='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b3'
probs=sorted(os.listdir(ROOT))
cel=[]; cic=[]
for pr in probs:
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]
    ftr=[x for x in recs if x['rec']=='footer'][0]
    gens=[x for x in recs if x['rec']=='b3_gen']
    sondas=[x for x in recs if x['rec']=='sonda']
    guards=[x for x in recs if x['rec']=='guard']
    D,M=hdr['D'],hdr['M']
    xc=[f'x{j}' for j in range(D)]; fc=[f'f{j}' for j in range(M)]
    muc=[f'mu_{j}' for j in range(M)]; sgc=[f'sigma_{j}' for j in range(M)]
    r=pd.read_parquet(b+'__real.parquet')
    p=pd.read_parquet(b+'__pop.parquet')
    t=pd.read_parquet(b+'__timing.parquet')
    s=pd.read_parquet(b+'__surrogate.parquet')
    on=s[s.regime=='online'].reset_index(drop=True); so=s[s.regime=='sonda']
    d=dict(problema=pr,D=D,M=M,maxfe=m['maxfe'])
    # ---- U1 orcamento
    d['U1_len1']=len(r); d['U1_ok']=(len(r)==31*D-1==m['maxfe']==m['fe_final'])
    d['U1_dense']=bool((r.fe_index.values==np.arange(len(r))).all())
    d['U1_sid_uniq']=int(r.solution_id.nunique()); d['U1_termino']=ftr['termino']
    # ---- U2 DoE
    ini=r[r.fase=='init']
    d['U2_init']=len(ini); d['U2_ok_n']=(len(ini)==11*D-1)
    try:
        A=np.load(f'{DOE}/{pr}/doe_{pr}_42.npy')
        d['U2_dX']=float(np.abs(A[:len(ini)].astype(np.float32)-ini[xc].to_numpy()).max())
        d['U2_shape']=str(A.shape)
    except Exception as e: d['U2_dX']=np.nan; d['U2_shape']='ERR:'+str(e)[:40]
    try:
        sc=json.load(open(f'{DOE}/{pr}/doe_{pr}_42.manifest.json'))
        d['U2_hash_ok']=(sc.get('sha256',sc.get('hash',''))==m['doe_hash'])
    except Exception: d['U2_hash_ok']='sidecar?'
    # X duplicados bit-a-bit na (1)
    d['U2_dupX']=int(len(ini)-len(np.unique(ini[xc].to_numpy(),axis=0)))
    d['dupX_total']=int(len(r)-len(np.unique(r[xc].to_numpy(),axis=0)))
    # ---- U3/U8 fits
    d['U3_ncic']=len(gens); d['U3_ntiming']=len(t); d['U3_nfit_series']=len(m['fit_series'])
    d['U3_ok']=(len(gens)==len(t)==len(m['fit_series']))
    d['U3_ger_seq']=bool((t.geracao.values==np.arange(1,len(t)+1)).all())
    ntr=np.array([g['n_treino'] for g in gens]); arq=np.array([g['arquivo'] for g in gens])
    d['B_A1_const']=bool((ntr==11*D-1).all() and (arq==11*D-1).all())
    d['B_nacum_const']=bool((t.n_acumulado.values==11*D-1).all())
    ftm=np.array([g['fe_treino_max'] for g in gens])
    d['U8_ftm_mono']=bool((np.diff(ftm)>=0).all()); d['U8_ftm_first']=int(ftm[0]); d['U8_ftm_last']=int(ftm[-1])
    fes=np.array([g['fe'] for g in gens]); lote=np.array([g['lote'] for g in gens]); uef=np.array([g['u_efetivo'] for g in gens])
    d['U8_ftm_eq_feprev']=bool((ftm==(fes-lote-1)).all())
    # ---- U7 timing
    viol=(t.tempo_fit_s+t.tempo_busca_s)>t.tempo_geracao_s
    d['U7_viol']=int(viol.sum())
    sg=set(m['sonda']['geracoes'])
    d['U7_viol_eq_sonda']=bool(set(t.geracao[viol])==sg) if viol.sum()>0 else (len(sg)==0)
    d['U7_pred_in_ger']=int(((t.tempo_fit_s+t.tempo_busca_s+t.tempo_pred_sonda_s)>t.tempo_geracao_s+1e-6).sum())
    # ---- U9/U10 ledger
    from collections import Counter
    gn=Counter([g['name'] for g in guards])
    d['U9_cache_guard']=gn.get('cache_hit',0); d['U9_cache_manif']=m['cache_hits']
    d['U9_ok']=(gn.get('cache_hit',0)==m['cache_hits']==ftr['cache_hits'])
    d['U9_hardstop']=gn.get('hard_stop',0)
    d['U10_sum_lote']=int(lote.sum()); d['U10_sum_uef']=int(uef.sum())
    d['U10_lote_ok']=bool(len(ini)+lote.sum()==m['maxfe'])
    d['U10_gap']=int(uef.sum()-lote.sum())
    d['U10_c0']=int(guards[0]['fe']==1 and guards[0]['name']=='cache_hit')
    d['U10_gap_vs_cache']=int(m['cache_hits']-1-d['U10_gap'])
    d['U10_pop_ngen']=int(p.geracao.nunique()); d['U10_pop_offby1']=bool(p.geracao.nunique()==len(gens)+1)
    d['U10_nger_manif']=m['n_geracoes']
    pg=p.groupby('geracao').size()
    d['U10_pop_size_rule']=bool((pg.values==11*D-1+5*(pg.index.values-1)).all())
    # ---- (3) online: blocos wmax
    nb=[len(g['pop_por_w']) for g in gens]; d['B_wmax_ok']=bool(set(nb)=={20})
    cnt_on=on.groupby('geracao').size()
    d['B_ppw_eq_rows']=bool(all(cnt_on.get(g['geracao'],-1)==sum(g['pop_por_w']) for g in gens))
    d['B_ppw_max']=int(max(max(g['pop_por_w']) for g in gens)); d['B_Nvet']=m['params']['N_vetores']
    d['B_ppw_le_N']=bool(d['B_ppw_max']<=d['B_Nvet'])
    d['B_ppw_first_mean']=float(np.mean([g['pop_por_w'][0] for g in gens]))
    d['B_ppw_last_mean']=float(np.mean([g['pop_por_w'][-1] for g in gens]))
    # ---- switch
    ramo=[g['ramo'] for g in gens]; Flag=np.array([g['Flag'] for g in gens]); dl=m['params']['delta']
    pred=np.where(Flag<=dl,'APD','incerteza')
    d['SW_consist']=int((np.array(ramo)==pred).sum()); d['SW_n']=len(gens)
    d['SW_inc']=int(sum(1 for x in ramo if x=='incerteza')); d['SW_apd']=len(gens)-d['SW_inc']
    d['SW_pct_inc']=round(100*d['SW_inc']/len(gens),1)
    d['SW_gen1']=ramo[0]; d['SW_flag_min']=int(Flag.min()); d['SW_flag_max']=int(Flag.max())
    d['SW_NumV1_eq_prev_NumV2']=int(sum(1 for i in range(1,len(gens)) if gens[i]['NumV1']==gens[i-1]['NumV2']))
    d['SW_flag_id']=int(sum(1 for g in gens if g['Flag']==g['NumV2']-g['NumV1']))
    d['SW_delta_ok']=bool(abs(dl-0.05*d['B_Nvet'])<1e-9)
    d['SW_nvv0']=int(sum(1 for g in gens if g['n_vetores_vazios']==0))
    d['SW_nzero0']=int(sum(1 for g in gens if g['nzero_updata']==0))
    # ---- query-joia
    ok_sig=0; ok_crit=0; ok_x=0; ok_mu=0; tot=0; msig=0.0; mcrit=0.0; mx=0.0
    pcts=[]; apds=[]; err_fant=[]
    for g in gens:
        ge=g['geracao']; blk=on[on.geracao==ge]
        ln=g['pop_por_w'][-1]; last=blk.iloc[len(blk)-ln:].reset_index(drop=True)
        idx=[i-1 for i in g['index']]; tot+=1
        if max(idx)>=len(last) or min(idx)<0:
            cic.append(dict(problema=pr,geracao=ge,erro='index_fora')); continue
        sel=last.iloc[idx]
        got=sel[sgc].to_numpy().astype(np.float64); exp=np.array(g['sigma_sel']['sqrtmse_por_objetivo'])
        e1=np.abs(got-exp).max(); msig=max(msig,e1); ok_sig+= (e1<1e-6)
        crit=np.array(g['sigma_sel']['criterio_meanMSE']); e2=np.abs(crit-(exp**2).mean(1)).max()/max(abs(crit).max(),1e-300)
        mcrit=max(mcrit,e2); ok_crit+=(e2<1e-12)
        # X do selecionado vs novas linhas da (1)
        fe0=g['fe']-g['lote']; newr=r[(r.fe_index>=fe0)&(r.fe_index<g['fe'])]
        if len(newr)==len(sel):
            e3=np.abs(sel[xc].to_numpy()-newr[xc].to_numpy()).max(); mx=max(mx,e3); ok_x+=(e3==0.0)
            ef=np.abs(sel[muc].to_numpy()-newr[fc].to_numpy())
            err_fant.append(np.median(ef))
        elif len(newr)>0 and len(newr)<len(sel):
            sub=sel.iloc[:len(newr)]
            e3=np.abs(sub[xc].to_numpy()-newr[xc].to_numpy()).max(); mx=max(mx,e3); ok_x+=(e3==0.0)
        mm=(last[sgc].to_numpy().astype(np.float64)**2).mean(1)
        pc=[float((mm<mm[i]).mean()) for i in idx]
        pcts.append((g['ramo'],np.mean(pc)))
        apds.append((g['ramo'],float(np.mean(g['apd_sel']))))
        cic.append(dict(problema=pr,geracao=ge,ramo=g['ramo'],Flag=g['Flag'],NumV1=g['NumV1'],NumV2=g['NumV2'],
                        fe=g['fe'],lote=g['lote'],u_ef=g['u_efetivo'],popw_last=ln,
                        d_sigma=e1,d_crit=e2,pct_mm=float(np.mean(pc)),apd_med=float(np.median(g['apd_sel'])),
                        crit_med=float(np.median(crit)),n_front1=g['n_front1'],
                        dmin=float(np.median(g['dist_min_arquivo'])),tempo_fit=g['tempo_fit_s']))
    d['J_n']=tot; d['J_sigma_ok']=ok_sig; d['J_sigma_maxerr']=msig
    d['J_crit_ok']=ok_crit; d['J_crit_maxrel']=mcrit; d['J_X_ok']=ok_x; d['J_X_maxerr']=mx
    d['J_pct_inc']=float(np.mean([v for k,v in pcts if k=='incerteza'])) if d['SW_inc'] else np.nan
    d['J_pct_apd']=float(np.mean([v for k,v in pcts if k=='APD'])) if d['SW_apd'] else np.nan
    d['J_apd_inc']=float(np.mean([v for k,v in apds if k=='incerteza'])) if d['SW_inc'] else np.nan
    d['J_apd_apd']=float(np.mean([v for k,v in apds if k=='APD'])) if d['SW_apd'] else np.nan
    d['U11_err_fant_med']=float(np.median(err_fant)) if err_fant else np.nan
    # ---- sigma export / negativos
    d['B_sig_neg']=int((s[sgc].to_numpy()<0).sum()); d['B_sig_zero']=int((s[sgc].to_numpy()==0).sum())
    d['B_sig_nan']=int(s[sgc].isna().to_numpy().sum()); d['n_linhas3']=len(s)
    d['B_mu_nan']=int(s[muc].isna().to_numpy().sum())
    d['B_pred_tipo']=str(sorted(s.pred_tipo.dropna().unique())); d['B_modelo_flag']=str(sorted(s.modelo_flag.dropna().unique()))
    d['B_espaco']=str(sorted(s.espaco_modelo.dropna().unique())); d['B_transf']=str(sorted(s.transf_tipo.dropna().unique()))
    d['B_predclasse_null']=bool(s.pred_classe.isna().all()); d['B_rsid_null_online']=int(on.real_solution_id.notna().sum())
    # ---- U4/U5 sonda
    sgl=sorted(m['sonda']['geracoes']); d['U4_nblocos']=len(sgl); d['U4_evt']=len(sondas)
    d['U4_regra']=bool(all((g==1) or (g%2==0) for g in sgl))
    d['U4_last_cic']=len(gens); d['U4_last_sonda']=max(sgl)
    d['U4_finalprobe']=bool(max(sgl)==len(gens) or (len(gens)%2==0 and max(sgl)==len(gens)))
    d['U4_cover_last']=bool(max(sgl)==len(gens))
    d['U4_S']=m['sonda']['S']; d['U4_bloco_ok']=bool(set(so.groupby('geracao').size().unique())=={2000})
    try:
        gab=pd.read_parquet(f'{SONDA}/sonda_{pr}.parquet')
        gx=gab[[c for c in gab.columns if c.startswith('x')]].to_numpy()[:2000].astype(np.float32)
        mx5=0.0
        for ge in sgl:
            blk=so[so.geracao==ge][xc].to_numpy()
            mx5=max(mx5,float(np.abs(blk-gx[:,:D]).max()))
        d['U5_dX']=mx5
        gf=gab[[c for c in gab.columns if c.startswith('f')]].to_numpy()[:2000]
        d['U5_gab_cols']=str(list(gab.columns)[:4])
    except Exception as e:
        d['U5_dX']=np.nan; d['U5_gab_cols']='ERR:'+str(e)[:50]
    d['maquina_tempo_s']=m['timing']['tempo_total_s']
    cel.append(d)
    print('OK',pr,flush=True)
pd.DataFrame(cel).to_csv(OUT+'/b3_aspectos_por_celula.csv',index=False)
pd.DataFrame(cic).to_csv(OUT+'/b3_ciclos.csv',index=False)
print('gravado')
