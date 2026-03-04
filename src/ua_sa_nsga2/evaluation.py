import pandas as pd
import numpy as np


# 1. Cria versões expandidas do landscape para garantir cobertura
def create_expanded_landscape(df_landscape):
    """Cria versões expandidas do landscape para garantir cobertura"""

    # 1 Cria versões expandidas do landscape para garantir cobertura
    df_original = df_landscape.copy()
    
    df_shift_x1 = df_landscape.copy()
    df_shift_x1['x_1'] = df_shift_x1['x_1'] + 0.01
    
    df_shift_x2 = df_landscape.copy()
    df_shift_x2['x_2'] = df_shift_x2['x_2'] + 0.01
    
    df_shift_both = df_landscape.copy()
    df_shift_both['x_1'] = df_shift_both['x_1'] + 0.01
    df_shift_both['x_2'] = df_shift_both['x_2'] + 0.01
    
    df_landscape_expanded = pd.concat([df_original, df_shift_x1, df_shift_x2, df_shift_both], 
                                   ignore_index=True)

    # 2. Arredonda x_1 e x_2 para 2 casas decimais
    df_landscape_expanded['x_1_round'] = df_landscape_expanded['x_1'].round(2)
    df_landscape_expanded['x_2_round'] = df_landscape_expanded['x_2'].round(2)

    return df_landscape_expanded


# 2. Função de mapeamento
def genotype_to_fitness(genotype, df_landscape_expanded, fitness_cols):
    """Mapeia genótipo para fitness arredondando para 2 casas decimais"""
    x1_round = round(genotype[0], 2)
    x2_round = round(genotype[1], 2)
    
    # Busca registros que correspondem aos valores arredondados
    matches = df_landscape_expanded[
        (df_landscape_expanded['x_1_round'] == x1_round) & 
        (df_landscape_expanded['x_2_round'] == x2_round)
    ]
    
    # Pega o primeiro registro se houver múltiplos
    if len(matches) > 0:
        row = matches.iloc[0]
        fitness1 = row[fitness_cols[0]]
        fitness2 = row[fitness_cols[1]]
        return [fitness1, fitness2]
    else:
        # Caso não encontre (não deveria acontecer com as cópias)
        raise ValueError(f"Nenhum registro encontrado para x_1={x1_round}, x_2={x2_round}")


# 3. Atualiza a função de avaliação
def evaluate_population(population, df_landscape, fitness_cols):
    """Avalia fitness de toda a população"""
    
    df_landscape_expanded = create_expanded_landscape(df_landscape)

    for individual in population:
        individual.fitness = genotype_to_fitness(
            individual.genotype, df_landscape_expanded, fitness_cols
        )






## Mapeamento genótipo <> fenótipo
#def genotype_to_registro(genotype):
#    """Converte lista de 6 dígitos em número de registro"""
#    return int(''.join(map(str, genotype)))
#
#def registro_to_genotype(registro):
#    """Converte número de registro em lista de 6 dígitos"""
#    return [int(d) for d in f"{registro:06d}"]