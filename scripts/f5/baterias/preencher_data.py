#!/usr/bin/env python3
# preencher_data.py — hardlinka no data/experiments/ do repo as células s42 do
# staging que NÃO existem localmente. NUNCA sobrescreve arquivo existente
# (a cópia local tem ⑥ com footer — superior ao bucket). Read-only nas fontes.
import csv, os, glob, json, collections

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
STAG = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/_bucket_raw/experiments'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')

st = collections.Counter()
for r in csv.DictReader(open(CENSO, encoding='utf-8')):
    if r['estado'] != 'OK':
        continue
    exp, alg, prob = r['exp'], r['alg'], r['problema']
    base = 'exp_%s_%s_%s_42' % (exp, alg, prob)
    srcdir = os.path.join(STAG, exp, alg)
    dest = os.path.join(REPO, 'data', 'experiments', exp, alg)
    os.makedirs(dest, exist_ok=True)
    files = sorted(set(glob.glob(os.path.join(srcdir, base + '.*')) +
                       glob.glob(os.path.join(srcdir, base + '__*'))))
    for f in files:
        d = os.path.join(dest, os.path.basename(f))
        if os.path.exists(d):
            st['ja_local'] += 1
            continue
        os.link(f, d)
        st['linkados'] += 1
print(json.dumps(st, indent=1))
