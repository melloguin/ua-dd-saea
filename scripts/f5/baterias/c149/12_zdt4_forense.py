import json,numpy as np,pandas as pd,pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
p=f"{ROOT}/q10_ZDT4/42/exp_batch_c149_ZDT4_42"
D=10;M=2;q=10;n_init=109
real=pq.read_table(p+"__real.parquet").to_pandas()
sur=pq.read_table(p+"__surrogate.parquet").to_pandas()
print("③ meta:",sur.algoritmo.unique(),sur.problema.unique(),sur.semente.unique())
on=sur[sur.regime=="online"]
sel=on[on.real_solution_id.notna()]
XC=[f"x{j}" for j in range(D)]
for g in [1,2,3,50]:
    s3=sel[sel.geracao==g]; sids=s3.real_solution_id.astype(int).values
    X3=s3[XC].values; X1=real.set_index("solution_id").loc[sids,XC].values
    # conjunto igual?
    a=set(map(tuple,np.round(X3,6))); b=set(map(tuple,np.round(X1,6)))
    print(f"g={g} sids={sids[:3]}... |∩conjunto|={len(a&b)}/10  dX_diag_max={np.abs(X3-X1).max():.4f}")
    # o X3 esta no front daquela geracao? procure X1 dentro de TODAS as 1000 linhas online da geracao
    allg=on[on.geracao==g][XC].values
    hits=0
    for row in X1:
        d=np.abs(allg-row).max(1); hits+= (d.min()<1e-6)
    print(f"     X da ① achado no front ③ da MESMA geracao: {hits}/10")
    # e em qualquer geracao?
    if g<=3:
        allx=on[XC].values
        h2=0
        for row in X1:
            d=np.abs(allx-row).max(1); h2+=(d.min()<1e-6)
        print(f"     X da ① achado em QUALQUER geracao da ③: {h2}/10")
# a ③ é de outra semente/execucao? compara com o DoE
init=real[real.fase=="init"][XC].values
print("\n① init[0][:4]",init[0][:4])
# a ③ tem o mesmo espaco de X? distribuicao
print("③ x0 range",on.x0.min(),on.x0.max()," ① x0 range",real.x0.min(),real.x0.max())
print("③ x1 range",on.x1.min(),on.x1.max()," ① x1 range",real.x1.min(),real.x1.max())
# sonda: os X da sonda batem entre as duas celulas ZDT4 (main x batch)?
son_b=sur[sur.regime=="sonda"]
pm=f"{ROOT}/ZDT4/42/exp_main_c149_ZDT4_42"
sm=pq.read_table(pm+"__surrogate.parquet",columns=["regime","geracao"]+XC).to_pandas()
son_m=sm[sm.regime=="sonda"]
b1=son_b[son_b.geracao==son_b.geracao.min()][XC].values
m1=son_m[son_m.geracao==son_m.geracao.min()][XC].values
print("sonda X batch==main (mesmo artefato):",np.abs(b1-m1).max())
# f_best do log bate com min da ①?
dec=[json.loads(l) for l in open(p+".jsonl") if '"decision"' in l]
print("f_best log g=1:",dec[0]["f_best"]," ① min f:",real[["f0","f1"]].min().values)
