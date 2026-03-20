import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from src.dr_nsga2.individual     import Individual
from src.dr_nsga2.inicialization import initialize_population
from src.dr_nsga2.evaluation     import evaluate_population
from src.dr_nsga2.offspring      import create_offspring_population
from src.dr_nsga2.selection      import environmental_selection
from src.dr_nsga2.utils          import collect_generation_stats, plot_optimization_progress


def create_landscape_for_dr_nsga2(df_previsao, df_mcmc, z=1.28, decision_variables=None):
    """
    Creates a landscape with both predicted fitness and uncertainty-adjusted fitness
    for DR-NSGA-II.

    The adjusted fitness penalizes uncertainty (for minimization problems):
        f_adj = f_predicted + z * std(error)

    where std(error) is the standard deviation of MCMC error samples per region.

    Args:
        df_previsao: DataFrame with predictions (x_1, x_2, f1, f2, f1_original, f2_original,
                     f1_predicted, f2_predicted, regiao)
        df_mcmc: DataFrame with MCMC error samples (erro_f1, erro_f2, regiao, id_simulacao)
        z: coefficient for uncertainty penalty (default 1.28, corresponding to 90th percentile)
        decision_variables: list of decision variable column names
    """
    if decision_variables is None:
        decision_variables = ['x_1', 'x_2']

    error_stats = df_mcmc.groupby('regiao').agg(
        std_f1=('erro_f1', 'std'),
        std_f2=('erro_f2', 'std')
    ).reset_index()

    cols = decision_variables + ['regiao', 'f1', 'f2', 'f1_original', 'f2_original', 'f1_predicted', 'f2_predicted']
    df_landscape = df_previsao[cols].merge(error_stats, on='regiao', how='left')

    df_landscape['fitness1'] = df_landscape['f1_predicted']
    df_landscape['fitness2'] = df_landscape['f2_predicted']

    df_landscape['fitness1_adj'] = df_landscape['f1_predicted'] + z * df_landscape['std_f1']
    df_landscape['fitness2_adj'] = df_landscape['f2_predicted'] + z * df_landscape['std_f2']

    return df_landscape


def run_dr_nsga2(config: dict,
                 df_landscape: pd.DataFrame,
                 save_history: bool = False,
                 input_initial_population: list = None,
                ) -> tuple[pd.DataFrame, list, pd.DataFrame, list]:
    """
    DR-NSGA-II: NSGA-II with Dual-Ranking strategy for offline data-driven MOO.

    Based on: Lyu et al. "Uncertainty-Aware Dual-Ranking Strategy for Offline
    Data-Driven Multi-Objective Optimization" (AAAI 2026).

    The algorithm modifies NSGA-II environmental selection:
    1. Non-dominated sort on original (predicted) fitness → rank_ori
    2. Non-dominated sort on adjusted fitness (predicted + z*σ) → rank_adj
    3. Final rank = mean(rank_ori, rank_adj)
    4. Hybrid fronts built from final rank
    5. Crowding distance on original fitness for tie-breaking

    Args:
        config: algorithm configuration dictionary
        df_landscape: landscape DataFrame with fitness1, fitness2,
                      fitness1_adj, fitness2_adj columns
        save_history: whether to save population history
        input_initial_population: optional initial population genotypes

    Returns:
        df_pareto: DataFrame with Pareto front solutions
        df_progress: progress statistics DataFrame
        history: population history (if save_history=True)
    """
    fitness_cols = config['fitness_cols']
    adjusted_fitness_cols = config.get('adjusted_fitness_cols', ['fitness1_adj', 'fitness2_adj'])

    np.random.seed(config['seed'])

    population, _ = initialize_population(config, input_initial_population)

    initial_stats = evaluate_population(population, df_landscape, fitness_cols, adjusted_fitness_cols)

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

        offspring = create_offspring_population(population, config)

        offspring_stats = evaluate_population(offspring, df_landscape, fitness_cols, adjusted_fitness_cols)

        combined_population = population + offspring

        population = environmental_selection(combined_population, config)

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
            'mapping_success': ind.mapping_success,
            'avg_rank': ind.avg_rank
        }
        for ind in population if ind.avg_rank is not None and ind.avg_rank <= 1.0
    ])

    if config.get('verbose', True):
        print(f"\n✅ DR-NSGA-II concluído!")
        print(f"Soluções no front de Pareto (avg_rank ≤ 1.0): {len(df_pareto)}")

    if config.get('track_progress', False) and progress_stats:
        df_progress = pd.DataFrame(progress_stats)
        if config.get('mostrar_grafico', True):
            plot_optimization_progress(df_progress)
    else:
        df_progress = None

    return df_pareto, df_progress, history
