#!/usr/bin/env python
"""
BATERIA B — c262 qNEHVI: aprofundamentos (F5.3b, protocolo v1.1). READ-ONLY nos dados.
  B1  U7 refeito: residual = tempo_geracao − (fit+busca) vs tempo_pred_sonda
  B2  reconciliação fina dos acqf_warnings (hard_stop não tem a chave)
  B3  n_baseline==0 ↔ nenhum ponto da ① domina o ref da aquisição (S.5)
  B4  posição do escolhido na ③ + identidade x(③ escolhido) ≡ x(①) bit-a-bit
  B5  determinismo do refit: pares com lengthscale IDÊNTICO ≡ iterações de cache-hit
  B6  trajetórias (20 checkpoints) — violações de monotonicidade do IGD+
  B7  sonda F5.2e — WAPE 1º/último bloco + cobertura por célula-objetivo
  B8  posição vs pisos (moead/nsga2/nsga3/smsemoa) e vs os 12 rivais SA
  B9  cache-hit: coordenadas do ponto repetido
  B10 paisagem da aquisição: spread dos 10 restarts
"""
import json, glob, os, collections
import numpy as np, pandas as pd

ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
REPO='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
F5=f'{REPO}/f5'; OUT=f'{F5}/baterias/c262'
PROBS=sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))

