import json, glob, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
R="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
fb=[]; guards=[]; inv=[]; ard=[]; sat=[]
tot=dict(dec=0, inv1=0, inv2_ok=0, inv2_n=0, ardviv=0, ardn=0, glob=0)
for lab in sorted(os.listdir(R)):
    d=f"{R}/{lab}/42"
    if not os.path.isdir(d): continue
    objs=[json.loads(l) for l in open(glob.glob(d+"/*.jsonl")[0])]
    m=json.load(open([p for p in glob.glob(d+"/*.manifest.json") if not p.endswith("__final.manifest.json")][0]))
    dec=[o for o in objs if o["rec"]=="decision"]; grd=[o for o in objs if o["rec"]=="guard"]
    tim=pq.read_table(glob.glob(d+"/*__timing.parquet")[0]).to_pandas()
    q=int(m.get("q") or 1); D=int(m["params"]["qpots_kwargs"]["dim"]); pop=int(m["params"]["nsga2_interno"]["pop"])
    snd_g=set(int(o["geracao"]) for o in objs if o["rec"]=="sonda")
    tot["dec"]+=len(dec)
    for i,o in enumerate(dec):
        g=int(o["geracao"]); tg=float(tim.tempo_geracao_s.iloc[i]); ts=float(tim.tempo_pred_sonda_s.iloc[i] or 0)
        if o["tempo_fit_s"]+o["tempo_busca_s"]<=tg: tot["inv1"]+=1
        exceed=(o["tempo_fit_s"]+o["tempo_busca_s"]+ts)>tg
        tot["inv2_n"]+=1
        if exceed==(g in snd_g): tot["inv2_ok"]+=1
        elif g in snd_g: inv.append((lab,g,o["tempo_fit_s"],o["tempo_busca_s"],ts,tg))
        if o["n_front_acq"]==pop: sat.append((lab,g,pop))
        for j,p in enumerate(o["modelo_hp"]["por_objetivo"]):
            tot["ardn"]+=1
            if p["lengthscale_min"]<p["lengthscale_max"]: tot["ardviv"]+=1
        if o["n_front_acq"]<q:
            fb.append(dict(cel=lab,g=g,n_front=o["n_front_acq"],q=q,n_lote=o["n_lote"]))
    for gg in grd:
        guards.append(dict(cel=lab,name=gg.get("name"),**{k:v for k,v in gg.items() if k in("n_front","n_lote","q","n_completado","n_pool_rank1mais","valor")}))
    # espectro ARD por celula-objetivo (ultima geracao)
    for j,p in enumerate(dec[-1]["modelo_hp"]["por_objetivo"]):
        ard.append(dict(cel=lab,obj=j,ratio=p["lengthscale_max"]/p["lengthscale_min"]))
    tot["glob"]+=1
print("=== s42: 30 celulas, %d decisoes ===" % tot["dec"])
print("inv-1 fit+busca<=tempo_geracao : %d/%d" % (tot["inv1"],tot["dec"]))
print("inv-2 excede sse tem sonda     : %d/%d  (excecoes: %s)" % (tot["inv2_ok"],tot["inv2_n"],[(c,g) for c,g,*_ in inv]))
for c,g,f_,b_,s_,t_ in inv: print("   %s g%d: fit %.4f + busca %.4f + sonda %.4f = %.4f  vs tempo_geracao %.4f (overhead %.4f)"%(c,g,f_,b_,s_,f_+b_+s_,t_,t_-(f_+b_+s_)))
print("ARD vivo (ls_min<ls_max)       : %d/%d iteracoes-objetivo" % (tot["ardviv"],tot["ardn"]))
gd=pd.DataFrame(guards); fbd=pd.DataFrame(fb)
print("\n=== DI-25 fallback qmaximin ===")
print("geracoes com n_front_acq<q: %d" % len(fbd))
print(fbd.groupby("cel").size().to_string())
print("registros guard: %d" % len(gd)); print(gd.groupby(["cel","name"]).size().to_string())
cc=gd[gd.name=="lote_completado_por"] if "lote_completado_por" in set(gd.name) else gd[gd.name.notna()]
lm=gd[gd.name=="lote_menor_que_q"]
if len(lm): 
    print("\nreconciliacao (lote_menor_que_q):")
    print("  n_lote+n_completado==q : %d/%d" % (sum((lm.n_lote.fillna(0)+lm.get('n_completado',pd.Series(0,index=lm.index)).fillna(0))==lm.q) if 'n_completado' in lm else -1, len(lm)))
print("\ncolunas guard:", list(gd.columns))
print(gd.head(4).to_string())
ad=pd.DataFrame(ard).sort_values("ratio")
print("\n=== espectro de anisotropia ARD (ultima geracao, 68 celula-objetivo) ===")
print("menores 5:"); print(ad.head(5).to_string(index=False))
print("maiores 5:"); print(ad.tail(5).to_string(index=False))
print("mediana ratio: %.3f | ratio>1.05 em %d/%d" % (ad.ratio.median(),(ad.ratio>1.05).sum(),len(ad)))
print("\n=== saturacao do front (n_front_acq==pop) ===")
sd=pd.DataFrame(sat,columns=["cel","g","pop"])
print(sd.groupby("cel").size().to_string() if len(sd) else "nenhuma")
pd.DataFrame(fb).to_csv("t11_e81_fallback.csv",index=False); gd.to_csv("t11_e81_guards.csv",index=False); ad.to_csv("t11_e81_ard.csv",index=False)
