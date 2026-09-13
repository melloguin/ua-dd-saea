import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    man=json.load(open(base+".manifest.json")); ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']
    G=[e for e in ev if e['rec']=='e7_gen']; SD=[e for e in ev if e['rec']=='sonda']
    GU=[e for e in ev if e['rec']=='guard']; C=len(G)
    hs=any(e['name']=='hard_stop' for e in GU)
    Gstart=C+(1 if hs else 0)
    esp=set([1])|set(g for g in range(2,Gstart+1) if g%2==0)|set([Gstart])
    obs=set(e['geracao'] for e in SD)
    out.append(dict(problema=p,D=D,C=C,hard_stop=hs,Gstart=Gstart,Gstart_impar=(Gstart%2==1),
        n_blocos=len(SD),esperado=len(esp),cad_ok=(obs==esp),
        finalprobe_usado=(Gstart%2==1),falta=sorted(esp-obs),extra=sorted(obs-esp),
        overshoot=(3-(20*D)%3)%3, infills_ciclo_abortado=(20*D)-3*C))
df=pd.DataFrame(out); df.to_csv("cadencia_e7.csv",index=False)
pd.set_option('display.width',250)
print(df.to_string())
print("\ncad_ok:",df.cad_ok.sum(),"/",len(df),"| finalProbe (Gstart impar):",df.finalprobe_usado.sum(),
      "| soma blocos",df.n_blocos.sum(),"| infills em ciclo abortado:",df.infills_ciclo_abortado.sum())
