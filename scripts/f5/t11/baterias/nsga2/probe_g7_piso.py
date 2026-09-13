#!/usr/bin/env python
"""T11/nsga2 — PROVA de que o gate G-7 (contrato_61.json) NAO cobre a linha
"pisos" do CONTRATO §6.1 (l.335: `n_front1`; `f_best[]`; **ideal/nadir da pop
por geracao**). Copia o smoke para um TEMPDIR, remove `ideal`/`nadir_pop`/
`nadir_front1` dos 13 eventos de geracao e re-roda os 6 gates.
Producao NUNCA e tocada: so o tempdir. READ-ONLY sobre evidencia_T11."""
import json, os, shutil, sys, tempfile

ROOT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
SRC = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/nsga2'
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'scripts'))
os.chdir(ROOT)
import gates_proveniencia as G

T = tempfile.mkdtemp(prefix='g7probe_')
d = os.path.join(T, 'experiments', 'main', 'nsga2')
os.makedirs(d)
for f in os.listdir(SRC):
    shutil.copy(os.path.join(SRC, f), d)
jp = os.path.join(d, 'exp_main_nsga2_DTLZ2_42.jsonl')

def rodar(tag):
    print(f'[{tag}]')
    for n, ok, det in G.gates_de_proveniencia('main', 'nsga2', 'DTLZ2', 42, T, modo='campanha'):
        print('  %-18s %-5s %s' % (n, {True: 'OK', False: 'RUIM', None: 'n/a'}[ok], det[:120]))

rodar('CONTROLE — smoke intacto')
linhas = [json.loads(l) for l in open(jp) if l.strip()]
n = 0
for e in linhas:
    if e.get('rec') == 'nsga2_gen':
        for k in ('ideal', 'nadir_pop', 'nadir_front1'):
            e.pop(k, None)
        n += 1
with open(jp, 'w') as fh:
    for e in linhas:
        fh.write(json.dumps(e, ensure_ascii=False) + '\n')
rodar(f'MUTANTE — ideal/nadir_pop/nadir_front1 removidos de {n}/{n} eventos')
shutil.rmtree(T)
print('\ncontrato_61.json[nsga2].di10 =', json.load(
    open('claude_code_context/artifacts/contrato_61.json'))['configs']['nsga2']['di10'])
print('CONTRATO §6.1 l.335 (pisos) exige: n_front1 · f_best[] · ideal/nadir da pop por geracao')
