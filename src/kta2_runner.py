"""
KTA2: Kriging-Assisted Two-Archive Evolutionary Algorithm.

Implementation based on:
    Song et al. "A Kriging-Assisted Two-Archive Evolutionary Algorithm for
    Expensive Many-Objective Optimization" (IEEE TEVC, 2021).

PAPER ALGORITHM (Fig. 3, Section III):
    1. Initialise with LHS; build influential point-insensitive (IPI) models.
    2. Generate candidate archives CCA/CDA via Two Arch2 for 10 generations.
    3. Assess optimisation state (convergence/diversity/uncertainty demand).
    4. Select eta samples with tailored strategy (Algorithm 1/2/3).
    5. Update CA/DA; rebuild IPI models.  Repeat until FEmax.

    IPI Model (Fig. 4, Section III-A):
    - 3 Kriging models per objective: 1 sensitive (all data) +
      2 insensitive (top/bottom tau*N sorted by objective value).
    - Routing: sensitive model predicts → select insensitive model
      whose training mean is closer to the prediction.

DEVIATIONS / NOTES:
    - The paper uses DACE (MATLAB) for Kriging.  This implementation uses
      sklearn's GaussianProcessRegressor with Matern(nu=2.5) kernel.
    - The paper uses PlatEMO (MATLAB) framework.  This is a standalone
      Python implementation.
    - The IPI model, adaptive sampling, and Two Arch2 logic follow the
      paper faithfully.
"""

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel

from src.problems import evaluate_problem


def _latin_hypercube_sampling(n_samples, n_var, xl, xu, seed=42):
    rng = np.random.RandomState(seed)
    result = np.zeros((n_samples, n_var))
    for j in range(n_var):
        cut = np.linspace(0, 1, n_samples + 1)
        u = rng.uniform(size=n_samples)
        points = cut[:n_samples] + u * (cut[1:] - cut[:n_samples])
        rng.shuffle(points)
        result[:, j] = xl[j] + points * (xu[j] - xl[j])
    return result


def _sbx_crossover(p1, p2, eta=20, prob=1.0, xl=None, xu=None):
    """SBX crossover producing one offspring."""
    n = len(p1)
    c = p1.copy()
    if np.random.random() > prob:
        return c
    for i in range(n):
        if np.random.random() < 0.5 and abs(p1[i] - p2[i]) > 1e-14:
            y1, y2 = min(p1[i], p2[i]), max(p1[i], p2[i])
            beta = 1.0 + 2.0 * (y1 - xl[i]) / (y2 - y1 + 1e-14)
            alpha = 2.0 - beta ** (-(eta + 1))
            rand = np.random.random()
            if rand <= 1.0 / alpha:
                betaq = (rand * alpha) ** (1.0 / (eta + 1))
            else:
                betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1))
            c[i] = 0.5 * ((y1 + y2) - betaq * (y2 - y1))
            c[i] = np.clip(c[i], xl[i], xu[i])
    return c


def _polynomial_mutation(x, eta=20, prob=None, xl=None, xu=None):
    """Polynomial mutation."""
    n = len(x)
    if prob is None:
        prob = 1.0 / n
    c = x.copy()
    for i in range(n):
        if np.random.random() < prob:
            delta = xu[i] - xl[i]
            rand = np.random.random()
            if rand < 0.5:
                xy = 1.0 - (c[i] - xl[i]) / delta
                val = 2.0 * rand + (1.0 - 2.0 * rand) * (xy ** (eta + 1))
                deltaq = val ** (1.0 / (eta + 1)) - 1.0
            else:
                xy = 1.0 - (xu[i] - c[i]) / delta
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (xy ** (eta + 1))
                deltaq = 1.0 - val ** (1.0 / (eta + 1))
            c[i] = np.clip(c[i] + deltaq * delta, xl[i], xu[i])
    return c


def _i_epsilon_plus(f1, f2):
    """I_ε+ indicator: min ε such that f1 - ε dominates f2."""
    return np.max(f1 - f2)


