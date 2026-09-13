#!/usr/bin/env python
"""C1 — RE-MEDICAO do mecanismo do c238 sobre TODAS as 25 celulas da rodada-42.
Query-joia (identidade EIMe do Apendice A), contrafactual sigma->0, N2, amostragem
densa (E5), saturacao (E6), re-scaling (E7), ledger pos-infill (A1), U11, semantica ND.
READ-ONLY sobre resultados_experimentos/. Escreve so em f5/t11/baterias/c238/.
"""
import json, os, sys, time
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import norm

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'


def nd_std(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y <= Y[i]).all(1) & (Y < Y[i]).any(1)).any():
            keep[i] = False
    return keep


def nd_weak_seq(Y):
    """paretofront (FEX-17251): dominancia FRACA com varredura sequencial."""
    n = len(Y); front = np.ones(n, bool)
    for i in range(n):
        if not front[i]:
            continue
        tail = Y[i + 1:]; alive = front[i + 1:]
        if len(tail) == 0:
            continue
        d_ij = (Y[i] <= tail).all(1) & alive
        d_ji = (tail <= Y[i]).all(1) & alive
        idx = np.flatnonzero(d_ji & ~d_ij)
        if idx.size:
            k = idx[0]
            front[i + 1 + np.flatnonzero(d_ij[:k])] = False
            front[i] = False
        else:
            front[i + 1 + np.flatnonzero(d_ij)] = False
    return front


def nd_strict_count(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y < Y[i]).all(1)).any():
            keep[i] = False
    return int(keep.sum())


def eim_euclidean(u, s, Fr):
    lam = (Fr[None, :, :] - u[:, None, :]) / s[:, None, :]
    E = (Fr[None, :, :] - u[:, None, :]) * norm.cdf(lam) + s[:, None, :] * norm.pdf(lam)
    E = np.nan_to_num(E, nan=0.0)
    return np.sqrt((E ** 2).sum(2)).min(1)


def improvement_only(u, Fr):
    E = np.maximum(Fr[None, :, :] - u[:, None, :], 0.0)
    return np.sqrt((E ** 2).sum(2)).min(1)


