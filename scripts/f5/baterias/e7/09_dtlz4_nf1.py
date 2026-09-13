import json
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
base=f"{ROOT}/DTLZ4/42/exp_main_e7_DTLZ4_42"
ev=[json.loads(l) for l in open(base+".jsonl")]
G=[e for e in ev if e['rec']=='e7_gen']; D=12; M=3; n0=131
real=pd.read_parquet(base+"__real.parquet")
F=real[[f"f{i}" for i in range(M)]].to_numpy(np.float64)
print("F[:8]:\n",F[:8])
print("linhas com f1==0 e f2==0:",int(((F[:,1]==0)&(F[:,2]==0)).sum()),"de",len(F))
print("f1 zeros:",int((F[:,1]==0).sum()),"f2 zeros:",int((F[:,2]==0).sum()))
def ndm(Y,eps=0.0):
    n=len(Y); dom=np.zeros(n,bool)
    for i in range(n):
        le=(Y<=Y[i]+eps).all(axis=1); lt=(Y<Y[i]-eps).any(axis=1)
        if (le&lt).any(): dom[i]=True
    return ~dom
for c in [1,2,40,80]:
    n=min(n0+3*c,len(F)); Y=F[:n]
    m=ndm(Y)
    # PlatEMO NDSort usa float; teste com float32
    m32=ndm(Y.astype(np.float32).astype(np.float64))
    g=[x for x in G if x['geracao']==c][0]
    # hipotese: front1 do arquivo SEM os duplicados exatos colapsados / com tolerancia
    print(f"c={c} n={n} log={g['n_front1']} ND={int(m.sum())} ND32={int(m32.sum())} "
          f"| ND(unique)={int(ndm(np.unique(Y,axis=0)).sum())} | ymin={g['ymin']} f_best={g['f_best']}")
# hipotese: n_front1 do PopObj (mu) do ciclo -> ja testado 0/80. Testar com sigma? ou pop final real?
sur=pd.read_parquet(base+"__surrogate.parquet",columns=['regime','geracao']+[f"mu_{i}" for i in range(M)])
on=sur[sur.regime=='online']
for c in [1,2,80]:
    b=on[on.geracao==c]; MU=b[[f"mu_{i}" for i in range(M)]].to_numpy(np.float64)
    g=[x for x in G if x['geracao']==c][0]
    print(f"c={c} log={g['n_front1']} | ND(pop final mu)={int(ndm(MU[-100:]).sum())} | ND(1900 mu)={int(ndm(MU).sum())}")
