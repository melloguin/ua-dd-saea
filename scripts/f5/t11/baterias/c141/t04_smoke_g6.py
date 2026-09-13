"""Smoke T11 (MMF1) + par G-6 (com/sem sonda) — instrumentacao NOVA e nao-perturbacao."""
import json, hashlib, numpy as np, pandas as pd
from collections import Counter
B={'s42':'/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141/MMF1/42/exp_main_c141_MMF1_42',
   'smoke':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42',
   'g6_com':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/c141/exp_main_c141_MMF1_42',
   'g6_sem':'/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/c141/exp_main_c141_MMF1_42'}
print('=== A. sha256 POR CAMADA (arquivo inteiro) ===')
lay=['__real.parquet','__pop.parquet','__surrogate.parquet','__timing.parquet','.jsonl']
print('%-8s %s'%('run',' '.join('%-18s'%l.replace('__','').replace('.parquet','').replace('.','') for l in lay)))
H={}
for t,b in B.items():
    hs=[hashlib.sha256(open(b+l,'rb').read()).hexdigest()[:16] for l in lay]
    H[t]=hs; print('%-8s %s'%(t,' '.join('%-18s'%h for h in hs)))
print()
print('①(real) g6_com == g6_sem :', H['g6_com'][0]==H['g6_sem'][0], '->', H['g6_com'][0])
print('②(pop)  g6_com == g6_sem :', H['g6_com'][1]==H['g6_sem'][1])
print('④(tim)  g6_com == g6_sem :', H['g6_com'][3]==H['g6_sem'][3])
print('③(sur)  g6_com == g6_sem :', H['g6_com'][2]==H['g6_sem'][2], '(esperado FALSE: o SEM nao tem bloco de sonda)')
print('①(real) smoke == g6_com  :', H['smoke'][0]==H['g6_com'][0])
print('①(real) s42   == smoke   :', H['s42'][0]==H['smoke'][0])
print()
print('=== B. os TRES sinais do desarme (G-6) ===')
for t in ['g6_com','g6_sem']:
    m=json.load(open(B[t]+'.manifest.json')); s=m['sonda']
    sur=pd.read_parquet(B[t]+'__surrogate.parquet')
    ev=[json.loads(l) for l in open(B[t]+'.jsonl') if l.strip()]
    c=Counter(e.get('rec') for e in ev)
    print('%-7s desligada=%-5s n_blocos=%-2d n_linhas=%-6d ③ total=%-6d online=%-4d sonda=%-6d | eventos sonda no ⑥=%d | fe_final=%d n_ger=%d'%(
        t,s.get('desligada'),s['n_blocos'],s['n_linhas'],len(sur),int((sur.regime=='online').sum()),
        int((sur.regime=='sonda').sum()),c.get('sonda',0),m['fe_final'],m['n_geracoes']))
print()
print('=== C. campos NOVOS: s42 x smoke ===')
ms=json.load(open(B['s42']+'.manifest.json')); mk=json.load(open(B['smoke']+'.manifest.json'))
for k in ['schema_version','campanha_id','repo_hash','algo_version']:
    print(' %-16s s42=%-24r smoke=%r'%(k,ms.get(k,'<AUSENTE>'),mk.get(k,'<AUSENTE>')))
for k in ['tempo_aval_real_s','tempo_fit_surrogate_s','tempo_busca_s','tempo_pred_sonda_s','tempo_total_s']:
    print(' timing.%-22s s42=%-12.6g smoke=%.6g'%(k,ms['timing'].get(k,float('nan')),mk['timing'].get(k,float('nan'))))
print(' sonda.desligada     s42=%r  smoke=%r'%(ms['sonda'].get('desligada','<AUSENTE>'),mk['sonda'].get('desligada','<AUSENTE>')))
print(' params              s42=%r'%ms.get('params'))
print(' params              smk=%r'%mk.get('params'))
print(' REGRA_DO_ROTULO     s42=%s smoke=%s  (c141 nao e classificador)'%('REGRA_DO_ROTULO' in ms,'REGRA_DO_ROTULO' in mk))
for t in ['s42','smoke']:
    sur=pd.read_parquet(B[t]+'__surrogate.parquet')
    print(' %-5s regimes na ③: %s'%(t,sur.regime.value_counts().to_dict()))
print()
print('=== D. ⑥ do smoke: eventos, guards, telemetria DI-10 ===')
ev=[json.loads(l) for l in open(B['smoke']+'.jsonl') if l.strip()]
print(' rec:',dict(Counter(e.get('rec') for e in ev)))
gen=[e for e in ev if e['rec']=='c141_gen']
print(' campos DI-10 completos em %d/%d ciclos'%(sum(1 for g in gen if all(k in g for k in
     ['n_por_nivel','modelo_hp','U_pool_max','dist_min_arquivo','f_best','fit1','fit2','fit3','Q','U','ramo_QU','motivo','nivel'])),len(gen)))
print(' niveis:',dict(Counter(g['nivel'] for g in gen)),' lotes:',dict(sorted(Counter(g['lote'] for g in gen).items())))
print(' modelo_hp:',{k:v for k,v in gen[0]['modelo_hp'].items() if k!='n'},' n:',[g['modelo_hp']['n'] for g in gen])
print(' guards:',dict(Counter(e.get('name') for e in ev if e.get('rec')=='guard')))
print(' header:',json.dumps([e for e in ev if e['rec']=='header'][0],ensure_ascii=False))
print(' footer:',json.dumps([e for e in ev if e['rec']=='footer'][0],ensure_ascii=False))
print(' geracoes de sonda:',[e.get('geracao') for e in ev if e.get('rec')=='sonda'],' motivos:',[e.get('motivo') for e in ev if e.get('rec')=='sonda'])
