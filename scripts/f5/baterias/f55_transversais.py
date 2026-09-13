#!/usr/bin/env python3
# f55_transversais.py — F5.5: os comparativos que exigem a visão do TODO.
# 1) A RÉGUA: SA vs pisos por dimensão (a tese: vantagem cresce com D)
# 2) Ranking global e por característica de problema
# 3) OFFLINE: endpoint ⑦ (nd_pos_real / f real) — NUNCA as métricas da ①,
#    que empatam por desenho entre os 5 offline (achado F5.3a/c311)
# 4) SWEEP: mais dado → melhor? (small→medium→big; LHS×MVNS)
# 5) BATCH q=1 × q=10 (caveat DI-37.4: contraste limpo = c262/e81)
# 6) A ablação D77 (b5r/b5m × moead_media) e big (c311 × treed_media)
# Saídas: f5/transversais_f55.md + f5/transversais_*.csv  READ-ONLY nos dados.
import csv, json, os, sys, collections, statistics
import numpy as np

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq  # noqa: E402

PISOS_ON = ['nsga2', 'nsga3', 'moead', 'smsemoa']
SA_ON = ['b1', 'b3', 'b4', 'c122', 'c141', 'c149', 'c154', 'c217', 'c238',
         'c262', 'e7', 'e74', 'e81']
OFFLINE = ['e103', 'b5r', 'b5m', 'c311', 'moead_media', 'treed_media']
EXCLUIDAS = {('sweep-big-mvns', 'c311', 'MMF16_20'), ('main', 'b1', 'WFG1')}

DIMS, CARACT = {}, {}
with open('claude_code_context/artifacts/characteristics.csv', encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        DIMS[r['problema']] = int(r['D'])
        CARACT[r['problema']] = r

M = list(csv.DictReader(open('f5/metricas_finais_f52c.csv', encoding='utf-8')))
MET = {(r['exp'], r['alg'], r['problema']): r for r in M if r['igd_plus']}
OUT = []


def w(s=''):
    OUT.append(s)


def label(exp, prob):
    if exp in ('main', 'off'):
        return prob
    if exp == 'batch':
        return 'q10_' + prob
    _, t, d = exp.split('-', 2)
    return 'swap_%s-%s_%s' % (t, d, prob)


# ══ 1. A RÉGUA ══════════════════════════════════════════════════════════════
w('# F5.5 — Comparativos transversais (semente 42)\n')
w('> Métrica primária IGD+ (D70). Piso de ruído entre máquinas: HV ≤1,55%, '
  'IGD+ até 58,98% (O-18) — diferenças abaixo disso NÃO são conclusivas. '
  'Base = 1 semente: tudo aqui é DESCRITIVO, não teste estatístico (isso é M13).\n')
w('## 1. A RÉGUA — SA-MOEAs vs pisos, por dimensão\n')
probs = sorted({r['problema'] for r in M if r['exp'] == 'main'}, key=lambda p: (DIMS[p], p))
linhas, por_D = [], collections.defaultdict(lambda: [0, 0])
detalhe = []
for p in probs:
    cel = {a: float(MET[('main', a, p)]['igd_plus'])
           for a in PISOS_ON + SA_ON if ('main', a, p) in MET}
    pisos = {a: v for a, v in cel.items() if a in PISOS_ON}
    sa = {a: v for a, v in cel.items() if a in SA_ON}
    if not pisos or not sa:
        continue
    bp_alg = min(pisos, key=pisos.get)
    bp = pisos[bp_alg]
    ganham = [a for a, v in sa.items() if v < bp]
    # vitória CONCLUSIVA: melhora > piso de ruído do IGD+ (58,98%)
    conclusivas = [a for a in ganham if sa[a] < bp * (1 - 0.5898)]
    por_D[DIMS[p]][0] += len(ganham)
    por_D[DIMS[p]][1] += len(sa)
    melhor_sa = min(sa, key=sa.get)
    linhas.append([p, DIMS[p], bp_alg, '%.4g' % bp, melhor_sa, '%.4g' % sa[melhor_sa],
                   len(ganham), len(sa), len(conclusivas)])
    detalhe.append((p, DIMS[p], sorted(ganham)))
w('| problema | D | melhor piso | IGD+ | melhor SA | IGD+ | SA>piso | conclusivas |')
w('|---|---:|---|---:|---|---:|---:|---:|')
for l in linhas:
    w('| %s | %d | %s | %s | %s | %s | %d/%d | %d |' % (l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8]))
w('\n**Agregado por dimensão** (a tese: a vantagem do surrogate cresce com D):\n')
w('| D | células SA que batem o melhor piso | % |')
w('|---:|---|---:|')
for d in sorted(por_D):
    g, t = por_D[d]
    w('| %d | %d/%d | %.0f%% |' % (d, g, t, 100 * g / t))
