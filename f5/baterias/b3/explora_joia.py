import pandas as pd, json, numpy as np, sys
base='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/DTLZ2/42/exp_main_b3_DTLZ2_42'
s=pd.read_parquet(base+'__surrogate.parquet'); on=s[s.regime=='online'].reset_index(drop=True)
recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
gens=[x for x in recs if x['rec']=='b3_gen']
r=pd.read_parquet(base+'__real.parquet')
M=3; D=12
sigcols=[f'sigma_{j}' for j in range(M)]; mucols=[f'mu_{j}' for j in range(M)]
xcols=[f'x{j}' for j in range(D)]
for g in gens[:3]+gens[-2:]:
    ge=g['geracao']; blk=on[on.geracao==ge].reset_index(drop=True)
    ppw=g['pop_por_w']; last_n=ppw[-1]; last=blk.iloc[len(blk)-last_n:].reset_index(drop=True)
    idx=[i-1 for i in g['index']]
    sel=last.iloc[idx]
    got=sel[sigcols].to_numpy()
    exp=np.array(g['sigma_sel']['sqrtmse_por_objetivo'])
    crit=np.array(g['sigma_sel']['criterio_meanMSE'])
    print('gen',ge,'ramo',g['ramo'],'maxabs sigma diff',np.abs(got-exp).max(),
          '| crit vs mean(sig^2) rel', np.abs(crit-(exp**2).mean(1)).max()/max(crit.max(),1e-30))
    # X match with new real rows
    fe_prev = g['fe'] - g['lote']
    newr = r[(r.fe_index>=fe_prev)&(r.fe_index<g['fe'])]
    print('   new real rows',len(newr),'maxabs X diff', np.abs(sel[xcols].to_numpy()-newr[xcols].to_numpy()).max() if len(newr)==len(sel) else 'NA')
    # rank of selected meanMSE within last block
    mm=(last[sigcols].to_numpy()**2).mean(1)
    pct=[(mm<mm[i]).mean() for i in idx]
    print('   pctil meanMSE dos selecionados', np.round(pct,3))
