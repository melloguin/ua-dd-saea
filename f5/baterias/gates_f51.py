#!/usr/bin/env python3
# gates_f51.py — F5.1: roda o portão (accept+auditar+final_eval) nas 666 células
# OK da semente 42, em paralelo, e consolida em CSV. Usa o env_main (B3).
import csv, os, subprocess, sys, json, collections
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
PY = '/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
OUT = os.path.join(REPO, 'f5', 'gates_f51.csv')
W = int(os.environ.get('W', '6'))

cells = [r for r in csv.DictReader(open(CENSO, encoding='utf-8')) if r['estado'] == 'OK']
assert len(cells) == 666, len(cells)

def gate(r):
    args = [PY, 'scripts/portao.py', '--exp', r['exp'], '--alg', r['alg'],
            '--problema', r['problema'], '--semente', '42']
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=1800)
    tail = (p.stdout or '').strip().splitlines()[-6:]
    return (r['exp'], r['alg'], r['problema'], p.returncode, ' | '.join(tail))

res = []
with ThreadPoolExecutor(max_workers=W) as ex:
    futs = {ex.submit(gate, r): r for r in cells}
    done = 0
    for f in as_completed(futs):
        res.append(f.result())
        done += 1
        if done % 50 == 0:
            print('%d/666' % done, flush=True)

res.sort()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['exp', 'alg', 'problema', 'exit', 'detalhe'])
    w.writerows(res)

vermelhos = [r for r in res if r[3] != 0]
por_cfg = collections.Counter(('%s/%s' % (r[0], r[1])) for r in vermelhos)
print(json.dumps({'total': len(res), 'verdes': len(res) - len(vermelhos),
                  'vermelhos': len(vermelhos),
                  'vermelhos_por_config': dict(por_cfg)}, indent=1))
for r in vermelhos[:40]:
    print('VERMELHO:', r[0], r[1], r[2], '|', r[4][:180])