with open('f5/transversal_regua.csv', 'w', newline='', encoding='utf-8') as fh:
    cw = csv.writer(fh)
    cw.writerow(['problema', 'D', 'melhor_piso', 'igd_piso', 'melhor_sa', 'igd_sa',
                 'n_sa_ganham', 'n_sa', 'n_conclusivas'])
    cw.writerows(linhas)

# ══ 2. RANKING GLOBAL ═══════════════════════════════════════════════════════
w('\n## 2. Ranking global no `main` (rank médio de IGD+ nos 25 problemas)\n')
ranks = collections.defaultdict(list)
for p in probs:
    cel = sorted([(a, float(MET[('main', a, p)]['igd_plus']))
                  for a in PISOS_ON + SA_ON if ('main', a, p) in MET], key=lambda kv: kv[1])
    for i, (a, _) in enumerate(cel):
        ranks[a].append(i + 1)
w('| # | config | tipo | rank médio | melhor | pior | n |')
w('|---:|---|---|---:|---:|---:|---:|')
for i, (a, v) in enumerate(sorted(ranks.items(), key=lambda kv: statistics.mean(kv[1]))):
    w('| %d | %s | %s | %.2f | %d | %d | %d |' % (i + 1, a, 'piso' if a in PISOS_ON else 'SA',
                                                  statistics.mean(v), min(v), max(v), len(v)))

# ══ 3. OFFLINE: o endpoint ⑦ ════════════════════════════════════════════════
w('\n## 3. OFFLINE — o endpoint é a ⑦, não a ①\n')
w('> As métricas da ① EMPATAM por desenho entre os 5 offline (a ① É o mesmo dataset '
  'compartilhado; D69 lê a ①). O discriminante é a camada ⑦: o ND final avaliado 1× na '
  'função REAL. `fantasia` = fração do "front" do modelo que sobrevive à realidade '
  '(`nd_pos_real`/n_final) — quanto MAIOR, menos o modelo se iludiu.\n')
rows7 = []
for alg in OFFLINE:
    for p in sorted(probs, key=lambda p: (DIMS[p], p)):
        base = 'data/experiments/off/%s/exp_off_%s_%s_42__final.parquet' % (alg, alg, p)
        if not os.path.exists(base):
            continue
        t = pq.read_table(base)
        nd = np.asarray(t.column('nd_pos_real').to_pylist(), dtype=bool)
        fcols = sorted([c for c in t.column_names if c[0] == 'f' and c[1:].isdigit()],
                       key=lambda c: int(c[1:]))
        F = np.column_stack([np.asarray(t.column(c), float) for c in fcols])
        try:
            from src import metrics as MX
            mm = MX.metrics_of_set(F[nd] if nd.any() else F, p)
            igd7, hv7 = mm['igd_plus'], mm['hv']
        except Exception:
            igd7, hv7 = float('nan'), float('nan')
        rows7.append([alg, p, DIMS[p], len(nd), int(nd.sum()),
                      round(float(nd.mean()), 4), round(igd7, 6), round(hv7, 6)])
with open('f5/transversal_offline_camada7.csv', 'w', newline='', encoding='utf-8') as fh:
    cw = csv.writer(fh)
    cw.writerow(['alg', 'problema', 'D', 'n_final', 'n_nd_pos_real', 'fantasia',
                 'igd_plus_c7', 'hv_c7'])
    cw.writerows(rows7)
agg = collections.defaultdict(list)
for r in rows7:
    agg[r[0]].append(r)
w('| config | células | fantasia mediana | IGD+⑦ mediano | vitórias IGD+⑦ (vs os outros offline) |')
w('|---|---:|---:|---:|---:|')
por_prob = collections.defaultdict(dict)
for r in rows7:
    if r[6] == r[6]:
        por_prob[r[1]][r[0]] = r[6]
vit = collections.Counter()
for p, d in por_prob.items():
    if d:
        vit[min(d, key=d.get)] += 1
for alg in OFFLINE:
    rs = agg.get(alg, [])
    if not rs:
        continue
    w('| %s | %d | %.3f | %.4g | %d |' % (
        alg, len(rs), statistics.median(r[5] for r in rs),
        statistics.median([r[6] for r in rs if r[6] == r[6]] or [float('nan')]), vit[alg]))

# ══ 4. SWEEP ════════════════════════════════════════════════════════════════
w('\n## 4. SWEEP — "mais dado → melhor?" (tier) e LHS × MVNS (distribuição)\n')
sw_rows = []
for r in M:
    if r['exp'].startswith('sweep-') and r['igd_plus']:
        _, tier, dist = r['exp'].split('-', 2)
        sw_rows.append([r['alg'], tier, dist, r['problema'], float(r['igd_plus']), float(r['hv'])])
by = collections.defaultdict(dict)
for alg, tier, dist, p, ig, hv in sw_rows:
    by[(alg, dist, p)][tier] = ig
