#!/usr/bin/env python
"""Parte 6: hashes de artefato (DoE/sonda) recomputados, contrato §6.1 do b1,
e a checagem explicita dos itens I-1..I-6 da torre no MEU config."""
import json, hashlib, numpy as np, pandas as pd

T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_42'
SON = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1'


def h64(M):
    return hashlib.sha256(np.ascontiguousarray(M, dtype='<f8').tobytes()).hexdigest()


man = json.load(open(T11 + '.manifest.json'))
recs = [json.loads(l) for l in open(T11 + '.jsonl') if l.strip()]
gen = [r for r in recs if r['rec'] == 'b1_gen']
sur = pd.read_parquet(T11 + '__surrogate.parquet')

doe = pd.read_parquet(DOE + '.parquet'); sc = json.load(open(DOE + '.manifest.json'))
print('DoE  sha256 recomputado :', h64(doe[['x0', 'x1']].to_numpy()))
print('DoE  sidecar doe_hash   :', sc['doe_hash'])
print('DoE  manifesto do run   :', man['doe_hash'])
print('DoE  header do 6        :', [r for r in recs if r['rec'] == 'header'][0]['doe_hash'])
print('DoE  3 batem            :', len({h64(doe[["x0","x1"]].to_numpy()), sc['doe_hash'], man['doe_hash']}) == 1)

son = pd.read_parquet(SON + '.parquet'); ss = json.load(open(SON + '.manifest.json'))
xh = h64(son[['x0', 'x1']].to_numpy())
print('\nsonda x_hash recomputado:', xh)
print('sonda sidecar           :', ss.get('x_hash'))
print('sonda manifesto do run  :', man['sonda']['x_hash'])
print('sonda evento do 6       :', [r for r in recs if r['rec'] == 'sonda'][0]['x_hash'])
print('sonda 3 batem           :', len({xh, ss.get('x_hash'), man['sonda']['x_hash']}) == 1)
print('sonda f_hash manifesto  :', man['sonda']['f_hash'][:16], '== sidecar', str(ss.get('f_hash'))[:16])

print('\n--- contrato_61 (b1) ---')
c = json.load(open('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/claude_code_context/artifacts/contrato_61.json'))
req6 = c['minimo_comum_di10']['campos'] + c['configs']['b1']['di10']
req5 = c['quinto_obrigatorio']['campos']
falta6 = [k for k in req6 if not all(k in g for g in gen)]
falta5 = [k for k in req5 if k not in man or man[k] in (None, '', {})]
print('6 campos exigidos :', req6, '-> faltando:', falta6 or 'nenhum')
print('5 chaves exigidas :', req5, '-> faltando/vazias:', falta5 or 'nenhuma')

print('\n--- I-1..I-6 da torre no b1 (o que se aplica) ---')
kg = set().union(*[set(g) for g in gen])
print('I-1 ref_ids/pmid_ids     :', 'ref_ids' in kg or 'pmid_ids' in kg, '(b1 nao e classificador nem tem referencia par-a-par -> N/A)')
print('I-2 REGRA_DO_ROTULO no 5 :', 'REGRA_DO_ROTULO' in json.dumps(man), '(N/A: b1 nao tem rotulo, sigma_dict e de VALOR)')
print('I-5 y_treino_dist        :', 'y_treino_dist' in json.dumps(man) or 'y_treino_dist' in kg, '(N/A: alvo escalar movel, D47)')
print('I-6 sonda_estratificada  :', 'sonda_estratificada' in set(sur.regime), '(N/A: A11 so nos 4 classificadores)')
print('I-3 tempo_aval_real_s    :', man['timing'].get('tempo_aval_real_s'), '-> nao-nulo:', bool(man['timing'].get('tempo_aval_real_s')))
print('I-4 NO_RETRY             : experiments.py:84 (conferido a parte)')
print('\nchaves do evento b1_gen  :', sorted(kg))
print('sigma_dict (5) chaves    :', sorted(man['sigma_dict']))
