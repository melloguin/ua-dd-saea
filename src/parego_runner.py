"""
ParEGO: Pareto-EGO — A hybrid algorithm with online landscape approximation.

Implementation based on:
    Knowles, "ParEGO: A Hybrid Algorithm With On-Line Landscape Approximation
    for Expensive Multiobjective Optimization Problems"
    (IEEE TEVC 10(1), 2006).

PAPER ALGORITHM (Algorithm 1 / Section IV):
    1. Initialize with Latin Hypercube Sampling of 11d-1 points.
    2. At each iteration:
       a. Draw random weight vector λ from simplex-lattice (Eq. 1, s=10).
       b. Normalize objectives to [0,1].
       c. Compute augmented Tchebycheff: max(λ_i*f_i) + ρ*Σ(λ_i*f_i), ρ=0.05.
       d. Build DACE (Kriging) model on scalar costs.
       e. Search for solution maximising Expected Improvement.
       f. Evaluate and update.
    3. Cap the model: if iter < 25 use all points; else use a subset of
       11d-1+25 points (half best under λ, half random without replacement).

FIDELITY NOTES (state after the canonical-fidelity refactor):
    FAITHFUL TO THE PAPER:
    - Augmented Tchebycheff with ρ=0.05 (Eq. 2).                     [Sec. IV]
    - Objective normalisation to [0,1] before scalarisation.        [Sec. IV]
    - λ drawn uniformly per iteration from a simplex-lattice (s=10).[Eq. 1]
    - Surrogate = Kriging/GP with a GAUSSIAN (squared-exponential)
      correlation, anisotropic / one length-scale per dimension —
      mirrors DACE `corrgauss` (one θ per dim). Constant-mean GP
      (`normalize_y=True`) ≈ ordinary Kriging of Jones-EGO.          [Sec. III]
    - Analytic single-point Expected Improvement.                   [Sec. III]
    - Model cap = 11d-1+25 with the iter<25 trigger and the
      half-best/half-random subset selection.                      [Sec. IV]
    - Internal GA maximising EI: pop=20, steady-state, binary
      tournament, SBX (p=0.2), mutation ±(1/100)·μ·range, init =
      5 mutants of the 5 best real points under λ + 15 LHS,
      10000 internal EI evaluations.                          [Sec. IV/Tab. V]
    - LHS init of 11d-1 points; q=1 real evaluation per iteration.

    CONSCIOUS / DOCUMENTED RESIDUAL DIVERGENCES (cannot be removed without
    leaving the standard scientific Python stack — none alters the nature of
    the algorithm):
    - Hyper-parameter MLE uses sklearn's L-BFGS with 20 restarts, whereas the
      paper uses the Nelder-Mead simplex with 20 restarts. Same objective
      (max likelihood of the DACE/GP model), different inner optimiser.
    - The internal-GA mutation operator and the SBX distribution index are
      reconstructed from the paper text (the exact symbols did not render in
      the available PDF extraction — see Flag H1 in the plan). Implemented as
      ±(1/100)·μ·range, μ~U(0.0001,1), p_m=1/d, SBX distribution index 20.
    - Normalisation uses the empirical min/max of the cumulative archive,
      i.e. "estimated" cost-space limits; the paper assumes known/estimated
      limits and explicitly allows the estimated case.

    A `differential_evolution`-based EI optimiser is preserved behind
    config['ei_optimizer'] = 'de' as a tested fallback / speed option; the
    default 'internal_ga' reproduces the paper's internal EA.
"""

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
from scipy.stats import norm
from scipy.optimize import differential_evolution

from src.problems import evaluate_problem


def _latin_hypercube_sampling(n_samples, n_var, xl, xu, rng):
    """Latin hypercube sample in [xl, xu], using a local RNG (Generator)."""
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

    Implements Eq. 1 from Knowles (2006):
        {lambda : lambda_j in {0/s, 1/s, ..., s/s}, sum(lambda) = 1}

    For n_obj >= 3 this uses the general combinatorial construction
    (same simplex-lattice formula used by RVEA/MOEA-D). The paper only tests
    M = 2 and 3; the construction reproduces Eq. 1 exactly in those cases.
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
    """Analytic Expected Improvement for MINIMISATION (Sec. III).

    EI(x) = (f_best - μ)·Φ(z) + σ·φ(z),  z = (f_best - μ)/σ;  EI=0 when σ≈0.
    Higher EI is better. Works on scalars or arrays.
    """
    with np.errstate(divide='warn'):
        improvement = f_best - mu
        Z = improvement / (sigma + 1e-12)
        ei = improvement * norm.cdf(Z) + sigma * norm.pdf(Z)
        ei = np.atleast_1d(ei)
        ei[np.atleast_1d(sigma) < 1e-12] = 0.0
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


