import json, numpy as np, pandas as pd
SM='/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1'
S4='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42'
f='exp_main_b1_MMF1_42'
a=pd.read_parquet(f'{SM}/{f}__real.parquet'); b=pd.read_parquet(f'{S4}/{f}__real.parquet')
print('① smoke',a.shape,'s42',b.shape, 'colunas', list(a.columns)==list(b.columns))
xc=[c for c in a.columns if c.startswith('x')]; fc=[c for c in a.columns if c.startswith('f') and c!='fase' and c!='fe_index']
print('init(fase=init) smoke',(a.fase=='init').sum(),'s42',(b.fase=='init').sum())
ni=(a.fase=='init').sum()
print('DoE bit-identico:', np.array_equal(a[xc].values[:ni],b[xc].values[:ni]), ' f idem:',np.array_equal(a[fc].values[:ni],b[fc].values[:ni]))
# primeiro infill onde divergem
n=min(len(a),len(b))
dif=np.where(~np.isclose(a[xc].values[:n],b[xc].values[:n],rtol=0,atol=0).all(axis=1))[0]
print('primeira linha da ① que difere: fe_index',dif[0] if len(dif) else None,' total linhas diferentes',len(dif),'de',n)
if len(dif):
    i=dif[0]
    print('  smoke X',a[xc].values[i],'f',a[fc].values[i])
    print('  s42   X',b[xc].values[i],'f',b[fc].values[i])
    print('  |dX| =',np.abs(a[xc].values[i]-b[xc].values[i]))
# jsonl gens
def gens(p):
    return [json.loads(l) for l in open(p) if json.loads(l).get('rec')=='b1_gen']
ga,gb=gens(f'{SM}/{f}.jsonl'),gens(f'{S4}/{f}.jsonl')
print('b1_gen smoke',len(ga),'s42',len(gb))
for i in range(min(len(ga),len(gb))):
    if json.dumps(ga[i]['lambda'])!=json.dumps(gb[i]['lambda']):
        print('  1a geracao com lambda diferente:',i+1); break
else: print('  lambda identico nas',min(len(ga),len(gb)),'primeiras geracoes')
for i in range(min(len(ga),len(gb))):
    if ga[i]['best_sid']!=gb[i]['best_sid']:
        print('  1a geracao com best_sid diferente: g',i+1,'smoke',ga[i]['best_sid'],'s42',gb[i]['best_sid'])
        print('   gbest smoke',ga[i]['gbest'],'s42',gb[i]['gbest'],' ei_best',ga[i]['ei_best'],gb[i]['ei_best'])
        print('   mu_best',ga[i]['mu_best'],gb[i]['mu_best'],' sigma',ga[i]['sigma_best'],gb[i]['sigma_best'])
        print('   theta_media',ga[i]['theta_media'],gb[i]['theta_media'])
        break
# gen 1 completo
print('--- geracao 1 lado a lado ---')
for k in ['gbest','mu_best','sigma_best','ei_best','norm_min','norm_max','n_treino','n_subset','ga_pop','ga_iters','best_sid','theta_media','theta_min','theta_max','dist_min_arquivo','n_dedup','fe_treino_max','n_arquivo']:
    print(' %-18s smoke=%s | s42=%s' % (k, ga[0].get(k), gb[0].get(k)))
print(' modelo_hp smoke', json.dumps(ga[0].get('modelo_hp'))[:300])
print(' modelo_hp s42  ', json.dumps(gb[0].get('modelo_hp'))[:300])
