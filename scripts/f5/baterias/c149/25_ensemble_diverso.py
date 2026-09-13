"""K=10 redes REALMENTE distintas? val_mse por rede no ⑥ (10 valores/iteracao).
Se as ativacoes/seeds fossem iguais, as redes coincidiriam. Mede: nº de val_mse distintos por iteracao,
ranking medio por indice de rede (assinatura das ativacoes), e dispersao."""
import json,os,numpy as np,pandas as pd
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149"
OUT="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c149"
ATIV=["tanh","ReLU","CELU","LeakyReLU","ELU","Hardswish","tanh","ReLU","CELU","LeakyReLU"]
rows=[];RK=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,"42")
    if not os.path.isdir(d): continue
    exp="batch" if lab.startswith("q10_") else "main"; prob=lab[4:] if lab.startswith("q10_") else lab
    p=os.path.join(d,f"exp_{exp}_c149_{prob}_42")
    V=np.array([json.loads(l)["val_mse"] for l in open(p+".jsonl") if '"rec": "fit"' in l])
    nd=np.array([len(set(v)) for v in V])
    rk=pd.DataFrame(V).rank(axis=1).mean(0).values
    RK.append(rk)
    rows.append(dict(exp=exp,prob=prob,n_iter=len(V),
        distintos_min=int(nd.min()),distintos_med=float(nd.mean()),
        cv_intra=float(np.median(V.std(1)/np.maximum(V.mean(1),1e-12))),
        val_mse_med=float(np.median(V)),val_mse_med_ini=float(np.median(V[0])),val_mse_med_fim=float(np.median(V[-1]))))
df=pd.DataFrame(rows); df.to_csv(OUT+"/ensemble_c149.csv",index=False)
print(df.to_string(index=False))
print("\nval_mse com 10 valores DISTINTOS em 100%% das iteracoes:", bool((df.distintos_min==10).all()),
      "| min de distintos:",int(df.distintos_min.min()))
print("CV intra-ensemble mediano: %.3f (dispersao ENTRE redes = a fonte da incerteza epistemica)"%df.cv_intra.median())
R=np.array(RK).mean(0)
print("\nrank medio do val_mse por indice de rede (0..9) e ativacao da RAIZ:")
for i,(a,r) in enumerate(zip(ATIV,R)): print(f"  net {i} {a:11s} rank medio {r:.2f}")
print("desvio dos ranks: %.3f (>0 => as redes NAO sao permutaveis: as ativacoes diferenciam)"%R.std())
