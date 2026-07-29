#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead_joias.py — queries-joia do config moead (F5.3b):
  J1  ledger de FE com a última geração truncada (déficit ∈ [0, N-1])
  J2  ② = snapshot no INÍCIO da geração (ger.1 == seeding)
  J3  seeding D88 recomputado (NDSort + CrowdingDistance) ≡ ②(ger.1)
  J4  vizinhança T = ceil(N/10) = 2 recomputada dos vetores → pares idênticos
  J5  taxa de clonagem prevista = f_pares_identicos × (1-1/D)^D  vs  medida
  J6  ponto ideal logado: PlatEMO Z (monótono) × min da população corrente
  J7  cache-hit → alvo (DoE × infill), re-hits
"""
import json, os, collections
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
DOE = os.path.join(REPO, 'data', 'doe')
PROBS = sorted(p for p in os.listdir(RAIZ) if not p.startswith('.'))

from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
try:
    from pymoo.operators.survival.rank_and_crowding.metrics import get_crowding_function
    _cd = lambda F: get_crowding_function('cd').do(F)
except Exception:
    from pymoo.algorithms.moo.nsga2 import calc_crowding_distance as _cdraw
    _cd = _cdraw


def crowding(F):
    F = np.asarray(F, dtype=float)
    if len(F) <= 2:
        return np.full(len(F), np.inf)
    return np.asarray(_cd(F)).ravel()


def vizinhanca(W, T):
    """Replica B = sort(pdist2(W,W),2); B = B(:,1:T) com desempate estável (MATLAB)."""
    d = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    B = np.argsort(d, axis=1, kind='stable')[:, :T]
    return B


linhas, gen_det = [], []
for prob in PROBS:
    base = os.path.join(RAIZ, prob, '42', 'exp_main_moead_%s_42' % prob)
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    dec = [e for e in evs if e['rec'] == 'decomposicao'][0]
    gens = [e for e in evs if e['rec'] == 'moead_gen']
    guards = [e for e in evs if e['rec'] == 'guard']
    D, M = hdr['D'], hdr['M']
    n_doe = 11 * D - 1
    N = man['params']['N_efetivo']
    n_ger = man['n_geracoes']
    W = np.array(dec['vetores'], dtype=float)
    T = int(np.ceil(len(W) / 10))

    fcols = [c for c in real.columns if c.startswith('f') and c != 'fe_index']
    fcols = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()],
                   key=lambda c: int(c[1:]))
    xcols = sorted([c for c in real.columns if c.startswith('x') and c[1:].isdigit()],
                   key=lambda c: int(c[1:]))
    F_all = real[fcols].to_numpy(dtype=float)
    sid2row = {int(s): i for i, s in enumerate(real['solution_id'].to_numpy())}

    # ---- J1 ledger com déficit ----
    ch = [g for g in guards if g['name'] == 'cache_hit']
    hs = [g for g in guards if g['name'] == 'hard_stop']
    ch_off = len(ch) - N            # os N primeiros são o seeding
    novos = (31 * D - 1) - n_doe
    deficit = n_ger * N - (novos + ch_off + len(hs))

    # ---- J2/J3 seeding ----
    P = pop.sort_values(['geracao']).reset_index(drop=True)
    g1 = pop[pop['geracao'] == pop['geracao'].min()]['solution_id'].to_numpy()
    g1_todos_doe = bool((g1 < n_doe).all())
    g1_unicos = len(set(g1.tolist())) == len(g1)
    # recomputo D88
    Fd = F_all[:n_doe]
    fronts = NonDominatedSorting().do(Fd)
    ordem = []
    for fr in fronts:
        fr = np.asarray(fr)
        cdv = crowding(Fd[fr])
        idx = np.lexsort((fr, -cdv))       # crowding desc, desempate por índice asc
        ordem.extend(fr[idx].tolist())
    esperado = np.array(ordem[:N])
    d88_conjunto = set(esperado.tolist()) == set(g1.tolist())
    d88_ordem = bool((esperado == g1).all()) if len(esperado) == len(g1) else False

    # ---- J4/J5 vizinhança e clonagem ----
    B = vizinhanca(W, T)
    nn = B[:, 1] if B.shape[1] > 1 else B[:, 0]
    pares_id, tot_i = 0, 0
    por_ger = []
    for gg, sub in pop.groupby('geracao'):
        s = sub['solution_id'].to_numpy()
        if len(s) != len(W):
            continue
        ident = int((s == s[nn]).sum())
        pares_id += ident; tot_i += len(s)
        por_ger.append((int(gg), ident, len(s), int(pd.Series(s).nunique())))
        gen_det.append(dict(problema=prob, geracao=int(gg), n=len(s),
                            n_unicos=int(pd.Series(s).nunique()), pares_identicos=ident))
    f_ident = pares_id / tot_i if tot_i else np.nan
    p_nomut = (1 - 1.0 / D) ** D
    clone_prev = f_ident * p_nomut
    clone_med = ch_off / (n_ger * N - deficit)

    # ---- J6 ideal ----
    ideal = np.array([g['ideal'] for g in gens], dtype=float)
    fbest = np.array([g['f_best'] for g in gens], dtype=float)
    ideal_eq_fbest = bool(np.allclose(ideal, fbest, rtol=0, atol=0))
    viol_mono = int((np.diff(ideal, axis=0) > 0).sum())
    # ideal ≡ min da população corrente?
    eq_pop, n_cmp, eq_arq = 0, 0, 0
    for k, (gg, sub) in enumerate(pop.groupby('geracao')):
        if k >= len(ideal):
            break
        rows = [sid2row[int(s)] for s in sub['solution_id'].to_numpy() if int(s) in sid2row]
        if not rows:
            continue
        mp = F_all[rows].min(axis=0)
        n_cmp += 1
        if np.allclose(mp, ideal[k], rtol=1e-6, atol=1e-9):
            eq_pop += 1
        fe_g = gens[k]['fe']
        ma = F_all[:fe_g].min(axis=0)
        if np.allclose(ma, ideal[k], rtol=1e-6, atol=1e-9):
            eq_arq += 1

    # ---- J7 cache-hit alvos ----
    sid_off = np.array([g['solution_id'] for g in ch[N:]], dtype=int)
    alvo_doe = int((sid_off < n_doe).sum())
    cnt = collections.Counter(sid_off.tolist())

    linhas.append(dict(problema=prob, D=D, M=M, N=N, T=T, n_ger=n_ger,
                       novos=novos, ch_off=ch_off, hard_stop=len(hs), deficit=deficit,
                       deficit_ok=(0 <= deficit < N),
                       g1_todos_doe=g1_todos_doe, g1_unicos=g1_unicos,
                       d88_conjunto=d88_conjunto, d88_ordem=d88_ordem,
                       f_pares_identicos=f_ident, p_nomut=p_nomut,
                       clone_previsto=clone_prev, clone_medido=clone_med,
                       raz_clone=clone_med / clone_prev if clone_prev else np.nan,
                       ideal_eq_fbest=ideal_eq_fbest, viol_mono_ideal=viol_mono,
                       ideal_eq_pop=eq_pop, ideal_eq_arq=eq_arq, n_cmp=n_cmp,
                       alvo_doe=alvo_doe, alvo_infill=len(sid_off) - alvo_doe,
                       max_hits_sid=max(cnt.values()) if cnt else 0))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, 'moead_joias.csv'), index=False)
pd.DataFrame(gen_det).to_csv(os.path.join(OUT, 'moead_pares_por_geracao.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 60)
print(df.to_string())
print()
for c in ['deficit_ok', 'g1_todos_doe', 'g1_unicos', 'd88_conjunto', 'd88_ordem', 'ideal_eq_fbest']:
    print('%-16s' % c, int(df[c].sum()), '/', len(df))
print('viol_mono_ideal total:', df.viol_mono_ideal.sum())
print('ideal_eq_pop:', df.ideal_eq_pop.sum(), '/', df.n_cmp.sum(), ' | ideal_eq_arq:', df.ideal_eq_arq.sum())
print('deficit range:', df.deficit.min(), df.deficit.max())
print('raz_clone: med %.3f  min %.3f  max %.3f' % (df.raz_clone.median(), df.raz_clone.min(), df.raz_clone.max()))
