"""Bateria universal U1-U12 + modulo GP-BO no SMOKE T11 (POS-T11) e agregados s42."""
import json, glob, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
SM="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81/exp_main_e81_MMF1_0"
m=json.load(open(SM+".manifest.json")); objs=[json.loads(l) for l in open(SM+".jsonl")]
dec=[o for o in objs if o["rec"]=="decision"]; fit=[o for o in objs if o["rec"]=="fit"]
snd=[o for o in objs if o["rec"]=="sonda"]
D,q,M=2,1,2; ok=lambda b:"OK" if b else "**FALHA**"
real=pq.read_table(SM+"__real.parquet").to_pandas()
sur=pq.read_table(SM+"__surrogate.parquet").to_pandas()
pop=pq.read_table(SM+"__pop.parquet").to_pandas()
tim=pq.read_table(SM+"__timing.parquet").to_pandas()
print("===== SMOKE T11 · BATERIA (main/e81/MMF1/s0, POS-T11) =====")
print("U1  FE=31D-1 exato ............. %s  (len①=%d maxfe=%d fe_final=%d)" % (ok(len(real)==61==m["maxfe"]==m["fe_final"]),len(real),m["maxfe"],m["fe_final"]))
print("U1b fe_index denso 0-based ..... %s" % ok(list(real.fe_index)==list(range(61))))
print("U2  init=11D-1 ................. %s  (%d)" % (ok((real.fase=='init').sum()==21),(real.fase=='init').sum()))
doe=pq.read_table("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_0.parquet").to_pandas()
xl=np.array([1.,-1.]); xu=np.array([3.,1.])
dX=np.abs(real[["x0","x1"]].to_numpy()[:21]-doe[["x0","x1"]].to_numpy())/(xu-xl)
print("U2b DoE bit-a-bit vs artefato .. %s  (max|ΔX| relativo = %.3e)" % (ok(dX.max()<=6e-8),dX.max()))
print("U2c doe_hash ⑤≡sidecar ......... %s" % ok(m["doe_hash"]==json.load(open("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_0.manifest.json"))["doe_hash"]))
print("U3  1 fit por decisao .......... %s  (fits=%d dec=%d ④=%d n_ger=%d)" % (ok(len(fit)==len(dec)==len(tim)==m["n_geracoes"]==40),len(fit),len(dec),len(tim),m["n_geracoes"]))
g=[int(s["geracao"]) for s in snd]; gmax=max(int(d["geracao"]) for d in dec)
esp=[x for x in range(1,gmax+1) if x==1 or x%2==0]
print("U4  cadencia sonda g==1∨g%%2==0 .. %s  (%d blocos; ultima ger %d coberta=%s)" % (ok(g==esp),len(g),gmax,gmax in g))
sd=sur[sur.regime=="sonda"]
print("U4b ③-sonda = blocos x 2000 .... %s  (%d linhas)" % (ok(len(sd)==21*2000),len(sd)))
gab=pq.read_table("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet").to_pandas()
dmax=0
for gg,blk in sd.groupby(sd.geracao.astype("Int64").astype(int)):
    dmax=max(dmax,(np.abs(blk[["x0","x1"]].to_numpy()-gab[["x0","x1"]].to_numpy()[:2000])/(xu-xl)).max())
print("U5  join posicional sonda ...... %s  (max|ΔX| relativo = %.3e)" % (ok(dmax<=6e-8),dmax))
print("U8  fe_treino_max MONOTONICO ... %s  (== n_treino-1 em %d/%d)" % (ok(all(f["fe_treino_max"]==f["n_treino"]-1 for f in fit) and all(fit[i]["fe_treino_max"]<=fit[i+1]["fe_treino_max"] for i in range(39))),sum(f["fe_treino_max"]==f["n_treino"]-1 for f in fit),len(fit)))
print("U9  guards ≡ agregados ......... %s  (cache_hits=%s fit_retries=%s guards=%d)" % (ok(m["cache_hits"]==0),m["cache_hits"],sum(d["fit_retries"] for d in dec),sum(1 for o in objs if o["rec"]=="guard")))
inv1=sum((d["tempo_fit_s"]+d["tempo_busca_s"])<=tim.tempo_geracao_s.iloc[i] for i,d in enumerate(dec))
print("U7  inv timing fit+busca≤ger .... %s  (%d/%d)" % (ok(inv1==40),inv1,40))
print("② linhas/geracao == fe ......... %s" % ok(all(len(v)==int(dec[i]["fe"]) for i,(k,v) in enumerate(pop.groupby(pop.geracao.astype(int))))))
print("σ>0 em 100%% da ③ .............. %s  (%d linhas, %d NaN)" % (ok((sur[["sigma_0","sigma_1"]]>0).all().all()),len(sur),int(sur[["sigma_0","sigma_1"]].isna().sum().sum())))
print("\n--- config-echo (mecanismo declarado, POS-T11) ---")
print("pop=100D .......... %s (%d)" % (ok(m["params"]["nsga2_interno"]["pop"]==200),m["params"]["nsga2_interno"]["pop"]))
print("ngen=10 ........... %s" % ok(all(d["ngen"]==10 for d in dec)))
print("nystrom=0 ......... %s" % ok(all(d["nystrom"]==0 for d in dec)))
print("q=1, |lote|==q .... %s (assert True em %d/%d)" % (ok(all(d["n_lote"]==d["q"]==1 for d in dec)),sum(d["assert_lote_eq_q"] for d in dec),len(dec)))
print("seed_gp=1024+iter . %s" % ok(all(d["seed_gp"]==1024+d["iteracao"] for d in dec)))
print("seed_nsga2=2430 ... %s" % ok(all(d["seed_nsga2"]==2430 for d in dec)))
print("TS n_chamadas=ngen  %s" % ok(all(d["draws_thompson"]["n_chamadas"]==10 for d in dec)))
print("TS n_pontos=pop*10  %s" % ok(all(d["draws_thompson"]["n_pontos"]==2000 for d in dec)))
print("train_Yvar=1e-12 .. %s" % ok(all(d["modelo_hp"]["train_Yvar"]==1e-12 for d in dec)))
print("kernel Matern5/2ARD %s" % ok(all(d["modelo_hp"]["kernel"]=="Matern5/2 ARD" for d in dec) and all(f["kernel"]=="get_matern_kernel_with_gamma_prior(D)" for f in fit)))
ard=[all(p["lengthscale_min"]<p["lengthscale_max"] for p in d["modelo_hp"]["por_objetivo"]) for d in dec]
print("ARD vivo (ls_min<max) %s (%d/%d iter-obj)" % (ok(all(ard)),sum(ard)*2,len(dec)*2))
ls=[d["modelo_hp"]["por_objetivo"][0]["lengthscale_med"] for d in dec]
print("GP nao congelado ... %s (%d/%d pares consecutivos mudam)" % (ok(all(ls[i]!=ls[i+1] for i in range(39))),sum(ls[i]!=ls[i+1] for i in range(39)),39))
print("dtype float64 ...... %s" % ok(all(d["dtype_check"]=="torch.float64" for d in dec)))
print("evento de geracao .. rec='decision', caminho=%r" % dec[0]["caminho"])
