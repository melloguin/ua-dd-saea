import pandas as pd, json, numpy as np, os, glob
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
probs=sorted(os.listdir(ROOT))
rows=[]; keyset={}
for pr in probs:
    base=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(base+'.manifest.json'))
    recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]
    ftr=[x for x in recs if x['rec']=='footer']
    gens=[x for x in recs if x['rec']=='b3_gen']
    sondas=[x for x in recs if x['rec']=='sonda']
    guards=[x for x in recs if x['rec']=='guard']
    for g in gens: keyset[pr]=sorted(g.keys())
    from collections import Counter
    rows.append(dict(problema=pr, D=hdr['D'], M=hdr['M'], maxfe=m['maxfe'], fe_final=m['fe_final'],
        init=11*hdr['D']-1, n_ger_manifest=m['n_geracoes'], n_gen_evt=len(gens),
        n_sonda=len(sondas), n_guard=len(guards),
        guard_names=str(Counter([x['name'] for x in guards])),
        cache_hits=m['cache_hits'], status=m['status'],
        termino=(ftr[0]['termino'] if ftr else 'SEM_FOOTER'),
        N_vet=m['params']['N_vetores'], delta=m['params']['delta'], wmax=m['params']['wmax'], mu=m['params']['mu'],
        alpha=m['params']['alpha'], theta0=m['params']['theta0'], tb=m['params']['theta_bounds'], dace=m['params']['dace'],
        ramos=str(Counter([g['ramo'] for g in gens])),
        u_ef=str(Counter([g['u_efetivo'] for g in gens])),
        n_wblocks=str(Counter([len(g['pop_por_w']) for g in gens])),
        arquivo=str(Counter([g['arquivo'] for g in gens])),
        n_treino=str(Counter([g['n_treino'] for g in gens])),
        nzero=str(Counter([g['nzero_updata'] for g in gens])),
        nvv=str(Counter([g['n_vetores_vazios'] for g in gens])),
        ramo_gen1=gens[0]['ramo'], flag_gen1=gens[0]['Flag'],
        sonda_gers=str(sorted(m['sonda']['geracoes']))[:60]+('...' if len(m['sonda']['geracoes'])>12 else ''),
        sonda_last=max(m['sonda']['geracoes']), sonda_nblocos=m['sonda']['n_blocos'], sonda_k=m['sonda']['k'],
        maq_tempo=m['timing']['tempo_total_s']))
df=pd.DataFrame(rows)
pd.set_option('display.width',300)
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b3/meta_celulas.csv',index=False)
print(df[['problema','D','M','maxfe','fe_final','init','n_ger_manifest','n_gen_evt','cache_hits','termino','N_vet','delta','ramos','u_ef','sonda_last','sonda_nblocos']].to_string())
print()
print(df[['problema','n_wblocks','arquivo','n_treino','nzero','nvv','ramo_gen1','flag_gen1','n_guard','guard_names']].to_string())
print()
ks=set()
for pr,k in keyset.items(): ks|=set(k)
print('UNIAO de chaves b3_gen:', sorted(ks))
for pr,k in keyset.items():
    if set(k)!=ks: print('DIFERE',pr, sorted(ks-set(k)))
