"""T02 — re-medição da bateria universal + estruturais do c311 sobre as 54 células
válidas da s42 (+ a 55ª, REPROVADA, medida à parte). Não cita: MEDE.
READ-ONLY sobre resultados_experimentos/. Escreve só nesta pasta.
"""
import sys, os, json
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311')
import numpy as np, pandas as pd
import lib_c311 as L

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'
DS = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets'
SONDA = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'

rows = []
for label, d, pref in L.celulas():
    man, evs, dfs = L.carrega(d, pref)
    mt = L.meta(label, man)
    real, sur, tim, fin, pop = dfs['real'], dfs['surrogate'], dfs['timing'], dfs['final'], dfs['pop']
    Xc = L.xcols(real); Fc = L.fcols(real); D, M, N = len(Xc), len(Fc), len(real)
    bu = L.busca(sur); so = L.sonda(sur)
    dec = [e for e in evs if e.get('rec') == 'decision']
    snd = [e for e in evs if e.get('rec') == 'sonda']
    ftr = [e for e in evs if e.get('rec') == 'footer']
    grd = [e for e in evs if e.get('rec') == 'guard']
    rty = [e for e in evs if e.get('rec') == 'retry']
    I = len(dec)
    g = bu['geracao'].astype(int)
    nger = int(g.max())
    r = dict(**mt, D=D, M=M, N=N, I_eff=I, n_ger=nger,
             status=man.get('status'), motivo_parada=man.get('motivo_parada'),
             schema_version=man.get('schema_version'), repo_hash=man.get('repo_hash'),
             campanha_id=man.get('campanha_id'),
             # ── U1 ─────────────────────────────────────────────────────────
             u1_fe=int(man['fe_final'] == man['maxfe'] == N),
             u1_tempo_aval=man['timing'].get('tempo_aval_real_s'),
             u1_init=int((real['fase'] == 'init').all()),
             u1_fe_index=int((real['fe_index'].values == np.arange(N)).all()),
             u1_N_esperado=int(N == (31 * D - 1 if mt['tier'] == 'small'
                                     else 2000 if mt['tier'] == 'medium' else 50000)),
             # ── U2 (proveniência) ──────────────────────────────────────────
             # ── U3/U10 (ledger) ────────────────────────────────────────────
             u3_timing_linhas=int(len(tim) == I == len(man['fit_series'])),
             u3_ger_51i=int((tim['geracao'].astype(int).values ==
                             51 * np.arange(1, I + 1)).all()),
             u10_nger=int(nger == 51 * I + 1000),
             u10_denso=int(set(g.unique()) == set(range(1, nger + 1))),
             u10_ledger=int(1 + I + len(snd) + len(ftr) + len(grd) + len(rty) == len(evs)),
             u10_fases=int(
                 (bu.loc[g <= 51 * I, 'modelo_flag'] == 'treedGP_build').all() and
                 (bu.loc[g > 51 * I, 'modelo_flag'] == 'treedGP_final').all()),
             # ── U4 (sonda) ─────────────────────────────────────────────────
             u4_2blocos=int(len(snd) == 2 and
                            [e['modelo_flag'] for e in snd] == ['treedGP_build', 'treedGP_final']),
             u4_20000=int(all(e['n_pontos'] == 20000 for e in snd)),
             u4_linhas=int(len(so) == 40000),
             u4_ger_null=int(so['geracao'].isna().all()),
             # ── U8 ─────────────────────────────────────────────────────────
             u8_fetreino=int(sur['fe_treino_max'].dropna().nunique() == 1 and
                             int(sur['fe_treino_max'].dropna().iloc[0]) == N - 1),
             # ── U9 ─────────────────────────────────────────────────────────
             u9_cache=int(man.get('cache_hits', 0) == 0),
             n_guard=len(grd), n_retry=len(rty), n_footer=len(ftr),
             guards=';'.join(sorted({e.get('name', '?') for e in grd})),
             # ── U11 ────────────────────────────────────────────────────────
             u11_pop_vazia=int(pop is None or len(pop) == 0),
             u11_rsid=int(sur['real_solution_id'].notna().sum()),
             n_sur=len(sur),
             # ── F1 (congelamento) ──────────────────────────────────────────
             # ── F3 (cobertura) ─────────────────────────────────────────────
             f3_monot=int(all(np.all(np.diff([e['total_points_per_model'] for e in dec],
                                             axis=0) >= 0) for _ in [0]) if I > 1 else 1),
             f3_passo=int(np.all(np.diff([e['n_gps'] for e in dec], axis=0) <= 1)
                          if I > 1 else 1),
             f3_ngps_folhas=int(all(np.all(np.array(e['n_gps']) <= np.array(e['n_folhas']))
                                    for e in dec)),
             f3_teto=int(all(np.all(np.array(e['n_folhas']) <= N // (10 * D)) for e in dec)),
             cobertura_final=float(np.mean(np.array(dec[-1]['total_points_per_model']) / N)),
             cob_completa=int(all(a == b for a, b in zip(dec[-1]['n_gps'], dec[-1]['n_folhas']))),
             prof_max=int(max(max(e['profundidade']) for e in dec)),
             # ── C3 ─────────────────────────────────────────────────────────
             I_max=int(np.ceil(N / (10 * D))),
             # ── C8 (lattice) ───────────────────────────────────────────────
             pop_max=int(bu.groupby('geracao').size().max()),
             pop_min_1_50=int(bu[g <= 50].groupby('geracao').size().min()),
             # ── C11 ────────────────────────────────────────────────────────
             c11_nacum=int(sum(1 for e in dec
                               if e['n_acumulado'] == sum(e['total_points_per_model']))),
             # ── U12 (⑦) ────────────────────────────────────────────────────
             n_final=len(fin), n_nd=int(fin['nd_pos_real'].sum()),
             )
    # U2 — dataset bit-a-bit
    tag = '' if mt['tier'] == 'small' else f"_{mt['tier']}_{mt['dist']}"
    dsp = os.path.join(DS, mt['problema'], f"ds_{mt['problema']}_42{tag}.parquet")
    art = pd.read_parquet(dsp)
    r['u2_dx'] = int((real[Xc].values.astype(np.float32) ==
                      art[Xc].values.astype(np.float32)).all())
    r['u2_df'] = int((real[Fc].values.astype(np.float32) ==
                      art[Fc].values.astype(np.float32)).all())
    sc = json.load(open(dsp.replace('.parquet', '.sidecar.json'))) \
        if os.path.exists(dsp.replace('.parquet', '.sidecar.json')) else None
    r['u2_hash'] = int(sc is not None and
                       man['cp_init_offline']['x_hash'] == sc.get('x_hash') and
                       man['cp_init_offline']['f_hash'] == sc.get('f_hash'))
    r['u2_doe'] = int(man['doe_hash'] == man['cp_init_offline']['x_hash'])
    # F1 — os 2 blocos bit-idênticos
    b0 = so[so['modelo_flag'] == 'treedGP_build'].reset_index(drop=True)
    b1 = so[so['modelo_flag'] == 'treedGP_final'].reset_index(drop=True)
    cols = Xc + L.mucols(so) + L.sigcols(so)
    A = b0[cols].values.astype(np.float64); B = b1[cols].values.astype(np.float64)
    r['f1_bitid'] = int(A.shape == B.shape and
                        np.array_equal(A, B, equal_nan=True))
    r['f1_1000'] = int((g > 51 * I).sum() > 0 and int(g.max()) - 51 * I == 1000)
    # U5 — join posicional com o gabarito
    gab = pd.read_parquet(os.path.join(SONDA, f"sonda_{mt['problema']}.parquet"))
    gxc = L.xcols(gab)
    r['u5_dx'] = float(np.abs(b0[Xc].values.astype(np.float64) -
                              gab[gxc].values[:20000].astype(np.float64)).max())
    # F2 — σ-NaN share por fase/regime
    sg = L.sigcols(sur)
    nan_ini = bu.loc[g <= 50, sg].isna().values.mean() if (g <= 50).any() else np.nan
    nan_bld = bu.loc[g <= 51 * I, sg].isna().values.mean()
    nan_fin = bu.loc[g > 51 * I, sg].isna().values.mean()
    nan_snd = b0[sg].isna().values.mean()
    r.update(f2_nan_1_50=float(nan_ini), f2_nan_build=float(nan_bld),
             f2_nan_final=float(nan_fin), f2_nan_sonda=float(nan_snd),
             n_sigma_valido_sonda=int(np.isfinite(b0[sg].values).sum()))
    # U12 — ND recomputado
    Ffin = fin[L.fcols(fin)].values.astype(np.float64)
    r['u12_nd'] = int(np.array_equal(L.nd_mask(Ffin), fin['nd_pos_real'].values.astype(bool)))
    ultima = bu[g == nger]
    r['u12_link'] = float(np.abs(ultima[Xc].values[fin['origem_linha'].values] -
                                 fin[L.xcols(fin)].values).max()) if len(fin) else np.nan
    r['u12_ratio'] = r['n_nd'] / max(r['n_final'], 1)
    r['u12_osid_null'] = int(fin['origem_solution_id'].isna().all())
    # U7 — invariante de timing
    t = tim
    soma = t['tempo_fit_s'].values + t['tempo_busca_s'].values
    r['u7_viol'] = int((soma > t['tempo_geracao_s'].values * (1 + 1e-9) + 1e-9).sum())
    r['u7_igual'] = int((np.abs(soma - t['tempo_geracao_s'].values) <= 1e-12).sum())
    r['u7_sonda_linhas'] = int((t['tempo_pred_sonda_s'].fillna(0) > 0).sum())
    rows.append(r)
    print('%-28s ok' % label)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 't02_universal.csv'), index=False)
n = len(df)
print('\n=== RESUMO (%d células) ===' % n)
for c in ['u1_fe', 'u1_init', 'u1_fe_index', 'u1_N_esperado', 'u2_dx', 'u2_df', 'u2_hash',
          'u2_doe', 'u3_timing_linhas', 'u3_ger_51i', 'u4_2blocos', 'u4_20000', 'u4_linhas',
          'u4_ger_null', 'u8_fetreino', 'u9_cache', 'u10_nger', 'u10_denso', 'u10_ledger',
          'u10_fases', 'u11_pop_vazia', 'f1_bitid', 'f1_1000', 'f3_monot', 'f3_passo',
          'f3_ngps_folhas', 'f3_teto', 'u12_nd', 'u12_osid_null']:
    print('  %-18s %d/%d' % (c, int(df[c].sum()), n))
print('  u11_rsid nao-nulos     %d de %d linhas ③' % (df.u11_rsid.sum(), df.n_sur.sum()))
print('  u5 max|ΔX|             %.3e' % df.u5_dx.max())
print('  u7 violações           %d de %d linhas ④' % (df.u7_viol.sum(), df.I_eff.sum()))
print('  u7 igualdade exata     %d de %d' % (df.u7_igual.sum(), df.I_eff.sum()))
print('  u7 linhas c/ sonda     %d (esperado 1/célula)' % df.u7_sonda_linhas.sum())
print('  u12 link Δmax          %.3e' % df.u12_link.max())
print('  u12 razão fantasia     mediana %.3f (min %.3f max %.3f)'
      % (df.u12_ratio.median(), df.u12_ratio.min(), df.u12_ratio.max()))
print('  tempo_aval_real_s      valores: %s' % sorted(df.u1_tempo_aval.unique()))
print('  guards                 %s' % df[df.n_guard > 0][['label', 'guards', 'n_guard']].to_dict('records'))
print('  células sem footer     %s' % df[df.n_footer == 0].label.tolist())
print('  n_footer distribuição  %s' % df.n_footer.value_counts().to_dict())
print('  Σ gerações             %d' % df.n_ger.sum())
print('  Σ linhas ③             %d' % df.n_sur.sum())
print('  Σ decisões             %d' % df.I_eff.sum())
for t_ in ['small', 'medium', 'big']:
    s = df[df.tier == t_]
    print('  [%s] n=%d  I_eff/I_max mediana %.3f  cobertura_final mediana %.3f  '
          'σ-NaN sonda mediana %.3f  cob_completa %d'
          % (t_, len(s), (s.I_eff / s.I_max).median(), s.cobertura_final.median(),
             s.f2_nan_sonda.median(), s.cob_completa.sum()))
print('  σ-NaN ger 1-50 == 1.0 em %d/%d' % (int((df.f2_nan_1_50 == 1.0).sum()), n))
print('  pop_max por M: %s' % df.groupby('M').pop_max.max().to_dict())
