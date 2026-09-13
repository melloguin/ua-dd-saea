"""O smoke T11 preserva o MECANISMO? joia + criterio + invariantes, na MMF1."""
import json, numpy as np, pandas as pd
P='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
L=[json.loads(l) for l in open(P+'.jsonl') if l.strip()]
gens=[x for x in L if x.get('rec')=='b3_gen']; M=2
s3=pd.read_parquet(P+'__surrogate.parquet'); on=s3[s3.regime=='online']
sig=[f'sigma_{j}' for j in range(M)]
nok=0;ntot=0;mx=0;errc=0
for g in gens:
    blk=on[on.geracao==g['geracao']]; k=g['pop_por_w'][-1]; last=blk.iloc[-k:]
    S=last[sig].to_numpy(float)
    ss=g['sigma_sel']; sq=np.array(ss['sqrtmse_por_objetivo'],float)
    if sq.ndim==1: sq=sq.reshape(len(g['index']),-1)
    cm=np.array(ss['criterio_meanMSE'],float)
    errc=max(errc,float(np.max(np.abs((sq**2).mean(1)-cm)/np.abs(cm))))
    for i,idx in enumerate(g['index']):
        ntot+=1; rel=np.max(np.abs(S[int(idx)-1]-sq[i])/np.maximum(np.abs(sq[i]),1e-12))
        mx=max(mx,rel); nok+= rel<1e-5
print(f'joia smoke: {nok}/{ntot} max_rel={mx:.3g}')
print(f'criterio_meanMSE == media das variancias: err_rel_max={errc:.3g}')
print('ramo==(Flag<=delta):',all(g['ramo']==('APD' if g['Flag']<=g['delta'] else 'incerteza') for g in gens))
print('Flag==NumV2-NumV1 :',all(g['Flag']==g['NumV2']-g['NumV1'] for g in gens))
print('wmax=20 / u=5 / nzero=0 / n_treino=21:',
      all(len(g['pop_por_w'])==20 for g in gens),
      all(g['u_efetivo']==5 for g in gens),
      sum(g['nzero_updata'] for g in gens),
      all(g['n_treino']==21 and g['arquivo']==21 for g in gens))
tim=pd.read_parquet(P+'__timing.parquet')
print('④ linhas',len(tim),'violacoes fit+busca>ger:',int(((tim.tempo_fit_s+tim.tempo_busca_s)>tim.tempo_geracao_s).sum()))
m=json.load(open(P+'.manifest.json'))
print('I-3 tempo_aval_real_s =',m['timing']['tempo_aval_real_s'],'(nao-nulo:',m['timing']['tempo_aval_real_s']>0,')')
print('campos NOVOS no ⑥ do smoke ausentes na s42:',
      sorted(set(gens[0].keys())-set(json.loads([l for l in open('/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42/exp_main_b3_MMF1_42.jsonl')][2]).keys())))
print('regimes na ③ do smoke:',s3.regime.value_counts().to_dict())
