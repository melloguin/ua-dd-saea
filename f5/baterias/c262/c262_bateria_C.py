#!/usr/bin/env python
"""
BATERIA C — c262 qNEHVI: fechamentos finos. READ-ONLY nos dados.
  C1 prune_baseline: n_baseline>0 ⟺ ∃ ponto do TREINO estritamente dentro da caixa do ref (S.5), POR ITERAÇÃO
  C2 determinismo do refit (índice correto): pares idênticos ⟺ iteração i foi cache-hit
  C3 contabilidade de tempo: Σ④ vs manifesto; onde vive a sonda
  C4 acqf_warnings: fechamento com a iteração hard_stop
  C5 ② off-by-one e passo por geração (0 nas gerações de cache-hit / hard_stop)
  C6 sinal: μ do escolhido vs f real (dupla-negação ausente) + faixa de σ
"""
import json, glob, os, collections
import numpy as np, pandas as pd

ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c262'
PROBS=sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))
rows=[]
for prob in PROBS:
    b=f'{ROOT}/{prob}/42'; s=f'exp_main_c262_{prob}_42'
    man=json.load(open(f'{b}/{s}.manifest.json'))
    recs=[json.loads(l) for l in open(f'{b}/{s}.jsonl') if l.strip()]
    by=collections.defaultdict(list)
    for x in recs: by[x.get('rec')].append(x)
    hdr=by['header'][0]; dec=by['decision']; snd=by['sonda']; tw=by['optimize_acqf_warning']
    D=hdr['D']; M=hdr['M']; ng=man['n_geracoes']
    real=pd.read_parquet(f'{b}/{s}__real.parquet')
    tim=pd.read_parquet(f'{b}/{s}__timing.parquet')
    pop=pd.read_parquet(f'{b}/{s}__pop.parquet')
    fc=[f'f{j}' for j in range(M)]
    F=real.sort_values('fe_index')[fc].values.astype(np.float64)
    ref=np.array(hdr['acqf_ref_f'],float)
    dentro=(F<ref).all(axis=1)                 # ponto dentro da caixa (minimização)
    cum=np.cumsum(dentro)                       # nº de in-box até fe_index k
    r={'problema':prob,'D':D,'M':M,'n_ger':ng}

    # C1 — por iteração
    ok=0; tot=0; mismatch=[]
    for d in dec:
        nb=d['n_baseline']
        nt=d.get('n_train')
        if nt is None:      # hard_stop: treina em tudo
            nt=man['fe_final']
        ndentro=int(cum[nt-1])
        tot+=1
        pred = ndentro>0
        if pred == (nb>0): ok+=1
        else: mismatch.append((d['it'], nb, ndentro))
    r['C1_ok']=ok; r['C1_tot']=tot; r['C1_mismatch']=json.dumps(mismatch[:6])
    r['C1_n_mismatch']=len(mismatch)

    # C2 — determinismo do refit
    ls=np.array([[o['lengthscale_med'] for o in d['modelo_hp']['por_objetivo']]+
                 [o['outputscale'] for o in d['modelo_hp']['por_objetivo']]+
                 [d['modelo_hp']['mll_final']] for d in dec])
    same=np.array([np.array_equal(ls[i],ls[i+1]) for i in range(len(ls)-1)])
    ch=np.array([bool(d.get('cache_hit',False)) for d in dec])[:-1]
    r['C2_pares']=len(same); r['C2_iguais']=int(same.sum()); r['C2_ch']=int(ch.sum())
    r['C2_identidade']=bool(np.array_equal(same,ch))

    # C3 — contabilidade de tempo
    r['C3_sum_ger']=float(tim['tempo_geracao_s'].sum())
    r['C3_sum_fit']=float(tim['tempo_fit_s'].sum()); r['C3_sum_busca']=float(tim['tempo_busca_s'].sum())
    r['C3_sum_sonda']=float(tim['tempo_pred_sonda_s'].sum())
    t=man['timing']
    r['C3_man_total']=t['tempo_total_s']; r['C3_man_fit']=t['tempo_fit_surrogate_s']
    r['C3_man_busca']=t['tempo_busca_s']; r['C3_man_sonda']=t['tempo_pred_sonda_s']
    r['C3_man_aval']=t['tempo_aval_real_s']; r['C3_man_desp']=t['tempo_total_despachante_s']
    r['C3_fit_bate']=abs(r['C3_sum_fit']-t['tempo_fit_surrogate_s'])/max(t['tempo_fit_surrogate_s'],1e-9)
    r['C3_busca_bate']=abs(r['C3_sum_busca']-t['tempo_busca_s'])/max(t['tempo_busca_s'],1e-9)
    r['C3_sonda_bate']=abs(r['C3_sum_sonda']-t['tempo_pred_sonda_s'])/max(t['tempo_pred_sonda_s'],1e-9)
    r['C3_ger_menos_fb']=float((tim['tempo_geracao_s']-tim['tempo_fit_s']-tim['tempo_busca_s']).sum())
    r['C3_sobra_total']=t['tempo_total_s']-r['C3_sum_ger']-r['C3_sum_sonda']
    r['C3_sobra_pct']=100*r['C3_sobra_total']/t['tempo_total_s']

    # C4 — warnings
    aw=sum(d.get('acqf_warnings',0) for d in dec)
    hs=[d for d in dec if d['caminho']=='hard_stop'][0]
    aw_hs=sum(x.get('n',0) for x in tw if x['it']==hs['it'])
    r['C4_dec']=aw; r['C4_rec']=sum(x.get('n',0) for x in tw); r['C4_hs']=aw_hs
    r['C4_fecha']=(aw+aw_hs==r['C4_rec'])
    r['C4_iters_com_warn']=len(set(x['it'] for x in tw))

    # C5 — ② off-by-one + passo
    gs=pop.groupby('geracao').size()
    r['C5_n_ger_pop']=len(gs); r['C5_igual_ng_mais1']=(len(gs)==ng+1)
    dif=np.diff(gs.values)
    r['C5_passos_1']=int((dif==1).sum()); r['C5_passos_0']=int((dif==0).sum())
    r['C5_passos_outros']=int(((dif!=0)&(dif!=1)).sum())
    r['C5_esperado_0']=int(sum(1 for d in dec if d.get('cache_hit')) + 1)   # cache-hits + hard_stop
    r['C5_g0']=int(gs.iloc[0]); r['C5_glast']=int(gs.iloc[-1])

    # C6 — sinal (μ vs f) e σ
    sur=pd.read_parquet(f'{b}/{s}__surrogate.parquet')
    on=sur[sur.regime=='online']; sel=on[on.real_solution_id.notna()]
    sid=sel.real_solution_id.astype(int).values
    fr=real.set_index('solution_id').loc[sid,fc].values.astype(np.float64)
    mu=sel[[f'mu_{j}' for j in range(M)]].values.astype(np.float64)
    sg=sel[[f'sigma_{j}' for j in range(M)]].values.astype(np.float64)
    r['C6_sinal_corr']=json.dumps([round(float(np.corrcoef(mu[:,j],fr[:,j])[0,1]),5) for j in range(M)])
    r['C6_mu_medio']=json.dumps([round(float(mu[:,j].mean()),4) for j in range(M)])
    r['C6_f_medio']=json.dumps([round(float(fr[:,j].mean()),4) for j in range(M)])
    r['C6_sigma_med']=json.dumps([round(float(np.median(sg[:,j])),6) for j in range(M)])
    r['C6_sigma_ini']=json.dumps([round(float(sg[0,j]),6) for j in range(M)])
    r['C6_sigma_fim']=json.dumps([round(float(sg[-1,j]),6) for j in range(M)])
    rows.append(r); print('[ok]',prob,flush=True)

df=pd.DataFrame(rows); df.to_csv(f'{OUT}/c262_bateriaC.csv',index=False)
pd.set_option('display.width',260)
print(df[['problema','C1_ok','C1_tot','C1_n_mismatch','C1_mismatch']].to_string())
print(df[['problema','C2_pares','C2_iguais','C2_ch','C2_identidade']].to_string())
print(df[['problema','C3_sum_ger','C3_sum_sonda','C3_man_total','C3_ger_menos_fb','C3_sobra_total','C3_sobra_pct',
          'C3_fit_bate','C3_busca_bate','C3_sonda_bate']].to_string())
print(df[['problema','C4_dec','C4_rec','C4_hs','C4_fecha','C4_iters_com_warn']].to_string())
print(df[['problema','C5_n_ger_pop','C5_igual_ng_mais1','C5_passos_1','C5_passos_0','C5_passos_outros','C5_esperado_0','C5_g0','C5_glast']].to_string())
print(df[['problema','C6_sinal_corr','C6_mu_medio','C6_f_medio','C6_sigma_med','C6_sigma_ini','C6_sigma_fim']].to_string())
