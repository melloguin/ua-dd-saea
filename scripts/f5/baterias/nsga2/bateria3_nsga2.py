#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 3 — provas de mecanismo + saúde em escala do piso `nsga2`.
(A) prova do float32-collapse: o n_front1 recomputado na ① só pode ENCOLHER vs o ⑥ (float64),
    e cada ponto demotado tem empate EXATO em >=1 objetivo com o seu dominador;
(B) DTLZ4: underflow do float32 (D53) destrói a estrutura de dominância do DoE;
(C) MMF4: o par X duplicado em float32 é um quase-clone de SBX (float64 distinto);
(D) trajetórias 20-checkpoints: violações de monotonia do IGD+;
(E) papel de régua: posição do nsga2 vs os outros 3 pisos e vs os 17 SA-MOEA.
"""
import json, os, re, itertools
import numpy as np, pandas as pd, pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos/nsga2'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'
CARACT = pd.read_csv(f'{RAIZ}/ua-dd-saea/claude_code_context/artifacts/characteristics.csv').set_index('problema')
PROBS = [p for p in sorted(os.listdir(DADOS)) if not p.startswith('.')]


def nd_sort(F):
    n = len(F); front = np.zeros(n, int); resto = np.arange(n); k = 1
    while len(resto):
        Fr = F[resto]; dom = np.zeros(len(resto), bool)
        for i in range(len(resto)):
            le = np.all(Fr <= Fr[i], 1); lt = np.any(Fr < Fr[i], 1)
            if np.any(le & lt):
                dom[i] = True
        front[resto[~dom]] = k; resto = resto[dom]; k += 1
    return front


# ================================================================= (A) + (B) + (C)
rows = []
for prob in PROBS:
    b = f'{DADOS}/{prob}/42/exp_main_nsga2_{prob}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl')]
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    real = pq.read_table(b + '__real.parquet').to_pandas()
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    D = int(CARACT.loc[prob, 'D']); M = int(CARACT.loc[prob, 'M'])
    fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
    fmap = real.set_index('solution_id')[fc]
    gl = {g: v['solution_id'].tolist() for g, v in pop.groupby('geracao')}
    n_mis = n_up = n_dn = 0; n_dem = 0; n_dem_com_empate = 0; dem_ex = []
    for i, g in enumerate(sorted(gl)):
        F = fmap.loc[gl[g]].values.astype(np.float64)
        fr = nd_sort(F); rec = int((fr == 1).sum()); log = gens[i]['n_front1']
        if rec != log:
            n_mis += 1
            if rec > log: n_up += 1
            else: n_dn += 1
            n_dem += (log - rec)
            # para cada ponto do front>=2, existe dominador com empate EXATO em >=1 objetivo?
            for j in np.where(fr >= 2)[0]:
                doms = np.where(np.all(F <= F[j], 1) & np.any(F < F[j], 1))[0]
                if len(doms) and any((F[d] == F[j]).any() for d in doms):
                    n_dem_com_empate += 1
                    if len(dem_ex) < 2:
                        d0 = [d for d in doms if (F[d] == F[j]).any()][0]
                        dem_ex.append((g, list(F[j]), list(F[d0])))
    Fall = real[fc].values
    rows.append(dict(problema=prob, D=D, M=M, gers=len(gens), nf1_mismatch=n_mis,
                     nf1_recomp_maior=n_up, nf1_recomp_menor=n_dn, pts_demotados=n_dem,
                     demot_com_empate_f32=n_dem_com_empate,
                     f_zeros=int((Fall == 0).sum()), f_total=int(Fall.size),
                     f_denormal=int(((np.abs(Fall) > 0) & (np.abs(Fall) < 1.18e-38)).sum()),
                     exemplo=str(dem_ex[:1])))
dfA = pd.DataFrame(rows)
dfA.to_csv(f'{OUT}/prova_float32_nsga2.csv', index=False)
print('=== (A) prova do float32-collapse do n_front1 ===')
pd.set_option('display.width', 300, 'display.max_columns', 60, 'display.max_colwidth', 60)
print(dfA[['problema', 'gers', 'nf1_mismatch', 'nf1_recomp_maior', 'nf1_recomp_menor',
           'pts_demotados', 'demot_com_empate_f32', 'f_zeros', 'f_total', 'f_denormal']].to_string())
print('\nTOTAIS: gerações=%d · mismatches=%d · recomp>log=%d · recomp<log=%d · demotados=%d · com empate f32=%d'
      % (dfA.gers.sum(), dfA.nf1_mismatch.sum(), dfA.nf1_recomp_maior.sum(),
         dfA.nf1_recomp_menor.sum(), dfA.pts_demotados.sum(), dfA.demot_com_empate_f32.sum()))
print('\nexemplo DTLZ7:', dfA.loc[dfA.problema == 'DTLZ7', 'exemplo'].values[0][:300])

# ================================================================= (B) DTLZ4
print('\n=== (B) DTLZ4 — underflow float32 no DoE ===')
b = f'{DADOS}/DTLZ4/42/exp_main_nsga2_DTLZ4_42'
real = pq.read_table(b + '__real.parquet').to_pandas()
fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
ini = real[real.fase == 'init']
F = ini[fc].values.astype(np.float64)
fr = nd_sort(F)
recs = [json.loads(l) for l in open(b + '.jsonl')]
sr = [x for x in recs if x['rec'] == 'seeding'][0]
print('  logado (float64, MATLAB): n_frentes=%d n_frente1=%d' % (sr['n_frentes'], sr['n_frente1']))
print('  recomputado na ① (float32): n_frentes=%d n_frente1=%d' % (fr.max(), (fr == 1).sum()))
print('  zeros exatos no DoE: %d de %d (%.1f%%); linhas com >=1 zero: %d de %d'
      % ((F == 0).sum(), F.size, 100 * (F == 0).mean(), (F == 0).any(1).sum(), len(F)))
print('  linhas com f1==f2==0: %d  → viram uma CADEIA de dominância por f0' % ((F[:, 1] == 0) & (F[:, 2] == 0)).sum())
print('  menor |f| não-nulo: %.3e (denormal float32 = 1.4e-45)' % np.abs(F[F != 0]).min())

# ================================================================= (C) MMF4
print('\n=== (C) MMF4 — o par X duplicado em float32 ===')
b = f'{DADOS}/MMF4/42/exp_main_nsga2_MMF4_42'
real = pq.read_table(b + '__real.parquet').to_pandas()
xc = [c for c in real.columns if re.fullmatch(r'x\d+', c)]
fc = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
X = real[xc].values
u, inv, cnt = np.unique(X, axis=0, return_inverse=True, return_counts=True)
for d in np.where(cnt > 1)[0]:
    idx = np.where(inv == d)[0]
    print('  linhas', idx, ' fases', real.fase.values[idx], ' solution_id', real.solution_id.values[idx])
    print('  X (hex float32):', [X[i].tobytes().hex() for i in idx])
    print('  f (hex float32):', [real[fc].values[i].tobytes().hex() for i in idx])
recs = [json.loads(l) for l in open(b + '.jsonl')]
ch = [g for g in recs if g.get('name') == 'cache_hit']
print('  x_keys dos %d cache-hits (todos do bloco de seeding, fe=21): %d únicos'
      % (len(ch), len(set(g['x_key'] for g in ch))))
print('  → o dedup D57 opera no x_key (float64); os 2 X só COLIDEM depois do cast float32 do export D53')

# ================================================================= (D) trajetórias
print('\n=== (D) trajetórias 20-checkpoints ===')
tr = []
for prob in PROBS:
    j = json.load(open(f'{F5}/trajetorias/main_nsga2_{prob}_42.json'))
    ig = np.array([c['igd_plus'] for c in j]); hv = np.array([c['hv'] for c in j])
    nd = np.array([c['n_nd'] for c in j]); fe = np.array([c['fe'] for c in j])
    d = np.diff(ig)
    tr.append(dict(problema=prob, n_ckpt=len(j), viol_igdplus=int((d > 1e-12).sum()),
                   viol_max=float(d.max()) if len(d) else 0.0,
                   igd0=ig[0], igdF=ig[-1], ganho=float(ig[0] / ig[-1]) if ig[-1] > 0 else np.inf,
                   hv_viol=int((np.diff(hv) < -1e-12).sum()), hv_final=hv[-1],
                   nd0=int(nd[0]), ndF=int(nd[-1]), fe_ult=int(fe[-1])))
dfD = pd.DataFrame(tr); dfD.to_csv(f'{OUT}/trajetorias_nsga2.csv', index=False)
print(dfD.to_string())
print('TOTAL transições=%d · violações IGD+=%d · violações HV=%d'
      % (dfD.n_ckpt.sum() - len(dfD), dfD.viol_igdplus.sum(), dfD.hv_viol.sum()))

# ================================================================= (E) papel de régua
print('\n=== (E) papel de régua: nsga2 vs pisos e vs SA-MOEA ===')
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
mm = m[m.exp == 'main']
PISOS = ['nsga2', 'nsga3', 'moead', 'smsemoa']
piv = mm.pivot_table(index='problema', columns='alg', values='igd_plus')
res = []
for prob in PROBS:
    if prob not in piv.index: continue
    lin = piv.loc[prob]
    v_ns = lin.get('nsga2', np.nan)
    pis = {p: lin.get(p, np.nan) for p in PISOS if p in lin.index}
    sa = lin.drop([c for c in PISOS if c in lin.index]).dropna()
    banda_lo = np.nanmin(list(pis.values())); banda_hi = np.nanmax(list(pis.values()))
    melhor_piso = min(pis, key=lambda k: pis[k] if pis[k] == pis[k] else np.inf)
    rank_pisos = int(pd.Series(pis).rank().get('nsga2', -1))
    n_sa_pior = int((sa > v_ns).sum()); n_sa = int(sa.notna().sum())
    todos = lin.dropna().sort_values()
    res.append(dict(problema=prob, igd_nsga2=v_ns, melhor_piso=melhor_piso,
                    piso_min=banda_lo, piso_max=banda_hi, rank_entre_pisos=rank_pisos,
                    ratio_vs_melhorpiso=v_ns / banda_lo if banda_lo > 0 else np.nan,
                    n_SA_piores_que_nsga2=n_sa_pior, n_SA=n_sa,
                    rank_global=int(list(todos.index).index('nsga2')) + 1, n_algs=len(todos),
                    melhor_global=todos.index[0], igd_melhor_global=todos.iloc[0]))
dfE = pd.DataFrame(res); dfE.to_csv(f'{OUT}/regua_nsga2.csv', index=False)
print(dfE.to_string())
print('\nresumo: nsga2 é o MELHOR piso em %d/%d problemas; rank médio entre os 4 pisos = %.2f'
      % ((dfE.melhor_piso == 'nsga2').sum(), len(dfE), dfE.rank_entre_pisos.mean()))
print('rank global médio = %.2f de %d algs; SA piores que o piso: mediana %d/%d, total %d de %d comparações'
      % (dfE.rank_global.mean(), dfE.n_algs.max(), int(dfE.n_SA_piores_que_nsga2.median()),
         int(dfE.n_SA.median()), dfE.n_SA_piores_que_nsga2.sum(), dfE.n_SA.sum()))
