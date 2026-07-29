"""Passo 2 da bateria b3: DoE bit-a-bit, sonda join posicional, U7 corrigido,
ledger exato (U10), fe_treino_max (U8), erro de fantasia (U11), WAPE de conferencia."""
import pandas as pd, json, numpy as np, os
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
DOE='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SND='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b3'
rows=[]
for pr in sorted(os.listdir(ROOT)):
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]
    gens=[x for x in recs if x['rec']=='b3_gen']
    guards=[x for x in recs if x['rec']=='guard']
    D,M=hdr['D'],hdr['M']
    xc=[f'x{j}' for j in range(D)]; fc=[f'f{j}' for j in range(M)]
    muc=[f'mu_{j}' for j in range(M)]; sgc=[f'sigma_{j}' for j in range(M)]
    r=pd.read_parquet(b+'__real.parquet'); t=pd.read_parquet(b+'__timing.parquet')
    s=pd.read_parquet(b+'__surrogate.parquet'); so=s[s.regime=='sonda']; on=s[s.regime=='online'].reset_index(drop=True)
    d=dict(problema=pr,D=D,M=M)
    # U2 DoE bit-a-bit
    dq=pd.read_parquet(f'{DOE}/{pr}/doe_{pr}_42.parquet')
    dx=dq[[c for c in dq.columns if c.startswith('x')]].to_numpy()
    ini=r[r.fase=='init']
    d['U2_doe_n']=len(dq); d['U2_dX_f32']=float(np.abs(dx[:len(ini)].astype(np.float32)-ini[xc].to_numpy()).max())
    dm=json.load(open(f'{DOE}/{pr}/doe_{pr}_42.manifest.json'))
    hk=[k for k in dm if 'hash' in k]
    d['U2_hash_ok']=any(dm[k]==m['doe_hash'] for k in hk); d['U2_hash_keys']=str(hk)
    # U5 sonda join posicional
    gab=pd.read_parquet(f'{SND}/sonda_{pr}.parquet')
    gx=gab[xc].to_numpy()[:2000]; gf=gab[fc].to_numpy()[:2000]
    sgl=sorted(m['sonda']['geracoes']); mx=0.0
    for ge in sgl:
        blk=so[so.geracao==ge]
        mx=max(mx,float(np.abs(blk[xc].to_numpy()-gx.astype(np.float32)).max()))
    d['U5_dX']=mx
    # U6 WAPE de conferencia (1o e ultimo bloco, espaco cru)
    for tag,ge in [('p',sgl[0]),('u',sgl[-1])]:
        blk=so[so.geracao==ge]
        mu=blk[muc].to_numpy(); sg=blk[sgc].to_numpy()
        w=[float(np.abs(mu[:,j]-gf[:,j]).sum()/np.abs(gf[:,j]).sum()) for j in range(M)]
        cov=[float((np.abs(mu[:,j]-gf[:,j])<=1.96*sg[:,j]).mean()) for j in range(M)]
        cr=[float(np.corrcoef(mu[:,j],gf[:,j])[0,1]) for j in range(M)]
        d[f'U6_wape_{tag}']=float(np.mean(w)); d[f'U6_cov_{tag}']=float(np.mean(cov)); d[f'U6_corr_{tag}']=float(np.mean(cr))
    d['U6_dWAPE_pct']=round(100*(d['U6_wape_u']/d['U6_wape_p']-1),1)
    # U7 corrigido
    v1=((t.tempo_fit_s+t.tempo_busca_s)>t.tempo_geracao_s).sum()
    mask=(t.tempo_fit_s+t.tempo_busca_s+t.tempo_pred_sonda_s)>t.tempo_geracao_s+1e-9
    d['U7_v_fitbusca']=int(v1); d['U7_v_comsonda']=int(mask.sum())
    d['U7_set_eq_sonda']=bool(set(t.geracao[mask].tolist())==set(sgl))
    d['U7_sonda_gt0_eq']=bool(set(t.geracao[t.tempo_pred_sonda_s>0].tolist())==set(sgl))
    # U8 fe_treino_max = fe do ciclo anterior - 1
    fes=np.array([g['fe'] for g in gens]); lote=np.array([g['lote'] for g in gens])
    uef=np.array([g['u_efetivo'] for g in gens]); ftm=np.array([g['fe_treino_max'] for g in gens])
    feprev=np.concatenate([[len(ini)],fes[:-1]])
    d['U8_ftm_id']=int((ftm==feprev-1).sum()); d['U8_n']=len(gens)
    d['U8_mono']=bool((np.diff(ftm)>=0).all()); d['U8_diffs']=str(sorted(set(np.diff(ftm).tolist())))
    # U10 ledger
    d['U10_sum_lote']=int(lote.sum()); d['U10_ok_orc']=bool(len(ini)+lote.sum()==m['maxfe'])
    d['U10_sum_uef']=int(uef.sum()); d['U10_gap']=int(uef.sum()-lote.sum())
    ch=sum(1 for g in guards if g['name']=='cache_hit'); hs=sum(1 for g in guards if g['name']=='hard_stop')
    d['U10_cache']=ch; d['U10_hardstop']=hs
    d['U10_c0']=int(guards[0]['name']=='cache_hit' and guards[0]['fe']==1)
    d['U10_lote_lt5']=int((lote<5).sum()); d['U10_lote_last']=int(lote[-1])
    d['U10_ident']=int(uef.sum()-lote.sum()-(ch-1))   # gap - (cache pos-init)
    # U11 erro de fantasia (mu do selecionado vs f real), por objetivo, mediana e sinal
    errs=[]; sig=[]
    for g in gens:
        ge=g['geracao']; blk=on[on.geracao==ge]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True)
        idx=[i-1 for i in g['index']]
        fe0=g['fe']-g['lote']; newr=r[(r.fe_index>=fe0)&(r.fe_index<g['fe'])]
        n=min(len(newr),len(idx))
        if n==0: continue
        sel=last.iloc[idx[:n]]
        e=sel[muc].to_numpy()-newr[fc].to_numpy()[:n]
        den=np.abs(newr[fc].to_numpy()[:n]).mean(0); den[den==0]=1
        errs.append(np.abs(e).mean(0)/den); sig.append((e<0).mean())
    d['U11_relerr_med']=float(np.median(np.concatenate([x for x in errs]))) if errs else np.nan
    d['U11_frac_otimista']=float(np.mean(sig)) if sig else np.nan
    rows.append(d); print('OK',pr,flush=True)
df=pd.DataFrame(rows); df.to_csv(OUT+'/b3_p2.csv',index=False)
pd.set_option('display.width',400); pd.set_option('display.max_columns',60)
print(df.to_string())
