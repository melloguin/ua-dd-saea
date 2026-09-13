"""[T11] Re-medida INDEPENDENTE do mecanismo do c122 sobre a s42 (25 celulas).
READ-ONLY. Nao toca data/experiments."""
import json, math, os, glob
import numpy as np, pandas as pd

ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122"
out=[]
for prob in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,prob,"42")
    if not os.path.isdir(d): continue
    base=glob.glob(os.path.join(d,"*.manifest.json"))[0][:-len(".manifest.json")]
    mf=json.load(open(base+".manifest.json"))
    recs=[json.loads(l) for l in open(base+".jsonl")]
    dec=[r for r in recs if r.get("rec")=="decision"]
    snd=[r for r in recs if r.get("rec")=="sonda"]
    est=[r for r in recs if r.get("rec")=="sonda_estratificada"]
    D=int(mf["params"]["pm"]["indpb"]**-1+.5) if False else None
    real=pd.read_parquet(base+"__real.parquet")
    D=len([c for c in real.columns if c.startswith("x")])
    M=len([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    N=int(mf["params"]["N_MU"]); ch=int(mf.get("cache_hits") or 0)
    r={"prob":prob,"D":D,"M":M,"N":N,"maxfe":mf["maxfe"],"fe_final":mf["fe_final"],
       "ok_31D1":mf["maxfe"]==31*D-1,"ok_hardstop":mf["fe_final"]==mf["maxfe"],
       "n_ger":mf["n_geracoes"],"cache_hits":ch,
       "ok_nger":mf["n_geracoes"]==mf["maxfe"]-(11*D-1)+ch,
       "n_dec":len(dec),"n_snd":len(snd),"n_est":len(est)}
    # prioridade Q1>Q2>Q3
    okp=0; ncat=0; pool=0; npool=0; qmax=0; gate_ok=0; gate_n=0; eupd_ok=0; eupd_n=0
    for e in dec:
        cat=(e.get("motivo") or "").split("categoria=")[-1].split(" ")[0]
        q1,q2,q3=e.get("n_q1"),e.get("n_q2"),e.get("n_q3")
        if q1 is None:
            esp="None"
        else:
            esp="ps" if q1>0 else ("s" if q2>0 else ("p" if q3>0 else "None"))
        okp+= (esp==cat); ncat+=1
        if e.get("n_acordo") is not None:
            npool+=1; pool+= (e["n_acordo"]+e["n_desacordo"]==7000)
        if q1 is not None:
            sz={"ps":q1,"s":q2,"p":q3}.get(cat,0)
            qmax+= (e.get("n_cands")==min(sz,300))
        for tag in ("p","s"):
            a=e.get("accs_"+tag); sk=e.get("skip_treino_"+tag); ep=e.get("epocas_"+tag)
            if a is None or sk is None: continue
            gate_n+=1; gate_ok+= ((min(a)>=0.9)==bool(sk))
            if not sk and ep is not None:
                eupd_n+=1
                eupd_ok+= (ep==math.ceil(20*((0.9-min(a))/0.9)))
    r.update(prio_ok=okp,prio_n=ncat,pool_ok=pool,pool_n=npool,qmax_ok=qmax,
             gate_ok=gate_ok,gate_n=gate_n,eupd_ok=eupd_ok,eupd_n=eupd_n)
    # T11: campos novos presentes na s42?
    r["s42_tem_ref_ids"]=any("ref_ids" in e for e in dec+snd)
    r["s42_tem_REGRA"]="REGRA_DO_ROTULO" in (mf.get("sigma_dict") or {})
    r["s42_tem_estrat"]=len(est)>0
    r["s42_tem_campanha_id"]="campanha_id" in mf
    r["s42_tem_y_treino"]=any("y_treino_dist_p" in e for e in dec)
    r["s42_nref_manifesto"]=mf["sonda"]["n_ref"]
    r["s42_nref_recs_iguais_N"]=sum(1 for e in snd if f"n_ref={N}" in (e.get("motivo") or ""))
    r["s42_nref_campo"]=sum(1 for e in snd if "n_ref" in e)
    # A27: e(z) do bloco 1 x 2N
    s=pd.read_parquet(base+"__surrogate.parquet",columns=["regime","geracao","pred_score"])
    sd=s[s.regime=="sonda"]
    g1=sd[sd.geracao==1]["pred_score"]
    g2=sd[sd.geracao>=2]["pred_score"]
    r["ez_max_g1"]=float(g1.max()); r["ez_max_g2p"]=float(g2.max())
    r["g1_gt_2N"]=bool(g1.max()>2*N); r["g1_le_2ninit"]=bool(g1.max()<=2*(11*D-1))
    r["g2p_le_2N"]=bool(g2.max()<=2*N+1e-6)
    r["frac_g1_gt_2N"]=float((g1>2*N).mean())
    out.append(r); print(prob,"ok")
df=pd.DataFrame(out)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c122/remedida_s42.csv",index=False)
print(df.to_string())
