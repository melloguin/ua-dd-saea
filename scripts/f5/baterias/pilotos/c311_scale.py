#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bateria de aspectos c311 em escala (54 células, semente 42). READ-ONLY."""
import json, math, os, sys
import numpy as np
import pandas as pd

BASE = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c311'
OUT = '/private/tmp/claude-501/-Users-gmello/c7372206-5092-4c09-9686-ccae3785ca0c/scratchpad'

labels = sorted(os.listdir(BASE))
labels = [l for l in labels if not l.startswith('.') and l != 'swap_big-mvns_MMF16_20']

def exp_of(label):
    if label.startswith('swap_'):
        tok = label.split('_')[1]          # ex 'big-lhs'
        return 'sweep-' + tok
    return 'off'

def problema_of(label):
    if label.startswith('swap_'):
        return label.split('_', 2)[2]
    return label

def pareto_mask(F):
    n = len(F)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not mask[i]:
            continue
        dom = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if dom.any():
            mask[i] = False
    return mask

rows = []
growth_rows = []
for label in labels:
    exp = exp_of(label)
    prob = problema_of(label)
    d = os.path.join(BASE, label, '42')
    stem = f'exp_{exp}_c311_{prob}_42'
    r = {'label': label, 'exp': exp, 'problema': prob}
    man = json.load(open(os.path.join(d, stem + '.manifest.json')))
    p = man['params']
    r['status'] = man['status']
    r['maxfe'] = man['maxfe']; r['fe_final'] = man['fe_final']
    r['n_geracoes_man'] = man['n_geracoes']
    r['tempo_aval_real_s'] = man['timing']['tempo_aval_real_s']
    r['wall_s'] = man['timing']['tempo_total_s']
    r['msl'] = p['min_samples_leaf']; r['max_depth'] = p['max_depth']
    r['kernel_decl'] = 'Matern52' in str(p.get('kernel', '')) or 'Matern52' in str(man['sigma_dict'].get('modelo', ''))
    r['sel_mean_decl'] = 'mean' in str(p.get('selection_type', '')) or 'mean' in str(p)
    r['params_keys'] = ','.join(sorted(p.keys()))
    r['cache_hits'] = man.get('cache_hits')
    r['fit_series_n'] = len(man.get('fit_series', []))

    # ① real
    real = pd.read_parquet(os.path.join(d, stem + '__real.parquet'))
    xcols = [c for c in real.columns if c.startswith('x')]
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    D = len(xcols); M = len(fcols); N = len(real)
    r['D'] = D; r['M'] = M; r['N'] = N
    tier = 'small' if exp == 'off' else label.split('_')[1].split('-')[0]
    r['tier'] = tier
    N_exp = {'small': 31 * D - 1, 'medium': 2000, 'big': 50000}[tier]
    r['ok_N'] = (N == N_exp) and (man['maxfe'] == N) and (man['fe_final'] == N)
    r['ok_fase_init'] = (real['fase'] == 'init').all()
    r['ok_fe_dense'] = (real['fe_index'].values == np.arange(N)).all()
    r['ok_msl_10D'] = (p['min_samples_leaf'] == 10 * D)
    Imax = math.ceil(N / (10 * D))
    r['I_max'] = Imax

    # ⑥ jsonl
    evs = []
    n_bad = 0
    with open(os.path.join(d, stem + '.jsonl')) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                evs.append(json.loads(line))
            except Exception:
                n_bad += 1
    r['jsonl_bad'] = n_bad
    recs = [e.get('rec') for e in evs]
    dec = [e for e in evs if e.get('rec') == 'decision']
    son = [e for e in evs if e.get('rec') == 'sonda']
    foot = [e for e in evs if e.get('rec') == 'footer']
    guards = [e for e in evs if e.get('rec') == 'guard']
    r['n_dec'] = len(dec); r['n_sonda_ev'] = len(son); r['n_footer'] = len(foot)
    r['n_guard'] = len(guards)
    r['I_eff'] = len(dec)
    r['ok_Ieff_le_Imax'] = len(dec) <= Imax
    es_flags = [bool(e.get('early_stop')) for e in dec]
    r['early_stop_any'] = any(es_flags)
    r['early_stop_last'] = es_flags[-1] if es_flags else None
    r['early_stop_fired'] = (len(dec) < Imax)
    r['delta_tp_last'] = dec[-1].get('delta_total_point') if dec else None
    r['delta_tp_uniq'] = len(set(str(e.get('delta_total_point')) for e in dec))
    r['dec_ger'] = ','.join(str(e.get('geracao')) for e in dec[:8])
    r['ok_dec_ger_51'] = all(int(e['geracao']) == 51 * (i + 1) for i, e in enumerate(dec))
    # growth per objective
    ngps = np.array([e['n_gps'] for e in dec])          # (I_eff, M)
    nfol = np.array([e['n_folhas'] for e in dec])
    prof = np.array([e['profundidade'] for e in dec])
    tpts = np.array([e['total_points_per_model'] for e in dec])
    r['ok_lists_M'] = ngps.shape[1] == M
    r['ok_gps_mono'] = bool((np.diff(ngps, axis=0) >= 0).all() and (np.diff(ngps, axis=0) <= 1).all()) if len(dec) > 1 else True
    r['ok_gps_le_folhas'] = bool((ngps <= nfol).all())
    r['ok_folhas_cap'] = bool(nfol.max() <= N // (10 * D))
    r['prof_max'] = int(prof.max()); r['ok_prof_le_100'] = bool(prof.max() <= 100)
    r['ok_tpts_mono'] = bool((np.diff(tpts, axis=0) >= 0).all()) if len(dec) > 1 else True
    incs = np.diff(tpts, axis=0).ravel() if len(dec) > 1 else np.array([])
    pos = incs[incs > 0]
    Nmin = 10 * D
    r['ok_inc_band'] = bool(((pos >= Nmin) & (pos <= 2 * Nmin - 1)).all()) if len(pos) else True
    r['inc_min'] = int(pos.min()) if len(pos) else None
    r['inc_max'] = int(pos.max()) if len(pos) else None
    r['ok_tpts_le_N'] = bool(tpts.max() <= N)
    r['gps_final'] = ','.join(map(str, ngps[-1])); r['folhas_final'] = ','.join(map(str, nfol[-1]))
    r['tpts_final_frac'] = float(tpts[-1].max()) / N
    r['cover_full'] = bool((ngps[-1] == nfol[-1]).all())
    fb = np.array([e.get('f_best') for e in dec], dtype=float)
    r['f_best_min'] = float(np.nanmin(fb)) if fb.size else None
    # sonda events
    r['ok_sonda_ev'] = (len(son) == 2 and all(e.get('n_pontos') == 20000 for e in son)
                        and all(str(e.get('hash_check', '')).startswith('ok') for e in son)
                        and sorted(e.get('modelo_flag') for e in son) == ['treedGP_build', 'treedGP_final'])
    # footer
    if foot:
        frun = [f for f in foot if 'n_final' in f or 'n_geracoes' in f]
        fr = frun[0] if frun else foot[0]
        r['foot_motivo'] = fr.get('motivo'); r['foot_n_final'] = fr.get('n_final')
        r['foot_n_nd'] = fr.get('n_nd_pos_real'); r['foot_ngen'] = fr.get('n_geracoes')
        r['foot_cache_hits'] = fr.get('cache_hits')
    else:
        r['foot_motivo'] = 'SEM_FOOTER'; r['foot_n_final'] = None; r['foot_n_nd'] = None; r['foot_ngen'] = None
        r['foot_cache_hits'] = None

    for i, e in enumerate(dec):
        growth_rows.append({'label': label, 'tier': tier, 'prob': prob, 'iter': i + 1,
                            'ger': e.get('geracao'), 'n_gps': e['n_gps'], 'n_folhas': e['n_folhas'],
                            'tpts': e['total_points_per_model'], 'early_stop': e.get('early_stop'),
                            'delta_tp': e.get('delta_total_point'), 'prof': e['profundidade']})

    # ② pop
    pop = pd.read_parquet(os.path.join(d, stem + '__pop.parquet'))
    r['ok_pop_vazia'] = len(pop) == 0

    # ③ surrogate
    sur = pd.read_parquet(os.path.join(d, stem + '__surrogate.parquet'))
    busca = sur[sur.regime == 'offline']
    sonda = sur[sur.regime == 'sonda']
    ger = busca.geracao.dropna().astype(int)
    ngen = int(ger.max())
    r['ngen_3'] = ngen
    exp_ngen = 51 * len(dec) + 1000
    r['ok_ngen'] = (ngen == exp_ngen == man['n_geracoes'])
    r['ok_ger_denso'] = set(ger.unique()) == set(range(1, ngen + 1))
    bmax = busca[busca.modelo_flag == 'treedGP_build'].geracao.dropna().astype(int).max()
    fmin = busca[busca.modelo_flag == 'treedGP_final'].geracao.dropna().astype(int).min()
    r['ok_fases'] = (int(bmax) == 51 * len(dec)) and (int(fmin) == 51 * len(dec) + 1)
    r['ok_rsid_null'] = busca.real_solution_id.notna().sum() == 0
    r['ok_fetm'] = list(sur.fe_treino_max.dropna().unique()) == [N - 1]
    sigcols = [c for c in sur.columns if c.startswith('sigma_')]
    mucols = [c for c in sur.columns if c.startswith('mu_')]
    pre = busca[ger.reindex(busca.index) <= 50]
    pre = busca[busca.geracao.notna() & (busca.geracao <= 50)]
    r['nan_pre50'] = float(pre[sigcols].isna().values.mean())
    bb = busca[busca.modelo_flag == 'treedGP_build']
    ff = busca[busca.modelo_flag == 'treedGP_final']
    r['nan_build'] = float(bb[sigcols].isna().values.mean())
    r['nan_final'] = float(ff[sigcols].isna().values.mean())
    r['ok_sonda_40k'] = len(sonda) == 40000
    b1 = sonda.iloc[:20000].reset_index(drop=True)
    b2 = sonda.iloc[20000:].reset_index(drop=True)
    cmp_cols = mucols + sigcols + xcols
    eq = True
    for c in cmp_cols:
        a, b = b1[c].values, b2[c].values
        if not ((a == b) | (pd.isna(a) & pd.isna(b))).all():
            eq = False
            break
    r['ok_sonda_bitid'] = eq
    r['nan_sonda'] = float(b1[sigcols].isna().values.mean())
    # pop por geração
    gsz = busca.groupby(busca.geracao.dropna().astype(int)).size()
    lat = 50 if M == 2 else 105
    r['pop_max'] = int(gsz.max()); r['ok_pop_teto'] = gsz.max() <= lat
    r['pop_min_pre50'] = int(gsz.loc[gsz.index <= 50].min())
    r['pop_med_final'] = float(gsz.loc[gsz.index > 51 * len(dec)].median())

    # ④ timing
    tim = pd.read_parquet(os.path.join(d, stem + '__timing.parquet'))
    r['ok_tim_rows'] = len(tim) == len(dec)
    r['ok_tim_ger'] = list(tim.geracao.astype(int)) == [51 * (i + 1) for i in range(len(dec))]
    ok_inv = ((tim.tempo_fit_s + tim.tempo_busca_s) <= tim.tempo_geracao_s + 1e-6).all()
    r['ok_tim_inv'] = bool(ok_inv)
    v = (tim.tempo_fit_s + tim.tempo_busca_s + tim.tempo_pred_sonda_s.fillna(0)) > tim.tempo_geracao_s + 1e-6
    r['tim_viol_sonda_rows'] = ','.join(str(int(g)) for g in tim.geracao[v])
    r['ok_tim_viol_last'] = bool(list(v) == [False] * (len(tim) - 1) + [True]) if len(tim) else False

    # ⑦ final
    fin = pd.read_parquet(os.path.join(d, stem + '__final.parquet'))
    r['n_final'] = len(fin)
    r['ok_orig_ger'] = (fin.origem_geracao == ngen).all()
    F = fin[[f'f{j}' for j in range(M)]].values.astype(float)
    mask = pareto_mask(F)
    nd_col = fin['nd_pos_real'].values.astype(bool)
    r['ok_nd_recomp'] = bool((mask == nd_col).all())
    r['nd_ratio'] = f"{int(nd_col.sum())}/{len(fin)}"
    # link posicional
    last = busca[busca.geracao == ngen].reset_index(drop=True)
    r['ok_n_final_pop'] = len(fin) == len(last)
    ok_link = True
    try:
        idx = fin['origem_linha'].values.astype(int)
        XF = fin[xcols].values
        XS = last[xcols].values[idx]
        ok_link = bool((XF == XS).all())
    except Exception as ex:
        ok_link = f'ERR:{ex}'
    r['ok_link_pos'] = ok_link
    r['ok_foot_n'] = (r['foot_n_final'] in (None, len(fin))) and (r['foot_n_nd'] in (None, int(nd_col.sum())))

    rows.append(r)
    print(label, 'ok', flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'c311_aspectos_54.csv'), index=False)
with open(os.path.join(OUT, 'c311_growth.json'), 'w') as fh:
    json.dump(growth_rows, fh)
print('DONE', len(df))
