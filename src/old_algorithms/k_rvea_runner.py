"""
K-RVEA Online: Kriging-assisted Reference Vector Guided Evolutionary Algorithm.

Implementation based on:
    Chugh et al. "A Surrogate-assisted Reference Vector Guided Evolutionary
    Algorithm for Computationally Expensive Many-objective Optimization"
    (IEEE TEVC 22(1), 2016).

PAPER ALGORITHM (Algorithm 2):
    1. Initialise with LHS of NI = 11n-1 points; evaluate with true function.
    2. Train Kriging model per objective from archive A1.
    3. Run RVEA for wmax generations using Kriging predictions (Algorithm 1).
    4. Select u individuals for re-evaluation (Algorithm 3): APD or
       uncertainty-based, depending on diversity check via fixed ref. vectors.
    5. Manage training archive A1 (Algorithm 4): keep NI samples via clustering.
    6. Repeat until FEmax true evaluations.

DEVIATIONS / NOTES:
    - The paper uses the DACE toolbox (Hookes-Jeeves) for Kriging
      hyperparameter optimisation.  This implementation uses sklearn's
      GaussianProcessRegressor with L-BFGS, which is a modern equivalent.
    - The paper tests with 3 to 10 objectives and 10 decision variables.
      This implementation supports any n_var and n_obj.
7. Returns non-dominated solutions from all truly-evaluated individuals
"""

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel
from sklearn.cluster import KMeans

from src.problems import evaluate_problem
from src.k_rvea.individual import Individual
from src.k_rvea.offspring import (
    simulated_binary_crossover,
    polynomial_mutation,
    tournament_selection,
    create_offspring_population,
)
from src.k_rvea.selection import (
    generate_reference_vectors,
    adapt_reference_vectors,
    compute_angle,
    rvea_environmental_selection,
)


def _latin_hypercube_sampling(n_samples, n_var, xl, xu, seed=42):
    """Generate Latin Hypercube Samples in [xl, xu]."""
    rng = np.random.RandomState(seed)
    result = np.zeros((n_samples, n_var))
    for j in range(n_var):
        cut = np.linspace(0, 1, n_samples + 1)
        u = rng.uniform(size=n_samples)
        points = cut[:n_samples] + u * (cut[1:] - cut[:n_samples])
        rng.shuffle(points)
        result[:, j] = xl[j] + points * (xu[j] - xl[j])
    return result


def _train_kriging_models(X_train, Y_train, n_obj):
    """Train one Gaussian Process model per objective."""
    models = []
    for k in range(n_obj):
        kernel = ConstantKernel(1.0) * Matern(nu=2.5)
        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            n_restarts_optimizer=2,
            normalize_y=True,
        )
        gp.fit(X_train, Y_train[:, k])
        models.append(gp)
    return models


def _predict_kriging(models, X):
    """Predict mean and std for each objective using trained GP models."""
    means = []
    stds = []
    for gp in models:
        mu, sigma = gp.predict(X, return_std=True)
        means.append(mu)
        stds.append(sigma)
    return np.column_stack(means), np.column_stack(stds)


def _evaluate_with_kriging(population, models):
    """Evaluate population fitness using Kriging models (no true evaluation)."""
    X = np.array([ind.genotype for ind in population])
    F_pred, F_std = _predict_kriging(models, X)
    for i, ind in enumerate(population):
        ind.fitness = F_pred[i].tolist()
        ind.kriging_std = F_std[i].tolist()
        ind.mapping_success = True


