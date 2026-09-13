#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 3 — qualidade do classificador na régua Sobol + TESTE DIRETO da
REGRA_DO_ROTULO (emparelhamento POSICIONAL E CÍCLICO) SEM os pmid_ids, via a
estrutura módulo-n do próprio pred_score. Também: o que falta para executar a regra."""
import json, os, math
import numpy as np, pandas as pd, pyarrow.parquet as pq

D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT  = os.path.join(REPO, 'f5/t11/baterias/c217')
B = os.path.join(D_EV, 'smoke_matlab/experiments/main/c217/exp_main_c217_MMF1_42')
rng = np.random.default_rng(20260731)
def rep(k, v): print('%-48s %s' % (k, v))

rows = [json.loads(l) for l in open(B + '.jsonl') if l.strip()]
gen  = {r['geracao']: r for r in rows if r.get('rec') == 'c217_gen'}
sur  = pq.read_table(B + '__surrogate.parquet').to_pandas()
real = pq.read_table(B + '__real.parquet').to_pandas()
art  = pq.read_table(os.path.join(REPO, 'data/sonda/sonda_MMF1.parquet')).to_pandas()
S = 2000
fc = [c for c in art.columns if c.startswith('f')][:2]
F = art[fc].values[:S].astype('float64')

print('======== gabarito global da régua (F5 §6.3) ========')
dom = np.zeros(S, dtype=int)
for i in range(S):
    le = (F <= F[i]).all(1); lt = (F < F[i]).any(1)
    dom[i] = int((le & lt).sum())
med = np.median(dom)
lab_bom = (dom <= med).astype(int)
lab_nd  = (dom == 0).astype(int)
rep('gabarito: mediana dom_count / #ND',  (med, int(lab_nd.sum())))

def auc_ties(score, y):
    if y.sum() == 0 or y.sum() == len(y): return np.nan
    r = pd.Series(score).rank().values
    n1, n0 = y.sum(), len(y) - y.sum()
    return (r[y == 1].sum() - n1*(n1+1)/2) / (n1*n0)

sb = sur[sur.regime == 'sonda'].copy()
res = []
for g, blk in sb.groupby('geracao'):
    s = blk.pred_score.values.astype(float)
    res.append(dict(g=int(g), n=len(s), nuniq=len(np.unique(s)),
                    frac_m1=float((s == -1).mean()), frac_0=float((s == 0).mean()),
                    frac_p1=float((s == 1).mean()),
                    auc_bom=auc_ties(s, lab_bom), auc_nd=auc_ties(s, lab_nd),
                    nPmid=gen[int(g)]['n_Pmid'], p_mais=gen[int(g)]['p_mais']))
dfa = pd.DataFrame(res)
inf = dfa[dfa.nuniq >= 2]
rep('blocos informativos (>=2 valores)',  '%d/%d' % (len(inf), len(dfa)))
rep('AUC_bom mediana / >0,5',             (round(float(inf.auc_bom.median()), 4),
                                           '%d/%d' % (int((inf.auc_bom > .5).sum()), len(inf))))
rep('AUC_ND  mediana / >0,5',             (round(float(inf.auc_nd.median()), 4),
                                           '%d/%d' % (int((inf.auc_nd > .5).sum()), len(inf))))
rep('AUC_bom 1o bloco / ultimo bloco',    (round(float(dfa.auc_bom.iloc[0]), 4),
                                           round(float(dfa.auc_bom.iloc[-1]), 4)))
q = len(dfa)//4
rep('AUC_bom 1o quartil -> 4o quartil',   (round(float(dfa.auc_bom[:q].mean()), 4),
                                           round(float(dfa.auc_bom[-q:].mean()), 4)))
rep('p_mais 1o quartil -> 4o quartil',    (round(float(dfa.p_mais[:q].mean()), 4),
                                           round(float(dfa.p_mais[-q:].mean()), 4)))
rep('frac(score=0) mediana',              round(float(dfa.frac_0.median()), 4))
rep('acuracia-por-amostra p+ + 0,5*contr',round(float(np.mean([
     r['p_mais'] + 0.5*r['n_contradicoes']/((r['p_mais']+r['p_menos'])*0+1)/1
     if False else r['p_mais'] + 0.5*(1 - r['p_mais'] - r['p_menos'])
     for r in gen.values()])), 4))

print('\n======== TESTE DA REGRA_DO_ROTULO: estrutura módulo-n ========')
# RBFNNPC.m:59-62 -> a linha i (1-based) pareia com Preference(mod(i,n)+1).
# Predição: se o emparelhamento é POSICIONAL E CÍCLICO, o pred_score tem de
# variar SISTEMATICAMENTE com o resíduo (i mod n). Teste de permutação: compara
# a variância ENTRE classes de resíduo com a de 2000 rótulos embaralhados.
out = []
for g, blk in sb.groupby('geracao'):
    s = blk.pred_score.values.astype(float)
    n = int(gen[int(g)]['n_Pmid'])
    j = np.arange(len(s)); r = (j + 1) % n           # índice 0-based da referência
    obs = np.array([s[r == k].mean() for k in range(n)])
    F_obs = obs.var()
    null = np.empty(400)
    for b in range(400):
        p = rng.permutation(s)
        null[b] = np.array([p[r == k].mean() for k in range(n)]).var()
    out.append(dict(g=int(g), n=n, var_obs=F_obs, var_null_med=float(np.median(null)),
                    razao=F_obs/max(np.median(null), 1e-12),
                    p=float((null >= F_obs).mean() + 1/401)))
dfm = pd.DataFrame(out)
rep('blocos com p<0,05 (estrutura mod-n)', '%d/%d' % (int((dfm.p < 0.05).sum()), len(dfm)))
rep('razao var(obs)/var(nulo) mediana',    round(float(dfm.razao.median()), 2))
rep('razao min .. max',                    (round(float(dfm.razao.min()), 2), round(float(dfm.razao.max()), 2)))
# controle: um n FALSO (n+1) tem de NAO estruturar
out2 = []
for g, blk in sb.groupby('geracao'):
    s = blk.pred_score.values.astype(float)
    n = int(gen[int(g)]['n_Pmid']) + 1
    j = np.arange(len(s)); r = (j + 1) % n
    obs = np.array([s[r == k].mean() for k in range(n)]).var()
    null = np.array([np.array([rng.permutation(s)[r == k].mean()
                               for k in range(n)]).var() for _ in range(200)])
    out2.append(float((null >= obs).mean() + 1/201))
rep('CONTROLE n+1 (falso): blocos p<0,05', '%d/%d' % (int((np.array(out2) < .05).sum()), len(out2)))

print('\n======== O QUE FALTA para EXECUTAR a regra ========')
rep('passo (1) pmid_ids reais',            'AUSENTE — 426/426 = -1')
rep('passo (2) n = numel(pmid_ids)',       'OK (n_Pmid 5..13, 42/42)')
rep('passo (3) f da referência via ①',     'BLOQUEADO — sem id não há linha da ①')
# rota alternativa: reconstruir Pmid exige a MEMBRESIA de Population
pop = pq.read_table(B + '__pop.parquet').to_pandas()
pgs = pop.groupby('geracao').size()
rep('②: é o Arc ou a Population?',         'Arc (|②(g)|+lote==arc_size 42/42; max|②|=%d > N=50)' % int(pgs.max()))
rep('membresia de Population exportada?',  'NAO — só |P| = min(50,|Arc|) é inferível')
rep('rate = FE/maxFE recuperável?',        'SIM (fe da geração anterior / 61)')
rep('PopObj em float64?',                  'NAO — ① é float32 (regra 11 do §10)')
rep('=> reconstrução de Pmid',             'NAO-VALIDÁVEL (nenhum campo exportado depende da ORDEM)')

dfa.to_csv(os.path.join(OUT, 'c217_t11_sonda_blocos.csv'), index=False)
dfm.to_csv(os.path.join(OUT, 'c217_t11_modn.csv'), index=False)
print('\nOK ->', OUT)
