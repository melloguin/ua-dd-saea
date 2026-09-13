#!/usr/bin/env python3
# f52d_tempo.py — F5.2d: matriz de tempo config × célula (wall do ⑤ timing.tempo_total_s,
# chave ANINHADA), heatmap HTML standalone e projeção 30 sementes.
# Atribuição de máquina: roster do censo + correções conhecidas (main/e7 = Mac;
# main/c238 DIVIDIDO; main/b1 parcial Mac — fonte: _logs_lotes/mac/*done.txt).
import csv, os, json, glob, collections, html

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')

def label(exp, prob):
    if exp in ('main', 'off'):
        return prob
    if exp == 'batch':
        return 'q10_' + prob
    _, tier, dist = exp.split('-', 2)
    return 'swap_%s-%s_%s' % (tier, dist, prob)

# células realmente rodadas no Mac (recuperações O-19) — dos done.txt
mac_real = set()
for f in glob.glob(os.path.join(RAIZ, '_old', '_lotes_mac', '*done.txt')):
    for ln in open(f, encoding='utf-8', errors='ignore'):
        ln = ln.strip()
        if ln:
            mac_real.add(ln.split()[0] if ' ' in ln else ln)

REPROVADAS_F51 = {('sweep-big-mvns','c311','MMF16_20')}
rows = [r for r in csv.DictReader(open(CENSO, encoding='utf-8')) if r['estado'] == 'OK' and (r['exp'],r['alg'],r['problema']) not in REPROVADAS_F51]
tab = []
for r in rows:
    exp, alg, prob = r['exp'], r['alg'], r['problema']
    base = 'exp_%s_%s_%s_42' % (exp, alg, prob)
    man = os.path.join(RAIZ, alg, label(exp, prob), '42', base + '.manifest.json')
    wall = None
    try:
        m = json.load(open(man, encoding='utf-8'))
        wall = (m.get('timing') or {}).get('tempo_total_s')
    except Exception:
        pass
    run_id = '%s_%s_%s_42' % (exp, alg, prob)
    maq = 'mac*' if any(run_id in x for x in mac_real) else r['maquina_roster']
    tab.append({'exp': exp, 'alg': alg, 'problema': prob, 'label': label(exp, prob),
                'maquina': maq, 'wall_s': wall})

with open(os.path.join(REPO, 'f5', 'tempo_f52d.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=['exp', 'alg', 'problema', 'label', 'maquina', 'wall_s'])
    w.writeheader()
    w.writerows(tab)

# ── heatmap HTML (standalone, sem libs) ─────────────────────────────────────
labels = sorted({t['label'] for t in tab})
algs = sorted({t['alg'] for t in tab})
cel = {(t['alg'], t['label']): t['wall_s'] for t in tab}
valid = [t['wall_s'] for t in tab if t['wall_s']]
vmax = max(valid) if valid else 1.0

def cor(v):
    if v is None:
        return '#eee', ''
    import math
    f = math.log1p(v) / math.log1p(vmax)
    r = int(255)
    g = int(235 * (1 - f) + 40 * f)
    b = int(205 * (1 - f) + 40 * f)
    return '#%02x%02x%02x' % (r, g, b), fmt(v)

def fmt(s):
    if s is None:
        return ''
    if s < 60:
        return '%.0fs' % s
    if s < 3600:
        return '%.0fm' % (s / 60)
    return '%.1fh' % (s / 3600)

cells_html = []
cells_html.append('<tr><th></th>' + ''.join('<th>%s</th>' % html.escape(a) for a in algs) + '</tr>')
for L in labels:
    tds = ['<th style="text-align:left">%s</th>' % html.escape(L)]
    for a in algs:
        v = cel.get((a, L))
        c, txt = cor(v)
        tds.append('<td style="background:%s">%s</td>' % (c, txt))
    cells_html.append('<tr>' + ''.join(tds) + '</tr>')

doc = ('<title>Heatmap de tempo — rodada-42</title><style>body{font:12px -apple-system,sans-serif;'
       'padding:16px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;'
       'text-align:center;font-size:11px}th{background:#f5f5f5;position:sticky;top:0}</style>'
       '<h2>Wall-clock por célula — semente 42 (⑤ timing.tempo_total_s)</h2>'
       '<p>Escala log; vazio = sem timing. Fonte: manifests. Caveat §19: wall cross-stack só '
       'com ressalva; maquina "mac*" = recuperada no Mac (O-19).</p>'
       '<div style="overflow-x:auto"><table>' + ''.join(cells_html) + '</table></div>')
open(os.path.join(REPO, 'f5', 'tempo_heatmap.html'), 'w', encoding='utf-8').write(doc)

# ── projeção 30 sementes ────────────────────────────────────────────────────
por_cfg = collections.defaultdict(float)
n_sem_wall = 0
for t in tab:
    if t['wall_s'] is None:
        n_sem_wall += 1
        continue
    por_cfg['%s/%s' % (t['exp'].split('-')[0], t['alg'])] += t['wall_s']

linhas = ['# Projeção 30 sementes (M8/M9) — base: walls da semente 42', '',
          '| família/config | wall s42 (h) | ×30 (h-core) |', '|---|---:|---:|']
tot = 0.0
for k in sorted(por_cfg, key=lambda k: -por_cfg[k]):
    h = por_cfg[k] / 3600
    tot += h * 30
    linhas.append('| %s | %.1f | %.0f |' % (k, h, h * 30))
linhas += ['', 'TOTAL ≈ **%.0f h-core** (30 sementes, todos os configs)' % tot,
           '', 'Células sem timing no ⑤: %d' % n_sem_wall,
           '', 'Caveats: wall MATLAB×Python confundido por linguagem (§19); células '
           'recuperadas no Mac (mac*) rodaram em máquina ≠ roster; pisos ~segundos.']
open(os.path.join(REPO, 'f5', 'projecao_30seeds.md'), 'w', encoding='utf-8').write('\n'.join(linhas))
print(json.dumps({'celulas': len(tab), 'sem_wall': n_sem_wall,
                  'total_projetado_h_core': round(tot)}, indent=1))
