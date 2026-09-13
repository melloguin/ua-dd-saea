import pandas as pd, numpy as np, json, ast
pd.set_option('display.width',300)
est=pd.read_csv("estrutural_e7.csv"); qj=pd.read_csv("queryjoia_celulas_e7.csv")
c3=pd.read_csv("camada3_e7.csv"); nf=pd.read_csv("nf1_voronoi_u11_e7.csv")
print("=== BLOCO DE NUMEROS PARA O RELATORIO ===")
print("celulas:",len(est),"| ciclos:",est.C_e7gen.sum(),"| infills(①opt):",est.n_opt.sum(),
      "| infills em ciclo completo:",qj.inf_tot.sum())
print("linhas ①:",est.n_real.sum(),"② :",est.n_pop_rows.sum(),"③ :",c3.n3.sum(),
      "(online",c3.n3_online.sum(),"+ sonda",c3.n3_sonda.sum(),") ④:",est.C_e7gen.sum()+25,
      "⑥ e7_gen:",est.C_e7gen.sum(),"sonda-ev:",est.sonda_n_blocos.sum())
print("U11 WAPE global:",round(nf.u11_num.sum()/nf.u11_den.sum(),4),
      "| por celula: min",round(nf.u11_wape.min(),4),"max",round(nf.u11_wape.max(),4),"mediana",round(nf.u11_wape.median(),4))
print(nf[['problema','u11_wape']].sort_values('u11_wape').round(4).to_string())
print("\ntempo: fit_inicial min/max:",round(est.tempo_fit_inicial_s.min(),2),round(est.tempo_fit_inicial_s.max(),2))
print("razao 80k/8k: mediana",round(est.razao_80k_8k.median(),3),"faixa",round(est.razao_80k_8k.min(),3),"-",round(est.razao_80k_8k.max(),3))
print("\nramos por celula:")
print(est[['problema','C_e7gen','n_conv','n_inc']].assign(frac_inc=lambda d:(d.n_inc/d.C_e7gen).round(3)).to_string())
print("\nNW por M:",est.groupby('M').NW.unique().to_dict(),"| Ratio faixa:",round(est.ratio_min.min(),4),"-",round(est.ratio_max.max(),4))
print("dist_min_arquivo: n",est.distmin_n.sum(),"min global",est.distmin_min.min(),"zeros",est.distmin_zeros.sum())
print("rss_mb: max",est.rss_max.max(),"mediana das celulas",est.rss_max.median())
