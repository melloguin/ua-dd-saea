#!/usr/bin/env python3
# organizar_666.py — organiza as 666 células OK do staging (_bucket_raw) no layout do autor:
#   {alg}/{label}/{seed}/  onde label = problema (main/off) | q10_{problema} (batch)
#   | swap_{tier}-{dist}_{problema} (sweep — tier/dist no nome p/ não colidir os 6 tokens).
# Hardlinks (zero disco extra). Melhor-fonte do ⑥: bucket nunca tem footer nos runs
# Python (upload precede fechamento) → se o jsonl local (repo ou _maquinas) tem footer
# e é >= e com a 1ª linha idêntica, substitui e registra em _FONTES.csv.
# READ-ONLY nas fontes; escreve SÓ em resultados_experimentos/{alg}/... e nos CSVs de meta.
import csv, os, shutil, glob, collections, json, sys

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
STAG = RAIZ + '/_bucket_raw/experiments'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
MAQS = [RAIZ + '/_maquinas/' + m + '/experiments' for m in ('mac', 'v5', 'v6', 'vm3')]
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
SEED = '42'

CAMADA_SUF = {'1': '__real.parquet', '2': '__pop.parquet', '3': '__surrogate.parquet',
              '4': '__timing.parquet', '5': '.manifest.json', '6': '.jsonl',
              '7': '__final.parquet'}

def label(exp, prob):
    if exp in ('main', 'off'):
        return prob
    if exp == 'batch':
        return 'q10_' + prob
    if exp.startswith('sweep-'):
        _, tier, dist = exp.split('-', 2)
        return 'swap_%s-%s_%s' % (tier, dist, prob)
    raise ValueError(exp)

def tem_footer(path):
    try:
        sz = os.path.getsize(path)
        with open(path, 'rb') as f:
            f.seek(max(0, sz - 8192))
            tail = f.read().decode('utf-8', 'ignore')
        return '"rec": "footer"' in tail or '"rec":"footer"' in tail
    except OSError:
        return False

rows = [r for r in csv.DictReader(open(CENSO, encoding='utf-8')) if r['estado'] == 'OK']
assert len(rows) == 666, 'censo OK != 666: %d' % len(rows)

fontes, problemas = [], []
st = collections.Counter()
for r in rows:
    exp, alg, prob = r['exp'], r['alg'], r['problema']
    base = 'exp_%s_%s_%s_%s' % (exp, alg, prob, SEED)
    srcdir = os.path.join(STAG, exp, alg)
    files = sorted(set(glob.glob(os.path.join(srcdir, base + '.*')) +
                       glob.glob(os.path.join(srcdir, base + '__*'))))
    if not files:
        problemas.append([alg, exp, prob, 'NENHUM arquivo no staging'])
        continue
    dest = os.path.join(RAIZ, alg, label(exp, prob), SEED)
    os.makedirs(dest, exist_ok=True)
    for f in files:
        d = os.path.join(dest, os.path.basename(f))
        if os.path.exists(d):
            os.remove(d)
        try:
            os.link(f, d)
        except OSError:
            shutil.copy2(f, d)
        st['arquivos'] += 1
    st['celulas'] += 1

    # melhor-fonte do ⑥
    jl = os.path.join(dest, base + '.jsonl')
    if os.path.exists(jl) and not tem_footer(jl):
        cands = [os.path.join(REPO, 'data', 'experiments', exp, alg, base + '.jsonl')] + \
                [os.path.join(m, exp, alg, base + '.jsonl') for m in MAQS]
        achou = False
        for c in cands:
            if os.path.exists(c) and tem_footer(c) and os.path.getsize(c) >= os.path.getsize(jl):
                with open(c, encoding='utf-8', errors='ignore') as fc, \
                     open(jl, encoding='utf-8', errors='ignore') as fj:
                    if fc.readline() != fj.readline():
                        continue
                os.remove(jl)
                shutil.copy2(c, jl)
                fontes.append([alg, exp, prob, '6-jsonl', c])
                st['jsonl_substituidos'] += 1
                achou = True
                break
        if not achou:
            st['jsonl_sem_footer_sem_fonte'] += 1
            problemas.append([alg, exp, prob, 'jsonl SEM footer e sem fonte melhor'])

# ── verificação D3: camadas presentes vs assinatura do censo ────────────────
faltas = []
for r in rows:
    exp, alg, prob = r['exp'], r['alg'], r['problema']
    base = 'exp_%s_%s_%s_%s' % (exp, alg, prob, SEED)
    dest = os.path.join(RAIZ, alg, label(exp, prob), SEED)
    for tag in r['camadas']:
        f = os.path.join(dest, base + CAMADA_SUF[tag])
        if not os.path.exists(f):
            faltas.append([alg, exp, prob, tag])

with open(os.path.join(RAIZ, '_FONTES.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['alg', 'exp', 'problema', 'camada', 'fonte_local_usada'])
    w.writerows(fontes)

print(json.dumps({'celulas': st['celulas'], 'arquivos': st['arquivos'],
                  'jsonl_substituidos_por_fonte_local': st['jsonl_substituidos'],
                  'jsonl_sem_footer_sem_fonte': st['jsonl_sem_footer_sem_fonte'],
                  'faltas_vs_censo': len(faltas), 'problemas': len(problemas)},
                 indent=1))
for p in problemas[:20]:
    print('PROBLEMA:', p)
for f in faltas[:20]:
    print('FALTA:', f)
sys.exit(1 if (faltas or problemas) else 0)
