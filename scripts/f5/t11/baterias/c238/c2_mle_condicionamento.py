#!/usr/bin/env python
"""C2 — o MOTOR DE MLE e o CONDICIONAMENTO de R, sobre as 25 celulas da s42.
(1) barato, do ⑥ inteiro: theta==theta0 EXATO (fmincon nao andou), saturacoes,
    trajetoria de lnL (sobe? fica negativa?).
(2) caro, amostrado: recomputa R com o theta LOGADO, mede cond(R), chol ok?,
    sigma2, e recomputa lnL para conferir contra o log.
Formulas verbatim de algorithms/c238_EIM/GP_Train.m.
READ-ONLY. Escreve so em f5/t11/baterias/c238/.
"""
import json, os, sys, time
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'
EPS = np.finfo(float).eps

BOUNDS = json.load(open('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/claude_code_context/artifacts/grid_experimentos.json')) \
    if os.path.exists('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/claude_code_context/artifacts/grid_experimentos.json') else None


def corr(Xn, theta):
    t1 = (Xn ** 2 * theta).sum(1)[:, None] * np.ones((1, len(Xn)))
    t2 = Xn * np.sqrt(theta)
    R = np.exp(-(t1 + t1.T - 2.0 * (t2 @ t2.T)))
    n = len(Xn)
    return R + np.eye(n) * (10 + n) * EPS


def lnL_of(Xn, Y, theta):
    n = len(Xn)
    R = corr(Xn, theta)
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        return np.nan, np.nan, np.nan, False
    one = np.ones((n, 1))
    Ri_Y = np.linalg.solve(L.T, np.linalg.solve(L, Y.reshape(-1, 1)))
    Ri_1 = np.linalg.solve(L.T, np.linalg.solve(L, one))
    mu = float((one.T @ Ri_Y) / (one.T @ Ri_1))
    d = (Y.reshape(-1, 1) - mu)
    Ri_d = np.linalg.solve(L.T, np.linalg.solve(L, d))
    s2 = float((d.T @ Ri_d) / n)
    if s2 <= 0:
        return np.nan, s2, np.nan, True
    lnL = -0.5 * n * np.log(s2) - np.log(np.abs(np.diag(L))).sum()
    c = float(np.linalg.cond(R))
    return float(lnL), s2, c, True