def _normalize_population(F):
    """Per-objective min-max normalization to [0,1]^m (Zitzler 2004).

    IBEA's I_ε+ indicator is scale-sensitive: without normalization, objectives
    on different magnitudes (WFG, DTLZ, BBOB) produce indicator values that
    cause `exp(-I/kappa)` to overflow when `kappa=0.05`. Normalizing the
    population to the unit hypercube keeps |I_ε+| <= 1 and therefore
    |exp argument| <= 1/kappa = 20, well within float64 range.
    """
    F = np.asarray(F, dtype=float)
    F_min = F.min(axis=0)
    F_max = F.max(axis=0)
    return (F - F_min) / np.maximum(F_max - F_min, 1e-12)


def _fitness_i_epsilon_all(F, kappa=0.05):
    """Vectorized IBEA fitness for the entire population.

    Returns Q where ``Q[i] = sum_{j != i} -exp(-I_eps+(F_norm[j], F_norm[i]) / kappa)``
    with F first normalized to [0,1]^m. Equivalent in semantics to calling
    `_fitness_i_epsilon(i, F)` for every i, but vectorized and overflow-safe.
    """
    F = np.asarray(F, dtype=float)
    n = len(F)
    if n <= 1:
        return np.zeros(n)
    F_norm = _normalize_population(F)
    # I[j, i] = max_k (F_norm[j, k] - F_norm[i, k])
    diff = F_norm[:, None, :] - F_norm[None, :, :]   # (n, n, m)
    I = diff.max(axis=2)                             # (n, n)
    mat = -np.exp(-I / kappa)                        # (n, n)
    np.fill_diagonal(mat, 0.0)
    return mat.sum(axis=0)


def _fitness_i_epsilon(idx, F, kappa=0.05):
    """IBEA fitness for a single individual (kept for backwards compatibility).

    Prefer `_fitness_i_epsilon_all` when computing fitness for the entire
    population — it normalizes once and is vectorized. This per-index variant
    normalizes the full population on every call.
    """
    F = np.asarray(F, dtype=float)
    n = len(F)
    if n <= 1:
        return 0.0
    F_norm = _normalize_population(F)
    fi = F_norm[idx]
    q = 0.0
    for j in range(n):
        if j != idx:
            q += -np.exp(-_i_epsilon_plus(F_norm[j], fi) / kappa)
    return q


def _lp_norm_distance(f1, f2, p=0.1):
    """Lp-norm distance for diversity measurement."""
    return np.sum(np.abs(f1 - f2) ** p) ** (1.0 / p)


def _pure_diversity(F, p=0.1):
    """Pure diversity indicator using Lp-norm."""
    n = len(F)
    if n <= 1:
        return 0.0
    total = 0.0
    for i in range(n):
        min_dist = float('inf')
        for j in range(n):
            if i != j:
                d = _lp_norm_distance(F[i], F[j], p)
                min_dist = min(min_dist, d)
        total += min_dist
    return total


def _update_ca(X_ca, F_ca, X_new, F_new, max_size):
    """Update convergence archive using I_ε+ indicator."""
    X = np.vstack([X_ca, X_new]) if len(X_ca) > 0 else X_new.copy()
    F = np.vstack([F_ca, F_new]) if len(F_ca) > 0 else F_new.copy()

    while len(X) > max_size:
        Q = _fitness_i_epsilon_all(F)
        worst = np.argmin(Q)
        X = np.delete(X, worst, axis=0)
        F = np.delete(F, worst, axis=0)

    return X, F


