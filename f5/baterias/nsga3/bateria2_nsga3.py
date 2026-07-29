"""Bateria 2 — lattice exato, aritmetica de descendentes, seeding, timing. READ-ONLY."""
import json,os,math,itertools
import numpy as np,pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3'
OUT='.'
probs=sorted(p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}'))

def uniformpoint_nbi(N,M):
    """Traducao literal de PlatEMO 4.15 UniformPoint(N,M,'NBI')."""
    H1=1
    while math.comb(H1+M,M-1)<=N: H1+=1
    rows=list(itertools.combinations(range(1,H1+M),M-1))
    W=np.array(rows,dtype=float)-np.arange(M-1)[None,:]-1.0
    W=(np.hstack([W,np.full((len(W),1),float(H1))])-np.hstack([np.zeros((len(W),1)),W]))/H1
    W=np.maximum(W,1e-6)
    return H1,W

res=[]; lat=[]; seedrows=[]
for prob in probs:
    base=f'{ROOT}/{prob}/42/exp_main_nsga3_{prob}_42'
    man=json.load(open(base+'.manifest.json'))
    recs=[json.loads(l) for l in open(base+'.jsonl') if l.strip()]
    hdr=[r for r in recs if r.get('rec')=='header'][0]
    dec=[r for r in recs if r.get('rec')=='decomposicao'][0]
    sd =[r for r in recs if r.get('rec')=='seeding'][0]
    gens=[r for r in recs if r.get('rec')=='nsga3_gen']
    guards=[r for r in recs if r.get('rec')=='guard']
    D,M=hdr['D'],hdr['M']; init=11*D-1; maxfe=31*D-1
    Nef=man['params']['N_efetivo']
    H1,Wr=uniformpoint_nbi(man['params']['N_nominal'],M)
    Wl=np.array(dec['vetores'],dtype=float)
    ok_shape=Wr.shape==Wl.shape
    dmax=float(np.abs(np.sort(Wr,axis=0)-np.sort(Wl,axis=0)).max()) if ok_shape else np.nan
    # comparacao por linha (ordem preservada)
    drow=float(np.abs(Wr-Wl).max()) if ok_shape else np.nan
    lat.append(dict(prob=prob,M=M,H1=H1,n_ref=len(Wr),n_log=len(Wl),Nef=Nef,
                    ordem_igual=drow, conjunto_igual=dmax))
    ch=[g for g in guards if g['name']=='cache_hit']; hs=[g for g in guards if g['name']=='hard_stop']
    ch_init=[g for g in ch if g['fe']==init]
    sid_init=[g['solution_id'] for g in ch_init]
    fe_last=gens[-1]['fe']
    ch_mid=[g for g in ch if init<g['fe']<=fe_last]
    ch_tail=[g for g in ch if g['fe']>fe_last]
    n_off=2*(Nef//2); ngen=len(gens)
    off_full=(ngen-1)*n_off
    fe_cons=fe_last-init
    partial=(maxfe-fe_last)+len(ch_tail)
    P=pd.read_parquet(base+'__pop.parquet'); R=pd.read_parquet(base+'__real.parquet')
    T=pd.read_parquet(base+'__timing.parquet')
    xc=[f'x{i}' for i in range(D)]; fc=[f'f{i}' for i in range(M)]
    # populacao inicial (gen1) == N melhores do DoE por NDSort+CD ?
    pop1=P[P.geracao==1].solution_id.values
    # recomputo NDSort na ① init
    F=R.iloc[:init][fc].values
    def ndsort(F):
        n=len(F); front=np.zeros(n,int); rank=np.full(n,-1)
        dom=[[ ] for _ in range(n)]; cnt=np.zeros(n,int)
        le=(F[:,None,:]<=F[None,:,:]).all(2); lt=(F[:,None,:]<F[None,:,:]).any(2)
        D_=le&lt   # i domina j
        cnt=D_.sum(0)
        cur=np.where(cnt==0)[0]; r=1
        while len(cur):
            rank[cur]=r
            nxt=[]
            for i in cur:
                for j in np.where(D_[i])[0]:
                    cnt[j]-=1
                    if cnt[j]==0: nxt.append(j)
            cur=np.array(sorted(set(nxt)),int); r+=1
        return rank
    rk=ndsort(F)
    n_f1=int((rk==1).sum()); n_fronts=int(rk.max())
    # os selecionados: rank dos ids de pop1
    rk_sel=rk[pop1]
    sel_ok = None
    # regra: seleciona frentes inteiras ate exceder; ultima frente por CD
    cum=0; k=1; full=[]
    while cum+int((rk==k).sum())<=Nef:
        cum+=int((rk==k).sum()); full.append(k); k+=1
    sel_ok = set(np.where(np.isin(rk,full))[0]) <= set(pop1.tolist())
    borda = int((rk_sel==k).sum()) if cum<Nef else 0
    seedrows.append(dict(prob=prob,M=M,Nef=Nef,n_doe_log=sd['n_doe'],n_doe_calc=init,
        n_frentes_log=sd['n_frentes'],n_frentes_calc=n_fronts,
        n_frente1_log=sd['n_frente1'],n_frente1_calc=n_f1,
        excede_log=sd['frente1_excede_pop'],excede_calc=(n_f1>man['params']['N_nominal']),
        rank_max_sel=int(rk_sel.max()),frentes_cheias=str(full),
        frentes_cheias_todas_dentro=bool(sel_ok),n_borda=borda,
        pop1_ids_no_doe=bool((pop1<init).all()),n_pop1=len(pop1),n_pop1_dist=len(set(pop1))))
    res.append(dict(prob=prob,D=D,M=M,Nef=Nef,ngen=ngen,n_off_gen=n_off,
        ch_init=len(ch_init),sid_init_dist=len(set(sid_init)),
        sid_init_eq_Nef=(len(set(sid_init))==Nef),extra_init=len(ch_init)-len(set(sid_init)),
        ch_mid=len(ch_mid),ch_tail=len(ch_tail),
        off_full=off_full,fe_cons=fe_cons,fecha=(off_full-fe_cons)==len(ch_mid),
        partial=partial,partial_le=partial<=n_off,
        hs_fe=hs[0]['fe'] if hs else None,hs_ok=(len(hs)==1 and hs[0]['fe']==maxfe),
        ch_man=man['cache_hits'],ch_tot=len(ch),ch_bate=(man['cache_hits']==len(ch)),
        t4_rows=len(T),t4_eq_ngen=(len(T)==ngen),
        soma_t4=float(T.tempo_geracao_s.sum()),t_total=man['timing']['tempo_total_s'],
        t_aval=man['timing']['tempo_aval_real_s'],
        t4_le_total=float(T.tempo_geracao_s.sum())<=man['timing']['tempo_total_s'],
        nan_fit=int(T.tempo_fit_s.isna().sum()),nan_busca=int(T.tempo_busca_s.isna().sum()),
        nan_sonda=int(T.tempo_pred_sonda_s.isna().sum()),nan_nac=int(T.n_acumulado.isna().sum()),
        dt_max=float(np.abs(np.array([g['tempo_geracao_s'] for g in gens])-T.sort_values('geracao').tempo_geracao_s.values).max())))
Rz=pd.DataFrame(res); Lz=pd.DataFrame(lat); Sz=pd.DataFrame(seedrows)
Rz.to_csv('aritmetica_descendentes.csv',index=False)
Lz.to_csv('lattice_uniformpoint.csv',index=False)
Sz.to_csv('seeding_D88.csv',index=False)
pd.set_option('display.width',260)
print(Lz.to_string(index=False)); print()
print(Rz.to_string(index=False)); print()
print(Sz.to_string(index=False))
