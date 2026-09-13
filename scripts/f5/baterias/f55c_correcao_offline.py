#!/usr/bin/env python3
# f55c_correcao_offline.py — CORRECAO da secao 4 da F5.5 (sweep) apos critica do
# consolidador F5.6: as metricas da camada 1 EMPATAM por desenho entre os configs
# offline (a camada 1 E o dataset compartilhado; D69 le a camada 1). Provado:
# 119 linhas -> 30 valores distintos; 30/30 grupos (tier,dist,problema) com valor
# UNICO entre todos os algoritmos.
# => o sweep tem de ser medido pela camada 7 (ND final avaliado na funcao REAL),
#    exatamente como a secao 3 ja fazia para o `off`.
import csv, os, sys, collections, statistics
import numpy as np

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq  # noqa: E402
from src import metrics as MX  # noqa: E402

TOKENS = ['sweep-small-lhs', 'sweep-small-mvns', 'sweep-medium-lhs',
          'sweep-medium-mvns', 'sweep-big-lhs', 'sweep-big-mvns']
PROBS = ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4']
EXCL = {('sweep-big-mvns', 'c311', 'MMF16_20')}   # REPROVADA-F5.1

rows = []
for exp in TOKENS:
    tier, dist = exp.split('-')[1], exp.split('-')[2]
    d = os.path.join('data/experiments', exp)
    if not os.path.isdir(d):
        continue
    for alg in sorted(os.listdir(d)):
        for p in PROBS:
            if (exp, alg, p) in EXCL:
                continue
            f7 = os.path.join(d, alg, 'exp_%s_%s_%s_42__final.parquet' % (exp, alg, p))
            if not os.path.exists(f7):
                continue
            t = pq.read_table(f7)
            nd = np.asarray(t.column('nd_pos_real').to_pylist(), dtype=bool)
            fc = sorted([c for c in t.column_names if c[0] == 'f' and c[1:].isdigit()],
                        key=lambda c: int(c[1:]))
            F = np.column_stack([np.asarray(t.column(c), float) for c in fc])
            X = np.column_stack([np.asarray(t.column(c), float)
                                 for c in sorted([c for c in t.column_names
                                                  if c[0] == 'x' and c[1:].isdigit()],
                                                 key=lambda c: int(c[1:]))])
            # guarda contra "front" degenerado (b5m/ZDT4: 50 linhas, 1 X distinto)
            n_x_dist = len(np.unique(np.round(X, 9), axis=0))
            m = MX.metrics_of_set(F[nd] if nd.any() else F, p)
            rows.append([alg, tier, dist, p, len(nd), int(nd.sum()),
                         round(float(nd.mean()), 4), n_x_dist,
                         round(m['igd_plus'], 6), round(m['hv'], 6)])

with open('f5/transversal_sweep_camada7.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['alg', 'tier', 'dist', 'problema', 'n_final', 'n_nd_pos_real',
                'fantasia', 'n_x_distintos', 'igd_plus_c7', 'hv_c7'])
    w.writerows(rows)

O = ['# F5.5 §4 — CORRIGIDA: o sweep medido pela camada 7\n',
     '> **Por que esta correcao existe.** A versao anterior desta secao usou o IGD+ da',
     '> camada 1. Nos configs OFFLINE a camada 1 E o dataset compartilhado, entao a metrica',
     '> EMPATA por desenho entre todos os algoritmos do mesmo (tier, dist, problema) —',
     '> provado: 119 linhas colapsam em **30 valores distintos**, e **30/30 grupos tem valor',
     '> unico entre todos os algs**. Aquele placar media o DATASET, nao o algoritmo.',
     '> O discriminante correto e a camada 7 (ND final avaliado na funcao REAL), como a',
     '> secao 3 ja fazia para o `off`. Achado do consolidador F5.6, confirmado e corrigido.\n']

# ── tier: mais dado -> melhor? (por config, por dist, por problema) ─────────
by = collections.defaultdict(dict)
for a, t, d, p, nf, nnd, fant, nx, ig, hv in rows:
    by[(a, d, p)][t] = (ig, fant, nx)
O.append('## A. "Mais dado -> melhor?" — pela camada 7\n')
O.append('| config | dist | problema | small | medium | big | melhora? |')
O.append('|---|---|---|---:|---:|---:|---|')
pl = collections.Counter()
for (a, d, p), v in sorted(by.items()):
    if len(v) < 2:
        continue
    maior = 'big' if 'big' in v else 'medium'
    if 'small' not in v:
        continue
    ok = v[maior][0] < v['small'][0]
    pl['sim' if ok else 'nao'] += 1
    g = lambda t: ('%.4g' % v[t][0]) if t in v else '—'
    O.append('| %s | %s | %s | %s | %s | %s | %s |'
             % (a, d, p, g('small'), g('medium'), g('big'), 'sim' if ok else 'NAO'))
O.append('\n**Placar (camada 7)**: mais dado melhorou o endpoint em **%d** series; piorou em **%d**.\n'
         % (pl['sim'], pl['nao']))

# ── LHS x MVNS ─────────────────────────────────────────────────────────────
lm = collections.Counter()
for (a, d, p), v in by.items():
    if d != 'lhs':
        continue
    o = by.get((a, 'mvns', p), {})
    for t in v:
        if t in o:
            lm['LHS' if v[t][0] < o[t][0] else 'MVNS'] += 1
O.append('**LHS x MVNS (camada 7, mesma celula)**: LHS melhor em **%d**, MVNS em **%d**.\n'
         % (lm['LHS'], lm['MVNS']))

# ── ranking por config no sweep (agora discrimina) ─────────────────────────
O.append('## B. Ranking dos configs no sweep (camada 7) — agora DISCRIMINA\n')
rk = collections.defaultdict(list)
grp = collections.defaultdict(dict)
for a, t, d, p, nf, nnd, fant, nx, ig, hv in rows:
    grp[(t, d, p)][a] = ig
for k, v in grp.items():
    for i, (a, _) in enumerate(sorted(v.items(), key=lambda kv: kv[1])):
        rk[a].append(i + 1)
O.append('| config | rank medio | celulas | fantasia mediana | vitorias |')
O.append('|---|---:|---:|---:|---:|')
vit = collections.Counter()
for k, v in grp.items():
    vit[min(v, key=v.get)] += 1
fant_by = collections.defaultdict(list)
degen = collections.defaultdict(int)
for a, t, d, p, nf, nnd, fant, nx, ig, hv in rows:
    fant_by[a].append(fant)
    if nx == 1:
        degen[a] += 1
for a in sorted(rk, key=lambda a: statistics.mean(rk[a])):
    O.append('| %s | %.2f | %d | %.3f | %d |'
             % (a, statistics.mean(rk[a]), len(rk[a]),
                statistics.median(fant_by[a]), vit[a]))
if degen:
    O.append('\n**Guarda de front degenerado**: celulas cuja camada 7 tem 1 unico X distinto '
             '(o "front" e uma duplicata): ' + ', '.join('%s=%d' % kv for kv in degen.items())
             + ' — reportadas, nao usadas como evidencia de qualidade.\n')

open('f5/transversais_f55_sec4_corrigida.md', 'w', encoding='utf-8').write('\n'.join(O) + '\n')
print('\n'.join(O))
