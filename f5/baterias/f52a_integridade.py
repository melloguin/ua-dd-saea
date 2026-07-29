#!/usr/bin/env python3
# f52a_integridade.py — F5.2a: o "OK de não-corrompido" — abre TODO arquivo das 666
# células organizadas: parquet (pyarrow, linhas), jsonl (parse linha a linha), manifest
# (json). Saída: f5/integridade_f52a.csv + resumo JSON no stdout. READ-ONLY.
import csv, os, json, glob, collections, sys

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
CENSO = os.path.expanduser('~/censo_bucket_42.csv')
import pyarrow.parquet as pq

def label(exp, prob):
    if exp in ('main', 'off'):
        return prob
    if exp == 'batch':
        return 'q10_' + prob
    _, tier, dist = exp.split('-', 2)
    return 'swap_%s-%s_%s' % (tier, dist, prob)

REPROVADAS_F51 = {('sweep-big-mvns','c311','MMF16_20')}
rows = [r for r in csv.DictReader(open(CENSO, encoding='utf-8')) if r['estado'] == 'OK' and (r['exp'],r['alg'],r['problema']) not in REPROVADAS_F51]
out, st = [], collections.Counter()
VAZIA_OK = {'__pop.parquet'}  # ② pode ter 0 linhas por desenho (família offline DI-16.17)

for r in rows:
    exp, alg, prob = r['exp'], r['alg'], r['problema']
    base = 'exp_%s_%s_%s_42' % (exp, alg, prob)
    d = os.path.join(RAIZ, alg, label(exp, prob), '42')
    for f in sorted(os.listdir(d)):
        if not f.startswith(base):
            continue
        path = os.path.join(d, f)
        suf = f[len(base):]
        veredito, detalhe = 'OK', ''
        try:
            if f.endswith('.parquet'):
                t = pq.read_table(path)
                n = t.num_rows
                detalhe = 'linhas=%d cols=%d' % (n, t.num_columns)
                if n == 0 and suf not in VAZIA_OK:
                    veredito = 'VAZIO'
            elif f.endswith('.manifest.json'):
                m = json.load(open(path, encoding='utf-8'))
                detalhe = 'status=%s' % m.get('status')
            elif f.endswith('.jsonl'):
                bad = 0
                nl = 0
                footer = False
                with open(path, encoding='utf-8', errors='strict') as fh:
                    for ln in fh:
                        ln = ln.strip()
                        if not ln:
                            continue
                        nl += 1
                        try:
                            ev = json.loads(ln)
                            if ev.get('rec') == 'footer':
                                footer = True
                        except Exception:
                            bad += 1
                detalhe = 'linhas=%d ruins=%d footer=%s' % (nl, bad, footer)
                if bad > 1:  # 1 linha rasgada no fim = assinatura conhecida de flush
                    veredito = 'JSONL_RUIM'
                elif bad == 1:
                    veredito = 'JSONL_1LINHA_RASGADA'
        except Exception as e:
            veredito, detalhe = 'ERRO', '%s: %s' % (type(e).__name__, str(e)[:120])
        st[veredito] += 1
        if veredito != 'OK':
            out.append([alg, exp, prob, suf, veredito, detalhe])

os.makedirs(os.path.join(REPO, 'f5'), exist_ok=True)
with open(os.path.join(REPO, 'f5', 'integridade_f52a.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['alg', 'exp', 'problema', 'camada', 'veredito', 'detalhe'])
    w.writerows(out)
print(json.dumps(st, indent=1))
for o in out[:30]:
    print('NAO-OK:', o)
sys.exit(0)
