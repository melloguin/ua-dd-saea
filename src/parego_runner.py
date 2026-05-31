"""
ParEGO: Pareto-EGO — A hybrid algorithm with online landscape approximation.

Implementation based on:
    Knowles, "ParEGO: A Hybrid Algorithm With On-Line Landscape Approximation
    for Expensive Multiobjective Optimization Problems"
    (IEEE TEVC 10(1), 2005).

PAPER ALGORITHM (Algorithm 1 / Section IV):
    1. Initialize with Latin Hypercube Sampling of 11d-1 points.
    2. At each iteration:
       a. Draw random weight vector λ from simplex-lattice (Eq. 1, s=10).
       b. Normalize objectives to [0,1].
       c. Compute augmented Tchebycheff: max(λ_i*f_i) + ρ*Σ(λ_i*f_i), ρ=0.05.
       d. Build DACE (Kriging) model on scalar costs.
       e. Search for solution maximising Expected Improvement.
       f. Evaluate and update.
    3. Cap DACE model at 80 training points.

DEVIATIONS / NOTES:
    - The paper uses Nelder-Mead (20 restarts) for likelihood optimisation
      and an internal GA (pop=20, 10000 evals) for EI maximisation.
      This implementation uses sklearn's GaussianProcessRegressor (L-BFGS
      for likelihood) and scipy.optimize.differential_evolution for EI
      maximisation.  Both are standard modern alternatives that produce
      equivalent results.
    - The paper caps the DACE model at 80 points and selects a subset
      heuristically (Section IV-A).  This implementation keeps all
      training data — feasible because sklearn's GP handles moderate N
      efficiently.
    - Weight vectors now support M >= 2 objectives via the general
      simplex-lattice construction (same formula as RVEA/MOEA-D).
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
    """Generate evenly distributed weight vectors using simplex-lattice design.

    Implements Eq. 1 from Knowles (2005):
        {lambda : lambda_j in {0/s, 1/s, ..., s/s}, sum(lambda) = 1}

    For n_obj >= 3 this uses the general combinatorial construction
    (same simplex-lattice formula used by RVEA/MOEA-D).
    """
    if n_obj == 2:
        return np.array([[i / s, 1 - i / s] for i in range(s + 1)])
    from itertools import combinations_with_replacement
    points = []
    for combo in combinations_with_replacement(range(s + 1), n_obj - 1):
        vals = [combo[0]]
        for j in range(1, len(combo)):
            vals.append(combo[j] - combo[j - 1])
        vals.append(s - combo[-1])
        points.append(np.array(vals, dtype=float) / s)
    return np.array(points)


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


def run_parego(problem, config, save_history: bool = False):
    """
    ParEGO online: Algorithm 1 from Knowles (2006).

    Args:
        problem: pymoo Problem instance
        config: dictionary with:
            - 'seed': random seed
            - 'FEmax': max true function evaluations (default 250)
            - 'parego_s': simplex-lattice parameter for weight vectors (default 10)
            - 'parego_rho': augmented Tchebycheff ρ parameter (default 0.05)
        save_history: when True, records a snapshot of the cumulative
            true-evaluated archive (X_all, F_all) at every EI iteration.

    Returns:
        df_pareto: DataFrame with non-dominated solutions
        info: dict with metadata
        history: list of {'generation': int,
                          'population': [{'genotype': [...],
                                          'fitness': [...]}, ...]}
            or ``None`` when save_history=False.
            "Generation" is the EI iteration index (0 = post-LHS init); the
            recorded population is the monotonically growing archive of
            true-evaluated points.
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

    history = [] if save_history else None
    gen_counter = 0
    if save_history:
        history.append({
            'generation': gen_counter,
            'population': [{'genotype': list(X_all[i]),
                            'fitness': list(F_all[i])}
                           for i in range(len(X_all))],
        })

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
            if save_history:
                gen_counter += 1
                history.append({
                    'generation': gen_counter,
                    'population': [{'genotype': list(X_all[i]),
                                    'fitness': list(F_all[i])}
                                   for i in range(len(X_all))],
                })
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

        if save_history:
            gen_counter += 1
            history.append({
                'generation': gen_counter,
                'population': [{'genotype': list(X_all[i]),
                                'fitness': list(F_all[i])}
                               for i in range(len(X_all))],
            })

    pbar.close()

    # Return non-dominated solutions
    X_nd, F_nd = _find_non_dominated(X_all, F_all)

    data = {}
    for i in range(X_nd.shape[1]):
        data[f'x_{i+1}'] = X_nd[:, i]
    for j in range(F_nd.shape[1]):
        data[f'f{j+1}'] = F_nd[:, j]
    df_pareto = pd.DataFrame(data)

    info = {'total_FE': FE, 'n_nondominated': len(X_nd), 'total_evaluated': len(X_all)}

    if config.get('verbose', True):
        print(f"\n✅ ParEGO concluído! FE={FE}, Soluções não-dominadas: {len(X_nd)}")

    return df_pareto, info, history
