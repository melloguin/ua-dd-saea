"""Bateria principal b1 (ParEGO) - F5.3a-v1.1.
Percorre TODAS as celulas main/42 e computa, por iteracao (evento b1_gen do (6)),
as identidades do mecanismo: PCheby/gbest, normalizacao, EI fechado, best_sid,
subset/dedup, GA interno, guards, theta, ledger de FE.
Saida: b1_iters.csv (1 linha/iteracao) + b1_celulas.csv (1 linha/celula).
READ-ONLY sobre dados/artefatos.
"""
import json, os, math
import numpy as np, pandas as pd
from scipy.stats import norm as _norm

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
EXCL = {'WFG1'}  # REPROVADA F5.2a

probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.'))])
probs = [p for p in probs if p not in EXCL]

iters_rows, cell_rows = [], []

for p in probs:
    d = f'{ROOT}/{p}/42'
    base = f'{d}/exp_main_b1_{p}_42'
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ftr = [e for e in evs if e['rec'] == 'footer']
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    guards = [e for e in evs if e['rec'] == 'guard']
    sondas = [e for e in evs if e['rec'] == 'sonda']
    D, M = hdr['D'], hdr['M']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    real = real.sort_values('fe_index').reset_index(drop=True)
    F = real[fc].values.astype(np.float64)
    SID = real['solution_id'].values
    XR = real[xc].values.astype(np.float32)

    # ---------- U1 orcamento ----------
    maxfe = 31 * D - 1
    u1_len = len(real) == maxfe
    u1_dense = (real['fe_index'].values == np.arange(len(real))).all()
    u1_sid_uniq = real['solution_id'].is_unique
    dupX = len(real) - len(set(map(bytes, np.ascontiguousarray(XR))))
    n_init = int((real['fase'] == 'init').sum())
    u2_ok = n_init == 11 * D - 1

    # ---------- U2 DoE bit-a-bit ----------
    doe = pd.read_parquet(f'{DOE}/{p}/doe_{p}_42.parquet')
    dX = np.abs(doe[xc].values.astype(np.float32) - XR[:len(doe)]).max()
    doe_man = json.load(open(f'{DOE}/{p}/doe_{p}_42.manifest.json'))
    doe_hash_ok = doe_man.get('x_hash', doe_man.get('hash', doe_man.get('doe_hash'))) == man['doe_hash']

    # ---------- guards ----------
    gn = pd.Series([g['name'] for g in guards]).value_counts().to_dict()
    n_cache = gn.get('cache_hit', 0)
    n_dedupg = gn.get('dedup_treino', 0)
    c0 = sum(1 for g in guards if g['name'] == 'cache_hit' and g.get('fe') == 1)
    cache_ok = n_cache == man['cache_hits'] == (ftr[0]['cache_hits'] if ftr else -1)

    # ---------- por iteracao ----------
    cap = 11 * D - 1 + 25
    Ngrid = man['params']['N_lambda']
    H = 99 if M == 2 else 12  # 1/(N-1) para M=2 (N=100); NBI H=12 -> 91 vetores p/ M=3
    prev_ftm = None
    lam_seen = []
    for e in ge:
        g, fe = e['geracao'], e['fe']
        na = e['n_arquivo']
        lam = np.array(e['lambda'], dtype=np.float64)
        nmin = np.array(e['norm_min'], dtype=np.float64)
        nmax = np.array(e['norm_max'], dtype=np.float64)
        # arquivo pre-fit: regra CANONICA = as primeiras (fe-1) linhas da (1);
        # em geracoes de cache-hit o arquivo tem `fe` linhas (armadilha do piloto).
        rng = np.where((nmax - nmin) == 0, 1.0, nmax - nmin)

        def _probe(n):
            A = F[:n]
            dmin = np.abs(A.min(0) - nmin).max() / max(np.abs(nmin).max(), 1e-12)
            dmax = np.abs(A.max(0) - nmax).max() / max(np.abs(nmax).max(), 1e-12)
            Fn = (A - nmin) / rng
            pcv = (Fn * lam).max(1) + 0.05 * (Fn * lam).sum(1)
            return dmin, dmax, abs(pcv.min() - e['gbest'])

        dn_nmin, dn_nmax, d_gbest_naive = _probe(fe - 1)
        p1 = _probe(fe) if fe <= len(F) else (np.inf, np.inf, np.inf)
        err0 = dn_nmin + dn_nmax + d_gbest_naive
        err1 = p1[0] + p1[1] + p1[2]
        if err1 < err0 * 0.5:
            n_arq_real = fe
            d_nmin, d_nmax, d_gbest = p1
        else:
            n_arq_real = fe - 1
            d_nmin, d_nmax, d_gbest = dn_nmin, dn_nmax, d_gbest_naive
        rel_gbest = d_gbest / max(abs(e['gbest']), 1e-30)
        # EI fechado
        mu, sg, gbl = e['mu_best'], e['sigma_best'], e['gbest']
        if sg > 0:
            z = (gbl - mu) / sg
            ei = (gbl - mu) * _norm.cdf(z) + sg * _norm.pdf(z)
        else:
            z = np.nan; ei = max(gbl - mu, 0.0)
        tgt = -e['ei_best']
        d_ei = abs(ei - tgt)
        rel_ei = d_ei / max(abs(tgt), 1e-300)
        # best_sid -> infill
        sid_infill = SID[fe - 1] if fe - 1 < len(SID) else np.nan
        # PCheby REAL do infill (erro de fantasia escalar)
        if fe - 1 < len(F):
            fi = (F[fe - 1] - nmin) / rng
            pc_inf = (fi * lam).max() + 0.05 * (fi * lam).sum()
        else:
            pc_inf = np.nan
        # lambda no grid
        d_grid = np.abs(lam * H - np.round(lam * H)).max()
        lam_seen.append(tuple(np.round(lam, 10)))
        e0 = e.get('e0_trace') or []
        ftm = e.get('fe_treino_max')
        iters_rows.append(dict(
            problema=p, D=D, M=M, geracao=g, fe=fe, n_arquivo=na,
            n_arq_real=n_arq_real, arquivo_eq_fe_menos_1=(n_arq_real == fe - 1),
            na_eq_pop=(na == 11 * D - 1 + g - 1),
            d_gbest=d_gbest, rel_gbest=rel_gbest, d_gbest_naive=d_gbest_naive,
            d_nmin=d_nmin, d_nmax=d_nmax, d_nmin_naive=dn_nmin, d_nmax_naive=dn_nmax,
            gbest=gbl, mu_best=mu, sigma_best=sg, ei_best=e['ei_best'], z=z,
            ei_calc=ei, d_ei=d_ei, rel_ei=rel_ei,
            best_sid=e['best_sid'], sid_infill=sid_infill,
            sid_match=(e['best_sid'] == sid_infill),
            pcheby_infill=pc_inf, erro_fantasia=(mu - pc_inf) if pc_inf == pc_inf else np.nan,
            n_subset=e['n_subset'], n_treino=e['n_treino'], n_dedup=e['n_dedup'],
            subset_id=(e['n_treino'] == e['n_subset'] - e['n_dedup']),
            subset_esperado=min(na, cap), subset_ok=(e['n_subset'] == min(na, cap)),
            cap=cap, no_cap=(e['n_subset'] == cap),
            ga_iters=e['ga_iters'], ga_pop=e['ga_pop'],
            ga_iters_ok=(e['ga_iters'] == math.ceil(10000 / e['ga_pop'])),
            ga_pop_delta=e['ga_pop'] - 2 * na,
            n_pool_ga=e.get('n_pool_ga'),
            theta_min=e['theta_min'], theta_max=e['theta_max'], theta_media=e['theta_media'],
            n_mse_neg=e.get('n_mse_neg', 0), n_ei_nan=e.get('n_ei_nan', 0),
            nan_guard=int(bool(e.get('nan_guard', 0))),
            dist_min_arquivo=e.get('dist_min_arquivo'),
            fe_treino_max=ftm, ftm_diff=(np.nan if prev_ftm is None else ftm - prev_ftm),
            e0_len=len(e0), e0_min=min(e0) if e0 else np.nan,
            ei_eq_min_e0=(abs(min(e0) - e['ei_best']) < 1e-12) if e0 else False,
            e0_monot=bool(np.all(np.diff(e0) <= 1e-15)) if len(e0) > 1 else True,
            e0_subidas=int((np.diff(e0) > 0).sum()) if len(e0) > 1 else 0,
            d_lambda_grid=d_grid, n_front1=e.get('n_front1'),
            tempo_fit_s=e.get('tempo_fit_s'), tempo_busca_s=e.get('tempo_busca_s'),
            tempo_geracao_s=e.get('tempo_geracao_s'), tempo_pred_sonda_s=e.get('tempo_pred_sonda_s'),
        ))
        prev_ftm = ftm

    # ---------- (2) off-by-one + dups ----------
    gmax = pop['geracao'].max()
    last = pop[pop['geracao'] == gmax]
    dup_last = int(last['solution_id'].duplicated().sum())
    pop_gens = pop['geracao'].nunique()
    sz = pop.groupby('geracao').size()
    pop_size_ok = bool((sz.values == np.arange(11 * D - 1, 11 * D - 1 + len(sz))).all())

    # ---------- (4) timing ----------
    t_ok = int((tim['tempo_fit_s'] + tim['tempo_busca_s'] <= tim['tempo_geracao_s'] + 1e-12).sum())
    t_viol_sonda = int(((tim['tempo_fit_s'] + tim['tempo_busca_s'] + tim['tempo_pred_sonda_s'].fillna(0)
                         > tim['tempo_geracao_s'])).sum())
    gens_sonda = set(man['sonda']['geracoes'])
    gens_viol = set(tim.loc[(tim['tempo_fit_s'] + tim['tempo_busca_s'] + tim['tempo_pred_sonda_s'].fillna(0)
                             > tim['tempo_geracao_s']), 'geracao'].astype(int))

    # ---------- sonda: cadencia ----------
    Gmax = len(ge)
    esperado = {1} | {g for g in range(2, Gmax + 1) if g % 2 == 0} | {Gmax}
    cad_ok = set(man['sonda']['geracoes']) == esperado
    sonda_gens_jsonl = set(int(s['geracao']) for s in sondas)

    # ---------- ledger ----------
    n_iter = len(ge)
    n_infill = maxfe - n_init
    ledger_ok = (n_iter == n_infill + n_cache - c0)

    it = pd.DataFrame([r for r in iters_rows if r['problema'] == p])
    cell_rows.append(dict(
        problema=p, D=D, M=M, maxfe=maxfe, n_linhas_1=len(real), n_init=n_init,
        n_iter=n_iter, n_infill=n_infill, cache_hits=n_cache, c0=c0, ledger_ok=ledger_ok,
        u1_len=u1_len, u1_dense=u1_dense, u1_sid_uniq=u1_sid_uniq, dupX=dupX,
        u2_ok=u2_ok, doe_dX=float(dX), doe_hash_ok=doe_hash_ok,
        termino=(ftr[0]['termino'] if ftr else None), status=man['status'],
        fe_final=man['fe_final'], cp_init=(ftr[0].get('cp_init') if ftr else None),
        cache_ok=cache_ok, n_dedup_guard=n_dedupg, dedup_total=int(it.n_dedup.sum()),
        # identidades
        gbest_ok_abs=int((it.d_gbest < 1e-6).sum()), gbest_naive_abs=int((it.d_gbest_naive < 1e-6).sum()),
        gbest_ok_rel=int((it.rel_gbest < 1e-6).sum()),
        gbest_max_abs=float(it.d_gbest.max()), gbest_max_rel=float(it.rel_gbest.max()),
        norm_ok=int(((it.d_nmin < 1e-5) & (it.d_nmax < 1e-5)).sum()),
        norm_naive_ok=int(((it.d_nmin_naive < 1e-5) & (it.d_nmax_naive < 1e-5)).sum()),
        norm_max_rel=float(np.maximum(it.d_nmin, it.d_nmax).max()),
        arq_ne_fe1=int((~it.arquivo_eq_fe_menos_1).sum()),
        na_eq_pop=int(it.na_eq_pop.sum()),
        ei_ok_rel=int((it.rel_ei < 1e-6).sum()), ei_ok_abs=int((it.d_ei < 1e-18).sum()),
        ei_max_rel=float(it.rel_ei.max()), ei_falhas_rel=int((it.rel_ei >= 1e-6).sum()),
        sid_match=int(it.sid_match.sum()), n_sid_check=int(it.sid_match.notna().sum()),
        subset_id_ok=int(it.subset_id.sum()), subset_ok=int(it.subset_ok.sum()),
        n_no_cap=int(it.no_cap.sum()), n_treino_max=int(it.n_treino.max()), cap=cap,
        ga_iters_ok=int(it.ga_iters_ok.sum()), ga_pop_delta_set=str(sorted(it.ga_pop_delta.unique())),
        ga_iters_min=int(it.ga_iters.min()), ga_iters_max=int(it.ga_iters.max()),
        theta_lo=float(it.theta_min.min()), theta_hi=float(it.theta_max.max()),
        theta_viol=int(((it.theta_min < 1e-5 - 1e-12) | (it.theta_max > 20 + 1e-9)).sum()),
        n_mse_neg=int(it.n_mse_neg.sum()), n_ei_nan=int(it.n_ei_nan.sum()), nan_guard=int(it.nan_guard.sum()),
        ftm_nao_monot=int((it.ftm_diff < 0).sum()),
        e0_ei_eq=int(it.ei_eq_min_e0.sum()), e0_monot=int(it.e0_monot.sum()),
        lam_grid_max=float(it.d_lambda_grid.max()), lam_distintos=len(set(lam_seen)), lam_N=Ngrid,
        lam_max_rep=int(pd.Series(lam_seen).value_counts().max()),
        dist_min_zero=int((it.dist_min_arquivo == 0).sum()),
        # (2)
        pop_gens=pop_gens, pop_gens_esperado=n_iter + 1, dup_last=dup_last,
        dup_last_ok=(dup_last == n_cache - 1), pop_size_ok=pop_size_ok, pop_linhas=len(pop),
        # (4)
        tim_linhas=len(tim), tim_ok=t_ok, tim_viol_sonda=t_viol_sonda,
        tim_viol_eq_sonda=(gens_viol == gens_sonda),
        n_gens_sonda=len(gens_sonda), sonda_cad_ok=cad_ok, Gmax=Gmax, Gmax_impar=(Gmax % 2 == 1),
        sonda_jsonl_ok=(sonda_gens_jsonl == gens_sonda),
        erro_fant_med=float(it.erro_fantasia.abs().median()),
        erro_fant_otimista=float((it.erro_fantasia < 0).mean()),
    ))
    print(f'{p:10s} D={D:2d} M={M} iters={n_iter:4d} EI_rel={int((it.rel_ei<1e-6).sum())}/{n_iter} '
          f'gbest={int((it.d_gbest<1e-6).sum())}/{n_iter} norm={int(((it.d_nmin<1e-5)&(it.d_nmax<1e-5)).sum())}/{n_iter} '
          f'cache={n_cache} c0={c0}')

pd.DataFrame(iters_rows).to_csv(f'{OUT}/b1_iters.csv', index=False)
cd = pd.DataFrame(cell_rows)
cd.to_csv(f'{OUT}/b1_celulas.csv', index=False)
print('\n=== TOTAIS ===')
print('celulas', len(cd), 'iteracoes', cd.n_iter.sum(), 'infills', cd.n_infill.sum(),
      'cache', cd.cache_hits.sum(), 'c0', cd.c0.sum())
print('EI rel<1e-6:', cd.ei_ok_rel.sum(), '/', cd.n_iter.sum(), ' | abs<1e-18:', cd.ei_ok_abs.sum())
print('gbest abs<1e-6:', cd.gbest_ok_abs.sum(), ' naive(fe-1):', cd.gbest_naive_abs.sum(), ' rel<1e-6:', cd.gbest_ok_rel.sum())
print('norm:', cd.norm_ok.sum(), ' naive:', cd.norm_naive_ok.sum())
print('ledger ok:', cd.ledger_ok.sum(), '/', len(cd))
