"""Re-medicao das IDENTIDADES da s42 (45 celulas): f_best/n_front1 do ⑥,
⑦ ND-recomputado, join posicional da sonda, binding do dataset, LHS, bounds."""
import os, json, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
DATA="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b5m"

def nd_mask(F):
    n=F.shape[0]; m=np.ones(n,bool)
    for i in range(n):
        if not m[i]: continue
        d=(F<=F[i]).all(1)&(F<F[i]).any(1)
        if d.any(): m[i]=False
    return m

rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    man=[p for p in glob.glob(d+"/*.manifest.json") if "__final" not in p]
    if not man: continue
    base=man[0][:-len(".manifest.json")]
    m=json.load(open(man[0]))
    recs=[json.loads(l) for l in open(base+".jsonl")]
    dec=[r for r in recs if r["rec"]=="decision"]
    sg=pq.read_table(base+"__surrogate.parquet").to_pandas()
    bu=sg[sg.regime=="offline"]; so=sg[sg.regime=="sonda"]
    xs=[c for c in sg.columns if c.startswith("x")]
    mus=[c for c in sg.columns if c.startswith("mu_")]
    fin=pq.read_table(base+"__final.parquet").to_pandas()
    rea=pq.read_table(base+"__real.parquet").to_pandas()
    fcols=[c for c in fin.columns if c.startswith("f")]
    # f_best / n_front1 do ⑥ vs ③
    ok_fb=0; ok_nf=0; maxrel=0.0
    for r in dec:
        g=r["geracao"]; Fg=bu[bu.geracao==g][mus].values
        fb=np.asarray(r["f_best"],float); calc=Fg.min(0)
        rel=np.max(np.abs(fb-calc)/np.maximum(np.abs(calc),1e-30))
        maxrel=max(maxrel,float(rel)); ok_fb+=int(rel<1e-6)
        ok_nf+=int(int(nd_mask(Fg).sum())==r["n_front1"])
    # ⑦ ND
    ndc=nd_mask(fin[fcols].values.astype(np.float64))
    ok7=int((ndc==fin.nd_pos_real.values.astype(bool)).all())
    # link posicional (origem_geracao, origem_linha) -> ③
    gl=int(fin.origem_geracao.iloc[0]); B=bu[bu.geracao==gl][xs].values
    ok_link=int(np.array_equal(B[fin.origem_linha.values.astype(int)], fin[xs].values))
    # sonda join posicional
    sp=os.path.join(DATA,"sonda","sonda_%s.parquet"%m["problema"])
    dS=np.nan
    if os.path.exists(sp):
        S=pq.read_table(sp).to_pandas()
        sx=[c for c in S.columns if c.startswith("x")][:len(xs)]
        dS=float(np.abs(S[sx].values[:len(so)].astype(np.float32)-so[xs].values.astype(np.float32)).max())
    # binding do dataset: ① vs artefato
    dsdir=os.path.join(DATA,"datasets",m["problema"])
    cand=sorted(glob.glob(dsdir+"/ds_*_42.parquet"))+sorted(glob.glob(dsdir+"/*.parquet"))
    dD=np.nan
    for c in cand:
        try:
            T=pq.read_table(c).to_pandas()
            tx=[q for q in T.columns if q.startswith("x")][:len(xs)]
            if len(T)==len(rea):
                dD=float(np.abs(T[tx].values.astype(np.float32)-rea[xs].values.astype(np.float32)).max()); break
        except Exception: pass
    # LHS estratificado na ger.1 + bounds
    g1=bu[bu.geracao==1][xs].values.astype(np.float64); pop=g1.shape[0]
    lo=bu[xs].values.min(0); hi=bu[xs].values.max(0)
    lo2=np.minimum(lo,rea[xs].values.min(0)); hi2=np.maximum(hi,rea[xs].values.max(0))
    u=(g1-lo2)/np.maximum(hi2-lo2,1e-300)
    estrat=int(sum(1 for j in range(g1.shape[1])
                   if np.array_equal(np.sort(np.floor(np.clip(u[:,j],0,1-1e-12)*pop).astype(int)),np.arange(pop))))
    inter=int(sum(1 for r in np.ascontiguousarray(g1.astype(np.float32))
                  if bytes(r) in set(map(bytes,np.ascontiguousarray(rea[xs].values.astype(np.float32))))))
    rows.append(dict(label=lab,n_dec=len(dec),ok_fbest=ok_fb,ok_nfront1=ok_nf,maxrel_fbest=maxrel,
                     c7_nd_ok=ok7,c7_link_ok=ok_link,sonda_dX=dS,dataset_dX=dD,
                     lhs_dims_estrat=estrat,D=len(xs),intersec_ds=inter,
                     x_fora_bounds=int(((bu[xs].values<lo2-1e-6)|(bu[xs].values>hi2+1e-6)).sum())))
    print("ok",lab,flush=True)
df=pd.DataFrame(rows); df.to_csv(os.path.join(OUT,"t11_b5m_identidades.csv"),index=False)
print("\n=== %d celulas ==="%len(df))
print("f_best identidade   : %d / %d eventos (celulas 100%%: %d/%d) maxrel=%.3g"%(
      df.ok_fbest.sum(),df.n_dec.sum(),(df.ok_fbest==df.n_dec).sum(),len(df),df.maxrel_fbest.max()))
print("n_front1 identidade : %d / %d eventos (celulas 100%%: %d/%d)"%(
      df.ok_nfront1.sum(),df.n_dec.sum(),(df.ok_nfront1==df.n_dec).sum(),len(df)))
print("⑦ ND == nd_pos_real : %d/%d   link posicional bit-a-bit: %d/%d"%(df.c7_nd_ok.sum(),len(df),df.c7_link_ok.sum(),len(df)))
print("sonda max|ΔX|       : max=%.3g (celulas com 0,0: %d/%d)"%(np.nanmax(df.sonda_dX),(df.sonda_dX==0).sum(),len(df)))
print("dataset ① max|ΔX|   : max=%.3g (celulas com 0,0: %d/%d, NaN=%d)"%(np.nanmax(df.dataset_dX),(df.dataset_dX==0).sum(),len(df),df.dataset_dX.isna().sum()))
print("LHS dims estratific.: %d/%d celulas com D/D"%((df.lhs_dims_estrat==df.D).sum(),len(df)))
print("intersecao ger1 x ①  : total=%d"%df.intersec_ds.sum())
print("x fora dos bounds   : %d"%df.x_fora_bounds.sum())
