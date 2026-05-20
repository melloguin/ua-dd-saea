"""
Parallel experiment runner for surrogate-assisted MOEA benchmarking.

Mirrors the pattern of ``fitness_landscape.py``: one task per
(algorithm, problem, seed) triple, dispatched via ``joblib.Parallel``
with the ``loky`` backend.

Usage:
    python experiments.py                                   # full run, all defaults
    python experiments.py --modo-rapido                     # quick smoke test
    python experiments.py --algorithms NSGA2_surrogate K-RVEA \
                          --problems MMF1 MMF4 \
                          --seeds 42 43 --n-jobs 4 --modo-rapido

Output layout:
    data/experiments/kriging_cache/{problem}_seed{seed}.pkl  (shared GPs)
    data/experiments/single/{algo}_{problem}_seed{seed}.parquet  (per-task)
    data/experiments/all.parquet                              (consolidated)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

# Ensure src/ is importable when invoked from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.experiment import (
    ALGORITHM_DISPATCH,
    ALL_PROBLEMS,
    BASE_CONFIG,
    experiment_sa_moea,
    train_and_cache_kriging,
    load_kriging_cache,
)


DEFAULT_ALGORITHMS = list(ALGORITHM_DISPATCH)
DEFAULT_SEEDS = [42, 43, 44, 45, 46]
DEFAULT_SINGLE_DIR = 'data/experiments/single'
DEFAULT_KRIGING_CACHE_DIR = 'data/experiments/kriging_cache'
DEFAULT_OUT = 'data/experiments/all.parquet'


def _safe(name: str) -> str:
    return name.replace('/', '_').replace(' ', '_').replace('-', '_').lower()


def _build_cfg(modo_rapido: bool) -> dict:
    cfg = BASE_CONFIG.copy()
    if modo_rapido:
        cfg['n_generations'] = max(1, int(cfg['n_generations'] * 0.1))
        cfg['krvea_feval']   = max(1, int(cfg['krvea_feval']   * 0.1))
        cfg['kta2_feval']    = max(1, int(cfg['kta2_feval']    * 0.1))
        cfg['parego_feval']  = max(1, int(cfg['parego_feval']  * 0.1))
        cfg['FEmax']         = cfg['krvea_feval']
    return cfg


def _task_safe(algo: str, problem: str, seed: int, cfg: dict,
               single_dir: str, kriging_cache_dir: str,
               skip_existing: bool):
    """One unit of parallel work — one experiment, one parquet, one tuple."""
    out_path = os.path.join(single_dir, f'{_safe(algo)}_{problem}_seed{seed}.parquet')

    if skip_existing and os.path.exists(out_path):
        try:
            df = pd.read_parquet(out_path)
            return (algo, problem, seed, True, 'skip_existing', df)
        except Exception as e:
            # Cached file corrupt — fall through to re-run
            pass

    try:
        kr = load_kriging_cache(problem, seed, cache_dir=kriging_cache_dir)
        df = experiment_sa_moea(algo, problem, seed, config=cfg,
                                 kriging_models=kr)
        df.to_parquet(out_path)
        return (algo, problem, seed, True, '', df)
    except Exception as e:
        err = f'{type(e).__name__}: {e}'
        # Capture traceback for diagnostics
        tb = traceback.format_exc()
        return (algo, problem, seed, False, err + '\n' + tb, None)


def _precache_kriging(problems, seeds, cache_dir: str, skip_existing: bool,
                       n_train: int = 500, n_jobs: int = 1):
    """Train and cache Kriging models for every (problem, seed) pair.

    Same models are reused by NSGA2_surrogate, DR-NSGA-II, Prob-MOEA/D.
    Skipped if file already exists and skip_existing=True.
    """
    os.makedirs(cache_dir, exist_ok=True)
    pairs = [(p, s) for p in problems for s in seeds]

    def _one(p, s):
        try:
            train_and_cache_kriging(p, s, cache_dir=cache_dir,
                                     n_train=n_train,
                                     skip_existing=skip_existing)
            return (p, s, True, '')
        except Exception as e:
            return (p, s, False, f'{type(e).__name__}: {e}')

    print(f'[Stage 1/3] Pre-caching Kriging for {len(pairs)} (problem, seed) pairs ...')
    results = Parallel(n_jobs=n_jobs, backend='loky', verbose=1)(
        delayed(_one)(p, s) for p, s in pairs
    )
    failed = [(p, s, e) for p, s, ok, e in results if not ok]
    if failed:
        print(f'  ⚠ {len(failed)} Kriging caches failed:')
        for p, s, e in failed[:10]:
            print(f'     - {p} seed={s}: {e}')


def _print_summary(ok, fail, elapsed):
    print('\n' + '=' * 70)
    print(f'Done in {elapsed:.1f}s.  OK: {len(ok)}  FAIL: {len(fail)}')
    print('=' * 70)
    if fail:
        print('Failures:')
        for algo, problem, seed, _, err, _ in fail[:20]:
            first_line = err.splitlines()[0] if err else ''
            print(f'  - {algo} | {problem} | seed={seed}: {first_line}')
        if len(fail) > 20:
            print(f'  ... and {len(fail) - 20} more')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('--algorithms', nargs='+', default=DEFAULT_ALGORITHMS,
                    help='Algorithms to run (subset of ALGORITHM_DISPATCH).')
    p.add_argument('--problems', nargs='+', default=ALL_PROBLEMS,
                    help='Problems to run (short names from PROBLEM_CLASSES).')
    p.add_argument('--seeds', nargs='+', type=int, default=DEFAULT_SEEDS,
                    help='Random seeds.')
    p.add_argument('--n-jobs', type=int, default=10,
                    help='Parallel workers for joblib (default: 10).')
    p.add_argument('--modo-rapido', action='store_true',
                    help='Scale iteration budgets to 10%% for quick tests.')
    p.add_argument('--single-dir', default=DEFAULT_SINGLE_DIR,
                    help=f'Per-task parquet dir (default: {DEFAULT_SINGLE_DIR}).')
    p.add_argument('--kriging-cache-dir', default=DEFAULT_KRIGING_CACHE_DIR,
                    help='Where to cache trained Kriging models per (problem, seed).')
    p.add_argument('--out', default=DEFAULT_OUT,
                    help=f'Consolidated parquet path (default: {DEFAULT_OUT}).')
    p.add_argument('--skip-existing', action='store_true',
                    help='Skip tasks whose parquet already exists.')
    p.add_argument('--no-kriging-cache', action='store_true',
                    help='Skip pre-caching of Kriging models (re-train per task).')
    p.add_argument('--no-consolidate', action='store_true',
                    help='Skip the final pd.concat / out.parquet step.')
    args = p.parse_args()

    # Validate inputs
    bad_algos = [a for a in args.algorithms if a not in ALGORITHM_DISPATCH]
    if bad_algos:
        raise SystemExit(f'Unknown algorithms: {bad_algos}. '
                          f'Available: {list(ALGORITHM_DISPATCH)}')
    bad_probs = [p for p in args.problems if p not in ALL_PROBLEMS]
    if bad_probs:
        raise SystemExit(f'Unknown problems: {bad_probs}.')

    os.makedirs(args.single_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    os.makedirs(args.kriging_cache_dir, exist_ok=True)

    cfg = _build_cfg(args.modo_rapido)

    # ── Stage 1: Pre-cache Kriging ────────────────────────────────────────
    if not args.no_kriging_cache:
        _precache_kriging(args.problems, args.seeds,
                           cache_dir=args.kriging_cache_dir,
                           skip_existing=args.skip_existing,
                           n_train=cfg.get('n_kriging_train', 500),
                           n_jobs=args.n_jobs)

    # ── Stage 2: Parallel experiments ─────────────────────────────────────
    tasks = [(a, p, s)
              for a in args.algorithms
              for p in args.problems
              for s in args.seeds]
    print(f'\n[Stage 2/3] Running {len(tasks)} tasks on {args.n_jobs} workers '
          f'(algorithms={len(args.algorithms)} × problems={len(args.problems)} '
          f'× seeds={len(args.seeds)}) ...')

    t0 = time.time()
    results = Parallel(n_jobs=args.n_jobs, backend='loky', verbose=5)(
        delayed(_task_safe)(a, p, s, cfg, args.single_dir,
                             args.kriging_cache_dir, args.skip_existing)
        for a, p, s in tasks
    )
    elapsed = time.time() - t0

    ok = [r for r in results if r[3]]
    fail = [r for r in results if not r[3]]
    _print_summary(ok, fail, elapsed)

    # ── Stage 3: Consolidate ──────────────────────────────────────────────
    if args.no_consolidate:
        print('\n[Stage 3/3] Skipping consolidation (--no-consolidate).')
        return

    print(f'\n[Stage 3/3] Consolidating {len(ok)} task DataFrames → {args.out} ...')
    dfs = [r[5] for r in ok if r[5] is not None]
    if not dfs:
        print('  No DataFrames to consolidate.')
        return

    df_all = pd.concat(dfs, ignore_index=True)
    df_all.to_parquet(args.out)
    print(f'  Saved: {args.out}  shape={df_all.shape}')


if __name__ == '__main__':
    main()
