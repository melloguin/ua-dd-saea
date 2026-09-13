"""t04 — reconstrucao da CASCATA MMRAEA (F1..F9) sobre o smoke T11 c141/MMF1.
Testes discriminativos: kernel, regularizacao, arquivo VERDADEIRO x PREDITO no nivel 1,
Fit1/SDE, nivel 2, Q/U, lote, papel da incerteza (Pa/Pb).
READ-ONLY."""
import json, os, sys
import numpy as np, pandas as pd

sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141')
from lib_c141 import sde, nd_levels, front1, ranks_asc, QU

STEM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42'
D, M = 2, 2
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

man = json.load(open(STEM + '.manifest.json'))
ev = [json.loads(l) for l in open(STEM + '.jsonl') if l.strip()]
real = pd.read_parquet(STEM + '__real.parquet')
sur = pd.read_parquet(STEM + '__surrogate.parquet')
gens = [e for e in ev if e.get('rec') == 'c141_gen']
online = sur[sur.regime == 'online']
xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]; mc = [f'mu_{i}' for i in range(M)]

KER = {
 'MQ_c1'   : lambda r2: np.sqrt(r2 + 1.0),
 'MQ_c0.5' : lambda r2: np.sqrt(r2 + 0.25),
 'MQ_c2'   : lambda r2: np.sqrt(r2 + 4.0),
 'IMQ_c1'  : lambda r2: 1.0/np.sqrt(r2 + 1.0),
 'gauss_c1': lambda r2: np.exp(-r2),
 'cubic'   : lambda r2: r2**1.5,
 'linear'  : lambda r2: np.sqrt(r2),
 'TPS'     : lambda r2: np.where(r2 > 0, r2*0.5*np.log(np.maximum(r2, 1e-300)), 0.0),
}