def _update_da(X_da, F_da, X_new, F_new, max_size):
    """Update diversity archive: keep non-dominated, select by Lp diversity."""
    X = np.vstack([X_da, X_new]) if len(X_da) > 0 else X_new.copy()
    F = np.vstack([F_da, F_new]) if len(F_da) > 0 else F_new.copy()

    # Keep non-dominated only
    n = len(F)
    is_dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        if is_dominated[i]:
            continue
        for j in range(n):
            if i == j or is_dominated[j]:
                continue
            if np.all(F[j] <= F[i]) and np.any(F[j] < F[i]):
                is_dominated[i] = True
                break
    nd_mask = ~is_dominated
    X = X[nd_mask]
    F = F[nd_mask]

    if len(X) <= max_size:
        return X, F

    # Select by Lp diversity
    selected = []
    # First add boundary solutions
    for k in range(F.shape[1]):
        selected.append(np.argmin(F[:, k]))
        selected.append(np.argmax(F[:, k]))
    selected = list(set(selected))

    remaining = [i for i in range(len(X)) if i not in selected]
    while len(selected) < max_size and remaining:
        best_idx = None
        best_dist = -1
        for r in remaining:
            min_d = min(_lp_norm_distance(F[r], F[s]) for s in selected)
            if min_d > best_dist:
                best_dist = min_d
                best_idx = r
        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)
        else:
            break

    selected = selected[:max_size]
    return X[selected], F[selected]


def _build_influential_point_insensitive_models(X_train, Y_train, n_obj, tau=0.75):
    """
    Build influential point-insensitive model for each objective.
    3 Kriging models per objective: sensitive + 2 insensitive.
    """
    models = []
    for k in range(n_obj):
        y = Y_train[:, k]
        sorted_idx = np.argsort(y)
        n = len(y)
        n_keep = max(3, int(tau * n))

        kernel = ConstantKernel(1.0) * Matern(nu=2.5)

        # Sensitive model (all data)
        gp_sensitive = GaussianProcessRegressor(kernel=kernel, alpha=1e-6,
                                                 n_restarts_optimizer=1, normalize_y=True)
        gp_sensitive.fit(X_train, y)

        # Insensitive model 1: top τN (small values)
        idx1 = sorted_idx[:n_keep]
        gp_insensitive1 = GaussianProcessRegressor(kernel=kernel, alpha=1e-6,
                                                     n_restarts_optimizer=1, normalize_y=True)
        gp_insensitive1.fit(X_train[idx1], y[idx1])
        mean1 = np.mean(y[idx1])

        # Insensitive model 2: last τN (large values)
        idx2 = sorted_idx[-n_keep:]
        gp_insensitive2 = GaussianProcessRegressor(kernel=kernel, alpha=1e-6,
                                                     n_restarts_optimizer=1, normalize_y=True)
        gp_insensitive2.fit(X_train[idx2], y[idx2])
        mean2 = np.mean(y[idx2])

        models.append({
            'sensitive': gp_sensitive,
            'insensitive1': gp_insensitive1,
            'insensitive2': gp_insensitive2,
            'mean1': mean1,
            'mean2': mean2,
        })

    return models


def _predict_with_ipi_models(models, X):
    """Predict using influential point-insensitive models."""
    n_obj = len(models)
    F_pred = np.zeros((len(X), n_obj))
    F_std = np.zeros((len(X), n_obj))

    for k in range(n_obj):
        m = models[k]
        y_sensitive = m['sensitive'].predict(X)

        for i in range(len(X)):
            if abs(y_sensitive[i] - m['mean1']) <= abs(y_sensitive[i] - m['mean2']):
                mu, sigma = m['insensitive1'].predict(X[i:i+1], return_std=True)
            else:
                mu, sigma = m['insensitive2'].predict(X[i:i+1], return_std=True)
            F_pred[i, k] = mu[0]
            F_std[i, k] = sigma[0]

    return F_pred, F_std


def _find_non_dominated(X, F):
    n = len(F)
    is_dominated = np.zeros(n, dtype=bool)
    for i in range(n):
        if is_dominated[i]:
            continue
        for j in range(n):
            if i == j or is_dominated[j]:
                continue
            if np.all(F[j] <= F[i]) and np.any(F[j] < F[i]):
                is_dominated[i] = True
                break
    mask = ~is_dominated
    return X[mask], F[mask]


