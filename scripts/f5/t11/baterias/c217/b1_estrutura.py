#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 1 — estrutura e identidades do smoke T11 do c217 (main/c217/MMF1/42).
READ-ONLY sobre /Users/.../evidencia_T11. Escreve SÓ em f5/t11/baterias/c217/."""
import json, math, hashlib, os, sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT  = os.path.join(REPO, 'f5/t11/baterias/c217')
BASE = os.path.join(D_EV, 'smoke_matlab/experiments/main/c217/exp_main_c217_MMF1_42')

R = {}
def rep(k, v):
    R[k] = v
    print('%-42s %s' % (k, v))

man = json.load(open(BASE + '.manifest.json'))
rows = [json.loads(l) for l in open(BASE + '.jsonl') if l.strip()]
hdr  = [r for r in rows if r.get('rec') == 'header'][0]
foot = [r for r in rows if r.get('rec') == 'footer'][0]
gen  = [r for r in rows if r.get('rec') == 'c217_gen']
snd  = [r for r in rows if r.get('rec') == 'sonda']
sne  = [r for r in rows if r.get('rec') == 'sonda_estratificada']
grd  = [r for r in rows if r.get('rec') == 'guard']

real = pq.read_table(BASE + '__real.parquet').to_pandas()
pop  = pq.read_table(BASE + '__pop.parquet').to_pandas()
sur  = pq.read_table(BASE + '__surrogate.parquet').to_pandas()
tim  = pq.read_table(BASE + '__timing.parquet').to_pandas()

D, M, maxfe = hdr['D'], hdr['M'], hdr['maxfe']
print('=== c217 / MMF1 / 42 · D=%d M=%d maxfe=%d ===' % (D, M, maxfe))

# ---------------- A1 orçamento ----------------
rep('A1.len_real == 31D-1',           (len(real), 31*D-1, len(real) == 31*D-1))
rep('A1.fe_index denso 0-based',      bool((np.sort(real.fe_index.values) == np.arange(len(real))).all()))
rep('A1.solution_id denso 0-based',   bool((np.sort(real.solution_id.values) == np.arange(len(real))).all()))
rep('A1.fe_final==maxfe==manifest',   (foot['fe_final'], foot['maxfe'], man['maxfe'], man['fe_final']))
rep('A1.footer.termino',              foot['termino'])
rep('A1.status/motivo_parada',        (man['status'], man.get('motivo_parada', 'AUSENTE')))

# ---------------- A2 DoE ----------------
n_init = int((real.fase == 'init').sum())
rep('A2.n_init == 11D-1',             (n_init, 11*D-1, n_init == 11*D-1))
doe_p = os.path.join(REPO, 'data/doe/MMF1/doe_MMF1_42.parquet')
doe_m = json.load(open(os.path.join(REPO, 'data/doe/MMF1/doe_MMF1_42.manifest.json')))
doe = pq.read_table(doe_p).to_pandas()
xc  = [c for c in doe.columns if c.startswith('x')]
Xd  = doe[xc].values.astype('float32')
Xi  = real.loc[real.fase == 'init', ['x%d' % i for i in range(D)]].values.astype('float32')
rep('A2.doe_hash manifesto==sidecar', (man['doe_hash'] == doe_m.get('hash', doe_m.get('doe_hash')),
                                       man['doe_hash'][:16]))
rep('A2.max|dX| DoE vs ①  (float32)', float(np.abs(Xd - Xi).max()))
rep('A2.footer.cp_init',              foot['cp_init'])

# ---------------- A3/A8/A14 constantes ----------------
rep('A3.header.N',                    hdr['N'])
rep('A8.header.delta / gmax',         (hdr['delta'], hdr['gmax']))
rep('A8.delta em todos os gens',      sorted({g['delta'] for g in gen}))
rep('A14.spread nos gens',            sorted({g['modelo_hp']['spread'] for g in gen}))
rep('A16.gmax no header (eco)',       hdr['gmax'])

# ---------------- |P| a partir da ② ----------------
pg = pop.groupby('geracao').size()
rep('A19.n_grupos ② / n_gen_events',  (len(pg), len(gen)))
P = {}
for g in sorted(pg.index):
    P[int(g)] = int(pg.loc[g]) if g == 1 else min(hdr['N'], int(pg.loc[g]))
gd = {g['geracao']: g for g in gen}

# ---------------- A4 split ----------------
ok_b = ok_w = ok_t = 0
det = []
for g, r in gd.items():
    p = P[g]
    Pb = math.ceil(p/4); Pw = math.ceil(p/2) - math.ceil(p/4)
    nb = math.ceil(0.75*Pb); nw = math.ceil(0.75*Pw)
    ok_b += (r['n_best'] == nb); ok_w += (r['n_worst'] == nw)
    ok_t += (r['n_treino'] == r['n_best'] + r['n_worst'])
    det.append(dict(g=g, P=p, Pb=Pb, Pw=Pw, nb_prev=nb, nb=r['n_best'], nw_prev=nw,
                    nw=r['n_worst'], ntr=r['n_treino'], npar=r['n_pares_treino'],
                    nPmid=r['n_Pmid'], Dv=(Pb-r['n_best'])+(Pw-r['n_worst']),
                    pm=r['p_mais'], pn=r['p_menos'], nc=r['n_contradicoes'],
                    estado=r['estado'], lote=r['lote'], score=r['score'],
                    ftm=r['fe_treino_max'], arc=r['arc_size'], fe=r['fe']))
dfg = pd.DataFrame(det).sort_values('g')
n = len(gd)
rep('A4.n_best == ceil(3/4*ceil(|P|/4))',  '%d/%d' % (ok_b, n))
rep('A4.n_worst == ceil(3/4*(c|P|/2-c|P|/4))', '%d/%d' % (ok_w, n))
rep('A4.n_treino == n_best+n_worst',       '%d/%d' % (ok_t, n))

# ---------------- A5 pares ----------------
rep('A5.n_pares == n_tr(n_tr-1)',     '%d/%d' % (int((dfg.npar == dfg.ntr*(dfg.ntr-1)).sum()), n))
rep('A5.razao vs 2*nb*nw (paper)',    float((dfg.npar/(2*dfg.nb*dfg.nw)).median()))

# ---------------- A6/A7 tricotomia ----------------
tri = np.abs(dfg.pm*dfg.Dv + dfg.pn*dfg.Dv + dfg.nc - dfg.Dv) < 1e-9
kint = (np.abs(dfg.pm*dfg.Dv - np.round(dfg.pm*dfg.Dv)) < 1e-6) & \
       (np.abs(dfg.pn*dfg.Dv - np.round(dfg.pn*dfg.Dv)) < 1e-6)
rep('A6.p+|Dv|+p-|Dv|+contrad==|Dv|', '%d/%d' % (int(tri.sum()), n))
rep('A6.k+ e k- inteiros',            '%d/%d' % (int(kint.sum()), n))
rep('A7.dist |Dvalid|',               dict(dfg.Dv.value_counts().sort_index()))
rep('A7.p_menos == 1-p_mais ?',       '%d/%d' % (int((np.abs(dfg.pm+dfg.pn-1) < 1e-9).sum()), n))

# ---------------- A9 regra tripla ----------------
def st(pm, pn, d=0.8):
    return 1 if pm > d else (2 if pn > d else 3)
rec = dfg.apply(lambda r: st(r.pm, r.pn), axis=1)
rep('A9.estado recomputado == logado',  '%d/%d' % (int((rec == dfg.estado).sum()), n))
rep('A9.distribuicao de estado',        dict(dfg.estado.value_counts().sort_index()))
cf = dfg.apply(lambda r: 1 if r.pm < 0.2 else (2 if r.pn < 0.2 else 3), axis=1)
rep('A9.CONTRAFACTUAL as-shipped',      dict(cf.value_counts().sort_index()))
rep('A9.divergencia D17 (ger)',         '%d/%d' % (int((cf != dfg.estado).sum()), n))
rep('A9.motivo cita delta=0.80',        '%d/%d' % (sum('delta=0.80' in g['motivo'] for g in gen), n))

# ---------------- A10 lote ----------------
lote_prev = dfg.apply(lambda r: 1 if r.estado == 3 else math.floor(math.ceil(r.P/4)/2), axis=1)
rep('A10.lote == previsto',           '%d/%d' % (int((lote_prev == dfg.lote).sum()), n))
rep('A10.lote por estado',            dfg.groupby('estado').lote.agg(['min','max','count']).to_dict())

# ---------------- A17 n_Pmid ----------------
pm_prev = dfg.P.apply(lambda p: 2*(p//8)+1)
rep('A17.n_Pmid == 2*floor(|P|/8)+1', '%d/%d' % (int((pm_prev == dfg.nPmid).sum()), n))
rep('A17.n_Pmid distintos',           sorted(set(dfg.nPmid)))

# ---------------- A18 min(N,|Arc|) ----------------
rep('A18.gers com |P|<N (fix exerc.)', int((dfg.P < hdr['N']).sum()))
rep('A18.trajetoria |P|',             '%d -> %d' % (dfg.P.iloc[0], dfg.P.iloc[-1]))

# ---------------- A19 ② off-by-one ----------------
sz = {int(g): int(v) for g, v in pg.items()}
ob = sum(1 for g, r in gd.items() if r['arc_size'] == sz[g] + r['lote'])
rep('A19.arc_size==|②(g)|+lote',      '%d/%d' % (ob, n))
rep('A19.|②(1)| == init',             (sz[1], n_init))

# ---------------- A20 fantasma ----------------
rep('A20.n_geracoes == eventos+1',    (foot['n_geracoes'], len(gen)+1, foot['n_geracoes'] == len(gen)+1))
rep('A20.guards',                     [(g.get('name'), g.get('fe'), g.get('solution_id')) for g in grd])

# ---------------- A21 cache ----------------
rep('A21.cache_hits manifesto/footer', (man['cache_hits'], foot['cache_hits'], len(grd)))
rep('A21.|①| == init+Σlote-(ch-1)',   (n_init + int(dfg.lote.sum()) - (man['cache_hits']-1), len(real)))

# ---------------- A12 score ternário ----------------
rep('A12.set(pred_score)',            sorted(set(np.unique(sur.pred_score.dropna().values).tolist())))
rep('A12.pred_tipo/modelo_flag',      (sorted(set(sur.pred_tipo)), sorted(set(sur.pred_flag if 'pred_flag' in sur else sur.modelo_flag))))
busca = sur[sur.regime == 'online']
ok = sum(1 for g, r in gd.items()
         if set(busca.loc[busca.geracao == g, 'pred_score'].unique()) == {float(r['score'])})
rep('A12.⑥.score == ③ da geracao',    '%d/%d' % (ok, n))
rep('A11.linhas online por ger==lote','%d/%d' % (sum(1 for g, r in gd.items()
      if int((busca.geracao == g).sum()) == r['lote']), n))

# ---------------- A13 pred_confianca ----------------
nun = sur.groupby(['regime','geracao']).pred_confianca.nunique()
rep('A13.nunique==1 por bloco',       '%d/%d' % (int((nun == 1).sum()), len(nun)))
eq = 0
for (rg, g), v in sur.groupby(['regime','geracao']).pred_confianca.first().items():
    if g in gd and abs(float(v) - gd[g]['p_mais']) < 1e-6: eq += 1
rep('A13.== p_mais da geracao',       '%d/%d' % (eq, len(nun)))

# ---------------- A24 mu/sigma NULL ----------------
rep('A24.mu/sigma/pred_classe nulos', {c: int(sur[c].isna().sum()) for c in
                                       ['mu_0','mu_1','sigma_0','sigma_1','pred_classe',
                                        'transf_tipo','transf_params']} | {'linhas': len(sur)})

# ---------------- A23 fe_treino_max ----------------
d1 = np.diff(dfg.ftm.values.astype(float))
rep('A23.quedas de fe_treino_max',    (int((d1 < 0).sum()), float(-d1[d1 < 0].sum() if (d1<0).any() else 0)))
rep('A23.ftm<arc_size / >=n_treino',  ('%d/%d' % (int((dfg.ftm < dfg.arc).sum()), n),
                                       '%d/%d' % (int((dfg.ftm >= dfg.ntr).sum()), n)))

# ---------------- A25 timing ----------------
t = tim.copy()
rep('A25.len ④ == n_gen',             (len(t), n))
rep('A25.fit+busca <= tempo_geracao', '%d/%d' % (int(((t.tempo_fit_s+t.tempo_busca_s) <= t.tempo_geracao_s+1e-9).sum()), len(t)))
gsonda = {s['geracao'] for s in snd}
ok2 = sum(1 for _, r in t.iterrows() if (r.tempo_pred_sonda_s > 0) == (r.geracao in gsonda))
rep('A25.sonda>0 <=> bloco',          '%d/%d' % (ok2, len(t)))
rep('A25.Σ④fit vs ⑤fit',              (float(t.tempo_fit_s.sum()), man['timing']['tempo_fit_surrogate_s']))
rep('I3.tempo_aval_real_s (⑤)',       man['timing']['tempo_aval_real_s'])
rep('A15.1 fit>0 por geracao',        '%d/%d' % (int((t.tempo_fit_s > 0).sum()), len(t)))
rep('A15.n_acumulado == n_treino',    '%d/%d' % (sum(1 for _, r in t.iterrows()
                                       if int(r.n_acumulado) == gd[int(r.geracao)]['n_treino']), len(t)))
rep('A16.busca st1/2 vs st3 (med)',   (float(dfg.loc[dfg.estado != 3, 'g'].map(
        dict(zip(t.geracao, t.tempo_busca_s))).median()) if (dfg.estado != 3).any() else None,
        float(dfg.loc[dfg.estado == 3, 'g'].map(dict(zip(t.geracao, t.tempo_busca_s))).median())))

# ---------------- A26 elo ③busca ↔ ① ----------------
rsi = busca.real_solution_id
rep('A26.real_solution_id nao-nulo',  '%d/%d' % (int(rsi.notna().sum()), len(busca)))
rep('A26.dtype real_solution_id',     str(sur.real_solution_id.dtype))
j = busca.merge(real, left_on=busca.real_solution_id.astype('float'),
                right_on=real.solution_id.astype('float'), suffixes=('_s','_r'))
dx = max(float(np.abs(j['x%d_s' % i].values.astype('float32') - j['x%d_r' % i].values.astype('float32')).max())
         for i in range(D))
rep('A26.max|dX| ③busca vs ①',        (dx, len(j)))
rep('A26.real_solution_id na sonda',  int(sur.loc[sur.regime != 'online','real_solution_id'].notna().sum()))

dfg.to_csv(os.path.join(OUT, 'c217_t11_geracoes.csv'), index=False)
json.dump({k: str(v) for k, v in R.items()}, open(os.path.join(OUT, 'b1_resultados.json'), 'w'),
          indent=1, ensure_ascii=False)
print('\nOK -> ', OUT)
