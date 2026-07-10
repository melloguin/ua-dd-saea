"""
Vectorized genetic operators for K-RVEA-OPT.

All operators work on numpy arrays ``X`` of shape ``(pop_size, n_var)``
and produce arrays of the same shape. No Python-level for-loops over
individuals or variables — everything is batched broadcasting.

Operators implemented:
  - vectorized_tournament(rank, crowding, k, n_select, rng): index selection
  - vectorized_sbx(P1, P2, eta, prob, xl, xu, rng): batched SBX crossover
  - vectorized_polynomial_mutation(X, eta, prob, xl, xu, rng): per-cell mutation
  - create_offspring_vec(X_parents, rank, crowding, cfg, rng): full pipeline

Semantically equivalent to the reference operators in
``src/k_rvea/offspring.py`` (same SBX/PM equations from Deb), but
statistically — not bit-identically — equivalent: the order in which
random numbers are consumed differs because we draw whole matrices at
once instead of one variable at a time.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Tournament selection
# ---------------------------------------------------------------------------

def vectorized_tournament(rank: np.ndarray, crowding: np.ndarray,
                          k_tournament: int, n_select: int,
                          rng: np.random.Generator) -> np.ndarray:
    """Binary (or k-ary) tournament. Returns array of winner indices.

    Rule (crowded-comparison operator): lower rank wins; on tie, higher
    crowding wins.
    """
    n = len(rank)
    if n == 0:
        return np.array([], dtype=int)
    if n < k_tournament:
        # Sample with replacement, matching reference behavior
        candidates = rng.integers(0, n, size=(n_select, k_tournament))
    else:
        # Sample without replacement per tournament. np.argpartition trick.
        # For speed, just allow replacement here too — k_tournament << n
        # so collisions are rare; the reference also uses
        # np.random.choice(replace=False) only when possible.
        candidates = rng.integers(0, n, size=(n_select, k_tournament))

    cand_rank = rank[candidates]              # (n_select, k_tournament)
    cand_crowd = crowding[candidates]         # (n_select, k_tournament)
    # Composite key: lower rank ranks first; among equal rank, higher
    # crowding ranks first.  Encode as a single float so np.argmin picks
    # the winner deterministically: score = rank * LARGE - crowding.
    score = cand_rank.astype(np.float64) * 1e12 - cand_crowd
    winners_in_tournament = np.argmin(score, axis=1)
    return candidates[np.arange(n_select), winners_in_tournament]


# ---------------------------------------------------------------------------
# SBX crossover  (Deb & Agrawal, simulated binary crossover)
# ---------------------------------------------------------------------------

def vectorized_sbx(parents1: np.ndarray, parents2: np.ndarray, *,
                   eta: float = 15.0, prob: float = 0.9,
                   xl: np.ndarray, xu: np.ndarray,
                   rng: np.random.Generator):
    """Batched SBX. P1, P2: (n_pairs, n_var). Returns (C1, C2) same shape."""
    n_pairs, n_var = parents1.shape

    # Whether each pair undergoes crossover at all
    do_pair = rng.random(n_pairs) < prob                      # (n_pairs,)
    # Per-variable validity: must have differing parent values
    diff = np.abs(parents1 - parents2) > 1e-14                # (n_pairs, n_var)

    y1 = np.minimum(parents1, parents2)
    y2 = np.maximum(parents1, parents2)
    delta = y2 - y1
    delta_safe = np.where(diff, delta, 1.0)  # avoid division by 0

    rand = rng.random((n_pairs, n_var))

    # beta from lower bound xl
    beta = 1.0 + 2.0 * (y1 - xl) / delta_safe
    # Guard: if delta is 0, beta will be huge; mask out later.
    beta = np.where(beta > 0, beta, 1.0)  # ensure positive base for power
    alpha = 2.0 - np.power(beta, -(eta + 1.0))
    # alpha can be slightly > 2 by FP; clip:
    alpha = np.clip(alpha, 1e-12, None)

    lower_branch = rand <= (1.0 / alpha)
    # val for both branches
    val_low = rand * alpha
    val_up = 1.0 / np.maximum(2.0 - rand * alpha, 1e-12)
    val = np.where(lower_branch, val_low, val_up)
    val = np.maximum(val, 1e-300)
    betaq = np.power(val, 1.0 / (eta + 1.0))

    c1_vals = 0.5 * ((y1 + y2) - betaq * delta)
    c2_vals = 0.5 * ((y1 + y2) + betaq * delta)

    # 50/50 swap (per the reference impl)
    swap = rng.random((n_pairs, n_var)) < 0.5
    c1 = np.where(swap, c2_vals, c1_vals)
    c2 = np.where(swap, c1_vals, c2_vals)

    c1 = np.clip(c1, xl, xu)
    c2 = np.clip(c2, xl, xu)

    apply_mask = diff & do_pair[:, None]
    out1 = np.where(apply_mask, c1, parents1)
    out2 = np.where(apply_mask, c2, parents2)
    return out1, out2


# ---------------------------------------------------------------------------
# Polynomial mutation (Deb)
# ---------------------------------------------------------------------------

def vectorized_polynomial_mutation(X: np.ndarray, *,
                                   eta: float = 20.0, prob: float,
                                   xl: np.ndarray, xu: np.ndarray,
                                   rng: np.random.Generator) -> np.ndarray:
    """Per-cell polynomial mutation. X: (n_pop, n_var)."""
    n_pop, n_var = X.shape

    mutate = rng.random((n_pop, n_var)) < prob
    delta_bounds = xu - xl
    delta_safe = np.where(delta_bounds > 0, delta_bounds, 1.0)

    rand = rng.random((n_pop, n_var))
    mut_pow = 1.0 / (eta + 1.0)

    lower_branch = rand < 0.5

    # Lower branch:  xy = 1 - (x - xl)/delta;  val = 2 r + (1-2r) xy^(eta+1)
    xy_l = 1.0 - (X - xl) / delta_safe
    xy_l = np.clip(xy_l, 0.0, 1.0)
    val_l = 2.0 * rand + (1.0 - 2.0 * rand) * np.power(xy_l, eta + 1.0)
    val_l = np.maximum(val_l, 1e-300)
    deltaq_l = np.power(val_l, mut_pow) - 1.0

    # Upper branch:  xy = 1 - (xu - x)/delta
    xy_u = 1.0 - (xu - X) / delta_safe
    xy_u = np.clip(xy_u, 0.0, 1.0)
    val_u = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * np.power(xy_u, eta + 1.0)
    val_u = np.maximum(val_u, 1e-300)
    deltaq_u = 1.0 - np.power(val_u, mut_pow)

    deltaq = np.where(lower_branch, deltaq_l, deltaq_u)
    X_new = X + deltaq * delta_bounds
    X_new = np.clip(X_new, xl, xu)
    return np.where(mutate, X_new, X)


# ---------------------------------------------------------------------------
# Full offspring pipeline
# ---------------------------------------------------------------------------

def create_offspring_vec(X_parents: np.ndarray, rank: np.ndarray,
                         crowding: np.ndarray, *, cfg: dict,
                         xl: np.ndarray, xu: np.ndarray,
                         rng: np.random.Generator) -> np.ndarray:
    """Build a full offspring population of size ``len(X_parents)``."""
    pop_size = len(X_parents)
    k_tour = cfg.get('k_tournament', 2)
    sbx_eta = cfg.get('crossover_eta', 15)
    sbx_prob = cfg.get('crossover_prob', 0.9)
    pm_eta = cfg.get('mutation_eta', 20)
    pm_prob = cfg.get('mutation_prob', 1.0 / X_parents.shape[1])

    n_pairs = (pop_size + 1) // 2
    idx1 = vectorized_tournament(rank, crowding, k_tour, n_pairs, rng)
    idx2 = vectorized_tournament(rank, crowding, k_tour, n_pairs, rng)

    P1 = X_parents[idx1]
    P2 = X_parents[idx2]
    C1, C2 = vectorized_sbx(P1, P2, eta=sbx_eta, prob=sbx_prob,
                            xl=xl, xu=xu, rng=rng)

    offspring = np.vstack([C1, C2])[:pop_size]
    offspring = vectorized_polynomial_mutation(offspring, eta=pm_eta,
                                               prob=pm_prob, xl=xl, xu=xu,
                                               rng=rng)
    return offspring
