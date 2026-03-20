import pandas as pd
import numpy as np


def create_expanded_landscape(df_landscape):
    """
    Cria versões expandidas do landscape para garantir cobertura.
    Preserva todas as colunas incluindo fitness1_adj e fitness2_adj.
    """
    df_original = df_landscape.copy()
    df_original['x_1_landscape_original'] = df_original['x_1']
    df_original['x_2_landscape_original'] = df_original['x_2']

    df_shift_x1 = df_original.copy()
    df_shift_x1['x_1'] = df_shift_x1['x_1'] + 0.01

    df_shift_x2 = df_original.copy()
    df_shift_x2['x_2'] = df_shift_x2['x_2'] + 0.01

    df_shift_both = df_original.copy()
    df_shift_both['x_1'] = df_shift_both['x_1'] + 0.01
    df_shift_both['x_2'] = df_shift_both['x_2'] + 0.01

    df_landscape_expanded = pd.concat([df_original, df_shift_x1, df_shift_x2, df_shift_both],
                                   ignore_index=True)

    df_landscape_expanded['x_1_round'] = df_landscape_expanded['x_1'].round(2)
    df_landscape_expanded['x_2_round'] = df_landscape_expanded['x_2'].round(2)

    return df_landscape_expanded


def genotype_to_fitness(genotype, df_landscape_expanded, fitness_cols, adjusted_fitness_cols):
    """
    Mapeia genótipo para fitness e adjusted_fitness arredondando para 2 casas decimais.

    Returns:
        tuple: (fitness, adjusted_fitness, mapped_point_info, mapping_success)
    """
    x1_round = round(genotype[0], 2)
    x2_round = round(genotype[1], 2)

    matches = df_landscape_expanded[
        (df_landscape_expanded['x_1_round'] == x1_round) &
        (df_landscape_expanded['x_2_round'] == x2_round)
    ]

    if len(matches) > 0:
        row = matches.iloc[0]
        fitness = [row[fitness_cols[0]], row[fitness_cols[1]]]
        adjusted_fitness = [row[adjusted_fitness_cols[0]], row[adjusted_fitness_cols[1]]]

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

        return (fitness, adjusted_fitness, mapped_point_info, True)
    else:
        return (None, None, None, False)


def evaluate_population(population, df_landscape, fitness_cols, adjusted_fitness_cols):
    """
    Avalia fitness e adjusted_fitness de toda a população.
    """
    df_landscape_expanded = create_expanded_landscape(df_landscape)

    total = len(population)
    mapped = 0
    not_found = 0

    for individual in population:
        fitness, adjusted_fitness, mapped_point_info, mapping_success = genotype_to_fitness(
            individual.genotype, df_landscape_expanded, fitness_cols, adjusted_fitness_cols
        )

        individual.fitness = fitness
        individual.adjusted_fitness = adjusted_fitness
        individual.mapped_point = mapped_point_info
        individual.mapping_success = mapping_success

        if mapping_success:
            mapped += 1
        else:
            not_found += 1

    return {
        'total': total,
        'mapped': mapped,
        'not_found': not_found
    }
