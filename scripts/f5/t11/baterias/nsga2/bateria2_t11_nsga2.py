#!/usr/bin/env python
"""Bateria 2 T11/nsga2: (a) P1 seeding D88 recomputado a partir da (1) init;
(b) P7 ledger separando rounds completos x round truncado; (c) forma fechada n_ger=D+1.
READ-ONLY."""
import json, os, math
import numpy as np, pandas as pd, pyarrow.parquet as pq
from collections import Counter

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga2'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT = os.path.dirname(os.path.abspath(__file__))

def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()]

def ndsort(F):
    n = len(F); fr = np.zeros(n, int); rest = np.arange(n); k = 1
    while len(rest):
        Fr = F[rest]; dom = np.zeros(len(rest), bool)
        for i in range(len(rest)):
            le = np.all(Fr <= Fr[i], axis=1); lt = np.any(Fr < Fr[i], axis=1)
            if np.any(le & lt): dom[i] = True
        fr[rest[~dom]] = k; rest = rest[dom]; k += 1
    return fr

def crowding(F):
    n, M = F.shape; cd = np.zeros(n)
    if n <= 2: return np.full(n, np.inf)
    for j in range(M):
        o = np.argsort(F[:, j], kind='stable')
        cd[o[0]] = cd[o[-1]] = np.inf
        rng = F[o[-1], j] - F[o[0], j]
        if rng == 0: continue
        cd[o[1:-1]] += (F[o[2:], j] - F[o[:-2], j]) / rng
    return cd

def selec(F, N):
    fr = ndsort(F); esc = []; k = 1
    while len(esc) < N:
        idx = np.where(fr == k)[0]
        if len(esc) + len(idx) <= N: esc.extend(idx.tolist())
        else:
            cd = crowding(F[idx]); ordem = np.lexsort((idx, -cd))
            esc.extend(idx[ordem][:N - len(esc)].tolist())
        k += 1
    return sorted(esc), fr

def dtlz4_f(X, M):
    """DTLZ4 do PlatEMO: alpha=100."""
    X = X.astype(np.float64).copy()
    Xa = X ** 100
    g = np.sum((X[:, M - 1:] - 0.5) ** 2, axis=1)
    F = np.tile(1 + g[:, None], (1, M))
    F[:, 0] *= np.prod(np.cos(Xa[:, :M - 1] * np.pi / 2), axis=1)
    for i in range(1, M):
        F[:, i] *= np.prod(np.cos(Xa[:, :M - 1 - i] * np.pi / 2), axis=1) * np.sin(Xa[:, M - 1 - i] * np.pi / 2)
    return F

