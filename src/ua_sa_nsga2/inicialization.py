import numpy as np
from src.ua_sa_nsga2.individual import Individual


def initialize_population(config, input_initial_population = None):

    '''
    Inicializa população com valores aleatórios.

    args:
        config["population_size"]:  tamanho da população
        config["tamanho_genotipo"]: tamanho do genótipo
        config["limite_inferior"]:  limite inferior dos valores possíveis do genótipo
        config["limite_superior"]:  limite superior dos valores possíveis do genótipo
    
    returns:
        initial_population: população inicial (lista de objetos Individual)
        initial_genotypes: genótipos da população inicial (array numpy)

    note: Foi feito um teste de similaridade entre o resultado da população inicial 
        gerada abaixo vs gerada pelo nsga-II pymoo. Não são iguais. Para reprodutibilidade,
        de testes, nossa versão do nsga-II aceita receber uma população inicial.
    '''

    # Inicializando população de soluções (array de arrays)
    if input_initial_population is not None:
        initial_genotypes = input_initial_population
    else:
        n_var = config['tamanho_genotipo']
        xl    = config['limite_inferior']
        xu    = config['limite_superior']
        
        if config['tipo_variavel_genotipo'] == int:
            initial_genotypes = np.column_stack([np.random.randint(xl[i], xu[i] + 1, size=config['population_size']) 
                                                for i in range(n_var)])
        elif config['tipo_variavel_genotipo'] == float:
            initial_genotypes = np.column_stack([np.random.uniform(xl[i], xu[i], size=config['population_size']) 
                                                for i in range(n_var)])
    # Cria população de objetos Individual a partir dos genótipos
    initial_population = []
    for i in range(config['population_size']):
        genotype = initial_genotypes[i].tolist()
        initial_population.append(Individual(genotype, pop_size = 1 + config['population_size']))


    return initial_population, initial_genotypes