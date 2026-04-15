"""
Prob-MOEA/D: Probabilistic Selection in Decomposition-Based EA for Offline MOO.

Implementation based on:
    Mazumdar et al. "Probabilistic Selection Approaches in Decomposition-Based
    Evolutionary Algorithms for Offline Data-Driven Multiobjective Optimization"
    (IEEE TEVC 26(5), 2022).

PAPER ALGORITHM (Algorithm 1):
    1. Build Kriging surrogates (one per objective) from offline data.
    2. Generate uniformly distributed reference vectors via simplex-lattice.
    3. For each generation:
       a. Generate offspring via crossover/mutation in the neighbourhood.
       b. Evaluate offspring with Kriging → (mean, std) per objective.
       c. Draw S Monte Carlo samples from N(mean, std).
       d. Compute the PBI scalarisation for each sample.
       e. Estimate PDF of PBI via Kernel Density Estimation (KDE).
       f. Calculate P_wrong (Eq. 8) via double integration of the KDE PDFs.
       g. Update neighbour if P_wrong(offspring < neighbour) > 0.5.

SIMPLIFICATION IN THIS IMPLEMENTATION:
    Steps (e) and (f) are simplified.  Instead of KDE + double integration
    to compute P_wrong, we use **direct Monte Carlo win-counting**:
        n_off_wins = count(PBI(sample_offspring) < PBI(sample_neighbour))
        update if n_off_wins / n_mc_samples > 0.5
    This captures the same probabilistic effect — the offspring is selected
    when it is better in more than half of the stochastic comparisons — but
    avoids the O(|P_j|^2) KDE fitting and numerical integration cost
    described in the paper.  The theoretical justification is that the MC
    win rate converges to P_wrong as S → ∞ (law of large numbers).

    See paper Eq. 7-9 and Section III-B for the full KDE-based formulation.
(offline with pre-computed surrogate predictions and MCMC error distributions).
"""

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from src.k_rvea.individual import Individual
from src.k_rvea.inicialization import initialize_population
from src.k_rvea.offspring import (
    simulated_binary_crossover,
    polynomial_mutation,
    create_offspring_population,
)
from src.k_rvea.selection import generate_reference_vectors
from src.kriging_evaluation import evaluate_population_kriging, get_kriging_uncertainty


def _compute_pbi(f, z_min, v, penalty=5.0):
    """PBI (Penalty-based Boundary Intersection) scalarizing function."""
    d = f - z_min
    v_norm = v / (np.linalg.norm(v) + 1e-12)
    d1 = np.dot(d, v_norm)
    d2 = np.linalg.norm(d - d1 * v_norm)
    return d1 + penalty * d2


def _evaluate_with_landscape(population, df_landscape, fitness_cols):
    """Evaluate population using discrete landscape lookup (same as k_rvea)."""
    from src.k_rvea.evaluation import evaluate_population
    return evaluate_population(population, df_landscape, fitness_cols)


def _get_uncertainty_from_mcmc(df_previsao, df_mcmc, n_obj=2):
    """Compute per-region std of MCMC errors for N objectives.

    Returns dict: region -> {'std_f1': ..., 'std_f2': ..., ...}
    """
    import re as _re
    erro_cols = sorted([c for c in df_mcmc.columns if _re.match(r'^erro_f\d+$', c)],
                       key=lambda c: int(c.split('_f')[1]))
    agg = {ec: 'std' for ec in erro_cols}
    stats = df_mcmc.groupby('regiao').agg(**{
        f'std_f{ec.split("_f")[1]}': (ec, 'std') for ec in erro_cols
    }).to_dict('index')
    return stats


def _find_non_dominated_from_pop(population):
    """Extract non-dominated solutions from population."""
    valid = [ind for ind in population if ind.fitness is not None]
    n = len(valid)
    is_dominated = [False] * n

    for i in range(n):
        if is_dominated[i]:
            continue
        for j in range(n):
            if i == j or is_dominated[j]:
                continue
            fi = valid[i].fitness
            fj = valid[j].fitness
            if all(fj[k] <= fi[k] for k in range(len(fi))) and any(fj[k] < fi[k] for k in range(len(fi))):
                is_dominated[i] = True
                break

    return [valid[i] for i in range(n) if not is_dominated[i]]


