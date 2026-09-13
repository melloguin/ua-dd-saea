"""Bateria b1 - parte 3: a (3) inteira.
(a) online: rows/gen == ga_pop, nao-greedy (argmax-EI != argmin-mu), sigma<0/==0,
    real_solution_id, mu_1../sigma_1.. NULL (D47), literais.
(b) sonda: join posicional contra o artefato (max|dX|), reconstrucao do gabarito
    ESCALAR PCheby com o transf_params do PROPRIO bloco, WAPE/corr/cobertura por bloco.
Saidas: b1_sonda_blocos.csv (1 linha/bloco) + b1_surrogate.csv (1 linha/celula)
        + b1_nao_greedy.csv (1 linha/iteracao)
"""
import json, os
import numpy as np, pandas as pd
import pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])

blk_rows, cell_rows, ng_rows = [], [], []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    D, M = hdr['D'], hdr['M']
    xc = [f'x{i}' for i in range(D)]
    sch = pq.read_schema(base + '__surrogate.parquet')
    names = sch.names
    mucols = [c for c in names if c.startswith('mu_')]
    sgcols = [c for c in names if c.startswith('sigma_')]
    lit = ['pred_tipo', 'pred_classe', 'pred_score', 'pred_confianca', 'modelo_flag',
           'espaco_modelo', 'transf_tipo']
    cols = ['regime', 'geracao', 'real_solution_id', 'fe_treino_max', 'transf_params'] + mucols + sgcols + lit
    sur = pq.read_table(base + '__surrogate.parquet', columns=cols).to_pandas()
    n_tot = len(sur)
    on = sur[sur.regime == 'online']
    so = sur[sur.regime == 'sonda']
    # literais
    litvals = {c: sorted(map(str, sur[c].dropna().unique().tolist()))[:3] for c in lit}
    n_null_lit = {c: int(sur[c].isna().sum()) for c in lit}
    # D47: mu_1.., sigma_1.. 100% NULL
    extra_mu = [c for c in mucols if c != 'mu_0']
    extra_sg = [c for c in sgcols if c != 'sigma_0']
    d47_null = all(sur[c].isna().all() for c in extra_mu + extra_sg)
    n_extra = len(extra_mu) + len(extra_sg)
    # guards P2
    n_sig_neg = int((sur.sigma_0 < 0).sum())
    n_sig_zero = int((sur.sigma_0 == 0).sum())
    n_mu_nan = int(sur.mu_0.isna().sum())
    n_sig_nan = int(sur.sigma_0.isna().sum())
    sig_min = float(sur.sigma_0.min())
    # rows/gen == ga_pop
    gp = {e['geracao']: e['ga_pop'] for e in ge}
    mub = {e['geracao']: e['mu_best'] for e in ge}
    eib = {e['geracao']: e['ei_best'] for e in ge}
    sizes = on.groupby('geracao').size()
    ok_pop = int(sum(1 for g, n in sizes.items() if gp.get(int(g)) == n))
    # nao-greedy: existe no pool final mu < mu_best?
    gmin = on.groupby('geracao').mu_0.min()
    ng_ok = 0
    for g, mn in gmin.items():
        g = int(g)
        mb = mub[g]
        tol = 1e-6 * max(abs(mb), 1.0)
        isng = bool(mn < mb - tol)
        ng_ok += isng
        ng_rows.append(dict(problema=p, geracao=g, mu_best=mb, mu_min_pool=float(mn),
                            nao_greedy=isng, gap=float(mb - mn)))
    frac_ng = ng_ok / len(gmin)
    # real_solution_id na busca
    rsid_frac = float(on.real_solution_id.notna().mean())
    # fe_treino_max preenchido
    ftm_on_null = int(on.fe_treino_max.isna().sum())

    # ---------- SONDA ----------
    art = pq.read_table(f'{ART}/sonda_{p}.parquet').to_pandas()
    fcs = [c for c in art.columns if c.startswith('f')]
    Fg = art[fcs].values[:2000].astype(np.float64)
    Xg = art[xc].values[:2000].astype(np.float32)
    # join posicional: X do bloco vs artefato
    sx = pq.read_table(base + '__surrogate.parquet', columns=['regime'] + xc).to_pandas()
    sx = sx[sx.regime == 'sonda']
    XS = sx[xc].values.astype(np.float32)
    nb = len(XS) // 2000
    dX = float(np.abs(XS.reshape(nb, 2000, D) - Xg[None]).max()) if nb else np.nan
    del sx, XS
    gens = list(dict.fromkeys(so.geracao.astype(int).tolist()))
    for gi, g in enumerate(gens):
        b = so[so.geracao == g]
        tp = json.loads(b.transf_params.iloc[0]) if isinstance(b.transf_params.iloc[0], str) else b.transf_params.iloc[0]
        lam = np.array(tp['lambda'], float); mn = np.array(tp['min'], float); mx = np.array(tp['max'], float)
        rng = np.where(mx - mn == 0, 1.0, mx - mn)
        Fn = (Fg - mn) / rng
        pc = (Fn * lam).max(1) + 0.05 * (Fn * lam).sum(1)
        mu = b.mu_0.values.astype(np.float64); sg = b.sigma_0.values.astype(np.float64)
        err = np.abs(mu - pc)
        wape = err.sum() / max(np.abs(pc).sum(), 1e-30)
        cov = float((err <= 1.96 * sg).mean())
        cor = float(np.corrcoef(mu, pc)[0, 1]) if np.std(mu) > 0 and np.std(pc) > 0 else np.nan
        blk_rows.append(dict(problema=p, D=D, M=M, bloco=gi + 1, geracao=g, n=len(b),
                             wape=float(wape), cobertura=cov, corr=cor,
                             sigma_med=float(np.median(sg)), gbest_bloco=float(tp.get('gbest', np.nan)),
                             erro_med=float(np.median(err)), pc_med=float(np.median(pc)),
                             tp_ok=set(tp.keys()) >= {'lambda', 'min', 'max'}))
    bb = pd.DataFrame([r for r in blk_rows if r['problema'] == p])
    cell_rows.append(dict(problema=p, D=D, M=M, n_linhas_3=n_tot, n_online=len(on), n_sonda=len(so),
                          n_blocos=len(gens), blocos_2000=int((bb.n == 2000).sum()),
                          d47_null=d47_null, n_extra_cols=n_extra,
                          n_sig_neg=n_sig_neg, n_sig_zero=n_sig_zero, sig_min=sig_min,
                          n_mu_nan=n_mu_nan, n_sig_nan=n_sig_nan,
                          rows_gen_ok=ok_pop, n_gens=len(sizes),
                          frac_nao_greedy=frac_ng, n_nao_greedy=ng_ok,
                          rsid_frac=rsid_frac, ftm_on_null=ftm_on_null,
                          sonda_dX=dX,
                          wape_1=float(bb.wape.iloc[0]), wape_last=float(bb.wape.iloc[-1]),
                          corr_1=float(bb['corr'].iloc[0]), corr_last=float(bb['corr'].iloc[-1]),
                          cob_1=float(bb.cobertura.iloc[0]), cob_last=float(bb.cobertura.iloc[-1]),
                          cob_med=float(bb.cobertura.median()),
                          lit=json.dumps(litvals), lit_null=json.dumps(n_null_lit)))
    print(f'{p:10s} 3={n_tot:8d} on={len(on):8d} sonda={len(so):7d} blocos={len(gens):4d} '
          f'dX={dX:.3g} pop_ok={ok_pop}/{len(sizes)} NG={frac_ng:.3f} '
          f'WAPE {bb.wape.iloc[0]:.3f}->{bb.wape.iloc[-1]:.3f} cob {bb.cobertura.iloc[0]:.2f}->{bb.cobertura.iloc[-1]:.2f} '
          f'signeg={n_sig_neg} sigzero={n_sig_zero} D47={d47_null}')
    del sur, on, so

