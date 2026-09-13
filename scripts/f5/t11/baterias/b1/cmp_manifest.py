import json
P={'SMOKE':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42.manifest.json',
   'G6COM':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b1/exp_main_b1_MMF1_42.manifest.json',
   'G6SEM':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/b1/exp_main_b1_MMF1_42.manifest.json',
   'S42':'/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42.manifest.json'}
ms={k:json.load(open(v)) for k,v in P.items()}
keys=sorted(set().union(*[set(m.keys()) for m in ms.values()]))
for k in keys:
    vals={t:ms[t].get(k,'<AUSENTE>') for t in ms}
    s=str(vals)
    print(('%-26s'%k), s[:600])
