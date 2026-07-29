"""Bateria 7 — dedup D57 na ①, ponto ideal, comparativo de geracoes nsga3 x nsga2 (DI-18). READ-ONLY."""
import json,os
import numpy as np,pandas as pd
RES='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
probs=sorted(p for p in os.listdir(f'{RES}/nsga3') if os.path.isdir(f'{RES}/nsga3/{p}'))
rows=[];ideal_v=[]
for prob in probs:
    b=f'{RES}/nsga3/{prob}/42/exp_main_nsga3_{prob}_42'
    man=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]; D,M=hdr['D'],hdr['M']
    gens=[r for r in recs if r.get('rec')=='nsga3_gen']
    R=pd.read_parquet(b+'__real.parquet'); xc=[f'x{i}' for i in range(D)]
    X=R[xc].values
    uni=np.unique(X,axis=0)
    # cache_hit keys distintas
    ch=[g for g in recs if g.get('rec')=='guard' and g['name']=='cache_hit']
    # ponto ideal
    ide=np.array([g['ideal'] for g in gens],dtype=float)
    dd=np.diff(ide,axis=0)
    for gi,mi in zip(*np.where(dd>1e-12)):
        ideal_v.append(dict(prob=prob,ger=int(gens[gi+1]['geracao']),obj=int(mi),
            antes=float(ide[gi,mi]),depois=float(ide[gi+1,mi]),
            delta=float(dd[gi,mi]),rel=float(dd[gi,mi]/max(abs(ide[gi,mi]),1e-30))))
    # nsga2 comparativo
    b2=f'{RES}/nsga2/{prob}/42/exp_main_nsga2_{prob}_42.manifest.json'
    m2=json.load(open(b2)) if os.path.exists(b2) else None
    rows.append(dict(prob=prob,D=D,M=M,n_real=len(R),x_unicos=len(uni),
        dup_x_na_1=len(R)-len(uni),ch=len(ch),
        ngen3=man['n_geracoes'],Nef3=man['params']['N_efetivo'],
        ngen2=m2['n_geracoes'] if m2 else None,
        Nef2=m2['params'].get('N_efetivo') if m2 else None,
        ch2=m2['cache_hits'] if m2 else None))
T=pd.DataFrame(rows); V=pd.DataFrame(ideal_v)
T.to_csv('dedup_e_geracoes.csv',index=False); V.to_csv('violacoes_ideal.csv',index=False)
pd.set_option('display.width',240)
print(T.to_string(index=False))
print('\nlinhas duplicadas bit-a-bit na ①:',int(T.dup_x_na_1.sum()),'em 25 celulas (total',int(T.n_real.sum()),'linhas)')
print('\n=== violacoes de monotonicidade do ponto ideal ==='); print(V.to_string(index=False) if len(V) else 'nenhuma')
tot=sum((r['ngen3']-1)*r['M'] for r in rows); print('violacoes',len(V),'de',tot,'transicoes-objetivo =',round(100*len(V)/tot,3),'%')
print('\nM=3: geracoes nsga3(N=15) x nsga2(N=20):')
print(T[T.M==3][['prob','D','ngen3','Nef3','ngen2','Nef2']].to_string(index=False))
