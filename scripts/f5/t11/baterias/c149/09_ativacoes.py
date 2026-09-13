"""T11/c149 — RE-MEDICAO do A12: a convencao da RAIZ das ativacoes recuperada
do padrao de val_mse por indice de rede. s42 (30 celulas) + SMOKE T11."""
import json,os,numpy as np
ATIV=["tanh","ReLU","CELU","LeakyReLU","ELU","Hardswish","tanh","ReLU","CELU","LeakyReLU"]
def ranks(paths):
    acc=np.zeros(10); n=0
    for P in paths:
        for l in open(P):
            r=json.loads(l)
            if r.get('rec')!='fit': continue
            v=np.asarray(r['val_mse'],float)
            if len(v)!=10: continue
            acc+=np.argsort(np.argsort(v))+1; n+=1
    return acc/n, n
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
ps=[]
for lab in sorted(os.listdir(ROOT)):
    d=os.path.join(ROOT,lab,'42')
    if not os.path.isdir(d): continue
    exp='batch' if lab.startswith('q10_') else 'main'; prob=lab[4:] if lab.startswith('q10_') else lab
    ps.append(os.path.join(d,f'exp_{exp}_c149_{prob}_42.jsonl'))
for nome,paths in [('s42 (30 celulas)',ps),
                   ('SMOKE T11 (MMF1/s0)',['/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c149/exp_main_c149_MMF1_0.jsonl'])]:
    r,n=ranks(paths)
    print(f"\n=== {nome} — {n} fits ({n*10} treinos de rede) ===")
    print("  rank medio de val_mse por indice de rede (1=melhor, 10=pior):")
    for i in range(10): print(f"    net{i} {ATIV[i]:11s} {r[i]:5.2f}")
    print("  PARES que a convencao da RAIZ preve (i, i+6):")
    for i in range(4): print(f"    net{i}({ATIV[i]:10s}) {r[i]:5.2f}  <->  net{i+6}({ATIV[i+6]:10s}) {r[i+6]:5.2f}   |Δ|={abs(r[i]-r[i+6]):.3f}")
    print(f"    singletons: net4 ELU {r[4]:.2f} · net5 Hardswish {r[5]:.2f}")
    print(f"  desvio-padrao dos ranks = {r.std():.3f}  (0 = redes permutaveis)")
    print(f"  max|Δ| dentro dos 4 pares = {max(abs(r[i]-r[i+6]) for i in range(4)):.3f}")
