import numpy as np
import copy
from src.dr_nsga2.individual import Individual


def crowded_comparison_operator(ind1, ind2):
    """
    Operador de comparação para DR-NSGA-II.
    Usa avg_rank (dual ranking) e crowding_distance.
    """
    r1 = ind1.avg_rank if ind1.avg_rank is not None else (ind1.rank or float('inf'))
    r2 = ind2.avg_rank if ind2.avg_rank is not None else (ind2.rank or float('inf'))
    if r1 != r2:
        return r1 < r2
    return ind1.crowding_distance > ind2.crowding_distance


def tournament_selection(population, k_tournament):
    use_replace = len(population) < k_tournament
    tournament_indices = np.random.choice(len(population), size=k_tournament, replace=use_replace)
    tournament_individuals = [population[i] for i in tournament_indices]

    best = tournament_individuals[0]
    for individual in tournament_individuals[1:]:
        if crowded_comparison_operator(individual, best):
            best = individual

    return copy.deepcopy(best)


def simulated_binary_crossover(parent1, parent2, eta=15, prob=0.9, xl=None, xu=None):
    p1 = np.array(parent1.genotype, dtype=float)
    p2 = np.array(parent2.genotype, dtype=float)
    n_var = len(p1)

    if xl is None:
        xl = np.zeros(n_var)
    else:
        xl = np.array(xl, dtype=float)
    if xu is None:
        xu = np.ones(n_var)
    else:
        xu = np.array(xu, dtype=float)

    c1 = p1.copy()
    c2 = p2.copy()

    if np.random.random() > prob:
        return c1.tolist(), c2.tolist()

    mask = np.abs(p1 - p2) > 1e-14
    if not np.any(mask):
        return c1.tolist(), c2.tolist()

    y1 = np.minimum(p1[mask], p2[mask])
    y2 = np.maximum(p1[mask], p2[mask])
    delta = y2 - y1
    rand = np.random.random(len(delta))

    beta = np.zeros(len(delta))
    alpha = np.zeros(len(delta))
    betaq = np.zeros(len(delta))

    xl_masked = xl[mask]
    xu_masked = xu[mask]

    beta = 1.0 + (2.0 * (y1 - xl_masked) / delta)
    alpha = 2.0 - np.power(beta, -(eta + 1.0))

    mask_lower = rand <= (1.0 / alpha)
    mask_upper = ~mask_lower

    if np.any(mask_lower):
        val = rand[mask_lower] * alpha[mask_lower]
        betaq[mask_lower] = np.power(val, 1.0 / (eta + 1.0))

    if np.any(mask_upper):
        val = 1.0 / (2.0 - rand[mask_upper] * alpha[mask_upper])
        betaq[mask_upper] = np.power(val, 1.0 / (eta + 1.0))

    c1_vals = 0.5 * ((y1 + y2) - betaq * delta)
    c2_vals = 0.5 * ((y1 + y2) + betaq * delta)

    swap = np.random.random(len(delta)) < 0.5
    final_c1 = np.where(swap, c2_vals, c1_vals)
    final_c2 = np.where(swap, c1_vals, c2_vals)

    final_c1 = np.clip(final_c1, xl_masked, xu_masked)
    final_c2 = np.clip(final_c2, xl_masked, xu_masked)

    c1[mask] = final_c1
    c2[mask] = final_c2

    return c1.tolist(), c2.tolist()


def polynomial_mutation(individual, eta=20, prob=1/6, xl=None, xu=None):
    mutated = list(individual.genotype) if not isinstance(individual.genotype, list) else individual.genotype.copy()
    n_var = len(mutated)

    if xl is None:
        xl = np.zeros(n_var)
    else:
        xl = np.array(xl, dtype=float)
    if xu is None:
        xu = np.ones(n_var)
    else:
        xu = np.array(xu, dtype=float)

    for i in range(len(mutated)):
        if np.random.random() <= prob:
            x = float(mutated[i])
            xl_i = float(xl[i])
            xu_i = float(xu[i])

            delta = xu_i - xl_i
            rand = np.random.random()
            mut_pow = 1.0 / (eta + 1.0)

            if rand < 0.5:
                xy = 1.0 - (x - xl_i) / delta
                val = 2.0 * rand + (1.0 - 2.0 * rand) * np.power(xy, eta + 1.0)
                deltaq = np.power(val, mut_pow) - 1.0
            else:
                xy = 1.0 - (xu_i - x) / delta
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * np.power(xy, eta + 1.0)
                deltaq = 1.0 - np.power(val, mut_pow)

            x_new = x + deltaq * delta
            x_new = np.clip(x_new, xl_i, xu_i)
            mutated[i] = x_new

    return mutated


def create_offspring_population(population, config):
    offspring = []
    n_offspring_needed = len(population)

    for _ in range(0, n_offspring_needed, 2):
        parent1 = tournament_selection(population, config['k_tournament'])
        parent2 = tournament_selection(population, config['k_tournament'])

        child1_genotype, child2_genotype = simulated_binary_crossover(
            parent1, parent2,
            eta=config['crossover_eta'],
            prob=config['crossover_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )

        child1_genotype = polynomial_mutation(
            Individual(child1_genotype),
            eta=config['mutation_eta'],
            prob=config['mutation_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )
        child2_genotype = polynomial_mutation(
            Individual(child2_genotype),
            eta=config['mutation_eta'],
            prob=config['mutation_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )

        offspring.append(Individual(list(child1_genotype) if not isinstance(child1_genotype, list) else child1_genotype))
        if len(offspring) < n_offspring_needed:
            offspring.append(Individual(list(child2_genotype) if not isinstance(child2_genotype, list) else child2_genotype))

    return offspring
