"""
Prob-MOEA/D: Probabilistic Selection in Decomposition-Based EA for Offline MOO.

Implementation based on:
Mazumdar et al. "Probabilistic Selection Approaches in Decomposition-Based
Evolutionary Algorithms for Offline Data-Driven Multiobjective Optimization"
(IEEE TEVC 2022).

The algorithm modifies MOEA/D's PBI selection to incorporate Kriging uncertainty:
1. Build Kriging surrogates from offline data
2. For each solution, draw Monte Carlo samples from the Kriging posterior
3. Compute PBI selection criterion on each sample
4. Use probabilistic comparison: update if P(offspring better) > 0.5

Adapted to work with the user's discrete landscape framework
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


def _get_uncertainty_from_mcmc(df_previsao, df_mcmc):
    """
    Compute per-region std of MCMC errors to use as Kriging-like uncertainty.
    Returns a dict: region -> (std_f1, std_f2).
    """
    error_stats = df_mcmc.groupby('regiao').agg(
        std_f1=('erro_f1', 'std'),
        std_f2=('erro_f2', 'std')
    ).to_dict('index')
    return error_stats


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


def run_prob_moead(config, df_landscape, df_previsao, df_mcmc):
    """
    Prob-MOEA/D (offline): MOEA/D with probabilistic PBI selection.

    Uses MCMC-derived uncertainty as a proxy for Kriging std,
    with Monte Carlo sampling for probabilistic comparisons.

    Args:
        config: algorithm configuration
        df_landscape: landscape DataFrame with fitness1, fitness2 (predicted)
        df_previsao: prediction DataFrame with regiao column
        df_mcmc: MCMC error samples DataFrame

    Returns:
        df_pareto: DataFrame with Pareto front solutions
        df_progress: progress stats
        history: None
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

    # Per-region uncertainty
    region_stds = _get_uncertainty_from_mcmc(df_previsao, df_mcmc)

    # Build region lookup for solutions
    def _get_region_for_genotype(genotype, df_prev):
        x1_round = round(genotype[0], 2)
        x2_round = round(genotype[1], 2)
        matches = df_prev[
            (df_prev['x_1'].round(2) == x1_round) &
            (df_prev['x_2'].round(2) == x2_round)
        ]
        if len(matches) > 0:
            return matches.iloc[0].get('regiao', 1)
        return 1

    # Initialize population
    config_local = config.copy()
    config_local['population_size'] = actual_pop_size
    population, _ = initialize_population(config_local)
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
            _evaluate_with_landscape(temp_pop, df_landscape, fitness_cols)

            if offspring.fitness is None:
                continue

            # Get offspring uncertainty
            offspring_region = _get_region_for_genotype(offspring.genotype, df_previsao)
            off_stds = region_stds.get(offspring_region, {'std_f1': 0.1, 'std_f2': 0.1})
            off_sigma = np.array([off_stds.get('std_f1', 0.1), off_stds.get('std_f2', 0.1)])

            # Probabilistic update in neighborhood
            ref_vec = V[i % n_ref]

            for j_idx in neighbors:
                j = min(j_idx, len(population) - 1)
                neighbor = population[j]
                if neighbor.fitness is None:
                    population[j] = offspring
                    continue

                # Get neighbor uncertainty
                neighbor_region = _get_region_for_genotype(neighbor.genotype, df_previsao)
                nb_stds = region_stds.get(neighbor_region, {'std_f1': 0.1, 'std_f2': 0.1})
                nb_sigma = np.array([nb_stds.get('std_f1', 0.1), nb_stds.get('std_f2', 0.1)])

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
                progress_stats.append({
                    'generation': generation,
                    'pop_size': len(population),
                    'obj1_mean': np.mean(fa[:, 0]),
                    'obj2_mean': np.mean(fa[:, 1]),
                })

    # Extract non-dominated solutions
    nd_pop = _find_non_dominated_from_pop(population)

    df_pareto = pd.DataFrame([
        {
            'x_1': ind.genotype[0],
            'x_2': ind.genotype[1],
            'fitness1': ind.fitness[0],
            'fitness2': ind.fitness[1],
            'x_1_landscape': ind.mapped_point['x_1_landscape'] if ind.mapped_point else None,
            'x_2_landscape': ind.mapped_point['x_2_landscape'] if ind.mapped_point else None,
            'f1': ind.mapped_point.get('f1') if ind.mapped_point else None,
            'f2': ind.mapped_point.get('f2') if ind.mapped_point else None,
            'f1_original': ind.mapped_point.get('f1_original') if ind.mapped_point else None,
            'f2_original': ind.mapped_point.get('f2_original') if ind.mapped_point else None,
            'f1_predicted': ind.mapped_point.get('f1_predicted') if ind.mapped_point else None,
            'f2_predicted': ind.mapped_point.get('f2_predicted') if ind.mapped_point else None,
            'mapping_success': ind.mapping_success
        }
        for ind in nd_pop
    ])

    if config.get('verbose', True):
        print(f"\n✅ Prob-MOEA/D concluído! Soluções não-dominadas: {len(nd_pop)}")

    df_progress = pd.DataFrame(progress_stats) if progress_stats else None
    return df_pareto, df_progress, None
