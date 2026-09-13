import json
import numpy as np, pandas as pd
B="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c122/exp_main_c122_MMF1_0"
s=pd.read_parquet(B+"__surrogate.parquet")
print("colunas:",list(s.columns))
print(s.groupby("regime").size())
for rg in s.regime.unique():
    sub=s[s.regime==rg]
    nn={c:int(sub[c].notna().sum()) for c in ["mu_0","mu_1","sigma_0","sigma_1","pred_score","pred_confianca","pred_classe","real_solution_id","fe_treino_max","espaco_modelo","transf_tipo"] if c in sub.columns}
    print("\n--",rg,"n=",len(sub)); print("  nao-nulos:",nn)
    print("  pred_tipo:",sub.pred_tipo.unique(),"modelo_flag:",sub.modelo_flag.unique())
    if rg=="sonda_estratificada":
        print("  mu_0 stats:",sub.mu_0.describe().to_dict())
        print("  sigma_0 stats:",sub.sigma_0.describe().to_dict())
        print("  geracoes:",sorted(sub.geracao.dropna().unique().astype(int)))
        print("  linhas/geracao:",sub.groupby("geracao").size().unique())
