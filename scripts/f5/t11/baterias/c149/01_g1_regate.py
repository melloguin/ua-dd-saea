"""T11/c149 — re-execucao INDEPENDENTE do gate G-1 (3x1) nas 30 celulas da s42.
READ-ONLY. Escreve so em f5/t11/baterias/c149/."""
import sys, os, glob, csv
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/scripts')
import gates_proveniencia as G

RAIZ='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c149'
out=[]
for lab in sorted(os.listdir(RAIZ)):
    d=os.path.join(RAIZ,lab,'42')
    if not os.path.isdir(d): continue
    t3=glob.glob(d+'/*__surrogate.parquet'); t1=glob.glob(d+'/*__real.parquet')
    if not t3 or not t1: out.append((lab,'SEM-ARQ','')); continue
    ok,det=G.gate_3x1(t3[0],t1[0])
    out.append((lab,{True:'OK',False:'RUIM',None:'n/a'}[ok],det))
    print(f"{lab:16s} {out[-1][1]:5s} {det}")
with open('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c149/g1_regate_c149.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['label','veredito','detalhe']); w.writerows(out)
from collections import Counter
print("\nPLACAR:",Counter(r[1] for r in out))
