import json, sys, os
from collections import Counter, defaultdict

def load(jl):
    recs=[]
    with open(jl) as f:
        for i,l in enumerate(f):
            l=l.strip()
            if not l: continue
            try: recs.append(json.loads(l))
            except Exception as e: print("BAD LINE",i,e)
    return recs

SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42.jsonl'
S42='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42.jsonl'
for tag,p in [('SMOKE',SM),('S42',S42)]:
    r=load(p)
    print('='*20,tag,len(r),'linhas')
    c=Counter(x.get('rec') for x in r)
    print('rec:',dict(c))
    for k in c:
        ex=[x for x in r if x.get('rec')==k]
        keys=sorted(set().union(*[set(x.keys()) for x in ex]))
        print('  ',k,'n=%d'%len(ex),'keys=',keys)
