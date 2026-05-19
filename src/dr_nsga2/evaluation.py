import pandas as pd
import numpy as np
import re
from scipy.spatial import cKDTree


def _detect_x_cols(df):
    cols = [c for c in df.columns if re.match(r'^x_\d+$', c)]
    return sorted(cols, key=lambda c: int(c.split('_')[1]))


def prepare_landscape(df_landscape, x_cols=None):
    if x_cols is None:
        x_cols = _detect_x_cols(df_landscape)
    X = df_landscape[x_cols].values.astype(float)
    tree = cKDTree(X)
    return tree, x_cols


def genotype_to_fitness(genotype, df_landscape, tree, x_cols,
                        fitness_cols, adjusted_fitness_cols=None):
    """Map genotype via nearest-neighbour; optionally read adjusted fitness."""
    query = np.array([genotype[i] for i in range(len(x_cols))], dtype=float)
    _, idx = tree.query(query)
    row = df_landscape.iloc[idx]

    fitness = [row[fc] for fc in fitness_cols]
    adjusted_fitness = ([row[afc] for afc in adjusted_fitness_cols]
                        if adjusted_fitness_cols else None)

    mapped_point = {}
    for xc in x_cols:
        mapped_point[f'{xc}_landscape'] = row[xc]
    for col in row.index:
        if re.match(r'^f\d+$', col):
            mapped_point[col] = row[col]
        elif re.match(r'^f\d+_(original|predicted)$', col):
            mapped_point[col] = row[col]

    return fitness, adjusted_fitness, mapped_point, True


def evaluate_population(population, df_landscape, fitness_cols,
                        adjusted_fitness_cols=None, x_cols=None):
    tree, x_cols = prepare_landscape(df_landscape, x_cols)

    total = len(population)
    mapped = 0

    for ind in population:
        fitness, adjusted_fitness, mapped_point, success = genotype_to_fitness(
            ind.genotype, df_landscape, tree, x_cols,
            fitness_cols, adjusted_fitness_cols)
        ind.fitness = fitness
        ind.adjusted_fitness = adjusted_fitness
        ind.mapped_point = mapped_point
        ind.mapping_success = success
        if success:
            mapped += 1

    return {'total': total, 'mapped': mapped, 'not_found': total - mapped}