rows = []
for g in gens:
    ge = g['geracao']; ftm = g['fe_treino_max']
    tr = real[real.fe_index <= ftm]
    X = tr[xc].values.astype(np.float64); F = tr[fc].values.astype(np.float64)
    Pk = online[online.geracao == ge]
    Xp = Pk[xc].values.astype(np.float64); mu = Pk[mc].values.astype(np.float64)
    d2 = ((X[:, None, :] - X[None, :, :])**2).sum(-1)
    d2p = ((Xp[:, None, :] - X[None, :, :])**2).sum(-1)
    FitA = sde(F); FNA = nd_levels(F).astype(float)
    Y = np.column_stack([F, FitA, FNA])
    r = dict(g=ge, n=len(X), n_pool=len(Xp))

    # --- F1: teste discriminativo de kernel (contra o mu LOGADO) ---
    best = {}
    for name, phi in KER.items():
        try:
            W = np.linalg.solve(phi(d2), Y)
            pred = phi(d2p) @ W
            e = np.abs(pred[:, :M] - mu)
            best[name] = float(np.median(e / (np.abs(mu).mean() + 1e-300)))
        except Exception:
            best[name] = np.inf
    # MQ + cauda polinomial grau 1
    try:
        n = len(X)
        Pm = np.column_stack([np.ones(n), X])
        A = np.block([[np.sqrt(d2+1.0), Pm], [Pm.T, np.zeros((D+1, D+1))]])
        rhs = np.vstack([Y, np.zeros((D+1, Y.shape[1]))])
        sol = np.linalg.solve(A, rhs)
        pred = np.sqrt(d2p+1.0) @ sol[:n] + np.column_stack([np.ones(len(Xp)), Xp]) @ sol[n:]
        best['MQ_poly1'] = float(np.median(np.abs(pred[:, :M]-mu)/(np.abs(mu).mean()+1e-300)))
    except Exception:
        best['MQ_poly1'] = np.inf
    # MQ c=1 COM scaling de X pelos bounds [0,1]x[-1,1] do MMF1 -> normalizado
    lo = np.minimum(X.min(0), Xp.min(0)); hi = np.maximum(X.max(0), Xp.max(0))
    Xs = (X-lo)/(hi-lo); Xps = (Xp-lo)/(hi-lo)
    d2s = ((Xs[:, None, :]-Xs[None, :, :])**2).sum(-1); d2ps = ((Xps[:, None, :]-Xs[None, :, :])**2).sum(-1)
    W = np.linalg.solve(np.sqrt(d2s+1.0), Y)
    best['MQ_c1_scaled'] = float(np.median(np.abs((np.sqrt(d2ps+1.0)@W)[:, :M]-mu)/(np.abs(mu).mean()+1e-300)))
    # MQ c=1 COM ridge (regularizacao) — o contrafactual de F2
    for lam in [1e-12, 1e-8, 1e-4]:
        Phi = np.sqrt(d2+1.0)
        W = np.linalg.solve(Phi + lam*np.eye(len(X)), Y)
        best[f'MQ_ridge{lam:g}'] = float(np.median(np.abs((np.sqrt(d2p+1.0)@W)[:, :M]-mu)/(np.abs(mu).mean()+1e-300)))
    r['kernel_best'] = min(best, key=best.get)
    for k, v in best.items():
        r['k_'+k] = v
    r['rcond'] = float(1.0/np.linalg.cond(np.sqrt(d2+1.0)))

    # --- reconstrucao canonica (MQ c=1, sem ridge, sem scaling) ---
    Phi = np.sqrt(d2+1.0); W = np.linalg.solve(Phi, Y)
    Pred = np.sqrt(d2p+1.0) @ W
    mu_rec = Pred[:, :M]; fitpred = Pred[:, M]; fnpred = Pred[:, M+1]
    r['mu_relerr_med'] = float(np.median(np.abs(mu_rec-mu)/(np.abs(mu)+1e-12)))
    # interpolacao: o modelo reconstruido nos PROPRIOS nos de treino
    r['interp_max'] = float(np.abs(np.sqrt(d2+1.0)@W - Y)[:, :M].max())

    # --- F3: nivel 1 nas DUAS hipoteses ---
    n1_true = len(np.intersect1d(front1(np.vstack([mu, F])), np.arange(len(mu))))
    FpredA = np.sqrt(((X[:, None, :]-X[None, :, :])**2).sum(-1)+1.0) @ W  # A predita p/ si mesma
    n1_pred = len(np.intersect1d(front1(np.vstack([mu, FpredA[:, :M]])), np.arange(len(mu))))
    r['n_front1_log'] = g['n_front1']; r['n1_true'] = n1_true; r['n1_pred'] = n1_pred
    r['hit_true'] = int(n1_true == g['n_front1']); r['hit_pred'] = int(n1_pred == g['n_front1'])

    idx1 = np.intersect1d(front1(np.vstack([mu, F])), np.arange(len(mu)))
    # --- F4: Fit1 = SDE(mu) sobre P ---
    if len(idx1) > 1:
        fit1 = sde(mu[idx1])
        r['fit1max_log'] = g['fit1']['max']; r['fit1max_rec'] = float(np.nanmax(fit1))
        r['fit1_relerr'] = float(abs(r['fit1max_rec']-r['fit1max_log'])/(abs(r['fit1max_log'])+1e-300))
        fit2 = fnpred[idx1]; fit3 = fitpred[idx1]
        Z = np.column_stack([-fit1, fit2, -fit3])
        f2 = front1(Z); idx2 = idx1[f2]
        r['n_front2_log'] = g['n_front2']; r['n_front2_rec'] = len(idx2)
        r['hit_front2'] = int(len(idx2) == g['n_front2'])
        R1 = ranks_asc(-fit1[f2]); R2 = ranks_asc(fit2[f2]); R3 = ranks_asc(-fit3[f2])
        Q, U = QU(R1, R2, R3)
        r['Qmin_log'] = g['Q']['min']; r['Qmax_log'] = g['Q']['max']
        r['Umin_log'] = g['U']['min']; r['Umax_log'] = g['U']['max']
        r['Qmin_rec'] = int(Q.min()); r['Qmax_rec'] = int(Q.max())
        r['Umin_rec'] = int(U.min()); r['Umax_rec'] = int(U.max())
        r['hit_QU'] = int(Q.min() == g['Q']['min'] and Q.max() == g['Q']['max']
                          and U.min() == g['U']['min'] and U.max() == g['U']['max'])
        r['QU_bounds_ok'] = int(Q.min() >= 3 and Q.max() <= 3*len(idx2)
                                and U.min() >= 0 and U.max() <= 2*(len(idx2)-1 if len(idx2) > 1 else 1))
        Pa = set(front1(np.column_stack([Q, U])).tolist())
        Pb = int(np.argmax(U))
        r['lote_log'] = g['lote']; r['lote_rec'] = len(Pa | {Pb})
        r['hit_lote'] = int(len(Pa | {Pb}) == g['lote'])
        r['Pb_extra'] = int(Pb not in Pa)      # F9: a incerteza acrescentou um FE?
        r['nPa'] = len(Pa)
        # --- fit2 x fit3: prova de escala ---
        r['ratio_f3_f1'] = float(abs(np.median(fit3))/ (abs(np.median(fit1))+1e-300))
        r['ratio_f2_f1'] = float(abs(np.median(fit2))/ (abs(np.median(fit1))+1e-300))
    # --- F7: U do pool completo ---
    fit1p = sde(mu)
    R1p = ranks_asc(-fit1p); R2p = ranks_asc(fnpred); R3p = ranks_asc(-fitpred)
    Qp, Up = QU(R1p, R2p, R3p)
    r['Upoolmax_log'] = g['U_pool_max']; r['Upoolmax_rec'] = int(Up.max())
    r['hit_Upool'] = int(Up.max() == g['U_pool_max'])
    s0 = Pk.sigma_0.values.astype(float)
    r['sig0_igual_frac'] = float((Up == s0).mean())
    r['sig0_corr'] = float(np.corrcoef(Up, s0)[0, 1]) if s0.std() > 0 else np.nan
    # --- F8: sigma_1 ddof ---
    st1 = np.std(np.column_stack([fit1p, fnpred, fitpred]), axis=1, ddof=1)
    st0 = np.std(np.column_stack([fit1p, fnpred, fitpred]), axis=1, ddof=0)
    s1 = Pk.sigma_1.values.astype(float)
    r['sig1_relerr_ddof1'] = float(np.median(np.abs(st1-s1)/(np.abs(s1)+1e-300)))
    r['sig1_relerr_ddof0'] = float(np.median(np.abs(st0-s1)/(np.abs(s1)+1e-300)))
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't04_cascata.csv'), index=False)