rows=[]
det_ch=[]
for prob in PROBS:
    b=f'{ROOT}/{prob}/42'; s=f'exp_main_c262_{prob}_42'
    man=json.load(open(f'{b}/{s}.manifest.json'))
    recs=[json.loads(l) for l in open(f'{b}/{s}.jsonl') if l.strip()]
    by=collections.defaultdict(list)
    for x in recs: by[x.get('rec')].append(x)
    hdr=by['header'][0]; dec=by['decision']; snd=by['sonda']; grd=by['guard']; tw=by['optimize_acqf_warning']
    D=hdr['D']; M=hdr['M']; ng=man['n_geracoes']
    real=pd.read_parquet(f'{b}/{s}__real.parquet')
    tim=pd.read_parquet(f'{b}/{s}__timing.parquet')
    xc=[f'x{i}' for i in range(D)]; fc=[f'f{j}' for j in range(M)]
    r={'problema':prob,'D':D,'M':M,'n_ger':ng}

    # B1 — U7 refeito
    resid = tim['tempo_geracao_s'].values - (tim['tempo_fit_s'].values+tim['tempo_busca_s'].values)
    ps = tim['tempo_pred_sonda_s'].values
    gset=set(int(x['geracao']) for x in snd)
    mask=np.array([g in gset for g in tim['geracao'].values])
    r['U7_inv1_viol']=int((resid < -1e-6).sum())
    r['U7_resid_ge_sonda']=int((resid + 1e-6 >= ps).sum()); r['U7_n']=len(resid)
    r['U7_resid_med_com_sonda']=float(np.median(resid[mask]))
    r['U7_resid_med_sem_sonda']=float(np.median(resid[~mask]))
    r['U7_sonda_med']=float(np.median(ps[mask]))
    r['U7_overhead_med']=float(np.median(resid[mask]-ps[mask]))
    r['U7_ps_zero_fora']=bool((ps[~mask]==0).all())

    # B2 — warnings
    aw=sum(d.get('acqf_warnings',0) for d in dec)
    awrec=sum(x.get('n',0) for x in tw)
    hs=[d for d in dec if d['caminho']=='hard_stop']
    hs_it=hs[0]['it'] if hs else None
    aw_hs=sum(x.get('n',0) for x in tw if x['it']==hs_it)
    r['warn_dec']=aw; r['warn_rec']=awrec; r['warn_no_hardstop']=aw_hs
    r['warn_fecha_c_hs']= (aw + aw_hs == awrec)

    # B3 — n_baseline==0 vs dominância do ref
    ref=np.array(hdr['acqf_ref_f'],float)           # ref em espaço de MINIMIZAÇÃO
    F=real[fc].values.astype(np.float64)
    dom=(F < ref).all(axis=1)                        # pontos DENTRO da caixa do ref
    r['n_dentro_ref']=int(dom.sum()); r['frac_dentro_ref']=float(dom.mean())
    nb=np.array([d['n_baseline'] for d in dec],float)
    r['nb_zero']=int((nb==0).sum()); r['nb_zero_frac']=float((nb==0).mean())
    r['nb_max']=float(nb.max())
    # primeira iteração com nb>0 e primeiro FE dentro do ref
    idx=np.where(nb>0)[0]
    r['it_1o_nb_pos']=int(idx[0]+1) if len(idx) else -1
    idx2=np.where(dom)[0]
    r['fe_1o_dentro_ref']=int(idx2[0]) if len(idx2) else -1
    n_front1=np.array([d['n_front1'] for d in dec],float)
    r['nb_ge_front1']=int((nb>=n_front1).sum()); r['nb_lt_front1']=int((nb<n_front1).sum())

    # B4 — posição do escolhido + identidade x
    sur=pd.read_parquet(f'{b}/{s}__surrogate.parquet')
    on=sur[sur.regime=='online']
    pos=[];
    for g,sub in on.groupby('geracao'):
        i=np.where(sub['real_solution_id'].notna().values)[0]
        pos.append(int(i[0]) if len(i)==1 else -1)
    cp=collections.Counter(pos)
    r['pos_escolhido_hist']=json.dumps(dict(cp))
    r['pos_sempre_9']=int(cp.get(9,0)); r['pos_menos1']=int(cp.get(-1,0)); r['pos_tot']=len(pos)
    sel=on[on.real_solution_id.notna()]
    sid=sel.real_solution_id.astype(int).values
    xr=real.set_index('solution_id').loc[sid,xc].values
    r['x3_x1_maxabs']=float(np.abs(xr-sel[xc].values).max())
    r['x3_x1_n']=len(sel)

    # B5 — determinismo do refit
    ls=np.array([[o['lengthscale_med'] for o in d['modelo_hp']['por_objetivo']] for d in dec])
    same=np.array([np.array_equal(ls[i],ls[i+1]) for i in range(len(ls)-1)])
    ch=np.array([bool(d.get('cache_hit',False)) for d in dec])
    ch_next=ch[1:]
    r['refit_pares']=int(len(same)); r['refit_iguais']=int(same.sum())
    r['refit_iguais_eq_cachehit']=bool(np.array_equal(same, ch_next))
    r['refit_ch_next']=int(ch_next.sum())
    # também outputscale/noise idênticos nesses pares
    if same.sum():
        os_=np.array([[o['outputscale'] for o in d['modelo_hp']['por_objetivo']] for d in dec])
        mll=np.array([d['modelo_hp']['mll_final'] for d in dec])
        k=np.where(same)[0]
        r['refit_mll_iguais']=int(sum(1 for i in k if mll[i]==mll[i+1]))
        r['refit_os_iguais']=int(sum(1 for i in k if np.array_equal(os_[i],os_[i+1])))
    else:
        r['refit_mll_iguais']=0; r['refit_os_iguais']=0

    # B10 — paisagem
    sp=np.array([np.ptp(d['acqf_todos_restarts']) for d in dec])
    r['acqf_spread_med']=float(np.median(sp)); r['acqf_spread_p90']=float(np.percentile(sp,90))
    r['acqf_spread_zero']=int((sp==0).sum())
    r['acqf_esc_ini']=float(dec[0]['acqf_escolhido']); r['acqf_esc_fim']=float(dec[-1]['acqf_escolhido'])

    # B9 — cache-hit detalhe
    chd=[d for d in dec if d.get('cache_hit')]
    if chd:
        sids=sorted(set(d['solution_id'] for d in chd))
        for sid_ in sids:
            xx=real.loc[real.solution_id==sid_, xc].values[0]
            det_ch.append(dict(problema=prob, solution_id=int(sid_), n_hits=sum(1 for d in chd if d['solution_id']==sid_),
                               x_min=float(xx.min()), x_max=float(xx.max()),
                               n_coord_no_limite=int(((xx==xx.min())|(xx==xx.max())).sum()),
                               x=json.dumps([round(float(v),6) for v in xx[:12]]),
                               its=json.dumps([d['it'] for d in chd if d['solution_id']==sid_][:60])))
    rows.append(r)
    print('[ok]',prob,flush=True)

df=pd.DataFrame(rows); df.to_csv(f'{OUT}/c262_bateriaB.csv',index=False)
pd.DataFrame(det_ch).to_csv(f'{OUT}/c262_cachehits.csv',index=False)

