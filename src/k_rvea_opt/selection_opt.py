"""
Vectorized RVEA selection primitives for K-RVEA-OPT.

Replaces the O(pop * n_ref) and O(n_ref^2) Python nested loops of
``src/k_rvea/selection.py`` and the K-RVEA-Online ``_select_for_reevaluation``
with matrix-cosine assignments and broadcasting.

Operations:
  - generate_reference_vectors(n_obj, n_partitions): unchanged simplex-lattice
    (reuses the reference impl since it's already cheap)
  - adapt_reference_vectors_vec(V0, F): vectorized z_min/z_max-based adaptation
  - assign_to_refs(f_bar, V): cosine-based assignment + angles, fully numpy
  - rvea_env_select_vec(F, V, k, t, tmax, alpha): RVEA APD selection
  - select_for_reeval_vec: K-RVEA Algorithm 3 — re-evaluation candidate
    selection via APD or uncertainty under diversity check
"""
from __future__ import annotations

import numpy as np
from itertools import combinations_with_replacement
from sklearn.cluster import KMeans


# ---------------------------------------------------------------------------
# Reference vectors (same simplex-lattice as the reference implementation)
# ---------------------------------------------------------------------------

def generate_reference_vectors(n_objectives: int, n_partitions: int) -> np.ndarray:
    """Simplex-lattice design, unit-normalized rows."""
    if n_objectives == 2:
        V = np.array([[i / n_partitions, 1.0 - i / n_partitions]
                      for i in range(n_partitions + 1)], dtype=float)
    else:
        pts = []
        for combo in combinations_with_replacement(range(n_partitions + 1),
                                                    n_objectives - 1):
            vals = [combo[0]]
            for j in range(1, len(combo)):
                vals.append(combo[j] - combo[j - 1])
            vals.append(n_partitions - combo[-1])
            pts.append(np.array(vals, dtype=float) / n_partitions)
        V = np.array(pts)
    norms = np.linalg.norm(V, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    return V / norms


def adapt_reference_vectors_vec(V0: np.ndarray, F: np.ndarray) -> np.ndarray:
    """Hadamard adaptation: V[i] *= (z_max - z_min), then re-normalize."""
    if len(F) == 0:
        return V0.copy()
    z_min = F.min(axis=0)
    z_max = F.max(axis=0)
    z_range = z_max - z_min
    z_range = np.where(z_range > 0, z_range, 1.0)
    Va = V0 * z_range
    norms = np.linalg.norm(Va, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    return Va / norms


# ---------------------------------------------------------------------------
# Angle computations
# ---------------------------------------------------------------------------

def _unit_rows(M: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    return M / np.where(norms > 0, norms, 1.0)


def cos_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Cosine similarity matrix between rows of A and rows of B."""
    Au = _unit_rows(A)
    Bu = _unit_rows(B)
    return np.clip(Au @ Bu.T, -1.0, 1.0)


def assign_to_refs(f_bar: np.ndarray, V: np.ndarray):
    """Vectorized angle assignment. Returns (assignment, min_angles, f_norm)."""
    cos = cos_matrix(f_bar, V)              # (n_pop, n_ref)
    angles = np.arccos(cos)
    assignment = np.argmin(angles, axis=1)
    min_angles = angles[np.arange(len(f_bar)), assignment]
    f_norm = np.linalg.norm(f_bar, axis=1)
    return assignment, min_angles, f_norm


def gamma_v_vec(V: np.ndarray) -> np.ndarray:
    """For each ref vector, smallest angle to any other vector."""
    cos = cos_matrix(V, V)
    angles = np.arccos(cos)
    np.fill_diagonal(angles, np.inf)
    return np.maximum(angles.min(axis=1), 1e-10)


# ---------------------------------------------------------------------------
# RVEA environmental selection (vectorized APD)
# ---------------------------------------------------------------------------

def rvea_env_select_vec(F: np.ndarray, V: np.ndarray, *,
                        k: int, t: int, tmax: int,
                        alpha_rate: float = 2.0) -> np.ndarray:
    """RVEA environmental selection. Returns indices into F of survivors."""
    if len(F) == 0:
        return np.array([], dtype=int)
    f_ideal = F.min(axis=0)
    f_bar = F - f_ideal
    assignment, min_angles, f_norm = assign_to_refs(f_bar, V)
    gamma_v = gamma_v_vec(V)

    # APD per individual
    P = k * (t / max(tmax, 1)) ** alpha_rate * (min_angles / gamma_v[assignment])
    apd = (1.0 + P) * f_norm

    # For each active reference vector, pick the individual with min APD.
    # We use a scatter-min via lexsort over (assignment, apd).
    n_pop = len(F)
    order = np.lexsort((apd, assignment))   # sort by ref first, apd second
    sorted_assign = assignment[order]
    # First occurrence of each ref-group in the sorted array is the min-APD pick.
    is_first = np.empty(n_pop, dtype=bool)
    is_first[0] = True
    is_first[1:] = sorted_assign[1:] != sorted_assign[:-1]
    selected = order[is_first]
    return selected


# ---------------------------------------------------------------------------
# K-RVEA Algorithm 3: re-evaluation candidate selection
# ---------------------------------------------------------------------------

def select_for_reeval_vec(X_pop: np.ndarray, F_pop: np.ndarray,
                          Sigma_pop: np.ndarray, V0: np.ndarray,
                          Vf: np.ndarray, *, n_select: int,
                          prev_n_inactive_fixed: int,
                          k_obj: int, delta_threshold: int | None = None,
                          rng: np.random.Generator | None = None):
    """Vectorized version of K-RVEA Algorithm 3.

    Returns (selected_indices, n_inactive_fixed) where selected_indices is
    a numpy array of indices into the pop arrays.
    """
    if len(F_pop) == 0:
        return np.array([], dtype=int), 0

    if rng is None:
        rng = np.random.default_rng(0)

    n_ref_f = len(Vf)
    if delta_threshold is None:
        delta_threshold = max(1, int(0.05 * n_ref_f))

    f_ideal = F_pop.min(axis=0)
    f_bar = F_pop - f_ideal

    # Assign to fixed reference vectors (to count inactive)
    assign_fixed, _, _ = assign_to_refs(f_bar, Vf)
    n_active_fixed = len(np.unique(assign_fixed))
    n_inactive_fixed = n_ref_f - n_active_fixed
    delta_vf = n_inactive_fixed - prev_n_inactive_fixed
    use_uncertainty = delta_vf > delta_threshold

    # Adaptive reference vectors based on current F_pop
    Va = adapt_reference_vectors_vec(V0, F_pop)
    assign_adapt, min_angles, f_norm = assign_to_refs(f_bar, Va)

    active_refs = np.unique(assign_adapt)
    n_active = len(active_refs)
    n_clusters = min(n_select, n_active)
    if n_clusters == 0:
        return np.array([], dtype=int), n_inactive_fixed

    # Cluster the *active adaptive* reference vectors
    if n_clusters >= n_active:
        cluster_assignment = {i: [int(r)] for i, r in enumerate(active_refs)}
    else:
        active_vecs = Va[active_refs]
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=3)
        labels = km.fit_predict(active_vecs)
        cluster_assignment = {}
        for ai, ref in enumerate(active_refs):
            cluster_assignment.setdefault(int(labels[ai]), []).append(int(ref))

    # Pre-compute candidates per ref for fast lookup
    candidates_per_ref = {}
    for ind_idx, ref in enumerate(assign_adapt):
        candidates_per_ref.setdefault(int(ref), []).append(ind_idx)

    gamma_v = gamma_v_vec(Va)
    t_ratio = 1.0   # full penalty for selection here (matches reference)

    # Pre-compute average uncertainty per individual once
    avg_sigma = Sigma_pop.mean(axis=1)

    selected = []
    for _, ref_list in cluster_assignment.items():
        cand_idx = []
        for r in ref_list:
            cand_idx.extend(candidates_per_ref.get(r, []))
        if not cand_idx:
            continue
        cand_idx = np.array(cand_idx, dtype=int)

        if use_uncertainty:
            pick = cand_idx[np.argmax(avg_sigma[cand_idx])]
        else:
            # APD over the candidate set
            P = k_obj * t_ratio * (min_angles[cand_idx]
                                    / gamma_v[assign_adapt[cand_idx]])
            apd_c = (1.0 + P) * f_norm[cand_idx]
            pick = cand_idx[np.argmin(apd_c)]
        if pick not in selected:
            selected.append(int(pick))

    return np.array(selected[:n_select], dtype=int), n_inactive_fixed


# ---------------------------------------------------------------------------
# Archive management (K-RVEA Algorithm 4) — vectorized clustering
# ---------------------------------------------------------------------------

def manage_archive_vec(X_archive: np.ndarray, Y_archive: np.ndarray,
                       X_new: np.ndarray, Y_new: np.ndarray, NI: int,
                       rng: np.random.Generator):
    """Keep at most NI samples; prefer the new ones, cluster older for diversity."""
    X_all = np.vstack([X_archive, X_new])
    Y_all = np.vstack([Y_archive, Y_new])

    # Deduplicate
    _, unique_idx = np.unique(X_all, axis=0, return_index=True)
    unique_idx = np.sort(unique_idx)
    X_all = X_all[unique_idx]
    Y_all = Y_all[unique_idx]

    if len(X_all) <= NI:
        return X_all, Y_all

    n_new = len(X_new)
    n_keep_old = NI - min(n_new, NI)
    if n_keep_old <= 0:
        return X_new[:NI], Y_new[:NI]

    X_old = X_archive
    Y_old = Y_archive
    if len(X_old) <= n_keep_old:
        return np.vstack([X_old, X_new]), np.vstack([Y_old, Y_new])

    # KMeans cluster old samples; pick one per cluster
    n_clusters = min(n_keep_old, len(X_old))
    if n_clusters <= 1:
        return np.vstack([X_old[:n_keep_old], X_new]), np.vstack([Y_old[:n_keep_old], Y_new])

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    labels = km.fit_predict(X_old)
    selected_old_X = []
    selected_old_Y = []
    for c in range(n_clusters):
        idxs = np.where(labels == c)[0]
        if len(idxs) > 0:
            pick = int(rng.choice(idxs))
            selected_old_X.append(X_old[pick])
            selected_old_Y.append(Y_old[pick])
    selected_old_X = np.array(selected_old_X)
    selected_old_Y = np.array(selected_old_Y)

    X_result = np.vstack([selected_old_X, X_new])
    Y_result = np.vstack([selected_old_Y, Y_new])
    return X_result[:NI], Y_result[:NI]
