import json, hashlib, os
import pandas as pd, numpy as np
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42'
man=json.load(open(B+'.manifest.json'))
recs=[json.loads(l) for l in open(B+'.jsonl')]
gens=[r for r in recs if r['rec']=='b3_gen']
sondas=[r for r in recs if r['rec']=='sonda']
guards=[r for r in recs if r['rec']=='guard']
footer=[r for r in recs if r['rec']=='footer'][0]
real=pd.read_parquet(B+'__real.parquet'); pop=pd.read_parquet(B+'__pop.parquet')
sur=pd.read_parquet(B+'__surrogate.parquet'); tim=pd.read_parquet(B+'__timing.parquet')
print('=== U1 orcamento ===')
D=recs[0]['D']; M=recs[0]['M']
print('D',D,'M',M,'maxfe',man['maxfe'],'31D-1',31*D-1,'len(1)',len(real),'fe_final',man['fe_final'])
print('cols real', list(real.columns))
print('fe_index denso 0-based:', (real.fe_index.values==np.arange(len(real))).all())
print('solution_id unicos', real.solution_id.nunique(),'de',len(real))
xc=[c for c in real.columns if c.startswith('x')]
print('xcols',xc)
b=[tuple(r) for r in real[xc].values]
print('dupX', len(b)-len(set(b)))
print('termino', footer['termino'], 'status', man['status'])
print()
print('=== U2 DoE ===')
init=real[real.fase=='init'] if 'fase' in real.columns else None
print('fases', real.fase.value_counts().to_dict())
print('n init', (real.fase=='init').sum(), '11D-1', 11*D-1)
doe='/Users/gmello/Documents/python_repos/mestrado/data/doe/MMF1/doe_MMF1_42.parquet'
print('doe existe', os.path.exists(doe))
if os.path.exists(doe):
    d=pd.read_parquet(doe); print('doe shape',d.shape, list(d.columns)[:6])
    A=real[real.fase=='init'][xc].values.astype(np.float64)
    dc=[c for c in d.columns if c.startswith('x')]
    Bx=d[dc].values.astype(np.float64)[:len(A)]
    print('max|dX| artefato vs (1) =', np.abs(A-Bx.astype(np.float32).astype(np.float64)).max(), ' (float64 direto)', np.abs(A-Bx).max())
    sc=doe.replace('.parquet','.sha256')
    for cand in [doe+'.sha256', doe.replace('.parquet','.sha256')]:
        if os.path.exists(cand): print('sidecar',cand, open(cand).read().strip()[:80])
    h=hashlib.sha256(open(doe,'rb').read()).hexdigest()
    print('sha256 do arquivo doe =',h,' manifest doe_hash=',man['doe_hash'],' igual?',h==man['doe_hash'])
    # dup no DoE
    bb=[tuple(r) for r in Bx]
    print('dup no DoE (float64):', len(bb)-len(set(bb)))
print()
print('=== U3 1 fit/ciclo ===')
print('len(4)',len(tim),'len(fit_series)',len(man['fit_series']),'n b3_gen',len(gens))
print('geracao 4:', list(tim.geracao.values))
print('cols timing', list(tim.columns))
print('n_acumulado', list(tim.n_acumulado.values) if 'n_acumulado' in tim.columns else None)
print()
print('=== U4 cadencia sonda ===')
nciclos=len(gens); hard=any(g['name']=='hard_stop' for g in guards)
G=nciclos+ (1 if hard else 0)
esperado=sorted(set([1]+[g for g in range(2,G+1) if g%2==0]+[G]))
obs=[r['geracao'] for r in sondas]
print('n_ciclos',nciclos,'hard_stop',hard,'G',G,'esperado',esperado,'observado',obs,'IGUAL',esperado==obs)
print('n_blocos manifest', man['sonda']['n_blocos'], 'S', man['sonda']['S'])
sb=sur[sur.regime=='sonda']
print('regimes na 3', sur.regime.value_counts().to_dict())
print('pts por bloco', sb.groupby('geracao').size().to_dict())
