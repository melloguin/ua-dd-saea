#!/usr/bin/env python
"""C4 — CONDICIONAMENTO de R (matriz de correlacao do kriging) nas 25 celulas da s42.
Formula verbatim de algorithms/c238_EIM/GP_Train.m:
  R = exp(-(t1 + t1' - 2*t2*t2')) + eye(n)*(10+n)*eps ,  t1=sum(Xn^2.*theta,2)*1',  t2=Xn.*sqrt(theta)
O theta ARD nao e logado componente a componente (so min/max/media) -> usamos o
cenario ISOTROPICO theta=theta_media[j] como proxy e reportamos tambem theta_min/max
para cercar. cond por eigvalsh (R e simetrica PSD).
READ-ONLY.
"""
import json, os, time
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'
EPS = np.finfo(float).eps


def corr(Xn, theta):
    t1 = (Xn ** 2 * theta).sum(1)[:, None]
    t2 = Xn * np.sqrt(theta)
    R = np.exp(-(t1 + t1.T - 2.0 * (t2 @ t2.T)))
    n = len(Xn)
    return R + np.eye(n) * (10 + n) * EPS


def diag(Xn, Y, theta):
    n = len(Xn)
    R = corr(Xn, theta)
    w = np.linalg.eigvalsh(R)
    cond = float(w.max() / max(w.min(), 1e-300))
    negmin = float(w.min())
    try:
        L = np.linalg.cholesky(R); chol_ok = True
    except np.linalg.LinAlgError:
        return cond, negmin, False, np.nan, np.nan
    one = np.ones((n, 1)); Yc = Y.reshape(-1, 1)
    RiY = np.linalg.solve(L.T, np.linalg.solve(L, Yc))
    Ri1 = np.linalg.solve(L.T, np.linalg.solve(L, one))
    mu = float((one.T @ RiY).item() / (one.T @ Ri1).item())
    d = Yc - mu
    Rid = np.linalg.solve(L.T, np.linalg.solve(L, d))
    s2 = float((d.T @ Rid).item() / n)
    if s2 <= 0:
        return cond, negmin, True, s2, np.nan
    lnL = float(-0.5 * n * np.log(s2) - np.log(np.abs(np.diag(L))).sum())
    return cond, negmin, True, s2, lnL


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
    lo, hi = X.min(0), X.max(0)
    rng = np.where(hi - lo == 0, 1.0, hi - lo)
    idx = np.unique(np.linspace(0, len(gl) - 1, 5).astype(int))
    t0 = time.time()
    for i in idx:
        r = gl[i]; npre = r['n_amostra']
        Xn = (X[:npre] - lo) / rng
        for j in range(M):
            th = np.full(D, float(r['theta_media'][j]))
            c, wmin, ok, s2, lnl = diag(Xn, F[:npre, j], th)
            rows.append(dict(problema=prob, D=D, M=M, geracao=r['geracao'], n=npre, obj=j,
                             theta_media=float(r['theta_media'][j]),
                             theta_min=float(r['theta_min'][j]), theta_max=float(r['theta_max'][j]),
                             cond=c, autoval_min=wmin, chol_ok=int(ok), sigma2=s2,
                             lnL_rec_iso=lnl, lnL_log=float(r['lnL'][j])))
    print('  %-10s D=%2d M=%d  n_max=%d  %d amostras (%.1fs)' % (prob, D, M, gl[-1]['n_amostra'], len(idx), time.time() - t0), flush=True)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/cond_s42.csv', index=False)
print('=' * 95)
print('CONDICIONAMENTO de R no theta LOGADO (isotropico=theta_media), %d pontos (25 celulas x 5 geracoes x M)' % len(df))
print('  cond(R): mediana=%.3g  p90=%.3g  max=%.3g' % (df['cond'].median(), df['cond'].quantile(.9), df['cond'].max()))
print('  cond>1e8 : %d/%d (%.1f%%) | cond>1e12: %d (%.1f%%) | cond>1e15: %d' % (
    int((df['cond'] > 1e8).sum()), len(df), 100 * (df['cond'] > 1e8).mean(),
    int((df['cond'] > 1e12).sum()), 100 * (df['cond'] > 1e12).mean(), int((df['cond'] > 1e15).sum())))
print('  chol FALHOU (no proxy isotropico): %d/%d' % (int((df.chol_ok == 0).sum()), len(df)))
print()
ult = df.sort_values('geracao').groupby(['problema', 'obj']).tail(1)
t = ult.groupby('problema').agg(D=('D', 'first'), n=('n', 'max'), cond_max=('cond', 'max'),
                                theta_med=('theta_media', 'median')).sort_values('cond_max', ascending=False)
print('  cond(R) na ULTIMA geracao amostrada, por celula:')
print(t.to_string())
print()
print('  correlacao log10(cond) x log10(theta_media): %.3f  (theta pequeno => R quase singular)' % (
    np.corrcoef(np.log10(np.clip(df['cond'], 1, None)), np.log10(np.clip(df.theta_media, 1e-12, None)))[0, 1]))
print('  cond mediana por faixa de theta_media:')
df['faixa'] = pd.cut(np.log10(np.clip(df.theta_media, 1e-12, None)), [-3.1, -2, -1, 0, 1, 2, 3.1])
print(df.groupby('faixa', observed=True)['cond'].agg(['count', 'median', 'max']).to_string())