# --------------------------------------------------------------------------
# Internal genetic operators for the EI-maximising EA (Knowles 2006, Sec. IV)
# --------------------------------------------------------------------------

def _ga_mutate(x, xl, xu, span, p_mut, rng):
    """Mutation of the internal GA (Sec. IV / Table V).

    Each gene is mutated with probability p_m = 1/d; a mutated gene is shifted
    by ±(1/100)·μ·(parameter range), with μ ~ U(0.0001, 1) and a random sign.
    (Operator reconstructed from the paper text — see Flag H1.)
    """
    child = x.copy()
    sites = rng.random(len(x)) < p_mut
    if np.any(sites):
        mu = rng.uniform(0.0001, 1.0, size=len(x))
        sign = rng.choice(np.array([-1.0, 1.0]), size=len(x))
        shift = sign * (mu / 100.0) * span
        child[sites] = child[sites] + shift[sites]
        child = np.clip(child, xl, xu)
    return child


def _sbx_one_child(p1, p2, xl, xu, rng, disC=20):
    """Simulated binary crossover producing ONE offspring (Deb's SBX [18]).

    The paper specifies SBX producing a single offspring; the distribution
    index is not legible in the available extraction — 20 is used (Deb's
    common default, also PlatEMO's). See Flag H1.
    """
    D = len(p1)
    u = rng.random(D)
    beta = np.where(u <= 0.5,
                    (2.0 * u) ** (1.0 / (disC + 1.0)),
                    (2.0 * (1.0 - u)) ** (-1.0 / (disC + 1.0)))
    c1 = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2)
    c2 = 0.5 * ((1 - beta) * p1 + (1 + beta) * p2)
    pick = rng.random(D) < 0.5
    child = np.where(pick, c1, c2)
    return np.clip(child, xl, xu)


def _binary_tournament(fitness, rng):
    """Binary tournament without replacement; higher EI wins."""
    a, b = rng.choice(len(fitness), size=2, replace=False)
    return a if fitness[a] >= fitness[b] else b


