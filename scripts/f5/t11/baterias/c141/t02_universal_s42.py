"""T11/c141 · re-medicao da bateria universal nas 25 celulas da s42 (READ-ONLY)."""
import sys, json, os, glob
sys.path.insert(0,'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
import numpy as np, pandas as pd
from lib_c141 import load, ROOT

PBS=sorted(os.listdir(ROOT))
rows=[]
for pb in PBS:
    if pb.startswith('.'): continue
    man,ev,real,pop,sur,tim = load(pb)
    D = len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])
    M = len([c for c in real.columns if c.startswith('f') and c[1:].isdigit()])
    gen=[e for e in ev if e.get('rec')=='c141_gen']
    snd=[e for e in ev if e.get('rec')=='sonda']
    guards=[e for e in ev if e.get('rec')=='guard']
    hdr=[e for e in ev if e.get('rec')=='header']; ftr=[e for e in ev if e.get('rec')=='footer']
    so=sur[sur.regime=='online']; ss=sur[sur.regime=='sonda']
    lote=np.array([g['lote'] for g in gen])
    N=man['params']['N_subpop']
    # U1 orcamento
    fe_ok = (man['maxfe']==31*D-1==man['fe_final']==len(real))
    dense = bool((real.fe_index.values==np.arange(len(real))).all())
    # U2 DoE
    init=int((real.fase=='init').sum())
    # U3 retreino
    u3 = (len(gen)==len(tim)==len(man['fit_series']))
    # U4 sonda
    blocos = ss.groupby(ss.geracao).size() if len(ss) else pd.Series(dtype=int)
    b2000 = bool((blocos==2000).all()) and len(blocos)==man['sonda']['n_blocos']
    # U6 timing
    viol=int(((tim.tempo_fit_s+tim.tempo_busca_s-tim.tempo_geracao_s)>1e-6).sum())
    # U7 fe_treino_max monotonico
    ftm=so.groupby('geracao').fe_treino_max.first().values
    mono=bool((np.diff(ftm)>=0).all())
    # U8 guards
    from collections import Counter
    gc=Counter(g.get('name') for g in guards)
    ch=gc.get('cache_hit',0); hs=gc.get('hard_stop',0)
    ch_ok = (ch==man['cache_hits'])
    # c0=1: cache-hit no init
    ch_init=sum(1 for g in guards if g.get('name')=='cache_hit' and g.get('fe',10**9)<=init)
    # U9 ledger
    lote_final = man['fe_final']-(init+int(lote.sum())-ch)
    ledger = (init+int(lote.sum())-ch+lote_final==man['fe_final'])
    # C1 N
    c1 = (N==min(100,11*D-1))
    # C2 bipop
    c2 = all(g['n_por_nivel']['entrada']==2*N for g in gen) and bool((so.groupby('geracao').size()==2*N).all())
    # C3 u=5
    lote_gt5=int((lote>5).sum()); lote0=int((lote==0).sum())
    n2=[g for g in gen if g.get('nivel_saida')==2]
    n2_front1=sum(1 for g in n2 if g.get('n_front2')==1)
    # F7 sigma_0 teto
    s0=so.sigma_0.values
    teto=2*(2*N-1)
    f7 = (np.nanmax(s0)==teto) and bool(np.all(np.equal(np.mod(s0,1),0)))
    # F9 papel da incerteza -> via ⑥? usar b04 anterior; aqui so registra
    rows.append(dict(pb=pb,D=D,M=M,N=N,maxfe=man['maxfe'],fe=man['fe_final'],init=init,
        n_gen=len(gen),n_ger_man=man['n_geracoes'],U1=fe_ok,dense=dense,U2=(init==11*D-1),
        U3=u3,blocos=len(blocos),U4=b2000,U6_viol=viol,U7_mono=mono,
        cache=ch,cache_ok=ch_ok,ch_init=ch_init,hard=hs,U9=ledger,lote_final=lote_final,
        C1=c1,C2=c2,lote_gt5=lote_gt5,lote0=lote0,n_saida2=len(n2),n_saida2_f1=n2_front1,
        F7_teto=f7,teto=teto,s0max=float(np.nanmax(s0)),
        s0_nan=int(np.isnan(so.sigma_0.values).sum()),s1_nan=int(np.isnan(so.sigma_1.values).sum()),
        n_online=len(so),n_sonda=len(ss),n_ev=len(ev),
        hdr=len(hdr),ftr=len(ftr),termino=(ftr[0].get('termino') if ftr else None),
        status=man['status'],
        schema=man.get('schema_version'),campanha=man.get('campanha_id'),repo=man.get('repo_hash'),
        t_aval=man['timing'].get('tempo_aval_real_s'),
        desligada=man['sonda'].get('desligada','AUSENTE'),
        params_ok=('params' in man), sigma_ok=('sigma_dict' in man),
        regra_rotulo=('REGRA_DO_ROTULO' in man), estrat=int((sur.regime=='sonda_estratificada').sum()),
        ))
df=pd.DataFrame(rows)
df.to_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c141/t02_universal_s42.csv',index=False)
pd.set_option('display.width',250)
print(df[['pb','D','N','maxfe','fe','init','n_gen','n_ger_man','U1','U2','U3','blocos','U4','U6_viol','U7_mono','cache','ch_init','hard','U9','lote_final','C1','C2','F7_teto','teto','s0max']].to_string())
print()
print('=== agregados 25 celulas ===')
for c in ['U1','U2','U3','U4','U7_mono','U9','C1','C2','F7_teto','dense','params_ok','sigma_ok']:
    print(' %-10s %d/%d'%(c,int(df[c].sum()),len(df)))
print(' U6 violacoes totais %d ; ciclos %d'%(df.U6_viol.sum(),df.n_gen.sum()))
print(' cache total %d ; cache no init %d/%d celulas com exatamente 1'%(df.cache.sum(),int((df.ch_init==1).sum()),len(df)))
print(' hard_stop %d celulas ; lote>5 %d ciclos ; lote==0 %d ; saidas nivel2 %d (todas n_front2==1: %s)'%(
    int((df.hard>0).sum()),df.lote_gt5.sum(),df.lote0.sum(),df.n_saida2.sum(),df.n_saida2.sum()==df.n_saida2_f1.sum()))
print(' online rows %d ; sonda rows %d ; blocos %d ; eventos %d'%(df.n_online.sum(),df.n_sonda.sum(),df.blocos.sum(),df.n_ev.sum()))
print(' sigma_0 NaN %d ; sigma_1 NaN %d'%(df.s0_nan.sum(),df.s1_nan.sum()))
print(' n_ger_man == n_gen+1 em %d/%d'%(int((df.n_ger_man==df.n_gen+1).sum()),len(df)))
print(' termino:',df.termino.value_counts().to_dict(),' status:',df.status.value_counts().to_dict())
print('=== campos T11 na s42 ===')
print(' schema_version:',df.schema.value_counts().to_dict())
print(' campanha_id nao-nulo:',int(df.campanha.notna().sum()),'/25')
print(' repo_hash preenchido:',int((df.repo.astype(str).str.len()>0).sum()),'/25')
print(' tempo_aval_real_s nao-nulo:',int(df.t_aval.notna().sum()),'/25  min %.4g max %.4g'%(df.t_aval.min(),df.t_aval.max()))
print(' sonda.desligada:',df.desligada.value_counts().to_dict())
print(' REGRA_DO_ROTULO:',int(df.regra_rotulo.sum()),'/25   linhas sonda_estratificada:',df.estrat.sum())
