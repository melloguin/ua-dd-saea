"""Kriging-based population evaluation for NSGA-II variants and Prob-MOEA/D.

Replaces the KDTree/DataFrame-based landscape lookup with direct Gaussian
Process predictions, providing continuous evaluation for any genotype and
native uncertainty estimates (mean, std) per objective.

Paper references:
- NSGA-II surrogate: uses Kriging mean as fitness (Deb et al., 2002 core +
  surrogate extension).
- DR-NSGA-II: uses Kriging (mean, std) for dual ranking with adjusted fitness
  f_adj = mean + z*std  (Lyu et al., 2025, Eq. 15).
- Prob-MOEA/D: uses Kriging (mean, std) for Monte-Carlo probabilistic
  selection (Mazumdar et al., 2022, Algorithm 1).
"""
import numpy as np


def evaluate_population_kriging(population, kriging_models):
    """Evaluate population using Kriging mean predictions.

    Used by NSGA-II surrogate: fitness = Kriging mean for each objective.

    Parameters
    ----------
    population : list of Individual
    kriging_models : list of GaussianProcessRegressor (one per objective)
    """
    n_obj = len(kriging_models)
    for ind in population:
        x = np.array(ind.genotype, dtype=float).reshape(1, -1)
        fitness = []
        for j in range(n_obj):
            mean = kriging_models[j].predict(x)[0]
            fitness.append(float(mean))
        ind.fitness = fitness
        ind.mapped_point = None
        ind.mapping_success = True

    return {'total': len(population), 'mapped': len(population), 'not_found': 0}


def evaluate_population_kriging_dual(population, kriging_models, z=1.28):
    """Evaluate population with both original and uncertainty-adjusted fitness.

    Used by DR-NSGA-II: dual ranking on f_ori and f_adj.

    From the paper (Lyu et al., 2025 — Eq. 15):
        f_adj(x) = mu(x) + z * sigma(x)
    where z = Phi^{-1}(tau), e.g. z ≈ 1.28 for tau = 0.9.

    Parameters
    ----------
    population : list of Individual
    kriging_models : list of GaussianProcessRegressor
    z : float
        Confidence multiplier for uncertainty penalty (default 1.28 ≈ 90th pct).
    """
    n_obj = len(kriging_models)
    for ind in population:
        x = np.array(ind.genotype, dtype=float).reshape(1, -1)
        fitness = []
        adjusted_fitness = []
        for j in range(n_obj):
            mean, std = kriging_models[j].predict(x, return_std=True)
            fitness.append(float(mean[0]))
            adjusted_fitness.append(float(mean[0] + z * std[0]))
        ind.fitness = fitness
        ind.adjusted_fitness = adjusted_fitness
        ind.mapped_point = None
        ind.mapping_success = True

    return {'total': len(population), 'mapped': len(population), 'not_found': 0}


def get_kriging_uncertainty(genotype, kriging_models):
    """Return (mean_array, std_array) for a single genotype.

    Used by Prob-MOEA/D for Monte-Carlo sampling.

    Parameters
    ----------
    genotype : array-like
    kriging_models : list of GaussianProcessRegressor

    Returns
    -------
    means : np.ndarray (n_obj,)
    stds : np.ndarray (n_obj,)
    """
    x = np.array(genotype, dtype=float).reshape(1, -1)
    n_obj = len(kriging_models)
    means = np.zeros(n_obj)
    stds = np.zeros(n_obj)
    for j in range(n_obj):
        m, s = kriging_models[j].predict(x, return_std=True)
        means[j] = m[0]
        stds[j] = s[0]
    return means, stds
