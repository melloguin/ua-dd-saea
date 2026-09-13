"""Bateria 8 — assinatura indireta do nicho por vetor de referencia (spacing) + contrato/⑤. READ-ONLY."""
import json,os,numpy as np,pandas as pd
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
RES='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
m=pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
mm=m[(m.exp=='main')&m.alg.isin(['nsga2','nsga3','moead','smsemoa'])]
sp=mm.pivot_table(index='problema',columns='alg',values='spacing')
rk=sp.rank(axis=1)
print('=== spacing: rank medio entre os 4 pisos (1=mais uniforme) ===')
print(rk.mean().round(2).to_dict())
print('nsga3 melhor spacing em',int((rk['nsga3']==1).sum()),'/',len(rk),'problemas')
M3=['DTLZ1','DTLZ2','DTLZ3','DTLZ4','DTLZ7','MMF16_20']
print('  M=3:',int((rk.loc[M3,'nsga3']==1).sum()),'/6 | rank medio M=3',round(rk.loc[M3,'nsga3'].mean(),2),
      '| M=2 rank medio',round(rk.drop(M3)['nsga3'].mean(),2))
sp.to_csv('spacing_pisos.csv'); rk.to_csv('spacing_ranks.csv')
# nsga3 x nsga2 par-a-par (mesmo motor, selecao diferente) em IGD+
ig=mm.pivot_table(index='problema',columns='alg',values='igd_plus')
print('\nnsga3 melhor que nsga2 (IGD+):',int((ig.nsga3<ig.nsga2).sum()),'/',len(ig),
      '| em M=3:',int((ig.loc[M3,'nsga3']<ig.loc[M3,'nsga2']).sum()),'/6')
print('nsga3 melhor que smsemoa:',int((ig.nsga3<ig.smsemoa).sum()),'/',len(ig),
      '| que moead:',int((ig.nsga3<ig.moead).sum()),'/',len(ig))
# --- contrato ⑤ / header
rows=[]
for prob in sorted(os.listdir(f'{RES}/nsga3')):
    d=f'{RES}/nsga3/{prob}/42'
    if not os.path.isdir(d): continue
    b=f'{d}/exp_main_nsga3_{prob}_42'
    man=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]
    rows.append(dict(prob=prob,tem_params=('params' in man),tem_sigma=('sigma_dict' in man),
        tem_run_id=('run_id' in man),tem_env=('env' in man),tem_timing=('timing' in man),
        n_chaves_params=len(man['params']),fit_series=len(man['fit_series']),
        fallback=man['fallback_ativado'],n_retries=man['n_retries'],
        stack=man['env'].get('stack'),matlab=man['env'].get('matlab'),
        algo_version=man['algo_version'],repo_hash=man['repo_hash'],
        hdr_piso=hdr['piso'],hdr_surr=hdr['surrogate'],hdr_ops=hdr['operadores'],
        sonda=man['sonda']['status'],n_blocos=man['sonda']['n_blocos'],
        motivo_parada=man.get('motivo_parada','<ausente>')))
C=pd.DataFrame(rows); C.to_csv('contrato_manifesto.csv',index=False)
print('\n=== contrato do ⑤ ===')
for c in ['tem_params','tem_sigma','tem_run_id','tem_env','tem_timing','fit_series','fallback','n_retries','sonda','n_blocos','stack','matlab','algo_version','repo_hash','hdr_piso','hdr_surr','motivo_parada','n_chaves_params']:
    print(f'  {c:18s}', dict(C[c].value_counts()))
print('  operadores (unico):',C.hdr_ops.unique())
