import pandas as pd, numpy as np, ast
d=pd.read_csv("queryjoia_ciclos_e7.csv")
d=d[d.n_achados==3].copy()
d['ranks']=d['ranks'].apply(lambda s: ast.literal_eval(s) if isinstance(s,str) else s)
for ramo in ['convergencia','incerteza']:
    g=d[d.ramo==ramo]
    r0=g['rank_min'].values
    print(f"=== {ramo}: n={len(g)} | rank do MELHOR infill (0=argmax/argmin global): "
          f"0 em {int((r0==0).sum())} ({100*(r0==0).mean():.2f}%), <=2 em {int((r0<=2).sum())}, <=5 em {int((r0<=5).sum())}, max={r0.max()}")
    allr=np.array([x for v in g['ranks'] for x in v])
    print(f"   ranks dos 3 infills: mediana {np.median(allr):.1f} | media {allr.mean():.2f} | <=9 em {100*(allr<=9).mean():.1f}% | <=19 em {100*(allr<=19).mean():.1f}% (esperado 3% se aleatorio p/ <=2)")
    print(f"   os 9 piores ciclos:"); 
    print(g.nlargest(6,'rank_min')[['problema','ciclo','rank_min','ranks']].to_string())
# km
print("\nkm_ok distribuicao:",d.km_ok.value_counts().sort_index().to_dict())
print("por ramo:"); print(d.groupby('ramo').km_ok.value_counts().unstack().to_string())
# EA interno
ea=pd.read_csv("ea_interno_e7.csv")
print("\n=== EA interno (||mu|| medio janela1 -> janela19) ===")
print("melhora em",int((ea.delta<0).sum()),"/",len(ea),"ciclos | delta mediano:",round(ea.delta.median(),4))
print(ea.groupby('problema').delta.median().round(4).to_string())
