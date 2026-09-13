import json, numpy as np, pandas as pd
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
def rd(root,suf):
    return pd.read_parquet(f'{root}/experiments/main/b1/exp_main_b1_MMF1_42{suf}.parquet')
com=rd(f'{B}/g6_com','__real'); sem=rd(f'{B}/g6_sem','__real')
print('① COM',com.shape,'SEM',sem.shape)
print('colunas iguais:', list(com.columns)==list(sem.columns))
cols=[c for c in com.columns if c.startswith(('x','f'))]
eq = com[cols].equals(sem[cols])
print('① X/f BIT-IDENTICA:',eq)
if not eq:
    for c in cols:
        d=(com[c].values!=sem[c].values).sum()
        if d: print('  difere',c,d)
# fase, solution_id, fe_index
for c in ['fase','solution_id','fe_index']:
    if c in com.columns:
        print('  ',c,'identico:',bool((com[c].values==sem[c].values).all()))
# ③
scom=rd(f'{B}/g6_com','__surrogate'); ssem=rd(f'{B}/g6_sem','__surrogate')
print('③ COM',scom.shape,'SEM',ssem.shape)
print('③ regimes COM',scom.regime.value_counts().to_dict())
print('③ regimes SEM',ssem.regime.value_counts().to_dict())
# online only comparison
ocom=scom[scom.regime=='online'].reset_index(drop=True); osem=ssem[ssem.regime=='online'].reset_index(drop=True)
print('③ online COM',len(ocom),'SEM',len(osem),'iguais:',ocom.shape==osem.shape)
if ocom.shape==osem.shape:
    cc=[c for c in ocom.columns if ocom[c].dtype.kind in 'fiu']
    bad=[c for c in cc if not np.array_equal(ocom[c].values,osem[c].values,equal_nan=True)]
    print('③ online colunas numericas que diferem:',bad)
# manifest sonda block
for t in ['g6_com','g6_sem']:
    m=json.load(open(f'{B}/{t}/experiments/main/b1/exp_main_b1_MMF1_42.manifest.json'))
    s=m.get('sonda',{})
    print(t,'sonda: desligada=',s.get('desligada'),'n_blocos=',s.get('n_blocos'),'n_linhas=',s.get('n_linhas'),'| cache_hits',m['cache_hits'],'n_ger',m['n_geracoes'],'fe_final',m['fe_final'])
# jsonl b1_gen sequence equality
def gens(root):
    out=[]
    for l in open(f'{B}/{root}/experiments/main/b1/exp_main_b1_MMF1_42.jsonl'):
        r=json.loads(l)
        if r.get('rec')=='b1_gen': out.append(r)
    return out
gc_,gs_=gens('g6_com'),gens('g6_sem')
print('b1_gen COM',len(gc_),'SEM',len(gs_))
keys=['geracao','fe','best_sid','gbest','mu_best','sigma_best','ei_best','norm_min','norm_max','lambda','n_treino','n_subset','ga_pop','ga_iters','dist_min_arquivo','theta_media']
diff={k:0 for k in keys}
for a,b in zip(gc_,gs_):
    for k in keys:
        if json.dumps(a.get(k))!=json.dumps(b.get(k)): diff[k]+=1
print('b1_gen campos com diferenca COM x SEM:',{k:v for k,v in diff.items() if v})
