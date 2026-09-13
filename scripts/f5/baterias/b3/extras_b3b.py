import pandas as pd, numpy as np, json, os
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=F5+'/baterias/b3'
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
sd=pd.read_csv(F5+'/sonda_f52e.csv'); s3=sd[(sd.exp=='main')&(sd.alg=='b3')]
print('blocos DTLZ2:',sorted(s3[s3.problema=='DTLZ2'].bloco.unique()))
print('cols',s3.columns.tolist())
w=s3[(s3.problema=='DTLZ2')].pivot_table(index='bloco',columns='obj',values='wape')
print(w.round(4).to_string())
rows=[]
for pr in sorted(os.listdir(ROOT)):
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]; D,M=hdr['D'],hdr['M']
    gens=[x for x in recs if x['rec']=='b3_gen']; guards=[x for x in recs if x['rec']=='guard']
    xc=[f'x{j}' for j in range(D)]
    r=pd.read_parquet(b+'__real.parquet'); RX=r[xc].to_numpy().astype(np.float64)
    s=pd.read_parquet(b+'__surrogate.parquet'); on=s[s.regime=='online'].reset_index(drop=True)
    ini=11*D-1; fes=np.array([g['fe'] for g in gens]); dif=np.diff(np.concatenate([[ini],fes]))
    ch=[x['fe'] for x in guards if x['name']=='cache_hit']
    c0=sum(1 for f in ch if f==1); ch_opt=sum(1 for f in ch if f>1 and f<=fes[-1])
    d=dict(problema=pr,c0=c0,ident_ok=bool(5*len(gens)-dif.sum()==ch_opt),gap=int(5*len(gens)-dif.sum()),ch_opt=ch_opt,
           ch_pos_ultciclo=sum(1 for f in ch if f>fes[-1]))
    # dist_min_arquivo >= min sobre a (1) inteira pre-ciclo?
    ge_=0; tot=0; eq=0
    for g in gens:
        fe0=g['fe']-5; blk=on[on.geracao==g['geracao']]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True); idx=[i-1 for i in g['index']]
        SX=last.iloc[idx][xc].to_numpy().astype(np.float64); A=RX[:fe0]
        if len(A)==0: continue
        dd=np.sqrt(((SX[:,None,:]-A[None,:,:])**2).sum(-1)).min(1)
        lg=np.array(g['dist_min_arquivo'])
        ge_+= int((lg>=dd-1e-9).all()); eq+=int(np.allclose(lg,dd,rtol=1e-5,atol=1e-9)); tot+=1
    d['dmin_ge']=ge_; d['dmin_eq']=eq; d['dmin_n']=tot
    # streaks do ramo
    ramo=[g['ramo'] for g in gens]
    st=1; best=1; cur=ramo[0]
    for x in ramo[1:]:
        if x==cur: st+=1; best=max(best,st)
        else: cur=x; st=1
    tail=1
    for i in range(len(ramo)-2,-1,-1):
        if ramo[i]==ramo[-1]: tail+=1
        else: break
    d['streak_max']=best; d['ramo_final']=ramo[-1]; d['streak_final']=tail; d['n']=len(ramo)
    rows.append(d)
E=pd.DataFrame(rows); E.to_csv(OUT+'/b3_extras2.csv',index=False)
pd.set_option('display.width',300); print(); print(E.to_string())
print('\nc0==1 (fe==1):',(E.c0==1).sum(),'/25 | identidade do ledger fecha:',E.ident_ok.sum(),'/25')
print('dist_min_arquivo >= min sobre (1):',E.dmin_ge.sum(),'/',E.dmin_n.sum(),'| igual:',E.dmin_eq.sum())
