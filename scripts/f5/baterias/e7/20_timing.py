import pandas as pd, numpy as np
df=pd.read_csv("estrutural_e7.csv")
df['soma_comp']=df.tempo_fit_tot+df.tempo_busca_tot+df.tempo_sonda_tot+df.tempo_aval_tot
df['frac_busca']=df.tempo_busca_tot/df.tempo_total_s
df['frac_fit']=df.tempo_fit_tot/df.tempo_total_s
df['frac_sonda']=df.tempo_sonda_tot/df.tempo_total_s
df['overhead']=(df.tempo_total_s-df.soma_comp)/df.tempo_total_s
df['s_por_ciclo']=df.tempo_total_s/(df.C_e7gen+1)
pd.set_option('display.width',260)
print(df[['problema','D','C_e7gen','tempo_total_s','frac_fit','frac_busca','frac_sonda','overhead','s_por_ciclo','rss_max']].round(4).to_string())
print("\nWALL total 25 celulas (h):",round(df.tempo_total_s.sum()/3600,2))
print("fracao do wall: busca",round(df.tempo_busca_tot.sum()/df.tempo_total_s.sum(),4),
      "| fit",round(df.tempo_fit_tot.sum()/df.tempo_total_s.sum(),4),
      "| sonda",round(df.tempo_sonda_tot.sum()/df.tempo_total_s.sum(),4),
      "| aval real",round(df.tempo_aval_tot.sum()/df.tempo_total_s.sum(),6))
print("s/ciclo: min",round(df.s_por_ciclo.min(),2),"max",round(df.s_por_ciclo.max(),2),"mediana",round(df.s_por_ciclo.median(),2))
# custo do fit ~ D? passos SGD = 8e4*? o batch=D => custo por passo ~ D
print("\ncusto do 1o fit (80k passos) vs D:")
print(df[['problema','D','tempo_fit_inicial_s']].sort_values('D').to_string())
print("correlacao tempo_fit_inicial x D:",round(np.corrcoef(df.D,df.tempo_fit_inicial_s)[0,1],4))
# passos SGD totais por run
df['passos_sgd']=80000+8000*(df.C_e7gen+1)
print("passos SGD por run: D=30 ->",int(df[df.D==30].passos_sgd.iloc[0]),"| total campanha:",int(df.passos_sgd.sum()))
df.to_csv("timing_e7.csv",index=False)
