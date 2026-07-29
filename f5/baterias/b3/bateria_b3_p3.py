"""Passo 3 b3: query-joia com tolerancia RELATIVA, ledger exato X(selecionado)->(1),
cadencia da sonda (formula fechada), rsid do (3) online, ledger de FE/cache."""
import pandas as pd, json, numpy as np, os
ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b3'
rows=[]; det=[]
for pr in sorted(os.listdir(ROOT)):
    b=f'{ROOT}/{pr}/42/exp_main_b3_{pr}_42'
    m=json.load(open(b+'.manifest.json'))
    recs=[json.loads(l) for l in open(b+'.jsonl') if l.strip()]
    hdr=[x for x in recs if x['rec']=='header'][0]
    gens=[x for x in recs if x['rec']=='b3_gen']; guards=[x for x in recs if x['rec']=='guard']
    D,M=hdr['D'],hdr['M']
    xc=[f'x{j}' for j in range(D)]; fc=[f'f{j}' for j in range(M)]
    muc=[f'mu_{j}' for j in range(M)]; sgc=[f'sigma_{j}' for j in range(M)]
    r=pd.read_parquet(b+'__real.parquet'); s=pd.read_parquet(b+'__surrogate.parquet')
    on=s[s.regime=='online'].reset_index(drop=True)
    d=dict(problema=pr,D=D,M=M)
    RX=r[xc].to_numpy(); key={}
    for i in range(len(RX)): key[RX[i].tobytes()]=i
    nsig=0; nsig_rel=0; nx_new=0; nx_old=0; nx_miss=0; msigrel=0.0; nsel=0
    n_cyc_x_ok=0; ncic=len(gens)
    ferr=[]; sgn=[]
    for g in gens:
        ge=g['geracao']; blk=on[on.geracao==ge]; ln=g['pop_por_w'][-1]
        last=blk.iloc[len(blk)-ln:].reset_index(drop=True)
        idx=[i-1 for i in g['index']]
        sel=last.iloc[idx]
        got=sel[sgc].to_numpy().astype(np.float64); exp=np.array(g['sigma_sel']['sqrtmse_por_objetivo'])
        rel=np.abs(got-exp)/np.maximum(np.abs(exp),1e-300)
        msigrel=max(msigrel,float(rel.max())); nsig+= int((rel<1e-6).all()); nsig_rel+=int((rel<1e-5).all())
        # ledger X: cada selecionado tem de existir na (1); novo (fe no ciclo) ou antigo (cache hit)
        fe0=g['fe']-5; ok=0
        SX=sel[xc].to_numpy()
        for i in range(len(SX)):
            j=key.get(SX[i].tobytes())
            if j is None: nx_miss+=1
            elif fe0<=j<g['fe']: nx_new+=1; ok+=1
            else: nx_old+=1; ok+=1
        nsel+=len(SX); n_cyc_x_ok+= int(ok==len(SX))
        # erro de fantasia so nos NOVOS
        for i in range(len(SX)):
            j=key.get(SX[i].tobytes())
            if j is not None and fe0<=j<g['fe']:
                fr=r[fc].to_numpy()[j]; mu=sel[muc].to_numpy()[i]
                den=np.maximum(np.abs(fr),1e-12)
                ferr.append(float(np.median(np.abs(mu-fr)/den))); sgn.append(float((mu<fr).mean()))
    d['J_ncic']=ncic; d['J_nsel']=nsel
    d['J_sig_rel1e6']=nsig; d['J_sig_rel1e5']=nsig_rel; d['J_sig_maxrel']=msigrel
    d['J_X_new']=nx_new; d['J_X_old']=nx_old; d['J_X_miss']=nx_miss; d['J_cyc_ok']=n_cyc_x_ok
    d['J_X_old_vs_cache']=nx_old
    d['U11_relerr_med']=float(np.median(ferr)) if ferr else np.nan
    d['U11_otimista']=float(np.mean(sgn)) if sgn else np.nan
    # ledger FE
    fes=np.array([g['fe'] for g in gens]); ini=11*D-1
    dif=np.diff(np.concatenate([[ini],fes]))
    ch=[x['fe'] for x in guards if x['name']=='cache_hit']; hs=[x for x in guards if x['name']=='hard_stop']
    d['L_sum_dfe']=int(dif.sum()); d['L_5n']=5*ncic; d['L_cache_tot']=len(ch)
    d['L_cache_init']=sum(1 for f in ch if f<=ini); d['L_cache_opt_cic']=int(5*ncic-dif.sum())
    d['L_ident']=bool(5*ncic-dif.sum()==sum(1 for f in ch if ini<f<=fes[-1]))
    d['L_fe_last_cic']=int(fes[-1]); d['L_maxfe']=m['maxfe']; d['L_resto']=int(m['maxfe']-fes[-1])
    d['L_hardstop']=len(hs); d['L_resto_le4']=bool(0<=m['maxfe']-fes[-1]<=4)
    d['L_hs_iff_resto']=bool((len(hs)>0)==(m['maxfe']-fes[-1]>0))
    # cadencia sonda
    G=ncic+(1 if len(hs)>0 else 0)
    sgl=sorted(m['sonda']['geracoes'])
    esp=sorted(set([1]+[x for x in range(2,G+1) if x%2==0]+[G]))
    d['S_G']=G; d['S_nb']=len(sgl); d['S_formula_ok']=bool(sgl==esp)
    d['S_last']=sgl[-1]; d['S_last_eq_G']=bool(sgl[-1]==G)
    d['S_finalprobe_impar']=bool(G%2==1)
    # rsid do (3) online: onde aparece
    rs=on.real_solution_id.notna().to_numpy()
    d['R_rsid_nn']=int(rs.sum()); d['R_online_rows']=len(on)
    # por bloco w
    posw=[]
    for g in gens:
        ge=g['geracao']; blkidx=np.where(on.geracao.to_numpy()==ge)[0]
        off=0
        for w,n in enumerate(g['pop_por_w']):
            seg=rs[blkidx[off:off+n]]; posw.append((w+1,seg.sum(),n)); off+=n
    pw=pd.DataFrame(posw,columns=['w','nn','n']).groupby('w').sum()
    d['R_frac_w1']=float(pw.loc[1,'nn']/pw.loc[1,'n']); d['R_frac_w20']=float(pw.loc[20,'nn']/pw.loc[20,'n'])
    d['R_frac_tot']=float(pw.nn.sum()/pw.n.sum())
    rows.append(d); print('OK',pr,flush=True)
df=pd.DataFrame(rows); df.to_csv(OUT+'/b3_p3.csv',index=False)
pd.set_option('display.width',420); pd.set_option('display.max_columns',60)
print(df.to_string())
