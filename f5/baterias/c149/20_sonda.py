import pandas as pd, numpy as np, json
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
s=pd.read_csv(F5+"/sonda_f52e.csv")
c=s[s.alg=="c149"].copy()
print("linhas c149:",len(c)," celulas:",c.groupby(['exp','problema']).ngroups," NaN:",c.n_nan.sum()," n_validas unicas:",sorted(c.n_validas.unique())[:5],"...")
print("modelo_flag:",c.modelo_flag.unique())
# 1o e ultimo bloco por celula/objetivo
res=[]
for (exp,prob),g in c.groupby(["exp","problema"]):
    for obj,go in g.groupby("obj"):
        go=go.sort_values("bloco")
        res.append(dict(exp=exp,prob=prob,obj=obj,n_blocos=len(go),
            wape_ini=go.wape.iloc[0],wape_fim=go.wape.iloc[-1],
            corr_ini=go["corr"].iloc[0],corr_fim=go["corr"].iloc[-1],
            cob_ini=go.cobertura95.iloc[0],cob_fim=go.cobertura95.iloc[-1],
            wape_min=go.wape.min(),wape_max=go.wape.max(),
            d_pct=100*(go.wape.iloc[-1]-go.wape.iloc[0])/go.wape.iloc[0] if go.wape.iloc[0]>0 else np.nan))
r=pd.DataFrame(res)
print("\n=== por celula (media dos objetivos) ===")
agg=r.groupby(["exp","prob"]).agg(wape_ini=("wape_ini","mean"),wape_fim=("wape_fim","mean"),
    d_pct=("d_pct","median"),corr_fim=("corr_fim","mean"),cob_ini=("cob_ini","mean"),cob_fim=("cob_fim","mean"),nb=("n_blocos","first")).reset_index()
print(agg.to_string(index=False))
print("\nΔWAPE mediano (todas 30 celulas × obj): %.1f%%"%np.nanmedian(r.d_pct))
print("ΔWAPE mediano main: %.1f%%"%np.nanmedian(r[r.exp=='main'].d_pct), " batch: %.1f%%"%np.nanmedian(r[r.exp=='batch'].d_pct))
print("cobertura95 mediana global: %.3f (1o bloco %.3f)"%(np.nanmedian(r.cob_fim),np.nanmedian(r.cob_ini)))
print("corr final mediana: %.3f"%np.nanmedian(r.corr_fim))
print("wape final mediana: %.3f  min %.4f (%s) max %.3f (%s)"%(np.nanmedian(r.wape_fim),r.wape_fim.min(),
    r.loc[r.wape_fim.idxmin(),['exp','prob','obj']].tolist(),r.wape_fim.max(),r.loc[r.wape_fim.idxmax(),['exp','prob','obj']].tolist()))
r.to_csv(F5+"/baterias/c149/sonda_c149.csv",index=False)
# tendencia: wape por bloco (curva media normalizada) p/ celulas exemplares
for exp,prob in [("main","ZDT1"),("main","MMF1"),("main","DTLZ2"),("batch","ZDT1"),("main","BBOB_F55")]:
    g=c[(c.exp==exp)&(c.problema==prob)].groupby("bloco").wape.mean()
    idx=np.linspace(0,len(g)-1,6).astype(int)
    print(f"  {exp}/{prob} WAPE(media obj) por bloco [{len(g)} blocos]:", [round(float(g.iloc[i]),4) for i in idx])
