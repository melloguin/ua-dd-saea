"""
K-RVEA Selection Module (Offline RVEA)

Implements the Reference Vector Guided Evolutionary Algorithm (RVEA)
selection mechanism from:
Chugh et al. "A Surrogate-assisted Reference Vector Guided Evolutionary
Algorithm for Computationally Expensive Many-objective Optimization"
(IEEE TEVC 2016).

In the offline setting (no re-evaluation possible), K-RVEA reduces to
RVEA using surrogate fitness. The Kriging model management component
(re-evaluation and model update) does not apply.

Key components:
1. Reference vector generation (simplex-lattice design)
2. Assignment of individuals to reference vectors (minimum angle)
3. Selection via Angle Penalized Distance (APD)
4. Reference vector adaptation
"""

import numpy as np
from itertools import combinations_with_replacement


def generate_reference_vectors(n_objectives, n_partitions):
    """
    Generate uniformly distributed reference vectors using simplex-lattice design.

    For biobjective problems (n_objectives=2), generates n_partitions+1 vectors.
    """
    if n_objectives == 2:
        points = []
        for i in range(n_partitions + 1):
            p = np.array([i / n_partitions, 1 - i / n_partitions])
            points.append(p)
        V = np.array(points)
    else:
        # General simplex-lattice design for k objectives with H partitions
        points = []
        for combo in combinations_with_replacement(range(n_partitions + 1), n_objectives - 1):
            vals = [combo[0]]
            for j in range(1, len(combo)):
                vals.append(combo[j] - combo[j-1])
            vals.append(n_partitions - combo[-1])
            p = np.array(vals) / n_partitions
            points.append(p)
        V = np.array(points)

    norms = np.linalg.norm(V, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    V = V / norms

    return V


def compute_angle(v1, v2):
    """Compute the acute angle (in radians) between two vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return np.pi / 2
    cos_angle = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return np.arccos(cos_angle)


def adapt_reference_vectors(V0, population):
    """
    Adapt reference vectors based on the current population's objective ranges.

    V_adapted[i] = V0[i] ⊙ (z_max - z_min) / ||V0[i] ⊙ (z_max - z_min)||

    where ⊙ is element-wise multiplication (Hadamard product).
    """
    fitness_matrix = np.array([ind.fitness for ind in population if ind.fitness is not None])
    if len(fitness_matrix) == 0:
        return V0.copy()

    z_min = fitness_matrix.min(axis=0)
    z_max = fitness_matrix.max(axis=0)
    z_range = z_max - z_min

    # Avoid zero range
    z_range[z_range == 0] = 1.0

    V_adapted = V0 * z_range
    norms = np.linalg.norm(V_adapted, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    V_adapted = V_adapted / norms

    return V_adapted


def rvea_environmental_selection(combined_population, config, reference_vectors_adapted, generation):
    """
    RVEA environmental selection using Angle Penalized Distance (APD).

    From each subpopulation (individuals assigned to the same reference vector),
    selects the individual with minimum APD.

    APD_j = (1 + P(θ_j)) * ||f̄_j||

    where:
    - f̄_j = translated objective vector (f - f_ideal)
    - ||f̄_j|| = distance from f̄_j to origin (convergence)
    - θ_j = angle between f̄_j and its assigned reference vector (diversity)
    - P(θ) = k * (t/tmax)^α * θ/γv (penalty function)
    - γv = minimum angle between adjacent reference vectors
    - α = rate parameter (default 2.0)
    """
    valid_pop = [ind for ind in combined_population if ind.fitness is not None]
    if len(valid_pop) == 0:
        return []

    k = config['n_objetivos']
    t = generation + 1
    tmax = config['n_generations']
    alpha_rate = config.get('rvea_alpha', 2.0)

    fitness_matrix = np.array([ind.fitness for ind in valid_pop])

    # Translate objectives: f̄ = f - f_ideal
    f_ideal = fitness_matrix.min(axis=0)
    f_bar = fitness_matrix - f_ideal

    n_pop = len(valid_pop)
    n_ref = len(reference_vectors_adapted)

    # Compute γv for each reference vector: smallest angle to any neighbor
    gamma_v = np.full(n_ref, np.inf)
    for i in range(n_ref):
        for j in range(n_ref):
            if i != j:
                angle_ij = compute_angle(reference_vectors_adapted[i], reference_vectors_adapted[j])
                if angle_ij < gamma_v[i]:
                    gamma_v[i] = angle_ij

    # Assign individuals to reference vectors and compute APD
    # For each individual: find closest reference vector
    assignments = {}
    for idx in range(n_pop):
        min_angle = float('inf')
        best_ref = 0
        for j in range(n_ref):
            angle = compute_angle(f_bar[idx], reference_vectors_adapted[j])
            if angle < min_angle:
                min_angle = angle
                best_ref = j

        if best_ref not in assignments:
            assignments[best_ref] = []
        assignments[best_ref].append((idx, min_angle))

    # Select one individual from each subpopulation using minimum APD
    selected = []
    for ref_idx, ind_entries in assignments.items():
        best_idx = None
        best_apd = float('inf')

        gv = gamma_v[ref_idx] if gamma_v[ref_idx] > 0 else 1e-10

        for (pop_idx, theta) in ind_entries:
            dist = np.linalg.norm(f_bar[pop_idx])
            P = k * (t / tmax) ** alpha_rate * theta / gv
            apd = (1 + P) * dist

            if apd < best_apd:
                best_apd = apd
                best_idx = pop_idx

        if best_idx is not None:
            valid_pop[best_idx].rank = 1
            selected.append(valid_pop[best_idx])

    # Mark non-selected as higher rank
    selected_set = set(id(ind) for ind in selected)
    for ind in valid_pop:
        if id(ind) not in selected_set:
            ind.rank = 2

    return selected


def environmental_selection(combined_population, config, V0, generation):
    """
    Full RVEA environmental selection:
    1. Adapt reference vectors
    2. Select via APD
    """
    Va = adapt_reference_vectors(V0, combined_population)
    selected = rvea_environmental_selection(combined_population, config, Va, generation)
    return selected