pd.DataFrame(blk_rows).to_csv(f'{OUT}/b1_sonda_blocos.csv', index=False)
cd = pd.DataFrame(cell_rows); cd.to_csv(f'{OUT}/b1_surrogate.csv', index=False)
pd.DataFrame(ng_rows).to_csv(f'{OUT}/b1_nao_greedy.csv', index=False)
print()
print('linhas (3) total', cd.n_linhas_3.sum(), 'online', cd.n_online.sum(), 'sonda', cd.n_sonda.sum(),
      'blocos', cd.n_blocos.sum())
print('sigma<0', cd.n_sig_neg.sum(), 'sigma==0', cd.n_sig_zero.sum(), 'mu NaN', cd.n_mu_nan.sum(),
      'sigma NaN', cd.n_sig_nan.sum())
print('D47 null em', cd.d47_null.sum(), '/23')
print('rows/gen==ga_pop', cd.rows_gen_ok.sum(), '/', cd.n_gens.sum())
print('nao-greedy: mediana', cd.frac_nao_greedy.median(), 'min', cd.frac_nao_greedy.min(), 'max', cd.frac_nao_greedy.max(),
      'total', cd.n_nao_greedy.sum())
print('join sonda max|dX|', cd.sonda_dX.max())
print('cobertura 1o bloco mediana', cd.cob_1.median(), '-> ultimo', cd.cob_last.median())
