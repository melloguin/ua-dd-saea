import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    ev=[json.loads(l) for l in open(base+".jsonl")]
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G)
    diff=np.array([g['RatioOld']-g['Ratio'] for g in G])
    r=dict(problema=p,C=C,
        inc_nosso=int((diff>=0.05).sum()),                 # nosso: conv <=> diff<0.05
        inc_paper=int((diff>0.08).sum()),                  # paper: inc <=> diff>0.08
        inc_paper_delta005=int((diff>0.05).sum()),
        inc_delta008_estrito_lt=int((diff>=0.08).sum()),
        diff_med=float(np.median(diff)),diff_min=float(diff.min()),diff_max=float(diff.max()),
        n_diff_igual_005=int((np.abs(diff-0.05)<1e-12).sum()),
        ratio_med=float(np.median([g['Ratio'] for g in G])),
        ratio_old_c1=G[0]['RatioOld'])
    r['frac_inc_nosso']=r['inc_nosso']/C; r['frac_inc_paper']=r['inc_paper']/C
    out.append(r)
df=pd.DataFrame(out); df.to_csv("contrafactual_delta_e7.csv",index=False)
pd.set_option('display.width',260); print(df.round(4).to_string())
print("\nTOT ciclos:",df.C.sum())
print("ramo INCERTEZA — nosso (delta=0,05, conv<=>diff<0,05):",df.inc_nosso.sum(),
      f"({100*df.inc_nosso.sum()/df.C.sum():.1f}%)")
print("ramo INCERTEZA — regra do PAPER (diff>0,08):",df.inc_paper.sum(),
      f"({100*df.inc_paper.sum()/df.C.sum():.1f}%)  => delta do paper reduziria a exploracao em "
      f"{100*(1-df.inc_paper.sum()/df.inc_nosso.sum()):.1f}%")
print("so o limiar (0,05 com '>' estrito):",df.inc_paper_delta005.sum(),"| empates exatos diff==0,05:",df.n_diff_igual_005.sum())
print("celulas com 0 ciclos de incerteza:",int((df.inc_nosso==0).sum()),"| min frac:",round(df.frac_inc_nosso.min(),4),"max:",round(df.frac_inc_nosso.max(),4))
