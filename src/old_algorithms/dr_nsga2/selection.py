"""
DR-NSGA-II Selection Module

Implements the Dual-Ranking strategy from:
Lyu et al. "Uncertainty-Aware Dual-Ranking Strategy for Offline Data-Driven
Multi-Objective Optimization" (AAAI 2026).

The dual-ranking strategy:
1. Non-dominated sort on original (predicted) fitness → rank_ori
2. Non-dominated sort on adjusted fitness (predicted + z*σ) → rank_adj
3. avg_rank = mean(rank_ori, rank_adj)
4. Build hybrid fronts from avg_rank
5. Crowding distance on original fitness for tie-breaking
"""


def dominates(fitness1, fitness2, maximize=False):
    better_in_any = False
    for f1, f2 in zip(fitness1, fitness2):
        if maximize:
            f1, f2 = -f1, -f2
        if f1 > f2:
            return False
        if f1 < f2:
            better_in_any = True
    return better_in_any


def fast_non_dominated_sort(population, config):
    fronts = [[]]

    for individual_p in population:
        individual_p.dominated_solutions = []
        individual_p.domination_count = 0

        for individual_q in population:
            if individual_p is individual_q:
                continue
            if dominates(individual_p.fitness, individual_q.fitness, config['maximize']):
                individual_p.dominated_solutions.append(individual_q)
            elif dominates(individual_q.fitness, individual_p.fitness, config['maximize']):
                individual_p.domination_count += 1

        if individual_p.domination_count == 0:
            individual_p.rank = 1
            fronts[0].append(individual_p)

    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for individual_p in fronts[i]:
            for individual_q in individual_p.dominated_solutions:
                individual_q.domination_count -= 1
                if individual_q.domination_count == 0:
                    individual_q.rank = i + 2
                    next_front.append(individual_q)
        fronts.append(next_front)
        i += 1

    if len(fronts[-1]) == 0:
        fronts.pop()

    return fronts


def calculate_crowding_distance(front):
    if len(front) == 0:
        return

    n_objectives = len(front[0].fitness)

    for individual in front:
        individual.crowding_distance = 0.0

    for obj_idx in range(n_objectives):
        front.sort(key=lambda ind: ind.fitness[obj_idx])

        front[0].crowding_distance = float('inf')
        front[-1].crowding_distance = float('inf')

        f_min = front[0].fitness[obj_idx]
        f_max = front[-1].fitness[obj_idx]

        if f_max - f_min == 0:
            continue

        for i in range(1, len(front) - 1):
            distance = (front[i + 1].fitness[obj_idx] - front[i - 1].fitness[obj_idx]) / (f_max - f_min)
            front[i].crowding_distance += distance


def dual_ranking(combined_population, config):
    """
    Dual-ranking strategy (Algorithm 2 from the DR-NSGA-II paper).

    1. NDS on original fitness → rank_ori
    2. NDS on adjusted fitness → rank_adj
    3. avg_rank = mean(rank_ori, rank_adj)
    4. Build hybrid fronts from avg_rank
    """
    # Step 1: NDS on original fitness
    fast_non_dominated_sort(combined_population, config)
    for ind in combined_population:
        ind.rank_ori = ind.rank

    # Step 2: NDS on adjusted fitness
    saved_fitness = []
    for ind in combined_population:
        saved_fitness.append(ind.fitness)
        ind.fitness = ind.adjusted_fitness

    fast_non_dominated_sort(combined_population, config)
    for ind in combined_population:
        ind.rank_adj = ind.rank

    # Restore original fitness
    for idx, ind in enumerate(combined_population):
        ind.fitness = saved_fitness[idx]

    # Step 3: avg_rank
    for ind in combined_population:
        ind.avg_rank = (ind.rank_ori + ind.rank_adj) / 2.0

    # Step 4: Build hybrid fronts from avg_rank
    sorted_pop = sorted(combined_population, key=lambda ind: ind.avg_rank)
    fronts = []
    current_rank = None
    current_front = []

    for ind in sorted_pop:
        if ind.avg_rank != current_rank:
            if current_front:
                fronts.append(current_front)
            current_front = [ind]
            current_rank = ind.avg_rank
        else:
            current_front.append(ind)
    if current_front:
        fronts.append(current_front)

    return fronts


def environmental_selection(combined_population, config):
    """
    DR-NSGA-II environmental selection using dual ranking.
    Crowding distance is computed on original (predicted) fitness values.
    """
    pop_size = config['population_size']

    fronts = dual_ranking(combined_population, config)

    for front in fronts:
        calculate_crowding_distance(front)

    next_population = []
    front_idx = 0

    while front_idx < len(fronts) and len(next_population) + len(fronts[front_idx]) <= pop_size:
        next_population.extend(fronts[front_idx])
        front_idx += 1

    if front_idx < len(fronts) and len(next_population) < pop_size:
        remaining = pop_size - len(next_population)
        fronts[front_idx].sort(key=lambda ind: ind.crowding_distance, reverse=True)
        next_population.extend(fronts[front_idx][:remaining])

    return next_population
