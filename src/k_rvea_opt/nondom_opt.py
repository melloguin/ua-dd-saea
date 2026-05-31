"""
Non-dominated sort utilities for K-RVEA-OPT.

Provides a numba-JITed mask function that replaces the O(N^2) Python
double loop in the reference implementation. Falls back gracefully to
a pure-numpy broadcasting version if numba is unavailable, so the
algorithm still runs (slower) on machines without numba installed.
"""
from __future__ import annotations

import numpy as np

try:
    import numba

    @numba.njit(cache=True, fastmath=False, parallel=False)
    def _non_dominated_mask_jit(F):
        n = F.shape[0]
        m = F.shape[1]
        is_dom = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if is_dom[i]:
                continue
            for j in range(n):
                if i == j or is_dom[j]:
                    continue
                dom = True
                strict = False
                for k in range(m):
                    fjk = F[j, k]
                    fik = F[i, k]
                    if fjk > fik:
                        dom = False
                        break
                    if fjk < fik:
                        strict = True
                if dom and strict:
                    is_dom[i] = True
                    break
        out = np.empty(n, dtype=np.bool_)
        for i in range(n):
            out[i] = not is_dom[i]
        return out

    _HAS_NUMBA = True
except ImportError:        # pragma: no cover
    _HAS_NUMBA = False


def _non_dominated_mask_numpy(F: np.ndarray) -> np.ndarray:
    """Broadcasting fallback. Memory O(N^2) but vectorized."""
    n = F.shape[0]
    # leq[i,j,k] = F[j,k] <= F[i,k]; lt[i,j,k] = F[j,k] <  F[i,k]
    leq = F[None, :, :] <= F[:, None, :]
    lt = F[None, :, :] <  F[:, None, :]
    dominates = leq.all(axis=2) & lt.any(axis=2)  # (n, n): j dominates i
    np.fill_diagonal(dominates, False)
    any_dominator = dominates.any(axis=1)
    return ~any_dominator


def non_dominated_mask(F: np.ndarray) -> np.ndarray:
    """Return boolean mask of non-dominated rows of F.

    Uses the numba JIT version when available, else falls back to a
    broadcasting numpy implementation.
    """
    F = np.ascontiguousarray(F, dtype=np.float64)
    if _HAS_NUMBA:
        return _non_dominated_mask_jit(F)
    return _non_dominated_mask_numpy(F)


def find_non_dominated(X: np.ndarray, F: np.ndarray):
    mask = non_dominated_mask(F)
    return X[mask], F[mask]
