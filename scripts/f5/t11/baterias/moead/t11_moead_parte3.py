#!/usr/bin/env python
"""Parte 3 — as joias re-medidas: seeding D88 (f32 e f64), co-substituicao do par,
M10 (frente1 excede pop), M12 (k do hard-stop) e o papel de regua (P1/P2).
READ-ONLY. Usa `src/problems.py` OFICIAL para o recomputo float64.
"""
import json, os, math, sys
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
DOE = f'{REPO}/data/doe'
OUT = f'{REPO}/f5/t11/baterias/moead'
sys.path.insert(0, REPO)
from src import experiment as EXPM  # noqa: E402
from src.problems import evaluate_problem  # noqa: E402


def nds(F):
    """NonDominatedSorting completo -> vetor de frentes (1-based)."""
    n = len(F)
    fno = np.zeros(n, int)
    rest = np.arange(n)
    f = 1
    while len(rest):
        O = F[rest]
        dom = np.zeros(len(rest), bool)
        for i in range(len(rest)):
            le = np.all(O <= O[i], 1)
            lt = np.any(O < O[i], 1)
            le[i] = False
            dom[i] = np.any(le & lt)
        fno[rest[~dom]] = f
        rest = rest[dom]
        f += 1
    return fno


def crowding(F):
    n, m = F.shape
    cd = np.zeros(n)
    for j in range(m):
        o = np.argsort(F[:, j], kind='stable')
        cd[o[0]] = cd[o[-1]] = np.inf
        rng = F[o[-1], j] - F[o[0], j]
        if rng <= 0:
            continue
        for k in range(1, n - 1):
            cd[o[k]] += (F[o[k + 1], j] - F[o[k - 1], j]) / rng
    return cd


def selec_d88(F, N):
    """NDSort frente a frente; dentro da frente que corta, crowding desc,
    desempate por indice crescente."""
    fno = nds(F)
    esc = []
    f = 1
    while len(esc) < N:
        idx = np.where(fno == f)[0]
        if len(esc) + len(idx) <= N:
            esc.extend(idx.tolist())
        else:
            cd = crowding(F[idx])
            ordem = sorted(range(len(idx)), key=lambda t: (-cd[t], idx[t]))
            esc.extend([idx[t] for t in ordem[:N - len(esc)]])
        f += 1
    return esc


rows = []
for prob in sorted(os.listdir(f'{RES}/moead')):
    base = f'{RES}/moead/{prob}/42/exp_main_moead_{prob}_42'
    if not os.path.exists(base + '.manifest.json'):
        continue
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    head = [x for x in recs if x['rec'] == 'header'][0]
    seed = [x for x in recs if x['rec'] == 'seeding'][0]
    dec = [x for x in recs if x['rec'] == 'decomposicao'][0]
    D, M = int(head['D']), int(head['M'])
    Nef = int(man['params']['N_efetivo'])
    init = real[real['fase'] == 'init']
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    xcols = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    F32 = init[fcols].values.astype(np.float64)          # ① float32 promovido
    # --- float64 oficial: reavalia o artefato do DoE com src/problems.py
    d = pd.read_parquet(f'{DOE}/{prob}/doe_{prob}_42.parquet')
    xd = [c for c in d.columns if c.startswith('x') and c[1:].isdigit()]
    X64 = d[xd].values.astype(np.float64)
    F64 = np.asarray(evaluate_problem(EXPM._instantiate_problem(prob), X64), dtype=np.float64)
    dF = float(np.max(np.abs(F64.astype(np.float32).astype(np.float64) - F32)))
    fno64 = nds(F64)
    r = dict(problema=prob, D=D, M=M, N_ef=Nef, n_doe=len(init),
             dF_f32=dF,
             log_nfrentes=seed['n_frentes'], log_nfrente1=seed['n_frente1'],
             f64_nfrentes=int(fno64.max()), f64_nfrente1=int((fno64 == 1).sum()),
             excede=seed.get('frente1_excede_pop'))
    fno32 = nds(F32)
    r['f32_nfrentes'] = int(fno32.max())
    r['f32_nfrente1'] = int((fno32 == 1).sum())
    r['seed_log_ok_f64'] = (r['log_nfrentes'] == r['f64_nfrentes'] and
                            r['log_nfrente1'] == r['f64_nfrente1'])
    r['seed_log_ok_f32'] = (r['log_nfrentes'] == r['f32_nfrentes'] and
                            r['log_nfrente1'] == r['f32_nfrente1'])
    r['excede_recomp'] = bool(r['f64_nfrente1'] > Nef)
    # --- selecao recomputada x ②(ger 1), em CONJUNTO e em ORDEM
    sid_init = init['solution_id'].values
    g1 = pop[pop['geracao'] == 1]['solution_id'].values
    for tag, FF in (('f64', F64), ('f32', F32)):
        esc = selec_d88(FF, Nef)
        sids = sid_init[esc]
        r[f'D88_{tag}_conj'] = bool(set(sids) == set(g1))
        r[f'D88_{tag}_ordem'] = bool(np.array_equal(sids, g1))
    # --- co-substituicao do par (M8)
    W = np.array(dec['vetores'], float)
    T = math.ceil(len(W) / 10)
    dd = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    B = np.argsort(dd, axis=1, kind='stable')[:, :T]
    nn = B[:, 1]
    gs = sorted(pop['geracao'].unique())
    sub = co = trans = 0
    for a, b in zip(gs[:-1], gs[1:]):
        sa = pop[pop['geracao'] == a]['solution_id'].values
        sb = pop[pop['geracao'] == b]['solution_id'].values
        if len(sa) != len(sb):
            continue
        trans += 1
        ch = sa != sb
        sub += int(ch.sum())
        co += int(sum(1 for i in range(len(sa))
                      if ch[i] and ch[nn[i]] and sb[i] == sb[nn[i]]))
    r['transicoes'] = trans
    r['substituicoes'] = sub
    r['co_subst'] = co
    r['frac_slots'] = sub / (trans * Nef) if trans else np.nan
    r['frac_co'] = co / sub if sub else np.nan
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/t11_moead_parte3.csv', index=False)
pd.set_option('display.width', 260)
print(df[['problema', 'D', 'M', 'N_ef', 'dF_f32', 'log_nfrentes', 'log_nfrente1',
          'f64_nfrentes', 'f64_nfrente1', 'f32_nfrente1', 'seed_log_ok_f64',
          'seed_log_ok_f32', 'D88_f64_ordem', 'D88_f32_ordem', 'excede',
          'excede_recomp', 'substituicoes', 'co_subst']].to_string(index=False))
