import pandas as pd, numpy as np
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
m=pd.read_csv(F5+"/metricas_finais_f52c.csv")
mm=m[(m.exp=="main")&(m.erro.isna())]
pisos=["moead","nsga2","nsga3","smsemoa"]
sa=sorted(set(mm.alg)-set(pisos))
print("algs main:",sorted(set(mm.alg)))
piv=mm.pivot(index="problema",columns="alg",values="igd_plus")
best_piso=piv[[p for p in pisos if p in piv.columns]].min(1)
res=[]
for prob in piv.index:
    v=piv.loc[prob,"c149"] if "c149" in piv.columns else np.nan
    bp=best_piso[prob]
    if np.isnan(v): continue
    delta=100*(bp-v)/bp
    # rank entre TODOS
    r=piv.loc[prob].rank().get("c149")
    rsa=piv.loc[prob,[a for a in piv.columns if a not in pisos]].rank().get("c149")
    res.append(dict(problema=prob,c149=v,melhor_piso=bp,piso_alg=piv.loc[prob,[p for p in pisos if p in piv.columns]].idxmin(),
        delta_pct=delta,bate_piso=v<=bp,rank_geral=r,rank_SA=rsa,n_algs=piv.loc[prob].notna().sum()))
r=pd.DataFrame(res)
print(r.to_string(index=False))
print("\nbate melhor piso em %d/%d"%(r.bate_piso.sum(),len(r)))
d=r[~r.bate_piso]
print("derrotas: %d; dentro do piso de ruido IGD+ (58,98%%): %d; conclusivas: %d"%(len(d),(d.delta_pct.abs()<=58.98).sum(),(d.delta_pct.abs()>58.98).sum()))
print("derrotas conclusivas:",d[d.delta_pct.abs()>58.98][["problema","c149","melhor_piso","delta_pct"]].to_dict("records"))
w=r[r.bate_piso]
print("vitorias conclusivas (>58,98%):",w[w.delta_pct>58.98][["problema","c149","melhor_piso","delta_pct"]].to_dict("records"))
print("\nrank medio geral c149: %.2f de %d"%(r.rank_geral.mean(),r.n_algs.iloc[0]))
print("rank medio entre SA: %.2f"%r.rank_SA.mean())
# rank medio de todos os algs p/ contexto
rk=piv.rank(axis=1).mean().sort_values()
print("\nrank medio IGD+ (25 problemas), todos:"); print(rk.to_string())
r.to_csv(F5+"/baterias/c149/pisos_c149.csv",index=False)
# batch vs main mesmo problema
b=m[(m.exp=="batch")&(m.alg=="c149")].set_index("problema").igd_plus
a=mm[mm.alg=="c149"].set_index("problema").igd_plus
print("\n=== q=10 vs q=1 (mesma semente, mesmo problema) ===")
for p in b.index:
    print(f"  {p:10s} q1={a[p]:.5f}  q10={b[p]:.5f}  delta={100*(a[p]-b[p])/a[p]:+.1f}%")
