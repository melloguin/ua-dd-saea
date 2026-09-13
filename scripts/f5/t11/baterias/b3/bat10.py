import json
import numpy as np, pandas as pd
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
man=json.load(open(B+'.manifest.json')); recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
def deep(o,alvo,niv=0):
    if niv>4: return False
    if isinstance(o,dict):
        if alvo in o: return True
        return any(deep(v,alvo,niv+1) for v in o.values())
    if isinstance(o,list): return any(deep(v,alvo,niv+1) for v in o)
    return False
print('=== contrato_61: minimo comum DI-10 + DI-10 do b3 no (6) ===')
for f in ['fe','f_best','n_front1','tempo_fit_s','tempo_busca_s','modelo_hp','dist_min_arquivo','apd_sel','sigma_sel','n_vetores_vazios','adapt_delta_V']:
    n=sum(1 for r in gens if deep(r,f))
    print('  %-20s presente em %d/%d eventos b3_gen'%(f,n,len(gens)))
print('=== quinto obrigatorio no (5) ===')
for f in ['params','sigma_dict','timing','doe_hash','campanha_id','repo_hash']:
    print('  %-14s'%f, 'PRESENTE' if f in man and man[f] not in (None,'',{}) else 'AUSENTE', str(man.get(f))[:60])
print('  timing.tempo_aval_real_s =',man['timing'].get('tempo_aval_real_s'))
print()
print('=== REGRA 12 / sonda estratificada ===')
sur=pd.read_parquet(B+'__surrogate.parquet')
print('  regimes presentes:',sorted(sur.regime.unique()),' -> b3 NAO e classificador: sem bloco estratificado; so a regua Sobol')
print('  pred_classe/pred_score/pred_confianca todos NULL:',sur.pred_classe.isna().all(),sur.pred_score.isna().all(),sur.pred_confianca.isna().all())
print()
print('=== U6/F5 consolidado (media entre objetivos, como no F5) ===')
d=pd.read_csv('b3_smoke_sonda.csv')
ag=d.groupby('bloco')[['WAPE','cob','corr']].mean()
print(ag.round(4).to_string())
print('  WAPE 1o->ultimo: %.4f -> %.4f (%+.1f%%)'%(ag.WAPE.iloc[0],ag.WAPE.iloc[-1],100*(ag.WAPE.iloc[-1]-ag.WAPE.iloc[0])/ag.WAPE.iloc[0]))
print('  cobertura 2sigma: %.4f -> %.4f ; corr %.4f -> %.4f'%(ag.cob.iloc[0],ag.cob.iloc[-1],ag['corr'].iloc[0],ag['corr'].iloc[-1]))
print('  F5/rodada-42 (MMF1, 6 blocos): WAPE 0,436->0,470 ; corr 0,56->0,59 ; cob 0,76->0,90')
