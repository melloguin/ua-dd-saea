"""
ParEGO: Pareto-EGO - A hybrid algorithm with online landscape approximation.

Full implementation of Algorithm 1 from:
Knowles, "ParEGO: A Hybrid Algorithm With On-Line Landscape Approximation
for Expensive Multiobjective Optimization Problems" (IEEE TEVC 2006).

ParEGO extends single-objective EGO to multi-objective by:
1. At each iteration, randomly selecting a weight vector λ
2. Scalarizing objectives via augmented Tchebycheff function
3. Building a Kriging model on the scalarized values
4. Finding the solution that maximizes Expected Improvement
5. Evaluating that solution on the true expensive function
6. Repeating until the evaluation budget is exhausted
"""

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel
from scipy.stats import norm
from scipy.optimize import differential_evolution

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


def _generate_weight_vectors(n_obj, s=10):
    """Generate evenly distributed weight vectors using simplex-lattice design."""
    if n_obj == 2:
        vectors = []
        for i in range(s + 1):
            vectors.append(np.array([i / s, 1 - i / s]))
        return np.array(vectors)
    else:
        raise NotImplementedError("Only 2 objectives supported")


def _augmented_tchebycheff(F_normalized, lam, rho=0.05):
    """
    Augmented Tchebycheff scalarizing function (Eq. 2 from paper).
    s(f|λ) = max_i(λ_i * f_i) + ρ * sum(λ_i * f_i)
    """
    weighted = lam * F_normalized
    return np.max(weighted, axis=1) + rho * np.sum(weighted, axis=1)


def _expected_improvement(mu, sigma, f_best):
    """Compute Expected Improvement."""
    with np.errstate(divide='warn'):
        improvement = f_best - mu
        Z = improvement / (sigma + 1e-12)
        ei = improvement * norm.cdf(Z) + sigma * norm.pdf(Z)
        ei[sigma < 1e-12] = 0.0
    return ei


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


def run_parego(problem, config):
    """
    ParEGO online: Algorithm 1 from Knowles (2006).

    Args:
        problem: pymoo Problem instance
        config: dictionary with:
            - 'seed': random seed
            - 'FEmax': max true function evaluations (default 250)
            - 'parego_s': simplex-lattice parameter for weight vectors (default 10)
            - 'parego_rho': augmented Tchebycheff ρ parameter (default 0.05)

    Returns:
        df_pareto: DataFrame with non-dominated solutions
        info: dict with metadata
    """
    np.random.seed(config['seed'])

    n_var = problem.n_var
    n_obj = problem.n_obj
    xl = problem.xl
    xu = problem.xu

    FEmax = config.get('FEmax', 250)
    s_param = config.get('parego_s', 10)
    rho = config.get('parego_rho', 0.05)
    NI = config.get('parego_NI', 11 * n_var - 1)

    weight_vectors = _generate_weight_vectors(n_obj, s_param)
    n_weights = len(weight_vectors)

    # Phase 1: Initialization with LHS
    X_all = _latin_hypercube_sampling(NI, n_var, xl, xu, seed=config['seed'])
    F_all = evaluate_problem(problem, X_all)
    FE = NI

    pbar = tqdm(total=FEmax, initial=FE, desc="ParEGO (FE)")

    # Phase 2: Main loop - one new solution per iteration
    while FE < FEmax:
        # Step 1: Randomly select a weight vector
        lam = weight_vectors[np.random.randint(n_weights)]

        # Step 2: Normalize objectives to [0, 1]
        f_min = F_all.min(axis=0)
        f_max = F_all.max(axis=0)
        f_range = f_max - f_min
        f_range[f_range == 0] = 1.0
        F_normalized = (F_all - f_min) / f_range

        # Step 3: Compute scalarized fitness
        scalar_values = _augmented_tchebycheff(F_normalized, lam, rho)

        # Step 4: Build Kriging model on scalarized values
        # Limit training data size for computational feasibility
        max_train = min(len(X_all), 80)
        if len(X_all) > max_train:
            # Select best half under current λ + random half
            n_best = max_train // 2
            n_random = max_train - n_best
            best_idx = np.argsort(scalar_values)[:n_best]
            remaining = np.setdiff1d(np.arange(len(X_all)), best_idx)
            random_idx = np.random.choice(remaining, size=min(n_random, len(remaining)), replace=False)
            train_idx = np.concatenate([best_idx, random_idx])
        else:
            train_idx = np.arange(len(X_all))

        X_train = X_all[train_idx]
        y_train = scalar_values[train_idx]
        f_best = y_train.min()

        kernel = ConstantKernel(1.0) * Matern(nu=2.5)
        gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6,
                                       n_restarts_optimizer=2, normalize_y=True)
        try:
            gp.fit(X_train, y_train)
        except Exception:
            # Fallback: random solution
            x_new = np.random.uniform(xl, xu)
            f_new = evaluate_problem(problem, x_new.reshape(1, -1))
            X_all = np.vstack([X_all, x_new])
            F_all = np.vstack([F_all, f_new])
            FE += 1
            pbar.update(1)
            continue

        # Step 5: Find solution maximizing Expected Improvement
        def neg_ei(x):
            mu, sigma = gp.predict(x.reshape(1, -1), return_std=True)
            return -_expected_improvement(mu, sigma, f_best)[0]

        bounds = list(zip(xl, xu))
        result = differential_evolution(neg_ei, bounds, seed=config['seed'] + FE,
                                        maxiter=100, popsize=15, tol=1e-6)
        x_new = result.x

        # Step 6: Evaluate new solution with true function
        f_new = evaluate_problem(problem, x_new.reshape(1, -1))
        X_all = np.vstack([X_all, x_new])
        F_all = np.vstack([F_all, f_new])
        FE += 1
        pbar.update(1)

    pbar.close()

    # Return non-dominated solutions
    X_nd, F_nd = _find_non_dominated(X_all, F_all)

    df_pareto = pd.DataFrame({
        'x_1': X_nd[:, 0],
        'x_2': X_nd[:, 1],
        'f1': F_nd[:, 0],
        'f2': F_nd[:, 1],
    })

    info = {'total_FE': FE, 'n_nondominated': len(X_nd), 'total_evaluated': len(X_all)}

    if config.get('verbose', True):
        print(f"\n✅ ParEGO concluído! FE={FE}, Soluções não-dominadas: {len(X_nd)}")

    return df_pareto, info
