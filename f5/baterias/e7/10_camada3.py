import json,os
import pandas as pd, numpy as np
ROOT="/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7"
REPO="/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
PROBS=sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT,d))])
out=[]
for p in PROBS:
    base=f"{ROOT}/{p}/42/exp_main_e7_{p}_42"
    man=json.load(open(base+".manifest.json")); ev=[json.loads(l) for l in open(base+".jsonl")]
    hdr=[e for e in ev if e['rec']=='header'][0]; D=hdr['D']; M=hdr['M']
    G=[e for e in ev if e['rec']=='e7_gen']; C=len(G)
    xc=[f"x{i}" for i in range(D)]; mc=[f"mu_{i}" for i in range(M)]; sc=[f"sigma_{i}" for i in range(M)]
    sur=pd.read_parquet(base+"__surrogate.parquet")
    r=dict(problema=p,D=D,M=M,n3=len(sur))
    r['n3_online']=int((sur.regime=='online').sum()); r['n3_sonda']=int((sur.regime=='sonda').sum())
    r['n3_online_esp']=1900*C; r['n3_sonda_esp']=2000*man['sonda']['n_blocos']
    S=sur[sc].to_numpy(np.float64); MU=sur[mc].to_numpy(np.float64)
    r['sigma_min']=float(S.min()); r['sigma_nan']=int(np.isnan(S).sum()); r['sigma_zero']=int((S==0).sum())
    r['mu_nan']=int(np.isnan(MU).sum())
    r['pred_tipo']=sorted(sur.pred_tipo.dropna().unique().tolist())
    r['pred_classe_null']=int(sur.pred_classe.isna().sum())==len(sur)
    r['pred_score_null']=int(sur.pred_score.isna().sum())==len(sur)
    r['pred_conf_null']=int(sur.pred_confianca.isna().sum())==len(sur)
    r['modelo_flag']=sorted(sur.modelo_flag.dropna().unique().tolist())
    r['transf_tipo']=sorted(sur.transf_tipo.dropna().unique().tolist())
    r['espaco_vals']=sorted(sur.espaco_modelo.dropna().unique().tolist())
    # espaco_modelo por geracao: 1 = cru, resto = transformado (nos DOIS regimes)
    ok=0; tot=0; tp_ok=0
    for gg,b in sur.groupby(['regime','geracao']):
        tot+=1
        esp=set(b.espaco_modelo.unique())
        ok+= (esp=={'cru'} if gg[1]==1 else esp=={'transformado'})
        tp=set(b.transf_params.unique()); tp_ok+= (len(tp)==1)
    r['espaco_por_ger_ok']=ok; r['espaco_por_ger_n']=tot; r['transfparams_unico_por_ger']=tp_ok
    # transf_params(③) == ymin(⑥) por ciclo (online e sonda)
    ymin_by_c={g['geracao']:np.array(g['ymin'],float) for g in G}
    err=0.0; nchk=0; nfail=0
    for gg,b in sur.groupby(['regime','geracao']):
        c=gg[1]
        tp=json.loads(b.transf_params.iloc[0])['ymin']
        # a sonda do ciclo c usa o ymin do ciclo c (modelo do ciclo)
        if c in ymin_by_c:
            e=float(np.max(np.abs(np.array(tp,float)-ymin_by_c[c]))); err=max(err,e); nchk+=1
            nfail+= (e>1e-12)
    r['tp_vs_ymin_err']=err; r['tp_vs_ymin_n']=nchk; r['tp_vs_ymin_fail']=nfail
    # fe_treino_max na ③ (por ciclo) == 11D-1+3(c-1)-1
    ftm_ok=0; ftm_n=0
    for gg,b in sur.groupby(['regime','geracao']):
        c=gg[1]; ftm_n+=1
        ftm_ok+= (set(b.fe_treino_max.unique())=={11*D-1+3*(c-1)-1})
    r['ftm3_ok']=ftm_ok; r['ftm3_n']=ftm_n
    # U5: join posicional sonda x gabarito
    gab=pd.read_parquet(f"{REPO}/data/sonda/sonda_{p}.parquet")
    gxc=[c2 for c2 in gab.columns if c2.startswith('x')][:D]
    Xg=gab[gxc].to_numpy(np.float64)[:2000]
    snd=sur[sur.regime=='sonda']
    dmax=0.0; nb=0
    for c,b in snd.groupby('geracao'):
        Xs=b[xc].to_numpy(np.float64)
        dmax=max(dmax,float(np.max(np.abs(Xs-Xg)))); nb+=1
    r['U5_dX_max']=dmax; r['U5_blocos']=nb
    # X da busca dentro dos bounds do problema (usa min/max do gabarito como proxy dos bounds)
    on=sur[sur.regime=='online']
    lo=Xg.min(axis=0); hi=Xg.max(axis=0)
    Xo=on[xc].to_numpy(np.float64)
    r['X_fora_bounds']=int(((Xo<lo-1e-6)|(Xo>hi+1e-6)).sum())
    r['X_min']=float(Xo.min()); r['X_max']=float(Xo.max())
    out.append(r); print("ok",p,flush=True)
    del sur
df=pd.DataFrame(out); df.to_csv("camada3_e7.csv",index=False)
pd.set_option('display.width',300)
print(df[['problema','n3','n3_online','n3_online_esp','n3_sonda','n3_sonda_esp','sigma_min','sigma_nan','sigma_zero','mu_nan','espaco_por_ger_ok','espaco_por_ger_n','tp_vs_ymin_err','tp_vs_ymin_fail','ftm3_ok','ftm3_n','U5_dX_max','U5_blocos','X_fora_bounds']].to_string())
print("\nTOT ③:",df.n3.sum(),"online",df.n3_online.sum(),"==",df.n3_online_esp.sum(),"| sonda",df.n3_sonda.sum(),"==",df.n3_sonda_esp.sum())
print("sigma min global:",df.sigma_min.min(),"NaN",df.sigma_nan.sum(),"zeros",df.sigma_zero.sum(),"| mu NaN",df.mu_nan.sum())
print("pred_tipo:",set(map(str,df.pred_tipo)),"| classe/score/conf NULL 100%:",df.pred_classe_null.sum(),df.pred_score_null.sum(),df.pred_conf_null.sum())
print("modelo_flag:",set(map(str,df.modelo_flag)),"| transf_tipo:",set(map(str,df.transf_tipo)))
print("espaco por ger:",df.espaco_por_ger_ok.sum(),"/",df.espaco_por_ger_n.sum(),"| transf_params unico/ger:",df.transfparams_unico_por_ger.sum())
print("transf_params == ymin(⑥):",df.tp_vs_ymin_n.sum()-df.tp_vs_ymin_fail.sum(),"/",df.tp_vs_ymin_n.sum(),"err max",df.tp_vs_ymin_err.max())
print("fe_treino_max(③):",df.ftm3_ok.sum(),"/",df.ftm3_n.sum())
print("U5 dX max:",df.U5_dX_max.max(),"em",df.U5_blocos.sum(),"blocos | X fora bounds:",df.X_fora_bounds.sum())