P('#### F1 kernel — vencedor por ciclo (erro relativo mediano contra o mu LOGADO)')
kcols = [c for c in df.columns if c.startswith('k_')]
P('  vencedores:', df.kernel_best.value_counts().to_dict())
P(df[['g', 'n'] + kcols].to_string(index=False, float_format=lambda v: f'{v:.3e}'))
P('')
P('#### F2 regularizacao / condicionamento')
P('  rcond por ciclo:', [f'{v:.2e}' for v in df.rcond])
P('  erro relativo mediano mu_rec x mu_log (MQ c=1 SEM ridge):', [f'{v:.2e}' for v in df.mu_relerr_med])
P('  interpolacao do modelo reconstruido nos nos de treino (max|Phi w - Y|):',
  [f'{v:.2e}' for v in df.interp_max])
P('  contrafactual ridge 1e-12 / 1e-8 / 1e-4 (mediana sobre ciclos):',
  f"{df['k_MQ_ridge1e-12'].median():.3e}", f"{df['k_MQ_ridge1e-08'].median():.3e}", f"{df['k_MQ_ridge0.0001'].median():.3e}")
P('  contrafactual MQ com scaling de X (mediana):', f"{df.k_MQ_c1_scaled.median():.3e}")
P('')
P('#### F3 nivel 1: arquivo VERDADEIRO x PREDITO')
P(df[['g', 'n_front1_log', 'n1_true', 'n1_pred', 'hit_true', 'hit_pred']].to_string(index=False))
P('  acertos: VERDADEIRO', int(df.hit_true.sum()), '/', len(df), ' PREDITO', int(df.hit_pred.sum()), '/', len(df))
P('  |delta| VERDADEIRO:', (df.n1_true-df.n_front1_log).abs().tolist())
P('  |delta| PREDITO   :', (df.n1_pred-df.n_front1_log).abs().tolist())
P('')
P('#### F4/F5/F6 Fit1, nivel 2, Q/U, lote')
cols = ['g', 'fit1max_log', 'fit1max_rec', 'fit1_relerr', 'n_front2_log', 'n_front2_rec',
        'Qmin_log', 'Qmin_rec', 'Qmax_log', 'Qmax_rec', 'Umin_log', 'Umin_rec', 'Umax_log', 'Umax_rec',
        'lote_log', 'lote_rec', 'nPa', 'Pb_extra']
