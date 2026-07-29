import json, os, glob
import pandas as pd, numpy as np

ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs=sorted(os.listdir(ROOT))
probs=[p for p in probs if not p.startswith('_') and not p.startswith('.')]
rows=[]
for p in probs:
    d=f'{ROOT}/{p}/42'
    man=json.load(open(f'{d}/exp_main_b1_{p}_42.manifest.json'))
    r={'problema':p}
    for k in ['status','fe_final','maxfe','n_geracoes','cache_hits','doe_hash','termino','motivo_parada','fallback_ativado','n_retries']:
        r[k]=man.get(k)
    par=man.get('params',{})
    r['params_keys']=';'.join(sorted(par.keys()))
    for k,v in par.items():
        r['p_'+k]=json.dumps(v) if isinstance(v,(dict,list)) else v
    s=man.get('sonda',{})
    r['sonda_keys']=';'.join(sorted(s.keys()))
    for k in ['S','k','n_blocos','n_linhas','n_falhas','artefato']:
        r['sonda_'+k]=s.get(k)
    r['sonda_geracoes_n']=len(s.get('geracoes',[]) or [])
    r['sonda_g_last']=(s.get('geracoes') or [None])[-1]
    r['fit_series_n']=len(man.get('fit_series',[]) or [])
    r['sigma_dict_keys']=';'.join(sorted((man.get('sigma_dict') or {}).keys()))
    tm=man.get('timing',{})
    r['tempo_total_s']=tm.get('tempo_total_s') if isinstance(tm,dict) else None
    r['manifest_top_keys']=';'.join(sorted(man.keys()))
    rows.append(r)
df=pd.DataFrame(rows)
df.to_csv(f'{OUT}/meta_celulas.csv',index=False)
print(df[['problema','status','fe_final','maxfe','n_geracoes','cache_hits','sonda_n_blocos','fit_series_n','tempo_total_s']].to_string())
print('\nPARAMS KEYS:', df.params_keys.unique())
print('\nSONDA KEYS:', df.sonda_keys.unique())
print('\nSIGMA KEYS:', df.sigma_dict_keys.unique())
print('\nTOP:', df.manifest_top_keys.unique())
