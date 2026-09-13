#!/usr/bin/env python
"""B5 — U5/U6 (regua Sobol: join posicional + WAPE/cobertura), E8/E10/E12/E14, A2 (colapso do GA),
e saude (IGD+/HV) do smoke; tudo espelhado contra a celula homologa da rodada-42.
"""
import json, hashlib, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
GAB = f'{ROOT}/data/sonda/sonda_MMF1.parquet'
CASES = {
    'T11_smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42',
    'R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42/exp_main_c238_MMF1_42',
}

gab = pq.read_table(GAB).to_pandas()
print('gabarito da sonda:', GAB, gab.shape, list(gab.columns)[:12])
Xg = gab[[c for c in gab.columns if c.startswith('x')]].to_numpy(np.float64)
Fg = gab[[c for c in gab.columns if c.startswith('f')]].to_numpy(np.float64)
S_ONLINE = 2000  # recorte online do gabarito (o manifesto carimba SO estas linhas)
hx = hashlib.sha256(np.ascontiguousarray(Xg[:S_ONLINE]).tobytes()).hexdigest()
hf = hashlib.sha256(np.ascontiguousarray(Fg[:S_ONLINE]).tobytes()).hexdigest()
print('  sha256(X)=%s\n  sha256(F)=%s' % (hx, hf))