def parte1():
    rows = []
    for prob in sorted(os.listdir(S42)):
        b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
        recs = [json.loads(l) for l in open(f'{b}.jsonl') if l.strip()]
        hdr = [r for r in recs if r.get('rec') == 'header'][0]
        M, D = hdr['M'], hdr['D']
        gl = sorted([r for r in recs if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
        tmin = np.array([r['theta_min'] for r in gl], float)
        tmax = np.array([r['theta_max'] for r in gl], float)
        lnL = np.array([r['lnL'] for r in gl], float)
        # theta == theta0 == 1 EXATO em TODAS as D componentes  <=> min==max==1
        parado = (tmin == 1.0) & (tmax == 1.0)
        piso = (tmin <= 1e-3 + 0)
        teto = (tmax >= 1e3 - 0)
        for j in range(M):
            rows.append(dict(problema=prob, D=D, M=M, obj=j, n_gens=len(gl),
                             parado=int(parado[:, j].sum()),
                             frac_parado=float(parado[:, j].mean()),
                             piso=int(piso[:, j].sum()), teto=int(teto[:, j].sum()),
                             lnL_ini=float(lnL[0, j]), lnL_fim=float(lnL[-1, j]),
                             lnL_max=float(lnL[:, j].max()), lnL_min=float(lnL[:, j].min()),
                             lnL_sobe=int(lnL[-1, j] > lnL[0, j]),
                             gens_lnL_neg=int((lnL[:, j] < 0).sum()),
                             frac_lnL_neg=float((lnL[:, j] < 0).mean()),
                             theta_med_ini=float(0.5 * (tmin[0, j] + tmax[0, j])),
                             theta_med_fim=float(0.5 * (tmin[-1, j] + tmax[-1, j])),
                             tmin_viol=int((tmin[:, j] < 1e-3 * (1 - 1e-9)).sum()),
                             tmax_viol=int((tmax[:, j] > 1e3 * (1 + 1e-9)).sum())))
    df = pd.DataFrame(rows)
    df.to_csv(f'{OUT}/mle_theta_s42.csv', index=False)
    n = len(df); ng = int(df.n_gens.sum())
    print('=' * 95)
    print('PARTE 1 — o motor de MLE, TODAS as 25 celulas (%d pares celula-objetivo, %d componentes-geracao)' % (n, ng))
    print('  theta ≡ theta0=1 EXATO (fmincon NAO ANDOU): %d de %d componentes-geracao (%.1f%%)' % (
        df.parado.sum(), ng, 100 * df.parado.sum() / ng))
    print('  celulas-objetivo com >=1 fit parado : %d/%d ; com >50%% parados: %d' % (
        int((df.parado > 0).sum()), n, int((df.frac_parado > .5).sum())))
    print('  top-10 por fracao de fits parados  :')
    print(df.sort_values('frac_parado', ascending=False)[
        ['problema', 'D', 'obj', 'n_gens', 'parado', 'frac_parado', 'lnL_ini', 'lnL_fim']].head(10).to_string(index=False))
    print('  saturacoes: piso 1e-3 = %d ; teto 1e3 = %d ; VIOLACOES de bound = %d/%d' % (
        df.piso.sum(), df.teto.sum(), df.tmin_viol.sum(), df.tmax_viol.sum()))
    print('  lnL SOBE do 1o ao ultimo fit: %d de %d pares celula-objetivo (%.1f%%)' % (
        df.lnL_sobe.sum(), n, 100 * df.lnL_sobe.mean()))
    print('  lnL final NEGATIVA em %d pares ; gens com lnL<0 = %d de %d (%.1f%%)' % (
        int((df.lnL_fim < 0).sum()), df.gens_lnL_neg.sum(), ng, 100 * df.gens_lnL_neg.sum() / ng))
    print('  lnL final < lnL MAXIMO da trajetoria em %d/%d pares (single-start cai em otimos locais distintos)' % (
        int((df.lnL_fim < df.lnL_max).sum()), n))
    print('  celulas com lnL final negativa:')
    print(df[df.lnL_fim < 0][['problema', 'D', 'obj', 'lnL_ini', 'lnL_fim', 'lnL_min', 'frac_lnL_neg', 'frac_parado']].to_string(index=False))
    return df


def parte2(k_amostras=6):
    """recomputa R/lnL/cond no theta LOGADO, em k geracoes por celula (amostra uniforme)."""
    rows = []
    for prob in sorted(os.listdir(S42)):
        b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
        recs = [json.loads(l) for l in open(f'{b}.jsonl') if l.strip()]
        hdr = [r for r in recs if r.get('rec') == 'header'][0]
        M, D = hdr['M'], hdr['D']
        gl = sorted([r for r in recs if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
        real = pq.read_table(f'{b}__real.parquet').to_pandas()
        F = real[[f'f{i}' for i in range(M)]].values.astype(np.float64)
        X = real[[f'x{i}' for i in range(D)]].values.astype(np.float64)
        lo, hi = X.min(0), X.max(0)   # aproxima os bounds do problema pelo envelope do DoE LHS
        idx = np.unique(np.linspace(0, len(gl) - 1, k_amostras).astype(int))
        t0 = time.time()
        for i in idx:
            r = gl[i]; npre = r['n_amostra']
            Xs = X[:npre]
            Xn = (Xs - lo) / np.where(hi - lo == 0, 1, hi - lo)
            for j in range(M):
                # theta ARD 1xD nao e logado inteiro — so min/max/media. Usamos
                # o cenario ISOTROPICO com theta=theta_media[j] como PROXY, e
                # tambem theta=min e theta=max, para cercar cond(R).
                for nome, tv in [('media', r['theta_media'][j]), ('min', r['theta_min'][j]), ('max', r['theta_max'][j])]:
                    th = np.full(D, float(tv))
                    lnl, s2, c, ok = lnL_of(Xn, F[:npre, j], th)
                    rows.append(dict(problema=prob, D=D, geracao=r['geracao'], n=npre, obj=j,
                                     cenario=nome, theta=float(tv), cond=c, chol_ok=int(ok),
                                     sigma2=s2, lnL_rec=lnl, lnL_log=r['lnL'][j]))
        print('  %-10s D=%2d  %d amostras (%.0fs)' % (prob, D, len(idx), time.time() - t0), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f'{OUT}/mle_cond_s42.csv', index=False)
    m = df[df.cenario == 'media']
    print('=' * 95)
    print('PARTE 2 — condicionamento de R no theta LOGADO (cenario isotropico theta=theta_media), %d pontos' % len(m))
    print('  cond(R) mediana=%.3g  p90=%.3g  max=%.3g' % (m['cond'].median(), m['cond'].quantile(.9), m['cond'].max()))
    print('  cond(R) > 1e12 em %d/%d (%.1f%%) ; > 1e15 em %d' % (
        int((m['cond'] > 1e12).sum()), len(m), 100 * (m['cond'] > 1e12).mean(), int((m['cond'] > 1e15).sum())))
    print('  chol FALHOU em %d/%d' % (int((m.chol_ok == 0).sum()), len(m)))
    print('  cond mediana por celula (ultima geracao amostrada):')
    ult = m.sort_values('geracao').groupby(['problema', 'obj']).tail(1)
    print(ult.groupby('problema')['cond'].max().sort_values(ascending=False).to_string())
    return df


if __name__ == '__main__':
    d1 = parte1()
    print()
    d2 = parte2()
    print('\nsalvo mle_theta_s42.csv e mle_cond_s42.csv')
