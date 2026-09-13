#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F5.3b · moead_media — BATERIA 1: estrutural (U1-U12 + família offline + config).
READ-ONLY nos dados. Escreve SOMENTE em f5/baterias/moead_media/.
Executa em TODAS as 45 células (25 off + 20 sweep), semente 42.
"""
import json, os, glob, hashlib, sys
import numpy as np
import pandas as pd

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = REPO + '/f5/baterias/moead_media'
DS = REPO + '/data/datasets'
SONDA = REPO + '/data/sonda'
EPS32 = np.finfo(np.float32).eps

def xcols(df):
    return sorted([c for c in df.columns if c[0] == 'x' and c[1:].isdigit()], key=lambda c: int(c[1:]))

def fcols(df):
    return sorted([c for c in df.columns if c[0] == 'f' and c[1:].isdigit()], key=lambda c: int(c[1:]))

def ndmask(F):
    """máscara não-dominada (minimização), definição padrão."""
    n = len(F)
    nd = np.ones(n, dtype=bool)
    for i in range(n):
        if not nd[i]:
            continue
        d = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if d.any():
            nd[i] = False
    return nd

rows = []
tj = []           # turnover por geração
sondajoin = []
for label in sorted(os.listdir(RES)):
    d = os.path.join(RES, label, '42')
    if not os.path.isdir(d):
        continue
    mfp = [p for p in glob.glob(d + '/*.manifest.json') if '__final' not in p][0]
    m = json.load(open(mfp))
    base = mfp[:-len('.manifest.json')]
    prob, exp = m['problema'], m['exp']
    r = {'label': label, 'exp': exp, 'problema': prob, 'tier': m['tier'] or 'small',
         'dist': m['dist'] or 'lhs'}
    # ── ⑤ manifesto ────────────────────────────────────────────────────
    r['status'] = m['status']; r['motivo_parada'] = m.get('motivo_parada')
    r['maxfe'] = m['maxfe']; r['fe_final'] = m['fe_final']; r['n_ger'] = m['n_geracoes']
    r['algo_version'] = m['algo_version']; r['env'] = m['env']['executable'].split('/')[-3]
    r['cache_hits'] = m['cache_hits']; r['fallback'] = m['fallback_ativado']
    r['n_retries'] = m['n_retries']; r['stack_trace'] = m['stack_trace'] is not None
    r['has_params_5'] = 'params' in m
    r['fit_series_len'] = len(m['fit_series'])
    r['sonda_nblocos_5'] = m['sonda']['n_blocos']; r['sonda_S_5'] = m['sonda']['S']
    r['t_total'] = m['timing']['tempo_total_s']; r['t_fit'] = m['timing']['tempo_fit_surrogate_s']
    r['t_busca'] = m['timing']['tempo_busca_s']; r['t_aval_real'] = m['timing']['tempo_aval_real_s']
    r['t_sonda'] = m['timing']['tempo_pred_sonda_s']
    sd = m['sigma_dict']
    r['sd_keys'] = len(sd)
    r['sd_modelo_hp_null'] = 'NULL no offline' in sd.get('modelo_hp', '')
    r['sd_sigma_null'] = 'NULL POR CONSTRUCAO' in sd.get('sigma_*', '')
    r['sd_mode12'] = 'mode 12' in sd.get('motor', '')
    # ── ① real ─────────────────────────────────────────────────────────
    d1 = pd.read_parquet(base + '__real.parquet')
    XC, FC = xcols(d1), fcols(d1)
    D, M = len(XC), len(FC)
    r['D'] = D; r['M'] = M
    r['n1'] = len(d1)
    r['u1_n1_eq_maxfe'] = (len(d1) == m['maxfe'] == m['fe_final'])
    r['u1_n1_eq_esperado'] = (len(d1) == (31 * D - 1 if m['tier'] in (None, 'small') else 2000))
    r['u1_fase_init_pct'] = float((d1['fase'] == 'init').mean())
    r['u1_fe_index_denso'] = bool(np.array_equal(d1['fe_index'].values, np.arange(len(d1))))
    r['u1_solution_id_denso'] = bool(np.array_equal(np.sort(d1['solution_id'].values), np.arange(len(d1))))
    # ── U2: binding ① ↔ artefato do dataset (bit-a-bit) ───────────────
    tag = '' if m['tier'] in (None, 'small') and m['dist'] in (None, 'lhs') else \
          '_%s_%s' % (m['tier'], m['dist'])
    dsp = '%s/%s/ds_%s_42%s.parquet' % (DS, prob, prob, tag)
    if os.path.exists(dsp):
        ds = pd.read_parquet(dsp)
        Xa = ds[xcols(ds)].values.astype(np.float32)
        Fa = ds[fcols(ds)].values.astype(np.float32)
        X1 = d1[XC].values.astype(np.float32); F1 = d1[FC].values.astype(np.float32)
        r['u2_ds_n'] = len(ds)
        r['u2_dX_max'] = float(np.abs(Xa - X1).max()) if Xa.shape == X1.shape else np.nan
        r['u2_dF_max'] = float(np.abs(Fa - F1).max()) if Fa.shape == F1.shape else np.nan
        r['u2_bitaabit'] = bool(np.array_equal(Xa, X1) and np.array_equal(Fa, F1))
        dsm = json.load(open(dsp.replace('.parquet', '.manifest.json')))
        r['u2_ds_tier'] = dsm['tier']; r['u2_ds_dist'] = dsm['dist']
    else:
        r['u2_ds_n'] = -1; r['u2_bitaabit'] = False
    r['u2_doe_hash_eq_cp'] = (m['doe_hash'] == m['cp_init_offline']['x_hash'])
    # ── ② pop ──────────────────────────────────────────────────────────
    d2 = pd.read_parquet(base + '__pop.parquet')
    r['n2'] = len(d2)
    # ── ③ surrogate ────────────────────────────────────────────────────
    d3 = pd.read_parquet(base + '__surrogate.parquet')
    r['n3'] = len(d3)
    reg = d3['regime'].value_counts().to_dict()
    r['n3_sonda'] = reg.get('sonda', 0); r['n3_offline'] = reg.get('offline', 0)
    r['n3_regimes'] = '|'.join(sorted(reg))
    off3 = d3[d3['regime'] == 'offline']
    son3 = d3[d3['regime'] == 'sonda']
    g = off3['geracao'].dropna().astype(int)
    r['u10_ger_min'] = int(g.min()); r['u10_ger_max'] = int(g.max())
    r['u10_ger_denso'] = bool(set(g.unique()) == set(range(1, m['n_geracoes'] + 1)))
    perg = g.value_counts()
    r['N_lattice'] = int(perg.mode().iloc[0])
    r['u10_pop_const'] = bool(perg.nunique() == 1)
    r['u10_n3off_eq'] = bool(len(off3) == r['N_lattice'] * m['n_geracoes'])
    r['c3_fe_surr'] = int(len(off3))
    r['c3_overshoot_ok'] = bool(len(off3) > 40000 >= len(off3) - r['N_lattice'])
    r['c3_nger_formula'] = bool(m['n_geracoes'] == 40000 // r['N_lattice'] + 1)
    mucols = ['mu_%d' % j for j in range(M)]
    sicols = ['sigma_%d' % j for j in range(M)]
    r['f2_sigma_nan_pct'] = float(d3[sicols].isna().all(axis=1).mean())
    r['f2_mu_nan_pct'] = float(d3[mucols].isna().any(axis=1).mean())
    r['f3_rsid_null_pct'] = float(d3['real_solution_id'].isna().mean())
    r['u8_fe_treino_max_u'] = '|'.join(map(str, sorted(d3['fe_treino_max'].unique())))
    r['u8_fe_treino_ok'] = bool(d3['fe_treino_max'].nunique() == 1 and
                                int(d3['fe_treino_max'].iloc[0]) == len(d1) - 1)
    r['c8_espaco'] = '|'.join(sorted(d3['espaco_modelo'].unique()))
    r['c8_transf_null'] = bool(d3['transf_tipo'].isna().all() and d3['transf_params'].isna().all())
    r['c1_modelo_flag'] = '|'.join(sorted(d3['modelo_flag'].unique()))
    r['c1_pred_tipo'] = '|'.join(sorted(d3['pred_tipo'].unique()))
    r['c1_pred_cls_null'] = bool(d3['pred_classe'].isna().all() and
                                 d3['pred_score'].isna().all() and d3['pred_confianca'].isna().all())
    r['c17_sonda_ger_null'] = bool(son3['geracao'].isna().all())
    # ── U5: join posicional sonda × gabarito ───────────────────────────
    sp = '%s/sonda_%s.parquet' % (SONDA, prob)
    sa = pd.read_parquet(sp)
    sam = json.load(open(sp.replace('.parquet', '.manifest.json')))
    Xs = son3[XC].values.astype(np.float32)
    Xg = sa[xcols(sa)].values.astype(np.float32)
    r['u5_n_sonda'] = len(son3)
    r['u5_dX_max'] = float(np.abs(Xs - Xg[:len(Xs)]).max()) if len(Xs) else np.nan
    r['u5_ok'] = bool(r['u5_dX_max'] <= EPS32)
    r['u5_hash_ok'] = (m['sonda']['x_hash'] == sam['x_hash'] and m['sonda']['f_hash'] == sam['f_hash'])
    Fg = sa[fcols(sa)].values.astype(np.float64)[:len(Xs)]
    Mu = son3[mucols].values.astype(np.float64)
    for j in range(M):
        sondajoin.append({'label': label, 'exp': exp, 'problema': prob, 'obj': j,
                          'wape': float(np.abs(Mu[:, j] - Fg[:, j]).sum() / np.abs(Fg[:, j]).sum()),
                          'corr': float(np.corrcoef(Mu[:, j], Fg[:, j])[0, 1]),
                          'mu_min': float(Mu[:, j].min()), 'mu_max': float(Mu[:, j].max()),
                          'f_min': float(Fg[:, j].min()), 'f_max': float(Fg[:, j].max())})
    # ── ④ timing ───────────────────────────────────────────────────────
    d4 = pd.read_parquet(base + '__timing.parquet')
    r['n4'] = len(d4)
    r['u3_n4_eq1'] = bool(len(d4) == 1 and len(m['fit_series']) == 1)
    r['u3_nacum'] = int(d4['n_acumulado'].iloc[0])
    r['u3_nacum_ok'] = bool(int(d4['n_acumulado'].iloc[0]) == len(d1))
    fb = float(d4['tempo_fit_s'].iloc[0]) + float(d4['tempo_busca_s'].iloc[0])
    tg = float(d4['tempo_geracao_s'].iloc[0])
    r['u7_fit_busca'] = fb; r['u7_tempo_ger'] = tg
    r['u7_le'] = bool(fb <= tg * (1 + 1e-6))
    r['u7_sonda_excluida'] = bool(abs(fb - tg) <= 1e-3 and float(d4['tempo_pred_sonda_s'].iloc[0]) > 0)
    # ── ⑥ jsonl ────────────────────────────────────────────────────────
    recs, bad, badtxt = [], 0, []
    for ln in open(base + '.jsonl', encoding='utf-8', errors='replace'):
        ln = ln.strip()
        if not ln:
            continue
        try:
            recs.append(json.loads(ln))
        except Exception:
            bad += 1; badtxt.append(ln[:120])
    from collections import Counter
    cc = Counter(x.get('rec') for x in recs)
    r['j_bad'] = bad; r['j_badtxt'] = ' ⟂ '.join(badtxt)[:200]
    r['j_header'] = cc.get('header', 0); r['j_sonda'] = cc.get('sonda', 0)
    r['j_decision'] = cc.get('decision', 0); r['j_footer'] = cc.get('footer', 0)
    r['j_guard'] = cc.get('guard', 0)
    r['j_recs'] = '|'.join(sorted(cc))
    dec = [x for x in recs if x.get('rec') == 'decision']
    r['u10_dec_eq_nger'] = bool(len(dec) == m['n_geracoes'])
    r['u10_dec_denso'] = bool(set(x['geracao'] for x in dec) == set(range(1, m['n_geracoes'] + 1)))
    r['c9_caminho'] = '|'.join(sorted({x.get('caminho', '') for x in dec}))
    r['c9_motivo'] = '|'.join(sorted({x.get('motivo', '') for x in dec}))[:90]
    r['c9_chaves_dec'] = '|'.join(sorted(dec[0].keys()))
    r['f3_nds_membros0'] = bool(all(x.get('n_ds_membros') == 0 for x in dec))
    r['j_fe_const'] = bool(len({x.get('fe') for x in dec}) == 1 and dec[0]['fe'] == len(d1))
    r['j_fbest_len'] = bool(all(len(x.get('f_best', [])) == M for x in dec))
    r['j_nfront1_min'] = min(x.get('n_front1', -1) for x in dec)
    r['j_nfront1_max'] = max(x.get('n_front1', -1) for x in dec)
    sev = [x for x in recs if x.get('rec') == 'sonda']
    r['u4_sonda_ev'] = len(sev)
    r['u4_npontos'] = sev[0]['n_pontos'] if sev else -1
    r['u4_hashcheck'] = sev[0].get('hash_check', '')[:2] if sev else ''
    r['u4_sonda_ger'] = sev[0].get('geracao') if sev else None
    ft = [x for x in recs if x.get('rec') == 'footer']
    r['j_footer_status'] = ft[0].get('status') if ft else None
    r['j_footer_nfinal'] = ft[0].get('n_final') if ft else None
    r['j_footer_nnd'] = ft[0].get('n_nd_pos_real') if ft else None
    r['u9_cache_footer'] = ft[0].get('cache_hits') if ft else None
    r['j_footer_cpinit'] = ft[0].get('cp_init') if ft else None
    # ── ⑦ final ────────────────────────────────────────────────────────
    d7 = pd.read_parquet(base + '__final.parquet')
    r['n7'] = len(d7)
    F7 = d7[fcols(d7)].values.astype(np.float64)
    nd = ndmask(F7)
    r['u12_nd_recomputo_ok'] = bool(np.array_equal(nd, d7['nd_pos_real'].values.astype(bool)))
    r['u12_nd'] = int(d7['nd_pos_real'].sum())
    r['u12_fantasia'] = float(d7['nd_pos_real'].mean())
    r['u12_origem_ger_u'] = '|'.join(map(str, sorted(d7['origem_geracao'].unique())))
    r['u12_origem_ger_ok'] = bool((d7['origem_geracao'] == m['n_geracoes']).all())
    r['u12_rsid_null'] = bool(d7['origem_solution_id'].isna().all())
    r['u12_n7_eq_pop'] = bool(len(d7) == int(perg.get(m['n_geracoes'], -1)))
    r['u12_footer_ok'] = bool(r['j_footer_nfinal'] == len(d7) and r['j_footer_nnd'] == int(d7['nd_pos_real'].sum()))
    # link posicional (ger, linha) → ③
    lastg = off3[off3['geracao'] == m['n_geracoes']].reset_index(drop=True)
    idx = d7['origem_linha'].values
    r['u12_linha_denso'] = bool(np.array_equal(np.sort(idx), np.arange(len(d7))))
    X7 = d7[XC].values.astype(np.float32)
    X3 = lastg.loc[idx, XC].values.astype(np.float32)
    r['u12_link_dX'] = float(np.abs(X7 - X3).max())
    r['u12_link_bit'] = bool(np.array_equal(X7, X3))
    # U11-offline: erro de fantasia μ (③ última ger) × f real (⑦)
    Mu7 = lastg.loc[idx, mucols].values.astype(np.float64)
    r['u11_erro_fantasia_med'] = float(np.median(np.abs(Mu7 - F7)))
    r['u11_erro_fant_rel_med'] = float(np.median(np.abs(Mu7 - F7) / np.maximum(np.abs(F7), 1e-12)))
    r['u11_mu_menor_pct'] = float((Mu7 < F7).mean())   # otimismo do modelo
    # ── turnover posicional por geração (③ offline) ────────────────────
    A = off3.sort_values('geracao', kind='stable')[XC].values.astype(np.float32)
    Np = r['N_lattice']
    if r['u10_pop_const'] and len(A) == Np * m['n_geracoes']:
        A = A.reshape(m['n_geracoes'], Np, D)
        ch = (A[1:] != A[:-1]).any(axis=2).mean(axis=1)
        r['c14_turnover_med'] = float(np.median(ch))
        r['c14_turnover_mean'] = float(ch.mean())
        r['c14_turnover_g1'] = float(ch[0])
        r['c14_turnover_ult'] = float(ch[-1])
        r['c14_turnover_max'] = float(ch.max())
        r['c14_gers_sem_mudanca'] = int((ch == 0).sum())
        q = max(1, len(ch) // 4)
        r['c14_turnover_q1'] = float(ch[:q].mean()); r['c14_turnover_q4'] = float(ch[-q:].mean())
        for i, v in enumerate(ch):
            tj.append({'label': label, 'geracao': i + 2, 'turnover': float(v)})
    print('%-26s ok' % label, flush=True)
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(OUT + '/bateria1_estrutural.csv', index=False)
pd.DataFrame(tj).to_csv(OUT + '/turnover_por_geracao.csv.gz', index=False, compression='gzip')
pd.DataFrame(sondajoin).to_csv(OUT + '/sonda_recomputada.csv', index=False)
print('\n== %d células ==' % len(df))
bools = [c for c in df.columns if df[c].dtype == bool]
for c in bools:
    print('%-26s %d/%d True' % (c, int(df[c].sum()), len(df)))