def do(prob):
    b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
    recs = [json.loads(l) for l in open(f'{b}.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    M, D = hdr['M'], hdr['D']
    gens = {r['geracao']: r for r in recs if r.get('rec') == 'c238_gen'}
    real = pq.read_table(f'{b}__real.parquet').to_pandas()
    F = real[[f'f{i}' for i in range(M)]].values.astype(np.float64)
    X = real[[f'x{i}' for i in range(D)]].values.astype(np.float64)
    cols = ['regime', 'geracao', 'real_solution_id'] + [f'mu_{i}' for i in range(M)] + \
           [f'sigma_{i}' for i in range(M)] + [f'x{i}' for i in range(D)]
    sur = pq.read_table(f'{b}__surrogate.parquet', columns=cols).to_pandas()
    on = sur[sur.regime == 'online']
    grp = dict(list(on.groupby('geracao')))
    rows = []
    for g in sorted(gens):
        r = gens[g]
        npre = r['n_amostra']
        Y = F[:npre]
        mask = nd_weak_seq(Y)
        n_lo = int(nd_std(Y).sum()); nstrict = nd_strict_count(Y)
        mn = np.array(r['norm_min'], float); rg = np.array(r['norm_range_efetivo'], float)
        Fr = (Y[mask] - mn) / rg
        sub = grp[g]
        u = sub[[f'mu_{i}' for i in range(M)]].values.astype(np.float64)
        s = sub[[f'sigma_{i}' for i in range(M)]].values.astype(np.float64)
        v = eim_euclidean(u, s, Fr)
        rsid = sub.real_solution_id.values
        pos = np.where(rsid == r['infill_sid'])[0]
        j = int(pos[0]) if len(pos) else int(np.argmax(v))
        eb = r['eim_best']; den = max(abs(eb), 1e-300); vmax = float(v.max())
        v0 = improvement_only(u, Fr)
        muda = int(np.argmax(v0)) != int(np.argmax(v))
        v_up = eim_euclidean(u, s * 1.01, Fr)
        n2_ok = bool((v_up >= v - 1e-12).all())
        lam = (Fr - u[j]) / s[j]
        Ecomp = (Fr - u[j]) * norm.cdf(lam) + s[j] * norm.pdf(lam)
        Ecomp = np.nan_to_num(Ecomp, nan=0.0)
        nrm = np.sqrt((Ecomp ** 2).sum(1)); k = int(np.argmin(nrm))
        expl = float(np.sqrt(((s[j] * norm.pdf(lam[k])) ** 2).sum()) / max(nrm[k], 1e-300))
        x_inf = X[int(r['infill_sid'])]
        dmin = float(np.sqrt(((X[:npre] - x_inf) ** 2).sum(1)).min())
        old = set(np.arange(npre).tolist())
        coinc = int(sum(1 for q in rsid if pd.notna(q) and int(q) in old))
        mu_cru = u[j] * rg + mn; s_cru = s[j] * rg; f_real = F[int(r['infill_sid'])]
        rows.append(dict(
            problema=prob, geracao=g, D=D, M=M, n_amostra=npre,
            n_front=r['n_front'], nd_weak=int(mask.sum()), nd_std=n_lo, nd_strict=nstrict,
            front_exato=int(int(mask.sum()) == r['n_front']),
            front_bracket=int(min(n_lo, int(mask.sum())) <= r['n_front'] <= nstrict),
            eim_best=eb, eim_rec_max=vmax, abs_max=abs(vmax - eb), rel_max=abs(vmax - eb) / den,
            argmax_eh_infill=int(int(np.argmax(v)) == j),
            gap_argmax=(vmax - v[j]) / max(vmax, 1e-300),
            eim_med_rec=float(np.median(v)), eim_med_log=r['eim_mediana_pool'],
            rel_med=abs(np.median(v) - r['eim_mediana_pool']) / max(abs(r['eim_mediana_pool']), 1e-300),
            pool_n=len(sub), pool_med_sobre_max=float(np.median(v) / max(vmax, 1e-300)),
            pool_min_sobre_max=float(v.min() / max(vmax, 1e-300)),
            sigma0_muda_argmax=int(muda), n2_ok=int(n2_ok), frac_exploracao=expl,
            min_dist_log=r['min_dist_infill'], min_dist_rec=dmin,
            pool_coincide_antigo=coinc,
            eim_zero=int(eb == 0.0), s_best_min=float(s[j].min()),
            lam_abs_max=float(np.abs(lam).max()),
            u11_otimista=int((mu_cru < f_real).sum()),
            u11_cob=int((np.abs(mu_cru - f_real) <= 1.96 * s_cru).sum()),
            u11_err_modelo=float(np.max(np.abs(u[j] - (f_real - mn) / rg))),
            norm_min_ok=float(np.max(np.abs(np.array(r['norm_min']) - Y.min(0)) / np.maximum(np.abs(Y.min(0)), 1e-12))),
            norm_max_ok=float(np.max(np.abs(np.array(r['norm_max']) - Y.max(0)) / np.maximum(np.abs(Y.max(0)), 1e-12))),
            range_ok=float(np.max(np.abs(np.array(r['norm_range_efetivo']) -
                                         np.maximum(np.array(r['norm_max']) - np.array(r['norm_min']), np.finfo(float).eps)))),
            n_eim_nan=r.get('n_eim_nan'), n_range0=r.get('n_range0'), n_dedup=r.get('n_dedup'),
            fe_treino_max=r.get('fe_treino_max'), n_treino=r.get('n_treino'),
            ga_pop=r.get('ga_pop'), ga_gens=r.get('ga_gens'), criterion=r.get('criterion'),
        ))
    df = pd.DataFrame(rows)
    gl = [gens[g] for g in sorted(gens)]
    fb = np.array([r['f_best'] for r in gl], float)
    nm = np.array([r['norm_min'] for r in gl], float)
    nf1 = np.array([r['n_front1'] for r in gl]); nf = np.array([r['n_front'] for r in gl])
    a1_f = int((fb[:-1] == nm[1:]).all(1).sum()); a1_n = int((nf1[:-1] == nf[1:]).sum())
    df['a1_f'] = a1_f; df['a1_n'] = a1_n; df['a1_den'] = len(gl) - 1
    return df


if __name__ == '__main__':
    probs = sorted(os.listdir(S42))
    outs = []
    for p in probs:
        t0 = time.time()
        try:
            d = do(p); outs.append(d)
            print('%-10s gens=%4d  |D|<1e-5 %4d/%4d  argmax==infill %4d  s0muda %4d  N2 %4d  eim0 %3d  (%.0fs)' % (
                p, len(d), (d.abs_max < 1e-5).sum(), len(d), d.argmax_eh_infill.sum(),
                d.sigma0_muda_argmax.sum(), d.n2_ok.sum(), d.eim_zero.sum(), time.time() - t0), flush=True)
        except Exception as e:
            print(f'{p} FALHOU {e!r}', flush=True)
    A = pd.concat(outs)
    A.to_csv(f'{OUT}/mecanismo_s42.csv', index=False)
    n = len(A)
    print('\n' + '=' * 90)
    print('TOTAL geracoes = %d  (celulas=%d)' % (n, A.problema.nunique()))
    print('E1 identidade EIMe |D|<1e-5 : %d/%d   med=%.3g p99=%.3g max=%.3g' % (
        (A.abs_max < 1e-5).sum(), n, A.abs_max.median(), A.abs_max.quantile(.99), A.abs_max.max()))
    print('E1 relativo rel<1e-5        : %d/%d   (so gens de frente EXATA: %d/%d)' % (
        (A.rel_max < 1e-5).sum(), n,
        ((A.rel_max < 1e-5) & (A.front_exato == 1)).sum(), (A.front_exato == 1).sum()))
    print('E2 argmax==infill           : %d/%d (%.1f%%)  gap<1e-6 em %d  max gap=%.3g' % (
        A.argmax_eh_infill.sum(), n, 100 * A.argmax_eh_infill.mean(), (A.gap_argmax < 1e-6).sum(), A.gap_argmax.max()))
    print('E2 pool achatado med/max    : mediana=%.6f  p05=%.6f  min/max mediana=%.6f' % (
        A.pool_med_sobre_max.median(), A.pool_med_sobre_max.quantile(.05), A.pool_min_sobre_max.median()))
    print('E3 sigma->0 muda argmax     : %d/%d (%.1f%%)' % (
        A.sigma0_muda_argmax.sum(), n, 100 * A.sigma0_muda_argmax.mean()))
    print('E3 N2 vale                  : %d/%d' % (A.n2_ok.sum(), n))
    print('E3 frac exploracao mediana por celula: %.4f' % A.groupby('problema').frac_exploracao.median().median())
    print('E4 front exato / bracket    : %d / %d  de %d' % (A.front_exato.sum(), A.front_bracket.sum(), n))
    print('   discordantes por celula  :', A[A.front_exato == 0].problema.value_counts().to_dict())
    print('E5 min_dist_infill min glob : %.4g  gens<1e-8: %d  pool coincidindo c/ ANTIGO: %d de %d linhas' % (
        A.min_dist_log.min(), int((A.min_dist_log < 1e-8).sum()), A.pool_coincide_antigo.sum(), A.pool_n.sum()))
    print('   min_dist logado==recomputado max|D| = %.3g' % (A.min_dist_log - A.min_dist_rec).abs().max())
    print('E6 eim_best==0 EXATO        : %d gens  ->' % A.eim_zero.sum(), A[A.eim_zero == 1].problema.value_counts().to_dict())
    print('E7 rescaling desvio rel max : norm_min=%.3g norm_max=%.3g ; guard range max|D|=%.3g' % (
        A.norm_min_ok.max(), A.norm_max_ok.max(), A.range_ok.max()))
    print('E11 mediana do pool rel<1e-5: %d/%d' % ((A.rel_med < 1e-5).sum(), n))
    print('E14 guards n_eim_nan=%d n_range0=%d n_dedup=%d ; n_front min=%d (n_front==1 em %d)' % (
        A.n_eim_nan.sum(), A.n_range0.sum(), A.n_dedup.sum(), A.n_front.min(), int((A.n_front == 1).sum())))
    print('E10 ga_pop==10D em %d/%d ; ga_gens==200 em %d/%d ; aval-aquisicao total = %d' % (
        int((A.ga_pop == 10 * A.D).sum()), n, int((A.ga_gens == 200).sum()), n, int((A.ga_pop * A.ga_gens).sum())))
    print('E11 pool linhas/geracao == 10D em %d/%d ; total de linhas de pool = %d' % (
        int((A.pool_n == 10 * A.D).sum()), n, A.pool_n.sum()))
    print('E12 criterion unico         :', A.criterion.unique().tolist())
    print('U11 otimista %d/%d componentes ; cobertura2s %d/%d' % (
        A.u11_otimista.sum(), int(A.M.sum()), A.u11_cob.sum(), int(A.M.sum())))
    a1 = A.groupby('problema')[['a1_f', 'a1_n', 'a1_den']].first()
    print('A1 ledger pos-infill: f_best==norm_min(g+1) %d/%d ; n_front1==n_front(g+1) %d/%d' % (
        a1.a1_f.sum(), a1.a1_den.sum(), a1.a1_n.sum(), a1.a1_den.sum()))
    print('U8 fe_treino_max monotonico em %d/%d celulas ; == n_amostra-1 em %d/%d gens' % (
        sum(1 for p, d in A.groupby('problema') if (d.sort_values('geracao').fe_treino_max.diff().dropna() > 0).all()),
        A.problema.nunique(), int((A.fe_treino_max == A.n_amostra - 1).sum()), n))
    print('salvo mecanismo_s42.csv', A.shape)
