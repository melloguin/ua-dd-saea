#!/usr/bin/env python
"""
BATERIA D — c262 qNEHVI: provas finais. READ-ONLY nos dados.
  D1 escala LOG da aquisição: qLogNEHVI ⇒ α pode ser NEGATIVO (qNEHVI cru é ≥0)
  D2 SAA/CBD determinístico DENTRO da iteração: restarts com α bit-idêntico
  D3 posição vs pisos com o piso de ruído entre máquinas (IGD+ 58,98%) aplicado
  D4 interseção com o setup do paper
"""
import json, glob, os, collections
import numpy as np, pandas as pd

ROOT='/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
F5='/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'; OUT=f'{F5}/baterias/c262'
PROBS=sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))
rows=[]
for prob in PROBS:
    b=f'{ROOT}/{prob}/42'; s=f'exp_main_c262_{prob}_42'
    dec=[json.loads(l) for l in open(f'{b}/{s}.jsonl') if l.strip()]
    dec=[d for d in dec if d.get('rec')=='decision']
    a=np.array([d['acqf_escolhido'] for d in dec])
    dup=0; multmax=0; dup_pairs=0
    for d in dec:
        v=d['acqf_todos_restarts']
        c=collections.Counter(repr(x) for x in v)
        m=max(c.values())
        if m>1: dup+=1
        multmax=max(multmax,m)
        dup_pairs+=sum(k-1 for k in c.values() if k>1)
    rows.append(dict(problema=prob, n=len(dec), a_min=a.min(), a_max=a.max(),
                     frac_neg=float((a<0).mean()), n_neg=int((a<0).sum()),
                     iters_com_dup=dup, mult_max=multmax, restarts_dup=dup_pairs))
D=pd.DataFrame(rows); D.to_csv(f'{OUT}/c262_bateriaD.csv',index=False)
pd.set_option('display.width',250)
print(D.to_string())
print('\nTOTAIS: decisões', D.n.sum(), '| α<0 em', D.n_neg.sum(), f'({100*D.n_neg.sum()/D.n.sum():.1f}%)',
      '| α global [', D.a_min.min(), ',', D.a_max.max(), ']')
print('iterações com ≥2 restarts α-bit-idênticos:', D.iters_com_dup.sum(), '| multiplicidade máx', D.mult_max.max(),
      '| restarts duplicados', D.restarts_dup.sum())

# D3 — piso de ruído
P=pd.read_csv(f'{OUT}/c262_posicao.csv')
PISO=58.98
P['alem_do_piso']=P.delta_pct.abs()>PISO
print('\n== D3 posição vs pisos (c262=v6, pisos=vm3 ⇒ piso de ruído 58,98% aplicável) ==')
print('bate piso ALÉM do ruído:', int(((P.delta_pct<0)&P.alem_do_piso).sum()))
print('bate piso DENTRO do ruído:', int(((P.delta_pct<0)&~P.alem_do_piso).sum()))
print('perde DENTRO do ruído:', int(((P.delta_pct>0)&~P.alem_do_piso).sum()))
print('perde ALÉM do ruído:', int(((P.delta_pct>0)&P.alem_do_piso).sum()))
print(P[['problema','igd','piso_melhor','piso_alg','delta_pct','alem_do_piso','rank_SA','n_SA']].to_string())
P.to_csv(f'{OUT}/c262_posicao.csv',index=False)

# D4 — interseção com o paper
paper={'DTLZ2':dict(d=6,M=2,FE=200,ruido='10% (H.7 tb noiseless)'),
       'ZDT1':dict(d=4,M=2,FE=200,ruido='noiseless (H.7)'),
       'BBOB(SphereEllipsoidal)':dict(d=5,M=2,FE=200,ruido='5%')}
nosso={'DTLZ2':dict(D=12,M=3,FE=371),'ZDT1':dict(D=30,M=2,FE=929),
       'BBOB_F1..F55':dict(D=10,M=2,FE=309)}
print('\n== D4 interseção ==')
for k in paper: print(k, 'PAPER', paper[k])
for k in nosso: print(k, 'NOSSO', nosso[k])