P(df[cols].to_string(index=False, float_format=lambda v: f'{v:.6g}'))
P('  Fit1.max relerr mediano:', f"{df.fit1_relerr.median():.3e}", ' <1e-5 em', int((df.fit1_relerr < 1e-5).sum()), '/', len(df))
P('  n_front2 fecha:', int(df.hit_front2.sum()), '/', len(df))
P('  Q/U (4 numeros) fecham:', int(df.hit_QU.sum()), '/', len(df), ' limites teoricos ok:', int(df.QU_bounds_ok.sum()), '/', len(df))
P('  lote fecha:', int(df.hit_lote.sum()), '/', len(df))
P('  razao |fit3|/|fit1| mediana:', f"{df.ratio_f3_f1.median():.3f}", ' |fit2|/|fit1| mediana:', f"{df.ratio_f2_f1.median():.1f}")
P('')
P('#### F9 papel da incerteza: Pb fora de Pa?')
P('  Pb EXTRA em', int(df.Pb_extra.sum()), '/', len(df), 'ciclos =', f'{100*df.Pb_extra.mean():.1f}%')
P('  |Pa| por ciclo:', df.nPa.tolist(), ' lote logado:', df.lote_log.tolist())
P('  FEs de infill logados:', int(df.lote_log.sum()), ' atribuiveis ao argmax-U:', int(df.Pb_extra.sum()),
  f'= {100*df.Pb_extra.sum()/df.lote_log.sum():.1f}%')
P('')
P('#### F7/F8 sigma')
P(df[['g', 'Upoolmax_log', 'Upoolmax_rec', 'hit_Upool', 'sig0_igual_frac', 'sig0_corr',
      'sig1_relerr_ddof1', 'sig1_relerr_ddof0']].to_string(index=False, float_format=lambda v: f'{v:.4g}'))
P('  U_pool_max fecha:', int(df.hit_Upool.sum()), '/', len(df))
P('  sigma_0 igualdade elemento-a-elemento media:', f'{df.sig0_igual_frac.mean()*100:.1f}%',
  ' corr media:', f'{df.sig0_corr.mean():.4f}')
P('  sigma_1: relerr ddof=1', f'{df.sig1_relerr_ddof1.median():.3e}', ' x ddof=0', f'{df.sig1_relerr_ddof0.median():.4f}',
  ' (1-1/sqrt(1.5) =', f'{1-1/np.sqrt(1.5):.5f})')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't04_cascata.txt'), 'w').write('\n'.join(out))
