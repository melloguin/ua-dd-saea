# -*- coding: utf-8 -*-
"""T11/c217 — BATERIA 2: as CORRECOES da T11 no smoke + nao-perturbacao g6.
READ-ONLY."""
import json, glob, os, math, hashlib
from collections import Counter
import pandas as pd, numpy as np

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = os.path.join(RAIZ, 'ua-dd-saea/f5/t11/baterias/c217')
SM = os.path.join(RAIZ, 'evidencia_T11/smoke_matlab/experiments/main/c217')
COM = os.path.join(RAIZ, 'evidencia_T11/g6_com/experiments/main/c217')
SEM = os.path.join(RAIZ, 'evidencia_T11/g6_sem/experiments/main/c217')

def carrega(d):
    j = glob.glob(os.path.join(d, '*.jsonl'))[0]
    man = json.load(open(glob.glob(os.path.join(d, '*.manifest.json'))[0]))
    recs = {}
    for line in open(j, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        x = json.loads(line); recs.setdefault(x.get('rec'), []).append(x)
    base = j[:-6]
    par = {k: pd.read_parquet(base + '__%s.parquet' % k)
           for k in ('pop', 'real', 'surrogate', 'timing')}
    return man, recs, par

print('#### SMOKE T11 · main/c217/MMF1/42')
man, R, P = carrega(SM)
gens = R['c217_gen']
print('n_gen=%d  n_sonda=%d  n_sondaE=%d  n_guard=%d  fe=%d/%d' %
      (len(gens), len(R.get('sonda', [])), len(R.get('sonda_estratificada', [])),
       len(R.get('guard', [])), man['fe_final'], man['maxfe']))

# --- I-1 pmid_ids
tot = sum(len(g['pmid_ids']) if isinstance(g['pmid_ids'], list) else 1 for g in gens)
neg = sum(sum(1 for v in (g['pmid_ids'] if isinstance(g['pmid_ids'], list) else [g['pmid_ids']]) if v == -1) for g in gens)
casaN = sum(1 for g in gens if len(g['pmid_ids']) == g['n_Pmid'])
print('\n[I-1] pmid_ids: %d/%d valores == -1 (%.1f%%) | comprimento==n_Pmid em %d/%d ger'
      % (neg, tot, 100*neg/tot, casaN, len(gens)))
print('      ids distintos observados: %s' % sorted({v for g in gens for v in g['pmid_ids']}))

# --- I-5 y_treino_dist
yz = Counter((g['y_treino_dist']['classe_menos1'] > 0, g['y_treino_dist']['classe_zero'] > 0,
              g['y_treino_dist']['classe_mais1'] > 0) for g in gens)
print('\n[I-5] y_treino_dist (menos1>0, zero>0, mais1>0): %s' % dict(yz))
print('      n == n_treino em %d/%d ; n == n_best+n_worst em %d/%d' %
      (sum(1 for g in gens if g['y_treino_dist']['n'] == g['n_treino']), len(gens),
       sum(1 for g in gens if g['y_treino_dist']['n'] == g['n_best']+g['n_worst']), len(gens)))
# n esperado = |Input| = ceil(|P|/2); |P| reconstruido de n_Pmid = 2*floor(|P|/8)+1 nao e injetivo
# -> usa a ② (Arc snapshot)
t2 = P['pop'].groupby('geracao').size()
okn = 0
for g in gens:
    gg = g['geracao']; a2 = int(t2.get(gg, 0)); Pp = a2 if gg == 1 else min(50, a2)
    if g['y_treino_dist']['n'] == math.ceil(Pp/2): okn += 1
print('      n == ceil(|P|/2) (=|Input|, NAO |TrainIn|) em %d/%d' % (okn, len(gens)))

# --- I-6 sonda estratificada
sE = R.get('sonda_estratificada', [])
sur = P['surrogate']
print('\n[I-6] regimes na ③: %s' % dict(Counter(sur.regime)))
print('      sonda_estratificada: %d blocos x n_pontos %s = %d linhas ; prevalencia %s ; ok %s' %
      (len(sE), sorted({e['n_pontos'] for e in sE}),
       int((sur.regime == 'sonda_estratificada').sum()),
       sorted({str(e['prevalencia_nd_no_bloco']) for e in sE}),
       sorted({e['ok'] for e in sE})))
print('      geracoes com bloco estratificado == geracoes com regua: %s' %
      ([e['geracao'] for e in sE] == [e['geracao'] for e in R['sonda']]))

# --- I-3 tempo_aval_real_s
print('\n[I-3] timing ⑤: %s' % {k: round(v, 4) for k, v in man['timing'].items()})

# --- contrato: params + regra
print('\n[contrato] params no ⑤: %s' % list(man.get('params', {}).keys()))
print('           REGRA_DO_ROTULO: %s (%d chars)' % ('REGRA_DO_ROTULO' in man['sigma_dict'],
                                                     len(man['sigma_dict'].get('REGRA_DO_ROTULO', ''))))
print('           header ⑥ chaves: %s' % list(R['header'][0].keys()))
print('           header tem run_id/ambiente/params/sigma_dict? %s' %
      [k in R['header'][0] for k in ('run_id', 'ambiente', 'params', 'sigma_dict')])

# --- MECANISMO no smoke (nao-regressao das identidades)
def ceilf(x): return int(math.ceil(x - 1e-12))
ok = dict(best=0, worst=0, tre=0, par=0, pmid=0, tri=0, est=0, lote=0, score=0, spread=0)
for g in gens:
    gg = g['geracao']; a2 = int(t2.get(gg, 0)); Pp = a2 if gg == 1 else min(50, a2)
    Pb, Pw = ceilf(Pp/4), ceilf(Pp/2)-ceilf(Pp/4)
    ok['best'] += g['n_best'] == ceilf(0.75*Pb)
    ok['worst'] += g['n_worst'] == ceilf(0.75*Pw)
    ok['tre'] += g['n_treino'] == g['n_best']+g['n_worst']
    ok['par'] += g['n_pares_treino'] == g['n_treino']*(g['n_treino']-1)
    ok['pmid'] += g['n_Pmid'] == 2*(Pp//8)+1
    Dv = (Pb-g['n_best'])+(Pw-g['n_worst'])
    ok['tri'] += abs(g['p_mais']*Dv + g['p_menos']*Dv + g['n_contradicoes'] - Dv) < 1e-6
    e = 1 if g['p_mais'] > g['delta'] else (2 if g['p_menos'] > g['delta'] else 3)
    ok['est'] += e == g['estado']
    ok['lote'] += (g['lote'] == 1) if g['estado'] == 3 else (g['lote'] == Pb//2)
    ok['score'] += g['score'] == {1: 1, 2: -1, 3: 0}[g['estado']]
    ok['spread'] += g['modelo_hp']['spread'] == 0.1925
print('\n[mecanismo no smoke, %d ger] %s' % (len(gens), {k: '%d/%d' % (v, len(gens)) for k, v in ok.items()}))
print('   estados: %s' % dict(Counter(g['estado'] for g in gens)))

# --- g6 com x sem (nao-perturbacao) — medido por mim
print('\n#### G6 COM x SEM (nao-perturbacao da sonda)')
mc, Rc, Pc = carrega(COM); ms, Rs, Ps = carrega(SEM)
for nome, a, b in [('①real', Pc['real'], Ps['real']), ('②pop', Pc['pop'], Ps['pop'])]:
    ha = hashlib.sha256(pd.util.hash_pandas_object(a, index=False).values.tobytes()).hexdigest()
    hb = hashlib.sha256(pd.util.hash_pandas_object(b, index=False).values.tobytes()).hexdigest()
    print('   %s linhas %d x %d ; sha256 %s' % (nome, len(a), len(b), 'IGUAL '+ha[:16] if ha == hb else 'DIFERE'))
print('   ③ linhas COM=%d SEM=%d ; regimes COM=%s SEM=%s' %
      (len(Pc['surrogate']), len(Ps['surrogate']),
       dict(Counter(Pc['surrogate'].regime)), dict(Counter(Ps['surrogate'].regime))))
print('   ⑤ sonda.desligada COM=%s SEM=%s ; n_blocos COM=%s SEM=%s' %
      (mc['sonda'].get('desligada'), ms['sonda'].get('desligada'),
       mc['sonda'].get('n_blocos'), ms['sonda'].get('n_blocos')))
gc_, gs_ = Rc['c217_gen'], Rs['c217_gen']
eq = sum(1 for x, y in zip(gc_, gs_) if (x['estado'], x['lote'], x['p_mais'], x['p_menos'],
                                        x['n_contradicoes'], x['arc_size'], x['fe']) ==
         (y['estado'], y['lote'], y['p_mais'], y['p_menos'], y['n_contradicoes'], y['arc_size'], y['fe']))
print('   ⑥ c217_gen: COM %d ger x SEM %d ger ; tuplas de decisao identicas em %d' % (len(gc_), len(gs_), eq))
