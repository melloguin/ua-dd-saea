#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""F5.3a e81 — bateria em escala nas 30 células (READ-ONLY)."""
import json, sys, os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src.experiment import _instantiate_problem

BASE = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81'
MAIN = ['MMF1','MMF4','MMF11_L','MMF16_20','ZDT1','ZDT3','ZDT4','ZDT6','DTLZ1','DTLZ2',
        'DTLZ3','DTLZ4','DTLZ7','WFG1','WFG2','WFG4','WFG5','WFG9','BBOB_F1','BBOB_F5',
        'BBOB_F17','BBOB_F22','BBOB_F37','BBOB_F49','BBOB_F55']
BATCH = ['DTLZ2','MMF16_20','WFG9','ZDT1','ZDT4']

bounds_cache = {}
def get_bounds(p):
    if p not in bounds_cache:
        prob = _instantiate_problem(p)
        bounds_cache[p] = (np.asarray(prob.xl, float), np.asarray(prob.xu, float))
    return bounds_cache[p]

rows = []
for exp, plist, prefix in [('main', MAIN, ''), ('batch', BATCH, 'q10_')]:
    for p in plist:
        d = f'{BASE}/{prefix}{p}/42'
        stem = f'{d}/exp_{exp}_e81_{p}_42'
        man = json.load(open(stem + '.manifest.json'))
        real = pd.read_parquet(stem + '__real.parquet').sort_values('fe_index').reset_index(drop=True)
        D = sum(c.startswith('x') and c[1:].isdigit() for c in real.columns)
        M = sum(c.startswith('f') and c[1:].isdigit() for c in real.columns)
        xcols = [f'x{i}' for i in range(D)]; fcols = [f'f{j}' for j in range(M)]
        xl, xu = get_bounds(p)

        # ---- jsonl ----
        decs, fits, sondas, footers, header = [], [], [], [], None
        bad = 0
        for line in open(stem + '.jsonl'):
            try: r = json.loads(line)
            except Exception: bad += 1; continue
            rec = r.get('rec')
            if rec == 'decision': decs.append(r)
            elif rec == 'fit': fits.append(r)
            elif rec == 'sonda': sondas.append(r)
            elif rec == 'footer': footers.append(r)
            elif rec == 'header': header = r
        frun = next((f for f in footers if 'fe_final' in f), {})

        q = man.get('q') or decs[0]['q']
        G = len(decs)
        exp_fe = 31*D-1 if exp == 'main' else (11*D-1) + 2000
        exp_init = 11*D-1
        exp_gens = 20*D if exp == 'main' else 200

        # ---- surrogate (busca only) ----
        sur = pd.read_parquet(stem + '__surrogate.parquet',
                              filters=[('regime', '=', 'online')])
        sur = sur.reset_index(drop=True)
        gsz = sur.groupby('geracao').size()

        # per-decision checks
        fe_seq = [dd['fe'] for dd in decs]
        c = dict(
            exp=exp, problema=p, D=D, M=M, q=q,
            status=man['status'], motivo=man.get('motivo_parada'),
            n_retries=man.get('n_retries'), fallback_ativado=man.get('fallback_ativado'),
            jsonl_bad=bad,
            # U1/B1
            fe_ok=(len(real) == exp_fe == man['fe_final'] == frun.get('fe_final')),
            fe_dense=bool((real.fe_index.values == np.arange(len(real))).all()),
            # B2
            init_ok=((real.fase == 'init').sum() == exp_init and frun.get('cp_init') is True),
            # B3/U3
            gens=G, gens_ok=(G == exp_gens == man.get('n_geracoes') == frun.get('n_geracoes')),
            fits_eq_gens=(len(fits) == G),
            ntreino_step_ok=all(b['n_treino'] - a['n_treino'] == q for a, b in zip(fits, fits[1:])),
            ntreino_first=fits[0]['n_treino'], ntreino_last=fits[-1]['n_treino'],
            # B18/U8
            fetm_mono=bool(np.all(np.diff([f['fe_treino_max'] for f in fits]) >= 0)),
            fetm_min=min(f['fe_treino_max'] for f in fits), fetm_max=max(f['fe_treino_max'] for f in fits),
            # B5/U10
            fe_eq_ntrain_q=all(dd['fe'] == dd['n_train'] + dd['q'] for dd in decs),
            fe_increasing=bool(np.all(np.diff(fe_seq) > 0)),
            # B9/B10
            ngen10=all(dd['ngen'] == 10 for dd in decs),
            draws_ok=all(dd['draws_thompson']['n_chamadas'] == 10 and
                         dd['draws_thompson']['n_pontos'] == 100*D*10 for dd in decs),
            pop_ok=(man['params']['nsga2_interno']['pop'] == 100*D and
                    man['params']['nsga2_interno']['n_gen'] == 10),
            # B11/B12
            kernel_ok=all(f['kernel'] == 'get_matern_kernel_with_gamma_prior(D)' for f in fits),
            yvar_ok=all(dd['modelo_hp']['train_Yvar'] == 1e-12 for dd in decs),
            flag=sur.modelo_flag.iloc[0], espaco=sur.espaco_modelo.iloc[0] if 'espaco_modelo' in sur else None,
            # ARD alive (B4/B11): lengthscales distinct within gen + moving between gens
            hp_moves=float(np.mean([decs[i]['modelo_hp']['por_objetivo'][0]['lengthscale_med'] !=
                                    decs[i-1]['modelo_hp']['por_objetivo'][0]['lengthscale_med']
                                    for i in range(1, G)])),
            ard_ok=all(dd['modelo_hp']['por_objetivo'][0]['lengthscale_min'] !=
                       dd['modelo_hp']['por_objetivo'][0]['lengthscale_max'] for dd in decs) if D > 1 else None,
            # B15
            assert_ok=all(dd['assert_lote_eq_q'] for dd in decs),
            nlote_ok=all(dd['n_lote'] == q for dd in decs),
            lote_menor=frun.get('n_lote_menor'), lote_comp=frun.get('n_lote_completado'),
            min_front_acq=min(dd['n_front_acq'] for dd in decs),
            # B17
            seeds_ok=all(dd['seed_gp'] == 43024 + dd['iteracao'] and dd['seed_nsga2'] == 44430 for dd in decs),
            nystrom_ok=all(dd['nystrom'] == 0 for dd in decs),
            # U9
            cache_hits_dec=sum(bool(dd['cache_hit']) for dd in decs),
            cache_hits_footer=frun.get('cache_hits'), cache_hits_man=man.get('cache_hits'),
            fit_retries=sum(dd.get('fit_retries', 0) for dd in decs),
            # B8
            front_eq=int(sum(gsz.get(float(dd['geracao']), gsz.get(dd['geracao'], -1)) == dd['n_front_acq']
                             for dd in decs)),
            # B16 (via jsonl sonda recs)
            sonda_n=len(sondas),
            sonda_n_ok=(len(sondas) == man['sonda']['n_blocos'] == (exp_gens//2 + 1)),
            sonda_pts_ok=all(s['n_pontos'] == 2000 for s in sondas),
            sonda_hash_ok=all(s.get('hash_check', True) for s in sondas),
            sonda_gens_ok=(sorted(s['geracao'] for s in sondas) ==
                           sorted({1} | {g for g in range(2, exp_gens+1, 2)} | {exp_gens})),
        )

        # ---- query-joia: recompute maximin in [0,1]^D, ALL generations ----
        Xr = real[xcols].values.astype(np.float64)
        Xr01 = (Xr - xl) / (xu - xl)
        match_idx = match_val = match_rsid = 0
        max_dv = 0.0
        sur_g = {g: sub for g, sub in sur.groupby('geracao')}
        for dd in decs:
            g = dd['geracao']
            sub = sur_g.get(g, sur_g.get(float(g)))
            cand = sub[xcols].values.astype(np.float64)
            cand01 = (cand - xl) / (xu - xl)
            ds01 = Xr01[:dd['n_train']]
            dist = cdist(cand01, ds01).min(axis=1)
            order = np.argsort(dist, kind='stable')
            top = order[-q:]
            chosen_logged = dd['idx_escolhidos'] if isinstance(dd['idx_escolhidos'], list) else [dd['idx_escolhidos']]
            mm = dd['maximin_escolhido'] if isinstance(dd['maximin_escolhido'], list) else [dd['maximin_escolhido']]
            if set(top.tolist()) == set(chosen_logged): match_idx += 1
            dv = float(np.max(np.abs(np.sort(dist[chosen_logged]) - np.sort(np.asarray(mm)))))
            max_dv = max(max_dv, dv)
            if dv < 1e-4: match_val += 1
            pos_chosen = set(np.where(sub.real_solution_id.notna().values)[0].tolist())
            if pos_chosen == set(chosen_logged): match_rsid += 1
        c.update(qj_idx=match_idx, qj_val=match_val, qj_rsid=match_rsid, qj_maxdiff=max_dv)

        # ---- U11/B13 fantasy error (all infills) ----
        ch = sur[sur.real_solution_id.notna()]
        j = ch.merge(real[['solution_id'] + fcols], left_on='real_solution_id',
                     right_on='solution_id', suffixes=('', '_r'))
        errs = [float(np.median(np.abs(j[f'mu_{k}'] - j[f'f{k}']))) for k in range(M)]
        c.update(n_infill_rows=len(ch), fantasy_med=[round(e, 4) for e in errs],
                 sigma_pos=bool((sur[[f'sigma_{k}' for k in range(M)]].notna().all().all())))

        # ---- U7 timing ----
        tm = pd.read_parquet(stem + '__timing.parquet')
        v1 = int((tm.tempo_fit_s + tm.tempo_busca_s > tm.tempo_geracao_s).sum())
        with_sonda = tm[tm.tempo_pred_sonda_s > 0]
        v2 = int((with_sonda.tempo_fit_s + with_sonda.tempo_busca_s + with_sonda.tempo_pred_sonda_s
                  > with_sonda.tempo_geracao_s).sum())
        c.update(timing_rows_ok=(len(tm) == G), t_inv1_viol=v1,
                 t_sonda_gens=len(with_sonda), t_inv2_hold=v2)

        rows.append(c)
        print(f"[{exp}/{p}] done", file=sys.stderr)

df = pd.DataFrame(rows)
pd.set_option('display.width', 250, 'display.max_columns', 100)
out = '/private/tmp/claude-501/-Users-gmello/c7372206-5092-4c09-9686-ccae3785ca0c/scratchpad/e81_scale_results.csv'
df.to_csv(out, index=False)
print(df.to_string())
print('\n=== AGREGADOS ===')
bools = [c for c in df.columns if df[c].dtype == bool]
for c in bools:
    print(f'{c}: {int(df[c].sum())}/30 true')
print('gens total:', df.gens.sum(),
      '| qj_idx:', df.qj_idx.sum(), '| qj_val:', df.qj_val.sum(),
      '| qj_rsid:', df.qj_rsid.sum(), '| qj_maxdiff global:', df.qj_maxdiff.max())
print('front_eq total:', df.front_eq.sum())
print('cache_hits (dec/footer/man):', df.cache_hits_dec.sum(), df.cache_hits_footer.sum(), df.cache_hits_man.sum())
print('lote_menor/comp:', df.lote_menor.sum(), df.lote_comp.sum(), '| min_front_acq por exp:')
print(df.groupby('exp').min_front_acq.min())
print('t_inv1_viol total:', df.t_inv1_viol.sum(), '| sonda-gens:', df.t_sonda_gens.sum(), '| inv2 hold:', df.t_inv2_hold.sum())
print('fit_retries total:', df.fit_retries.sum(), '| jsonl_bad:', df.jsonl_bad.sum())
print('hp_moves min:', df.hp_moves.min())
