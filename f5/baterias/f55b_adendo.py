#!/usr/bin/env python3
# f55b_adendo.py — F5.5 (adendo): (A) a régua agrupada por FAMÍLIA de problema —
# a leitura que explica por que ela NÃO é monotônica em D; (B) a ablação do tier
# BIG pela camada ⑦ (c311 × treed_media), que a varredura do `off` não cobria.
import csv, os, sys, collections, statistics
import numpy as np

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, REPO)
os.chdir(REPO)
import pyarrow.parquet as pq  # noqa: E402
from src import metrics as MX  # noqa: E402

DIMS = {}
for r in csv.DictReader(open('claude_code_context/artifacts/characteristics.csv', encoding='utf-8')):
    DIMS[r['problema']] = int(r['D'])

def familia(p):
    for f in ('MMF16', 'MMF', 'DTLZ', 'WFG', 'ZDT', 'BBOB'):
        if p.startswith(f):
            return 'MMF' if f == 'MMF16' else f
    return '?'

OUT = ['# F5.5 — ADENDO: a régua por família e a ablação do tier big\n']
R = list(csv.DictReader(open('f5/transversal_regua.csv', encoding='utf-8')))

OUT.append('## A. A régua por FAMÍLIA de problema (a variável que explica melhor que D)\n')
fam = collections.defaultdict(lambda: [0, 0, 0, []])
for r in R:
    f = familia(r['problema'])
    fam[f][0] += int(r['n_sa_ganham'])
    fam[f][1] += int(r['n_sa'])
    fam[f][2] += int(r['n_conclusivas'])
    fam[f][3].append(DIMS[r['problema']])
OUT.append('| família | problemas | D (faixa) | SA batem o melhor piso | % | conclusivas |')
OUT.append('|---|---:|---|---|---:|---:|')
for f in sorted(fam, key=lambda f: -fam[f][0] / max(fam[f][1], 1)):
    g, t, c, ds = fam[f]
    OUT.append('| %s | %d | %d–%d | %d/%d | **%.0f%%** | %d |' %
               (f, len(ds), min(ds), max(ds), g, t, 100 * g / t, c))
OUT.append('\n**Leitura**: a fração de SA-MOEAs que batem o melhor piso varia mais por '
           'FAMÍLIA que por dimensão. A afirmação "a vantagem do surrogate cresce com D" '
           '(construída na R1 sobre 3 problemas: MMF1 D=2, DTLZ2 D=12, ZDT1 D=30) NÃO se '
           'sustenta no grid completo de 25 problemas — o que separa é a natureza do '
           'problema (multimodalidade/deceptividade × suavidade), não o número de '
           'variáveis. Base: 1 semente — descritivo, não teste (M13).\n')

OUT.append('\n## B. Ablação do tier BIG pela camada ⑦ — `c311` × `treed_media`\n')
OUT.append('> `treed_media` = "o c311 SEM os GPs locais" (T8/DI-35.2): árvore pura + RVEA '
           'sobre a média das folhas. A pergunta: **quanto os GPs locais acrescentam em '
           'N=50.000?** Endpoint = ⑦ (ND final avaliado na função real).\n')
rows = []
for dist in ('lhs', 'mvns'):
    exp = 'sweep-big-%s' % dist
    for p in ('DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4'):
        linha = {'dist': dist, 'problema': p, 'D': DIMS[p]}
        for alg in ('c311', 'treed_media'):
            if (exp, alg, p) == ('sweep-big-mvns', 'c311', 'MMF16_20'):
                linha[alg] = None  # REPROVADA-F5.1
                continue
            f7 = 'data/experiments/%s/%s/exp_%s_%s_%s_42__final.parquet' % (exp, alg, exp, alg, p)
            if not os.path.exists(f7):
                linha[alg] = None
                continue
            t = pq.read_table(f7)
            nd = np.asarray(t.column('nd_pos_real').to_pylist(), dtype=bool)
            fc = sorted([c for c in t.column_names if c[0] == 'f' and c[1:].isdigit()],
                        key=lambda c: int(c[1:]))
            F = np.column_stack([np.asarray(t.column(c), float) for c in fc])
            m = MX.metrics_of_set(F[nd] if nd.any() else F, p)
            linha[alg] = (round(m['igd_plus'], 5), round(float(nd.mean()), 3), len(nd))
        rows.append(linha)
OUT.append('| dist | problema | IGD+⑦ c311 | fantasia c311 | IGD+⑦ treed | fantasia treed | GPs ajudam? |')
OUT.append('|---|---|---:|---:|---:|---:|---|')
ajuda = collections.Counter()
for l in rows:
    a, b = l.get('c311'), l.get('treed_media')
    if a and b:
        v = '✔ sim' if a[0] < b[0] else ('✘ não' if a[0] > b[0] else 'empate')
        ajuda['sim' if a[0] < b[0] else 'não'] += 1
    else:
        v = '— (célula excluída)'
    OUT.append('| %s | %s | %s | %s | %s | %s | %s |' % (
        l['dist'], l['problema'],
        '%.4g' % a[0] if a else '—', '%.3f' % a[1] if a else '—',
        '%.4g' % b[0] if b else '—', '%.3f' % b[1] if b else '—', v))
OUT.append('\n**Placar**: os GPs locais melhoraram o endpoint em **%d** células big e '
           'pioraram em **%d** (de %d comparáveis). Custo: o c311-big roda ~100× mais caro '
           'que o treed_media (6-14 s/célula) — o insumo de custo×benefício da ablação.\n'
           % (ajuda['sim'], ajuda['não'], ajuda['sim'] + ajuda['não']))

with open('f5/transversal_big_ablacao.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['dist', 'problema', 'D', 'igd7_c311', 'fantasia_c311', 'n_c311',
                'igd7_treed', 'fantasia_treed', 'n_treed'])
    for l in rows:
        a, b = l.get('c311'), l.get('treed_media')
        w.writerow([l['dist'], l['problema'], l['D'],
                    a[0] if a else '', a[1] if a else '', a[2] if a else '',
                    b[0] if b else '', b[1] if b else '', b[2] if b else ''])

open('f5/transversais_f55_adendo.md', 'w', encoding='utf-8').write('\n'.join(OUT) + '\n')
print('\n'.join(OUT))