def run_prob_moead(config, df_landscape=None, df_previsao=None, df_mcmc=None,
                   kriging_models=None):
    """
    Prob-MOEA/D (offline): MOEA/D with probabilistic PBI selection.

    Based on: Mazumdar et al. (2022) "Probabilistic Selection Approaches in
    Decomposition-Based Evolutionary Algorithms for Offline Data-Driven
    Multiobjective Optimization", IEEE TEVC 26(5).

    When ``kriging_models`` is provided, uses native Kriging (mean, std) for
    uncertainty — matching the paper's use of Kriging surrogates.
    Falls back to CatBoost landscape + MCMC stds when kriging_models is None.

    Returns:
        df_pareto, df_progress, None
    """
    np.random.seed(config['seed'])

    n_obj = config['n_objetivos']
    pop_size = config['population_size']
    n_gen = config['n_generations']
    fitness_cols = config['fitness_cols']

    n_partitions = pop_size - 1
    V = generate_reference_vectors(n_obj, n_partitions)
    actual_pop_size = len(V)

    # Neighborhood: T closest reference vectors for each vector
    T = config.get('moead_neighborhood', 20)
    n_mc_samples = config.get('prob_moead_samples', 100)
    pbi_penalty = config.get('moead_pbi_penalty', 5.0)

    # Compute distances between reference vectors for neighborhoods
    n_ref = len(V)
    dists = np.zeros((n_ref, n_ref))
    for i in range(n_ref):
        for j in range(n_ref):
            dists[i, j] = np.linalg.norm(V[i] - V[j])

    neighborhoods = np.argsort(dists, axis=1)[:, :T]

    _use_kriging = kriging_models is not None

    if not _use_kriging:
        region_stds = _get_uncertainty_from_mcmc(df_previsao, df_mcmc)
        import re as _re
        _x_cols_prev = sorted([c for c in df_previsao.columns if _re.match(r'^x_\d+$', c)],
                              key=lambda c: int(c.split('_')[1]))
        from scipy.spatial import cKDTree as _cKDTree
        _region_tree = _cKDTree(df_previsao[_x_cols_prev].values.astype(float))

        def _get_region_for_genotype(genotype, df_prev):
            query = np.array([genotype[i] for i in range(len(_x_cols_prev))], dtype=float)
            _, idx = _region_tree.query(query)
            return df_prev.iloc[idx].get('regiao', 1)

    # Initialize population
    config_local = config.copy()
    config_local['population_size'] = actual_pop_size
    population, _ = initialize_population(config_local)
    if _use_kriging:
        evaluate_population_kriging(population, kriging_models)
    else:
        _evaluate_with_landscape(population, df_landscape, fitness_cols)

    # Assign each individual to its closest reference vector
    pop_assignment = list(range(min(actual_pop_size, len(population))))

    z_min = np.array([
        min(ind.fitness[k] for ind in population if ind.fitness is not None)
        for k in range(n_obj)
    ])

    progress_stats = []

    for generation in tqdm(range(n_gen)):
        # Update z_min
        for ind in population:
            if ind.fitness is not None:
                for k in range(n_obj):
                    z_min[k] = min(z_min[k], ind.fitness[k])

        # For each subproblem
        for i in range(min(actual_pop_size, len(population))):
            # Generate offspring from neighborhood
            neighbors = neighborhoods[i % n_ref]
            p1_idx = np.random.choice(neighbors)
            p2_idx = np.random.choice(neighbors)

            p1_idx = min(p1_idx, len(population) - 1)
            p2_idx = min(p2_idx, len(population) - 1)

            parent1 = population[p1_idx]
            parent2 = population[p2_idx]

            c1_geno, _ = simulated_binary_crossover(
                parent1, parent2,
                eta=config['crossover_eta'],
                prob=config['crossover_prob'],
                xl=config['limite_inferior'],
                xu=config['limite_superior']
            )
            c1_geno = polynomial_mutation(
                Individual(c1_geno),
                eta=config['mutation_eta'],
                prob=config['mutation_prob'],
                xl=config['limite_inferior'],
                xu=config['limite_superior']
            )

            offspring = Individual(list(c1_geno) if not isinstance(c1_geno, list) else c1_geno)
            temp_pop = [offspring]
            if _use_kriging:
                evaluate_population_kriging(temp_pop, kriging_models)
            else:
                _evaluate_with_landscape(temp_pop, df_landscape, fitness_cols)

            if offspring.fitness is None:
                continue

            if _use_kriging:
                _, off_sigma = get_kriging_uncertainty(offspring.genotype, kriging_models)
            else:
                offspring_region = _get_region_for_genotype(offspring.genotype, df_previsao)
                off_stds = region_stds.get(offspring_region, {})
                off_sigma = np.array([off_stds.get(f'std_f{k+1}', 0.1) for k in range(n_obj)])

            # Probabilistic update in neighborhood
            ref_vec = V[i % n_ref]

            for j_idx in neighbors:
                j = min(j_idx, len(population) - 1)
                neighbor = population[j]
                if neighbor.fitness is None:
                    population[j] = offspring
                    continue

                if _use_kriging:
                    _, nb_sigma = get_kriging_uncertainty(neighbor.genotype, kriging_models)
                else:
                    neighbor_region = _get_region_for_genotype(neighbor.genotype, df_previsao)
                    nb_stds = region_stds.get(neighbor_region, {})
                    nb_sigma = np.array([nb_stds.get(f'std_f{k+1}', 0.1) for k in range(n_obj)])

                # Monte Carlo probabilistic comparison using PBI
                off_mean = np.array(offspring.fitness)
                nb_mean = np.array(neighbor.fitness)

                n_off_wins = 0
                for _ in range(n_mc_samples):
                    off_sample = off_mean + np.random.randn(n_obj) * off_sigma
                    nb_sample = nb_mean + np.random.randn(n_obj) * nb_sigma

                    pbi_off = _compute_pbi(off_sample, z_min, V[j_idx % n_ref], pbi_penalty)
                    pbi_nb = _compute_pbi(nb_sample, z_min, V[j_idx % n_ref], pbi_penalty)

                    if pbi_off < pbi_nb:
                        n_off_wins += 1

                # Probabilistic update: if offspring wins more than 50%
                if n_off_wins / n_mc_samples > 0.5:
                    population[j] = offspring

        if config.get('track_progress', False):
            fitness_values = [ind.fitness for ind in population if ind.fitness is not None]
            if fitness_values:
                fa = np.array(fitness_values)
                stat = {'generation': generation, 'pop_size': len(population)}
                for k in range(fa.shape[1]):
                    stat[f'obj{k+1}_mean'] = np.mean(fa[:, k])
                progress_stats.append(stat)

    # Extract non-dominated solutions
    nd_pop = _find_non_dominated_from_pop(population)

    records = []
    for ind in nd_pop:
        row = {}
        for i in range(len(ind.genotype)):
            row[f'x_{i+1}'] = ind.genotype[i]
        if ind.fitness:
            for j in range(len(ind.fitness)):
                row[f'fitness{j+1}'] = ind.fitness[j]
        if ind.mapped_point:
            row.update(ind.mapped_point)
        row['mapping_success'] = ind.mapping_success
        records.append(row)
    df_pareto = pd.DataFrame(records)

    if config.get('verbose', True):
        print(f"\n✅ Prob-MOEA/D concluído! Soluções não-dominadas: {len(nd_pop)}")

    df_progress = pd.DataFrame(progress_stats) if progress_stats else None
    return df_pareto, df_progress, None
