"""
DR-NSGA-II: Dual-Ranking NSGA-II for Offline Data-Driven MOO.

Implementation based on:
    Lyu et al. "Uncertainty-Aware Dual-Ranking Strategy for Offline
    Data-Driven Multi-Objective Optimization" (AAAI 2026).

PAPER ALGORITHM (Algorithm 2):
    1. Train surrogate models on offline data.
    2. For each generation:
       a. Generate offspring via SBX + PM.
       b. Evaluate with surrogate → f_ori(x) = mu(x).
       c. Compute adjusted fitness: f_adj(x) = mu(x) + z * sigma(x)  (Eq. 15).
       d. Non-dominated sort on f_ori → rank_ori.
       e. Non-dominated sort on f_adj → rank_adj.
       f. avg_rank = mean(rank_ori, rank_adj)  (Algorithm 2, line 5).
       g. Rebuild hybrid fronts from avg_rank.
       h. Crowding distance on f_ori only.

DEVIATIONS / NOTES:
    - The paper evaluates four surrogate types: Kriging, QR, MCD, BNN.
      This implementation uses **Kriging only** (when kriging_models is
      provided), which provides native (mean, std) matching Eq. 15 exactly.
    - The paper's DR strategy is surrogate-agnostic (Algorithm 2 works the
      same regardless of the surrogate choice); our Kriging-only choice
      does not affect the core dual-ranking mechanism.
    - When kriging_models is None, falls back to CatBoost predictions +
      MCMC-derived std for backward compatibility with the discrete
      landscape approach.
"""
import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from src.dr_nsga2.individual     import Individual
from src.dr_nsga2.inicialization import initialize_population
from src.dr_nsga2.evaluation     import evaluate_population
from src.kriging_evaluation      import evaluate_population_kriging_dual
from src.dr_nsga2.offspring      import create_offspring_population
from src.dr_nsga2.selection      import environmental_selection
from src.dr_nsga2.utils          import collect_generation_stats, plot_optimization_progress


def create_landscape_for_dr_nsga2(df_previsao, df_mcmc, z=1.28, decision_variables=None):
    """Create landscape with predicted + uncertainty-adjusted fitness for DR-NSGA-II.

    Supports N decision variables and M objectives.
    """
    import re as _re
    if decision_variables is None:
        decision_variables = sorted(
            [c for c in df_previsao.columns if _re.match(r'^x_\d+$', c)],
            key=lambda c: int(c.split('_')[1]))

    erro_cols = sorted([c for c in df_mcmc.columns if _re.match(r'^erro_f\d+$', c)],
                       key=lambda c: int(c.split('_f')[1]))
    agg_kw = {f'std_f{ec.split("_f")[1]}': (ec, 'std') for ec in erro_cols}
    error_stats = df_mcmc.groupby('regiao').agg(**agg_kw).reset_index()

    keep = set(decision_variables + ['regiao'])
    for c in df_previsao.columns:
        if _re.match(r'^f\d+', c):
            keep.add(c)
    cols = [c for c in df_previsao.columns if c in keep]
    df_landscape = df_previsao[cols].merge(error_stats, on='regiao', how='left')

    obj_indices = sorted(set(int(c[1:]) for c in df_previsao.columns if _re.match(r'^f\d+$', c)))
    for j in obj_indices:
        df_landscape[f'fitness{j}'] = df_landscape[f'f{j}_predicted']
        std_col = f'std_f{j}'
        if std_col in df_landscape.columns:
            df_landscape[f'fitness{j}_adj'] = df_landscape[f'f{j}_predicted'] + z * df_landscape[std_col]

    return df_landscape


def run_dr_nsga2(config: dict,
                 df_landscape=None,
                 save_history: bool = False,
                 input_initial_population: list = None,
                 kriging_models=None,
                 z=1.28,
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

    if kriging_models is not None:
        initial_stats = evaluate_population_kriging_dual(population, kriging_models, z)
    else:
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

        if kriging_models is not None:
            offspring_stats = evaluate_population_kriging_dual(offspring, kriging_models, z)
        else:
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

    records = []
    for ind in [p for p in population if p.avg_rank is not None and p.avg_rank <= 1.0]:
        row = {}
        for i in range(len(ind.genotype)):
            row[f'x_{i+1}'] = ind.genotype[i]
        if ind.fitness:
            for j in range(len(ind.fitness)):
                row[f'fitness{j+1}'] = ind.fitness[j]
        if ind.mapped_point:
            row.update(ind.mapped_point)
        row['mapping_success'] = ind.mapping_success
        row['avg_rank'] = ind.avg_rank
        records.append(row)
    df_pareto = pd.DataFrame(records)

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
