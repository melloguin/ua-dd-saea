#!/usr/bin/env python
"""T11/e7 — a s42 e a mesma busca que o codigo de hoje faria? Comparacao celula-a-celula
entre a s42 (vm3, 2026-07-26) e o smoke T11 (Mac, 2026-07-30) para as 2 celulas comuns.
READ-ONLY."""
import json
import numpy as np, pandas as pd

S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'

pares = {
    'MMF11_L': (f'{S42}/MMF11_L/42/exp_main_e7_MMF11_L_42',
                f'{EV}/smoke_matlab/experiments/main/e7/exp_main_e7_MMF11_L_42'),
    'MMF1': (f'{S42}/MMF1/42/exp_main_e7_MMF1_42',
             f'{EV}/g6_com/experiments/main/e7/exp_main_e7_MMF1_42'),
}
res = {}
for prob, (a, b) in pares.items():
    ra = pd.read_parquet(a + '__real.parquet'); rb = pd.read_parquet(b + '__real.parquet')
    import re
    xc = [c for c in ra.columns if re.fullmatch(r'x\d+', c)]
    fc = [c for c in ra.columns if re.fullmatch(r'f\d+', c)]
    dx = np.abs(ra[xc].to_numpy(float) - rb[xc].to_numpy(float)).max(axis=1)
    df_ = np.abs(ra[fc].to_numpy(float) - rb[fc].to_numpy(float)).max(axis=1)
    prim = int(np.argmax(dx > 0)) if (dx > 0).any() else None
    ev_a = [json.loads(x) for x in open(a + '.jsonl')]
    ev_b = [json.loads(x) for x in open(b + '.jsonl')]
    ga = [e for e in ev_a if e.get('rec') == 'e7_gen']; gb = [e for e in ev_b if e.get('rec') == 'e7_gen']
    ciclos_ident = {}
    for campo in ('RatioOld', 'Ratio', 'ramo', 'f_best', 'ymin', 'n_front1', 'n_treino', 'fe_treino_max', 'dist_min_arquivo'):
        va = [e.get(campo) for e in ga]; vb = [e.get(campo) for e in gb]
        prim_c = next((i + 1 for i, (p, q) in enumerate(zip(va, vb)) if p != q), None)
        ciclos_ident[campo] = {'igual': va == vb, 'primeiro_ciclo_divergente': prim_c}
    res[prob] = {
        'n_fe': len(ra), 'n_ciclos': (len(ga), len(gb)),
        'init_11D_1_identico': bool(dx[:len(ra) - (len(ra) - int((ra.fase == "init").sum() if "fase" in ra else 0))].size),
        'n_init': int((ra['fase'] == 'init').sum()) if 'fase' in ra.columns else None,
        'primeiro_fe_divergente_X': prim,
        'n_fe_com_X_divergente': int((dx > 0).sum()),
        'maxdX': float(dx.max()), 'maxdF': float(df_.max()),
        'ciclos': ciclos_ident,
        'ts_a': ev_a[0]['ts'], 'ts_b': ev_b[0]['ts'],
    }
    # ate onde a trajetoria e bit-identica
    res[prob]['fe_bit_identicos_prefixo'] = int(prim) if prim is not None else len(ra)

json.dump(res, open(f'{OUT}/reprodutibilidade_e7.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
