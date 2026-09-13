import json
import numpy as np, pandas as pd
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
recs=[json.loads(l) for l in open(B+'.jsonl')]; gens=[r for r in recs if r['rec']=='b3_gen']
sur=pd.read_parquet(B+'__surrogate.parquet'); on=sur[sur.regime=='online']
print('=== CONTROLE da query-joia F1 (a identidade DISCRIMINA?) ===')
def erro(modo):
    mx=0
    for r in gens:
        blk=on[on.geracao==r['geracao']]; ppw=r['pop_por_w']
        if modo=='ultima': sub=blk.iloc[-ppw[-1]:]
        elif modo=='primeira': sub=blk.iloc[:ppw[0]]
        elif modo=='penultima': sub=blk.iloc[-(ppw[-1]+ppw[-2]):-ppw[-1]]
        elif modo=='inteira': sub=blk
        for k,idx in enumerate(r['index']):
            j = idx-1 if modo!='0based' else idx
            if modo=='0based': sub=blk.iloc[-ppw[-1]:]
            if j>=len(sub): return float('inf')
            row=sub.iloc[j]
            got=np.array([row.sigma_0,row.sigma_1]); exp=np.array(r['sigma_sel']['sqrtmse_por_objetivo'][k])
            mx=max(mx,(np.abs(got-exp)/np.maximum(np.abs(exp),1e-300)).max())
    return mx
for m in ['ultima','primeira','penultima','inteira','0based']:
    print('  %-11s max erro relativo = %.3e'%(m,erro(m)))
print()
print('=== U7 segunda perna (invariante do relogio) ===')
tim=pd.read_parquet(B+'__timing.parquet')
man=json.load(open(B+'.manifest.json'))
v=(tim.tempo_fit_s+tim.tempo_busca_s+tim.tempo_pred_sonda_s>tim.tempo_geracao_s)
print('  geracoes com fit+busca+sonda > tempo_geracao:',sorted(tim.geracao[v].tolist()))
print('  geracoes de sonda (manifesto)              :',man['sonda']['geracoes'])
print('  set-equality:',sorted(tim.geracao[v].tolist())==man['sonda']['geracoes'])
print('  tempo_pred_sonda_s por geracao:',[round(x,5) for x in tim.tempo_pred_sonda_s.tolist()])
print()
print('=== FICHA final consolidada ===')
sb=sur[sur.regime=='sonda']
print('  linhas (3) total %d = online %d + sonda %d'%(len(sur),len(on),len(sb)))
print('  ciclos %d | selecoes %d | blocos de sonda %d x %d pts'%(len(gens),5*len(gens),sb.geracao.nunique(),2000))
print('  geracoes internas do RVEA reconciliadas: %d'%(sum(len(r['pop_por_w']) for r in gens)))
print('  wall total %.3f s'%man['timing']['tempo_total_s'])
