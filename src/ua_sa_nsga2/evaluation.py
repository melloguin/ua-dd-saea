import pandas as pd
import numpy as np


# 1. Cria versões expandidas do landscape para garantir cobertura
def create_expanded_landscape(df_landscape):
    """
    Cria versões expandidas do landscape para garantir cobertura.
    Preserva todas as colunas do df_landscape original incluindo:
    x_1, x_2, f1, f2, f1_original, f2_original, f1_predicted, f2_predicted, fitness1, fitness2
    
    IMPORTANTE: Preserva x_1_original e x_2_original antes de aplicar shifts
    """

    # 1 Cria versões expandidas do landscape para garantir cobertura
    df_original = df_landscape.copy()
    # Preservar valores originais de x_1 e x_2
    df_original['x_1_landscape_original'] = df_original['x_1']
    df_original['x_2_landscape_original'] = df_original['x_2']
    
    df_shift_x1 = df_original.copy()
    # Preservar valores originais ANTES de fazer shift
    df_shift_x1['x_1'] = df_shift_x1['x_1'] + 0.01
    
    df_shift_x2 = df_original.copy()
    # Preservar valores originais ANTES de fazer shift
    df_shift_x2['x_2'] = df_shift_x2['x_2'] + 0.01
    
    df_shift_both = df_original.copy()
    # Preservar valores originais ANTES de fazer shift
    df_shift_both['x_1'] = df_shift_both['x_1'] + 0.01
    df_shift_both['x_2'] = df_shift_both['x_2'] + 0.01
    
    df_landscape_expanded = pd.concat([df_original, df_shift_x1, df_shift_x2, df_shift_both], 
                                   ignore_index=True)

    # 2. Arredonda x_1 e x_2 para 2 casas decimais (para matching)
    df_landscape_expanded['x_1_round'] = df_landscape_expanded['x_1'].round(2)
    df_landscape_expanded['x_2_round'] = df_landscape_expanded['x_2'].round(2)

    return df_landscape_expanded


# 2. Função de mapeamento
def genotype_to_fitness(genotype, df_landscape_expanded, fitness_cols):
    """
    Mapeia genótipo para fitness arredondando para 2 casas decimais.
    
    Returns:
        tuple: (fitness, mapped_point_info, mapping_success)
            - fitness: [fitness1, fitness2]
            - mapped_point_info: dict com x_1, x_2, f1, f2, f1_original, f2_original, 
                                f1_predicted, f2_predicted
            - mapping_success: bool indicando se o mapeamento teve sucesso
    """
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
        
        # Extrair informações do ponto mapeado
        # IMPORTANTE: Usar x_1_landscape_original e x_2_landscape_original 
        # (valores originais antes do shift, não os valores arredondados)
        mapped_point_info = {
            'x_1_landscape': row['x_1_landscape_original'],
            'x_2_landscape': row['x_2_landscape_original'],
            'f1': row['f1'],
            'f2': row['f2'],
            'f1_original': row['f1_original'],
            'f2_original': row['f2_original'],
            'f1_predicted': row['f1_predicted'],
            'f2_predicted': row['f2_predicted']
        }
        
        return ([fitness1, fitness2], mapped_point_info, True)
    else:
        # Caso não encontre (não deveria acontecer com as cópias, mas pode acontecer)
        return (None, None, False)


# 3. Atualiza a função de avaliação
def evaluate_population(population, df_landscape, fitness_cols):
    """
    Avalia fitness de toda a população e rastreia estatísticas de mapeamento.
    
    Returns:
        dict: Estatísticas de mapeamento com 'total', 'mapped', 'not_found'
    """
    
    df_landscape_expanded = create_expanded_landscape(df_landscape)
    
    # Contadores de mapeamento
    total = len(population)
    mapped = 0
    not_found = 0

    for individual in population:
        fitness, mapped_point_info, mapping_success = genotype_to_fitness(
            individual.genotype, df_landscape_expanded, fitness_cols
        )
        
        individual.fitness = fitness
        individual.mapped_point = mapped_point_info
        individual.mapping_success = mapping_success
        
        if mapping_success:
            mapped += 1
        else:
            not_found += 1
    
    # Retornar estatísticas de mapeamento
    return {
        'total': total,
        'mapped': mapped,
        'not_found': not_found
    }






## Mapeamento genótipo <> fenótipo
#def genotype_to_registro(genotype):
#    """Converte lista de 6 dígitos em número de registro"""
#    return int(''.join(map(str, genotype)))
#
#def registro_to_genotype(registro):
#    """Converte número de registro em lista de 6 dígitos"""
#    return [int(d) for d in f"{registro:06d}"]