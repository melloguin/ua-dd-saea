#!/usr/bin/env python
"""
BATERIA DE FIDELIDADE — c262 qNEHVI (F5.3b, protocolo v1.1)
READ-ONLY sobre os dados. Escreve SOMENTE em f5/baterias/c262/.

Executa, nas 21 células main da semente 42:
  U1..U11 (universais; U12 N/A = online), módulo de família GP-BO
  (query-joia do ranking dos restarts + identidade do train_Yvar sob Standardize)
  e os aspectos específicos do bundle alg_c262_qnehvi.md.

Saídas: c262_resultados.csv (1 linha/célula) · c262_decisoes.parquet (1 linha/decisão)
"""
import json, glob, os, sys, collections
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c262'

EPS32 = np.finfo(np.float32).eps

def cell_paths(prob):
    base = f'{ROOT}/{prob}/42'
    stem = f'exp_main_c262_{prob}_42'
    return dict(
        jsonl=f'{base}/{stem}.jsonl',
        man=f'{base}/{stem}.manifest.json',
        real=f'{base}/{stem}__real.parquet',
        pop=f'{base}/{stem}__pop.parquet',
        sur=f'{base}/{stem}__surrogate.parquet',
        tim=f'{base}/{stem}__timing.parquet',
    )

def analisa(prob):
    P = cell_paths(prob)
    r = {'problema': prob}
    man = json.load(open(P['man']))
    D_ = None

    # ---------- ⑥ jsonl ----------
    recs, bad = [], 0
    for l in open(P['jsonl']):
        l = l.strip()
        if not l: continue
        try: recs.append(json.loads(l))
        except Exception: bad += 1
    r['jsonl_linhas_ruins'] = bad
    by = collections.defaultdict(list)
    for x in recs: by[x.get('rec')].append(x)
    hdr = by['header'][0]
    dec = by['decision']; grd = by['guard']; snd = by['sonda']
    ftr = by['footer']; twarn = by['optimize_acqf_warning']; tmg = by['timing']
    D = hdr['D']; M = hdr['M']
    r['D'], r['M'] = D, M
    n_init = 11*D - 1
    maxfe = 31*D - 1
    r['n_init_esperado'] = n_init
    r['maxfe_formula'] = maxfe

    # ---------- manifesto ----------
    r['status'] = man['status']; r['n_retries'] = man['n_retries']
    r['fallback_ativado'] = man.get('fallback_ativado')
    r['maxfe_man'] = man['maxfe']; r['fe_final_man'] = man['fe_final']
    r['n_geracoes_man'] = man['n_geracoes']; r['cache_hits_man'] = man.get('cache_hits')
    r['acqf_ref_f'] = json.dumps(man.get('acqf_ref_f'))
    r['fused_kernel'] = man.get('fused_kernel')
    r['man_tem_params'] = 'params' in man
    r['man_tem_sigma_dict'] = 'sigma_dict' in man
    r['man_tem_sonda'] = 'sonda' in man
    r['doe_hash_man'] = man['doe_hash']
    r['algo_version'] = man['algo_version']
    e = man['env']
    for k in ['python','numpy','scipy','pymoo','torch','gpytorch','botorch','botorch_record_sha256']:
        r['env_'+k] = e.get(k)
    pin = e['pinning']
    r['pin_ok'] = (pin['torch_num_threads']==1 and pin['default_dtype']=='torch.float64'
                   and pin['device']=='cpu' and all(pin[k]=='1' for k in
                   ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']))
    r['fit_series_len'] = len(man['fit_series'])
    r['wall_s'] = man['timing']['tempo_total_s']

    # header: params + ref
    prm = hdr.get('params', {})
    r['hdr_tem_params'] = bool(prm)
    for k in ['mc_samples','num_restarts','raw_samples','train_Yvar','q','refit','kernel','acqf','cache_root','maxiter','init_batch_limit']:
        r['prm_'+k] = prm.get(k, 'AUSENTE')
    r['ideal_s5'] = json.dumps(hdr.get('ideal_s5')); r['nadir_s5'] = json.dumps(hdr.get('nadir_s5'))
    r['acqf_ref_max'] = json.dumps(hdr.get('acqf_ref_max'))
    r['ref_fonte'] = hdr.get('ref_fonte')
    # álgebra do ref: r = nadir + 0.1*(nadir - ideal) em MIN; max = -r
    id5 = np.array(hdr['ideal_s5'], float); nd5 = np.array(hdr['nadir_s5'], float)
    ref_calc = nd5 + 0.1*(nd5 - id5)
    ref_log = np.array(hdr['acqf_ref_f'], float)
    r['ref_algebra_maxabs'] = float(np.max(np.abs(ref_calc - ref_log)))
    r['ref_max_espelha'] = bool(np.allclose(np.array(hdr['acqf_ref_max'],float), -ref_log))
    r['warning_filter'] = hdr.get('warning_filter','')[:60]

    # ---------- ① real ----------
    real = pd.read_parquet(P['real'])
    r['n_real'] = len(real)
    r['U1_fe_igual'] = (len(real)==maxfe==man['maxfe']==man['fe_final'])
    fi = real['fe_index'].values
    r['U1_fe_index_denso'] = bool(np.array_equal(np.sort(fi), np.arange(len(real))))
    r['U1_fe_index_ordenado'] = bool(np.array_equal(fi, np.arange(len(real))))
    fases = real['fase'].value_counts().to_dict()
    r['fases'] = json.dumps(fases)
    r['U2_n_init'] = int((real['fase']=='init').sum())
    r['U2_init_ok'] = (r['U2_n_init']==n_init)
    r['sol_id_denso'] = bool(np.array_equal(np.sort(real['solution_id'].values), np.arange(len(real))))
    xcols = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    r['n_xcols'], r['n_fcols'] = len(xcols), len(fcols)
    # U2 bit-a-bit vs artefato DoE
    dp = f'{REPO}/data/doe/{prob}/doe_{prob}_42.parquet'
    if os.path.exists(dp):
        doe = pd.read_parquet(dp)
        Xd = doe.values.astype(np.float32)
        Xi = real.loc[real['fase']=='init', xcols].values.astype(np.float32)
        r['U2_doe_maxabs'] = float(np.max(np.abs(Xd - Xi))) if Xd.shape==Xi.shape else -1.0
    else:
        r['U2_doe_maxabs'] = np.nan
    Fmin = real[fcols].values.astype(np.float64)   # f de MINIMIZAÇÃO

    # ---------- ② pop ----------
    pop = pd.read_parquet(P['pop'])
    r['n_pop'] = len(pop)
    gs = pop.groupby('geracao').size()
    r['pop_g0'] = int(gs.iloc[0]); r['pop_gmax'] = int(gs.iloc[-1])
    r['pop_n_ger'] = int(pop['geracao'].nunique())
    r['pop_monotona'] = bool((np.diff(gs.values) >= 0).all())
    r['pop_passo_max'] = int(np.max(np.diff(gs.values))) if len(gs)>1 else 0

    # ---------- ③ surrogate ----------
    sur = pd.read_parquet(P['sur'])
    r['n_sur'] = len(sur)
    r['regimes'] = json.dumps(sur['regime'].value_counts().to_dict())
    on = sur[sur['regime']=='online']
    so = sur[sur['regime']=='sonda']
    r['n_online'] = len(on); r['n_sonda_linhas'] = len(so)
    ng = man['n_geracoes']
    r['DI10_online_eq_10xger'] = (len(on) == 10*ng)
    r['DI10_restarts_por_ger_unico'] = json.dumps(sorted(on.groupby('geracao').size().unique().tolist()))
    r['U12_NA'] = 'online: sem camada ⑦'
    mucols = [c for c in sur.columns if c.startswith('mu_')]
    sgcols = [c for c in sur.columns if c.startswith('sigma_')]
    r['sigma_notna_frac'] = float(sur[sgcols].notna().all(axis=1).mean())
    r['sigma_pos_frac'] = float((sur[sgcols].values > 0).all(axis=1).mean())
    r['modelo_flag'] = json.dumps(sur['modelo_flag'].value_counts().to_dict())
    r['transf_tipo_nulo'] = bool(sur['transf_tipo'].isna().all())
    r['espaco_modelo'] = json.dumps(sur['espaco_modelo'].value_counts(dropna=False).to_dict())
    # U8 fe_treino_max
    ft = on.groupby('geracao')['fe_treino_max'].max()
    r['U8_ftmax_monotono'] = bool((np.diff(ft.values) >= 0).all())
    r['U8_ftmax_min'] = int(ft.min()); r['U8_ftmax_max'] = int(ft.max())
    r['U8_ftmax_esperado_min'] = n_init - 1
    # real_solution_id
    rsi = on['real_solution_id']
    r['n_rsi_notna'] = int(rsi.notna().sum())
    r['rsi_unicos'] = int(rsi.dropna().nunique())
    gcnt = on[rsi.notna()].groupby('geracao').size()
    r['rsi_por_ger_max'] = int(gcnt.max()) if len(gcnt) else 0
    r['rsi_ger_cobertas'] = int(len(gcnt))
    r['rsi_sonda_null'] = bool(so['real_solution_id'].isna().all())
    # bounds nativos do problema (x na ③ é NATIVO)
    r['x_min'] = float(on[xcols].values.min()); r['x_max'] = float(on[xcols].values.max())

    # ---------- ④ timing ----------
    tim = pd.read_parquet(P['tim'])
    r['n_timing'] = len(tim)
    r['U3_1fit_por_ger'] = (len(tim)==ng==len(man['fit_series'])==len(tmg))
    soma = tim['tempo_fit_s'].values + tim['tempo_busca_s'].values
    r['U7_inv1_viol'] = int((soma > tim['tempo_geracao_s'].values + 1e-6).sum())
    gs_sonda = set(int(x['geracao']) for x in snd)
    tim_g = tim['geracao'].values
    excede = (tim['tempo_geracao_s'].values - soma) > (tim['tempo_pred_sonda_s'].values*0.5 + 1e-9)
    com_sonda = np.array([g in gs_sonda for g in tim_g])
    r['U7_inv2_sonda_excede'] = int((excede & com_sonda).sum())
    r['U7_inv2_n_sonda'] = int(com_sonda.sum())
    r['U7_sem_sonda_excede'] = int((excede & ~com_sonda).sum())
    r['tempo_fit_total'] = float(tim['tempo_fit_s'].sum())
    r['tempo_busca_total'] = float(tim['tempo_busca_s'].sum())
    r['tempo_sonda_total'] = float(tim['tempo_pred_sonda_s'].sum())

    # ---------- ⑥ decisões ----------
    r['rec_counts'] = json.dumps({k: len(v) for k, v in sorted(by.items())})
    r['n_decisoes'] = len(dec)
    r['dec_eq_ger'] = (len(dec)==ng)
    caminhos = collections.Counter(d['caminho'] for d in dec)
    r['caminhos'] = json.dumps(dict(caminhos))
    motivos = collections.Counter(d['motivo'] for d in dec)
    r['motivos'] = json.dumps(dict(motivos))
    n_ch = sum(1 for d in dec if d.get('cache_hit'))
    r['n_cache_hit_dec'] = n_ch
    gnames = collections.Counter(g['name'] for g in grd)
    r['guard_names'] = json.dumps(dict(gnames))
    r['U9_guard_cachehit'] = gnames.get('cache_hit', 0)
    r['U9_fecha'] = (gnames.get('cache_hit',0) == n_ch == man.get('cache_hits'))
    n_hs = sum(1 for d in dec if d['caminho']=='hard_stop')
    r['n_hard_stop'] = n_hs
    r['hard_stop_guard'] = gnames.get('hard_stop', 0)
    r['U10_arit'] = (ng == (man['fe_final'] - n_init) + n_ch + n_hs)
    r['U10_lhs'] = ng
    r['U10_rhs'] = (man['fe_final'] - n_init) + n_ch + n_hs
    # footer
    r['n_footer'] = len(ftr)
    f0 = ftr[0] if ftr else {}
    r['footer_status'] = f0.get('status'); r['footer_fe_final'] = f0.get('fe_final')
    r['footer_ger'] = f0.get('n_geracoes'); r['footer_cache_hits'] = f0.get('cache_hits')
    r['footer_cp_init'] = f0.get('cp_init'); r['footer_hard_stopped'] = f0.get('hard_stopped')
    r['footer_blocos'] = f0.get('n_blocos_sonda')
    r['footer_fecha_man'] = (f0.get('fe_final')==man['fe_final'] and f0.get('n_geracoes')==ng
                             and f0.get('cache_hits')==man.get('cache_hits'))

    # QUERY-JOIA 1: escolhido == argmax dos restarts
    ok_max = 0; ok_arg = 0; n10 = 0; dmax = 0.0
    argmax_pos = []
    for d in dec:
        a = np.array(d['acqf_todos_restarts'], float)
        if len(a)==10: n10 += 1
        if d['n_restarts']!=10: n10 -= 0
        m = a.max()
        if abs(m - d['acqf_escolhido']) <= 1e-12*max(1.0, abs(m)): ok_max += 1
        dmax = max(dmax, abs(m - d['acqf_escolhido']))
        argmax_pos.append(int(np.argmax(a)))
    r['QJ1_escolhido_eq_max'] = ok_max
    r['QJ1_delta_max'] = dmax
    r['QJ1_len10'] = n10
    r['QJ1_argmax_hist'] = json.dumps(dict(collections.Counter(argmax_pos)))

    # QUERY-JOIA 1b: a POSIÇÃO do argmax == posição da linha com real_solution_id na ③
    on2 = on.reset_index(drop=True)
    pos_ok = 0; pos_tot = 0; pos_mismatch = []
    grp = on2.groupby('geracao', sort=True)
    dec_by_it = {d['it']: d for d in dec}
    for g, sub in grp:
        d = dec_by_it.get(int(g))
        if d is None: continue
        idx = np.where(sub['real_solution_id'].notna().values)[0]
        if len(idx)!=1: continue
        pos_tot += 1
        a = np.array(d['acqf_todos_restarts'], float)
        if int(np.argmax(a)) == int(idx[0]): pos_ok += 1
        else: pos_mismatch.append((int(g), int(idx[0]), int(np.argmax(a))))
    r['QJ1b_pos_ok'] = pos_ok; r['QJ1b_pos_tot'] = pos_tot
    r['QJ1b_mismatch'] = json.dumps(pos_mismatch[:10])

    # QUERY-JOIA 2: identidade do train_Yvar sob Standardize
    #   noise_j == max(1e-6, 1e-6 / var_ddof1( (-f_j)[:n_train] ))
    nid_ok = 0; nid_tot = 0; nid_relmax = 0.0; n_piso = 0
    Ymax = -Fmin
    for d in dec:
        nt = d.get('n_train')
        if nt is None: continue
        for j, o in enumerate(d['modelo_hp']['por_objetivo']):
            v = Ymax[:nt, j].var(ddof=1)
            esp = max(1e-6, 1e-6 / v) if v > 0 else np.nan
            got = o['noise']
            nid_tot += 1
            if abs(got - 1e-6) <= 1e-15: n_piso += 1
            if np.isfinite(esp):
                rel = abs(got - esp) / esp
                nid_relmax = max(nid_relmax, rel)
                if rel < 1e-6: nid_ok += 1
    r['QJ2_noise_ok'] = nid_ok; r['QJ2_noise_tot'] = nid_tot
    r['QJ2_rel_max'] = nid_relmax; r['QJ2_n_piso1e6'] = n_piso

    # ARD vivo + refit do zero
    ard = 0; ard_tot = 0; muda = 0; pares = 0
    prev = None
    lsmed_series = []
    for d in dec:
        po = d['modelo_hp']['por_objetivo']
        for o in po:
            ard_tot += 1
            if o['lengthscale_max'] > o['lengthscale_min']: ard += 1
        cur = tuple(round(o['lengthscale_med'], 12) for o in po)
        lsmed_series.append([o['lengthscale_med'] for o in po])
        if prev is not None:
            pares += 1
            if cur != prev: muda += 1
        prev = cur
    r['ARD_vivo'] = ard; r['ARD_tot'] = ard_tot
    r['refit_muda'] = muda; r['refit_pares'] = pares
    ls = np.array(lsmed_series)
    r['ls_med_inicio'] = json.dumps([round(float(x),4) for x in ls[0]])
    r['ls_med_fim'] = json.dumps([round(float(x),4) for x in ls[-1]])

    # prune_baseline / n_baseline
    nb = np.array([d['n_baseline'] for d in dec], float)
    ntr = np.array([d.get('n_train', np.nan) for d in dec], float)
    r['nb_min'] = float(np.nanmin(nb)); r['nb_max'] = float(np.nanmax(nb))
    r['nb_le_ntrain'] = int(np.nansum(nb <= ntr))
    r['nb_tot_comp'] = int(np.sum(np.isfinite(ntr)))
    with np.errstate(invalid='ignore', divide='ignore'):
        ratio = nb/ntr
    r['nb_ratio_final'] = float(ratio[np.isfinite(ratio)][-1]) if np.isfinite(ratio).any() else np.nan
    r['nb_ratio_med'] = float(np.nanmedian(ratio))
    r['nb_zero_iters'] = int(np.sum(nb==0))
    r['mll_final_ultimo'] = dec[-1]['modelo_hp']['mll_final']
    r['mll_finito'] = int(sum(1 for d in dec if np.isfinite(d['modelo_hp']['mll_final'])))

    # RNG: torch_seed/h1/h2 por iteração
    ts = [d['torch_seed'] for d in dec]; h1 = [d['h1'] for d in dec]; h2 = [d['h2'] for d in dec]
    r['seeds_unicos_ts'] = len(set(ts)); r['seeds_unicos_h1'] = len(set(h1)); r['seeds_unicos_h2'] = len(set(h2))
    r['seeds_h1_ne_h2'] = int(sum(1 for a,b in zip(h1,h2) if a!=b))

    # retries / warnings
    r['fit_retries_soma'] = int(sum(d.get('fit_retries',0) for d in dec))
    r['acqf_warn_soma'] = int(sum(d.get('acqf_warnings',0) for d in dec))
    r['n_rec_warn'] = len(twarn)
    r['warn_soma_rec'] = int(sum(x.get('n',0) for x in twarn))
    r['warn_fecha'] = (r['acqf_warn_soma'] == r['warn_soma_rec'])

    # cache-hit: dist_min_arquivo == 0 e x_key
    dmins = [d['dist_min_arquivo'] for d in dec if d.get('cache_hit')]
    r['ch_dist0'] = int(sum(1 for x in dmins if x==0.0)); r['ch_n'] = len(dmins)
    xk = collections.Counter(g['x_key'] for g in grd if g['name']=='cache_hit')
    r['ch_xkeys_distintas'] = len(xk)
    r['ch_xkey_top'] = json.dumps(xk.most_common(3))
    r['ch_sol_ids'] = json.dumps(sorted(set(g['solution_id'] for g in grd if g['name']=='cache_hit'))[:8])
    dmin_all = np.array([d['dist_min_arquivo'] for d in dec], float)
    r['dist_min_mediana'] = float(np.median(dmin_all))

    # n_front1 / f_best (evolução da fronteira interna)
    nf = np.array([d['n_front1'] for d in dec], float)
    r['n_front1_ini'] = float(nf[0]); r['n_front1_fim'] = float(nf[-1]); r['n_front1_max'] = float(nf.max())

    # ---------- U4 cadência da sonda ----------
    gsl = sorted(gs_sonda)
    esperado = sorted(set([g for g in range(1, ng+1) if (g==1 or g%2==0)] + [ng]))
    r['U4_blocos'] = len(gsl)
    r['U4_esperado'] = len(esperado)
    r['U4_igual'] = (gsl == esperado)
    r['U4_ultima_coberta'] = (ng in gs_sonda)
    r['U4_ng_par'] = (ng % 2 == 0)
    r['U4_blocos_man'] = man['sonda']['n_blocos']
    r['U4_hash_ok'] = all(x.get('hash_check','').startswith('ok') for x in snd)
    r['U4_npontos_ok'] = all(x['n_pontos']==2000 for x in snd)
    r['U4_blocos_sur'] = int(so['geracao'].nunique())
    r['U4_linhas_por_bloco'] = json.dumps(sorted(so.groupby('geracao').size().unique().tolist()))

    # ---------- U5 join posicional sonda × gabarito ----------
    sp = f'{REPO}/data/sonda/sonda_{prob}.parquet'
    if os.path.exists(sp) and len(so):
        gab = pd.read_parquet(sp)
        gx = gab[[f'x{i}' for i in range(D)]].values[:2000].astype(np.float32)
        g1 = sorted(so['geracao'].unique())
        worst = 0.0
        for g in [g1[0], g1[len(g1)//2], g1[-1]]:
            b = so[so['geracao']==g][[f'x{i}' for i in range(D)]].values.astype(np.float32)
            if b.shape == gx.shape:
                worst = max(worst, float(np.max(np.abs(b-gx))))
            else:
                worst = 9e9
        r['U5_maxabs'] = worst
        gf = gab[[f'f{j}' for j in range(M)]].values[:2000].astype(np.float64)
    else:
        r['U5_maxabs'] = np.nan; gf = None

    # ---------- U6 WAPE/cobertura própria (1º e último bloco) ----------
    if gf is not None and len(so):
        g1 = sorted(so['geracao'].unique())
        res = {}
        for tag, g in [('ini', g1[0]), ('fim', g1[-1])]:
            b = so[so['geracao']==g]
            mu = b[[f'mu_{j}' for j in range(M)]].values.astype(np.float64)
            sg = b[[f'sigma_{j}' for j in range(M)]].values.astype(np.float64)
            for j in range(M):
                w = np.abs(mu[:,j]-gf[:,j]).sum()/np.abs(gf[:,j]).sum()
                cov = float((np.abs(mu[:,j]-gf[:,j]) <= 1.96*sg[:,j]).mean())
                res[f'wape_{tag}_o{j}'] = float(w); res[f'cob_{tag}_o{j}'] = cov
        r['U6_wape_ini'] = json.dumps({k:round(v,5) for k,v in res.items() if k.startswith('wape_ini')})
        r['U6_wape_fim'] = json.dumps({k:round(v,5) for k,v in res.items() if k.startswith('wape_fim')})
        r['U6_cob_ini'] = json.dumps({k:round(v,4) for k,v in res.items() if k.startswith('cob_ini')})
        r['U6_cob_fim'] = json.dumps({k:round(v,4) for k,v in res.items() if k.startswith('cob_fim')})
        dw = []
        for j in range(M):
            a=res[f'wape_ini_o{j}']; b2=res[f'wape_fim_o{j}']
            dw.append((b2-a)/a if a>0 else np.nan)
        r['U6_dwape_med'] = float(np.nanmedian(dw))

    # ---------- U11 erro de fantasia ----------
    sel = on[on['real_solution_id'].notna()]
    if len(sel):
        sid = sel['real_solution_id'].astype(int).values
        freal = real.set_index('solution_id').loc[sid, fcols].values.astype(np.float64)
        mu = sel[[f'mu_{j}' for j in range(M)]].values.astype(np.float64)
        sg = sel[[f'sigma_{j}' for j in range(M)]].values.astype(np.float64)
        err = np.abs(mu - freal)
        r['U11_med_abs'] = json.dumps([round(float(np.median(err[:,j])),6) for j in range(M)])
        r['U11_p90_abs'] = json.dumps([round(float(np.percentile(err[:,j],90)),6) for j in range(M)])
        rng = np.abs(freal).mean(axis=0)
        r['U11_med_rel'] = json.dumps([round(float(np.median(err[:,j])/rng[j]),6) if rng[j]>0 else None for j in range(M)])
        r['U11_cob_infill'] = json.dumps([round(float((err[:,j] <= 1.96*sg[:,j]).mean()),4) for j in range(M)])
        r['U11_n'] = len(sel)
        # sinal: dupla negação daria erro ~2|f|
        r['U11_erro_vs_2f'] = json.dumps([round(float(np.median(err[:,j])/(2*rng[j])),6) if rng[j]>0 else None for j in range(M)])

    # ---------- decisões detalhadas ----------
    rows = []
    for k, d in enumerate(dec):
        po = d['modelo_hp']['por_objetivo']
        rows.append(dict(problema=prob, it=d['it'], caminho=d['caminho'],
                         cache_hit=bool(d.get('cache_hit', False)),
                         acqf=d['acqf_escolhido'], n_baseline=d['n_baseline'],
                         n_train=d.get('n_train'), fe=d['fe'], n_front1=d['n_front1'],
                         dist_min=d['dist_min_arquivo'], mll=d['modelo_hp']['mll_final'],
                         ls_med_0=po[0]['lengthscale_med'], noise_0=po[0]['noise'],
                         outputscale_0=po[0]['outputscale'],
                         spread=float(np.ptp(d['acqf_todos_restarts'])),
                         t_fit=d['tempo_fit_s'], t_busca=d['tempo_busca_s']))
    return r, pd.DataFrame(rows)


def main():
    probs = sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))
    out, decs = [], []
    for p in probs:
        try:
            rr, dd = analisa(p)
            out.append(rr); decs.append(dd)
            print(f'[ok] {p}', flush=True)
        except Exception as ex:
            import traceback; traceback.print_exc()
            print(f'[ERRO] {p}: {ex}', flush=True)
    df = pd.DataFrame(out)
    df.to_csv(f'{OUT}/c262_resultados.csv', index=False)
    pd.concat(decs, ignore_index=True).to_parquet(f'{OUT}/c262_decisoes.parquet')
    print('\ncélulas:', len(df))
    print(df[['problema','D','M','n_real','n_geracoes_man','cache_hits_man','U1_fe_igual',
              'U2_init_ok','U9_fecha','U10_arit','QJ1_escolhido_eq_max','QJ1b_pos_ok','QJ1b_pos_tot',
              'QJ2_noise_ok','QJ2_noise_tot']].to_string())

if __name__ == '__main__':
    main()
