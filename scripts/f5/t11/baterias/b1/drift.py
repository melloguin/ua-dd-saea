import json, numpy as np, pandas as pd
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1'
S4='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42'
f='exp_main_b1_MMF1_42'
def gens(p): return [json.loads(l) for l in open(p) if json.loads(l).get('rec')=='b1_gen']
ga,gb=gens(f'{SM}/{f}.jsonl'),gens(f'{S4}/{f}.jsonl')
print('--- drift relativo por geracao (smoke x s42), campos escalares ---')
fields=['gbest','mu_best','sigma_best','ei_best','dist_min_arquivo','theta_media','theta_min','theta_max']
rows=[]
for i in range(45):
    r={'g':i+1}
    for k in fields:
        x,y=ga[i][k],gb[i][k]
        r[k]=abs(x-y)/max(abs(y),1e-300)
    rows.append(r)
d=pd.DataFrame(rows)
print('max drift relativo nas 45 primeiras geracoes:')
print(d[fields].max().to_string())
print('\nprimeira geracao com drift>0 por campo:')
for k in fields:
    nz=d.index[d[k]>0]
    print(' %-18s g=%s' % (k, (nz[0]+1) if len(nz) else 'nunca'))
print('\ndrift de ei_best por geracao (g1..g46):')
print(' '.join('%d:%.1e'%(i+1,abs(ga[i]['ei_best']-gb[i]['ei_best'])/max(abs(gb[i]['ei_best']),1e-300)) for i in range(46)))
# norm_min/max e lambda
nl=sum(1 for i in range(48) if json.dumps(ga[i]['lambda'])!=json.dumps(gb[i]['lambda']))
print('\ngeracoes com lambda diferente (de 48):',nl)
nb=sum(1 for i in range(48) if ga[i]['best_sid']!=gb[i]['best_sid'])
print('geracoes com best_sid diferente (de 48):',nb, [i+1 for i in range(48) if ga[i]['best_sid']!=gb[i]['best_sid']])
# timing manifest
for t,p in [('SMOKE',SM),('S42',S4)]:
    m=json.load(open(f'{p}/{f}.manifest.json'))
    print(t,'timing keys=',sorted(m['timing'].keys()),' tempo_aval_real_s=',m['timing'].get('tempo_aval_real_s'))
    print(t,'params keys=',sorted(m.get('params',{}).keys()))
# schemas parquet
for suf in ['__real','__pop','__surrogate','__timing']:
    a=pd.read_parquet(f'{SM}/{f}{suf}.parquet'); b=pd.read_parquet(f'{S4}/{f}{suf}.parquet')
    ca,cb=list(a.columns),list(b.columns)
    print(suf,'smoke cols=',len(ca),'s42 cols=',len(cb),'novas=',[c for c in ca if c not in cb],'sumidas=',[c for c in cb if c not in ca])
