import json,os,numpy as np,pandas as pd,pyarrow.parquet as pq, collections
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
df=pd.read_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149/estrutural_c149.csv")
print(df[["exp","prob","D","M","U4_G","POP_n_ger","POP_size_min","POP_size_max","U10_pop_linhas","U2_n_init","maxfe"]].to_string(index=False))
print()
# semantica da ②
for lab,exp,prob in [("ZDT1","main","ZDT1"),("MMF1","main","MMF1"),("q10_ZDT4","batch","ZDT4")]:
    p=f"{ROOT}/{lab}/42/exp_{exp}_c149_{prob}_42"
    pop=pq.read_table(p+"__pop.parquet").to_pandas()
    real=pq.read_table(p+"__real.parquet").to_pandas()
    g=pop.groupby("geracao").size()
    print(f"--- {exp}/{prob}: ② {len(pop)} linhas, gers {g.index.min()}..{g.index.max()}, tam {g.iloc[0]},{g.iloc[1]},{g.iloc[2]} ... {g.iloc[-1]}")
    print("    diff tam:", set(np.diff(g.values)), " g1 solids:", pop[pop.geracao==g.index[0]].solution_id.min(), "..", pop[pop.geracao==g.index[0]].solution_id.max(), "n=",g.iloc[0])
    # é o arquivo acumulado? ou o ND do arquivo?
    n_init=len(real[real.fase=="init"])
    print("    n_init=",n_init," 31D-1=",len(real))
    for gg in [g.index[0],g.index[1],g.index[-1]]:
        sids=set(pop[pop.geracao==gg].solution_id)
        print(f"    ger {gg}: |pop|={len(sids)} max_sid={max(sids)} subset_do_arquivo_ate_max={sids<=set(range(0,max(sids)+1))}")
