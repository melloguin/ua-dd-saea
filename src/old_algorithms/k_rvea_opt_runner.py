"""
K-RVEA-OPT: vectorized + parallel implementation of K-RVEA.

This is a fresh runner that re-implements the same algorithm as
``src/k_rvea_runner.py::run_k_rvea`` but optimized for speed:

  Phase 1 — Angle computations vectorized via cosine matrices
            (selection_opt.py).
  Phase 2 — Offspring generation vectorized; full population processed
            with broadcasting (offspring_opt.py).
  Phase 3 — M Gaussian Processes fit AND predict in parallel via
            joblib threading (gp_opt.py).
  Phase 4 — Custom FastGP class avoids sklearn's per-call overhead and
            caches the Cholesky factor (gp_opt.py).
  Phase 5 — Non-dominated mask JIT-compiled with numba (nondom_opt.py).

The algorithm's logic (LHS init, RVEA inner loop, K-RVEA Algorithms 2-4)
is preserved.  Results are statistically equivalent — not bit-identical —
to ``run_k_rvea`` because the order in which random numbers are consumed
differs (vectorized offspring draws whole matrices).

Public signature mirrors ``run_k_rvea`` so it slots into the existing
dispatch in ``src/experiment.py``:

    df_pareto, info, history = run_k_rvea_opt(problem, config,
                                              save_history=False)
"""
from __future__ import annotations

import os
# Best-effort BLAS thread setup: only when the user hasn't pinned it.
# Must be set *before* numpy is imported, but since experiment.py imports
# numpy first, the effect here is limited — this is safe though.
os.environ.setdefault('OMP_NUM_THREADS', str(max(1, (os.cpu_count() or 1))))
os.environ.setdefault('MKL_NUM_THREADS', str(max(1, (os.cpu_count() or 1))))
os.environ.setdefault('OPENBLAS_NUM_THREADS', str(max(1, (os.cpu_count() or 1))))

import warnings
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from src.problems import evaluate_problem
from src.k_rvea_opt.gp_opt import fit_gps_parallel, predict_gps_parallel
from src.k_rvea_opt.offspring_opt import create_offspring_vec
from src.k_rvea_opt.selection_opt import (
    generate_reference_vectors,
    adapt_reference_vectors_vec,
    rvea_env_select_vec,
    select_for_reeval_vec,
    manage_archive_vec,
)
from src.k_rvea_opt.nondom_opt import find_non_dominated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _latin_hypercube_sampling(n_samples: int, n_var: int,
                              xl: np.ndarray, xu: np.ndarray,
                              seed: int = 42) -> np.ndarray:
    """Latin Hypercube Sampling in [xl, xu], identical to the reference impl."""
    rng = np.random.RandomState(seed)
    result = np.zeros((n_samples, n_var))
    for j in range(n_var):
        cut = np.linspace(0, 1, n_samples + 1)
        u = rng.uniform(size=n_samples)
        points = cut[:n_samples] + u * (cut[1:] - cut[:n_samples])
        rng.shuffle(points)
        result[:, j] = xl[j] + points * (xu[j] - xl[j])
    return result


