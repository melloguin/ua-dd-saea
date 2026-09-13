#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA 2 — refinamentos do config `nsga2` (piso online NSGA-II).
Corrige 3 armadilhas descobertas na bateria 1:
 (i)  o ② tem MULTISET de solution_id (clones de cache-hit ocupam slot) — usar lista, não set;
 (ii) o ledger de FE tem de separar o BLOCO DE SEEDING (N+1 cache-hits em fe=n_init) dos
      cache-hits de prole;
 (iii) recomputar ideal/nadir/n_front1 contra o ⑥ exige comparação RELATIVA (⑥ = float64,
      ① = float32/D53) e, no DTLZ4, o underflow float32 destrói a estrutura de dominância.
"""
import json, os, re, pickle
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos/nsga2'
OUT = f'{RAIZ}/ua-dd-saea/f5/baterias/nsga2'
CARACT = pd.read_csv(f'{RAIZ}/ua-dd-saea/claude_code_context/artifacts/characteristics.csv').set_index('problema')
PROBS = [p for p in sorted(os.listdir(DADOS)) if not p.startswith('.')]

def nd_sort(F):
    """Fronteiras de não-dominância (1-based), semântica PlatEMO/ENS."""
    n = len(F); front = np.zeros(n, dtype=int); resto = np.arange(n); k = 1
    while len(resto):
        Fr = F[resto]; dominado = np.zeros(len(resto), dtype=bool)
        for i in range(len(resto)):
            le = np.all(Fr <= Fr[i], axis=1); lt = np.any(Fr < Fr[i], axis=1)
            if np.any(le & lt):
                dominado[i] = True
        front[resto[~dominado]] = k; resto = resto[dominado]; k += 1
    return front


linhas = []
det_clones = []
for prob in PROBS:
    b = f'{DADOS}/{prob}/42/exp_main_nsga2_{prob}_42'
    man = json.load(open(b + '.manifest.json'))
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    real = pq.read_table(b + '__real.parquet').to_pandas()
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    D = int(CARACT.loc[prob, 'D']); M = int(CARACT.loc[prob, 'M'])
    xcols = [c for c in real.columns if re.fullmatch(r'x\d+', c)]
    fcols = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    guards = [x for x in recs if x['rec'] == 'guard']
    ch_g = [g for g in guards if g['name'] == 'cache_hit']
    N = 20; n_init = 11 * D - 1
    fes = np.array([g['fe'] for g in gens])
    r = {'problema': prob, 'D': D, 'M': M, 'n_gens': len(gens)}

    # ---------------- (ii) LEDGER exato de FE / slots (D89)
    ch_fes = np.array(sorted(g['fe'] for g in ch_g))
    r['ch_total'] = len(ch_g)
    r['ch_bloco_seeding'] = int((ch_fes == n_init).sum())
    r['ch_seeding_esperado'] = N + 1               # N do seeding + o c0 duplicado
    r['ch_seeding_ok'] = (r['ch_bloco_seeding'] == N + 1)
    r['ch_prole'] = r['ch_total'] - r['ch_bloco_seeding']
    # slots vs FE nos rounds COMPLETOS
    dfe = np.diff(fes)
    r['rounds_completos'] = len(dfe)
    r['slots_completos'] = len(dfe) * N
    r['fe_completos'] = int(dfe.sum())
    r['ch_prole_completos'] = r['slots_completos'] - r['fe_completos']
    r['resto_final'] = int(man['maxfe'] - fes[-1])
    r['LEDGER_resto_eq_chprole'] = (r['resto_final'] == r['ch_prole_completos'])
    r['ch_prole_round_final'] = r['ch_prole'] - r['ch_prole_completos']
    r['slots_round_final'] = r['resto_final'] + r['ch_prole_round_final']
    r['slots_final_le_N'] = (r['slots_round_final'] <= N)
    r['ch_taxa_prole'] = r['ch_prole'] / (r['slots_completos'] + r['slots_round_final'])
    # o c0: primeiro cache-hit duplicado?
    r['c0_dup'] = (len(ch_g) >= 2 and ch_g[0]['solution_id'] == ch_g[1]['solution_id']
                   and ch_g[0]['x_key'] == ch_g[1]['x_key'])
    r['ch_seeding_sids_unicos'] = len(set(g['solution_id'] for g in ch_g if g['fe'] == n_init))
    r['ch_seeding_todos_init'] = all(g['solution_id'] < n_init for g in ch_g if g['fe'] == n_init)

    # ---------------- (i) ② como MULTISET: clones na população
    gl = {g: v['solution_id'].tolist() for g, v in pop.groupby('geracao')}
    gk = sorted(gl)
    n_dup_pop = [len(gl[g]) - len(set(gl[g])) for g in gk]
    r['pop_clones_total'] = int(sum(n_dup_pop))
    r['pop_gers_com_clone'] = int(sum(1 for v in n_dup_pop if v > 0))
    r['pop_clone_max'] = int(max(n_dup_pop))
    r['pop_linhas_20'] = all(len(gl[g]) == N for g in gk)
    # clones ≡ cache-hits? (um clone na pop vem de um infill duplicado que virou cache-hit)
    det_clones.append((prob, r['pop_clones_total'], r['ch_prole']))

    # ---------------- (iii) recomputo ideal/nadir/n_front1 com erro RELATIVO
    fmap = real.set_index('solution_id')[fcols]
    ideal = np.array([g['ideal'] for g in gens], float)
    nad1 = np.array([g['nadir_front1'] for g in gens], float)
    nadp = np.array([g['nadir_pop'] for g in gens], float)
    nf1 = np.array([g['n_front1'] for g in gens])
    ideal_r, nadp_r, nad1_r, nf1_r = [], [], [], []
    for g in gk:
        F = fmap.loc[gl[g]].values.astype(np.float64)
        ideal_r.append(F.min(axis=0)); nadp_r.append(F.max(axis=0))
        fr = nd_sort(F)
        nf1_r.append(int((fr == 1).sum())); nad1_r.append(F[fr == 1].max(axis=0))
    ideal_r = np.array(ideal_r); nadp_r = np.array(nadp_r); nad1_r = np.array(nad1_r)
    rel = lambda A, B: float(np.nanmax(np.abs(A - B) / np.maximum(np.abs(B), 1e-30)))
    r['rel_ideal'] = rel(ideal_r, ideal)
    r['rel_nadirpop'] = rel(nadp_r, nadp)
    r['rel_nadir1'] = rel(nad1_r, nad1)
    r['nf1_eq'] = int((np.array(nf1_r) == nf1).sum()); r['nf1_n'] = len(nf1)
    r['nf1_dmax'] = int(np.abs(np.array(nf1_r) - nf1).max())
    # quantos f do ① sofreram flush-to-zero do float32 (underflow D53)?
    Fall = real[fcols].values
    r['f_zeros_exatos'] = int((Fall == 0).sum())
    r['f_zeros_frac'] = float((Fall == 0).mean())
    r['f_min_abs_naozero'] = float(np.abs(Fall[Fall != 0]).min()) if (Fall != 0).any() else np.nan

    # ---------------- turnover em MULTISET + sobrevivência
    from collections import Counter
    turn = []
    for i in range(len(gk) - 1):
        a, b_ = Counter(gl[gk[i]]), Counter(gl[gk[i + 1]])
        novos = sum((b_ - a).values())
        turn.append(novos)
    r['turn_med'] = float(np.mean(turn)); r['turn_min'] = int(min(turn)); r['turn_max'] = int(max(turn))
    r['turn_zero'] = int(sum(1 for t in turn if t == 0))
    sid_init = set(real.loc[real['fase'] == 'init', 'solution_id'].tolist())
    r['sobrev_doe_final'] = len(set(gl[gk[-1]]) & sid_init)
    r['sobrev_doe_frac'] = r['sobrev_doe_final'] / N

    # ---------------- clone bit-exato na ① (X duplicado apesar do dedup D57)
    X32 = real[xcols].values
    u, cnt = np.unique(X32, axis=0, return_counts=True)
    r['dupX_f32'] = int(len(X32) - len(u))
    # menor distância relativa entre pares distintos (só D<=12 por custo)
    if D <= 12 and len(X32) <= 400:
        from scipy.spatial.distance import pdist
        dd = pdist(X32.astype(np.float64))
        esc = np.linalg.norm(X32.astype(np.float64).max(0) - X32.astype(np.float64).min(0))
        r['dmin_rel'] = float(dd[dd > 0].min() / esc) if (dd > 0).any() else 0.0
        r['n_pares_lt_1e6'] = int((dd / esc < 1e-6).sum())
    else:
        r['dmin_rel'] = np.nan; r['n_pares_lt_1e6'] = -1

    linhas.append(r)

df = pd.DataFrame(linhas)
df.to_csv(f'{OUT}/aspectos2_nsga2.csv', index=False)
pd.set_option('display.width', 320, 'display.max_columns', 400)
print(df.to_string())
