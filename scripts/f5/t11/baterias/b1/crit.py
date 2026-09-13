import json,os,numpy as np
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
c={'argmin0':0,'g2_nao_melhora':0,'e0len1':0,'tot':0,'const':0,'argmin0_semWFG1':0,'tot_semWFG1':0}
for prob in sorted(x for x in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{x}')):
    p=f'{ROOT}/{prob}/42'
    if not os.path.isdir(p): continue
    for f in os.listdir(p):
        if not f.endswith('.jsonl'): continue
        for l in open(f'{p}/{f}'):
            try: r=json.loads(l)
            except Exception: continue
            if r.get('rec')!='b1_gen': continue
            e0=np.asarray(r.get('e0_trace') or [],float)
            if not len(e0): continue
            c['tot']+=1
            a0=int(np.argmin(e0))==0
            c['argmin0']+=a0
            c['const']+= (e0.max()==e0.min())
            c['e0len1']+= (len(e0)==1)
            c['g2_nao_melhora']+= (len(e0)>1 and e0[1]>=e0[0]) or len(e0)==1
            if prob!='WFG1':
                c['tot_semWFG1']+=1; c['argmin0_semWFG1']+=a0
print(c)