def _snapshot(X_A2: np.ndarray, Y_A2: np.ndarray, generation: int) -> dict:
    """Build a history snapshot in the schema expected by experiment.py."""
    return {
        'generation': int(generation),
        'population': [
            {'genotype': list(X_A2[i]), 'fitness': list(Y_A2[i])}
            for i in range(len(X_A2))
        ],
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_k_rvea_opt(problem, config: dict, save_history: bool = False):
    """K-RVEA Online (vectorized + parallel).

    Same Args/Returns as ``run_k_rvea``.  See module docstring for the list
    of optimization phases applied.
    """
    seed = int(config['seed'])
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    n_var = problem.n_var
    n_obj = problem.n_obj
    xl = np.asarray(problem.xl, dtype=float)
    xu = np.asarray(problem.xu, dtype=float)

    FEmax = int(config.get('FEmax', 300))
    wmax = int(config.get('krvea_wmax', 20))
    u = int(config.get('krvea_u', 5))
    NI = int(config.get('krvea_NI', 11 * n_var - 1))
    pop_target = int(config.get('population_size', 100))
    alpha_rate = float(config.get('rvea_alpha', 2.0))
    n_generations = int(config.get('n_generations', 100))
    n_jobs_gp = int(config.get('krvea_opt_gp_jobs',
                                min(n_obj, max(1, os.cpu_count() or 1))))

    # Reference vectors
    V0 = generate_reference_vectors(n_obj, pop_target - 1)
    Vf = V0.copy()
    pop_size = len(V0)

    # ------------------------ Phase 1: LHS init ----------------------------
    X_init = _latin_hypercube_sampling(NI, n_var, xl, xu, seed=seed)
    F_init = evaluate_problem(problem, X_init)
    FE = NI

    X_A1 = X_init.copy()   # training archive
    Y_A1 = F_init.copy()
    X_A2 = X_init.copy()   # all truly-evaluated
    Y_A2 = F_init.copy()

    # Train initial GPs
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        gps = fit_gps_parallel(X_A1, Y_A1, n_jobs=n_jobs_gp,
                                alpha=1e-6, n_restarts=2, base_seed=seed)

    # Initial population: random uniform; evaluated on surrogate
    X_pop = rng.uniform(xl, xu, size=(pop_size, n_var))
    F_pop, Sigma_pop = predict_gps_parallel(gps, X_pop, n_jobs=n_jobs_gp)
    rank_pop = np.ones(pop_size, dtype=int)
    crowding_pop = np.zeros(pop_size)

    history = [] if save_history else None
    if save_history:
        history.append(_snapshot(X_A2, Y_A2, 0))

    prev_n_inactive_fixed = 0
    tu = 0
    gen_global = 0
    progress_log = []

    pbar = tqdm(total=FEmax, initial=FE, desc='K-RVEA-OPT (FE)')

    # ------------------------ Phase 2+: main loop --------------------------
    while FE < FEmax:
        # Inner RVEA loop on surrogates
        for _ in range(wmax):
            gen_global += 1

            X_off = create_offspring_vec(
                X_pop, rank_pop, crowding_pop,
                cfg=config, xl=xl, xu=xu, rng=rng
            )
            F_off, Sigma_off = predict_gps_parallel(gps, X_off,
                                                    n_jobs=n_jobs_gp)

            X_comb = np.vstack([X_pop, X_off])
            F_comb = np.vstack([F_pop, F_off])
            Sigma_comb = np.vstack([Sigma_pop, Sigma_off])

            Va = adapt_reference_vectors_vec(V0, F_comb)
            sel_idx = rvea_env_select_vec(F_comb, Va, k=n_obj,
                                           t=gen_global, tmax=n_generations,
                                           alpha_rate=alpha_rate)
            if len(sel_idx) == 0:
                # Defensive fallback (matches reference behavior)
                sel_idx = np.arange(min(pop_size, len(X_comb)))

            X_pop = X_comb[sel_idx]
            F_pop = F_comb[sel_idx]
            Sigma_pop = Sigma_comb[sel_idx]
            rank_pop = np.ones(len(X_pop), dtype=int)
            crowding_pop = np.zeros(len(X_pop))

        # Algorithm 3: re-evaluation candidate selection
        selected_idx, prev_n_inactive_fixed = select_for_reeval_vec(
            X_pop, F_pop, Sigma_pop, V0, Vf,
            n_select=u, prev_n_inactive_fixed=prev_n_inactive_fixed,
            k_obj=n_obj, rng=rng,
        )

        if len(selected_idx) == 0:
            n_pick = min(u, len(X_pop))
            selected_idx = rng.choice(len(X_pop), n_pick, replace=False)

        X_reeval = X_pop[selected_idx]
        n_reeval = min(len(X_reeval), FEmax - FE)
        X_reeval = X_reeval[:n_reeval]
        if len(X_reeval) == 0:
            break

        F_reeval = evaluate_problem(problem, X_reeval)
        FE += len(X_reeval)
        pbar.update(len(X_reeval))

        # Append to archives
        X_A2 = np.vstack([X_A2, X_reeval])
        Y_A2 = np.vstack([Y_A2, F_reeval])

        # Algorithm 4: manage A1
        X_A1, Y_A1 = manage_archive_vec(X_A1, Y_A1, X_reeval, F_reeval,
                                          NI, rng)

        # Re-train Kriging models in parallel
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            gps = fit_gps_parallel(X_A1, Y_A1, n_jobs=n_jobs_gp,
                                    alpha=1e-6, n_restarts=2,
                                    base_seed=seed + tu)

        tu += 1
        progress_log.append({
            'update': tu,
            'FE': FE,
            'archive_A1_size': len(X_A1),
            'archive_A2_size': len(X_A2),
            'generation_global': gen_global,
        })
        if save_history:
            history.append(_snapshot(X_A2, Y_A2, tu))

    pbar.close()

    # ------------------------ Finalization ---------------------------------
    X_nd, F_nd = find_non_dominated(X_A2, Y_A2)
    data = {}
    for i in range(X_nd.shape[1]):
        data[f'x_{i + 1}'] = X_nd[:, i]
    for j in range(F_nd.shape[1]):
        data[f'f{j + 1}'] = F_nd[:, j]
    df_pareto = pd.DataFrame(data)

    info = {
        'total_FE': FE,
        'n_updates': tu,
        'n_generations': gen_global,
        'archive_A2_size': len(X_A2),
        'n_nondominated': len(X_nd),
        'progress': progress_log,
    }

    if config.get('verbose', False):
        print(f'\n✅ K-RVEA-OPT concluído! FE={FE}/{FEmax}, '
              f'updates={tu}, non-dominated={len(X_nd)}')

    return df_pareto, info, history
