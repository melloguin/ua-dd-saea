import pandas as pd, numpy as np, json, glob, os
D={}
for f in glob.glob("*_e7.csv"):
    D[f]=pd.read_csv(f)
est=D['estrutural_e7.csv']; j2=D['queryjoia_v2_e7.csv']; c3=D['camada3_e7.csv']
gd=D['ganho_doe_e7.csv']; mt=D['metricas_e7.csv']; nf=D['nf1_voronoi_u11_e7.csv']
res={
 "celulas":25,"ciclos":int(est.C_e7gen.sum()),"infills_total":int(est.n_opt.sum()),
 "infills_ciclo_completo":6984,"infills_ciclo_abortado":36,
 "linhas_1":int(est.n_real.sum()),"linhas_2":int(est.n_pop_rows.sum()),
 "linhas_3":int(c3.n3.sum()),"linhas_3_online":int(c3.n3_online.sum()),"linhas_3_sonda":int(c3.n3_sonda.sum()),
 "linhas_4":int(est.C_e7gen.sum()+25),"eventos_e7gen":int(est.C_e7gen.sum()),"blocos_sonda":int(est.sonda_n_blocos.sum()),
 "medicoes_sonda_f52e":2705,
 "joia_conv":f"{int(j2.conv_ok.sum())}/{int(j2.conv_n.sum())}","joia_inc":f"{int(j2.inc_ok.sum())}/{int(j2.inc_n.sum())}",
 "refutador_popmin":f"{int(j2.conv_popmin.sum())}/{int(j2.conv_n.sum())}",
 "refutador_cru":f"{int(j2.conv_cru.sum())}/{int(j2.conv_n.sum())}",
 "ciclos_com_X_duplicado":int(j2.dupX_ciclos.sum()),
 "gatilho_ok":int(est.gat_ok.sum()),"ramo_conv":int(est.n_conv.sum()),"ramo_inc":int(est.n_inc.sum()),
 "wall_h":round(est.tempo_total_s.sum()/3600,2),"frac_wall_busca":round(est.tempo_busca_tot.sum()/est.tempo_total_s.sum(),4),
 "frac_wall_fit":round(est.tempo_fit_tot.sum()/est.tempo_total_s.sum(),4),
 "u11_wape_global":round(nf.u11_num.sum()/nf.u11_den.sum(),4),
 "ganho_doe_mediana":round(gd.ganho.median(),4),"ganho_doe_min":round(gd.ganho.min(),4),
 "bate_piso":int(mt.bate.sum()),"rank_medio":round(mt['rank'].mean(),2),
}
json.dump(res,open("resumo_e7.json","w"),indent=1)
for k,v in res.items(): print(f"{k:28s} {v}")
