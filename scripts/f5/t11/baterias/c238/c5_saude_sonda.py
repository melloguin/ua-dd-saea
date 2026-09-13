#!/usr/bin/env python
"""C5 — SAUDE (metricas, trajetorias, pisos) + SONDA (regua Sobol) do c238 na s42,
a partir dos insumos PRE-COMPUTADOS da F5 (nao recomputa: f5/metricas_finais_f52c.csv,
f5/sonda_f52e.csv, f5/trajetorias/, f5/contrato_f52b.csv, f5/integridade_f52a.csv,
f5/tempo_f52d.csv). READ-ONLY.
"""
import json, os, glob
import numpy as np, pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/t11/baterias/c238'

print('=' * 100)
print('C5.1 — CONTRATO e INTEGRIDADE (F5.2a/b) — quantas linhas o c238 tem?')
print('=' * 100)
for nome, f in [('integridade_f52a', f'{F5}/integridade_f52a.csv'), ('contrato_f52b', f'{F5}/contrato_f52b.csv')]:
    d = pd.read_csv(f)
    col = [c for c in d.columns if c.lower() in ('alg', 'algoritmo', 'config')]
    sub = d[d[col[0]].astype(str) == 'c238'] if col else pd.DataFrame()
    print('  %-18s total=%d linhas | c238 = %d linhas   (colunas: %s)' % (
        nome, len(d), len(sub), ','.join(d.columns[:8])))
    if len(sub): print(sub.head(20).to_string(index=False))

print()
print('=' * 100)
print('C5.2 — METRICAS FINAIS (F5.2c) — c238 vs os 4 pisos, celula a celula')
print('=' * 100)
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
print('  colunas:', list(m.columns))
ca = [c for c in m.columns if c.lower() in ('alg', 'algoritmo', 'config')][0]
cp = [c for c in m.columns if c.lower() in ('problema', 'problem')][0]
ce = [c for c in m.columns if c.lower() in ('exp', 'experimento', 'estudo', 'label')]
ce = ce[0] if ce else None
sub = m[m[ca] == 'c238']
if ce: sub = sub[sub[ce] == 'main']
print('  celulas c238:', len(sub))
pisos = ['nsga2', 'nsga3', 'moead', 'smsemoa']
mm = m[m[ce] == 'main'] if ce else m
rows = []
for _, r in sub.iterrows():
    p = r[cp]
    conc = mm[mm[cp] == p]
    pz = conc[conc[ca].isin(pisos)]
    best = pz.loc[pz.igd_plus.idxmin()] if len(pz) else None
    todos = conc.sort_values('igd_plus').reset_index(drop=True)
    rank = int(todos.index[todos[ca] == 'c238'][0]) + 1
    rows.append(dict(problema=p, igd_plus=r.igd_plus, hv=r.get('hv'),
                     melhor_piso=(best[ca] if best is not None else None),
                     piso_igd=(best.igd_plus if best is not None else np.nan),
                     razao=(r.igd_plus / best.igd_plus if best is not None else np.nan),
                     rank=rank, n_algs=len(todos)))
S = pd.DataFrame(rows).sort_values('razao')
S.to_csv(f'{OUT}/saude_c238_t11.csv', index=False)
print(S.to_string(index=False))
print('\n  bate o MELHOR piso em %d/%d celulas ; rank medio = %.2f de %d algoritmos' % (
    int((S.razao < 1).sum()), len(S), S['rank'].mean(), int(S.n_algs.max())))
print('  vitorias decisivas (razao<=0.33): %s' % S[S.razao <= .33].problema.tolist())
print('  derrotas decisivas (razao>=1.58): %s' % S[S.razao >= 1.58].problema.tolist())
print('  primeiros lugares absolutos: %s' % S[S['rank'] == 1].problema.tolist())

print()
print('=' * 100)
print('C5.3 — TRAJETORIAS (monotonicidade IGD+ e ganho)')
print('=' * 100)
tr = []
for f in sorted(glob.glob(f'{F5}/trajetorias/main_c238_*_42.json')):
    j = json.load(open(f))
    p = os.path.basename(f).replace('main_c238_', '').replace('_42.json', '')
    if isinstance(j, dict):
        cand = None
        for k in ('igd_plus', 'igdplus', 'checkpoints', 'pontos', 'serie'):
            if k in j: cand = j[k]; break
        if cand is None: cand = list(j.values())[0]
    else:
        cand = j
    if isinstance(cand, list) and cand and isinstance(cand[0], dict):
        v = [c.get('igd_plus', c.get('igdplus')) for c in cand]
    else:
        v = cand
    v = np.array([x for x in v if x is not None], float)
    d = np.diff(v)
    tr.append(dict(problema=p, n_cp=len(v), cp0=v[0], cpN=v[-1],
                   ganho=v[0] / v[-1] if v[-1] > 0 else np.nan,
                   viol_monot=int((d > 1e-12).sum())))
