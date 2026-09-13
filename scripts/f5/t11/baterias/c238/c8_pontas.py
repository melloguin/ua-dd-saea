#!/usr/bin/env python
"""C8 — pontas soltas: (a) A2 colapso do GA interno por celula (X bit-identico ao
vencedor + real_solution_id no pool); (b) fracao de exploracao agregada de dois jeitos;
(c) E13 sonda DTLZ2/MMF1 no detalhe; (d) sigma->0 excluindo D=2. READ-ONLY.
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'

print('=' * 100)
print('(a) A2 — colapso do GA interno: quanto do pool FINAL e copia bit-a-bit do vencedor?')
print('=' * 100)
rows = []
for prob in sorted(os.listdir(S42)):
    b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    M, D = hdr['M'], hdr['D']
    gens = {r['geracao']: r for r in recs if r.get('rec') == 'c238_gen'}
    cols = ['regime', 'geracao', 'real_solution_id'] + [f'x{i}' for i in range(D)]
    sur = pq.read_table(b + '__surrogate.parquet', columns=cols).to_pandas()
    on = sur[sur.regime == 'online']
    tot = len(on); marc = int(on.real_solution_id.notna().sum())
    cop = 0
    for g, sub in on.groupby('geracao'):
        X = sub[[f'x{i}' for i in range(D)]].values
        w = sub[sub.real_solution_id.notna()]
        if len(w) == 0: continue
        xw = w[[f'x{i}' for i in range(D)]].values[0]
        cop += int((X == xw).all(1).sum())
    rows.append(dict(problema=prob, D=D, pool=tot, marcadas=marc, frac_marcadas=marc / tot,
                     copias=cop, frac_copias=cop / tot))
A2 = pd.DataFrame(rows).sort_values('frac_copias', ascending=False)
A2.to_csv(f'{OUT}/a2_colapso_ga.csv', index=False)
print(A2.to_string(index=False))
print('  TOTAL: %d linhas de pool ; %d marcadas com real_solution_id ; %d copias bit-a-bit do vencedor' % (
    A2.pool.sum(), A2.marcadas.sum(), A2.copias.sum()))
print('  D=2 (pop=20): frac de copias = %s' % A2[A2.D == 2].set_index('problema').frac_copias.round(3).to_dict())
print('  D>=7        : frac de marcadas mediana = %.4f (1 linha/geracao = o proprio vencedor)' % A2[A2.D >= 7].frac_marcadas.median())

print()
print('=' * 100)
print('(b)+(d) E3 — exploracao e o contrafactual sigma->0, com e sem as 3 celulas D=2')
print('=' * 100)
M = pd.read_csv(f'{OUT}/mecanismo_s42.csv')
print('  fracao de exploracao: mediana GLOBAL (7020 gens) = %.4f ; mediana das medianas por celula = %.4f' % (
    M.frac_exploracao.median(), M.groupby('problema').frac_exploracao.median().median()))
print('  sigma->0 muda o argmax: TODAS = %d/%d (%.1f%%)' % (
    M.sigma0_muda_argmax.sum(), len(M), 100 * M.sigma0_muda_argmax.mean()))
sd = M[M.D >= 7]
print('                          SEM as 3 celulas D=2 = %d/%d (%.1f%%)' % (
    sd.sigma0_muda_argmax.sum(), len(sd), 100 * sd.sigma0_muda_argmax.mean()))
print('                          SEM D=2 e SEM BBOB_F1 (E6) = %d/%d (%.1f%%)' % (
    sd[sd.problema != 'BBOB_F1'].sigma0_muda_argmax.sum(), len(sd[sd.problema != 'BBOB_F1']),
    100 * sd[sd.problema != 'BBOB_F1'].sigma0_muda_argmax.mean()))
print('  por celula (sigma decide):')
print(M.groupby('problema').agg(D=('D', 'first'), gens=('geracao', 'size'),
                                s0=('sigma0_muda_argmax', 'mean'),
                                expl=('frac_exploracao', 'median')).sort_values('s0').to_string())

print()
print('=' * 100)
print('(c) E13 — a sonda no detalhe: DTLZ2 (aprende) x MMF1/MMF4 (degenera)')
print('=' * 100)
s = pd.read_csv(f'{F5}/sonda_f52e.csv')
s = s[s.alg == 'c238']
for p in ['DTLZ2', 'MMF1', 'MMF4', 'MMF11_L', 'DTLZ4', 'MMF16_20', 'BBOB_F1', 'DTLZ7']:
    t = s[s.problema == p].sort_values('bloco')
    for j in sorted(t.obj.unique()):
        u = t[t.obj == j]
        print('  %-9s obj%d: WAPE %.4f -> %.4f | cob %.3f -> %.3f | corr %.4f -> %.4f | blocos=%d n_nan=%d' % (
            p, j, u.wape.iloc[0], u.wape.iloc[-1], u.cobertura95.iloc[0], u.cobertura95.iloc[-1],
            u['corr'].iloc[0] if pd.notna(u['corr'].iloc[0]) else float('nan'),
            u['corr'].iloc[-1] if pd.notna(u['corr'].iloc[-1]) else float('nan'),
            len(u), int(u.n_nan.sum())))
print()
print('  sigma-NaN em TODO o c238: n_nan somado = %d ; n_validas != 2000 em %d de %d blocos-objetivo' % (
    int(s.n_nan.sum()), int((s.n_validas != 2000).sum()), len(s)))
print('  modelo_flag na sonda:', s.modelo_flag.value_counts().to_dict())
