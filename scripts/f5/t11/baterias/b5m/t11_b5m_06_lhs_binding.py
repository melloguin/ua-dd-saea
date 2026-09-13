"""A3 (binding do dataset por `dataset_path` do HEADER) e A17 (LHS estratificado
contra os BOUNDS REAIS de src/problems.py) — re-medicao correta."""
import os, json, glob, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import standalone_harness as SH
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b5m"
DATA="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data"
rows=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    man=[p for p in glob.glob(d+"/*.manifest.json") if "__final" not in p]
    if not man: continue
    base=man[0][:-len(".manifest.json")]; m=json.load(open(man[0]))
    hdr=[json.loads(l) for l in open(base+".jsonl")][0]
    sg=pq.read_table(base+"__surrogate.parquet").to_pandas()
    bu=sg[sg.regime=="offline"]
    xs=[c for c in sg.columns if c.startswith("x")]
    rea=pq.read_table(base+"__real.parquet").to_pandas()
    xl,xu=SH._bounds(m["problema"])
    # dataset apontado pelo HEADER (dataset_path pode ser de outra maquina -> refaz por basename)
    dp=hdr.get("dataset_path"); dD=np.nan
    for c in ([dp] if dp and os.path.exists(dp) else []) + \
             glob.glob(os.path.join(DATA,"datasets",m["problema"],os.path.basename(dp or ""))):
        try:
            T=pq.read_table(c).to_pandas(); tx=[q for q in T.columns if q.startswith("x")][:len(xs)]
            if len(T)==len(rea):
                dD=float(np.abs(T[tx].values.astype(np.float32)-rea[xs].values.astype(np.float32)).max()); break
        except Exception: pass
    g1=bu[bu.geracao==1][xs].values.astype(np.float64); pop=g1.shape[0]
    u=(g1-xl)/(xu-xl)
    estrat=int(sum(1 for j in range(g1.shape[1])
                   if np.array_equal(np.sort(np.floor(np.clip(u[:,j],0,1-1e-12)*pop).astype(int)),np.arange(pop))))
    fora=int(((bu[xs].values<xl-1e-5)|(bu[xs].values>xu+1e-5)).sum())
    rows.append(dict(label=lab,problema=m["problema"],D=len(xs),pop=pop,
                     dataset_basename=os.path.basename(dp or ""),dataset_dX=dD,
                     lhs_estrat=estrat,fora_bounds=fora,linhas_busca=len(bu)))
df=pd.DataFrame(rows); df.to_csv(os.path.join(OUT,"t11_b5m_lhs_binding.csv"),index=False)
print("celulas:",len(df))
print("dataset ① max|ΔX| == 0,0 :",int((df.dataset_dX==0).sum()),"/",len(df)," (NaN=%d, max=%.3g)"%(df.dataset_dX.isna().sum(),np.nanmax(df.dataset_dX)))
print("LHS D/D dimensoes estratificadas:",int((df.lhs_estrat==df.D).sum()),"/",len(df))
print("x fora de [xl,xu] :",int(df.fora_bounds.sum()),"de",int(df.linhas_busca.sum()),"linhas de busca")
print(df[df.lhs_estrat!=df.D][["label","D","pop","lhs_estrat","dataset_dX"]].to_string(index=False))