# ---------- B6 trajetórias ----------
tr=[]
for prob in PROBS:
    j=json.load(open(f'{F5}/trajetorias/main_c262_{prob}_42.json'))
    ig=np.array([c['igd_plus'] for c in j]); hv=np.array([c['hv'] for c in j])
    d=np.diff(ig)
    tr.append(dict(problema=prob,n_ckpt=len(j),igd_ini=ig[0],igd_fim=ig[-1],
                   viol_igd=int((d>1e-12).sum()), viol_igd_rel_max=float((d/np.maximum(ig[:-1],1e-30)).max()),
                   hv_ini=hv[0],hv_fim=hv[-1],viol_hv=int((np.diff(hv)<-1e-12).sum()),
                   nd_fim=j[-1]['n_nd']))
tdf=pd.DataFrame(tr); tdf.to_csv(f'{OUT}/c262_trajetorias.csv',index=False)
print('\n== trajetórias ==\n', tdf.to_string())

# ---------- B7 sonda ----------
sn=pd.read_csv(f'{F5}/sonda_f52e.csv'); sn=sn[(sn.alg=='c262')&(sn.exp=='main')]
g=[]
for (p,o),sub in sn.groupby(['problema','obj']):
    sub=sub.sort_values('bloco')
    w0,w1=sub.wape.iloc[0],sub.wape.iloc[-1]
    g.append(dict(problema=p,obj=o,n_blocos=len(sub),wape_ini=w0,wape_fim=w1,
                  dwape=(w1-w0)/w0 if w0>0 else np.nan, wape_min=sub.wape.min(),
                  cob_ini=sub.cobertura95.iloc[0],cob_fim=sub.cobertura95.iloc[-1],
                  cob_med=sub.cobertura95.median(), corr_fim=sub['corr'].iloc[-1],
                  n_nan=int(sub.n_nan.sum())))
sdf=pd.DataFrame(g); sdf.to_csv(f'{OUT}/c262_sonda.csv',index=False)
print('\n== sonda ==\n', sdf.to_string())

# ---------- B8 posição vs pisos/rivais ----------
m=pd.read_csv(f'{F5}/metricas_finais_f52c.csv'); m=m[m.exp=='main']
PIS=['moead','nsga2','nsga3','smsemoa']
SA=[a for a in sorted(m.alg.unique()) if a not in PIS]
out=[]
for p in PROBS:
    sub=m[m.problema==p]
    me=sub[sub.alg=='c262']
    if me.empty: continue
    ig=float(me.igd_plus.iloc[0]); hv=float(me.hv.iloc[0])
    pis=sub[sub.alg.isin(PIS)]
    best_p=pis.igd_plus.min(); who=pis.loc[pis.igd_plus.idxmin(),'alg'] if len(pis) else None
    sas=sub[sub.alg.isin(SA)].sort_values('igd_plus')
    rank=int((sas.igd_plus.values<ig).sum())+1
    out.append(dict(problema=p, igd=ig, hv=hv, piso_melhor=best_p, piso_alg=who,
                    delta_pct=100*(ig-best_p)/best_p if best_p>0 else np.nan,
                    bate_piso=bool(ig<best_p), rank_SA=rank, n_SA=len(sas),
                    hv_piso=float(pis.loc[pis.igd_plus.idxmin(),'hv']) if len(pis) else np.nan,
                    igd_e81=float(sub[sub.alg=='e81'].igd_plus.iloc[0]) if len(sub[sub.alg=='e81']) else np.nan,
                    hv_e81=float(sub[sub.alg=='e81'].hv.iloc[0]) if len(sub[sub.alg=='e81']) else np.nan,
                    igd_c154=float(sub[sub.alg=='c154'].igd_plus.iloc[0]) if len(sub[sub.alg=='c154']) else np.nan,
                    igd_b3=float(sub[sub.alg=='b3'].igd_plus.iloc[0]) if len(sub[sub.alg=='b3']) else np.nan,
                    igd_b1=float(sub[sub.alg=='b1'].igd_plus.iloc[0]) if len(sub[sub.alg=='b1']) else np.nan))
odf=pd.DataFrame(out); odf.to_csv(f'{OUT}/c262_posicao.csv',index=False)
print('\n== posição ==\n', odf.to_string())
print('\nrank médio SA (21 problemas):', odf.rank_SA.mean(), ' | bate piso:', odf.bate_piso.sum(),'/',len(odf))
print('\n== B ==\n', df[['problema','U7_inv1_viol','U7_resid_ge_sonda','U7_n','warn_dec','warn_rec','warn_fecha_c_hs',
                        'nb_zero','n_dentro_ref','pos_sempre_9','pos_tot','x3_x1_maxabs','refit_iguais','refit_ch_next',
                        'refit_iguais_eq_cachehit']].to_string())
