import pandas as pd, numpy as np
S=pd.read_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/sonda_f52e.csv")
S["bloco"]=pd.to_numeric(S.bloco,errors="coerce")   # ARMADILHA: vem como string -> ordem lexicografica
c=S[S.alg=="c149"]
def dwape(df):
    r=[]
    for (e,p,o),g in df.groupby(["exp","problema","obj"]):
        g=g.sort_values("bloco"); a=g.wape.iloc[0]; b=g.wape.iloc[-1]
        r.append(dict(exp=e,problema=p,obj=o,b0=g.bloco.iloc[0],bN=g.bloco.iloc[-1],w0=a,wN=b,d=(b-a)/a))
    return pd.DataFrame(r)
D=dwape(c)
for exp in ["main","batch"]:
    d=D[D.exp==exp]
    print(f"[{exp}] n={len(d)} mediana DeltaWAPE = {d.d.median()*100:+.2f}%")
    if exp=="batch":
        d2=d[d.problema!="ZDT4"]
        print(f"        SEM q10_ZDT4: n={len(d2)} mediana = {d2.d.median()*100:+.2f}%  (move o numero publicado em {(d2.d.median()-d.d.median())*100:+.2f} p.p.)")
        print(d.assign(pct=(d.d*100).round(1))[["problema","obj","b0","bN","w0","wN","pct"]].to_string(index=False))
b=c[c.exp=="batch"].sort_values("bloco")
last=b.groupby(["problema","obj"]).tail(1)
for col in ["cobertura95","corr"]:
    print(f"[batch] {col} final: mediana COM ZDT4 {last[col].median():.4f} | SEM {last[last.problema!='ZDT4'][col].median():.4f}")
print("\n[ZDT4 batch] linhas contaminadas em sonda_f52e.csv:",len(c[(c.exp=='batch')&(c.problema=='ZDT4')]),"de",len(c[c.exp=='batch']),"do batch c149 e",len(S),"do estudo")
