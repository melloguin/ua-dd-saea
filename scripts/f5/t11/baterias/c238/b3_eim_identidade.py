#!/usr/bin/env python
"""B3 — QUERY-JOIA do c238 no smoke T11 (main/c238/MMF1/42) + contrafactuais.
Recomputa EIM_Euclidean (Apendice A do paper) sobre a pop FINAL do GA (③, DEF-C2),
confronta com eim_best/eim_mediana_pool/infill do ⑥. Roda a MESMA bateria sobre a
celula homologa da rodada-42 (controle).
"""
import json, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import norm

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
ROOTS = {
    'T11_smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42',
    'R42':       '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42/exp_main_c238_MMF1_42',
    'g6_com':    '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/c238/exp_main_c238_MMF1_42',
    'g6_sem':    '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/c238/exp_main_c238_MMF1_42',
}


def nd_std(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y <= Y[i]).all(1) & (Y < Y[i]).any(1)).any():
            keep[i] = False
    return keep


def nd_weak_seq(Y):
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
    """contrafactual sigma->0+: EIM colapsa em min_j ||max(F^j-u,0)||_2"""
    E = np.maximum(Fr[None, :, :] - u[:, None, :], 0.0)
    return np.sqrt((E ** 2).sum(2)).min(1)


def do(tag, b):
    recs = [json.loads(l) for l in open(f'{b}.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    M, D = hdr['M'], hdr['D']
    gens = {r['geracao']: r for r in recs if r.get('rec') == 'c238_gen'}
    real = pq.read_table(f'{b}__real.parquet').to_pandas()
    F = real[[f'f{i}' for i in range(M)]].values.astype(np.float64)
    X = real[[f'x{i}' for i in range(D)]].values.astype(np.float64)
    cols = ['regime', 'geracao', 'real_solution_id'] + [f'mu_{i}' for i in range(M)] + \
           [f'sigma_{i}' for i in range(M)] + [f'x{i}' for i in range(D)] + \
           ['espaco_modelo', 'transf_tipo', 'transf_params', 'modelo_flag', 'pred_tipo',
            'pred_classe', 'pred_score', 'pred_confianca', 'fe_treino_max']
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
        Xp = sub[[f'x{i}' for i in range(D)]].values.astype(np.float64)
        v = eim_euclidean(u, s, Fr)
        rsid = sub.real_solution_id.values
        pos = np.where(rsid == r['infill_sid'])[0]
        j = int(pos[0]) if len(pos) else int(np.argmax(v))
        eb = r['eim_best']; den = max(abs(eb), 1e-300); vmax = float(v.max())
        # contrafactual sigma->0
        v0 = improvement_only(u, Fr)
        muda = int(np.argmax(v0)) != int(np.argmax(v))
        # N2: sigma*1.01 nunca diminui EIM
        v_up = eim_euclidean(u, s * 1.01, Fr)
        n2_ok = bool((v_up >= v - 1e-12).all())
        # fracao de exploracao no ponto escolhido: s*phi / EIM (componente)
        lam = (Fr - u[j]) / s[j]
        Ecomp = (Fr - u[j]) * norm.cdf(lam) + s[j] * norm.pdf(lam)
        nrm = np.sqrt((Ecomp ** 2).sum(1)); k = int(np.argmin(nrm))
        expl = float(np.sqrt(((s[j] * norm.pdf(lam[k])) ** 2).sum()) / max(nrm[k], 1e-300))
        # distancia do infill ao arquivo anterior (recomputada)
        x_inf = X[int(r['infill_sid'])]
        dmin = float(np.sqrt(((X[:npre] - x_inf) ** 2).sum(1)).min())
        # pool coincide com ponto ANTIGO?
        old = set(np.arange(npre).tolist())
        coinc = int(sum(1 for q in rsid if pd.notna(q) and int(q) in old))
        # U11 espaco cru
        mu_cru = u[j] * rg + mn; s_cru = s[j] * rg; f_real = F[int(r['infill_sid'])]
        rows.append(dict(
            fonte=tag, geracao=g, D=D, M=M, n_amostra=npre,
            n_front=r['n_front'], nd_weak=int(mask.sum()), nd_std=n_lo, nd_strict=nstrict,
            front_exato=int(mask.sum()) == r['n_front'],
            front_bracket=(min(n_lo, int(mask.sum())) <= r['n_front'] <= nstrict),
            eim_best=eb, eim_rec_max=vmax, abs_max=abs(vmax - eb), rel_max=abs(vmax - eb) / den,
            eim_rec_infill=float(v[j]), rel_infill=abs(v[j] - eb) / den,
            argmax_eh_infill=int(np.argmax(v)) == j,
            gap_argmax=(vmax - v[j]) / max(vmax, 1e-300),
            eim_med_rec=float(np.median(v)), eim_med_log=r['eim_mediana_pool'],
            rel_med=abs(np.median(v) - r['eim_mediana_pool']) / max(abs(r['eim_mediana_pool']), 1e-300),
            pool_n=len(sub), pool_med_sobre_max=float(np.median(v) / max(vmax, 1e-300)),
            pool_min_sobre_max=float(v.min() / max(vmax, 1e-300)),
            sigma0_muda_argmax=muda, n2_ok=n2_ok, frac_exploracao=expl,
            min_dist_log=r['min_dist_infill'], min_dist_rec=dmin,
            pool_coincide_antigo=coinc,
            eim_zero=int(eb == 0.0), s_best_min=float(s[j].min()),
            lam_abs_max=float(np.abs(lam).max()),
            u11_err=float(np.max(np.abs(mu_cru - f_real))),
            u11_otimista=int((mu_cru < f_real).sum()),
            u11_cob=int((np.abs(mu_cru - f_real) <= 1.96 * s_cru).sum()),
            u11_err_modelo=float(np.max(np.abs(u[j] - (f_real - mn) / rg))),
            # E7 re-scaling
            norm_min_ok=float(np.max(np.abs(np.array(r['norm_min']) - Y.min(0)) / np.maximum(np.abs(Y.min(0)), 1e-12))),
            norm_max_ok=float(np.max(np.abs(np.array(r['norm_max']) - Y.max(0)) / np.maximum(np.abs(Y.max(0)), 1e-12))),
            range_ok=float(np.max(np.abs(np.array(r['norm_range_efetivo']) -
                                         np.maximum(np.array(r['norm_max']) - np.array(r['norm_min']), np.finfo(float).eps)))),
        ))
    df = pd.DataFrame(rows)
    # A1 ledger pos-infill
    gl = [gens[g] for g in sorted(gens)]
    fb = np.array([r['f_best'] for r in gl], float)
    nm = np.array([r['norm_min'] for r in gl], float)
    nf1 = np.array([r['n_front1'] for r in gl]); nf = np.array([r['n_front'] for r in gl])
    a1_f = int((fb[:-1] == nm[1:]).all(1).sum()); a1_n = int((nf1[:-1] == nf[1:]).sum())
    print(f'--- {tag} ---')
    print('  gens=%d  front_exato=%d  front_bracket=%d' % (len(df), df.front_exato.sum(), df.front_bracket.sum()))
    print('  IDENTIDADE EIM: |D|<1e-5 em %d/%d (med=%.3g p99=%.3g max=%.3g)' % (
        (df.abs_max < 1e-5).sum(), len(df), df.abs_max.median(), df.abs_max.quantile(.99), df.abs_max.max()))
    print('  IDENTIDADE rel<1e-5 em %d/%d (med=%.3g)' % ((df.rel_max < 1e-5).sum(), len(df), df.rel_max.median()))
    print('  mediana do pool: rel<1e-5 em %d/%d' % ((df.rel_med < 1e-5).sum(), len(df)))
    print('  argmax==infill: %d/%d  gap<1e-6 em %d/%d (max=%.3g)' % (
        df.argmax_eh_infill.sum(), len(df), (df.gap_argmax < 1e-6).sum(), len(df), df.gap_argmax.max()))
    print('  pool achatado: mediana/max med=%.6f  min/max med=%.6f' % (
        df.pool_med_sobre_max.median(), df.pool_min_sobre_max.median()))
    print('  CONTRAFACTUAL sigma->0 muda argmax em %d/%d (%.1f%%)' % (
        df.sigma0_muda_argmax.sum(), len(df), 100 * df.sigma0_muda_argmax.mean()))
    print('  N2 (sigma*1.01 nunca diminui EIM) vale em %d/%d' % (df.n2_ok.sum(), len(df)))
    print('  fracao de exploracao no escolhido: mediana=%.4f  min=%.4f  max=%.4f' % (
        df.frac_exploracao.median(), df.frac_exploracao.min(), df.frac_exploracao.max()))
    print('  E5 densa: min_dist_infill min=%.4g  gens<1e-8: %d  pool coincidindo c/ ponto ANTIGO: %d de %d linhas' % (
        df.min_dist_log.min(), int((df.min_dist_log < 1e-8).sum()), df.pool_coincide_antigo.sum(), df.pool_n.sum()))
    print('     min_dist logado == recomputado? max|D|=%.3g' % (df.min_dist_log - df.min_dist_rec).abs().max())
    print('  E6 saturacao eim_best==0: %d gens;  |lambda|max mediana=%.4g' % (df.eim_zero.sum(), df.lam_abs_max.median()))
    print('  E7 rescaling: max desvio rel de norm_min=%.3g norm_max=%.3g ; range guard max|D|=%.3g' % (
        df.norm_min_ok.max(), df.norm_max_ok.max(), df.range_ok.max()))
    print('  U11: erro cru mediano=%.4g ; otimista %d/%d ; cobertura2s %d/%d' % (
        df.u11_err.median(), df.u11_otimista.sum(), len(df) * df.M.iloc[0],
        df.u11_cob.sum(), len(df) * df.M.iloc[0]))
    print('     erro no espaco do MODELO mediano=%.4g' % df.u11_err_modelo.median())
    print('  A1 ledger pos-infill: f_best(g)==norm_min(g+1) em %d/%d ; n_front1(g)==n_front(g+1) em %d/%d' % (
        a1_f, len(gl) - 1, a1_n, len(gl) - 1))
    return df


if __name__ == '__main__':
    outs = []
    for tag, b in ROOTS.items():
        try:
            outs.append(do(tag, b))
        except Exception as e:
            print(f'--- {tag} FALHOU: {e!r}')
    A = pd.concat(outs)
    A.to_csv(f'{OUT}/eim_gens_t11.csv', index=False)
    print('\nsalvo eim_gens_t11.csv', A.shape)
