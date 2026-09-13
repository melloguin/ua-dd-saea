import json, os, hashlib, sys
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
REPO="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
rows=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    man=json.load(open(base+".manifest.json"))
    ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]
    ft=[e for e in ev if e['rec']=='footer']
    G=[e for e in ev if e['rec']=='e7_gen']
    SD=[e for e in ev if e['rec']=='sonda']
    GU=[e for e in ev if e['rec']=='guard']
    D=hdr['D']; M=hdr['M']
    real=pd.read_parquet(base+"__real.parquet")
    pop=pd.read_parquet(base+"__pop.parquet")
    tim=pd.read_parquet(base+"__timing.parquet")
    xc=[f"x{i}" for i in range(D)]; fc=[f"f{i}" for i in range(M)]
    r={}
    r['problema']=p; r['D']=D; r['M']=M
    # U1 orcamento
    r['n_real']=len(real); r['maxfe']=man['maxfe']; r['fe_final']=man['fe_final']
    r['U1_fe_exato']=(len(real)==31*D-1) and (man['fe_final']==31*D-1) and (man['maxfe']==31*D-1)
    r['U1_feidx_denso']=(sorted(real.fe_index.tolist())==list(range(31*D-1)))
    r['U1_solid_denso']=(sorted(real.solution_id.tolist())==list(range(31*D-1)))
    # U2 DoE
    n_init=int((real.fase=='init').sum()); r['n_init']=n_init
    r['U2_init_exato']=(n_init==11*D-1)
    r['n_opt']=int((real.fase=='opt').sum()); r['U2_opt_exato']=(r['n_opt']==20*D)
    doe_f=f"{REPO}/data/doe/{p}/doe_{p}_42.parquet"
    if os.path.exists(doe_f):
        doe=pd.read_parquet(doe_f)
        dxc=[c for c in doe.columns if c.startswith('x')][:D]
        A=real.loc[real.fase=='init',xc].to_numpy(np.float64)
        B=doe[dxc].to_numpy(np.float64)[:n_init]
        r['U2_dX_max']=float(np.max(np.abs(A-B))) if A.shape==B.shape else -1.0
    else:
        r['U2_dX_max']=np.nan
    dm=json.load(open(f"{REPO}/data/doe/{p}/doe_{p}_42.manifest.json")) if os.path.exists(f"{REPO}/data/doe/{p}/doe_{p}_42.manifest.json") else {}
    r['U2_hash_ok']=(man['doe_hash']==hdr['doe_hash']) and (man['doe_hash']==dm.get('hash',dm.get('doe_hash',man['doe_hash'])))
    r['doe_hash_sidecar']=dm.get('hash',dm.get('doe_hash',''))[:12]
    # ciclos
    C=len(G); r['C_e7gen']=C
    r['n_geracoes_man']=man['n_geracoes']
    r['U10_ngen_eq_C1']=(man['n_geracoes']==C+1)
    r['U10_timing_C1']=(len(tim)==C+1)
    r['U10_pop_gers']=int(pop.geracao.nunique()); r['U10_pop_eq_C1']=(pop.geracao.nunique()==C+1)
    szs=pop.groupby('geracao').size()
    exp_sz=pd.Series({g:11*D-1+3*(g-1) for g in szs.index})
    r['U10_pop_prog_ok']=bool((szs.values==exp_sz.values).all())
    r['n_pop_rows']=len(pop); r['n_pop_esperado']=int(sum(11*D-1+3*(g-1) for g in range(1,C+2)))
    r['U10_pop_total_ok']=(len(pop)==r['n_pop_esperado'])
    # ④ geracao 1 duplicada
    r['U10_ger1_dup']=(int((tim.geracao==1).sum())==2)
    r['tempo_fit_inicial_s']=float(G[0].get('tempo_fit_inicial_s',np.nan))
    r['tempo_fit_upd_c1']=float(G[0].get('tempo_fit_s',np.nan))
    r['razao_80k_8k']=r['tempo_fit_inicial_s']/r['tempo_fit_upd_c1'] if r['tempo_fit_upd_c1'] else np.nan
    r['tfi_so_em_c1']=all(('tempo_fit_inicial_s' not in g) or g.get('tempo_fit_inicial_s') in (None,) for g in G[1:])
    # Ke / lote
    r['lote3_all']=all(g['lote']==3 for g in G); r['lotes']=sorted(set(g['lote'] for g in G))
    r['fe_ciclo3_all']=all(g['fe_ciclo']==3 for g in G)
    # gatilho dual
    r['delta_set']=sorted(set(g['delta'] for g in G))
    ok_gat=sum(1 for g in G if ((g['RatioOld']-g['Ratio'])<g['delta'])==(g['ramo']=='convergencia'))
    r['gat_ok']=ok_gat; r['gat_n']=C
    r['n_conv']=sum(1 for g in G if g['ramo']=='convergencia'); r['n_inc']=C-r['n_conv']
    # motivo string consistente com flag
    r['motivo_ok']=sum(1 for g in G if (('< delta' in g['motivo']) == (g['ramo']=='convergencia')))
    # paper delta 0.08 com '>' -> contrafactual
    r['n_inc_se_paper']=sum(1 for g in G if (g['RatioOld']-g['Ratio'])>0.08)
    # Ratio quantizado
    NWs=sorted(set(g['NW'] for g in G)); r['NW']=NWs[0] if len(NWs)==1 else NWs
    r['NW_manifest']=man['params']['NW']; r['N_pop']=man['params']['N_pop']
    q=[abs(g['Ratio']*g['NW']-round(g['Ratio']*g['NW'])) for g in G]
    r['ratio_quant_max']=float(max(q)); r['ratio_quant_ok']=int(sum(1 for v in q if v<1e-9))
    r['ratio_min']=float(min(g['Ratio'] for g in G)); r['ratio_max']=float(max(g['Ratio'] for g in G))
    # pop_por_w = 19 x N
    pw=[g['pop_por_w'] for g in G]
    r['pop_por_w_len']=sorted(set(len(v) for v in pw))
    r['pop_por_w_vals']=sorted(set(x for v in pw for x in v))
    # guards
    r['n_std_neg_tot']=sum(g['n_std_neg'] for g in G)
    r['n_dup_infill_tot']=sum(g['n_dup_infill'] for g in G)
    r['stall_tot']=sum(g['stall_ciclos'] for g in G)
    r['guards']=[ (e['name'],e.get('fe')) for e in GU]
    r['cache_hits_man']=man['cache_hits']; r['cache_hits_footer']=ft[0]['cache_hits'] if ft else None
    r['n_cache_guard']=sum(1 for e in GU if e['name']=='cache_hit')
    r['U9_ok']= (man['cache_hits']==r['n_cache_guard']) and (ft and ft[0]['cache_hits']==man['cache_hits'])
    r['hard_stop']=any(e['name']=='hard_stop' for e in GU)
    r['hard_stop_esperado']=((20*D)%3!=0)
    r['C_esperado']=(20*D)//3
    r['U14_ok']=(r['hard_stop']==r['hard_stop_esperado']) and (C==r['C_esperado'])
    r['overshoot_teorico']=(3-(20*D)%3)%3
    # translacao
    r['esp_c1']=G[0]['espaco']; r['esp_resto_ok']=all(g['espaco']=='transformado' for g in G[1:])
    chain=[float(np.max(np.abs(np.array(G[i+1]['ymin'])-np.array(G[i]['f_best'])))) for i in range(C-1)]
    r['ymin_chain_max']=float(max(chain)) if chain else 0.0; r['ymin_chain_n']=len(chain)
    r['ymin_c1']=G[0]['ymin']
    # cap de treino
    r['n_treino_const']=all(g['n_treino']==11*D-1 for g in G)
    r['n_acum_const']=bool((tim.n_acumulado==11*D-1).all())
    # relogios
    r['fe_ok']=all(g['fe']==11*D-1+3*g['geracao'] for g in G)
    r['fetm_ok']=all(g['fe_treino_max']==11*D-1+3*(g['geracao']-1)-1 for g in G)
    r['fetm_mono']=all(G[i+1]['fe_treino_max']>=G[i]['fe_treino_max'] for i in range(C-1))
    # U7 timing
    t2=tim.dropna(subset=['tempo_geracao_s'])
    viol=int(((t2.tempo_fit_s+t2.tempo_busca_s)>t2.tempo_geracao_s+1e-9).sum())
    r['U7_viol']=viol; r['U7_n']=len(t2)
    viol_s=int(((t2.tempo_fit_s+t2.tempo_busca_s+t2.tempo_pred_sonda_s)>t2.tempo_geracao_s+1e-9).sum())
    r['U7_viol_com_sonda']=viol_s
    r['U7_sonda_gers']=len(SD)
    # modelo_hp echo
    hp=G[0]['modelo_hp']
    r['hp_T']=hp['T']; r['hp_drop']=tuple(hp['dropP']); r['hp_lr']=hp['learnR']; r['hp_wd']=hp['decay_efetivo']
    r['hp_batch']=hp['batchsize']; r['hp_batch_eq_D']=(hp['batchsize']==D); r['hp_neuron']=hp['neuronN']
    r['hp_pi']=hp['passos_init']; r['hp_pu']=hp['passos_update']; r['hp_loss']=hp['loss_treino']
    r['hp_const']=all(g['modelo_hp']==hp or (g['modelo_hp']['T']==100 and tuple(g['modelo_hp']['dropP'])==(0.1,0.1)) for g in G)
    r['hp_drop_all']=len(set(tuple(g['modelo_hp']['dropP']) for g in G))==1
    r['hp_T_all']=len(set(g['modelo_hp']['T'] for g in G))==1
    r['hp_loss_all']=len(set(g['modelo_hp']['loss_treino'] for g in G))==1
    # kmeans
    r['nclu3']=all(g['n_clusters_efetivo']==3 for g in G)
    # n_front1
    nf=[g['n_front1'] for g in G]; r['nfront1_min']=min(nf); r['nfront1_max']=max(nf); r['nfront1_c1']=nf[0]; r['nfront1_last']=nf[-1]
    # dist_min_arquivo
    dmin=[v for g in G for v in g['dist_min_arquivo']]
    r['distmin_n']=len(dmin); r['distmin_min']=float(np.min(dmin)); r['distmin_med']=float(np.median(dmin))
    r['distmin_zeros']=int(sum(1 for v in dmin if v==0))
    # rss
    r['rss_max']=float(max(g['rss_mb'] for g in G)); r['rss_c1']=float(G[0]['rss_mb'])
    # sonda cadencia
    gers_esp=set([1]+[g for g in range(2,man['n_geracoes']+1) if g%2==0]+[man['n_geracoes']])
    gers_obs=set(e['geracao'] for e in SD)
    r['sonda_n_blocos']=len(SD); r['sonda_man_blocos']=man['sonda']['n_blocos']
    r['sonda_gers_eq_man']=(sorted(gers_obs)==sorted(man['sonda']['geracoes']))
    r['sonda_cad_ok']=(gers_obs==gers_esp)
    r['sonda_gers_falt']=sorted(gers_esp-gers_obs); r['sonda_gers_extra']=sorted(gers_obs-gers_esp)
    r['sonda_falhas']=man['sonda']['n_falhas']; r['sonda_npontos_ok']=all(e['n_pontos']==2000 for e in SD)
    r['sonda_ok_all']=all(e['ok'] for e in SD)
    r['sonda_xhash_ok']=len(set(e['x_hash'] for e in SD))==1 and SD[0]['x_hash']==man['sonda']['x_hash']
    # footer / termino
    r['status']=man['status']; r['n_retries']=man['n_retries']; r['fallback']=man['fallback_ativado']
    r['footer_n']=len(ft); r['termino']=ft[0]['termino'] if ft else None; r['cp_init']=ft[0]['cp_init'] if ft else None
    r['tem_motivo_parada']=('motivo_parada' in man)
    r['tempo_total_s']=man['timing']['tempo_total_s']
    r['tempo_fit_tot']=man['timing']['tempo_fit_surrogate_s']; r['tempo_busca_tot']=man['timing']['tempo_busca_s']
    r['tempo_sonda_tot']=man['timing']['tempo_pred_sonda_s']; r['tempo_aval_tot']=man['timing']['tempo_aval_real_s']
    rows.append(r); print("ok",p,flush=True)
df=pd.DataFrame(rows)
df.to_csv("estrutural_e7.csv",index=False)
pd.set_option('display.width',250)
print(df[['problema','D','M','U1_fe_exato','U1_feidx_denso','U2_init_exato','U2_dX_max','U2_hash_ok','C_e7gen','C_esperado','hard_stop','hard_stop_esperado','U14_ok']].to_string())
