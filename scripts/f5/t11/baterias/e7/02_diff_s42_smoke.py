#!/usr/bin/env python
"""T11/e7 — o que a instrumentacao T11 ACRESCENTOU: diff de schema s42 x smoke.
READ-ONLY."""
import json, glob, os
import pandas as pd

S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'

def carrega(base):
    man = json.load(open(base + '.manifest.json'))
    ev = [json.loads(x) for x in open(base + '.jsonl')]
    return man, ev

def chaves_por_rec(ev):
    d = {}
    for e in ev:
        r = e.get('rec', '?')
        d.setdefault(r, set()).update(e.keys())
    return {k: sorted(v) for k, v in d.items()}

alvos = {
    's42_MMF1':  f'{S42}/MMF1/42/exp_main_e7_MMF1_42',
    's42_MMF11_L': f'{S42}/MMF11_L/42/exp_main_e7_MMF11_L_42',
    's42_ZDT1':  f'{S42}/ZDT1/42/exp_main_e7_ZDT1_42',
    'smokeT11_MMF11_L': f'{EV}/smoke_matlab/experiments/main/e7/exp_main_e7_MMF11_L_42',
    'smokeT11_MMF1(g6com)': f'{EV}/g6_com/experiments/main/e7/exp_main_e7_MMF1_42',
}
res = {}
for nome, base in alvos.items():
    man, ev = carrega(base)
    res[nome] = {
        'manifest_keys': sorted(man.keys()),
        'params': man.get('params'),
        'sigma_dict': man.get('sigma_dict'),
        'timing_keys': sorted((man.get('timing') or {}).keys()),
        'timing': man.get('timing'),
        'env_keys': sorted((man.get('env') or {}).keys()),
        'sonda_keys': sorted((man.get('sonda') or {}).keys()),
        'recs': chaves_por_rec(ev),
        'n_ev': len(ev),
        'schema_version': man.get('schema_version'),
        'campanha_id': man.get('campanha_id'),
        'repo_hash': man.get('repo_hash'),
        'motivo_parada': man.get('motivo_parada', '<<AUSENTE>>'),
        'footer': [e for e in ev if e.get('rec') == 'footer'],
        'header': [e for e in ev if e.get('rec') == 'header'],
        'guards': [e for e in ev if e.get('rec') == 'guard'],
        'ex_gen': next((e for e in ev if e.get('rec') == 'e7_gen'), None),
        'ex_sonda': next((e for e in ev if e.get('rec') == 'sonda'), None),
    }
    df = pd.read_parquet(base + '__surrogate.parquet')
    res[nome]['sur_cols'] = list(df.columns)
    res[nome]['sur_regimes'] = df['regime'].value_counts().to_dict()
    dt = pd.read_parquet(base + '__timing.parquet')
    res[nome]['tim_cols'] = list(dt.columns)
    res[nome]['tim_nonnull'] = {c: int(dt[c].notna().sum()) for c in dt.columns}
    res[nome]['tim_n'] = len(dt)
    dr = pd.read_parquet(base + '__real.parquet')
    res[nome]['real_cols'] = list(dr.columns)

json.dump(res, open(f'{OUT}/diff_schema_e7.json', 'w'), indent=1, default=str)

# imprime o DIFF
A = res['s42_MMF11_L']; B = res['smokeT11_MMF11_L']
print('== MANIFEST keys: NOVAS no T11 ==', sorted(set(B['manifest_keys']) - set(A['manifest_keys'])))
print('== MANIFEST keys: SUMIRAM      ==', sorted(set(A['manifest_keys']) - set(B['manifest_keys'])))
print('== params NOVOS ==', sorted(set((B['params'] or {}).keys()) - set((A['params'] or {}).keys())))
print('== params SUMIRAM==', sorted(set((A['params'] or {}).keys()) - set((B['params'] or {}).keys())))
print('== timing NOVOS  ==', sorted(set(B['timing_keys']) - set(A['timing_keys'])))
print('== env NOVOS     ==', sorted(set(B['env_keys']) - set(A['env_keys'])))
print('== sonda NOVOS   ==', sorted(set(B['sonda_keys']) - set(A['sonda_keys'])))
print('== sigma_dict s42   ==', json.dumps(A['sigma_dict'], ensure_ascii=False))
print('== sigma_dict smoke ==', json.dumps(B['sigma_dict'], ensure_ascii=False))
for rec in sorted(set(A['recs']) | set(B['recs'])):
    a = set(A['recs'].get(rec, [])); b = set(B['recs'].get(rec, []))
    print(f'-- rec {rec}: NOVAS {sorted(b-a)} | SUMIRAM {sorted(a-b)}')
print('== ③ cols NOVAS ==', sorted(set(B['sur_cols']) - set(A['sur_cols'])))
print('== ④ cols NOVAS ==', sorted(set(B['tim_cols']) - set(A['tim_cols'])))
print('== ① cols NOVAS ==', sorted(set(B['real_cols']) - set(A['real_cols'])))
print('== ④ nonnull s42   ==', A['tim_nonnull'], A['tim_n'])
print('== ④ nonnull smoke ==', B['tim_nonnull'], B['tim_n'])
