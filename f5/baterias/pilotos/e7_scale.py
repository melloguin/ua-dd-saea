
import pandas as pd, numpy as np, json, glob, os, sys, math
from collections import Counter

BASE='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
cells=sorted(os.listdir(BASE))
cells=[c for c in cells if os.path.isdir(f'{BASE}/{c}/42')]
rows=[]
detail={}
for p in cells:
    d=f'{BASE}/{p}/42'
    pref=f'{d}/exp_main_e7_{p}_42'
    man=json.load(open(pref+'.manifest.json'))
    real=pd.read_parquet(pref+'__real.parquet')
    sur=pd.read_parquet(pref+'__surrogate.parquet')
    tim=pd.read_parquet(pref+'__timing.parquet')
    pop=pd.read_parquet(pref+'__pop.parquet')
    ev=[json.loads(l) for l in open(pref+'.jsonl')]
    G=[e for e in ev if e['rec']=='e7_gen']
    guards=[e for e in ev if e['rec']=='guard']
    sondas=[e for e in ev if e['rec']=='sonda']
    footer=[e for e in ev if e['rec']=='footer']
    xcols=[c for c in real.columns if c.startswith('x')]
    fcols=[c for c in real.columns if c.startswith('f') and c!='fase' and c!='fe_index']
    D=len(xcols); M=len(fcols)
    C_exp=(20*D)//3; trunc=(20*D)%3!=0
    r={'p':p,'D':D,'M':M}
    # --- structure ---
    r['n_real']=len(real); r['fe_ok']=(len(real)==31*D-1) and (real.fe_index.nunique()==31*D-1) and (real.fe_index.min()==0) and (real.fe_index.max()==31*D-2)
    r['init_ok']=int((real.fase=='init').sum())==11*D-1
    r['opt_n']=int((real.fase=='opt').sum())
    r['C']=len(G); r['C_ok']=len(G)==C_exp; r['trunc_exp']=trunc
    hs=[g for g in guards if g.get('name')=='hard_stop']; ch=[g for g in guards if g.get('name')=='cache_hit']
    r['hard_stop']=len(hs); r['hs_ok']=(len(hs)>0)==trunc
    r['cache_hits_ev']=len(ch); r['cache_hits_man']=man.get('cache_hits')
    r['cache_init']=all(g.get('fe')==1 for g in ch)
    r['footer_termino']=footer[0].get('termino') if footer else None
    r['status']=man.get('status'); r['fe_final_ok']=man.get('fe_final')==man.get('maxfe')==31*D-1
    r['n_ger_man']=man.get('n_geracoes'); r['nger_ok']=man.get('n_geracoes')==len(G)+1
    # pop layer: C+1 gens, size 11D-1+3(g-1)
    gp=pop.groupby('geracao').size()
    r['pop_gers']=len(gp); r['pop_gers_ok']=len(gp)==len(G)+1
    exp_sizes=pd.Series({g:11*D-1+3*(g-1) for g in gp.index})
    r['pop_prog_ok']=bool((gp.sort_index()==exp_sizes.sort_index()).all())
    # timing layer
    r['tim_n']=len(tim); r['tim_n_ok']=len(tim)==len(G)+1
    r['tim_ger1_dup']=int((tim.geracao==1).sum())==2
    r['nacum_ok']=bool(tim.n_acumulado.eq(11*D-1).all())
    fits=tim.tempo_fit_s.values
    r['fit_ratio']=float(fits[0]/np.mean(fits[1:])) if len(fits)>1 else np.nan
    # U7: fit+busca <= tempo_geracao
    viol=tim[(tim.tempo_fit_s+tim.tempo_busca_s)>tim.tempo_geracao_s]
    r['u7_viol']=len(viol)
    sonda_gers=set(man['sonda']['geracoes'])
    r['u7_viol_em_sonda']=bool(set(viol.geracao.dropna().astype(int)).issubset(sonda_gers)) if len(viol) else True
    # surrogate layer
    bus=sur[sur.regime=='online']; snd=sur[sur.regime=='sonda']
    bcnt=bus.groupby('geracao').size()
    r['busca_blocos']=len(bcnt); r['busca_blocos_ok']=len(bcnt)==len(G)
    r['busca_1900_ok']=bool(bcnt.eq(1900).all())
    r['sonda_blocos']=snd.geracao.nunique(); r['sonda_2000_ok']=bool(snd.groupby('geracao').size().eq(2000).all())
    Glast=C_exp+1 if trunc else C_exp
    exp_sonda=sorted({1}|{g for g in range(2,Glast+1,2)}|{Glast})
    r['sonda_cadencia_ok']=sorted(set(snd.geracao))==exp_sonda==sorted(sonda_gers)
    r['sonda_man_ok']=man['sonda']['n_blocos']==len(exp_sonda) and man['sonda']['n_falhas']==0
    r['modelo_flag_ok']=set(sur.modelo_flag.unique())=={'EDN-MCdropout'}
    sigc=[f'sigma_{j}' for j in range(M)]; muc=[f'mu_{j}' for j in range(M)]
    r['sigma_pos_ok']=bool((sur[sigc]>0).all().all()) and not sur[sigc].isna().any().any()
    # espaco: ciclo1 cru
    esp=bus.groupby('geracao').espaco_modelo.first()
    r['espaco_ok']=esp.get(1)=='cru' and bool((esp.drop(1)=='transformado').all())
    # fe_treino_max relógio (busca): ciclo c treina no arquivo pós ciclo c-1
    ftm=bus.groupby('geracao').fe_treino_max.first().sort_index()
    exp_ftm=pd.Series({c:(11*D-1+3*(c-1)-1) for c in ftm.index})
    r['ftm_ok']=bool((ftm==exp_ftm).all())
    r['ftm_mono']=bool(ftm.is_monotonic_increasing)
    # jsonl mechanism
    r['lote3_ok']=all(g['lote']==3 for g in G)
    r['ncl3_ok']=all(g['n_clusters_efetivo']==3 for g in G)
    r['ntre_ok']=all(g['n_treino']==11*D-1 for g in G)
    r['nstd_sum']=sum(g['n_std_neg'] for g in G)
    r['ndup_sum']=sum(g['n_dup_infill'] for g in G)
    r['stall_sum']=sum(g['stall_ciclos'] for g in G)
    r['delta_ok']=all(g['delta']==0.05 for g in G)
    r['NW']=G[0]['NW']; r['NW_const']=len({g['NW'] for g in G})==1
    r['NW_man']=man['params'].get('NW')
    # gatilho
    r['gat_ok']=all(((g['RatioOld']-g['Ratio'])<0.05)==(g['ramo']=='convergencia') for g in G)
    r['ramo_inc']=sum(1 for g in G if g['ramo']!='convergencia')
    # Ratio quantizacao
    qerr=max(abs(g['Ratio']*g['NW']-round(g['Ratio']*g['NW'])) for g in G)
    r['ratio_quant_ok']=qerr<1e-9
    # ymin chain
    ymax_err=0.0; esp_ok=True
    for i in range(len(G)-1):
        y=np.array(G[i+1]['ymin'],dtype=float); fb=np.array(G[i]['f_best'],dtype=float)
        ymax_err=max(ymax_err,float(np.max(np.abs(y-fb))))
    r['ymin_chain_maxerr']=ymax_err
    r['espaco_ev_ok']=(G[0]['espaco']=='cru') and all(g['espaco']=='transformado' for g in G[1:])
    # modelo_hp
    hp=G[0]['modelo_hp']
    r['T100']=all(g['modelo_hp']['T']==100 for g in G)
    r['dropP_ok']=all(tuple(g['modelo_hp']['dropP'])==(0.1,0.1) for g in G)
    r['loss_sent']=hp.get('loss_treino')
    r['hp_passos']=(hp.get('passos_init'),hp.get('passos_update'),hp.get('batchsize'),hp.get('learnR'))
    # e7_gen fe: fe after ciclo c = 11D-1+3c
    r['fe_gen_ok']=all(g['fe']==11*D-1+3*g['geracao'] for g in G)
    # --- deep: infills (U11 fantasia, #18 semantica do ramo), #20 warm-start ---
    ninit=11*D-1
    blocks={g:sub for g,sub in bus.groupby('geracao')}
    X_real=real[xcols].values
    fant=[]; inc_pct=[]; conv_pct=[]; ws_inter=0; ws_pairs=0; infill_match=0; infill_tot=0
    for c in range(1,len(G)+1):
        blk=blocks.get(c)
        if blk is None: continue
        tail=blk.tail(100)
        tp=json.loads(tail.transf_params.iloc[0]); ymin=np.array(tp['ymin'],dtype=float)
        idx=[ninit+3*(c-1)+j for j in range(3)]
        sids=real.solution_id.values[idx] if hasattr(real,'solution_id') else idx
        frs=real.iloc[idx]
        # match infills in tail by X (bit-a-bit float32)
        tX=tail[xcols].values
        sig_bar=tail[sigc].values.mean(axis=1)
        mu_t=tail[muc].values
        mmin=mu_t.min(axis=0)
        dist=np.linalg.norm(mu_t-mmin,axis=1)
        ramo=G[c-1]['ramo']
        for k,(i_r,fr) in enumerate(zip(idx,frs.itertuples())):
            xr=real[xcols].values[i_r]
            m=np.where((tX==xr).all(axis=1))[0]
            infill_tot+=1
            if len(m)==0: continue
            infill_match+=1
            m0=m[0]
            mu_raw=mu_t[m0]+ymin
            f_true=real[fcols].values[i_r]
            wape=np.sum(np.abs(mu_raw-f_true))/max(np.sum(np.abs(f_true)),1e-12)
            fant.append(wape)
            if ramo!='convergencia':
                inc_pct.append(float((sig_bar<=sig_bar[m0]).mean()))
            else:
                conv_pct.append(float((dist<dist[m0]).mean()))
        # warm-start: head100 of c+1 vs tail100 of c
        nblk=blocks.get(c+1)
        if nblk is not None:
            hX=nblk.head(100)[xcols].values
            a={tuple(np.round(x,9)) for x in tX}
            b={tuple(np.round(x,9)) for x in hX}
            ws_inter+=len(a&b); ws_pairs+=1
    r['infill_match']=f'{infill_match}/{infill_tot}'
    r['fant_wape_med']=float(np.median(fant)) if fant else np.nan
    r['inc_pct_med']=float(np.median(inc_pct)) if inc_pct else np.nan
    r['inc_n']=len(inc_pct)
    r['conv_pct_med']=float(np.median(conv_pct)) if conv_pct else np.nan
    r['ws_inter']=ws_inter; r['ws_pairs']=ws_pairs
    rows.append(r)
    print(f"done {p} D={D} M={M} C={len(G)}", file=sys.stderr)

df=pd.DataFrame(rows)
out='/private/tmp/claude-501/-Users-gmello/c7372206-5092-4c09-9686-ccae3785ca0c/scratchpad/e7_scale_results.csv'
df.to_csv(out,index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',100)
print(df.to_string())
