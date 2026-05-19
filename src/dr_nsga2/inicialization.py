import numpy as np
from src.dr_nsga2.individual import Individual


def initialize_population(config, input_initial_population=None):

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

    initial_population = []
    for i in range(config['population_size']):
        genotype = initial_genotypes[i].tolist()
        initial_population.append(Individual(genotype))

    return initial_population, initial_genotypes
