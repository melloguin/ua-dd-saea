#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""F5.3a b1 (ParEGO) — analise em escala, parte A: camadas ①②④⑥ + ③-busca. READ-ONLY."""
import json, math, os, sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
CELLS = ['BBOB_F1','BBOB_F5','BBOB_F17','BBOB_F22','BBOB_F37','BBOB_F49','BBOB_F55',
         'DTLZ1','DTLZ2','DTLZ3','DTLZ7','MMF1','MMF4','MMF11_L','MMF16_20',
         'WFG2','WFG4','WFG5','WFG9','ZDT1','ZDT3','ZDT4','ZDT6']

SQRT2 = math.sqrt(2.0)
def Phi(z): return 0.5*(1.0+math.erf(z/SQRT2))
def phi(z): return math.exp(-0.5*z*z)/math.sqrt(2*math.pi)

out = {}
for prob in CELLS:
    d = os.path.join(BASE, prob, '42')
    pref = f'exp_main_b1_{prob}_42'
    man = json.load(open(os.path.join(d, pref+'.manifest.json')))
    D_from_fe = (man['maxfe']+1)//31  # 31D-1
    r = {}
    r['status'] = man['status']; r['fe_final'] = man['fe_final']; r['maxfe'] = man['maxfe']
    r['n_geracoes_manifest'] = man['n_geracoes']; r['cache_hits_manifest'] = man['cache_hits']
    r['N_lambda'] = man['params']['N_lambda']
    r['sonda_geracoes'] = man['sonda']['geracoes']; r['sonda_nblocos'] = man['sonda']['n_blocos']
    r['created_at'] = man.get('created_at','')

    # ⑥ jsonl
    ge, guards, footer, header = [], [], None, None
    with open(os.path.join(d, pref+'.jsonl')) as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            e = json.loads(line)
            rec = e.get('rec')
            if rec == 'b1_gen': ge.append(e)
            elif rec == 'guard': guards.append(e)
            elif rec == 'footer': footer = e
            elif rec == 'header': header = e
    r['n_ge'] = len(ge)
    r['termino'] = footer.get('termino') if footer else None
    r['footer_fe_final'] = footer.get('fe_final') if footer else None

    # ① real
    real = pd.read_parquet(os.path.join(d, pref+'__real.parquet'))
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    M = len(fcols); D = sum(1 for c in real.columns if c.startswith('x') and c[1:].isdigit())
    r['D'] = D; r['M'] = M
    r['U1_n_real'] = len(real); r['U1_ok'] = (len(real) == 31*D-1) and real.fe_index.is_unique \
        and (real.fe_index.min()==0) and (real.fe_index.max()==31*D-2)
    r['U2_n_init'] = int((real.fase=='init').sum()); r['U2_ok'] = r['U2_n_init'] == 11*D-1
    n_opt = int((real.fase=='opt').sum()); r['n_opt'] = n_opt
    real = real.sort_values('fe_index').reset_index(drop=True)
    F = real[fcols].to_numpy(dtype=np.float64)
    sid_real = set(real.solution_id)

    # ④ timing
    tim = pd.read_parquet(os.path.join(d, pref+'__timing.parquet'))
    r['U3_n_tim'] = len(tim); r['U3_ok'] = (len(tim)==len(ge)) and tim.tempo_fit_s.notna().all()
    r['U7_viol'] = int((tim.tempo_fit_s+tim.tempo_busca_s > tim.tempo_geracao_s).sum())
    r['B5_n_acum_max'] = int(tim.n_acumulado.max())

    # ② pop
    pop = pd.read_parquet(os.path.join(d, pref+'__pop.parquet'))
    r['n_gen_pop'] = pop.geracao.nunique()
    gmax = pop.geracao.max()
    r['pop_dup_lastgen'] = int(pop[pop.geracao==gmax].solution_id.duplicated().sum())
    r['offby1_ok'] = (r['n_gen_pop'] == man['n_geracoes']) and (len(ge) == man['n_geracoes']-1) and (len(tim) == man['n_geracoes']-1)

    # ⑥-based aspects
    lam_all = np.array([e['lambda'] for e in ge], dtype=np.float64)
    if M == 2: H = r['N_lambda'] - 1
    else: H = 12  # NBI 91 p/ M=3: C(12+2,2)=91
    r['B1_H'] = H
    r['B1_grid_maxdev'] = float(np.abs(lam_all*H - np.round(lam_all*H)).max())
    r['B1_n_distinct_lambda'] = int(len(set(map(tuple, np.round(lam_all*H).astype(int)))))
    r['B1_max_reps'] = int(pd.Series(list(map(tuple, np.round(lam_all*H).astype(int)))).value_counts().max())
    r['B1_lam_sum_dev'] = float(np.abs(lam_all.sum(axis=1)-1).max())

    # fe increments (U6)
    fes = [e['fe'] for e in ge]
    diffs = set(np.diff(fes).tolist())
    r['U6_diffs'] = sorted(diffs); r['U6_ok'] = diffs <= {0,1}
    r['U6_n_fe0'] = int((np.diff(fes)==0).sum())
    r['lote_set'] = sorted(set(e.get('lote') for e in ge))

    # guards / U9
    gnames = pd.Series([g.get('name') for g in guards]).value_counts().to_dict()
    r['guards'] = gnames
    r['U9_cache_ok'] = gnames.get('cache_hit',0) == man['cache_hits']
    r['U10_c0'] = n_opt + man['cache_hits'] - len(ge)  # cache-hits que cairam no init

    # B2 gbest + B3 norm (todas as gens)
    b2_ok = b2_ok_loose = b3_ok = 0; b2_maxdev = 0.0; b2_alt = 0
    for e in ge:
        fe_e = e['fe']; nm = np.array(e['norm_min'],dtype=np.float64); nx = np.array(e['norm_max'],dtype=np.float64)
        lam = np.array(e['lambda'],dtype=np.float64)
        A = F[:fe_e-1]
        rng = np.where(nx-nm>0, nx-nm, 1.0)
        Fn = (A-nm)/rng
        pc = (Fn*lam).max(axis=1) + 0.05*(Fn*lam).sum(axis=1)
        dev = abs(pc.min()-e['gbest'])
        if dev < 1e-6: b2_ok += 1
        else:
            A2 = F[:fe_e]; Fn2=(A2-nm)/rng
            pc2=(Fn2*lam).max(axis=1)+0.05*(Fn2*lam).sum(axis=1)
            if abs(pc2.min()-e['gbest'])<1e-6: b2_alt += 1
        if dev < 1e-4: b2_ok_loose += 1
        b2_maxdev = max(b2_maxdev, min(dev, 999))
        if np.allclose(A.min(axis=0), nm, rtol=1e-5, atol=1e-6) and np.allclose(A.max(axis=0), nx, rtol=1e-5, atol=1e-6):
            b3_ok += 1
    r['B2_ok'] = b2_ok; r['B2_alt_posinfill'] = b2_alt; r['B2_ok_loose'] = b2_ok_loose; r['B3_ok'] = b3_ok

    # B5 subset
    cap = 11*D-1+25
    r['B5_cap'] = cap; r['B5_ntreino_max'] = max(e['n_treino'] for e in ge)
    r['B5_id_ok'] = sum(1 for e in ge if e['n_treino']==e['n_subset']-e['n_dedup'])
    r['B5_gens_no_cap'] = sum(1 for e in ge if e['n_treino']==cap)

    # B6/B7 contadores
    r['B6_sum_mse_neg'] = sum(e.get('n_mse_neg',0) for e in ge)
    r['B7_sum_ei_nan'] = sum(e.get('n_ei_nan',0) for e in ge)
    r['B7_nan_guard'] = sum(1 for e in ge if e.get('nan_guard'))

    # B8 GA interno
    r['B8_iters_ok'] = sum(1 for e in ge if e['ga_iters']==math.ceil(10000/e['ga_pop']))
    r['B8_pool_ok'] = sum(1 for e in ge if (e['ga_pop']-2*e['n_arquivo']) in (0,-2))
    r['B8_ga_iters_range'] = [min(e['ga_iters'] for e in ge), max(e['ga_iters'] for e in ge)]

    # B9 identidade EI (query-joia)
    ok9 = 0; relerrs = []; bsid_miss = 0; degen = 0
    for e in ge:
        g_, mu_, s_ = e['gbest'], e['mu_best'], e['sigma_best']
        if s_ is None or s_ <= 0: degen += 1; continue
        z = (g_-mu_)/s_
        ei = (g_-mu_)*Phi(z) + s_*phi(z)
        tgt = -e['ei_best']
        den = max(abs(ei), 1e-300)
        rel = abs(ei-tgt)/den
        relerrs.append(rel)
        if rel < 1e-6: ok9 += 1
        if e.get('best_sid') is not None and e['best_sid'] not in sid_real: bsid_miss += 1
    r['B9_ok'] = ok9; r['B9_n'] = len(ge); r['B9_degen_sigma0'] = degen
    r['B9_relerr_med'] = float(np.median(relerrs)) if relerrs else None
    r['B9_relerr_max'] = float(np.max(relerrs)) if relerrs else None
    r['B9_bsid_missing'] = bsid_miss
    r['B9_eibest_neg'] = sum(1 for e in ge if e['ei_best'] <= 0)

    # B11 theta bounds
    th_all = []; sat20 = 0; satlo = 0; oob = 0
    for e in ge:
        th = e.get('modelo_hp',{}).get('theta')
        if th is None: continue
        th = np.atleast_1d(np.array(th,dtype=np.float64))
        th_all.append(th)
        sat20 += int((th >= 20-1e-9).sum()); satlo += int((th <= 1e-5+1e-12).sum())
        oob += int(((th < 1e-5-1e-12)|(th > 20+1e-9)).sum())
    r['B11_oob'] = oob; r['B11_sat20'] = sat20; r['B11_satlo'] = satlo

    # ③ busca (colunas leves)
    sur_path = os.path.join(d, pref+'__surrogate.parquet')
    schema_cols = pq.read_schema(sur_path).names
    mu_extra = [c for c in schema_cols if c.startswith('mu_') and c != 'mu_0']
    sg_extra = [c for c in schema_cols if c.startswith('sigma_') and c != 'sigma_0']
    cols = ['regime','geracao','mu_0','sigma_0','real_solution_id','fe_treino_max',
            'pred_tipo','transf_tipo','modelo_flag'] + mu_extra + sg_extra
    sur = pd.read_parquet(sur_path, columns=cols)
    busca = sur[sur.regime=='online']
    r['B4_mu1_null'] = bool(all(busca[c].isna().all() for c in mu_extra)) if mu_extra else None
    r['B4_sig1_null'] = bool(all(busca[c].isna().all() for c in sg_extra)) if sg_extra else None
    r['B4_pred_tipo'] = sorted(busca.pred_tipo.unique().tolist())
    r['B4_transf_tipo'] = sorted(busca.transf_tipo.unique().tolist())
    r['B4_modelo_flag'] = sorted(busca.modelo_flag.unique().tolist())
    r['B6_sigma_min'] = float(busca.sigma_0.min()); r['B6_sigma_neg'] = int((busca.sigma_0<0).sum())
    r['B12_rsid_frac_busca'] = float(busca.real_solution_id.notna().mean())
    r['B12_n_busca'] = int(len(busca))

    # B13 granularidade: rows/gen == ga_pop
    cnt = busca.groupby(busca.geracao.dropna().astype(int) if busca.geracao.dtype!=object else busca.geracao).size()
    bg = busca.dropna(subset=['geracao']).copy(); bg['g'] = bg.geracao.astype(int)
    cnt = bg.groupby('g').size().to_dict()
    gp = {int(e['geracao']): e['ga_pop'] for e in ge}
    r['B13_ok'] = sum(1 for g,n in cnt.items() if gp.get(g)==n); r['B13_n'] = len(cnt)

    # B14 fe_treino_max monotonico?
    ftm = bg.groupby('g').fe_treino_max.first().sort_index()
    r['B14_monotonic'] = bool((ftm.diff().dropna()>=0).all())

    # B10 contrafactual greedy: pool tem mu < mu_best?
    mn = bg.groupby('g').mu_0.min().to_dict()
    mb = {int(e['geracao']): e['mu_best'] for e in ge}
    both = [g for g in mn if g in mb]
    r['B10_frac_nongreedy'] = float(np.mean([mn[g] < mb[g]-1e-12 for g in both])) if both else None
    r['B10_n'] = len(both)

    out[prob] = r
    sys.stderr.write(prob+' ok\n')

print(json.dumps(out, indent=1, default=str))
