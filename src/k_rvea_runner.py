import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from src.k_rvea.individual     import Individual
from src.k_rvea.inicialization import initialize_population
from src.k_rvea.evaluation     import evaluate_population
from src.k_rvea.offspring      import create_offspring_population
from src.k_rvea.selection      import generate_reference_vectors, environmental_selection
from src.k_rvea.utils          import collect_generation_stats, plot_optimization_progress


def run_k_rvea(config: dict,
               df_landscape: pd.DataFrame,
               save_history: bool = False,
               input_initial_population: list = None,
              ) -> tuple[pd.DataFrame, list, pd.DataFrame, list]:
    """
    K-RVEA (offline): Reference Vector Guided EA with surrogate fitness.

    Based on: Chugh et al. "A Surrogate-assisted Reference Vector Guided
    Evolutionary Algorithm for Computationally Expensive Many-objective
    Optimization" (IEEE TEVC 2016).

    In the offline data-driven setting, the Kriging model management
    component (re-evaluation and model update) does not apply. The
    algorithm reduces to RVEA using surrogate predictions as fitness.

    Key differences from NSGA-II:
    - Uses reference vectors (simplex-lattice design) instead of crowding distance
    - Selection based on Angle Penalized Distance (APD) which balances
      convergence and diversity via adaptive penalty
    - Population size = number of reference vectors

    Args:
        config: algorithm configuration dictionary.
                Uses config['population_size'] - 1 as number of partitions
                for reference vector generation, yielding population_size vectors.
        df_landscape: landscape DataFrame with fitness1, fitness2 columns
        save_history: whether to save population history
        input_initial_population: optional initial population genotypes

    Returns:
        df_pareto: DataFrame with Pareto front solutions
        df_progress: progress statistics DataFrame
        history: population history (if save_history=True)
    """
    np.random.seed(config['seed'])

    n_objectives = config['n_objetivos']
    n_partitions = config['population_size'] - 1
    V0 = generate_reference_vectors(n_objectives, n_partitions)
    pop_size = len(V0)

    config_local = config.copy()
    config_local['population_size'] = pop_size

    population, _ = initialize_population(config_local, input_initial_population)

    initial_stats = evaluate_population(population, df_landscape, config['fitness_cols'])

    history = [] if save_history else None
    if save_history:
        population_snapshot = [
            {
                'genotype': ind.genotype.copy(),
                'fitness': ind.fitness.copy() if ind.fitness is not None else None,
                'mapped_point': ind.mapped_point.copy() if ind.mapped_point else None,
                'mapping_success': ind.mapping_success
            }
            for ind in population
        ]
        history.append({
            'generation': 0,
            'population': population_snapshot,
            'mapping_stats': {'population': initial_stats}
        })

    progress_stats = []
    for generation in tqdm(range(config['n_generations'])):

        offspring = create_offspring_population(population, config_local)

        offspring_stats = evaluate_population(offspring, df_landscape, config['fitness_cols'])

        combined_population = population + offspring

        population = environmental_selection(combined_population, config_local, V0, generation)

        if config.get('track_progress', False):
            stats = collect_generation_stats(population, generation, config)
            progress_stats.append(stats)

        if save_history:
            population_snapshot = [
                {
                    'genotype': ind.genotype.copy(),
                    'fitness': ind.fitness.copy() if ind.fitness is not None else None,
                    'mapped_point': ind.mapped_point.copy() if ind.mapped_point else None,
                    'mapping_success': ind.mapping_success
                }
                for ind in population
            ]
            history.append({
                'generation': generation + 1,
                'population': population_snapshot,
                'mapping_stats': {'offspring': offspring_stats}
            })

    df_pareto = pd.DataFrame([
        {
            'x_1': ind.genotype[0],
            'x_2': ind.genotype[1],
            'fitness1': ind.fitness[0],
            'fitness2': ind.fitness[1],
            'x_1_landscape': ind.mapped_point['x_1_landscape'] if ind.mapped_point else None,
            'x_2_landscape': ind.mapped_point['x_2_landscape'] if ind.mapped_point else None,
            'f1': ind.mapped_point['f1'] if ind.mapped_point else None,
            'f2': ind.mapped_point['f2'] if ind.mapped_point else None,
            'f1_original': ind.mapped_point['f1_original'] if ind.mapped_point else None,
            'f2_original': ind.mapped_point['f2_original'] if ind.mapped_point else None,
            'f1_predicted': ind.mapped_point['f1_predicted'] if ind.mapped_point else None,
            'f2_predicted': ind.mapped_point['f2_predicted'] if ind.mapped_point else None,
            'mapping_success': ind.mapping_success
        }
        for ind in population if ind.rank == 1
    ])

    if config.get('verbose', True):
        print(f"\n✅ K-RVEA (offline) concluído!")
        print(f"Soluções no front de Pareto: {len(df_pareto)}")

    if config.get('track_progress', False) and progress_stats:
        df_progress = pd.DataFrame(progress_stats)
        if config.get('mostrar_grafico', True):
            plot_optimization_progress(df_progress)
    else:
        df_progress = None

    return df_pareto, df_progress, history
