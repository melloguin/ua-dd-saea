import pandas as pd, numpy as np, json, collections
pd.set_option("display.width",250); pd.set_option("display.max_columns",100)
df=pd.read_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149/estrutural_c149.csv")
def chk(col, expect=True):
    v=df[col]
    ok=(v==expect).sum()
    print(f"{col:38s} {ok}/{len(df)}", "" if ok==len(df) else f"  FALHAS: {df.loc[v!=expect,['exp','prob',col]].to_dict('records')}")
for c in ["U1_fe_denso","U1_solid_denso","U2_doe_hash_ok","U3_fit_eq_dec","U3_fit_ger_denso",
          "U10_fe_final_eq_maxfe","U10_nopt_eq_q_x_iter","U10_ninit_mais_qiter",
          "U4_cadencia_ok","U4_ultima_coberta","U4_bloco_2000_ok","U4_gs_sur_eq_ev",
          "U8_ftm_monot","U8_ftm_eq_ninit_mais","FIT_ntreino_eq","U7_viol_sao_sonda",
          "ACQ_gs_eq_dec","POP_eq_ACQ","U9_clamp_bate","U9_cache_bate","U9_ngers_bate",
          "RSI_so_online","RSI_um_por_ger","DEC_q_ok",
          "sur_pred_classe_nan","sur_pred_score_nan","sur_pred_conf_nan"]:
    chk(c)
print()
print("U1 len==31D-1:", int((df.U1_len_real==df.U1_maxfe_esperado).sum()),"/",len(df), " (main)"," batch:", df.loc[df.exp=="batch",["prob","U1_len_real","maxfe","D","q"]].to_dict("records"))
print("U2 init==11D-1:", int((df.U2_n_init==df.U2_esperado).sum()),"/",len(df))
print("fases:", collections.Counter(df.fases))
print("RSI_n==esperado:", int((df.RSI_n==df.RSI_esperado).sum()),"/",len(df), " RSI unicos==n:", int((df.RSI_unicos==df.RSI_n).sum()))
print("U7 violacoes:", df.U7_viol.sum(), "de", df.U7_n.sum(), " (soma c/ sonda:", df.U7_soma_pred_ok.sum(),")")
print("regimes ③:", collections.Counter(df.sur_regimes), " espaco:", collections.Counter(df.sur_espaco), " transf:", collections.Counter(df.sur_transf))
print("modelo_flag:", collections.Counter(df.sur_modelo_flag), " pred_tipo:", collections.Counter(df.sur_pred_tipo))
print("epocas:", collections.Counter(df.FIT_epocas), " K val_mse:", collections.Counter(df.FIT_K_valmse))
print("params: K",set(df.P_K),"epocas",set(df.P_epocas),"batch",set(df.P_batch),"lr0",set(df.P_lr0),"decay",set(df.P_decay))
print("  nsga pop",set(df.P_nsga_pop),"gen",set(df.P_nsga_gen),"sbx",set(df.P_sbx),"init",set(df.P_init),"loss",set(df.P_loss))
print("  pm:",set(df.P_pm))
print("  ativ:",set(df.P_ativ))
print("  split:",set(df.P_split)," seedbase:",set(df.P_seedbase)," dtype:",set(df.P_dtype)," fixM:",set(df.P_fixM)," cachecap:",set(df.P_cachecap))
print("  env:",set(df.ENV_pymoo),set(df.ENV_torch),set(df.ENV_py),set(df.ENV_numpy),set(df.ENV_dev))
print("  arch:", df[["prob","exp","D","M","P_arch"]].drop_duplicates("P_arch").to_dict("records"))
print()
print("=== ACQ front (res.X rank-0) ===")
print(df[["exp","prob","D","M","ACQ_front_min","ACQ_front_max","ACQ_front_mean","ACQ_front_eq_1000_frac","DEC_nfront_min","DEC_nfront_max"]].to_string(index=False))
print()
print("=== HVI / decisao ===")
print(df[["exp","prob","D","M","U4_G","DEC_caminhos","DEC_hvi_max_eq_top1","DEC_hvi_zero","DEC_n_hvi_pos_zero","DEC_n_hvi_pos_med","DEC_n_empatados_med","DEC_n_empatados_max","DEC_cache_hit","DEC_clamp","DEC_seed_unico","DEC_seed_n"]].to_string(index=False))
print()
print("=== fit linearidade + valmse ===")
print(df[["exp","prob","D","M","FIT_valmse_med_ini","FIT_valmse_med_fim","FIT_valmse_med_all","FITLIN_slope_ms_por_n","FITLIN_r2","FITLIN_r2_cub","T_total","T_fit","T_busca","T_sonda","T_aval"]].to_string(index=False))
print()
print("=== sonda blocos ===")
print(df[["exp","prob","U4_G","U4_n_blocos","U4_n_blocos_sur","SONDA_nblocos","U4_finalProbe_extra","sur_n_sonda","sur_n_online","sur_linhas"]].to_string(index=False))
print()
print("=== footer/manifest ===")
print(df[["exp","prob","status","motivo_parada","FOOT_status","FOOT_motivo","FOOT_cp_init","FOOT_cache_hits","FOOT_n_cache_infill","FOOT_n_clamp","cache_hits","nparse_fail","n_footer"]].to_string(index=False))
