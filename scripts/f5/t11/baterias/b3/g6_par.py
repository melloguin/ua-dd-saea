"""§3.1 NAO-PERTURBACAO da sonda no b3: par COM x SEM, todas as camadas."""
import json, numpy as np, pandas as pd, hashlib
B='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
A=f'{B}/g6_com/experiments/main/b3/exp_main_b3_MMF1_42'
C=f'{B}/g6_sem/experiments/main/b3/exp_main_b3_MMF1_42'
def H(a): return hashlib.sha256(np.ascontiguousarray(a)).hexdigest()[:16]
for lay in ['real','pop','surrogate','timing']:
    a=pd.read_parquet(A+f'__{lay}.parquet'); c=pd.read_parquet(C+f'__{lay}.parquet')
    num=[k for k in a.columns if a[k].dtype.kind in 'fiu']
    print(f'{lay:10s} com={a.shape} sem={c.shape}')
    if lay in ('real','pop'):
        same=a.shape==c.shape and H(a[num].to_numpy(float))==H(c[num].to_numpy(float))
        print(f'           BIT-IDENTICA: {same}  hash_com={H(a[num].to_numpy(float))} hash_sem={H(c[num].to_numpy(float))}')
    if lay=='surrogate':
        for t,d in [('com',a),('sem',c)]:
            print(f'           {t}: regimes={d.regime.value_counts().to_dict()}')
        ao=a[a.regime=='online']; co=c[c.regime=='online']
        n=[k for k in ao.columns if ao[k].dtype.kind in 'fiu']
        print(f'           online com={len(ao)} sem={len(co)} bit-identica={H(ao[n].to_numpy(float))==H(co[n].to_numpy(float))}')
# ⑥ decisoes
def gens(p): return [json.loads(l) for l in open(p+'.jsonl') if l.strip() and json.loads(l).get('rec')=='b3_gen']
ga,gc=gens(A),gens(C)
campos=['geracao','fe','n_treino','arquivo','u_alvo','u_efetivo','NumV1','NumV2','Flag','ramo','lote','index','pop_por_w','nzero_updata','fe_treino_max']
ok=all(all(x[k]==y[k] for k in campos) for x,y in zip(ga,gc)) and len(ga)==len(gc)
print(f'⑥ b3_gen: com={len(ga)} sem={len(gc)} decisoes IDENTICAS={ok}')
for x,y in zip(ga,gc):
    d=[k for k in campos if x[k]!=y[k]]
    if d: print('   difere no ciclo',x['geracao'],d)
# numericos finos
for nome in ['apd_sel','tempo_fit_s']:
    dif=max(abs(np.array(x[nome],float)-np.array(y[nome],float)).max() for x,y in zip(ga,gc))
    print(f'   max|Δ {nome}| = {dif:.3g}')
ma=json.load(open(A+'.manifest.json')); mc=json.load(open(C+'.manifest.json'))
print('⑤ com: sonda.desligada=',ma['sonda']['desligada'],'n_blocos=',ma['sonda']['n_blocos'],'| sem:',mc['sonda']['desligada'],mc['sonda']['n_blocos'])
print('⑤ fe_final/n_ger/cache_hits com',ma['fe_final'],ma['n_geracoes'],ma['cache_hits'],'sem',mc['fe_final'],mc['n_geracoes'],mc['cache_hits'])
print('⑤ tempo_pred_sonda_s com',ma['timing']['tempo_pred_sonda_s'],'sem',mc['timing']['tempo_pred_sonda_s'])
print('⑤ tempo_aval_real_s com',ma['timing']['tempo_aval_real_s'],'sem',mc['timing']['tempo_aval_real_s'])
