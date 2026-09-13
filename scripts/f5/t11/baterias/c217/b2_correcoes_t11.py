#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria 2 — as CORREÇÕES da T11 no c217: pmid_ids (I-1), REGRA_DO_ROTULO (I-2),
y_treino_dist (I-5), sonda_estratificada (I-6), params no ⑤, NO_RETRY (I-4),
sonda canônica (join posicional) e o par COM/SEM sonda (não-perturbação)."""
import json, os, hashlib, math
import numpy as np, pandas as pd, pyarrow.parquet as pq

D_EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT  = os.path.join(REPO, 'f5/t11/baterias/c217')
def base(root): return os.path.join(D_EV, root, 'experiments/main/c217/exp_main_c217_MMF1_42')
B = base('smoke_matlab')

def rep(k, v): print('%-46s %s' % (k, v))

man  = json.load(open(B + '.manifest.json'))
rows = [json.loads(l) for l in open(B + '.jsonl') if l.strip()]
gen  = [r for r in rows if r.get('rec') == 'c217_gen']
snd  = [r for r in rows if r.get('rec') == 'sonda']
sne  = [r for r in rows if r.get('rec') == 'sonda_estratificada']
sur  = pq.read_table(B + '__surrogate.parquet').to_pandas()
real = pq.read_table(B + '__real.parquet').to_pandas()
pop  = pq.read_table(B + '__pop.parquet').to_pandas()
D = 2

print('======== I-1 · pmid_ids (a identidade da referência) ========')
tot = sum(len(g['pmid_ids']) for g in gen)
neg = sum(sum(1 for v in g['pmid_ids'] if v == -1) for g in gen)
rep('I1.gerações com campo pmid_ids',      '%d/%d' % (sum('pmid_ids' in g for g in gen), len(gen)))
rep('I1.gerações 100%% sentinela -1',       '%d/%d' % (sum(all(v == -1 for v in g['pmid_ids']) for g in gen), len(gen)))
rep('I1.ids totais / ids == -1',           (tot, neg))
rep('I1.ids REAIS (>=0)',                  tot - neg)
rep('I1.len(pmid_ids) == n_Pmid',          '%d/%d' % (sum(len(g['pmid_ids']) == g['n_Pmid'] for g in gen), len(gen)))
# controle interno: o MESMO bud, na MESMA geração, resolve TrainIn (fatiado 1:D)
rep('I1.CONTROLE fe_treino_max nao-nulo',  '%d/%d' % (sum(g['fe_treino_max'] is not None for g in gen), len(gen)))
rep('I1.fe_treino_max min..max',           (min(g['fe_treino_max'] for g in gen),
                                            max(g['fe_treino_max'] for g in gen)))

print('\n======== I-5 · y_treino_dist ========')
ys = pd.DataFrame([dict(g=g['geracao'], **g['y_treino_dist']) for g in gen])
rep('I5.presente',                         '%d/%d' % (sum('y_treino_dist' in g for g in gen), len(gen)))
rep('I5.classe_menos1 (soma / distintos)', (int(ys.classe_menos1.sum()), sorted(set(ys.classe_menos1))))
rep('I5.classe_zero   (soma / distintos)', (int(ys.classe_zero.sum()), sorted(set(ys.classe_zero))))
rep('I5.classe_mais1 == n  (tautologia?)', '%d/%d' % (int((ys.classe_mais1 == ys.n).sum()), len(ys)))
gd = {g['geracao']: g for g in gen}
pg = pop.groupby('geracao').size()
Pm = {int(g): (int(pg.loc[g]) if g == 1 else min(50, int(pg.loc[g]))) for g in pg.index}
ys['P'] = ys.g.map(Pm); ys['ceilP2'] = ys.P.apply(lambda p: math.ceil(p/2))
rep('I5.n == ceil(|P|/2) (= |Pb|+|Pw|)',   '%d/%d' % (int((ys.n == ys.ceilP2).sum()), len(ys)))
ys['ntr'] = ys.g.map({g: gd[g]['n_treino'] for g in gd})
rep('I5.n == n_treino ? (nome "treino")',  '%d/%d' % (int((ys.n == ys.ntr).sum()), len(ys)))
ys['npar'] = ys.g.map({g: gd[g]['n_pares_treino'] for g in gd})
rep('I5.n == n_pares_treino (alvo do PNN)?','%d/%d' % (int((ys.n == ys.npar).sum()), len(ys)))
rep('I5.prevalência recuperável do log?',  'SIM via n_best/n_worst (mesmo Output>1/<=1)')

print('\n======== I-2 · REGRA_DO_ROTULO ========')
sd = man['sigma_dict']
rep('I2.chave REGRA_DO_ROTULO presente',   'REGRA_DO_ROTULO' in sd)
rr = sd.get('REGRA_DO_ROTULO', '')
rep('I2.tamanho (chars)',                  len(rr))
for frag in ['POSICIONAL E CICLICO', 'RBFNNPC.m:59-62', 'pmid_ids[(j+1) mod n]',
             'NAO e pmid_ids[j mod n]', 'NAO agregue contra o conjunto Pmid inteiro',
             'REORDENAR o bloco muda os PROPRIOS scores']:
    rep('   contém: %s' % frag[:38], frag in rr)
rep('I2.regra EXECUTÁVEL com o dado?',     'NAO — o passo (1) pede pmid_ids e eles são -1')

print('\n======== I-6 · sonda_estratificada ========')
rep('I6.blocos estratificados (⑥)',        len(sne))
rep('I6.n_pontos por bloco',               sorted({s['n_pontos'] for s in sne}))
rep('I6.prevalencia_nd_no_bloco',          sorted({str(s['prevalencia_nd_no_bloco']) for s in sne}))
rep('I6.n_arquivo min..max',               (min(s['n_arquivo'] for s in sne), max(s['n_arquivo'] for s in sne)))
rep('I6.sigma_rel',                        sorted({s['sigma_rel'] for s in sne}))
reg = sur.regime.value_counts().to_dict()
rep('I6.regimes na ③',                     reg)
rep('I6.linhas estratificadas == 500*22',  (reg.get('sonda_estratificada'), 500*len(sne)))
se = sur[sur.regime == 'sonda_estratificada']
rep('I6.score na estratificada (frac 0)',  round(float((se.pred_score == 0).mean()), 4))
sb = sur[sur.regime == 'sonda']
rep('I6.score na régua Sobol (frac 0)',    round(float((sb.pred_score == 0).mean()), 4))
rep('I6.regra 12: blocos SEPARADOS',       'aplicada nesta análise')

print('\n======== A22 · sonda canônica (régua Sobol) ========')
rep('A22.n_blocos ⑥ / manifesto',          (len(snd), man['sonda']['n_blocos']))
rep('A22.linhas por bloco',                sorted(set(sb.groupby('geracao').size())))
gs = sorted({s['geracao'] for s in snd})
esp = [1] + [g for g in range(2, max(gd)+1) if g % 2 == 0]
rep('A22.cadência == [1]+pares',           (gs == esp, gs[:5], gs[-3:]))
rep('A22.motivos de bloco',                sorted({s.get('motivo', '-') for s in snd}))
art = pq.read_table(os.path.join(REPO, 'data/sonda/sonda_MMF1.parquet')).to_pandas()
xc = [c for c in art.columns if c.startswith('x')][:D]
Xa = art[xc].values[:2000].astype('float32')
dmax = 0.0; nb = 0
for g, blk in sb.groupby('geracao'):
    Xb = blk[['x0','x1']].values.astype('float32')
    dmax = max(dmax, float(np.abs(Xb - Xa).max())); nb += 1
rep('A22.max|dX| join POSICIONAL vs artef.',(dmax, '%d/%d blocos' % (nb, len(snd))))
am = json.load(open(os.path.join(REPO, 'data/sonda/sonda_MMF1.manifest.json')))
rep('A22.x_hash manifesto == sidecar',     man['sonda']['x_hash'] == am.get('x_hash_online', am.get('x_hash')))

print('\n======== I-4 · lista NO_RETRY ========')
p = os.path.join(REPO, 'scripts/experiments.py')
if not os.path.exists(p): p = os.path.join(REPO, 'experiments.py')
src = open(p).read().splitlines()
for i, l in enumerate(src[:130], 1):
    if 'NO_RETRY' in l or (75 <= i <= 95 and l.strip().startswith(('"', "'"))):
        print('   %s:%d  %s' % (os.path.basename(p), i, l.strip()[:110]))
rep('I4.n_retries no manifesto',           man['n_retries'])

print('\n======== ⑤ params + proveniência ========')
rep('P.params presente no ⑤',              'params' in man)
rep('P.params.keys',                       sorted(man.get('params', {}).keys()))
rep('P.params.operadores',                 man['params']['operadores'])
rep('P.params.treino',                     man['params']['treino'])
rep('P.schema_version/campanha/repo_hash', (man['schema_version'], man['campanha_id'], man['repo_hash'][:12]))
rep('P.env',                               man['env'])

print('\n======== G-6 · COM x SEM sonda (não-perturbação) ========')
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
Bc, Bs = base('g6_com'), base('g6_sem')
mc, ms = json.load(open(Bc + '.manifest.json')), json.load(open(Bs + '.manifest.json'))
rc = pq.read_table(Bc + '__real.parquet').to_pandas()
rs = pq.read_table(Bs + '__real.parquet').to_pandas()
cols = ['solution_id','x0','x1','f0','f1','fe_index','fase']
rep('G6.① COM == ① SEM (bit-a-bit)',        rc[cols].equals(rs[cols]))
rep('G6.sha256 ① COM / SEM',                (sha(Bc + '__real.parquet')[:16], sha(Bs + '__real.parquet')[:16]))
rep('G6.sonda.desligada COM / SEM',         (mc['sonda'].get('desligada'), ms['sonda'].get('desligada')))
rep('G6.n_blocos COM / SEM',                (mc['sonda']['n_blocos'], ms['sonda']['n_blocos']))
sc = pq.read_table(Bc + '__surrogate.parquet').to_pandas()
ss = pq.read_table(Bs + '__surrogate.parquet').to_pandas()
rep('G6.③ linhas COM / SEM',                (len(sc), len(ss)))
rep('G6.③ regimes SEM',                     ss.regime.value_counts().to_dict())
gc = [json.loads(l) for l in open(Bc + '.jsonl') if l.strip()]
gs_ = [json.loads(l) for l in open(Bs + '.jsonl') if l.strip()]
kc = [(r['geracao'], r['p_mais'], r['p_menos'], r['estado'], r['lote'], r['n_Pmid'])
      for r in gc if r.get('rec') == 'c217_gen']
ks = [(r['geracao'], r['p_mais'], r['p_menos'], r['estado'], r['lote'], r['n_Pmid'])
      for r in gs_ if r.get('rec') == 'c217_gen']
rep('G6.trilha da regra tripla idêntica',   (kc == ks, len(kc), len(ks)))
rep('G6.hash do par (handoff §5)',          '868a15c02c09610f (declarado)')
rep('G6.célula do par',                     (mc['problema'], mc['semente'], mc['maxfe']))
