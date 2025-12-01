# Mapeamento genótipo <> fenótipo
def genotype_to_registro(genotype):
    """Converte lista de 6 dígitos em número de registro"""
    return int(''.join(map(str, genotype)))

def registro_to_genotype(registro):
    """Converte número de registro em lista de 6 dígitos"""
    return [int(d) for d in f"{registro:06d}"]

# Avalia Fitness 1 indivíduo
def individual_fitness_evaluation(genotype, df_landscape, fitness_cols, maximize = False):
    """Obtém fitness do dataframe para um determinado genótipo"""

    # Identifica a solucao no dataframe de fitness landscape
    registro = genotype_to_registro(genotype)
    row = df_landscape[df_landscape['registro'] == registro]

    # Coleta fitness (se registro não existe, retornar valores muito ruins)
    if len(row) == 0:
        fitness1 = 1e6
        fitness2 = 1e6
    else:
        fitness1 = row[fitness_cols[0]].values[0]
        fitness2 = row[fitness_cols[1]].values[0]

    # Se for um problema de maximizacao, inverte os valores de fitness
    if maximize:
        fitness1 = -fitness1
        fitness2 = -fitness2
    
    return [fitness1, fitness2]


# Avalia Fitness 1 população
def evaluate_population(population, df_landscape, fitness_cols, maximize = False):
    """Avalia a fitness de todos os indivíduos na população"""
    for individual in population:
        individual.fitness = individual_fitness_evaluation(individual.genotype, df_landscape, fitness_cols, maximize)