T = pd.DataFrame(tr)
print(T.to_string(index=False))
print('  IGD+ nao-crescente em %d/%d celulas ; violacoes totais = %d em %d transicoes' % (
    int((T.viol_monot == 0).sum()), len(T), T.viol_monot.sum(), int((T.n_cp - 1).sum())))
print('  ganho 1o->ultimo checkpoint: mediana=%.1fx  max=%.1fx (%s)  min=%.2fx (%s)' % (
    T.ganho.median(), T.ganho.max(), T.loc[T.ganho.idxmax(), 'problema'],
    T.ganho.min(), T.loc[T.ganho.idxmin(), 'problema']))

print()
print('=' * 100)
print('C5.4 — SONDA: a REGUA SOBOL (regime="sonda"); regra 12 — nao ha bloco estratificado no c238')
print('=' * 100)
s = pd.read_csv(f'{F5}/sonda_f52e.csv')
ca2 = [c for c in s.columns if c.lower() in ('alg', 'algoritmo', 'config')][0]
sub = s[s[ca2] == 'c238']
print('  colunas:', list(s.columns))
print('  linhas c238 = %d' % len(sub))
if 'regime' in sub.columns:
    print('  regimes presentes:', sub.regime.value_counts().to_dict())
cb = [c for c in sub.columns if 'bloco' in c.lower() or c.lower() in ('geracao',)]
cw = [c for c in sub.columns if 'wape' in c.lower()]
cc = [c for c in sub.columns if 'cob' in c.lower()]
ck = [c for c in sub.columns if 'corr' in c.lower()]
cobj = [c for c in sub.columns if c.lower() in ('objetivo', 'obj', 'j')]
print('  chaves: bloco=%s wape=%s cob=%s corr=%s obj=%s' % (cb, cw, cc, ck, cobj))
if cw and cb and cobj:
    key = ['problema', cobj[0]] if 'problema' in sub.columns else [cobj[0]]
    g = sub.sort_values(cb[0]).groupby(key)
    prim = g.head(1).set_index(key); ult = g.tail(1).set_index(key)
    J = prim[[cw[0]] + (cc[:1]) + (ck[:1])].join(ult[[cw[0]] + (cc[:1]) + (ck[:1])], lsuffix='_1o', rsuffix='_ult')
    J['dWAPE'] = J[cw[0] + '_ult'] - J[cw[0] + '_1o']
    J.to_csv(f'{OUT}/sonda_c238_t11.csv')
    print('\n  pares (celula,objetivo) = %d' % len(J))
    print('  WAPE MELHORA (ultimo<primeiro) em %d/%d pares (%.1f%%) ; dWAPE mediano=%+.4f' % (
        int((J.dWAPE < 0).sum()), len(J), 100 * (J.dWAPE < 0).mean(), J.dWAPE.median()))
    if cc:
        print('  cobertura 2sigma: mediana 1o bloco=%.3f -> ultimo=%.3f ; pares <0.90 no fim = %d' % (
            J[cc[0] + '_1o'].median(), J[cc[0] + '_ult'].median(), int((J[cc[0] + '_ult'] < .90).sum())))
    print('\n  os 8 piores no ultimo bloco (WAPE):')
    print(J.sort_values(cw[0] + '_ult', ascending=False).head(8).to_string())
    print('\n  os 8 melhores:')
    print(J.sort_values(cw[0] + '_ult').head(8).to_string())

print()
print('=' * 100)
print('C5.5 — TEMPO (F5.2d) e a MAQUINA REAL (O-19)')
print('=' * 100)
t = pd.read_csv(f'{F5}/tempo_f52d.csv')
ca3 = [c for c in t.columns if c.lower() in ('alg', 'algoritmo', 'config')][0]
sub = t[t[ca3] == 'c238']
print('  colunas:', list(t.columns))
if 'maquina' in sub.columns:
    print('  maquinas:', sub.maquina.value_counts().to_dict())
    print(sub[['problema', 'maquina'] + [c for c in sub.columns if 'tempo' in c.lower() or 'wall' in c.lower()][:3]].to_string(index=False))
