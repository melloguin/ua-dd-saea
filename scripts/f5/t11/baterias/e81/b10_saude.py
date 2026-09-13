import pandas as pd, numpy as np
F="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
s=pd.read_csv(F+"/sonda_f52e.csv"); s=s[s.alg=="e81"]
print("medicoes de sonda e81:",len(s),"| celula-objetivo:",s.groupby(["exp","problema","obj"]).ngroups)
r=[]
for (e,p,o),g in s.groupby(["exp","problema","obj"]):
    g=g.assign(_b=pd.to_numeric(g.bloco,errors="coerce")).sort_values(["fe_treino_max","_b"])
    r.append(dict(exp=e,prob=p,obj=o,w0=g.wape.iloc[0],wN=g.wape.iloc[-1],
                  d=(g.wape.iloc[-1]-g.wape.iloc[0])/g.wape.iloc[0]*100,
                  cobN=g.cobertura95.iloc[-1],corrN=g["corr"].iloc[-1],nan=g.n_nan.sum()))
d=pd.DataFrame(r)
mn=d[d.exp=="main"]; bt=d[d.exp=="batch"]
print("\nDeltaWAPE 1o->ultimo bloco (mediana por celula-objetivo):")
print("  main : %+.1f%%  (melhoram %d/%d)" % (mn.d.median(),(mn.d<0).sum(),len(mn)))
print("  batch: %+.1f%%  (melhoram %d/%d)" % (bt.d.median(),(bt.d<0).sum(),len(bt)))
print("\nCobertura +-1.96s FINAL: mediana %.4f (main %.4f) | >=0.90 em %d/%d | minimo %.4f (%s)"
      % (d.cobN.median(),mn.cobN.median(),(d.cobN>=0.90).sum(),len(d),d.cobN.min(),d.loc[d.cobN.idxmin(),["prob","obj"]].to_dict()))
print("sigma-NaN em toda a sonda:",int(d.nan.sum()))
print("\nmelhores 3 DeltaWAPE:"); print(d.nsmallest(3,"d")[["exp","prob","obj","d"]].to_string(index=False))
print("pioras:"); print(d[d.d>0][["exp","prob","obj","d"]].to_string(index=False))
print("\ncorr(mu,f) final positiva em %d/%d | faixa %.3f .. %.5f" % ((d.corrN>0).sum(),len(d),d.corrN.min(),d.corrN.max()))
m=pd.read_csv(F+"/metricas_finais_f52c.csv"); e=m[m.alg=="e81"]
print("\n=== q=1 x q=10 (mesmos 5 problemas) ===")
b=e[e.exp=="batch"].set_index("problema"); a=e[e.exp=="main"].set_index("problema")
for p in b.index:
    print("  %-10s IGD+ main %10.4f -> batch %10.4f (%s) | n_nd %4d -> %4d"
          % (p,a.loc[p,"igd_plus"],b.loc[p,"igd_plus"],"MELHORA" if b.loc[p,"igd_plus"]<a.loc[p,"igd_plus"] else "piora",a.loc[p,"n_nd"],b.loc[p,"n_nd"]))
sb=m[(m.alg=="sobol_batch")].set_index("problema")
print("\n=== e81 q=10 x sobol_batch (MESMO orcamento) ===")
for p in b.index:
    if p in sb.index:
        print("  %-10s IGD+ e81 %10.4f x sobol %10.4f (%s) | HV %.4f x %.4f"
              % (p,b.loc[p,"igd_plus"],sb.loc[p,"igd_plus"],"e81 VENCE" if b.loc[p,"igd_plus"]<sb.loc[p,"igd_plus"] else "sobol vence",b.loc[p,"hv"],sb.loc[p,"hv"]))
t=pd.read_csv(F+"/tempo_f52d.csv"); te=t[t.alg=="e81"]
print("\n=== tempo === total %.2f h-core | maquinas: %s" % (te.wall_s.sum()/3600, dict(te.maquina.value_counts())))
print("main %.2f h | batch %.2f h | mais cara: %s %.2f h" % (te[te.exp=='main'].wall_s.sum()/3600, te[te.exp=='batch'].wall_s.sum()/3600, te.loc[te.wall_s.idxmax(),'label'], te.wall_s.max()/3600))