def _internal_ga_maximize_ei(gp, f_best, xl, xu, n_var, X_real, scalar_real,
                             rng, n_evals=10000, pop_size=20, p_cross=0.2):
    """Internal EA that maximises Expected Improvement over the surrogate.

    Canonical spec — Knowles (2006), Sec. IV ("The EA used within ParEGO...")
    and Table V:
      - Population: 20 solutions.
      - Steady-state: one offspring per generation (crossover OR cloning,
        followed by mutation).
      - Budget: 10000 EI evaluations on the GP (NOT real function evals).
      - Reproductive selection: binary tournament without replacement.
      - Crossover: SBX with probability 0.2, producing one offspring;
        otherwise a parent is cloned.
      - Mutation: ±(1/100)·μ·range, μ~U(0.0001,1), p_m = 1/d.
      - Replacement: offspring replaces the (first) parent if better.
      - Initialization: 5 mutants of the 5 best REAL points under λ + 15 LHS.

    Returns the decision vector with the highest EI found.
    """
    xl = np.asarray(xl, dtype=float)
    xu = np.asarray(xu, dtype=float)
    span = xu - xl
    p_mut = 1.0 / n_var

    def ei_of(X):
        X = np.atleast_2d(X)
        mu, sigma = gp.predict(X, return_std=True)
        return _expected_improvement(mu, sigma, f_best)

    # --- Initialisation: 5 mutants of the 5 best real points under λ + 15 LHS
    order = np.argsort(scalar_real)
    n_seed = int(min(5, pop_size, len(order)))
    seed_pts = np.atleast_2d(X_real[order[:n_seed]]).astype(float)
    init_rows = [_ga_mutate(seed_pts[k], xl, xu, span, p_mut, rng)
                 for k in range(n_seed)]
    pop = np.array(init_rows) if init_rows else np.empty((0, n_var))
    n_lhs = pop_size - len(pop)
    if n_lhs > 0:
        pop = np.vstack([pop, _latin_hypercube_sampling(n_lhs, n_var, xl, xu, rng)])

    fitness = ei_of(pop)
    evals = len(pop)

    # --- Steady-state loop
    while evals < n_evals:
        i1 = _binary_tournament(fitness, rng)
        if rng.random() < p_cross:
            i2 = _binary_tournament(fitness, rng)
            child = _sbx_one_child(pop[i1], pop[i2], xl, xu, rng)
        else:
            child = pop[i1].copy()           # cloning event
        child = _ga_mutate(child, xl, xu, span, p_mut, rng)
        cf = ei_of(child)[0]
        evals += 1
        if cf > fitness[i1]:                  # replace first parent if better
            pop[i1] = child
            fitness[i1] = cf

    return pop[int(np.argmax(fitness))]


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
            - 'parego_NI': initial LHS size (default 11*n_var - 1)
            - 'parego_ifes': internal EI evaluations for the GA (default 10000)
            - 'ei_optimizer': 'internal_ga' (default, canonical) or 'de' (fallback)
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
    # Single local RNG seeded from config['seed'] drives ALL stochastic
    # components (LHS, λ draw, random half of the model cap, internal GA),
    # so two runs with the same seed are identical.
    rng = np.random.default_rng(config['seed'])

    n_var = problem.n_var
    n_obj = problem.n_obj
    xl = problem.xl
    xu = problem.xu

    FEmax = config.get('FEmax', 250)
    s_param = config.get('parego_s', 10)
    rho = config.get('parego_rho', 0.05)
    NI = config.get('parego_NI', 11 * n_var - 1)
    ifes = config.get('parego_ifes', 10000)
    ei_optimizer = config.get('ei_optimizer', 'internal_ga')

    weight_vectors = _generate_weight_vectors(n_obj, s_param)
    n_weights = len(weight_vectors)

    # Phase 1: Initialization with LHS (11d-1 points)
    X_all = _latin_hypercube_sampling(NI, n_var, xl, xu, rng)
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

    # Phase 2: Main loop - one new solution per iteration (q=1)
    while FE < FEmax:
        # Step 1: Randomly select a weight vector
        lam = weight_vectors[rng.integers(n_weights)]

        # Step 2: Normalize objectives to [0, 1] over the cumulative archive
        f_min = F_all.min(axis=0)
        f_max = F_all.max(axis=0)
        f_range = f_max - f_min
        f_range[f_range == 0] = 1.0
        F_normalized = (F_all - f_min) / f_range

        # Step 3: Compute scalarized fitness (augmented Tchebycheff)
        scalar_values = _augmented_tchebycheff(F_normalized, lam, rho)

        # Step 4: Build Kriging model on scalarized values.
        # Canonical ParEGO cap (Sec. IV): if iter<25 use all points; else use
        # a subset of 11d-1+25 points (half best under λ, half random). As q=1,
        # this is equivalent to the size-based trigger len(X_all) > 11d-1+25.
        cap = 11 * n_var - 1 + 25
        if len(X_all) <= cap:
            train_idx = np.arange(len(X_all))
        else:
            n_best = cap // 2
            n_random = cap - n_best
            best_idx = np.argsort(scalar_values)[:n_best]
            remaining = np.setdiff1d(np.arange(len(X_all)), best_idx)
            random_idx = rng.choice(remaining, size=min(n_random, len(remaining)),
                                    replace=False)
            train_idx = np.concatenate([best_idx, random_idx])

        X_train = X_all[train_idx]
        y_train = scalar_values[train_idx]

        # Robustness (cf. PlatEMO ParEGO.m): drop duplicated decision rows to
        # avoid a singular correlation matrix in late iterations.
        _, uniq = np.unique(np.round(X_train * 1e6) / 1e6, axis=0,
                            return_index=True)
        uniq = np.sort(uniq)
        X_train = X_train[uniq]
        y_train = y_train[uniq]

        # Incumbent for EI = best scalarized cost under λ over the whole archive
        f_best = float(scalar_values.min())

        # Gaussian (squared-exponential) correlation, anisotropic (one
        # length-scale per dimension, like DACE corrgauss); constant-mean GP.
        kernel = ConstantKernel(1.0) * RBF(length_scale=np.ones(n_var),
                                           length_scale_bounds=(1e-2, 1e3))
        gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6,
                                      n_restarts_optimizer=20, normalize_y=True)
        try:
            gp.fit(X_train, y_train)
        except Exception:
            # Fallback: random solution
            x_new = rng.uniform(xl, xu)
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
        if ei_optimizer == 'internal_ga':
            # Canonical internal EA over the decision space (Sec. IV).
            x_new = _internal_ga_maximize_ei(
                gp, f_best, xl, xu, n_var, X_all, scalar_values, rng,
                n_evals=ifes)
        else:
            # Fallback: scipy differential evolution (preserved, selectable).
            def neg_ei(x):
                mu, sigma = gp.predict(x.reshape(1, -1), return_std=True)
                return -_expected_improvement(mu, sigma, f_best)[0]

            bounds = list(zip(xl, xu))
            result = differential_evolution(neg_ei, bounds,
                                            seed=int(config['seed']) + FE,
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
