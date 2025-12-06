import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from src.nsga2.individual     import Individual
from src.nsga2.inicialization import initialize_population
from src.nsga2.evaluation     import evaluate_population, genotype_to_registro
from src.nsga2.offspring      import create_offspring_population
from src.nsga2.selection      import environmental_selection
from src.nsga2.utils          import collect_generation_stats, plot_optimization_progress


def run_my_nsga2(config: dict,
                 df_landscape: pd.DataFrame, 
                 input_initial_population: list = None
                ) -> tuple[pd.DataFrame, list, pd.DataFrame]:
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

    returns:
        df_pareto: dataframe com as soluções no front de Pareto encontrado
        pareto_front: lista de soluções no front de Pareto encontrado
        df_progress: dataframe com as estatísticas de progresso por geração
    """

    ######### 1. População Inicial (initial population)
    # Define random seed    
    np.random.seed(config['seed'])

    # Inicializando população de soluções    
    population, _ = initialize_population(config, input_initial_population)

    # Avalia fitness da população inicial
    evaluate_population(population, df_landscape, config['fitness_cols'], config['maximize'])
    

    ############# Loop principal das gerações
    progress_stats = []
    for generation in tqdm(range(config['n_generations'])):

        ######### 2. População Descendente (offspring population)
        # Criar população descendente Qt
        offspring = create_offspring_population(population, config)

        # Avalia fitness da população descendente
        evaluate_population(offspring, df_landscape, config['fitness_cols'], config['maximize'])


        ######### 3. Seleção Geracional (environmental selection)
        # Combinar Pt e Qt para formar Rt
        combined_population = population + offspring

        # Seleção geracional: selecionar N melhores para formar P(t+1)
        population = environmental_selection(combined_population, config['population_size'])

        # Rastreamento de progresso
        if config['track_progress']:
            stats = collect_generation_stats(population, generation, config)
            progress_stats.append(stats)


    ######### Finalização
    # Extrair front de Pareto final (rank 1)
    pareto_front = [ind for ind in population if ind.rank == 1]
        
    # Converter para registros e criar dataframe
    registros = [genotype_to_registro(ind.genotype) for ind in pareto_front]
    df_pareto = df_landscape[df_landscape['registro'].isin(registros)].copy()
    
    print(f"\n✅ Otimização concluída!")
    print(f"Soluções encontradas no front: {len(pareto_front)}")
    print(f"Registros únicos no dataframe: {len(df_pareto)}")

    if config['track_progress']:
        df_progress = pd.DataFrame(progress_stats)
        plot_optimization_progress(df_progress)
    else:
        df_progress = None


    return df_pareto, pareto_front, df_progress