def run_kta2(problem, config, save_history: bool = False):
    """
    KTA2 online: Kriging-Assisted Two-Archive EA.

    Args:
        problem: pymoo Problem instance
        config: dictionary with:
            - 'seed': random seed
            - 'FEmax': max true function evaluations (default 300)
            - 'kta2_archive_size': size of CA and DA (default 100)
            - 'kta2_eta': infill samples per update (default 5)
            - 'kta2_tau': proportion for insensitive models (default 0.75)
            - 'kta2_phi': random selection size for uncertainty sampling (default 0.1)
        save_history: when True, records a snapshot of the cumulative
            archive (X_all, F_all) of all truly-evaluated points at the end
            of every outer iteration.

    Returns:
        df_pareto: DataFrame with non-dominated solutions from DA
        info: dict with metadata
        history: list of {'generation': int,
                          'population': [{'genotype': [...],
                                          'fitness': [...]}, ...]}
            or ``None`` when save_history=False.
    """
    np.random.seed(config['seed'])

    n_var = problem.n_var
    n_obj = problem.n_obj
    xl = problem.xl
    xu = problem.xu

    FEmax = config.get('FEmax', 300)
    archive_size = config.get('kta2_archive_size', 100)
    eta = config.get('kta2_eta', 5)
    tau = config.get('kta2_tau', 0.75)
    phi_ratio = config.get('kta2_phi', 0.1)
    phi = max(2, int(phi_ratio * archive_size))

    NI = min(archive_size, 11 * n_var - 1)

    # Phase 1: Initialization
    X_init = _latin_hypercube_sampling(NI, n_var, xl, xu, seed=config['seed'])
    F_init = evaluate_problem(problem, X_init)
    FE = NI

    X_all = X_init.copy()
    F_all = F_init.copy()

    # Initialize CA and DA
    X_ca, F_ca = _update_ca(np.empty((0, n_var)), np.empty((0, n_obj)),
                             X_init, F_init, archive_size)
    X_da, F_da = _update_da(np.empty((0, n_var)), np.empty((0, n_obj)),
                             X_init, F_init, archive_size)

    # Build initial models
    ipi_models = _build_influential_point_insensitive_models(X_all, F_all, n_obj, tau)

    history = [] if save_history else None
    gen_counter = 0
    if save_history:
        history.append({
            'generation': gen_counter,
            'population': [{'genotype': list(X_all[i]),
                            'fitness': list(F_all[i])}
                           for i in range(len(X_all))],
        })

    pbar = tqdm(total=FEmax, initial=FE, desc="KTA2 (FE)")

    while FE < FEmax:
        # Phase 2: Candidate Offspring Generation (10 generations on surrogate)
        X_cca = X_ca.copy()
        F_cca = F_ca.copy()
        X_cda = X_da.copy()
        F_cda = F_da.copy()

        for gen in range(10):
            # Generate offspring: crossover between CCA and CDA, mutation on CCA
            offspring_X = []
            n_off = min(len(X_cca), len(X_cda))
            for _ in range(max(1, n_off)):
                i_ca = np.random.randint(len(X_cca))
                i_da = np.random.randint(len(X_cda))
                child = _sbx_crossover(X_cca[i_ca], X_cda[i_da], xl=xl, xu=xu)
                child = _polynomial_mutation(child, xl=xl, xu=xu, prob=1.0/n_var)
                offspring_X.append(child)

            # Also mutate some CA members
            for _ in range(max(1, len(X_cca) // 2)):
                i_ca = np.random.randint(len(X_cca))
                child = _polynomial_mutation(X_cca[i_ca].copy(), xl=xl, xu=xu, prob=1.0/n_var)
                offspring_X.append(child)

            offspring_X = np.array(offspring_X)
            offspring_F, _ = _predict_with_ipi_models(ipi_models, offspring_X)

            X_cca, F_cca = _update_ca(X_cca, F_cca, offspring_X, offspring_F, archive_size)
            X_cda, F_cda = _update_da(X_cda, F_cda, offspring_X, offspring_F, archive_size)

        # Phase 3: Adaptive Sampling
        # Assess optimization state
        if len(X_cca) > 0 and len(X_cda) > 0:
            z_ideal_est = np.min(F_all, axis=0) if len(F_all) > 0 else np.zeros(n_obj)

            dist_cca = np.linalg.norm(F_cca - z_ideal_est, axis=1)
            dist_cda = np.linalg.norm(F_cda - z_ideal_est, axis=1)

            # Convergence demand: CCA significantly closer than CDA
            convergence_demand = np.median(dist_cca) < np.median(dist_cda) * 0.9

            if convergence_demand:
                # Convergence sampling: select eta best from CCA by I_ε+
                n_sel = min(eta, len(X_cca))
                Q = _fitness_i_epsilon_all(F_cca)
                best_idx = np.argsort(-Q)[:n_sel]
                X_new = X_cca[best_idx]
            else:
                # Check diversity demand
                pd_da = _pure_diversity(F_da)
                pd_cda = _pure_diversity(F_cda)

                if pd_cda >= pd_da:
                    # Diversity sampling: select most different from DA
                    X_new = []
                    X_pool = X_cda.copy()
                    F_pool = F_cda.copy()
                    for _ in range(min(eta, len(X_pool))):
                        best_idx = None
                        best_dist = -1
                        for r in range(len(X_pool)):
                            min_d = min(
                                _lp_norm_distance(F_pool[r], F_da[s])
                                for s in range(len(F_da))
                            ) if len(F_da) > 0 else float('inf')
                            if min_d > best_dist:
                                best_dist = min_d
                                best_idx = r
                        if best_idx is not None:
                            X_new.append(X_pool[best_idx])
                            X_pool = np.delete(X_pool, best_idx, axis=0)
                            F_pool = np.delete(F_pool, best_idx, axis=0)
                    X_new = np.array(X_new) if X_new else X_cda[:eta]
                else:
                    # Uncertainty sampling: randomly select phi, pick most uncertain
                    X_new = []
                    X_pool = X_cda.copy()
                    for _ in range(min(eta, len(X_pool))):
                        n_candidates = min(phi, len(X_pool))
                        cand_idx = np.random.choice(len(X_pool), size=n_candidates, replace=False)
                        _, cand_std = _predict_with_ipi_models(ipi_models, X_pool[cand_idx])
                        avg_std = np.mean(cand_std, axis=1)
                        best_local = cand_idx[np.argmax(avg_std)]
                        X_new.append(X_pool[best_local])
                        X_pool = np.delete(X_pool, best_local, axis=0)
                    X_new = np.array(X_new) if X_new else X_cda[:eta]
        else:
            X_new = _latin_hypercube_sampling(eta, n_var, xl, xu, seed=config['seed'] + FE)

        # Evaluate new samples
        n_eval = min(len(X_new), FEmax - FE)
        X_new = X_new[:n_eval]
        if len(X_new) == 0:
            break

        F_new = evaluate_problem(problem, X_new)
        FE += len(X_new)
        pbar.update(len(X_new))

        X_all = np.vstack([X_all, X_new])
        F_all = np.vstack([F_all, F_new])

        # Update archives with truly evaluated data
        X_ca, F_ca = _update_ca(X_ca, F_ca, X_new, F_new, archive_size)
        X_da, F_da = _update_da(X_da, F_da, X_new, F_new, archive_size)

        # Rebuild models
        ipi_models = _build_influential_point_insensitive_models(X_all, F_all, n_obj, tau)

        if save_history:
            gen_counter += 1
            history.append({
                'generation': gen_counter,
                'population': [{'genotype': list(X_all[i]),
                                'fitness': list(F_all[i])}
                               for i in range(len(X_all))],
            })

    pbar.close()

    # Return non-dominated from DA
    X_nd, F_nd = _find_non_dominated(X_da, F_da)

    data = {}
    for i in range(X_nd.shape[1]):
        data[f'x_{i+1}'] = X_nd[:, i]
    for j in range(F_nd.shape[1]):
        data[f'f{j+1}'] = F_nd[:, j]
    df_pareto = pd.DataFrame(data)

    info = {'total_FE': FE, 'n_nondominated': len(X_nd), 'total_evaluated': len(X_all)}

    if config.get('verbose', True):
        print(f"\n✅ KTA2 concluído! FE={FE}, Soluções não-dominadas: {len(X_nd)}")

    return df_pareto, info, history
