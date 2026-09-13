#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""F5.3a c217 — bateria em escala (25 células main, semente 42). READ-ONLY."""
import json, os, glob
import numpy as np
import pandas as pd

BASE = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c217'
SONDA_ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
TRAJ = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/trajetorias'
probs = sorted(os.listdir(BASE))
probs = [p for p in probs if not p.startswith('_')]

rows = []
sonda_health = []
state_events = []  # per-gen state records across cells
hdr_keys_seen = set()
rng = np.random.default_rng(0)

def dom_auc(FA, FB, cap=250):
    """AUC = P(+1 domina -1) + 0.5*P(incomparavel)."""
    if len(FA) == 0 or len(FB) == 0:
        return np.nan
    if len(FA) > cap: FA = FA[rng.choice(len(FA), cap, replace=False)]
    if len(FB) > cap: FB = FB[rng.choice(len(FB), cap, replace=False)]
    A = FA[:, None, :]; B = FB[None, :, :]
    le = (A <= B).all(-1); lt = (A < B).any(-1)
    ge = (A >= B).all(-1); gt = (A > B).any(-1)
    win = (le & lt); loss = (ge & gt)
    tot = win.size
    return (win.sum() + 0.5 * (tot - win.sum() - loss.sum())) / tot

for prob in probs:
    d = os.path.join(BASE, prob, '42')
    stem = f'exp_main_c217_{prob}_42'
    man = json.load(open(os.path.join(d, stem + '.manifest.json')))
    ev = [json.loads(l) for l in open(os.path.join(d, stem + '.jsonl'))]
    real = pd.read_parquet(os.path.join(d, stem + '__real.parquet'))
    pop = pd.read_parquet(os.path.join(d, stem + '__pop.parquet'))
    sur = pd.read_parquet(os.path.join(d, stem + '__surrogate.parquet'))
    tim = pd.read_parquet(os.path.join(d, stem + '__timing.parquet'))

    import re as _re
    xcols = [c for c in real.columns if _re.fullmatch(r'x\d+', c)]
    fcols = [c for c in real.columns if _re.fullmatch(r'f\d+', c)]
    D, M = len(xcols), len(fcols)
    header = [e for e in ev if e.get('rec') == 'header'][0]
    footer = [e for e in ev if e.get('rec') == 'footer']
    guards = [e for e in ev if e.get('rec') == 'guard']
    gens = [e for e in ev if e.get('rec') == 'c217_gen']
    sev = [e for e in ev if e.get('rec') == 'sonda']
    hdr_keys_seen |= set(header.keys())

    r = dict(prob=prob, D=D, M=M)
    r['n_ger_man'] = man['n_geracoes']
    r['status'] = man['status']
    r['termino'] = footer[0].get('termino') if footer else None
    r['cp_init'] = footer[0].get('cp_init') if footer else None

    # U1/A1 orcamento
    r['A1_fe'] = (len(real) == 31 * D - 1) and (man['fe_final'] == man['maxfe'] == 31 * D - 1)
    fi = np.sort(real['fe_index'].values)
    r['A1_dense'] = bool((fi == np.arange(31 * D - 1)).all())
    # A2 init
    r['A2_init'] = int((real['fase'] == 'init').sum()) == 11 * D - 1
    r['doe_hash'] = bool(man.get('doe_hash'))
    # A3/A8 header params
    r['A3_N'] = header.get('N')
    r['A8_delta'] = header.get('delta')
    r['gmax_hdr'] = header.get('gmax')
    r['spread_hdr'] = header.get('spread', None)
    # A4 retreino
    r['A4_fit'] = bool(tim['tempo_fit_s'].notna().all()) and (len(man['fit_series']) == len(gens))
    r['n_gens_ev'] = len(gens)
    r['n_tim'] = len(tim)
    # A18 fantasma
    r['A18_ghost'] = (len(tim) == man['n_geracoes'] - 1) and (len(gens) == man['n_geracoes'] - 1)

    g = pd.DataFrame(gens)
    # A5 split
    g['tuple'] = list(zip(g.n_best, g.n_worst, g.n_treino, g.n_Pmid))
    steady = g[g.geracao >= 2]
    modal = steady['tuple'].mode().iloc[0] if len(steady) else None
    r['A5_modal'] = modal
    r['A5_n_off_modal_steady'] = int((steady['tuple'] != modal).sum())
    r['A5_gen1'] = g[g.geracao == 1]['tuple'].iloc[0]
    r['A5_bw_sum'] = bool(((g.n_best + g.n_worst) == g.n_treino).all())
    # A6 pares todos x todos
    r['A6_pares'] = bool((g.n_pares_treino == g.n_treino * (g.n_treino - 1)).all())
    # A7 regra tripla — consistencia numerica estado<=>desigualdade
    delta = header.get('delta', 0.8)
    pred_state = np.where(g.p_mais > delta, 1, np.where(g.p_menos > delta, 2, 3))
    r['A7_consist'] = bool((pred_state == g.estado.values).all())
    r['A7_n_incons'] = int((pred_state != g.estado.values).sum())
    r['st1'] = int((g.estado == 1).sum()); r['st2'] = int((g.estado == 2).sum()); r['st3'] = int((g.estado == 3).sum())
    # granularidade Error (steady, gens>=2): multiplos de 1/6 (D>=5) ou 1/2 (D=2 teste=2)
    if D >= 5:
        gr = steady.p_mais * 6
        r['gran_off'] = int((np.abs(gr - np.round(gr)) > 1e-9).sum())
    else:
        r['gran_off'] = None
    # A9 lote
    r['A9_lote3'] = bool((g.loc[g.estado == 3, 'lote'] == 1).all())
    r['A9_lote12'] = bool((g.loc[g.estado < 3, 'lote'] <= 6).all())
    r['lote_hist'] = dict(g.lote.value_counts().sort_index())
    # A19 NaN no motivo
    r['A19_nan'] = int(g.motivo.astype(str).str.contains('NaN', case=False).sum())
    # A13 spread
    sp = g.modelo_hp.apply(lambda h: h.get('spread') if isinstance(h, dict) else json.loads(h).get('spread') if isinstance(h, str) else None)
    r['A13_spread'] = bool((sp == 0.1925).all())

    # camada 3
    bu = sur[sur.regime == 'online'].copy()
    sb = sur[sur.regime == 'sonda'].copy()
    r['A11_tern'] = set(sur.pred_score.dropna().unique()) <= {-1.0, 0.0, 1.0}
    r['mu_null'] = bool(sur[[c for c in sur.columns if c.startswith('mu_')]].isna().all().all())
    r['sig_null'] = bool(sur[[c for c in sur.columns if c.startswith('sigma_')]].isna().all().all())
    r['n_busca'] = len(bu)
    r['busca_eq_sum_lote'] = (len(bu) == int(g.lote.sum()))
    r['rsid_busca_null'] = int(bu.real_solution_id.isna().sum())
    # A10 gate: escolhidos em gens estado 1/2 tem score +-1 com sinal certo
    g12 = g[g.estado < 3]
    ok10 = True; det10 = []
    for _, ge in g12.iterrows():
        sc = bu[bu.geracao == ge.geracao].pred_score.values
        want = 1.0 if ge.estado == 1 else -1.0
        if not (len(sc) == ge.lote and (sc == want).all()):
            ok10 = False
        det10.append((int(ge.geracao), int(ge.estado), list(sc)))
    r['A10_gate'] = ok10; r['A10_det'] = det10
    # A12 pred_confianca constante por bloco e == p_mais
    nun = sur.dropna(subset=['pred_confianca']).groupby(['regime', 'geracao']).pred_confianca.nunique()
    r['A12_const'] = bool((nun <= 1).all())
    pm = g.set_index('geracao').p_mais
    conf_b = bu.groupby('geracao').pred_confianca.first()
    common = conf_b.index.intersection(pm.index)
    r['A12_eq_pmais_busca'] = bool(np.allclose(conf_b.loc[common], pm.loc[common], atol=1e-9))
    conf_s = sb.groupby('geracao').pred_confianca.first()
    common_s = conf_s.index.intersection(pm.index)
    r['A12_eq_pmais_sonda'] = bool(np.allclose(conf_s.loc[common_s], pm.loc[common_s], atol=1e-9))
    # A14 sonda cadencia + blocos
    sg = sorted(sb.geracao.dropna().astype(int).unique())
    last_full = man['n_geracoes'] - 1
    expect = [1] + [x for x in range(2, last_full + 1, 2)]
    r['A14_cad'] = (sg == expect)
    r['A14_nblocos'] = len(sg)
    r['A14_man_nblocos'] = man['sonda']['n_blocos']
    bsz = sb.groupby('geracao').size()
    r['A14_2000'] = bool((bsz == 2000).all())
    r['last_full_gen_par'] = (last_full % 2 == 0)
    r['A14_last_covered'] = (max(sg) == last_full) if sg else False
    r['sonda_motivos'] = dict(pd.Series([e.get('motivo') for e in sev]).value_counts())
    r['n_sonda_ev'] = len(sev)
    # U5 join posicional (bloco da ger 1 vs artefato[0:2000])
    art = pd.read_parquet(os.path.join(SONDA_ART, f'sonda_{prob}.parquet'))
    b1 = sb[sb.geracao == 1]
    if len(b1) == 2000:
        dx = np.abs(b1[xcols].values - art.iloc[:2000][xcols].values.astype(np.float32))
        r['U5_maxdx'] = float(dx.max())
    else:
        r['U5_maxdx'] = np.nan
    # A15 fe_treino_max nao-monotonico
    ftm = sb.groupby('geracao').fe_treino_max.first().sort_index()
    r['A15_drops'] = int((np.diff(ftm.values) < 0).sum())
    # A16 cache
    r['cache_hits_man'] = man['cache_hits']
    r['n_guard_ev'] = len(guards)
    r['guard_names_ok'] = all(e.get('name') == 'cache_hit' for e in guards)
    arranque = [e for e in guards if e.get('fe') == 1 or e.get('solution_id') == 0]
    r['arranque_guard'] = len(arranque)
    opt_rows = int((real.fase != 'init').sum())
    r['ghost_infill'] = opt_rows - int(g.lote.sum()) + man['cache_hits']
    r['opt_rows'] = opt_rows
    # A17 pop = Arc append-only
    psz = pop.groupby('geracao').size().sort_index()
    arc_ev = g.set_index('geracao').arc_size
    common_a = psz.index.intersection(arc_ev.index)
    r['A17_arc_eq'] = bool((psz.loc[common_a] == arc_ev.loc[common_a]).all())
    r['A17_n_cmp'] = len(common_a)
    r['A17_append'] = bool((np.diff(psz.values) >= 0).all())
    # U7 timing
    r['U7_fitbusca'] = bool(((tim.tempo_fit_s + tim.tempo_busca_s) <= tim.tempo_geracao_s + 1e-9).all())
    ts = tim.set_index('geracao').tempo_pred_sonda_s
    with_block = set(sg)
    pos = set(ts[ts > 0].index.astype(int))
    r['U7_sonda_exact'] = (pos == (with_block & set(ts.index.astype(int))))
    # n_acumulado do timing == n_treino
    ntr = g.set_index('geracao').n_treino
    common_t = ts.index.intersection(ntr.index)
    na = tim.set_index('geracao').n_acumulado
    r['tim_nacum_eq_ntreino'] = bool((na.loc[common_t] == ntr.loc[common_t]).all())

    # ---- SAUDE: sonda por bloco ----
    F_art = art.iloc[:2000][fcols].values
    for gg in sg:
        blk = sb[sb.geracao == gg]
        sc = blk.pred_score.values
        f0 = float((sc == 0).mean()); fp = float((sc == 1).mean()); fm = float((sc == -1).mean())
        auc = dom_auc(F_art[sc == 1], F_art[sc == -1])
        pmg = float(pm.loc[gg]) if gg in pm.index else np.nan
        sonda_health.append(dict(prob=prob, ger=gg, frac0=f0, fracp=fp, fracm=fm,
                                 auc=auc, p_mais=pmg))
    # p_mais trend
    q = len(g) // 4
    if q > 0:
        r['pmais_q1'] = float(g.p_mais.iloc[:q].mean())
        r['pmais_q4'] = float(g.p_mais.iloc[-q:].mean())
    r['pmais_max'] = float(g.p_mais.max()); r['pmenos_max'] = float(g.p_menos.max())

    for _, ge in g.iterrows():
        state_events.append(dict(prob=prob, ger=int(ge.geracao), estado=int(ge.estado),
                                 p_mais=float(ge.p_mais), p_menos=float(ge.p_menos), lote=int(ge.lote)))
    rows.append(r)
    print('done', prob, 'D=', D, 'M=', M, 'gens=', len(g), flush=True)

df = pd.DataFrame(rows)
sh = pd.DataFrame(sonda_health)
se = pd.DataFrame(state_events)
out = '/private/tmp/claude-501/-Users-gmello/c7372206-5092-4c09-9686-ccae3785ca0c/scratchpad'
df.to_pickle(out + '/c217_aspectos.pkl'); sh.to_pickle(out + '/c217_sonda.pkl'); se.to_pickle(out + '/c217_estados.pkl')
print('HEADER KEYS:', sorted(hdr_keys_seen))

# ---- trajetorias ----
tr = []
for prob in probs:
    t = json.load(open(os.path.join(TRAJ, f'main_c217_{prob}_42.json')))
    ig = [c['igd_plus'] for c in t]
    viol = sum(1 for i in range(1, len(ig)) if ig[i] > ig[i - 1] * (1 + 1e-12))
    tr.append(dict(prob=prob, n_cp=len(ig), viol=viol, igd0=ig[0], igdF=ig[-1]))
trd = pd.DataFrame(tr)
trd.to_pickle(out + '/c217_traj.pkl')
print(trd.to_string())