def _select_for_reevaluation(population, config, V0, Va, n_select,
                              prev_n_inactive_fixed, Vf):
    """
    Algorithm 3: Select individuals for re-evaluation.

    Uses either APD (convergence) or Kriging uncertainty (diversity)
    depending on the change in inactive fixed reference vectors.
    """
    valid_pop = [ind for ind in population if ind.fitness is not None]
    if len(valid_pop) == 0:
        return [], 0

    n_ref = len(Vf)
    delta_threshold = config.get('krvea_delta', max(1, int(0.05 * n_ref)))

    # Assign population to fixed reference vectors to count inactive
    fitness_matrix = np.array([ind.fitness for ind in valid_pop])
    f_ideal = fitness_matrix.min(axis=0)
    f_bar = fitness_matrix - f_ideal

    active_fixed = set()
    for idx in range(len(valid_pop)):
        min_angle = float('inf')
        best_ref = 0
        for j in range(n_ref):
            angle = compute_angle(f_bar[idx], Vf[j])
            if angle < min_angle:
                min_angle = angle
                best_ref = j
        active_fixed.add(best_ref)

    n_inactive_fixed = n_ref - len(active_fixed)
    delta_vf = n_inactive_fixed - prev_n_inactive_fixed

    # Cluster active adaptive reference vectors
    Va_adapted = adapt_reference_vectors(V0, valid_pop)
    n_va = len(Va_adapted)

    # Assign to adaptive reference vectors
    assignments_adaptive = {}
    for idx in range(len(valid_pop)):
        min_angle = float('inf')
        best_ref = 0
        for j in range(n_va):
            angle = compute_angle(f_bar[idx], Va_adapted[j])
            if angle < min_angle:
                min_angle = angle
                best_ref = j
        if best_ref not in assignments_adaptive:
            assignments_adaptive[best_ref] = []
        assignments_adaptive[best_ref].append(idx)

    active_adaptive_refs = list(assignments_adaptive.keys())
    n_clusters = min(n_select, len(active_adaptive_refs))
    if n_clusters == 0:
        return [], n_inactive_fixed

    # Cluster the active adaptive reference vectors
    if n_clusters >= len(active_adaptive_refs):
        clusters = {i: [r] for i, r in enumerate(active_adaptive_refs)}
    else:
        active_vecs = Va_adapted[active_adaptive_refs]
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=3)
        labels = km.fit_predict(active_vecs)
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(active_adaptive_refs[i])

    # Select one individual from each cluster
    selected_indices = []
    use_uncertainty = delta_vf > delta_threshold

    k = config['n_objetivos']
    t_ratio = 1.0  # use full penalty for convergence selection

    for cluster_id, ref_indices in clusters.items():
        # Gather all individuals assigned to reference vectors in this cluster
        candidate_indices = []
        for ref_idx in ref_indices:
            if ref_idx in assignments_adaptive:
                candidate_indices.extend(assignments_adaptive[ref_idx])

        if len(candidate_indices) == 0:
            continue

        if use_uncertainty:
            # Select by maximum uncertainty (average std across objectives)
            best_idx = None
            best_unc = -float('inf')
            for ci in candidate_indices:
                ind = valid_pop[ci]
                avg_std = np.mean(ind.kriging_std) if hasattr(ind, 'kriging_std') else 0
                if avg_std > best_unc:
                    best_unc = avg_std
                    best_idx = ci
        else:
            # Select by minimum APD
            best_idx = None
            best_apd = float('inf')
            for ci in candidate_indices:
                # Find the reference vector this individual is assigned to
                min_angle = float('inf')
                assigned_ref = 0
                for j in range(n_va):
                    angle = compute_angle(f_bar[ci], Va_adapted[j])
                    if angle < min_angle:
                        min_angle = angle
                        assigned_ref = j

                gamma_v = float('inf')
                for j2 in range(n_va):
                    if j2 != assigned_ref:
                        a = compute_angle(Va_adapted[assigned_ref], Va_adapted[j2])
                        if a < gamma_v:
                            gamma_v = a
                gamma_v = max(gamma_v, 1e-10)

                dist = np.linalg.norm(f_bar[ci])
                P = k * t_ratio * min_angle / gamma_v
                apd = (1 + P) * dist

                if apd < best_apd:
                    best_apd = apd
                    best_idx = ci

        if best_idx is not None and best_idx not in selected_indices:
            selected_indices.append(best_idx)

    selected = [valid_pop[i] for i in selected_indices[:n_select]]
    return selected, n_inactive_fixed


