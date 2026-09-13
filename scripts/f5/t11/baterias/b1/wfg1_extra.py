import json,numpy as np,pandas as pd
P='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/WFG1/42'
base=f'{P}/exp_main_b1_WFG1_42'
man=json.load(open(base+'.manifest.json'))
evs=[]
for l in open(base+'.jsonl'):
    try: evs.append(json.loads(l))
    except Exception: pass
ge=[e for e in evs if e['rec']=='b1_gen']; gu=[e for e in evs if e['rec']=='guard']; so=[e for e in evs if e['rec']=='sonda']
real=pd.read_parquet(base+'__real.parquet').sort_values('fe_index').reset_index(drop=True)
SID=real.solution_id.values
mis=[e['geracao'] for e in ge if e['best_sid']!=SID[e['fe']-1]]
cache=[e['geracao'] for e in ge if e.get('dist_min_arquivo')==0]
print('F2 mismatches:',mis,' iteracoes cache (dist_min=0):',cache,' iguais:',mis==cache)
from collections import Counter
print('guards:',Counter(g['name'] for g in gu))
c0=[g for g in gu if g['name']=='cache_hit' and g.get('fe')==1]; print('N1 c0 (cache_hit com fe=1):',len(c0))
print('cache_hits manifesto:',man['cache_hits'])
n_iter=443; esperado={1}|{g for g in range(2,n_iter+1) if g%2==0}|{n_iter}
print('U4 cadencia: |esperado|=%d  |manifesto.sonda.geracoes|=%d  identicos=%s'%(len(esperado),len(man['sonda']['geracoes']),set(man['sonda']['geracoes'])==esperado))
print('   motivos dos eventos de sonda sobreviventes:',Counter(s.get('motivo') for s in so),' (G=443 impar)')
print('   ultima geracao sondada:',max(man['sonda']['geracoes']))
tim=pd.read_parquet(base+'__timing.parquet')
viol=set(tim.loc[tim.tempo_fit_s+tim.tempo_busca_s+tim.tempo_pred_sonda_s.fillna(0)>tim.tempo_geracao_s,'geracao'].astype(int))
gs=set(man['sonda']['geracoes'])
print('U7 2a perna: violacoes=%d  subset das gers de sonda=%s  falta=%s'%(len(viol),viol<=gs,sorted(gs-viol)[:5]))
print('ledger: n_iter=%d  n_infill=%d  cache=%d  c0=%d  =>%d'%(n_iter,681-241,man['cache_hits'],len(c0),(681-241)+man['cache_hits']-len(c0)))
