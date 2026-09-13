#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead_extras.py — fechamentos finos do config moead:
  E1  U7/timing: ④ × ⑥ × ⑤ (reconciliação do relógio sem fit/busca)
  E2  `f_best`/`ideal`/`nadir_*`: semântica (componentwise da POP — CONTRATO §DI-10 pisos)
  E3  clonagem: bracket previsto [f_ident(início), f_ident(fim)] × (1-1/D)^D vs medido
  E4  saúde do n_front1 e da diversidade ao longo do run
  E5  arqueologia do cache-hit: distância no tempo entre o hit e a linha ① alvo
"""
import json, os, collections
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
PROBS = sorted(p for p in os.listdir(RAIZ) if not p.startswith('.'))


def viz(W):
    T = int(np.ceil(len(W) / 10))
    d = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    return np.argsort(d, axis=1, kind='stable')[:, :T], T


rows = []
for prob in PROBS:
    base = os.path.join(RAIZ, prob, '42', 'exp_main_moead_%s_42' % prob)
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    dec = [e for e in evs if e['rec'] == 'decomposicao'][0]
    gens = [e for e in evs if e['rec'] == 'moead_gen']
    guards = [e for e in evs if e['rec'] == 'guard']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    D, M = hdr['D'], hdr['M']
    n_doe = 11 * D - 1
    N = man['params']['N_efetivo']
    fc = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))
    F = real[fc].to_numpy(np.float64)
    sid2row = {int(s): i for i, s in enumerate(real['solution_id'].to_numpy())}

    # E1 timing
    st = float(tim['tempo_geracao_s'].sum())
    tt = man['timing']['tempo_total_s']
    ta = man['timing']['tempo_aval_real_s']
    e1_fit = bool(tim['tempo_fit_s'].isna().all() and tim['tempo_busca_s'].isna().all()
                  and tim['tempo_pred_sonda_s'].isna().all())
    e1_ord = bool((tim['geracao'].to_numpy() == np.arange(1, len(tim) + 1)).all())
    e1_pos = bool((tim['tempo_geracao_s'].to_numpy() > 0).all())
    e1_aval_le = ta <= st

    # E2 semântica de f_best/ideal/nadir
    snaps = [g[1]['solution_id'].to_numpy() for g in sorted(pop.groupby('geracao'), key=lambda t: t[0])]
    ok_ideal = ok_nadir = ok_nf1 = ok_fbest_ind = 0
    from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
    nds = NonDominatedSorting()
    for k, g in enumerate(gens):
        if k >= len(snaps):
            break
        rr = [sid2row[int(s)] for s in snaps[k]]
        P = F[rr]
        if np.allclose(P.min(0), g['ideal'], rtol=1e-6, atol=1e-12):
            ok_ideal += 1
        if np.allclose(P.max(0), g['nadir_pop'], rtol=1e-6, atol=1e-12):
            ok_nadir += 1
        f1 = nds.do(P)[0]
        if len(f1) == g['n_front1']:
            ok_nf1 += 1
        if np.allclose(P.max(0), g['nadir_pop'], rtol=1e-6, atol=1e-12):
            pass
        # f_best é atingido por UM indivíduo?
        if (np.isclose(P, np.array(g['f_best']), rtol=1e-9, atol=0).all(1)).any():
            ok_fbest_ind += 1

    # E3 bracket da clonagem
    B, T = viz(np.array(dec['vetores'], float))
    nn = B[:, 1]
    fi = np.array([float((s == s[nn]).mean()) for s in snaps])
    pnm = (1 - 1.0 / D) ** D
    ch = [g for g in guards if g['name'] == 'cache_hit']
    ch_off = len(ch) - (N + 1)                       # N do seeding + 1 c0
    hs = sum(1 for g in guards if g['name'] == 'hard_stop')
    novos = (31 * D - 1) - n_doe
    k_last = novos + ch_off + hs - (man['n_geracoes'] - 1) * N   # subproblema do hard-stop
    tent = (man['n_geracoes'] - 1) * N + k_last
    lo = float(fi[:-1].mean() if len(fi) > 1 else fi[0]) * pnm   # início das gerações
    hi = float(fi[1:].mean() if len(fi) > 1 else fi[0]) * pnm    # fim das gerações
    med = ch_off / tent
    p_sbx = 0.5 ** D
    lo2 = (float(fi[:-1].mean() if len(fi) > 1 else fi[0]) + (1 - float(fi[:-1].mean() if len(fi) > 1 else fi[0])) * p_sbx) * pnm
    hi2 = (float(fi[1:].mean() if len(fi) > 1 else fi[0]) + (1 - float(fi[1:].mean() if len(fi) > 1 else fi[0])) * p_sbx) * pnm

    # E5 distância temporal do cache-hit
    sid_off = np.array([g['solution_id'] for g in ch[N + 1:]], dtype=int)
    fe_off = np.array([g['fe'] for g in ch[N + 1:]], dtype=int)
    idade = fe_off - sid_off        # nº de FEs entre o alvo e o momento do hit
    rows.append(dict(problema=prob, D=D, M=M, N=N, T=T, n_ger=man['n_geracoes'],
                     tim_null_ok=e1_fit, tim_ordem_ok=e1_ord, tim_pos_ok=e1_pos,
                     soma_tger=st, t_total=tt, t_aval=ta, aval_le_ger=e1_aval_le,
                     frac_ger_no_total=st / tt, frac_aval=ta / st,
                     ideal_eq_minpop=ok_ideal, nadir_eq_maxpop=ok_nadir,
                     nf1_confere=ok_nf1, fbest_e_individuo=ok_fbest_ind, n_gens=len(gens),
                     k_hardstop=k_last, tentativas=tent,
                     clone_lo=lo, clone_hi=hi, clone_lo2=lo2, clone_hi2=hi2, clone_med=med,
                     dentro_bracket=bool(min(lo2, hi2) - 1e-9 <= med <= max(lo2, hi2) + 1e-9),
                     idade_med=float(np.median(idade)) if len(idade) else np.nan,
                     idade_max=int(idade.max()) if len(idade) else -1,
                     hits_no_mesmo_lote=int((idade <= N).sum()), n_hits_off=len(idade)))

df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'moead_extras.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40)
print(df.to_string())
print()
print('tim_null_ok %d/25 | tim_ordem_ok %d/25 | tim_pos_ok %d/25 | aval<=Σger %d/25'
      % (df.tim_null_ok.sum(), df.tim_ordem_ok.sum(), df.tim_pos_ok.sum(), df.aval_le_ger.sum()))
print('ideal==min(pop): %d/%d | nadir==max(pop): %d/%d | n_front1 confere: %d/%d | f_best É um indivíduo: %d/%d'
      % (df.ideal_eq_minpop.sum(), df.n_gens.sum(), df.nadir_eq_maxpop.sum(), df.n_gens.sum(),
         df.nf1_confere.sum(), df.n_gens.sum(), df.fbest_e_individuo.sum(), df.n_gens.sum()))
print('k_hardstop range: %d..%d (N=15/20)' % (df.k_hardstop.min(), df.k_hardstop.max()))
print('clonagem dentro do bracket previsto: %d/25' % df.dentro_bracket.sum())
print('Σ tentativas: %d | Σ hits de offspring: %d | taxa global %.4f'
      % (df.tentativas.sum(), df.n_hits_off.sum(), df.n_hits_off.sum() / df.tentativas.sum()))
print('frac do tempo total gasto nas gerações: med %.3f' % df.frac_ger_no_total.median())
