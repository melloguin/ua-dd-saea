#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103.py — F5.3b · RELATORIO DE FIDELIDADE do config e103 (IBEA-MS, offline MATLAB).
Executa a bateria U1-U12 + modulo de familia (offline) + aspectos especificos do bundle
nas 45 celulas da semente 42 (25 off + 20 sweep).  READ-ONLY sobre dados/artefatos.
Saidas (unico local de escrita permitido): f5/baterias/e103/*.csv
"""
import os, sys, json, math, glob, hashlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, REPO)

EPS32 = np.finfo(np.float32).eps


def cells():
    """(label, exp, problema, dir) das 45 celulas."""
    out = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, '42')
        if not os.path.isdir(d):
            continue
        mf = glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json'))
        mf = [f for f in mf if '__final' not in f]
        assert len(mf) == 1, (lab, mf)
        base = os.path.basename(mf[0])[:-len('.manifest.json')]
        exp = base.split('_e103_')[0][len('exp_'):]
        prob = base.split('_e103_')[1][:-len('_42')]
        out.append((lab, exp, prob, d, base))
    return out


def read_jsonl(path):
    recs, orfas = [], 0
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            orfas += 1
    return recs, orfas


def nd_mask(F):
    """mascara de nao-dominancia (minimizacao), semantica de metrics.nondominated_front."""
    n = len(F)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        d = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if d.any():
            keep[i] = False
    return keep


def uma(lab, exp, prob, d, base):
    r = {'label': lab, 'exp': exp, 'problema': prob}
    man = json.load(open(os.path.join(d, base + '.manifest.json')))
    recs, orfas = read_jsonl(os.path.join(d, base + '.jsonl'))
    by = {}
    for x in recs:
        by.setdefault(x.get('rec'), []).append(x)
    hdr = by['header'][0]
    setup = by['e103_setup'][0]
    gens = sorted(by.get('e103_gen', []), key=lambda x: x['geracao'])
    foot = by['footer'][0] if 'footer' in by else None
    son_ev = by.get('sonda', [])

    D, M = hdr['D'], hdr['M']
    n_ds = hdr['n_dataset']
    r.update(D=D, M=M, n_dataset=n_ds, n_recs=len(recs), n_orfas=orfas,
             tier=man['dataset']['tier'], dist=man['dataset']['dist'],
             status=man['status'], termino=(foot or {}).get('termino'),
             n_geracoes=man['n_geracoes'], maxfe=man['maxfe'], fe_final=man['fe_final'],
             algo_version=man.get('algo_version'), matlab=man['env'].get('matlab'))

    # ---------- camadas ----------
    real = pq.read_table(os.path.join(d, base + '__real.parquet')).to_pandas()
    popl = pq.read_table(os.path.join(d, base + '__pop.parquet')).to_pandas()
    sur = pq.read_table(os.path.join(d, base + '__surrogate.parquet')).to_pandas()
    tim = pq.read_table(os.path.join(d, base + '__timing.parquet')).to_pandas()
    fin = pq.read_table(os.path.join(d, base + '__final.parquet')).to_pandas()
    xc = ['x%d' % i for i in range(D)]
    fc = ['f%d' % i for i in range(M)]
    muc = ['mu_%d' % i for i in range(M)]
    sgc = ['sigma_%d' % i for i in range(M)]

    # ---------- U1 · FE / dataset / fase init ----------
    r['U1_n_real'] = len(real)
    r['U1_fe_ok'] = (man['fe_final'] == man['maxfe'] == n_ds == len(real))
    r['U1_tier_ok'] = (n_ds == 31 * D - 1) if man['dataset']['tier'] == 'small' else (n_ds == 2000)
    r['U1_fase_init_pct'] = float((real['fase'] == 'init').mean())
    r['U1_feidx_denso'] = bool(np.array_equal(np.sort(real['fe_index'].values), np.arange(n_ds)))
    r['U1_solid_denso'] = bool(np.array_equal(np.sort(real['solution_id'].values), np.arange(n_ds)))
    r['U1_dup_x'] = int(len(real) - len(real[xc].drop_duplicates()))

    # ---------- U2 · proveniencia (hash) ----------
    ds = man['dataset']
    r['U2_hash_hdr_eq_man'] = (hdr['x_hash'] == ds['x_hash'] and hdr['f_hash'] == ds['f_hash']
                               and hdr['dataset_hash'] == ds['dataset_hash'])
    r['U2_cp'] = bool(ds.get('cp_x')) and bool(ds.get('cp_f'))
    r['U2_doe_hash_eq_x'] = (man.get('doe_hash') == ds['x_hash'])
    # binding real vs artefato
    dsp = os.path.join(REPO, ds['path'])
    r['U2_artefato_existe'] = os.path.exists(dsp)
    if r['U2_artefato_existe']:
        art = pq.read_table(dsp).to_pandas()
        axc = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
        afc = [c for c in art.columns if c.startswith('f') and c[1:].isdigit()]
        A = art[sorted(axc, key=lambda s: int(s[1:]))].values.astype(np.float32)
        B = real[xc].values.astype(np.float32)
        r['U2_dX_max'] = float(np.abs(A - B).max()) if A.shape == B.shape else -1.0
        AF = art[sorted(afc, key=lambda s: int(s[1:]))].values.astype(np.float32)
        BF = real[fc].values.astype(np.float32)
        r['U2_dF_max'] = float(np.abs(AF - BF).max()) if AF.shape == BF.shape else -1.0

    # ---------- U3 / A_treino_unico · 1 fit total (offline, nunca retreina) ----------
    r['U3_tim_linhas'] = len(tim)
    r['U3_tim_ger0'] = bool((tim['geracao'] == 0).all())
    r['U3_tim_nacum'] = int(tim['n_acumulado'].iloc[0])
    r['U3_fit_series'] = len(man.get('fit_series', []))
    r['U3_tempo_ger_nan'] = bool(tim['tempo_geracao_s'].isna().all())

    # ---------- U4/U5 · sonda: 2 blocos POR MODELO ----------
    son = sur[sur['regime'] == 'sonda']
    r['U4_sonda_eventos'] = len(son_ev)
    r['U4_sonda_npontos'] = [e.get('n_pontos') for e in son_ev]
    r['U4_sonda_modelos'] = [e.get('modelo') for e in son_ev]
    r['U4_sonda_ok'] = all(bool(e.get('ok')) for e in son_ev)
    r['U4_sonda_ger_null'] = all(e.get('geracao') is None for e in son_ev)
    r['U4_sonda_linhas'] = len(son)
    g = son.groupby('modelo_flag').size().to_dict()
    r['U4_sonda_K'] = g.get('Kriging-DACE', 0)
    r['U4_sonda_R'] = g.get('RBFN', 0)
    # join posicional com o gabarito
    sp = os.path.join(REPO, 'data', 'sonda', 'sonda_%s.parquet' % prob)
    r['U5_gabarito'] = os.path.exists(sp)
    if r['U5_gabarito']:
        gab = pq.read_table(sp).to_pandas()
        gxc = sorted([c for c in gab.columns if c.startswith('x') and c[1:].isdigit()],
                     key=lambda s: int(s[1:]))
        gfc = sorted([c for c in gab.columns if c.startswith('f') and c[1:].isdigit()],
                     key=lambda s: int(s[1:]))
        G = gab[gxc].values.astype(np.float32)
        dmax = []
        for mflag in ['Kriging-DACE', 'RBFN']:
            S = son[son['modelo_flag'] == mflag][xc].values.astype(np.float32)
            dmax.append(float(np.abs(S - G[:len(S)]).max()) if S.shape == G.shape else -1.0)
        r['U5_dX_sonda_K'] = dmax[0]
        r['U5_dX_sonda_R'] = dmax[1]
        # X dos 2 blocos identico entre si (mesmo artefato)
        SK = son[son['modelo_flag'] == 'Kriging-DACE'][xc].values
        SR = son[son['modelo_flag'] == 'RBFN'][xc].values
        r['U5_blocos_X_identicos'] = bool(SK.shape == SR.shape and np.array_equal(SK, SR))
        # mu difere entre modelos (nao e repeticao)
        MK = son[son['modelo_flag'] == 'Kriging-DACE'][muc].values
        MR = son[son['modelo_flag'] == 'RBFN'][muc].values
        r['U5_blocos_mu_identicos'] = bool(np.array_equal(MK, MR))
        r['U5_blocos_dmu_med'] = float(np.nanmedian(np.abs(MK - MR)))
        # hash do gabarito
        r['U5_hash_sonda_ok'] = (man['sonda']['x_hash'] == son_ev[0].get('x_hash'))

    # ---------- U6 · sigma por modelo (RBFN NULL por desenho) ----------
    K = sur[sur['modelo_flag'] == 'Kriging-DACE']
    Rb = sur[sur['modelo_flag'] == 'RBFN']
    r['U6_sigmaK_null_pct'] = float(K[sgc].isna().values.mean())
    r['U6_sigmaR_null_pct'] = float(Rb[sgc].isna().values.mean())
    r['U6_sigmaK_neg'] = int((K[sgc].values < 0).sum())
    r['U6_sigmaK_med'] = float(np.nanmedian(K[sgc].values))
    r['U6_sigmaK_max'] = float(np.nanmax(K[sgc].values))

    # ---------- U7 · tempo ----------
    t = man['timing']
    r['U7_t_total'] = t['tempo_total_s']
    r['U7_t_fit'] = t['tempo_fit_surrogate_s']
    r['U7_t_busca'] = t['tempo_busca_s']
    r['U7_t_real'] = t['tempo_aval_real_s']
    r['U7_t_sonda'] = t['tempo_pred_sonda_s']
    r['U7_soma_le_total'] = ((t['tempo_fit_surrogate_s'] + t['tempo_busca_s'] +
                              t['tempo_pred_sonda_s']) <= t['tempo_total_s'] * 1.001)
    r['U7_fit_kriging'] = setup.get('tempo_fit_kriging_s')
    r['U7_fit_rbfn'] = setup.get('tempo_fit_rbfn_s')

    # ---------- U8 · fe_treino_max ----------
    u = sorted(sur['fe_treino_max'].dropna().unique().tolist())
    r['U8_fe_treino_uniq'] = u
    r['U8_fe_treino_ok'] = (u == [n_ds - 1])
    gu = sorted(set(x['fe_treino_max'] for x in gens))
    r['U8_fe_treino_gen_ok'] = (gu == [n_ds - 1])

    # ---------- U9 · guards / contadores ----------
    r['U9_guards'] = len(by.get('guard', []))
    r['U9_mse_neg_total'] = int(sum(x.get('n_mse_neg', 0) for x in gens))
    r['U9_cache_hits'] = man.get('cache_hits')
    r['U9_fallback'] = man.get('fallback_ativado')
    r['U9_warn_setup'] = setup.get('warn_setup', '')
    r['U9_recs_tipos'] = json.dumps({k: len(v) for k, v in sorted(by.items())})

    # ---------- U10 · aritmetica entre camadas ----------
    r['U10_n_gen_ev'] = len(gens)
    r['U10_ger_densa'] = (sorted(x['geracao'] for x in gens) == list(range(1, len(gens) + 1)))
    opt = sur[sur['regime'] != 'sonda']
    r['U10_opt_linhas'] = len(opt)
    r['U10_opt_esperado'] = len(gens) * 100 * 2
    r['U10_opt_ok'] = (len(opt) == len(gens) * 100 * 2)
    r['U10_sur_total_ok'] = (len(sur) == len(opt) + len(son))
    r['U10_nsel_uniq'] = sorted(set(x['n_sel'] for x in gens))
    r['U10_orcamento_surrogate'] = len(gens) * 100

    # ---------- U11 · fantasia / membros do dataset (② e real_solution_id) ----------
    r['U11_pop_linhas'] = len(popl)
    r['U11_pop_gens'] = sorted(popl['geracao'].unique().tolist())
    r['U11_pop_ultima_ger'] = int(popl['geracao'].max()) if len(popl) else 0
    ndsm = {x['geracao']: x['n_ds_membros'] for x in gens}
    r['U11_ndsm_g1'] = ndsm.get(1)
    r['U11_ndsm_g2'] = ndsm.get(2)
    r['U11_ndsm_ult_pos'] = max([g_ for g_, v in ndsm.items() if v > 0], default=0)
    r['U11_ndsm_serie'] = json.dumps([ndsm.get(i, 0) for i in range(1, min(11, len(gens) + 1))])
    pc = popl.groupby('geracao').size().to_dict()
    r['U11_pop_eq_ndsm'] = all(pc.get(g_, 0) == ndsm.get(g_, 0) for g_ in range(1, len(gens) + 1))
    r['U11_rsid_naonulo'] = int(sur['real_solution_id'].notna().sum())
    r['U11_rsid_esperado'] = 2 * len(popl)
    # erro de interpolacao nos membros do dataset (Kriging deve interpolar ~exato)
    o = opt[opt['real_solution_id'].notna()]
    if len(o):
        mp = real.set_index('solution_id')[fc]
        tf = mp.loc[o['real_solution_id'].astype(int).values].values.astype(np.float64)
        for mflag, tag in [('Kriging-DACE', 'K'), ('RBFN', 'R')]:
            oo = o[o['modelo_flag'] == mflag]
            if len(oo):
                tt = mp.loc[oo['real_solution_id'].astype(int).values].values.astype(np.float64)
                dd = np.abs(oo[muc].values.astype(np.float64) - tt)
                den = np.abs(tt).sum(axis=0)
                r['U11_interp_%s_wape' % tag] = float(dd.sum(axis=0).sum() / den.sum()) if den.sum() else np.nan
                r['U11_interp_%s_absmed' % tag] = float(np.median(dd))

    # ---------- U12 · camada ⑦ (o endpoint do offline) ----------
    r['U12_n_final'] = len(fin)
    r['U12_ger_uniq'] = sorted(fin['origem_geracao'].unique().tolist())
    r['U12_linha_densa'] = bool(np.array_equal(np.sort(fin['origem_linha'].values), np.arange(len(fin))))
    F = fin[fc].values.astype(np.float64)
    m_ = nd_mask(F)
    r['U12_nd_recomputo_ok'] = bool(np.array_equal(m_, fin['nd_pos_real'].values))
    r['U12_nd_pos_real'] = int(fin['nd_pos_real'].sum())
    r['U12_fantasia'] = float(fin['nd_pos_real'].mean())
    r['U12_rsid_null'] = int(fin['origem_solution_id'].isna().sum())
    # link posicional (ger,linha) -> ③ (linhas Kriging da ultima geracao, em ordem)
    g_last = int(fin['origem_geracao'].iloc[0])
    blk = opt[(opt['geracao'] == g_last) & (opt['modelo_flag'] == 'Kriging-DACE')]
    XS = blk[xc].values.astype(np.float32)
    XF = fin[xc].values.astype(np.float32)
    if XS.shape == XF.shape:
        idx = fin['origem_linha'].values
        r['U12_link_dX_max'] = float(np.abs(XS[idx] - XF).max())
        r['U12_link_bit'] = bool(np.array_equal(XS[idx], XF))
    else:
        r['U12_link_dX_max'] = -1.0
        r['U12_link_bit'] = False
    r['U12_footer_nfinal'] = (foot or {}).get('n_final')

    # ---------- FAMILIA/CONFIG · KFlag, gate 3sigma, modelos ----------
    kf = np.array([x['kflag'] for x in gens])
    r['A_kflag_1'] = int((kf == 1).sum())
    r['A_kflag_0'] = int((kf == 0).sum())
    r['A_kflag_lider'] = json.dumps(pd.Series([x['modelo_lider'] for x in gens]).value_counts().to_dict())
    r['A_kflag_g1'] = int(kf[0])
    r['A_kflag_estavel'] = bool(len(set(kf.tolist())) == 1)
    r['A_kflag_trocas'] = int((kf[1:] != kf[:-1]).sum())
    # consistencia KFlag <=> margem_3sigma
    ok, tot, cons, ufok = [], [], 0, 0
    for x in gens:
        ms = x.get('margem_3sigma_stats') or {}
        a, b = ms.get('n_pares_ok'), ms.get('n_pares_total')
        po = ms.get('n_pares_ok_por_objetivo') or []
        ok.append(a); tot.append(b)
        if a is not None and b:
            cons += int((a == b) == (x['kflag'] == 1))
        # UF >= M-1  <=>  existe pelo menos 1 objetivo confiavel em todos os pares
        if po:
            ufok += int((max(po) == b) == (x['kflag'] == 1))
    r['A_marg_cons'] = cons
    r['A_marg_n'] = len(gens)
    r['A_uf_cons'] = ufok
    r['A_marg_pares_g1'] = tot[0]
    r['A_marg_esperado_g1'] = (n_ds + 100) ** 2
    r['A_njulg_g1'] = gens[0]['n_julgados']
    r['A_njulg_g2'] = gens[1]['n_julgados'] if len(gens) > 1 else None
    r['A_njulg_uniq_g2p'] = sorted(set(x['n_julgados'] for x in gens[1:]))
    fr = [(x.get('margem_3sigma_stats') or {}).get('n_pares_ok', 0) /
          max((x.get('margem_3sigma_stats') or {}).get('n_pares_total', 1), 1) for x in gens]
    r['A_marg_frac_med'] = float(np.median(fr))
    r['A_marg_frac_min'] = float(np.min(fr))
    po_all = np.array([[(x.get('margem_3sigma_stats') or {}).get('n_pares_ok_por_objetivo', [np.nan] * M)[j]
                        for j in range(M)] for x in gens], dtype=float)
    tot_a = np.array(tot, dtype=float)
    r['A_obj_frac_med'] = json.dumps([round(float(np.median(po_all[:, j] / tot_a)), 6) for j in range(M)])
    r['A_obj_sempre_ok'] = json.dumps([int((po_all[:, j] == tot_a).all()) for j in range(M)])

    # sqrt(MSE) do gate
    r['A_sqrtmse_sel_max_g1'] = gens[0].get('sqrtmse_sel_max')
    r['A_sqrtmse_surr_med_med'] = float(np.median([x.get('sqrtmse_surr_med', np.nan) for x in gens]))
    r['A_sqrtmse_surr_max_max'] = float(np.nanmax([x.get('sqrtmse_surr_max', np.nan) for x in gens]))
    r['A_div_modelos_med'] = float(np.median([x.get('divergencia_modelos', np.nan) for x in gens]))
    r['A_div_modelos_g1'] = gens[0].get('divergencia_modelos')
    r['A_div_modelos_ult'] = gens[-1].get('divergencia_modelos')

    # RBFN / Kriging setup
    r['A_center_num'] = setup.get('center_num')
    r['A_center_esperado'] = int(math.ceil(math.sqrt(n_ds)))
    r['A_center_stock_11D'] = int(math.ceil(math.sqrt(11 * D - 1)))
    r['A_rbfn_spread'] = setup.get('rbfn_spread')
    r['A_rbfn_kernel'] = setup.get('rbfn_kernel')
    r['A_krig_theta_min'] = json.dumps(setup.get('krig_theta_min'))
    r['A_krig_theta_max'] = json.dumps(setup.get('krig_theta_max'))
    r['A_krig_sigma2'] = json.dumps(setup.get('krig_sigma2'))
    r['A_theta_no_teto'] = bool(all(abs(v - 10.0) < 1e-9 for v in (setup.get('krig_theta_min') or [])))

    # f_best trajectory (espaco surrogate) e f_best do dataset
    fb = np.array([x['f_best'] for x in gens], dtype=float)
    fbd = np.array(by['f_best_dataset'][0]['f_best_dataset'], dtype=float)
    r['A_fbest_ds'] = json.dumps([float(v) for v in fbd])
    r['A_fbest_g1'] = json.dumps([float(v) for v in fb[0]])
    r['A_fbest_ult'] = json.dumps([float(v) for v in fb[-1]])
    r['A_fbest_abaixo_ds'] = int((fb[-1] < fbd).sum())
    r['A_nfront1_g1'] = gens[0].get('n_front1')
    r['A_nfront1_ult'] = gens[-1].get('n_front1')
    r['A_nfront1_med'] = float(np.median([x.get('n_front1', np.nan) for x in gens]))

    # header/params echo (verificabilidade declarativa)
    p = man.get('params', {})
    r['A_N'] = p.get('N')
    r['A_kappa'] = p.get('kappa')
    r['A_decl_pm'] = ('proM=1' in str(p.get('pm', '')))
    r['A_decl_judge'] = ('diagonal i==j EXCLUIDA' in str(p.get('judgemodel', '')))
    r['A_decl_krig'] = ('regpoly1' in str(p.get('kriging', '')))
    r['A_decl_centros'] = ('ceil(sqrt(n_dataset))' in str(p.get('rbfn', '')))
    r['A_decl_stateless'] = ('STATELESS' in str(p.get('judgemodel', '')))
    r['A_sigma_dict'] = 'sigma_dict' in man
    return r


if __name__ == '__main__':
    rows = []
    for c in cells():
        try:
            rows.append(uma(*c))
            print('ok', c[0], flush=True)
        except Exception as e:
            print('ERRO', c[0], type(e).__name__, e, flush=True)
            raise
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, 'bateria_e103_celulas.csv'), index=False)
    print(df.shape)
