"""DEF-A6/D62/D91/D22: seed_nsga2 do ⑥ == iteration_seed(1000*42, alg_id=12, iter, uso=1, bits32) BIT-A-BIT."""
import json,os,sys,numpy as np,pandas as pd
sys.path.insert(0,"/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src.standalone_harness import iteration_seed, seed_base
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
base=seed_base("c149",42); print("seed_base(c149,42) =",base)
rows=[];tot=0;ok=0
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    dec=[json.loads(l) for l in open(p+".jsonl") if '"rec": "decision"' in l]
    n=len(dec); k=0
    for g,dd in enumerate(dec,1):
        k+= dd["seed_nsga2"]==iteration_seed(base,12,g,1,bits32=True)
    rows.append(dict(exp=exp,prob=prob,n=n,ok=k,unicos=len({d_["seed_nsga2"] for d_ in dec}))); tot+=n; ok+=k
df=pd.DataFrame(rows); df.to_csv(OUT+"/seeds_c149.csv",index=False)
print(df.to_string(index=False))
print(f"\nTOTAL: {ok}/{tot} sementes NSGA-II reproduzidas BIT-A-BIT pela formula do harness")
print("uso_id=1 constante; sementes distintas por iteracao em todas as celulas:", bool((df.unicos==df.n).all()))