def _manage_archive(X_archive, Y_archive, X_new, Y_new, NI, V0):
    """
    Algorithm 4: Manage training data archive A1.

    Keeps at most NI samples by removing duplicates and selecting
    diverse samples using reference vector clustering.
    """
    X_all = np.vstack([X_archive, X_new])
    Y_all = np.vstack([Y_archive, Y_new])

    # Remove duplicates
    _, unique_idx = np.unique(X_all, axis=0, return_index=True)
    X_all = X_all[unique_idx]
    Y_all = Y_all[unique_idx]

    if len(X_all) <= NI:
        return X_all, Y_all

    # Keep all newly added samples, remove from the older ones
    n_new = len(X_new)
    n_keep_old = NI - min(n_new, NI)

    if n_keep_old <= 0:
        return X_new[:NI], Y_new[:NI]

    X_old = X_all[:len(X_archive)]
    Y_old = Y_all[:len(Y_archive)]

    if len(X_old) <= n_keep_old:
        return np.vstack([X_old, X_new]), np.vstack([Y_old, Y_new])

    # Cluster old samples and select one per cluster
    n_clusters = min(n_keep_old, len(X_old))
    if n_clusters <= 1:
        selected_old = X_old[:n_keep_old]
        selected_old_y = Y_old[:n_keep_old]
    else:
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=3)
        labels = km.fit_predict(X_old)
        selected_old = []
        selected_old_y = []
        for c in range(n_clusters):
            mask = labels == c
            indices = np.where(mask)[0]
            if len(indices) > 0:
                pick = np.random.choice(indices)
                selected_old.append(X_old[pick])
                selected_old_y.append(Y_old[pick])
        selected_old = np.array(selected_old)
        selected_old_y = np.array(selected_old_y)

    X_result = np.vstack([selected_old, X_new])
    Y_result = np.vstack([selected_old_y, Y_new])

    return X_result[:NI], Y_result[:NI]


def _find_non_dominated(X, F):
    """Find non-dominated solutions from a set of objective vectors."""
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