n = len(df)
print(f'\nP3 max|dF| f64->f32 vs ①: {df.dF_f32.max()}')
print(f'M9 seeding: log ≡ recomputo f64 {int(df.seed_log_ok_f64.sum())}/{n} · '
      f'f32 {int(df.seed_log_ok_f32.sum())}/{n}')
print(f'M9 D88 selecao ≡ ②(g1): f64 conjunto {int(df.D88_f64_conj.sum())}/{n} · '
      f'ORDEM {int(df.D88_f64_ordem.sum())}/{n} | f32 ORDEM {int(df.D88_f32_ordem.sum())}/{n}')
print(f'M10 frente1_excede_pop: log {int(df.excede.sum())}/{n} · recomputo f64 '
      f'{int(df.excede_recomp.sum())}/{n} · concordam '
      f'{int((df.excede==df.excede_recomp).sum())}/{n}')
print(f'M8 substituicoes {df.substituicoes.sum()} em {df.transicoes.sum()} transicoes '
      f'({df.frac_slots.median():.3f} dos slots, mediana) · co-substituicoes '
      f'{df.co_subst.sum()} = {df.co_subst.sum()/df.substituicoes.sum():.3f}')

# ---------------- P1/P2 regua (metricas pre-computadas da F5.2c)
met = pd.read_csv(f'{REPO}/f5/metricas_finais_f52c.csv')
m = met[met.exp == 'main'].pivot_table(index='problema', columns='alg', values='igd_plus')
pisos = ['moead', 'nsga2', 'nsga3', 'smsemoa']
print('\n=== P1/P2 (IGD+ main, insumo F5.2c) ===')
for casado in ['b3', 'c122', 'b1']:
    sub = m[[casado, 'moead']].dropna()
    print(f'{casado}: bate o moead em {(sub[casado]<sub["moead"]).sum()}/{len(sub)} '
          f'| razao mediana {(sub[casado]/sub["moead"]).median():.3f}')
P = m[pisos].dropna()
pior = (P.idxmax(axis=1) == 'moead').sum()
melhor = (P.idxmin(axis=1) == 'moead').sum()
banda_com = (P.max(1) / P.min(1)).median()
banda_sem = (P[['nsga2', 'nsga3', 'smsemoa']].max(1) /
             P[['nsga2', 'nsga3', 'smsemoa']].min(1)).median()
print(f'P2 moead e o TETO da banda em {pior}/{len(P)} · piso em {melhor}/{len(P)} '
      f'| largura mediana com ele {banda_com:.3f}x · sem ele {banda_sem:.3f}x')
sa = [c for c in m.columns if c not in pisos]
tot = win = conc = 0
for c in sa:
    s = m[[c, 'moead']].dropna()
    tot += len(s)
    win += int((s[c] < s['moead']).sum())
    conc += int((s[c] / s['moead'] < 1 / 1.5898).sum())
print(f'P1 SA x moead: {win}/{tot} celulas SA batem o piso; conclusivas vs O-18: {conc}/{tot}')