w('| config | dist | problema | small | medium | big | melhora small→maior |')
w('|---|---|---|---:|---:|---:|---|')
melhora = collections.Counter()
for (alg, dist, p), d in sorted(by.items()):
    if len(d) < 2:
        continue
    ts = [d.get(t) for t in ('small', 'medium', 'big')]
    maior = 'big' if 'big' in d else 'medium'
    ok = d[maior] < d.get('small', float('inf'))
    melhora['sim' if ok else 'não'] += 1
    w('| %s | %s | %s | %s | %s | %s | %s |' % (
        alg, dist, p,
        '%.4g' % ts[0] if ts[0] else '—', '%.4g' % ts[1] if ts[1] else '—',
        '%.4g' % ts[2] if ts[2] else '—', '✔' if ok else '✘'))
w('\n**Placar tier**: mais dado melhorou o IGD+ em **%d** séries; piorou em **%d**.\n'
  % (melhora['sim'], melhora['não']))
lm = collections.Counter()
for (alg, dist, p), d in by.items():
    for t, v in d.items():
        o = by.get((alg, 'mvns' if dist == 'lhs' else 'lhs', p), {}).get(t)
        if o is not None and dist == 'lhs':
            lm['LHS' if v < o else 'MVNS'] += 1
w('**Placar distribuição** (mesma célula, LHS × MVNS): LHS melhor em **%d**, '
  'MVNS melhor em **%d**.\n' % (lm['LHS'], lm['MVNS']))
with open('f5/transversal_sweep.csv', 'w', newline='', encoding='utf-8') as fh:
    cw = csv.writer(fh)
    cw.writerow(['alg', 'tier', 'dist', 'problema', 'igd_plus', 'hv'])
    cw.writerows(sw_rows)

# ══ 5. BATCH ════════════════════════════════════════════════════════════════
w('\n## 5. BATCH q=10 × main q=1 (⚠ orçamentos DIFERENTES: batch = 11D−1+2000)\n')
w('> Caveat DI-37.4: o contraste limpo é c262/e81 (o c154 saiu do roster por DI-40 e '
  'carrega 2 confounders). `sobol_batch` é o CONTROLE — todo SA-batch deve batê-lo.\n')
bt = [r for r in M if r['exp'] == 'batch' and r['igd_plus']]
bprobs = sorted({r['problema'] for r in bt}, key=lambda p: (DIMS[p], p))
algs_b = sorted({r['alg'] for r in bt})
w('| problema | D | ' + ' | '.join(algs_b) + ' | q=1 (melhor SA main) |')
w('|---|---:|' + '---:|' * (len(algs_b) + 1))
for p in bprobs:
    cel = {r['alg']: float(r['igd_plus']) for r in bt if r['problema'] == p}
    m1 = [float(MET[('main', a, p)]['igd_plus']) for a in SA_ON if ('main', a, p) in MET]
    w('| %s | %d | %s | %s |' % (
        p, DIMS[p],
        ' | '.join('%.4g' % cel[a] if a in cel else '—' for a in algs_b),
        '%.4g' % min(m1) if m1 else '—'))
sob = {r['problema']: float(r['igd_plus']) for r in bt if r['alg'] == 'sobol_batch'}
w('\n**Vs o controle Sobol**:')
for a in algs_b:
    if a == 'sobol_batch':
        continue
    d = {r['problema']: float(r['igd_plus']) for r in bt if r['alg'] == a}
    v = sum(1 for p in d if p in sob and d[p] < sob[p])
    w('- `%s`: bate o Sobol em **%d/%d** problemas' % (a, v, len(d)))

# ══ 6. ABLAÇÕES ═════════════════════════════════════════════════════════════
w('\n## 6. Ablações declaradas (D77 e big)\n')
w('> **D77**: `moead_media` = "o b5 sem σ" — mesmo motor, mesmo surrogate, mesmo '
  'lattice; muda SÓ a seleção. **Big**: `treed_media` = "o c311 sem os GPs locais".\n')
f7 = {(r[0], r[1]): r for r in rows7}
w('| problema | b5m (σ) | moead_media (μ) | quem espalha mais | c311 | treed_media |')
w('|---|---:|---:|---|---:|---:|')
for p in sorted({r[1] for r in rows7}, key=lambda p: (DIMS[p], p)):
    g = lambda a: ('%.3f' % f7[(a, p)][5]) if (a, p) in f7 else '—'
    n = lambda a: (f7[(a, p)][4] if (a, p) in f7 else None)
    b5m_, pis = n('b5m'), n('moead_media')
    quem = '—' if b5m_ is None or pis is None else ('b5m' if b5m_ > pis else ('piso' if pis > b5m_ else 'empate'))
    w('| %s | %s | %s | %s | %s | %s |' % (p, g('b5m'), g('moead_media'), quem, g('c311'), g('treed_media')))

open('f5/transversais_f55.md', 'w', encoding='utf-8').write('\n'.join(OUT) + '\n')
print('\n'.join(OUT[:60]))
print('\n... (completo em f5/transversais_f55.md)')
