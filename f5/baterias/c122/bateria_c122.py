#!/usr/bin/env python
"""BATERIA DE FIDELIDADE — c122 (theta-DEA-DP) — F5.3b, protocolo v1.1.

Executa TODAS as queries dos aspectos U1-U12 + modulo de familia
(classificador par-a-par) + especificos do bundle nas 25 celulas main/42.
Saidas: c122_aspectos.csv (1 linha/celula, ~90 colunas) + c122_*.pkl.

READ-ONLY sobre dados/artefatos. Unico local de escrita: esta pasta.
"""
import json, os, sys, math, pickle
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122'
DOE  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SND  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c122'
EPS32 = np.finfo(np.float32).eps

PROBS = sorted(os.listdir(RAIZ))
PROBS = [p for p in PROBS if not p.startswith('.')]


def ceil_tol(v, nd=9):
    return math.ceil(round(v, nd))


def cell(prob):
    b = f'{RAIZ}/{prob}/42/exp_main_c122_{prob}_42'
    r = {'problema': prob}
    mf = json.load(open(b + '.manifest.json'))
    recs = [json.loads(l) for l in open(b + '.jsonl')]
    hdr = [x for x in recs if x['rec'] == 'header'][0]
    dec = pd.DataFrame([x for x in recs if x['rec'] == 'decision'])
    snd = pd.DataFrame([x for x in recs if x['rec'] == 'sonda'])
    gds = pd.DataFrame([x for x in recs if x['rec'] == 'guard'])
    fts = [x for x in recs if x['rec'] == 'footer']
    fit0 = [x for x in recs if x['rec'] == 'fit_inicial'][0]

    D, M, N = hdr['D'], hdr['M'], mf['params']['N_MU']
    r.update(D=D, M=M, N=N, maxfe=mf['maxfe'], fe_final=mf['fe_final'],
             n_ger=mf['n_geracoes'], status=mf['status'],
             motivo_parada=mf.get('motivo_parada'), cache_hits=mf['cache_hits'],
             n_init=hdr['n_init'], wall_s=mf['timing']['tempo_total_s'],
             maq_env=mf['env']['executable'].split('/')[2] if '/' in mf['env']['executable'] else '')

    # ---------- U1 orcamento / fe_index ----------
    real = pd.read_parquet(b + '__real.parquet',
                           columns=['solution_id', 'fe_index', 'fase'] +
                                   [f'x{i}' for i in range(D)] +
                                   [f'f{j}' for j in range(M)])
    r['A1_maxfe_31D_1'] = (mf['maxfe'] == 31 * D - 1)
    r['A1_fe_final_eq'] = (mf['fe_final'] == mf['maxfe'])
    r['A1_n_real'] = len(real)
    r['A1_fe_index_denso'] = bool((real.fe_index.values == np.arange(len(real))).all())
    r['A1_sid_denso'] = bool((real.solution_id.values == np.arange(len(real))).all())

    # ---------- U2 init / DoE ----------
    ini = real[real.fase == 'init']
    r['A2_init_11D_1'] = (len(ini) == 11 * D - 1)
    dh = json.load(open(f'{DOE}/{prob}/doe_{prob}_42.manifest.json'))
    hsc = dh.get('hash') or dh.get('doe_hash') or dh.get('sha256')
    r['A2_doe_hash_bate'] = (hsc == mf['doe_hash'])
    dx = pd.read_parquet(f'{DOE}/{prob}/doe_{prob}_42.parquet')
    Xd = dx[[c for c in dx.columns if c.startswith('x')]].to_numpy(np.float64)
    Xi = ini[[f'x{i}' for i in range(D)]].to_numpy(np.float64)
    r['A2_dX_init'] = float(np.abs(Xd[:len(Xi)] - Xi).max()) if Xd.shape == Xi.shape else np.nan
    r['A2_fases'] = '|'.join(sorted(real.fase.unique()))

    # ---------- camada 3 ----------
    sg = pd.read_parquet(b + '__surrogate.parquet',
                         columns=['regime', 'geracao', 'real_solution_id', 'mu_0',
                                  'sigma_0', 'pred_tipo', 'pred_classe', 'pred_score',
                                  'pred_confianca', 'modelo_flag', 'espaco_modelo',
                                  'transf_tipo', 'fe_treino_max'])
    on = sg[sg.regime == 'online']
    so = sg[sg.regime == 'sonda']
    r['A6_mu_sigma_null'] = bool(sg.mu_0.isna().all() and sg.sigma_0.isna().all())
    r['A6_pred_classe_null'] = bool(sg.pred_classe.isna().all())
    r['A6_pred_tipo'] = '|'.join(sorted(sg.pred_tipo.dropna().unique()))
    r['A6_modelo_flag'] = '|'.join(sorted(sg.modelo_flag.dropna().unique()))
    r['A6_espaco_transf_null'] = bool(sg.espaco_modelo.isna().all() and sg.transf_tipo.isna().all())

    # 1 FE / iteracao + escolhido unico
    ch = on[on.real_solution_id.notna()]
    r['A10_um_rsid_por_ger'] = bool((on.groupby('geracao').real_solution_id.count() == 1).all())
    r['A10_n_escolhidos'] = len(ch)
    r['A10_rsid_unicos'] = int(ch.real_solution_id.nunique())
    r['A10_iter_eq_fe'] = (mf['n_geracoes'] == mf['maxfe'] - (11 * D - 1) - mf['cache_hits'])
    r['A10_sonda_sem_rsid'] = bool(so.real_solution_id.isna().all())

    # TOP-100 = min(100, n_cands)
    cnt = on.groupby('geracao').size()
    ncd = dec.set_index('geracao').n_cands
    esperado = ncd.clip(upper=100)
    r['A10_top100_exato'] = bool((cnt.reindex(esperado.index).fillna(0).astype(int).values == esperado.values).all())
    r['A10_n_dec'] = int(len(dec))
    r['A10_dec_eq_nger'] = (len(dec) == mf['n_geracoes'])
    r['A10_ncands0'] = int((dec.n_cands == 0).sum())
    r['A10_gens_sem_rsid'] = int(mf['n_geracoes'] - len(ch))
    r['A10_linhas_busca'] = int(len(on))
    r['A10_max_linhas_ger'] = int(cnt.max())

    # ---------- U8 fe_treino_max ----------
    ftm = on.groupby('geracao').fe_treino_max.max()
    d = ftm.diff().dropna()
    r['A8_ftm_monotonico'] = bool((d >= 0).all())
    r['A8_ftm_quedas'] = int((d < 0).sum())
    gsx = ftm.index.to_numpy()
    r['A8_ftm_eq_arch_menos1'] = bool((ftm.values == (11 * D - 1) + gsx - 2 + 1).all()) if False else bool(
        (ftm.values == np.array([(11 * D - 1) + g - 2 for g in gsx])).all())
    r['A8_ftm_min'] = int(ftm.min()); r['A8_ftm_max'] = int(ftm.max())

    # ---------- U4/U5 sonda ----------
    ng = mf['n_geracoes']
    esperados = [g for g in range(1, ng + 1) if g == 1 or g % 2 == 0]
    if ng % 2 == 1:
        esperados.append(ng)
    gs = sorted(so.geracao.unique().tolist())
    r['A4_cadencia_ok'] = (gs == sorted(esperados))
    r['A4_n_blocos'] = len(gs)
    r['A4_n_blocos_manifesto'] = mf['sonda']['n_blocos']
    r['A4_blocos_2000'] = bool((so.groupby('geracao').size() == 2000).all())
    r['A4_finalprobe'] = (ng % 2 == 1)
    r['A4_ultima_coberta'] = (ng in gs)
    # join posicional com o gabarito
    sx = pd.read_parquet(f'{SND}/sonda_{prob}.parquet')
    colx = [c for c in sx.columns if c.startswith('x')][:D]
    Xg = sx[colx].to_numpy(np.float64)
    sg1 = pd.read_parquet(b + '__surrogate.parquet',
                          columns=['regime', 'geracao'] + [f'x{i}' for i in range(D)])
    b1 = sg1[(sg1.regime == 'sonda') & (sg1.geracao == gs[0])][[f'x{i}' for i in range(D)]].to_numpy(np.float64)
    bl = sg1[(sg1.regime == 'sonda') & (sg1.geracao == gs[-1])][[f'x{i}' for i in range(D)]].to_numpy(np.float64)
    r['A5_dX_sonda_1'] = float(np.abs(Xg[:2000] - b1).max())
    r['A5_dX_sonda_last'] = float(np.abs(Xg[:2000] - bl).max())
    del sg1

    # ---------- U7 timing ----------
    tm = pd.read_parquet(b + '__timing.parquet')
    r['A7_n_timing'] = len(tm)
    r['A7_timing_eq_nger'] = (len(tm) == ng)
    inv = (tm.tempo_fit_s + tm.tempo_busca_s) <= tm.tempo_geracao_s + 1e-6
    r['A7_inv1_frac'] = float(inv.mean())
    tem_sonda = tm.geracao.isin(gs)
    r['A7_sonda_pos_frac'] = float(((tm.tempo_pred_sonda_s > 0) == tem_sonda).mean())
    r['A7_fitseries_eq'] = (len(mf['fit_series']) == ng)
    r['A7_n_acum_eq'] = bool((tm.n_acumulado.values == (11 * D - 1) + 1 + np.arange(ng)).all())

    # ---------- camada 2 (pop) ----------
    pop = pd.read_parquet(b + '__pop.parquet')
    tam = pop.groupby('geracao').size()
    r['A_pop_N_todas'] = bool((tam == N).all())
    r['A_pop_ngrupos'] = int(pop.geracao.nunique())
    r['A_pop_ids_no_real'] = bool(pop.solution_id.isin(real.solution_id).all())
    # o escolhido da geracao g entra na pop de g+1?
    ch_ord = ch.sort_values('geracao')
    mapa = dict(zip(ch_ord.geracao.astype(int), ch_ord.real_solution_id.astype(int)))
    entra = []
    pg = {g: set(v.solution_id) for g, v in pop.groupby('geracao')}
    for g in range(1, ng):
        if g in mapa and (g + 1) in pg:
            entra.append(mapa[g] in pg[g + 1])
    r['A_pop_escolhido_entra_frac'] = float(np.mean(entra)) if entra else np.nan

    # ---------- FAMILIA: identidade e(z) argmax ----------
    dch = dec.set_index('geracao')
    j = ch.set_index('geracao')
    ez = dch.e_z_escolhido.reindex(j.index)
    sm = dch.softmax_escolhido.reindex(j.index)
    ok_ez = np.isclose(j.pred_score.values.astype(float), ez.values.astype(float),
                       rtol=1e-5, atol=1e-4, equal_nan=True)
    ok_sm = np.isclose(j.pred_confianca.values.astype(float), sm.values.astype(float),
                       rtol=1e-5, atol=1e-6, equal_nan=True)
    r['A12_ez_id_frac'] = float(ok_ez.mean())
    r['A12_ez_id_maxdelta'] = float(np.nanmax(np.abs(j.pred_score.values.astype(float) -
                                                     ez.values.astype(float))))
    r['A12_sm_id_frac'] = float(ok_sm.mean())
    mx = on.groupby('geracao').pred_score.max()
    eq = np.isclose(j.pred_score.values.astype(float), mx.reindex(j.index).values.astype(float),
                    equal_nan=True)
    r['A12_argmax_frac'] = float(eq.mean())
    r['A12_ez_null_ncands1'] = int(((dec.n_cands == 1) & dec.e_z_escolhido.isna()).sum())
    r['A12_ez_null_total'] = int(dec.e_z_escolhido.isna().sum())
    r['A12_ncands1'] = int((dec.n_cands == 1).sum())

    # ---------- confianca por regime ----------
    r['A13_conf_sonda_media'] = float(so.pred_confianca.mean())
    r['A13_conf_sonda_frac1'] = float((so.pred_confianca >= 1 - 1e-6).mean())
    r['A13_conf_busca_min'] = float(on.pred_confianca.min())
    r['A13_conf_busca_med'] = float(on.pred_confianca.median())
    r['A13_conf_busca_frac1'] = float((on.pred_confianca >= 1 - 1e-6).mean())

    # ---------- regra das categorias (III-D-1) ----------
    def cat_rec(x):
        if x['caminho'].endswith('distinct'):
            return 'None'
        for k, nm in ((('n_q1'), 'Q1'), (('n_q2'), 'Q2'), (('n_q3'), 'Q3')):
            if x[k] > 0:
                return nm
        return 'None'
    dec['cat_rec'] = dec.apply(cat_rec, axis=1)
    dec['cat_log'] = dec.motivo.str.extract(r'categoria=(\w+)')[0]
    r['A15_prioridade_frac'] = float((dec.cat_rec == dec.cat_log).mean())
    vc = dec.cat_log.value_counts()
    for k in ['Q1', 'Q2', 'Q3', 'None']:
        r['A15_n_' + k] = int(vc.get(k, 0))
    # Qmax
    def qsel(x):
        return {'Q1': x['n_q1'], 'Q2': x['n_q2'], 'Q3': x['n_q3'], 'None': x['n_q1']}[x['cat_log']]
    dec['qsel'] = dec.apply(qsel, axis=1)
    r['A16_qmax_frac'] = float((dec.n_cands == dec.qsel.clip(upper=300)).mean())
    r['A16_n_estourou300'] = int((dec.qsel > 300).sum())
    r['A16_max_ncands'] = int(dec.n_cands.max())
    # pool N*
    catp = dec[dec.caminho.str.endswith('categorias')]
    pool = (catp.n_acordo + catp.n_desacordo)
    r['A18_pool7000_frac'] = float((pool == 7000).mean()) if len(catp) else np.nan
    r['A18_acordo_med'] = float(catp.n_acordo.median()) if len(catp) else np.nan
    r['A18_desacordo_med'] = float(catp.n_desacordo.median()) if len(catp) else np.nan
    dis = dec[dec.caminho.str.endswith('distinct')]
    r['A17_distinct_n'] = int(len(dis))
    r['A17_distinct_pool_null'] = float(dis.n_acordo.isna().mean()) if len(dis) else np.nan
    r['A17_distinct_scf_null'] = float(dis.pool_scf_min.isna().mean()) if len(dis) else np.nan
    r['A17_cat_None_eq_distinct'] = bool((dec.cat_log == 'None').sum() == len(dis))

    # ---------- gate warm-start + E_upd ----------
    for net, tag in (('p', 'P'), ('s', 'S')):
        acc = dec['accs_' + net].apply(lambda a: min(a) if isinstance(a, list) else np.nan)
        sk = dec['skip_treino_' + net].astype(bool)
        ep = dec['epocas_' + net].fillna(-1)
        semmod = acc.isna()
        r[f'A19_{tag}_sem_modelo'] = int(semmod.sum())
        r[f'A19_{tag}_gate_frac'] = float(((acc[~semmod] >= 0.9) == sk[~semmod]).mean()) if (~semmod).any() else np.nan
        sub = (~sk) & (~semmod)
        if sub.sum():
            pred = np.array([math.ceil(20 * ((0.9 - a) / 0.9)) for a in acc[sub]])
            r[f'A19_{tag}_Eupd_frac'] = float((pred == ep[sub].values).mean())
            r[f'A19_{tag}_Eupd_n'] = int(sub.sum())
            r[f'A19_{tag}_Eupd_med'] = float(ep[sub].median())
        else:
            r[f'A19_{tag}_Eupd_frac'] = np.nan
            r[f'A19_{tag}_Eupd_n'] = 0
            r[f'A19_{tag}_Eupd_med'] = np.nan
        r[f"A19_{tag}_skip_frac"] = float(sk.mean())
        r[f"A19_{tag}_epocas_pos"] = int((ep > 0).sum())
        r[f'A19_{tag}_epocas_zero_quando_skip'] = bool((ep[sk] == 0).all())
        # sentinela acc=1 por classe ausente
        r[f'A21_{tag}_frac_acc_com_1'] = float(dec['accs_' + net].apply(
            lambda a: any(x == 1.0 for x in a) if isinstance(a, list) else False).mean())
        r[f'A21_{tag}_frac_todas_1'] = float(dec['accs_' + net].apply(
            lambda a: all(x == 1.0 for x in a) if isinstance(a, list) else False).mean())
    r['A20_Tmax'] = mf['params']['T_max']
    r['A20_Tmax_formula'] = (mf['params']['T_max'] == 11 * D + 24)
    r['A20_reinit_p'] = int(dec.reinit_p.sum())
    r['A20_reinit_s'] = int(dec.reinit_s.sum())
    r['A20_fit0_pnet'] = bool(fit0['p_net'])
    r['A20_fit0_snet'] = bool(fit0['s_net'])
    r['A20_fit0_ntreino'] = int(fit0['n_treino'])
    r['A20_fit0_epocas'] = int(fit0['epocas'])

    # ---------- f_min/f_max ----------
    r['A22_fmin'] = str(mf['params']['f_min'])
    r['A22_fmax'] = str(mf['params']['f_max'])
    r['A22_const_no_log'] = bool(dec.f_min.astype(str).nunique() == 1 and
                                 dec.f_max.astype(str).nunique() == 1)
    r['A22_eq_manifesto'] = bool(str(dec.f_min.iloc[0]) == str(mf['params']['f_min']) and
                                 str(dec.f_max.iloc[0]) == str(mf['params']['f_max']))
    r['A23_xnorm'] = mf['params']['x_norm']
    r['A25_visualization'] = mf['params']['visualization']
    r['A28_dtype_params'] = mf['params']['torch_default_dtype'][:7]
    r['A28_dtype_pinning'] = mf['env']['pinning']['default_dtype']
    r['A33_sbx'] = f"proC={mf['params']['sbx']['proC']},disC={mf['params']['sbx']['disC']}"
    r['A33_pm'] = (f"proM={mf['params']['pm']['proM']},indpb={mf['params']['pm']['indpb']:.6f},"
                   f"disM={mf['params']['pm']['disM']}")
    r['A33_indpb_1_n'] = bool(abs(mf['params']['pm']['indpb'] - 1.0 / D) < 1e-12)
    r['A34_fnn'] = mf['params']['fnn']
    r['A34_adam'] = str(mf['params']['adam'])
    r['A34_Einit'] = mf['params']['E_init']
    r['A34_gamma'] = mf['params']['gamma_acc_thr']
    r['A34_Qmax'] = mf['params']['Q_max']
    r['A34_theta'] = mf['params']['theta_PBI']
    r['A34_pool'] = mf['params']['lambda_pool']
    r['A32_N_tabela2'] = (N == (11 if M == 2 else 15))

    # ---------- U9 guards / footer ----------
    ft = fts[0]
    r['A9_n_guards'] = int(len(gds))
    tipos = gds.name.value_counts().to_dict() if len(gds) else {}
    r['A9_tipos_guard'] = '|'.join(f'{k}:{v}' for k, v in sorted(tipos.items()))
    r['A9_spin_total_footer'] = int(ft.get('n_spin_total', 0))
    r['A9_spin_guards'] = int(tipos.get('spin_resample', 0))
    r['A9_spin_bate'] = (int(ft.get('n_spin_total', 0)) == int(dec.n_spin.sum()) ==
                         int(tipos.get('spin_resample', 0)))
    r['A9_cache_footer'] = int(ft.get('cache_hits', 0))
    r['A9_cache_manifesto'] = int(mf['cache_hits'])
    r['A9_n_cache_infill'] = int(ft.get('n_cache_infill', 0))
    r['A9_skip_p_footer'] = int(ft['n_skip_treino']['p'])
    r['A9_skip_s_footer'] = int(ft['n_skip_treino']['s'])
    r['A9_skip_bate'] = (int(ft['n_skip_treino']['p']) == int(dec.skip_treino_p.sum()) and
                         int(ft['n_skip_treino']['s']) == int(dec.skip_treino_s.sum()))
    r['A9_footer_status'] = ft['status']
    r['A9_footer_motivo'] = ft.get('motivo_parada')
    r['A9_footer_cp_init'] = ft.get('cp_init')
    r['A9_n_footer'] = len(fts)
    r['A30_spin_cap_disparos'] = int(tipos.get('spin_cap', 0))
    r['A30_teto_wall_disparos'] = int(tipos.get('teto_wall', 0))
    r['A30_cache_travado'] = int(tipos.get('cache_hit_travado', 0))
    r['A30_max_tentativa'] = int(gds.tentativa.max()) if len(gds) and 'tentativa' in gds else 0

    # ---------- A24 round-robin PerCounter (decisao + spins) ----------
    seq = []
    if len(gds):
        gmap = {}
        for _, x in gds[gds.name == 'spin_resample'].iterrows():
            gmap.setdefault(int(x['geracao']), []).append((int(x['tentativa']), int(x['cid'])))
    else:
        gmap = {}
    capg = set()
    if len(gds) and 'name' in gds:
        capg = set(gds[gds.name == 'spin_cap'].geracao.astype(int))
    for _, x in dec.sort_values('geracao').iterrows():
        g = int(x['geracao'])
        for _, c in sorted(gmap.get(g, [])):
            seq.append(c)
        # no cap anti-spin o fallback NAO chama counter(): o cid da decisao e o
        # mesmo do ultimo spin — nao conta 2x na roda
        if g not in capg:
            seq.append(int(x['cid']))
    nb = len(seq) // N
    blocos = [seq[i * N:(i + 1) * N] for i in range(nb)]
    r['A24_seq_len'] = len(seq)
    r['A24_rodadas_completas'] = int(sum(len(set(bl)) == N for bl in blocos))
    r['A24_rodadas_total'] = nb
    r['A24_perm_frac'] = float(np.mean([len(set(bl)) == N for bl in blocos])) if nb else np.nan
    r['A24_1a_rodada_natural'] = (blocos[0] == list(range(N))) if nb else False
    r['A24_cids_unicos'] = int(len(set(seq)))
    r['A24_resto'] = len(seq) % N

    # ---------- A27 sonda g=1 (P nao truncada) ----------
    s1 = so[so.geracao == gs[0]]
    r['A27_ez_max_g1'] = float(s1.pred_score.max())
    r['A27_ez_max_g1_gt_2N'] = bool(s1.pred_score.max() > 2 * N)
    r['A27_frac_g1_gt_2N'] = float((s1.pred_score > 2 * N).mean())
    outros = so[so.geracao != gs[0]]
    r['A27_ez_max_g2plus'] = float(outros.pred_score.max()) if len(outros) else np.nan
    r['A27_ez_max_g2plus_le_2N'] = bool(outros.pred_score.max() <= 2 * N + 1e-6) if len(outros) else True
    r['A27_ez_max_g1_le_2ninit'] = bool(s1.pred_score.max() <= 2 * (11 * D - 1))

    # ---------- SAUDE: sonda (analise propria) ----------
    blk = so.groupby('geracao').pred_score.agg(
        mx='max', mean='mean', fz=lambda x: float((x > 0).mean()))
    r['H_sonda_frac_pos_b1'] = float(blk.fz.iloc[0])
    r['H_sonda_frac_pos_b2'] = float(blk.fz.iloc[1]) if len(blk) > 1 else np.nan
    r['H_sonda_frac_pos_ult'] = float(blk.fz.iloc[-1])
    r['H_sonda_blocos_zerados'] = int((blk.fz == 0).sum())
    r['H_sonda_n_blocos'] = int(len(blk))
    prim = blk.fz.iloc[1:].to_numpy()
    r['H_sonda_ger_1o_zero'] = int(blk.index[1:][prim == 0][0]) if (prim == 0).any() else -1
    r['H_sonda_frac_blocos_zerados_pos_b1'] = float((prim == 0).mean()) if len(prim) else np.nan

    # ---------- U11 fantasia: e(z) do escolhido x resultado real ----------
    fj = real.set_index('solution_id')[[f'f{j}' for j in range(M)]]
    ch2 = ch.copy()
    ch2['rsid'] = ch2.real_solution_id.astype(int)
    F = fj.loc[ch2.rsid].to_numpy(np.float64)
    # o escolhido domina/e dominado pela populacao do momento? usamos o arquivo ate o momento
    Fall = fj.to_numpy(np.float64)
    ndom = np.zeros(len(ch2))
    for i, sid in enumerate(ch2.rsid.values):
        A = Fall[:sid]                      # arquivo ANTES da avaliacao
        f = Fall[sid]
        le = (f <= A).all(axis=1)
        lt = (f < A).any(axis=1)
        ndom[i] = float((le & lt).sum())
    ez_v = ch2.pred_score.to_numpy(np.float64)
    ok = ~np.isnan(ez_v)
    r['U11_rho_ez_ndom'] = float(pd.Series(ez_v[ok]).corr(pd.Series(ndom[ok]), method='spearman'))
    r['U11_ndom_med'] = float(np.median(ndom))
    r['U11_frac_infill_domina'] = float((ndom > 0).mean())
    r['U11_frac_infill_ndom0'] = float((ndom == 0).mean())

    pk = {'dec': dec, 'blk': blk, 'ndom': ndom, 'ez': ez_v, 'seq': seq, 'tm': tm}
    return r, pk


def main():
    linhas, packs = [], {}
    for p in PROBS:
        try:
            r, pk = cell(p)
            linhas.append(r)
            packs[p] = pk
            print('OK', p, r['D'], r['M'], r['n_ger'], flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            print('ERR', p, e, flush=True)
    df = pd.DataFrame(linhas)
    df.to_csv(f'{OUT}/c122_aspectos.csv', index=False)
    with open(f'{OUT}/c122_packs.pkl', 'wb') as f:
        pickle.dump(packs, f)
    print(df.shape)


if __name__ == '__main__':
    main()
