"""A14 (ablacao D77, sigma da ⑦ pela regua da sonda) — recomputo da estatistica
sobre o b5m_endpoint7.csv da F5; sonda da regua Sobol; determinismo off x swap_small-lhs."""
import numpy as np, pandas as pd, glob, os, json
import pyarrow.parquet as pq
from scipy.stats import wilcoxon, binomtest
F5="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
e=pd.read_csv(F5+"/baterias/b5m/b5m_endpoint7.csv")
print("endpoint7 colunas:",list(e.columns)); print("configs:",sorted(e.alg.unique()) if "alg" in e else "?")
piv=e.pivot_table(index="label",columns="alg",values="sigma_nn_med")
a,b=piv["b5m"].values,piv["moead_media"].values
ok=~np.isnan(a)&~np.isnan(b); a,b=a[ok],b[ok]
dif=a!=b
print("\n--- A14 ablacao D77 (sigma da ⑦ pela regua da sonda do b5m) ---")
print("celulas pareadas: %d | b5m < piso em %d/%d (sem empate: %d/%d)"%(len(a),(a<b).sum(),len(a),(a[dif]<b[dif]).sum(),dif.sum()))
print("razao mediana b5m/piso: %.4f"%np.median(a[dif]/b[dif]))
print("Wilcoxon p=%.5g  | binomial p=%.5g"%(wilcoxon(a,b).pvalue, binomtest(int((a[dif]<b[dif]).sum()),int(dif.sum())).pvalue))
piv2=e.pivot_table(index="label",columns="alg",values="sigma_nn_med").median()
print("mediana sigma_nn_med por config:\n",piv2.round(4).to_string())
pi=e.pivot_table(index="label",columns="alg",values="igd_plus")
print("\n--- IGD+ da ⑦ ---"); print(pi.median().round(4).to_string())
print("b5m < piso em %d/%d  Wilcoxon p=%.4f"%((pi["b5m"]<pi["moead_media"]).sum(),len(pi),
      wilcoxon(pi["b5m"],pi["moead_media"]).pvalue))

print("\n--- SONDA (regua Sobol, sonda_f52e.csv) ---")
s=pd.read_csv(F5+"/sonda_f52e.csv")
s=s[s.alg=="b5m"] if "alg" in s.columns else s[s.iloc[:,0].astype(str).str.contains("b5m")]
print("colunas:",list(s.columns)[:14]); print("pares:",len(s))
for c in ["wape","corr","cobertura95","n_nan"]:
    if c in s.columns: print("  %-12s mediana=%.5g  p25=%.5g p75=%.5g  min=%.5g"%(c,s[c].median(),s[c].quantile(.25),s[c].quantile(.75),s[c].min()))
deg=s[(s.wape.round(6)==1.0)|(s.corr_ if "corr_" in s else s["corr"]).isna()] if "corr" in s.columns else None
if deg is not None:
    print("  pares DEGENERADOS (WAPE==1 ou corr NaN): %d/%d"%(len(deg),len(s)))
    print(deg[[c for c in ["label","obj","wape","corr","cobertura95"] if c in deg.columns]].to_string(index=False))
    print("  corr>0.9 em %d/%d"%((s["corr"]>0.9).sum(),len(s)))
