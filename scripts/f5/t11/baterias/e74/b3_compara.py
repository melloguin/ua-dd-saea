# -*- coding: utf-8 -*- READ-ONLY. Comparacao PRE(s42) x POS(smoke) celula a celula nas 3 comuns.
import sys, json, glob
import numpy as np, pandas as pd
OUT='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e74'
ROOT='/Users/gmello/Documents/python_repos/mestrado'
def evs(base):
    return [json.loads(l) for l in open(base+'.jsonl')]
def resumo(prob, base, tag):
    ev=evs(base)
    g=[r for r in ev if r.get('rec')=='e74_gen']
    d=pd.DataFrame(g)
    tot={}
    for s in (1,2,3):
        sd=d[d.estrategia==s]
        tot[f'slots_s{s}']=len(sd); tot[f'aceitos_s{s}']=int(sd.aceito.sum())
        tot[f'perdidos_s{s}']=int(sd.slot_perdido.sum()); tot[f'vazio_s{s}']=int((sd.n_cand==0).sum())
    s1=d[d.estrategia==1]
    a1=s1[s1.aceito==1]
    tot.update(problema=prob, corpus=tag, ciclos=tot['slots_s1'],
        noop=int((s1['count']==0).sum()), noop_pct=100*(s1['count']==0).mean(),
        n_desal_med=float(s1.n_desalinhado.mean()),
        cand_dist_med=float(a1.cand_dist_dec.median()), cand_dist_mean=float(a1.cand_dist_dec.mean()),
        count_med=float(s1['count'].median()), count_max=int(s1['count'].max()),
        frac_n1_med=float(s1.frac_nivel1.median()),
        saida_90=int((s1['frac_nivel1']>=0.9).sum()), saida_guarda=int((s1['count']==51).sum()),
        infills=int(d.aceito.sum()), fe_final=int(d.fe.max()),
        n1_pop_med=float(s1.n_por_nivel_pop.apply(lambda v: v[0]).median()))
    tot['share_s1']=100*tot['aceitos_s1']/tot['infills']; tot['share_s2']=100*tot['aceitos_s2']/tot['infills']
    tot['share_s3']=100*tot['aceitos_s3']/tot['infills']
    return tot
rows=[]
for prob in ['MMF1','DTLZ2','ZDT1']:
    rows.append(resumo(prob,f'{ROOT}/resultados_experimentos/e74/{prob}/42/exp_main_e74_{prob}_42','PRE_s42'))
    rows.append(resumo(prob,f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/e74/exp_main_e74_{prob}_42','POS_smoke'))
df=pd.DataFrame(rows); df.to_csv(f'{OUT}/compara_3celulas.csv',index=False)
cols=['problema','corpus','ciclos','infills','aceitos_s1','aceitos_s2','aceitos_s3','share_s1','share_s2','share_s3',
      'perdidos_s1','vazio_s1','noop','noop_pct','n_desal_med','cand_dist_med','count_med','count_max','saida_90','saida_guarda','frac_n1_med']
pd.set_option('display.width',260); pd.set_option('display.max_columns',50)
print(df[cols].to_string(index=False))
# agregado s42 completo (25 celulas) para o denominador global
rows2=[]
for d in sorted(glob.glob(f'{ROOT}/resultados_experimentos/e74/*/42')):
    p=d.split('/')[-2]; rows2.append(resumo(p,f'{d}/exp_main_e74_{p}_42','PRE_s42'))
g=pd.DataFrame(rows2); g.to_csv(f'{OUT}/s42_25celulas.csv',index=False)
print('\n== s42 GLOBAL 25 celulas ==')
print('ciclos %d | infills %d | s1 %d (%.2f%%) s2 %d (%.2f%%) s3 %d (%.2f%%)'%(
  g.ciclos.sum(),g.infills.sum(),g.aceitos_s1.sum(),100*g.aceitos_s1.sum()/g.infills.sum(),
  g.aceitos_s2.sum(),100*g.aceitos_s2.sum()/g.infills.sum(),g.aceitos_s3.sum(),100*g.aceitos_s3.sum()/g.infills.sum()))
print('perdidos s1 %d s2 %d s3 %d | vazio s1 %d | noop %d (%.2f%%)'%(
  g.perdidos_s1.sum(),g.perdidos_s2.sum(),g.perdidos_s3.sum(),g.vazio_s1.sum(),g.noop.sum(),100*g.noop.sum()/g.ciclos.sum()))
