#!/usr/bin/env python
"""B4 - Bateria 4: corte RIGOROSO da regra de rotulo.
label_hi = '<=' em tudo (limite superior);
label_lo = '<' em tudo EXCETO a auto-comparacao (linha do arquivo == a propria ref), que e
           exata em double tambem -> limite inferior valido sob a hipotese de empate float32.
Geracao DECIDIDA <=> label_hi == label_lo (nenhum empate float32 relevante).
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])
rows = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    real = pd.read_parquet(base + '__real.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet', columns=['regime', 'geracao', 'real_solution_id'])
    on = sur[sur.regime == 'online']
    fc = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    F = real[fc].to_numpy(np.float64)
    init = int((real.fase == 'init').sum())
    arc = np.array(list(range(init)) + [int(v) for v in on.real_solution_id.to_numpy()])
    for r in gens:
        nA = int(r['n_treino']); ids = arc[:nA]; Fa = F[ids]
        rid = np.array(r['ref_ids'], int); R = F[rid]
        n1log = int(round(r['rr'] * nA))
        hi = np.ones(nA, bool); lo = np.ones(nA, bool)
        for j in range(len(R)):
            c_le = (Fa <= R[j]).any(axis=1)
            c_lt = (Fa < R[j]).any(axis=1)
            selfrow = (ids == rid[j])           # a propria referencia: exata em double
            hi &= c_le
            lo &= (c_lt | selfrow)
        rows.append(dict(problema=prob, geracao=r['geracao'], nA=nA, n1log=n1log,
                         n1_hi=int(hi.sum()), n1_lo=int(lo.sum()), n_amb=int((hi & ~lo).sum())))
    print('ok', prob)
df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/b4_regra_rotulo_tight.csv', index=False)
dec = df[df.n_amb == 0]
print('\ngeracoes:', len(df))
print('SANDUICHE n1_lo <= n1log <= n1_hi:', int(((df.n1_lo <= df.n1log) & (df.n1log <= df.n1_hi)).sum()), '/', len(df))
print('geracoes DECIDIDAS (zero empate float32 relevante):', len(dec), '/', len(df),
      f'({100*len(dec)/len(df):.1f}%)  -> match exato da regra: {int((dec.n1_hi==dec.n1log).sum())}/{len(dec)}')
print('\npor problema:')
print(df.groupby('problema').apply(lambda d: pd.Series({
    'n_gen': len(d), 'decididas': int((d.n_amb == 0).sum()),
    'dec_match': int(((d.n_amb == 0) & (d.n1_hi == d.n1log)).sum()),
    'sand': int(((d.n1_lo <= d.n1log) & (d.n1log <= d.n1_hi)).sum()),
    'amb_med': float(d.n_amb.median()), 'nA_med': float(d.nA.median())}), include_groups=False).to_string())
