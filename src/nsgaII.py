"""
NSGA-II: Non-dominated Sorting Genetic Algorithm II.

Implementation based on:
    Deb et al. "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"
    (IEEE TEVC 6(2), 2002).

PAPER ALGORITHM (Section III-C):
    1. Create random parent population P_0 of size N.
    2. Create offspring Q_t via binary tournament (crowded comparison), SBX, PM.
    3. Combine R_t = P_t ∪ Q_t (size 2N).
    4. Fast non-dominated sort on R_t → fronts F_1, F_2, ...
    5. Fill P_{t+1} from F_1, F_2, ... until last front that fits.
    6. For the last partial front, sort by crowding distance descending.
    7. Repeat from step 2.

DEVIATIONS / NOTES:
    - The paper uses η_c = η_m = 20 (Section IV).  This implementation uses
      η_c = 15, η_m = 20 by default (configurable via config dict).
    - When kriging_models is provided, evaluation is done via Kriging
      surrogate instead of discrete landscape lookup.  This is the
      "NSGA-II + surrogate" variant, not a deviation from the core
      algorithm — only the fitness source changes.
"""
import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from src.nsga2.individual     import Individual
from src.nsga2.inicialization import initialize_population
from src.nsga2.evaluation     import evaluate_population
from src.nsga2.offspring      import create_offspring_population
from src.nsga2.selection      import environmental_selection
from src.nsga2.utils          import collect_generation_stats, plot_optimization_progress
from src.kriging_evaluation   import evaluate_population_kriging


def run_my_nsga2(config: dict,
                 df_landscape=None,
                 save_history: bool = False,
                 input_initial_population: list = None,
                 kriging_models=None,
                ) -> tuple[pd.DataFrame, list, pd.DataFrame, list]:
    """
    Implementação completa do algoritmo NSGA-II, seguindo o paper original de Deb et al. (2002)

    Algoritmo:
        1. População Inicial - P(t) 
           (initial population)
            - inicializa população inicial aleatoriamente
            - avalia Fitness da população inicial

        2. População Descendente - Q(t) 
           (offspring population)
            - seleciona conjunto de N pais via seleção por torneio (K = 2)
            - gera população descendente (N filhos) via operações genéticas (crossover e mutação) - sobre conjunto de pais
            - avalia Fitness da população descendente

        3. Seleção Ambiental - P(t+1) 
            (environmental selection)
             - população Combinada (Rt) = população Inicial (Pt) + Descendente (Qt)
             - utilizamos a operação "fast-non-dominated-sort" em Rt, para definir os fronts (ranking) de dominância
             - calculamos a crowding distance das soluções em cada front
             - selecionamos a população resultante P(t+1) a partir dos melhores fronts que couberem inteiros em N
                 + preenche c/ melhores soluções (crowding distance) do primeiro conjunto que não cabe inteiro

        > Repete 2 e 3 a cada geração, até atingir critério de parada.

    args:
        config: dicionário de configuração
        df_landscape: dataframe com o landscape de fitness
        input_initial_population: lista de genótipos (opcional)
        save_history: se True, salva o histórico de populações (default: False)

    returns:
        df_pareto: dataframe com as soluções no front de Pareto encontrado
        pareto_front: lista de soluções no front de Pareto encontrado
        df_progress: dataframe com as estatísticas de progresso por geração
        history: lista com histórico de populações (se save_history=True), senão None
    """

    ######### 1. População Inicial (initial population)
    # Define random seed    
    np.random.seed(config['seed'])

    # Inicializando população de soluções    
    population, _ = initialize_population(config, input_initial_population)

    # Avalia fitness da população inicial
    if kriging_models is not None:
        initial_stats = evaluate_population_kriging(population, kriging_models)
    else:
        initial_stats = evaluate_population(population, df_landscape, config['fitness_cols'])
    
    # Inicializar histórico se solicitado
    history = [] if save_history else None
    if save_history:
        # Salvar população inicial (geração 0)
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
            'mapping_stats': {
                'population': initial_stats
            }
        })

    ############# Loop principal das gerações
    progress_stats = []
    for generation in tqdm(range(config['n_generations'])):

        ######### 2. População Descendente (offspring population)
        # Criar população descendente Qt
        offspring = create_offspring_population(population, config)

        # Avalia fitness da população descendente
        if kriging_models is not None:
            offspring_stats = evaluate_population_kriging(offspring, kriging_models)
        else:
            offspring_stats = evaluate_population(offspring, df_landscape, config['fitness_cols'])


        ######### 3. Seleção Geracional (environmental selection)
        # Combinar Pt e Qt para formar Rt
        combined_population = population + offspring
        
        # Calcular stats da combined_population
        combined_stats = {
            'total': len(combined_population),
            'mapped': sum(1 for ind in combined_population if ind.mapping_success),
            'not_found': sum(1 for ind in combined_population if not ind.mapping_success)
        }

        # Seleção geracional: selecionar N melhores para formar P(t+1)
        population = environmental_selection(combined_population, config)

        # Rastreamento de progresso
        if config['track_progress']:
            stats = collect_generation_stats(population, generation, config)
            progress_stats.append(stats)

        # Salvar snapshot da população se histórico está ativado
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
                'mapping_stats': {
                    'offspring': offspring_stats,
                    'combined': combined_stats
                }
            })


    ######### Finalização
    # Criar dataframe com as soluções finais
    records = []
    for ind in [p for p in population if p.rank == 1]:
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
        print(f"\n✅ Otimização concluída!")
        print(f"Registros únicos no dataframe: {len(df_pareto)}")

    if config['track_progress']:
        df_progress = pd.DataFrame(progress_stats)
        if config.get('mostrar_grafico', True):
            plot_optimization_progress(df_progress)
    else:
        df_progress = None


    return df_pareto, df_progress, history