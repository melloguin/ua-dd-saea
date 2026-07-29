"""Bateria estrutural c149 (F5.3b) — U1..U11 + aspectos do bundle, TODAS as 30 celulas."""
import json, os, glob, collections, math
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"

cells=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"
    prob=lab[4:] if lab.startswith("q10_") else lab
    cells.append((exp,prob,lab,d))
print("celulas:",len(cells))

rows=[]; dec_rows=[]
for exp,prob,lab,d in cells:
    stem=f"exp_{exp}_c149_{prob}_42"
    p=os.path.join(d,stem)
    m=json.load(open(p+".manifest.json"))
    D=None
    # jsonl
    ev=collections.defaultdict(list); nparse_fail=0
    for line in open(p+".jsonl"):
        line=line.strip()
        if not line: continue
        try: dd=json.loads(line)
        except Exception: nparse_fail+=1; continue
        ev[dd.get("rec","?")].append(dd)
    hdr=ev["header"][0]; D=hdr["D"]; M=hdr["M"]
    foot=ev["footer"]
    dec=pd.DataFrame(ev["decision"]); fit=pd.DataFrame(ev["fit"]); son=pd.DataFrame(ev["sonda"])
    real=pq.read_table(p+"__real.parquet").to_pandas()
    pop=pq.read_table(p+"__pop.parquet").to_pandas()
    tim=pq.read_table(p+"__timing.parquet").to_pandas()
    sur_f=pq.ParquetFile(p+"__surrogate.parquet")
    nsur=sur_f.metadata.num_rows
    # leitura leve da ③: so colunas de controle
    ctrl=pq.read_table(p+"__surrogate.parquet",columns=["regime","geracao","real_solution_id","fe_treino_max","espaco_modelo","transf_tipo","modelo_flag","pred_tipo","pred_classe","pred_score","pred_confianca"]).to_pandas()
    q=m["q"]; maxfe=m["maxfe"]
    n_init = 11*D-1
    r={"exp":exp,"prob":prob,"D":D,"M":M,"q":q,
       "maxfe":maxfe,"fe_final":m["fe_final"],"n_ger":m["n_geracoes"],
       "status":m["status"],"motivo_parada":m.get("motivo_parada"),
       "cache_hits":m["cache_hits"],"nparse_fail":nparse_fail,
       # U1
       "U1_len_real":len(real),"U1_maxfe_esperado":31*D-1,
       "U1_fe_denso":bool((real.fe_index.values==np.arange(len(real))).all()),
       "U1_solid_denso":bool((real.solution_id.values==np.arange(len(real))).all()),
       # U2
       "U2_n_init":int((real.fase=="init").sum()),"U2_esperado":n_init,
       "U2_doe_hash_ok":m["doe_hash"]==hdr["doe_hash"],
       "U2_n_opt":int((real.fase!="init").sum()),
       "fases":sorted(real.fase.unique().tolist()),
       # iteracoes
       "n_dec":len(dec),"n_fit":len(fit),"n_sonda_ev":len(son),"n_footer":len(foot),
       "n_tim":len(tim),
       # U3: 1 fit por iteracao
       "U3_fit_eq_dec":len(fit)==len(dec),
       "U3_fit_ger_denso":bool((fit.geracao.values==np.arange(1,len(fit)+1)).all()),
       # U10 aritmetica
       "U10_fe_final_eq_maxfe":m["fe_final"]==maxfe,
       "U10_nopt_eq_q_x_iter":int((real.fase!="init").sum())==q*len(dec),
       "U10_ninit_mais_qiter":n_init+q*len(dec)==maxfe,
       "U10_pop_linhas":len(pop),
       # ③
       "sur_linhas":nsur,
       "sur_regimes":sorted(ctrl.regime.unique().tolist()),
       "sur_n_online":int((ctrl.regime=="online").sum()),
       "sur_n_sonda":int((ctrl.regime=="sonda").sum()),
       "sur_espaco":sorted(ctrl.espaco_modelo.unique().tolist()),
       "sur_transf":sorted(ctrl.transf_tipo.unique().tolist()),
       "sur_modelo_flag":sorted(ctrl.modelo_flag.unique().tolist()),
       "sur_pred_tipo":sorted(ctrl.pred_tipo.unique().tolist()),
       "sur_pred_classe_nan":bool(ctrl.pred_classe.isna().all()),
       "sur_pred_score_nan":bool(ctrl.pred_score.isna().all()),
       "sur_pred_conf_nan":bool(ctrl.pred_confianca.isna().all()),
       }
    # U4 cadencia sonda
    gs=sorted(son.geracao.unique().tolist()); G=len(dec)
    esperado=sorted(set([1]+[g for g in range(2,G+1) if g%2==0]+[G]))
    r["U4_cadencia_ok"]= gs==esperado
    r["U4_n_blocos"]=len(gs); r["U4_G"]=G
    r["U4_ultima_coberta"]= G in gs
    r["U4_finalProbe_extra"]= (G%2==1)
    # blocos da ③ sonda
    sb=ctrl[ctrl.regime=="sonda"].groupby("geracao").size()
    r["U4_bloco_2000_ok"]=bool((sb.values==2000).all()); r["U4_n_blocos_sur"]=len(sb)
    r["U4_gs_sur_eq_ev"]= sorted(sb.index.tolist())==gs
    # busca online por geracao
    ob=ctrl[ctrl.regime=="online"].groupby("geracao").size()
    r["ACQ_front_min"]=int(ob.min()); r["ACQ_front_max"]=int(ob.max()); r["ACQ_front_mean"]=float(ob.mean())
    r["ACQ_n_ger"]=len(ob)
    r["ACQ_front_eq_1000_frac"]=float((ob.values==1000).mean())
    r["ACQ_gs_eq_dec"]= sorted(ob.index.tolist())==list(range(1,G+1))
    # ② pop
    pg=pop.groupby("geracao").size()
    r["POP_n_ger"]=len(pg); r["POP_size_min"]=int(pg.min()); r["POP_size_max"]=int(pg.max())
    r["POP_eq_ACQ"]= bool((pg.reindex(ob.index).values==ob.values).all()) if len(pg)==len(ob) else False
    # U8 fe_treino_max monotonico
    ft=ctrl[ctrl.regime=="online"].groupby("geracao").fe_treino_max.first()
    r["U8_ftm_monot"]=bool((np.diff(ft.values)>=0).all())
    r["U8_ftm_eq_ninit_mais"]=bool((ft.values==(n_init+q*(np.arange(1,G+1)-1)-1)).all())
    r["U8_ftm_min"]=int(ft.min()); r["U8_ftm_max"]=int(ft.max())
    # fit: n_treino
    r["FIT_ntreino_eq"]=bool((fit.n_treino.values==(n_init+q*(np.arange(1,G+1)-1))).all())
    r["FIT_epocas"]=sorted(fit.epocas.unique().tolist())
    r["FIT_K_valmse"]=sorted(set(len(v) for v in fit.val_mse))
    r["FIT_valmse_med_ini"]=float(np.median(fit.val_mse.iloc[0]))
    r["FIT_valmse_med_fim"]=float(np.median(fit.val_mse.iloc[-1]))
    r["FIT_valmse_med_all"]=float(np.median([np.median(v) for v in fit.val_mse]))
    # z-score params
    zm=np.array(fit.z_mean.tolist()); zs=np.array(fit.z_std.tolist())
    r["ZS_std_min"]=float(zs.min()); r["ZS_varia"]=bool((np.abs(np.diff(zm,axis=0)).sum()>0))
    # U7 timing
    viol = tim.tempo_fit_s+tim.tempo_busca_s > tim.tempo_geracao_s
    r["U7_viol"]=int(viol.sum()); r["U7_n"]=len(tim)
    viol_g=set(tim.geracao[viol].tolist())
    r["U7_viol_sao_sonda"]= viol_g<=set(gs)
    r["U7_soma_pred_ok"]=int(((tim.tempo_fit_s+tim.tempo_busca_s+tim.tempo_pred_sonda_s)>tim.tempo_geracao_s).sum())
    # fit ~linear em n (M.11)
    nn=tim.n_acumulado.values.astype(float); tf=tim.tempo_fit_s.values.astype(float)
    if len(nn)>10:
        A=np.vstack([nn,np.ones_like(nn)]).T
        coef,res_,_,_=np.linalg.lstsq(A,tf,rcond=None)
        pred=A@coef; ss=1-((tf-pred)**2).sum()/((tf-tf.mean())**2).sum()
        r["FITLIN_slope_ms_por_n"]=float(coef[0]*1000); r["FITLIN_r2"]=float(ss)
        # cubico?
        A3=np.vstack([nn**3,nn**2,nn,np.ones_like(nn)]).T
        c3,_,_,_=np.linalg.lstsq(A3,tf,rcond=None); p3=A3@c3
        r["FITLIN_r2_cub"]=float(1-((tf-p3)**2).sum()/((tf-tf.mean())**2).sum())
    # decisoes
    r["DEC_caminhos"]=json.dumps(dict(collections.Counter(dec.caminho)))
    r["DEC_q_ok"]=bool((dec.q==q).all())
    r["DEC_nfront_min"]=int(dec.n_front_acq.min()); r["DEC_nfront_max"]=int(dec.n_front_acq.max())
    r["DEC_hvi_max_eq_top1"]=int((dec.hvi_escolhido.round(9)==dec.hvi_top5.apply(lambda v: round(max(v),9))).sum())
    r["DEC_hvi_zero"]=int((dec.hvi_escolhido==0).sum())
    r["DEC_n_hvi_pos_zero"]=int((dec.n_hvi_pos==0).sum())
    r["DEC_n_hvi_pos_med"]=float(dec.n_hvi_pos.median())
    r["DEC_n_empatados_med"]=float(dec.n_empatados.median())
    r["DEC_n_empatados_max"]=int(dec.n_empatados.max())
    r["DEC_cache_hit"]=int(dec.cache_hit.sum())
    r["DEC_clamp"]=int(dec.n_clamp_sigma2_iter.sum())
    r["DEC_seed_unico"]=int(dec.seed_nsga2.nunique()); 
    r["DEC_seed_n"]=len(dec)
    r["DEC_sigma2aggsel_med"]=float(dec.sigma2_agg_sel_z.median())
    # sigma2_z max reportado na acq
    s2max=np.array(dec.acq_resF_sigma2_z_max.tolist())
    r["ACQ_s2max_med"]=float(np.median(s2max))
    # fe/solution_id coerentes
    r["DEC_fe_seq"]=bool((dec.fe.values==np.arange(n_init+q,maxfe+1,q)).all()) if q==1 else None
    r["DEC_solid_seq"]=bool((dec.solution_id.values==np.arange(n_init,maxfe,q)).all()) if q==1 else None
    # footer
    f0=foot[0]
    r["FOOT_status"]=f0.get("status"); r["FOOT_motivo"]=f0.get("motivo_parada")
    r["FOOT_cp_init"]=f0.get("cp_init"); r["FOOT_cache_hits"]=f0.get("cache_hits")
    r["FOOT_n_cache_infill"]=f0.get("n_cache_infill"); r["FOOT_n_clamp"]=f0.get("n_clamp_sigma2")
    r["U9_clamp_bate"]= f0.get("n_clamp_sigma2")==int(dec.n_clamp_sigma2_iter.sum())
    r["U9_cache_bate"]= f0.get("cache_hits")==m["cache_hits"]==int(dec.cache_hit.sum())
    r["U9_ngers_bate"]= f0.get("n_geracoes")==m["n_geracoes"]==len(dec)
    # real_solution_id na ③
    rs=ctrl[ctrl.real_solution_id.notna()]
    r["RSI_n"]=len(rs); r["RSI_esperado"]=q*len(dec)
    r["RSI_so_online"]=bool((rs.regime=="online").all())
    r["RSI_unicos"]=int(rs.real_solution_id.nunique())
    r["RSI_um_por_ger"]=bool((rs.groupby("geracao").size().values==q).all())
    # params echo
    pa=m["params"]
    r["P_K"]=pa["K"]; r["P_arch"]=pa["arch"]; r["P_epocas"]=pa["epocas"]; r["P_batch"]=pa["batch"]
    r["P_lr0"]=pa["adam"]["lr0"]; r["P_decay"]=pa["adam"]["decay_por_epoca"]
    r["P_ativ"]=json.dumps(pa["ativacoes_raiz"]); r["P_init"]=pa["init"]; r["P_loss"]=pa["loss"]
    r["P_nsga_pop"]=pa["nsga2_acq"]["pop"]; r["P_nsga_gen"]=pa["nsga2_acq"]["n_gen"]
    r["P_sbx"]=json.dumps(pa["nsga2_acq"]["sbx"]); r["P_pm"]=json.dumps({k:v for k,v in pa["nsga2_acq"]["pm"].items() if k!="decisao"})
    r["P_split"]=pa["split"]; r["P_seedbase"]=pa["seed_base"]; r["P_q"]=pa["q"]
    r["P_cachecap"]=pa["cache_cap"]; r["P_dtype"]=pa["torch_default_dtype"]
    r["P_fixM"]=pa["fix_M"]
    r["ENV_pymoo"]=m["env"]["pymoo"]; r["ENV_torch"]=m["env"]["torch"]; r["ENV_py"]=m["env"]["python"]
    r["ENV_numpy"]=m["env"]["numpy"]; r["ENV_dev"]=m["env"]["pinning"]["device"]
    r["T_total"]=m["timing"]["tempo_total_s"]; r["T_fit"]=m["timing"]["tempo_fit_surrogate_s"]
    r["T_busca"]=m["timing"]["tempo_busca_s"]; r["T_aval"]=m["timing"]["tempo_aval_real_s"]
    r["T_sonda"]=m["timing"]["tempo_pred_sonda_s"]
    r["SONDA_S"]=m["sonda"]["S"]; r["SONDA_nblocos"]=m["sonda"]["n_blocos"]
    rows.append(r)
    d2=dec.copy(); d2["prob"]=prob; d2["exp"]=exp; d2["D"]=D; d2["M"]=M
    dec_rows.append(d2[["exp","prob","D","M","geracao","caminho","seed_nsga2","n_front_acq","q",
                        "hvi_escolhido","n_hvi_pos","n_empatados","sigma2_agg_sel_z","cache_hit",
                        "solution_id","fe","n_front1","dist_min_arquivo","tempo_fit_s","tempo_busca_s"]])
    print(f"[ok] {exp}/{prob} D={D} M={M} G={G} FE={m['fe_final']}/{maxfe}")

df=pd.DataFrame(rows)
df.to_csv(os.path.join(OUT,"estrutural_c149.csv"),index=False)
pd.concat(dec_rows).to_csv(os.path.join(OUT,"decisoes_c149.csv.gz"),index=False,compression="gzip")
print("\nSALVO.", df.shape)