for tag, b in CASES.items():
    print('\n' + '=' * 88)
    print('###', tag)
    man = json.load(open(f'{b}.manifest.json'))
    recs = [json.loads(l) for l in open(f'{b}.jsonl')]
    g = [r for r in recs if r.get('rec') == 'c238_gen']
    print('  manifest.sonda.x_hash == sha256(X do gabarito)?', man['sonda']['x_hash'] == hx,
          ' f_hash?', man['sonda']['f_hash'] == hf)
    sur = pq.read_table(f'{b}__surrogate.parquet').to_pandas()
    sb = sur[sur.regime == 'sonda']
    print('  regimes:', sur.regime.value_counts().to_dict(),
          ' sonda_estratificada presente?', 'sonda_estratificada' in set(sur.regime))

    # --- U5 join posicional
    dmax = 0.0
    for gg, sub in sb.groupby('geracao'):
        Xs = sub[['x0', 'x1']].to_numpy(np.float64)
        dmax = max(dmax, float(np.abs(Xs - Xg[:len(Xs)]).max()))
    print('  U5 join posicional: max|dX| sonda x gabarito em %d blocos = %.4g' % (sb.geracao.nunique(), dmax))

    # --- espacos misturados (armadilha 2 da F5)
    on = sur[sur.regime == 'online']
    print('  espaco_modelo: sonda=%s  online=%s' % (sb.espaco_modelo.unique().tolist(), on.espaco_modelo.unique().tolist()))
    print('  transf_tipo  : sonda=%s  online=%s' % (sb.transf_tipo.unique().tolist(), on.transf_tipo.unique().tolist()))
    print('  transf_params NULL na sonda? %s' % sb.transf_params.isna().all())

    # --- U6 WAPE + cobertura no espaco CRU (sonda ja vem crua)
    rows = []
    for gg, sub in sb.groupby('geracao'):
        mu = sub[['mu_0', 'mu_1']].to_numpy(np.float64)
        sg = sub[['sigma_0', 'sigma_1']].to_numpy(np.float64)
        f = Fg[:len(sub)]
        for j in range(2):
            w = np.abs(mu[:, j] - f[:, j]).sum() / np.abs(f[:, j]).sum()
            cov = float((np.abs(mu[:, j] - f[:, j]) <= 1.96 * sg[:, j]).mean())
            cor = float(np.corrcoef(mu[:, j], f[:, j])[0, 1])
            rows.append(dict(geracao=gg, obj=j, WAPE=w, cob=cov, correl=cor,
                             mu_absmax=float(np.abs(mu[:, j]).max()),
                             n_validas=int(np.isfinite(sg[:, j]).sum()),
                             sig_nan=int((~np.isfinite(sg[:, j])).sum())))
    S = pd.DataFrame(rows)
    S.to_csv(f'{ROOT}/f5/t11/baterias/c238/sonda_{tag}.csv', index=False)
    for j in range(2):
        s = S[S.obj == j].sort_values('geracao')
        print('  U6 obj%d: WAPE %0.4f -> %0.4f  | cob %0.3f -> %0.3f | corr %0.3f -> %0.3f | |mu|max=%0.4g | sigma-NaN=%d'
              % (j, s.WAPE.iloc[0], s.WAPE.iloc[-1], s.cob.iloc[0], s.cob.iloc[-1],
                 s.correl.iloc[0], s.correl.iloc[-1], s.mu_absmax.max(), s.sig_nan.sum()))
    print('  n_validas por bloco: %s (esperado 2000)' % sorted(S.n_validas.unique()))

    # --- E8 declarativo
    print('  E8 modelo_flag: %s (n=%d, 100%%? %s)' % (sur.modelo_flag.unique().tolist(), len(sur),
          sur.modelo_flag.nunique() == 1))
    print('     pred_tipo=%s pred_classe NULL=%s pred_score NULL=%s pred_confianca NULL=%s ; sigma nulos=%d'
          % (sur.pred_tipo.unique().tolist(), sur.pred_classe.isna().all(), sur.pred_score.isna().all(),
             sur.pred_confianca.isna().all(), int(sur[['sigma_0', 'sigma_1']].isna().sum().sum())))

    # --- E10/E12/E14
    print('  E10 ga_pop=%s ga_gens=%s -> aval/iter=%d ; total=%d'
          % (sorted({r['ga_pop'] for r in g}), sorted({r['ga_gens'] for r in g}),
             g[0]['ga_pop'] * g[0]['ga_gens'], sum(r['ga_pop'] * r['ga_gens'] for r in g)))
    print('  E11 linhas de pool por geracao: %s (esperado 10D=%d) ; total=%d'
          % (sorted(on.groupby('geracao').size().unique()), 10 * 2, len(on)))
    print('  E12 criterion no evento: %s (%d/%d)'
          % (sorted({r['criterion'] for r in g}), sum(1 for r in g if r['criterion'] == 'Euclidean'), len(g)))
    print('     header.criterion=%r ; params.criterion=%r' % (recs[0]['criterion'], man['params']['criterion']))
    print('  E14 guards: n_eim_nan=%d n_range0=%d n_dedup=%d ; n_front min=%d (n_front==1 em %d gens)'
          % (sum(r['n_eim_nan'] for r in g), sum(r['n_range0'] for r in g), sum(r['n_dedup'] for r in g),
             min(r['n_front'] for r in g), sum(1 for r in g if r['n_front'] == 1)))
    print('     range efetivo min=%.4g (eps=%.3g)' % (min(min(r['norm_range_efetivo']) for r in g), np.finfo(float).eps))

    # --- A2 colapso do GA em D=2
    real = pq.read_table(f'{b}__real.parquet').to_pandas()
    tot_rsid = int(on.real_solution_id.notna().sum())
    de_antigo = 0; ident = 0; tot = 0
    for gg, sub in on.groupby('geracao'):
        r = [x for x in g if x['geracao'] == gg][0]
        sid = r['infill_sid']
        v = sub.real_solution_id.dropna().astype(int)
        de_antigo += int((v != sid).sum())
        xw = real.loc[real.solution_id == sid, ['x0', 'x1']].to_numpy(np.float32)[0]
        Xp = sub[['x0', 'x1']].to_numpy(np.float32)
        ident += int((Xp == xw).all(1).sum()); tot += len(sub)
    print('  A2 real_solution_id no pool: %d de %d linhas ; apontando p/ ponto ANTIGO: %d'
          % (tot_rsid, len(on), de_antigo))
    print('     X bit-identico ao vencedor: %d de %d (%.1f%%) -> colapso do GA interno em D=2'
          % (ident, tot, 100 * ident / tot))

    # --- saude: IGD+ / HV com src/metrics.py
    sys.path.insert(0, ROOT)
    try:
        from src import metrics as MT
        from src import problems as PB
        print('  metrics disponivel:', [x for x in dir(MT) if 'igd' in x.lower() or 'hv' in x.lower()][:8])
    except Exception as e:
        print('  metrics indisponivel:', repr(e))