def run_k_rvea(problem, config, save_history: bool = False):
    """
    K-RVEA Online: full Algorithm 2 from Chugh et al. (2016).

    Args:
        problem: pymoo Problem instance with _evaluate method
        config: dictionary with:
            - 'seed': random seed
            - 'n_objetivos': number of objectives (2)
            - 'population_size': reference vector count ≈ pop size
            - 'n_generations': max generations for inner RVEA loop (used as tmax)
            - 'FEmax': maximum number of true function evaluations (default 300)
            - 'krvea_wmax': RVEA generations before Kriging update (default 20)
            - 'krvea_u': individuals to re-evaluate per update (default 5)
            - 'krvea_delta': threshold for diversity/convergence switch
            - 'crossover_prob', 'crossover_eta', 'mutation_prob', 'mutation_eta'
            - 'k_tournament'
            - 'rvea_alpha': APD rate parameter (default 2.0)
        save_history: when True, records a snapshot of the cumulative
            archive A2 (all truly-evaluated points) at the end of each
            outer iteration (Kriging update cycle).

    Returns:
        df_pareto: DataFrame with non-dominated solutions (true evaluations)
        info: dict with metadata (FE count, archive sizes, etc.)
        history: list of {'generation': int (update index),
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
    wmax = config.get('krvea_wmax', 20)
    u = config.get('krvea_u', 5)
    NI = config.get('krvea_NI', 11 * n_var - 1)

    n_partitions = config['population_size'] - 1
    V0 = generate_reference_vectors(n_obj, n_partitions)
    Vf = V0.copy()
    pop_size = len(V0)

    config_local = config.copy()
    config_local['population_size'] = pop_size
    config_local['limite_inferior'] = xl
    config_local['limite_superior'] = xu
    config_local['tamanho_genotipo'] = n_var

    # ========== Phase 1: Initialization ==========
    X_init = _latin_hypercube_sampling(NI, n_var, xl, xu, seed=config['seed'])
    F_init = evaluate_problem(problem, X_init)
    FE = NI

    # Archives
    X_A1 = X_init.copy()   # training data archive
    Y_A1 = F_init.copy()
    X_A2 = X_init.copy()   # all evaluated solutions
    Y_A2 = F_init.copy()

    # Train initial Kriging models
    kriging_models = _train_kriging_models(X_A1, Y_A1, n_obj)

    # Create initial population from Kriging predictions
    population = []
    for i in range(pop_size):
        genotype = np.random.uniform(xl, xu).tolist()
        population.append(Individual(genotype))
    _evaluate_with_kriging(population, kriging_models)

    prev_n_inactive_fixed = 0
    tu = 0
    generation_global = 0

    progress_log = []
    history = [] if save_history else None
    if save_history:
        history.append({
            'generation': 0,
            'population': [{'genotype': list(X_A2[i]),
                            'fitness': list(Y_A2[i])}
                           for i in range(len(X_A2))],
        })

    # ========== Phase 2-3: Main loop ==========
    pbar = tqdm(total=FEmax, initial=FE, desc="K-RVEA Online (FE)")

    while FE < FEmax:
        # Phase 2: Run RVEA for wmax generations using Kriging
        for w in range(wmax):
            generation_global += 1

            offspring = create_offspring_population(population, config_local)
            _evaluate_with_kriging(offspring, kriging_models)

            combined = population + offspring
            Va = adapt_reference_vectors(V0, combined)
            population = rvea_environmental_selection(
                combined, config_local, Va, generation_global
            )

            if len(population) == 0:
                population = combined[:pop_size]

        # Phase 3: Update surrogate
        selected_for_reeval, prev_n_inactive_fixed = _select_for_reevaluation(
            population, config_local, V0,
            adapt_reference_vectors(V0, population),
            u, prev_n_inactive_fixed, Vf
        )

        if len(selected_for_reeval) == 0:
            # Fallback: pick random individuals
            n_pick = min(u, len(population))
            indices = np.random.choice(len(population), size=n_pick, replace=False)
            selected_for_reeval = [population[i] for i in indices]

        # Re-evaluate selected individuals with true function
        X_reeval = np.array([ind.genotype for ind in selected_for_reeval])
        n_reeval = min(len(X_reeval), FEmax - FE)
        X_reeval = X_reeval[:n_reeval]

        if len(X_reeval) == 0:
            break

        F_reeval = evaluate_problem(problem, X_reeval)
        FE += len(X_reeval)
        pbar.update(len(X_reeval))

        # Add to archives
        X_A2 = np.vstack([X_A2, X_reeval])
        Y_A2 = np.vstack([Y_A2, F_reeval])

        # Manage A1 (keep at most NI training samples)
        X_A1, Y_A1 = _manage_archive(X_A1, Y_A1, X_reeval, F_reeval, NI, V0)

        # Retrain Kriging models
        kriging_models = _train_kriging_models(X_A1, Y_A1, n_obj)

        tu += 1

        progress_log.append({
            'update': tu,
            'FE': FE,
            'archive_A1_size': len(X_A1),
            'archive_A2_size': len(X_A2),
            'generation_global': generation_global,
        })

        if save_history:
            history.append({
                'generation': tu,
                'population': [{'genotype': list(X_A2[i]),
                                'fitness': list(Y_A2[i])}
                               for i in range(len(X_A2))],
            })

    pbar.close()

    # ========== Finalization ==========
    # Return non-dominated solutions from archive A2
    X_nd, F_nd = _find_non_dominated(X_A2, Y_A2)

    data = {}
    for i in range(X_nd.shape[1]):
        data[f'x_{i+1}'] = X_nd[:, i]
    for j in range(F_nd.shape[1]):
        data[f'f{j+1}'] = F_nd[:, j]
    df_pareto = pd.DataFrame(data)

    info = {
        'total_FE': FE,
        'n_updates': tu,
        'n_generations': generation_global,
        'archive_A2_size': len(X_A2),
        'n_nondominated': len(X_nd),
        'progress': progress_log,
    }

    if config.get('verbose', True):
        print(f"\n✅ K-RVEA Online concluído!")
        print(f"   Avaliações reais: {FE}/{FEmax}")
        print(f"   Atualizações do Kriging: {tu}")
        print(f"   Soluções não-dominadas: {len(X_nd)}")

    return df_pareto, info, history
