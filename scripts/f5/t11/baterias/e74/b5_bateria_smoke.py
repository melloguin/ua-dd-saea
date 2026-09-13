# -*- coding: utf-8 -*- READ-ONLY. Bateria universal + joias no SMOKE T11 pos-DI45 (3 celulas) e contraste s42.
import sys, json, glob
import numpy as np, pandas as pd
ROOT='/Users/gmello/Documents/python_repos/mestrado'
OUT=f'{ROOT}/ua-dd-saea/f5/t11/baterias/e74'
SM=f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_%s_42'
S42=f'{ROOT}/resultados_experimentos/e74/%s/42/exp_main_e74_%s_42'
def load(base):
    real=pd.read_parquet(base+'__real.parquet'); pop=pd.read_parquet(base+'__pop.parquet')
    sur=pd.read_parquet(base+'__surrogate.parquet'); tim=pd.read_parquet(base+'__timing.parquet')
    man=json.load(open(base+'.manifest.json')); ev=[json.loads(l) for l in open(base+'.jsonl')]
    return real,pop,sur,tim,man,ev
def bat(prob,base,tag):
    real,pop,sur,tim,man,ev=load(base)
    xc=[c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    D=len(xc); M=len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    gen=[r for r in ev if r.get('rec')=='e74_gen']; boot=[r for r in ev if r.get('rec')=='e74_boot']
    guards=[r for r in ev if r.get('rec')=='guard']; foot=[r for r in ev if r.get('rec')=='footer'][-1]
    on=sur[sur.regime=='online']; sd=sur[sur.regime=='sonda']
    o=dict(corpus=tag,problema=prob,D=D,M=M)
    o['U1_fe']= (man['fe_final']==31*D-1==man['maxfe'])
    o['U1_denso']= bool((np.sort(real.fe_index.values)==np.arange(len(real))).all())
    o['U2_init']= int((real.fase=='init').sum())==11*D-1
    o['U2_doehash']= bool(man.get('doe_hash'))
    C=len([r for r in gen if r['estrategia']==1]); ks=[r['estrategia'] for r in gen][-1]
    o['ciclos']=C; o['k']=ks
    o['U10_nger']= man['n_geracoes']==4*C-2+ks
    o['U10_eventos']= len(gen)==3*(C-1)+ks
    o['U3_timing_linhas']= len(tim)==len(gen)+len(boot)
    o['U7_viol']= int((tim.tempo_fit_s+tim.tempo_busca_s > tim.tempo_geracao_s).sum()) if set(['tempo_fit_s','tempo_busca_s','tempo_geracao_s'])<=set(tim.columns) else -1
    o['A4_rot']= (len([r for r in gen if r['estrategia']==2])==C-1+(ks>=2)) and (len([r for r in gen if r['estrategia']==3])==C-1+(ks>=3))
    o['FE_fecha']= ((11*D-1) + int(boot[0]['aceitos']) + sum(r['aceito'] for r in gen)) == man['fe_final']
    # A20 sigma NaN na sonda + A21 pred_tipo
    o['A20_sigma_nan']= float(sd.sigma_0.isna().mean()); o['A20_conf_nan']=float(sd.pred_confianca.isna().mean())
    hib=on.groupby('geracao').pred_tipo.nunique(); o['A21_hibridos']=int((hib>1).sum())
    o['A21_mu_em_pnn']= int(on[(on.modelo_flag=='PNN(s1)')].mu_0.notna().sum())
    o['A21_classe_em_rbf']= int(on[on.modelo_flag.str.startswith('RBF')].pred_classe.notna().sum())
    # U5 join posicional sonda x gabarito
    art=man['sonda']['cabecas']['s1']['artefato'].split('/')[-1]
    gab=None
    for cand in [f'{ROOT}/ua-dd-saea/data/sonda/{art}', f'{ROOT}/evidencia_T11/smoke_matlab/sonda/{art}']:
        try: gab=pd.read_parquet(cand); break
        except Exception: pass
    if gab is not None:
        gxc=[c for c in gab.columns if c.startswith('x') and c[1:].isdigit()]
        dmax=0.0; nb=0
        for (g,mf),b in sd.groupby(['geracao','modelo_flag']):
            v=np.abs(b[xc].values.astype(np.float64)-gab[gxc].values[:len(b)].astype(np.float64)).max(); dmax=max(dmax,v); nb+=1
        o['U5_maxdX']=dmax; o['U5_blocos']=nb
    # A8 joia s2
    Xr=real[xc].values.astype(np.float64)
    s2=on[on.modelo_flag=='RBF-global(s2)']; blk2={int(g):b for g,b in s2.groupby('geracao')}
    ok=tot=0; ident=0; dif=[]
    for r in gen:
        if r['estrategia']!=2 or r['aceito']!=1: continue
        b=blk2.get(int(r['geracao']));
        if b is None: continue
        s0=b.sigma_0.values.astype(np.float64)
        if np.isnan(s0).all(): continue
        pos=int(np.argmin(np.abs(b[xc].values.astype(np.float64)-Xr[r['fe']-1]).max(axis=1)))
        tot+=1; ok+= int(pos==int(np.nanargmax(s0)))
        if r.get('hv_base') is not None:
            dif.append(abs(s0[pos]-(b.pred_score.values.astype(np.float64)[pos]-r['hv_base'])))
    o['A8_argmax']=f'{ok}/{tot}'; o['A8_pct']=100*ok/tot if tot else np.nan
    o['A8_ident_max']=float(np.nanmax(dif)) if dif else np.nan
    # A11 joia s3: argmax global (assinatura) — a versao RESTRITA exige reconstrucao do front
    s3=on[on.modelo_flag=='RBF-local(s3)']; blk3={int(g):b for g,b in s3.groupby('geracao')}
    ok3=tot3=0
    for r in gen:
        if r['estrategia']!=3 or r['aceito']!=1: continue
        b=blk3.get(int(r['geracao']))
        if b is None: continue
        s0=b.sigma_0.values.astype(np.float64)
        pos=int(np.argmin(np.abs(b[xc].values.astype(np.float64)-Xr[r['fe']-1]).max(axis=1)))
        tot3+=1; ok3+= int(pos==int(np.nanargmax(s0)))
    o['A11_argmax_global']=f'{ok3}/{tot3}'; o['A11_pct_global']=100*ok3/tot3 if tot3 else np.nan
    # A28 f_best pos-FE
    err=[]
    for r in gen:
        n=r['arquivo']; F=real[[c for c in real.columns if c.startswith('f') and c[1:].isdigit()]].values[:n]
        fb=np.array(r['f_best'],float); mn=F.min(axis=0)
        err.append(np.max(np.abs(fb-mn)/np.maximum(np.abs(mn),1e-12)))
    o['A28_fbest_relmax']=float(np.max(err))
    # guards
    from collections import Counter
    o['guards']=str(dict(Counter(g['name'] for g in guards)))
    o['termino']=foot.get('termino'); o['status']=man['status']; o['cp_init']=foot.get('cp_init')
    o['tempo_aval_real_s']=man.get('timing',{}).get('tempo_aval_real_s')
    o['campanha_id']=man.get('campanha_id'); o['schema']=man.get('schema_version')
    o['tem_REGRA_DO_ROTULO']= 'REGRA_DO_ROTULO' in json.dumps(man)
    o['tem_ids']= any(k.endswith('_ids') for k in json.dumps(man).split('"'))
    return o
rows=[]
for p in ['MMF1','DTLZ2','ZDT1']:
    rows.append(bat(p,SM%p,'POS_smoke')); rows.append(bat(p,S42%(p,p),'PRE_s42'))
df=pd.DataFrame(rows); df.to_csv(f'{OUT}/bateria_smoke.csv',index=False)
pd.set_option('display.width',300); pd.set_option('display.max_columns',60)
print(df.T.to_string())
