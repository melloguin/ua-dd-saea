"""Query-joia do e81 re-medida: maximin top-q em [0,1]^D.
Roda sobre (a) as 30 celulas da s42 e (b) o smoke T11 (POS-T11) — READ-ONLY."""
import json, glob, os, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.spatial.distance import cdist

DOE="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe"
def bounds(prob, sem):
    m=json.load(open(f"{DOE}/{prob}/doe_{prob}_{sem}.manifest.json"))
    return np.array(m["bounds"]["xl"],float), np.array(m["bounds"]["xu"],float)

def analisa(d, tag):
    js=glob.glob(d+"/*.jsonl")[0]
    mfp=[p for p in glob.glob(d+"/*.manifest.json") if not p.endswith("__final.manifest.json")][0]
    m=json.load(open(mfp))
    prob, sem, q = m["problema"], int(m["semente"]), int(m.get("q") or 1)
    objs=[json.loads(l) for l in open(js)]
    dec=[o for o in objs if o.get("rec")=="decision"]
    xl,xu=bounds(prob,sem); D=len(xl); xc=[f"x{i}" for i in range(D)]
    real=pq.read_table(glob.glob(d+"/*__real.parquet")[0], columns=xc).to_pandas().to_numpy(float)
    sur=pq.read_table(glob.glob(d+"/*__surrogate.parquet")[0],
                      columns=["regime","geracao","real_solution_id"]+xc).to_pandas()
    on=sur[sur.regime=="online"]
    grp={int(g):v for g,v in on.groupby(on.geracao.astype("Int64").astype(int))}
    W=(xu-xl)
    r=dict(tag=tag, celula=os.path.basename(os.path.dirname(d)) if tag!="smoke" else "smoke_MMF1_s0",
           problema=prob, semente=sem, D=D, q=q, n_dec=len(dec),
           val_ok=0, val_n=0, dmax=0.0, conj_ok=0, ordem_ok=0, marca_ok=0, linkX_ok=0, linkX_n=0,
           nofb_n=0, fb_n=0, distmin_ok=0)
    for o in dec:
        g=int(o["geracao"]); nt=int(o["n_train"]); nfa=int(o["n_front_acq"])
        mx=np.asarray(o["maximin_escolhido"],float); idx=list(o["idx_escolhidos"])
        blk=grp[g]; X=blk[xc].to_numpy(float)
        ds=(real[:nt]-xl)/W; cand=(X-xl)/W
        dmin=cdist(cand,ds).min(axis=1)
        fb = nfa < q
        if fb:
            r["fb_n"]+=1
            continue
        r["nofb_n"]+=1; r["val_n"]+=1
        order=np.argsort(dmin, kind="stable")
        top=order[-q:]
        rec=np.sort(dmin[top])
        d_=float(np.max(np.abs(rec-np.sort(mx))))
        r["dmax"]=max(r["dmax"],d_)
        if d_<=1e-6: r["val_ok"]+=1
        if set(top.tolist())==set(idx): r["conj_ok"]+=1
        if list(top.tolist())==list(idx): r["ordem_ok"]+=1
        marc=sorted(np.flatnonzero(blk.real_solution_id.notna().to_numpy()).tolist())
        if marc==sorted(idx): r["marca_ok"]+=1
        # link X bit-a-bit: ③ marcada  vs ① no solution_id
        sids=blk.real_solution_id.to_numpy()
        for pos in marc:
            sid=int(sids[pos]); r["linkX_n"]+=1
            if np.array_equal(X[pos], real[sid]): r["linkX_ok"]+=1
        # dist_min_arquivo = min do lote, espaco NATIVO
        if "dist_min_arquivo" in o and o["dist_min_arquivo"] is not None:
            dn=cdist(X[sorted(idx)], real[:nt]).min(axis=1).min()
            if abs(dn-float(o["dist_min_arquivo"]))<=1e-6*max(1.0,abs(dn)): r["distmin_ok"]+=1
    return r

rows=[]
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if os.path.isdir(d): rows.append(analisa(d,"s42"))
rows.append(analisa("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/e81","smoke"))
df=pd.DataFrame(rows); df.to_csv("t11_e81_joia.csv",index=False)
pd.set_option("display.width",250); pd.set_option("display.max_columns",50)
print(df.to_string(index=False))
s=df[df.tag=="s42"]
print("\n=== s42 AGREGADO (30 celulas) ===")
print("decisoes:",s.n_dec.sum()," sem fallback:",s.nofb_n.sum()," fallback:",s.fb_n.sum())
for k in ["val_ok","conj_ok","ordem_ok","marca_ok","distmin_ok"]:
    print(f"  {k}: {s[k].sum()} / {s.nofb_n.sum()}")
print("  linkX bit-identico:", s.linkX_ok.sum(), "/", s.linkX_n.sum())
print("  |Delta| maximo global:", s.dmax.max())
k=df[df.tag=="smoke"].iloc[0]
print("\n=== SMOKE T11 (POS-T11) ===")
print(f"  decisoes={k.n_dec} val={k.val_ok}/{k.val_n} conj={k.conj_ok} ordem={k.ordem_ok} marca={k.marca_ok} linkX={k.linkX_ok}/{k.linkX_n} distmin={k.distmin_ok} |D|max={k.dmax}")
