"""Bateria de fidelidade — config nsga3 (piso online NSGA-III), F5.3b. READ-ONLY sobre os dados."""
import json, os, itertools, math
import numpy as np, pandas as pd

ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/nsga3'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
probs=sorted(p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}'))

# NOTA: a versao correta (literal) do UniformPoint do PlatEMO esta em bateria2_nsga3.py.
# Esta bateria 1 e apenas o censo/estrutura; o lattice aqui era uma 1a aproximacao com H
# decrementado a mais (10 e 19 vetores) e foi SUPERSEDIDA. Nao usar o campo H desta saida.

def dasdennis(H,M):
    pts=[]
    for c in itertools.combinations(range(H+M-1), M-1):
        prev=-1; row=[]
        for x in c:
            row.append(x-prev-1); prev=x
        row.append(H+M-2-prev)
        pts.append(row)
    W=np.array(pts,dtype=float)/H
    return W

def lattice_platemo(N,M):
    H=1
    while math.comb(H+M, M-1) <= N: H+=1
    H-=1
    W=dasdennis(H,M)
    W=np.maximum(W,1e-6)
    return H,W

rows_asp=[]; gen_rows=[]; guard_rows=[]; cell=[]
lat_rows=[]; tim_rows=[]
for prob in probs:
    d=f'{ROOT}/{prob}/42'; base=f'{d}/exp_main_nsga3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]
    dec=[r for r in recs if r.get('rec')=='decomposicao'][0]
    sd =[r for r in recs if r.get('rec')=='seeding'][0]
    foot=[r for r in recs if r.get('rec')=='footer'][0]
    gens=[r for r in recs if r.get('rec')=='nsga3_gen']
    guards=[r for r in recs if r.get('rec')=='guard']
    D,M=hdr['D'],hdr['M']
    R=pd.read_parquet(base+'__real.parquet')
    P=pd.read_parquet(base+'__pop.parquet')
    S=pd.read_parquet(base+'__surrogate.parquet')
    T=pd.read_parquet(base+'__timing.parquet')
    xc=[f'x{i}' for i in range(D)]; fc=[f'f{i}' for i in range(M)]
    init=11*D-1; maxfe=31*D-1
    Nef=man['params']['N_efetivo']; Nnom=man['params']['N_nominal']
    # --- lattice
    H,Wref=lattice_platemo(Nnom,M)
    Wlog=np.array(dec['vetores'],dtype=float)
    # ordena ambos lexicograficamente p/ comparar como conjunto
    def key(a): return sorted(map(tuple,np.round(a,9)))
    dmax=np.abs(np.array(key(Wref))-np.array(key(Wlog))).max() if Wref.shape==Wlog.shape else np.nan
    lat_rows.append(dict(prob=prob,M=M,Nnom=Nnom,H=H,n_ref=len(Wref),n_log=len(Wlog),
        Nef_man=Nef,Nlat_log=dec['N_lattice'],dmax=dmax,
        soma1=float(np.abs(Wlog.sum(1)-1).max()),
        vals=sorted(set(np.round(Wlog.flatten(),6)))[:6]))
    # --- guards
    ch=[g for g in guards if g['name']=='cache_hit']
    hs=[g for g in guards if g['name']=='hard_stop']
    ch_init=[g for g in ch if g['fe']==init]
    # --- ② pop
    grp=P.groupby('geracao')
    pop_sizes=set(grp.size().values)
    pop1=set(P[P.geracao==1].solution_id)
    doe_ids=set(range(init))
    # --- ① fases
    fases=R.fase.value_counts().to_dict()
    fe_dense = (R.fe_index.values==np.arange(len(R))).all()
    sid_dense= (R.solution_id.values==np.arange(len(R))).all()
    # duplicatas bit-exatas na ①
    Xr=R[xc].values
    nuniq=len(pd.unique([tuple(r) for r in Xr]))
    # --- ④ timing
    t_gen_jsonl=np.array([g['tempo_geracao_s'] for g in gens],dtype=float)
    t_gen_p=T.sort_values('geracao').tempo_geracao_s.values.astype(float)
    dt=np.abs(t_gen_jsonl-t_gen_p).max() if len(t_gen_jsonl)==len(t_gen_p) else np.nan
    # --- offspring arithmetic
    n_off_gen = 2*(Nef//2)          # PlatEMO OperatorGA: 2*floor(N/2)
    ngen=len(gens)
    fe_gen=np.array([g['fe'] for g in gens])
    fe_consumido=fe_gen[-1]-init
    off_full=(ngen-1)*n_off_gen
    ch_pos=[g for g in ch if g['fe']>init]
    for g in gens:
        gen_rows.append(dict(prob=prob,D=D,M=M,**{k:v for k,v in g.items() if k not in('rec','ts')}))
    for g in guards:
        guard_rows.append(dict(prob=prob,**{k:v for k,v in g.items() if k not in('rec','ts')}))
    cell.append(dict(prob=prob,D=D,M=M,Nnom=Nnom,Nef=Nef,H=H,ngen=ngen,
        maxfe_ok=(man['maxfe']==maxfe and man['fe_final']==maxfe and len(R)==maxfe),
        init_ok=(fases.get('init',0)==init), fases=str(sorted(fases)),
        fe_dense=fe_dense, sid_dense=sid_dense, n_x_unicos=nuniq, n_real=len(R),
        pop_sizes=str(sorted(pop_sizes)), n_grp=len(grp), pop1_in_doe=pop1<=doe_ids,
        n_pop1=len(pop1),
        ch_total=len(ch), ch_init=len(ch_init), ch_pos=len(ch_pos), hs=len(hs),
        hs_fe=hs[0]['fe'] if hs else None, ch_man=man['cache_hits'],
        n_off_gen=n_off_gen, off_full=off_full, fe_consumido=fe_consumido,
        arit_off=off_full-fe_consumido, arit_ok=(off_full-fe_consumido)==len(ch_pos),
        surr_rows=len(S), fit_series=len(man['fit_series']),
        sigma_dict=('sigma_dict' in man), sonda_status=man['sonda']['status'],
        n_blocos=man['sonda']['n_blocos'],
        t_fit=man['timing']['tempo_fit_surrogate_s'], t_busca=man['timing']['tempo_busca_s'],
        t_sonda=man['timing']['tempo_pred_sonda_s'], t_aval=man['timing']['tempo_aval_real_s'],
        t_total=man['timing']['tempo_total_s'], soma_t4=float(np.nansum(t_gen_p)),
        t4_nan_fit=int(T.tempo_fit_s.isna().sum()), t4_nan_busca=int(T.tempo_busca_s.isna().sum()),
        t4_nan_sonda=int(T.tempo_pred_sonda_s.isna().sum()), t4_nan_nac=int(T.n_acumulado.isna().sum()),
        t4_rows=len(T), dt_jsonl_p=dt,
        n_doe_log=sd['n_doe'], n_frentes=sd['n_frentes'], n_frente1=sd['n_frente1'],
        excede=sd['frente1_excede_pop'],
        doe_hash_man=man['doe_hash'], doe_hash_hdr=hdr['doe_hash'],
        algo_version=man['algo_version'], status=man['status'], termino=foot['termino'],
        cp_init=foot['cp_init'], n_foot=len([r for r in recs if r.get('rec')=='footer']),
        piso=hdr['piso'], surrogate_flag=hdr['surrogate'],
        principio=hdr['principio'], patches=man['params']['patches'],
        operadores=hdr['operadores'], Nef_foot=foot['N_efetivo']))
C=pd.DataFrame(cell); L=pd.DataFrame(lat_rows)
G=pd.DataFrame(gen_rows); Q=pd.DataFrame(guard_rows)
C.to_csv(f'{OUT}/celulas_aspectos.csv',index=False)
L.to_csv(f'{OUT}/lattice_uniformpoint.csv',index=False)
G.to_pickle(f'{OUT}/gen_events.pkl'); Q.to_pickle(f'{OUT}/guards.pkl')
pd.set_option('display.width',250)
print(C[['prob','D','M','Nnom','Nef','H','ngen','maxfe_ok','init_ok','fe_dense','sid_dense','pop_sizes','n_grp','pop1_in_doe','n_pop1','ch_total','ch_init','ch_pos','hs','ch_man','n_off_gen','off_full','fe_consumido','arit_off','arit_ok']].to_string(index=False))
print()
print(L.to_string(index=False))
