#!/usr/bin/env python
"""BATERIA 11 e74/CLMEA — contrato/integridade/tempo + insumos da COMPARACAO CANONICA
(IGD cru da F5.2c p/ os 9 problemas com interseccao de familia) + rank global
+ re-checagem do n_front1 (pre x pos FE).
Escreve: e74_b11.txt, e74_b11_canonica.csv
"""
import json, os
import pandas as pd, numpy as np

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/e74'
ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
buf = []


def P(*a):
    s = ' '.join(str(x) for x in a); buf.append(s); print(s, flush=True)


pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

P('#'*100); P('# CONTRATO / INTEGRIDADE / TEMPO (F5.2a/b/d) — linhas do e74'); P('#'*100)
for nm in ['contrato_f52b', 'integridade_f52a']:
    c = pd.read_csv(f'{F5}/{nm}.csv')
    col = 'alg' if 'alg' in c.columns else c.columns[1]
    sub = c[c[col] == 'e74']
    P(f'  {nm}: linhas e74 = {len(sub)} (de {len(c)} no total) | colunas: {c.columns.tolist()}')
    if len(sub):
        P(sub.to_string(index=False))
tp = pd.read_csv(f'{F5}/tempo_f52d.csv')
te = tp[tp.alg == 'e74']
P(f'  tempo_f52d: linhas e74 = {len(te)} | colunas: {tp.columns.tolist()}')
P(te.to_string(index=False))
if 'maquina' in te.columns:
    P('  maquinas:', te.maquina.value_counts().to_dict())
    P('  wall total e74 (h): %.2f' % (te.wall_s.sum() / 3600))

P(''); P('#'*100); P('# METRICAS F5.2c — colunas e rank global'); P('#'*100)
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
P('  colunas:', m.columns.tolist())
mm = m[m.exp == 'main']
key = [c for c in m.columns if 'igd' in c.lower()]
P('  colunas de metrica com igd:', key)
kp = 'igd_plus' if 'igd_plus' in m.columns else ('igdplus' if 'igdplus' in m.columns else key[0])
P('  usando primaria =', kp)
pisos = ['moead', 'nsga2', 'nsga3', 'smsemoa']
rk_all, rk_sa, n_all = [], [], []
for pr, sub in mm.groupby('problema'):
    if not len(sub[sub.alg == 'e74']):
        continue
    v = float(sub[sub.alg == 'e74'][kp].iloc[0])
    rk_all.append(int((sub[kp] < v).sum() + 1)); n_all.append(len(sub))
    sa = sub[~sub.alg.isin(pisos + ['sobol_batch'])]
    rk_sa.append(int((sa[kp] < v).sum() + 1))
P('  rank medio e74 no conjunto COMPLETO (SA+pisos): %.2f de %.1f algs/problema' % (np.mean(rk_all), np.mean(n_all)))
P('  rank medio e74 entre os SA: %.2f' % np.mean(rk_sa))
P('  ranks completos por problema:', dict(zip(sorted(mm[mm.alg == 'e74'].problema), rk_all)))

P(''); P('#'*100); P('# COMPARACAO CANONICA — nossos numeros nos 9 problemas com interseccao de familia'); P('#'*100)
alvo = {'ZDT1': (30, 2), 'ZDT3': (30, 2), 'ZDT4': (10, 2), 'ZDT6': (10, 2),
        'DTLZ1': (7, 3), 'DTLZ2': (12, 3), 'DTLZ3': (12, 3), 'DTLZ4': (12, 3), 'DTLZ7': (22, 3)}
paper = {  # CLMEA no paper (Tabelas III/IV/V), IGD cru, 300 FEs, 20 runs
    'ZDT1': {30: 1.7209e-01, 50: 2.5621e-01, 100: 6.5192e-01, 200: 1.1857e+00},
    'ZDT3': {30: 8.0636e-01, 50: 1.2693e+00, 100: 1.8374e+00, 200: 2.0650e+00},
    'ZDT4': {30: 2.6938e+02, 50: 4.5928e+02, 100: 1.0032e+03, 200: 2.0531e+03},
    'ZDT6': {30: 1.6945e+00, 50: 2.5857e+00, 100: 4.2129e+00, 200: 5.6334e+00},
    'DTLZ1': {30: 2.8640e+02, 50: 4.5536e+02, 100: 9.3303e+02, 200: 2.1620e+03},
    'DTLZ2': {30: 2.9013e-01, 50: 8.9291e-01, 100: 1.7226e+00, 200: 3.1795e+00},
    'DTLZ3': {30: 6.7609e+02, 50: 1.1955e+03, 100: 2.6658e+03, 200: 5.7911e+03},
    'DTLZ4': {30: 1.0051e+00, 50: 1.2718e+00, 100: 1.8990e+00, 200: 3.2875e+00},
    'DTLZ7': {30: 8.0399e-01, 50: 1.4570e+00, 100: 3.5307e+00, 200: 6.3128e+00}}
rows = []
for pr, (D, M) in alvo.items():
    sub = mm[(mm.problema == pr) & (mm.alg == 'e74')]
    if not len(sub):
        continue
    r = sub.iloc[0]
    rows.append(dict(problema=pr, D=D, M=M, maxfe=31 * D - 1, init=11 * D - 1,
                     igd_nosso=float(r['igd']) if 'igd' in r else np.nan,
                     igdplus_nosso=float(r[kp]),
                     hv_nosso=float(r['hv']) if 'hv' in r else np.nan,
                     paper_D30=paper[pr][30], paper_menor_D=min(paper[pr]),
                     razao_orcamento=(31 * D - 1) / 300,
                     razao_D=D / 30))
CN = pd.DataFrame(rows); CN.to_csv(f'{OUT}/e74_b11_canonica.csv', index=False)
P(CN.round(5).to_string(index=False))

P(''); P('#'*100); P('# n_front1 — pre x pos FE (re-checagem)'); P('#'*100)


def nd1(F):
    n = len(F); k = 0
    for i in range(n):
        if not ((F <= F[i]).all(1) & (F < F[i]).any(1)).any():
            k += 1
    return k


tot = pre = pos = 0
for pr in sorted(os.listdir(ROOT)):
    b = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    M = [r for r in recs if r['rec'] == 'header'][0]['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(b + '__real.parquet')
    F = real[[f'f{i}' for i in range(M)]].to_numpy(np.float64)
    for ev in gens[:: max(1, len(gens) // 8)][:8]:
        na = ev['arquivo']
        tot += 1
        pos += int(nd1(F[:na]) == ev['n_front1'])
        pre += int(nd1(F[:na - ev['aceito']]) == ev['n_front1'])
P('  n_front1 == |ND1(arquivo POS-FE)|:', pos, '/', tot, '= %.1f%%' % (100 * pos / tot))
P('  n_front1 == |ND1(arquivo PRE-FE)|:', pre, '/', tot, '= %.1f%%' % (100 * pre / tot))
P('  (uniao: pelo menos uma das duas)', '-> amostra de', tot, 'eventos')

open(f'{OUT}/e74_b11.txt', 'w').write('\n'.join(buf))
print('\n[ok] e74_b11.txt')