rows = []
for prob in sorted(os.listdir(RAIZ)):
    base = f'{RAIZ}/{prob}/42/exp_main_nsga2_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    ev = jl(base + '.jsonl')
    hdr = [e for e in ev if e['rec'] == 'header'][0]
    sd = [e for e in ev if e['rec'] == 'seeding'][0]
    gens = [e for e in ev if e['rec'] == 'nsga2_gen']
    guards = [e for e in ev if e['rec'] == 'guard']
    real = pq.read_table(base + '__real.parquet').to_pandas()
    pop = pq.read_table(base + '__pop.parquet').to_pandas()
    D, M = hdr['D'], hdr['M']
    n_init = 11 * D - 1
    fc = [f'f{i}' for i in range(M)]; xc = [f'x{i}' for i in range(D)]
    ini = real[real.fase == 'init'].sort_values('fe_index')
    r = dict(problema=prob, D=D, M=M)

    # ---- P1 via (1) float32
    F32 = ini[fc].to_numpy(np.float64)
    esc, fr = selec(F32, 20)
    ids = ini.solution_id.to_numpy()
    g1 = sorted(pop[pop.geracao == 1].solution_id.tolist())
    r['p1_f32_bate'] = (sorted(ids[esc].tolist()) == g1)
    r['p1_f32_inter'] = len(set(ids[esc].tolist()) & set(g1))
    r['p1_f32_nfrentes'] = int(fr.max()); r['p1_f32_nf1'] = int((fr == 1).sum())
    r['nfrentes_log'] = sd['n_frentes']; r['nf1_log'] = sd['n_frente1']
    r['p1_f32_frentes_ok'] = (int(fr.max()) == sd['n_frentes'] and int((fr == 1).sum()) == sd['n_frente1'])
    r['excede_log'] = sd['frente1_excede_pop']; r['excede_calc'] = bool(int((fr == 1).sum()) > 20)
    r['ndoe_log'] = sd['n_doe']; r['ndoe_ok'] = (sd['n_doe'] == n_init)

    # ---- P1 via float64 (DTLZ4)
    r['p1_f64_bate'] = None; r['p1_f64_nfrentes'] = None; r['p1_f64_nf1'] = None
    if prob == 'DTLZ4':
        doe = pq.read_table(f'{DOE}/{prob}/doe_{prob}_42.parquet').to_pandas()
        X64 = doe[[f'x{i}' for i in range(D)]].to_numpy(np.float64)[:n_init]
        F64 = dtlz4_f(X64, M)
        # validar a formula: cast float32 tem de bater a (1)
        r['p1_f64_valida'] = int((F64.astype(np.float32) == ini[fc].to_numpy(np.float32)).sum())
        r['p1_f64_valida_tot'] = F64.size
        e64, fr64 = selec(F64, 20)
        r['p1_f64_bate'] = (sorted(ids[e64].tolist()) == g1)
        r['p1_f64_nfrentes'] = int(fr64.max()); r['p1_f64_nf1'] = int((fr64 == 1).sum())
        r['p1_f64_frentes_ok'] = (r['p1_f64_nfrentes'] == sd['n_frentes'] and r['p1_f64_nf1'] == sd['n_frente1'])

    # ---- P7 ledger: rounds completos x truncado
    ch = [g for g in guards if g['name'] == 'cache_hit']
    seed = [g for g in ch if g['fe'] == n_init]
    prole = [g for g in ch if g['fe'] != n_init]
    fe_last = gens[-1]['fe']
    r['fe_last'] = fe_last; r['resto'] = man['maxfe'] - fe_last
    r['ch_prole_tot'] = len(prole)
    r['ch_prole_completos'] = sum(1 for g in prole if g['fe'] < fe_last)
    r['ch_prole_truncado'] = sum(1 for g in prole if g['fe'] >= fe_last)
    r['ledger_ok'] = (r['resto'] == r['ch_prole_completos'])
    r['hard_stop'] = sum(1 for g in guards if g['name'] == 'hard_stop')
    r['hs_iff_resto'] = ((r['hard_stop'] > 0) == (r['resto'] > 0))
    # forma fechada
    r['n_ger'] = man['n_geracoes']; r['D_mais_1'] = (man['n_geracoes'] == D + 1)
    r['fe_g1'] = gens[0]['fe']; r['fe_g1_ok'] = (gens[0]['fe'] == n_init)
    # incremento de FE por geracao
    inc = [gens[i + 1]['fe'] - gens[i]['fe'] for i in range(len(gens) - 1)]
    r['inc_min'] = min(inc) if inc else None; r['inc_max'] = max(inc) if inc else None
    r['inc_eq20'] = sum(1 for i in inc if i == 20); r['inc_n'] = len(inc)
    r['soma_20_menos_inc'] = sum(20 - i for i in inc)
    rows.append(r)
    print('.', end='', flush=True)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/p1_p7_t11_nsga2.csv', index=False)
print('\n== P1 (seeding D88) ==')
print('bate conjunto via (1) float32:', df.p1_f32_bate.sum(), '/25')
print('n_frentes+n_frente1 do log reproduzidos via (1):', df.p1_f32_frentes_ok.sum(), '/25')
print('n_doe log == 11D-1:', df.ndoe_ok.sum(), '| excede_pop log==calc:', (df.excede_log == df.excede_calc).sum(),
      '| excede True:', df.excede_log.sum())
print(df.loc[~df.p1_f32_bate.astype(bool), ['problema', 'p1_f32_inter', 'p1_f32_nfrentes', 'nfrentes_log',
                                            'p1_f32_nf1', 'nf1_log', 'p1_f64_bate', 'p1_f64_nfrentes',
                                            'p1_f64_nf1', 'p1_f64_valida', 'p1_f64_valida_tot']].to_string())
print('\n== P7 ledger ==')
print('resto == ch_prole(rounds completos):', df.ledger_ok.sum(), '/25')
print('ch_prole total', df.ch_prole_tot.sum(), '| em rounds completos', df.ch_prole_completos.sum(),
      '| no round truncado', df.ch_prole_truncado.sum())
print('hard_stop <=> resto>0:', df.hs_iff_resto.sum(), '/25')
print('incremento de FE por geracao: min', df.inc_min.min(), 'max', df.inc_max.max(),
      '| ==20 em', df.inc_eq20.sum(), 'de', df.inc_n.sum(),
      '| Sigma(20-inc)', df.soma_20_menos_inc.sum())
print('fe(g=1)==11D-1:', df.fe_g1_ok.sum(), '| n_ger==D+1:', df.D_mais_1.sum())
print(df[['problema', 'D', 'n_ger', 'resto', 'ch_prole_tot', 'ch_prole_completos', 'ch_prole_truncado',
          'hard_stop', 'ledger_ok']].to_string())
