# -*- coding: utf-8 -*-
"""B1 - o efeito do fix DI-45 (ClassifierSelect.m:56-58): PRE (s42) x POS (smoke T11).
READ-ONLY. Uso: python b1_di45.py <corpus> ; corpus in {s42, smoke}
"""
import sys, json, os, glob
import numpy as np, pandas as pd

ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e74'

def cells(corpus):
    if corpus=='s42':
        for d in sorted(glob.glob(f'{ROOT}/resultados_experimentos/e74/*/42')):
            prob=d.split('/')[-2]
            yield prob, f'{d}/exp_main_e74_{prob}_42'
    else:
        for p in ['MMF1','DTLZ2','ZDT1']:
            yield p, f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{p}_42'

def analisa(prob, base):
    real=pd.read_parquet(base+'__real.parquet')
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    sur=pd.read_parquet(base+'__surrogate.parquet',
        columns=['regime','geracao','modelo_flag','pred_classe','sigma_0','real_solution_id']+xc)
    sur=sur[(sur.regime=='online') & (sur.modelo_flag=='PNN(s1)')]
    ev=[json.loads(l) for l in open(base+'.jsonl')]
    ev=[r for r in ev if r.get('rec')=='e74_gen' and r.get('estrategia')==1]
    Xr=real[xc].values.astype(np.float64)
    rows=[]
    for g,blk in sur.groupby('geracao'):
        pass
    blocks={int(g):b for g,b in sur.groupby('geracao')}
    for r in ev:
        g=int(r['geracao']); b=blocks.get(g)
        if b is None: continue
        Xb=b[xc].values.astype(np.float64); s0=b['sigma_0'].values.astype(np.float64)
        cls=(b['pred_classe'].values=='nivel_1')
        n=len(b)
        rec=dict(problema=prob, geracao=g, fe=r['fe'], aceito=r['aceito'],
                 slot_perdido=r['slot_perdido'], n_cand=r['n_cand'], N=n,
                 count=r['count'], frac_n1=r['frac_nivel1'], n_desal=r['n_desalinhado'],
                 flag_copia=r['flag_copia'], cand_dist=r.get('cand_dist_dec'),
                 cand_classe=r.get('cand_classe'),
                 n1_pop=int(cls.sum()), nan_s0=int(np.isnan(s0).sum()))
        if r['aceito']==1:
            fx=Xr[r['fe']-1]
            d=np.abs(Xb-fx).max(axis=1)
            pos=int(np.argmin(d)); rec['match_dx']=float(d[pos]); rec['pos']=pos
            order=np.argsort(-s0, kind='stable')
            rank=int(np.where(order==pos)[0][0])+1
            rec['rank_global']=rank
            rec['is_argmax_global']=int(rank==1)
            S1=np.where(cls)[0]
            if len(S1):
                sub=S1[np.argmax(s0[S1])]
                rec['is_argmax_S']=int(sub==pos)
                rec['pos_in_S']=int(np.where(np.sort(-s0[S1],kind='stable')== -s0[pos])[0][0])+1 if pos in S1 else -1
                rec['chosen_in_S']=int(pos in S1)
                rec['|S1|']=len(S1)
            rec['limiar_pre']=int(pos <= round(r['frac_nivel1']*n)-1)
        rows.append(rec)
    return pd.DataFrame(rows)

if __name__=='__main__':
    corpus=sys.argv[1]
    dfs=[analisa(p,b) for p,b in cells(corpus)]
    df=pd.concat(dfs, ignore_index=True)
    df.to_csv(f'{OUT}/di45_{corpus}.csv', index=False)
    a=df[df.aceito==1]
    print(f'--- {corpus}: {len(df)} slots s1, {len(a)} infills aceitos, {df.problema.nunique()} celulas')
    print('match bit-a-bit max|dX| =', a['match_dx'].max())
    print('argmax GLOBAL do dist_dec : %d/%d = %.2f%%'%(a.is_argmax_global.sum(),len(a),100*a.is_argmax_global.mean()))
    print('argmax restrito a {pred_classe==1}: %d/%d = %.2f%%'%(a.is_argmax_S.sum(),len(a),100*a.is_argmax_S.mean()))
    print('rank global mediano %.1f  (q25 %.0f q75 %.0f) de N mediano %.0f'%(a.rank_global.median(),a.rank_global.quantile(.25),a.rank_global.quantile(.75),a.N.median()))
    print('escolhido dentro de {pred_classe==1}: %.2f%%'%(100*a.chosen_in_S.mean()))
    print('predicao PRE-fix (pos <= |S|-1): %d/%d = %.2f%%'%(a.limiar_pre.sum(),len(a),100*a.limiar_pre.mean()))
    print('frac_n1==1 -> argmax: %s'%(a[a.frac_n1==1].is_argmax_global.mean() if (a.frac_n1==1).any() else 'n/a'))
    print('frac_n1<1  -> argmax: %s'%(a[a.frac_n1<1].is_argmax_global.mean() if (a.frac_n1<1).any() else 'n/a'))
    z=a[a.n_desal==0]
    print('BLOCOS n_desalinhado==0 (S == {pred_classe==1} EXATO): n=%d  argmax_S=%.2f%%  argmax_global=%.2f%%'%(len(z),100*z.is_argmax_S.mean() if len(z) else float('nan'),100*z.is_argmax_global.mean() if len(z) else float('nan')))
    print('slots perdidos: %d (%.2f%%) | count==0: %d | cand_vazio(n_cand=0): %d'%(df.slot_perdido.sum(),100*df.slot_perdido.mean(),(df['count']==0).sum(),(df.n_cand==0).sum()))
    print('n_desalinhado medio %.2f  mediana %.0f  max %d'%(df.n_desal.mean(),df.n_desal.median(),df.n_desal.max()))
    print('por celula:')
    print(a.groupby('problema').agg(n=('fe','size'),argmax=('is_argmax_global','mean'),argmaxS=('is_argmax_S','mean'),rank=('rank_global','median')).to_string())
