"""Biblioteca de reconstrucao do mecanismo MMRAEA (c141) a partir dos dados.
READ-ONLY sobre os dados; nada aqui escreve em resultados_experimentos.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141'


def load(pb):
    stem = os.path.join(ROOT, pb, '42', f'exp_main_c141_{pb}_42')
    man = json.load(open(stem + '.manifest.json'))
    ev = [json.loads(l) for l in open(stem + '.jsonl') if l.strip()]
    real = pd.read_parquet(stem + '__real.parquet')
    pop = pd.read_parquet(stem + '__pop.parquet')
    sur = pd.read_parquet(stem + '__surrogate.parquet')
    tim = pd.read_parquet(stem + '__timing.parquet')
    return man, ev, real, pop, sur, tim


def nd_levels(F):
    """Front numbers (1-based) por dominancia de Pareto (minimizacao). O(n^2 M)."""
    n = len(F)
    lvl = np.zeros(n, int)
    remaining = np.arange(n)
    cur = 1
    Fr = F
    while len(remaining):
        Fs = F[remaining]
        m = len(remaining)
        dom = np.zeros(m, bool)
        for i in range(m):
            le = (Fs <= Fs[i]).all(1)
            lt = (Fs < Fs[i]).any(1)
            if (le & lt).any():
                dom[i] = True
        lvl[remaining[~dom]] = cur
        remaining = remaining[dom]
        cur += 1
    return lvl


def front1(F):
    n = len(F)
    dom = np.zeros(n, bool)
    for i in range(n):
        le = (F <= F[i]).all(1)
        lt = (F < F[i]).any(1)
        if (le & lt).any():
            dom[i] = True
    return np.where(~dom)[0]


def sde(F):
    """Fitness SDE (Eq.7) com normalizacao min-max sobre o proprio conjunto.
    Fit(p) = min_{q!=p} ||max(0, f(q)-f(p))||_2 . Maior = melhor."""
    F = np.asarray(F, float)
    mn, mx = F.min(0), F.max(0)
    rg = mx - mn
    Fn = (F - mn) / np.where(rg == 0, np.nan, rg)
    diff = Fn[None, :, :] - Fn[:, None, :]
    d = np.sqrt((np.maximum(diff, 0) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return d.min(1)


def rbf_fit(X, Y):
    """RBF multiquadratica c=1, poly=0, mldivide denso (sem regularizacao)."""
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    Phi = np.sqrt(d2 + 1.0)
    W = np.linalg.solve(Phi, Y)
    return W


def rbf_pred(Xp, X, W):
    d2 = ((Xp[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    return np.sqrt(d2 + 1.0) @ W


def ranks_asc(v):
    """Rank 1-based por ordenacao ascendente (ties -> ordem estavel, como sort do MATLAB)."""
    order = np.argsort(v, kind='stable')
    r = np.empty(len(v), int)
    r[order] = np.arange(1, len(v) + 1)
    return r


def QU(R1, R2, R3):
    Q = R1 + R2 + R3
    U = np.abs(R1 - R2) + np.abs(R1 - R3) + np.abs(R2 - R3)
    return Q, U


def reconstruir_ciclo(g, real, sur, D, M):
    """Reconstroi um ciclo completo a partir do arquivo (①) e do pool (③ online).
    Devolve dict com todas as quantidades da cascata."""
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    mc = [f'mu_{i}' for i in range(M)]
    tr = real[real.fe_index <= g['fe_treino_max']]
    X = tr[xc].values.astype(np.float64)
    F = tr[fc].values.astype(np.float64)
    P = sur[(sur.regime == 'online') & (sur.geracao == g['geracao'])]
    Xp = P[xc].values.astype(np.float64)
    mu = P[mc].values.astype(np.float64)

    # --- 3 modos ---
    FitA = sde(F)                       # alvo do FitRBF
    FNA = nd_levels(F).astype(float)    # alvo do FNRBF
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    Phi = np.sqrt(d2 + 1.0)
    Y = np.column_stack([F, FitA, FNA])
    W = np.linalg.solve(Phi, Y)
    d2p = ((Xp[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    Pred = np.sqrt(d2p + 1.0) @ W
    mu_rec = Pred[:, :M]
    fitpred_pool = Pred[:, M]     # SDE predito  (log: fit3)
    fnpred_pool = Pred[:, M + 1]  # front number predito (log: fit2)

    # --- nivel 1: F1(Ptot U A) ∩ Ptot ---
    allF = np.vstack([mu, F])
    f1 = front1(allF)
    idx1 = f1[f1 < len(mu)]

    # --- Fit1 = SDE(mu) sobre P (nivel-1) ---
    sub = mu[idx1]
    fit1 = sde(sub)
    fit2 = fnpred_pool[idx1]
    fit3 = fitpred_pool[idx1]

    # --- nivel 2: ND de [-Fit1, Fit2, -Fit3] ---
    Z = np.column_stack([-fit1, fit2, -fit3])
    f2 = front1(Z)
    idx2 = idx1[f2]

    # --- ranks / Q / U sobre o nivel-2 ---
    R1 = ranks_asc(-fit1[f2]); R2 = ranks_asc(fit2[f2]); R3 = ranks_asc(-fit3[f2])
    Q, U = QU(R1, R2, R3)

    # --- nivel 3: ND de (Q,U) U argmax U ---
    QUm = np.column_stack([Q, U])
    fa = front1(QUm)
    sel = set(fa.tolist()) | {int(np.argmax(U))}

    # --- U sobre o POOL completo (sigma_0, extensao D45) ---
    fit1_pool = sde(mu)
    R1p = ranks_asc(-fit1_pool); R2p = ranks_asc(fnpred_pool); R3p = ranks_asc(-fitpred_pool)
    Qp, Up = QU(R1p, R2p, R3p)
    sig1_pool = np.std(np.column_stack([fit1_pool, fnpred_pool, fitpred_pool]), axis=1)

    return dict(P=P, mu_obs=mu, mu_rec=mu_rec, idx1=idx1, idx2=idx2,
                fit1=fit1[f2], fit2=fit2[f2], fit3=fit3[f2], Q=Q, U=U,
                n_sel=len(sel), U_pool=Up, Q_pool=Qp, sig1_pool=sig1_pool,
                fit1_pool=fit1_pool, fnpred_pool=fnpred_pool, fitpred_pool=fitpred_pool,
                n=len(X), Phi=Phi)
