import glob, pandas as pd
for alg in ["c217","b4"]:
    p=glob.glob(f"/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/{alg}/*__surrogate.parquet")
    if not p: print(alg,"sem parquet"); continue
    s=pd.read_parquet(p[0])
    sub=s[s.regime=="sonda_estratificada"]
    print(f"== {alg} ({p[0].split('/')[-1]}) regimes:",s.groupby('regime').size().to_dict())
    if len(sub):
        cols=[c for c in ["mu_0","sigma_0","pred_score","pred_classe","pred_confianca"] if c in sub.columns]
        print("   estrat n=",len(sub),"nao-nulos:",{c:int(sub[c].notna().sum()) for c in cols},"pred_tipo:",sub.pred_tipo.unique())
