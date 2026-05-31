"""
Experiment harness for surrogate-assisted MOEA benchmarking.

Single entry point: ``experiment_sa_moea(algorithm, problem, seed)`` runs ONE
algorithm on ONE problem with ONE seed and returns a long-format DataFrame
with the full population recorded at every generation/iteration:

    columns: algorithm, problem, seed, generation, individual_id,
             x_1..x_n, f1..fm

The `f*` columns are always re-evaluated against the **clean** problem,
guaranteeing comparability across algorithms regardless of the surrogate or
noise source seen during optimization.

Used by:
    - Notebook ``2. optimization.ipynb`` (sequential loop, seed=42)
    - Script ``experiments.py`` (parallel via joblib over algo×problem×seed)
"""

from __future__ import annotations

import os
import warnings
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel

from src import problems as _problems_mod
from src.processing import NoisyProblem
from src.nsgaII_runner import run_my_nsga2
from src.k_rvea_runner import run_k_rvea
from src.dr_nsgaII_runner import run_dr_nsga2
from src.prob_moead_runner import run_prob_moead
from src.parego_runner import run_parego
from src.kta2_runner import run_kta2
from src.k_rvea_opt_runner import run_k_rvea_opt


# ═══════════════════════════════════════════════════════════════════════════
#  Problem catalog (short name → class name in src.problems)
# ═══════════════════════════════════════════════════════════════════════════

PROBLEM_CLASSES: dict[str, str] = {
    'MMF1':     'MMF1',
    'MMF4':     'MMF4',
    'MMF11_L':  'MMF11_L',
    'MMF16_L3': 'MMF16_L3',
    'MMF16_20': 'MMF16_20',
    'ZDT1':     'ZDT1',
    'ZDT3':     'ZDT3',
    'ZDT4':     'ZDT4',
    'ZDT6':     'ZDT6',
    'DTLZ1':    'DTLZ1',
    'DTLZ2':    'DTLZ2',
    'DTLZ3':    'DTLZ3',
    'DTLZ4':    'DTLZ4',
    'DTLZ7':    'DTLZ7',
    'WFG1':     'WFG1',
    'WFG2':     'WFG2',
    'WFG4':     'WFG4',
    'WFG5':     'WFG5',
    'WFG9':     'WFG9',
    'BBOB1':    'BBOB_F1_Sphere_Sphere',
    'BBOB5':    'BBOB_F5_Sphere_SharpRidge',
    'BBOB17':   'BBOB_F17_EllipsoidSeparable_SchafferF7',
    'BBOB22':   'BBOB_F22_AttractiveSector_SharpRidge',
    'BBOB37':   'BBOB_F37_SharpRidge_Rastrigin',
    'BBOB49':   'BBOB_F49_Rastrigin_Gallagher101',
    'BBOB55':   'BBOB_F55_Gallagher101_Gallagher101',
}

ALL_PROBLEMS: list[str] = list(PROBLEM_CLASSES)


def _instantiate_problem(short_name: str):
    """Instantiate a problem class by short name (e.g. 'MMF1' or 'BBOB1')."""
    cls_name = PROBLEM_CLASSES[short_name]
    return getattr(_problems_mod, cls_name)()


# ═══════════════════════════════════════════════════════════════════════════
#  Algorithm dispatch
# ═══════════════════════════════════════════════════════════════════════════

ALGORITHM_DISPATCH: dict[str, dict] = {
    'NSGA2_surrogate':  {'mode': 'offline_kriging', 'runner': run_my_nsga2},
    'DR-NSGA-II':       {'mode': 'offline_kriging', 'runner': run_dr_nsga2},
    'Prob-MOEA/D':      {'mode': 'offline_kriging', 'runner': run_prob_moead},
    'K-RVEA':           {'mode': 'online_noisy',    'runner': run_k_rvea},
    'ParEGO':           {'mode': 'online_noisy',    'runner': run_parego},
    'KTA2':             {'mode': 'online_noisy',    'runner': run_kta2},
    'K-RVEA-OPT':       {'mode': 'online_noisy',    'runner': run_k_rvea_opt},
}


def _apply_algorithm_overrides(cfg: dict, algo: str, n_var: int) -> dict:
    """Apply per-algorithm config tunings (centralized from the old notebook).

    Reads ``cfg['krvea_feval' | 'kta2_feval' | 'parego_feval' | 'n_generations']``
    so MODO_RAPIDO scaling (or any user override of those keys) is respected.
    Returns the mutated cfg.
    """
    if algo == 'K-RVEA':
        cfg['FEmax'] = cfg.get('krvea_feval', 300)
        cfg.setdefault('krvea_wmax', 20)
        cfg.setdefault('krvea_u', 5)
        cfg['krvea_NI'] = 11 * n_var - 1
    elif algo == 'K-RVEA-OPT':
        # Same overrides as K-RVEA: K-RVEA-OPT is a drop-in optimized
        # variant, not a new algorithm.
        cfg['FEmax'] = cfg.get('krvea_feval', 300)
        cfg.setdefault('krvea_wmax', 20)
        cfg.setdefault('krvea_u', 5)
        cfg['krvea_NI'] = 11 * n_var - 1
    elif algo == 'ParEGO':
        cfg['FEmax'] = cfg.get('parego_feval', 250)
        cfg['parego_NI'] = 11 * n_var - 1
    elif algo == 'KTA2':
        cfg['FEmax'] = cfg.get('kta2_feval', 300)
        cfg.setdefault('kta2_archive_size', 100)
        cfg.setdefault('kta2_eta', 5)
    elif algo == 'Prob-MOEA/D':
        cfg.setdefault('prob_moead_samples', 50)
        cfg.setdefault('moead_neighborhood', 20)
    return cfg


# ═══════════════════════════════════════════════════════════════════════════
#  Base configuration (same as notebook 2)
# ═══════════════════════════════════════════════════════════════════════════

BASE_CONFIG: dict = {
    'population_size': 100,
    'n_generations': 100,
    'krvea_feval':   300,
    'kta2_feval':    300,
    'parego_feval':  250,
    'k_tournament': 2,
    'crossover_prob': 0.9,
    'crossover_eta': 15,
    'mutation_eta': 20,
    'seed': 42,
    'track_progress': False,
    'utiliza_ds_niching': False,
    'pesos_ds_niching': [1, 1],
    'maximize': False,
    'n_restricoes': 0,
    'tipo_variavel_genotipo': float,
    'verbose': False,
    'mostrar_grafico': False,
}


NOISE_CONFIG: dict = {
    1:  {'dist': 'bimodal',     'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'p': [0.6, 0.4], 'mu1': -2, 'sd1': 0.5, 'mu2': 2, 'sd2': 1}},
    2:  {'dist': 'student_t',   'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'df': 3}},
    3:  {'dist': 'lognormal',   'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'mean': 0, 'sigma': 0.8}},
    4:  {'dist': 'poisson',     'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'lam': 5.0}},
    5:  {'dist': 'binomial',    'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'n': 10, 'p': 0.5}},
    6:  {'dist': 'geometric',   'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'p': 0.3}},
    7:  {'dist': 'exponential', 'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'scale': 1.0}},
    8:  {'dist': 'uniform',     'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'low': -1.0, 'high': 1.0}},
    9:  {'dist': 'laplace',     'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'loc': 0.0, 'scale': 1.0}},
    10: {'dist': 'gamma',       'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'shape': 2.0, 'scale': 2.0}},
    11: {'dist': 'beta',        'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'a': 0.5, 'b': 0.5}},
    12: {'dist': 'rayleigh',    'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'scale': 1.0}},
    13: {'dist': 'weibull',     'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'a': 1.5}},
    14: {'dist': 'logistic',    'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'loc': 0.0, 'scale': 1.0}},
    15: {'dist': 'pareto',      'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {'a': 3.0}},
    16: {'dist': 'rademacher',  'target_mean': 0.0, 'forca_ruido': 0.2, 'params': {}},
}


# ═══════════════════════════════════════════════════════════════════════════
#  Kriging training (replaces df_previsao dependency)
# ═══════════════════════════════════════════════════════════════════════════

def _train_one_gp(X, y, seed):
    kernel = ConstantKernel(1.0) * Matern(nu=2.5)
    gp = GaussianProcessRegressor(
        kernel=kernel, alpha=1e-3,
        n_restarts_optimizer=2, normalize_y=True,
        random_state=seed,
    )
    gp.fit(X, y)
    return gp


def _train_kriging_from_landscape(clean_problem, noisy_problem, seed: int,
                                   n_train: int = 500):
    """Train one Kriging (GP) model per objective.

    Replaces the old ``train_kriging_surrogates(df_previsao, ...)`` dependency:
    samples ``n_train`` points via Latin Hypercube Sampling within the problem
    bounds and queries the ``noisy_problem`` (NoisyProblem wrapper) to obtain
    noisy fitness for training.  Deterministic given ``(problem, seed)``.

    LHS is preferred over Sobol here because ``n_train`` is not constrained to
    a power of 2 (Sobol's balance properties require ``n = 2^k``); LHS gives
    well-spread coverage for any ``n`` and is the canonical DOE for kriging.
    """
    sampler = qmc.LatinHypercube(d=clean_problem.n_var, seed=seed)
    U = sampler.random(n_train)
    X = qmc.scale(U, clean_problem.xl, clean_problem.xu)
    out = {'F': np.zeros((n_train, clean_problem.n_obj))}
    noisy_problem._evaluate(X, out)
    return [_train_one_gp(X, out['F'][:, j], seed)
            for j in range(clean_problem.n_obj)]


# ═══════════════════════════════════════════════════════════════════════════
#  Runner dispatch and history → long-DataFrame
# ═══════════════════════════════════════════════════════════════════════════

def _build_config(problem_name: str, seed: int, clean_problem,
                  algorithm: str, base_config: dict | None) -> dict:
    """Merge BASE_CONFIG + per-problem fields + per-algorithm overrides."""
    cfg = (base_config or BASE_CONFIG).copy()
    cfg['seed'] = seed
    cfg['tamanho_genotipo'] = clean_problem.n_var
    cfg['limite_inferior'] = clean_problem.xl.copy()
    cfg['limite_superior'] = clean_problem.xu.copy()
    cfg['n_objetivos'] = clean_problem.n_obj
    cfg['fitness_cols'] = [f'fitness{j+1}' for j in range(clean_problem.n_obj)]
    cfg['mutation_prob'] = 1.0 / clean_problem.n_var
    cfg['alpha_exploration_rank_distance'] = np.linspace(
        1.0, 0.0, cfg['n_generations'])
    return _apply_algorithm_overrides(cfg, algorithm, clean_problem.n_var)


def _invoke_runner(algorithm: str, cfg: dict, clean_problem,
                   problem_for_runners, kriging_models):
    """Dispatch to the appropriate runner with ``save_history=True``.

    Parameters
    ----------
    problem_for_runners : pymoo Problem
        The problem instance passed to the online runners (K-RVEA, ParEGO,
        KTA2). It is the ``NoisyProblem`` wrapper when ``noisy_problem=True``
        in the caller, and the bare ``clean_problem`` when ``False``.
        (Previously misnamed ``noisy_problem``.)

    Returns the ``history`` list (see _history_to_long_df for schema).
    """
    if algorithm == 'NSGA2_surrogate':
        _, _, history = run_my_nsga2(cfg, kriging_models=kriging_models,
                                     save_history=True)
    elif algorithm == 'DR-NSGA-II':
        _, _, history = run_dr_nsga2(cfg, kriging_models=kriging_models,
                                     save_history=True, z=1.28)
    elif algorithm == 'Prob-MOEA/D':
        _, _, history = run_prob_moead(cfg, kriging_models=kriging_models,
                                       save_history=True)
    elif algorithm == 'K-RVEA':
        _, _, history = run_k_rvea(problem_for_runners, cfg, save_history=True)
    elif algorithm == 'ParEGO':
        _, _, history = run_parego(problem_for_runners, cfg, save_history=True)
    elif algorithm == 'KTA2':
        _, _, history = run_kta2(problem_for_runners, cfg, save_history=True)
    elif algorithm == 'K-RVEA-OPT':
        _, _, history = run_k_rvea_opt(problem_for_runners, cfg,
                                       save_history=True)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return history


def _history_to_long_df(history, algorithm: str, problem_name: str,
                        seed: int, clean_problem) -> pd.DataFrame:
    """Convert runner history (list of {'generation', 'population'}) into the
    long-format DataFrame defined by the harness spec.

    Re-evaluates ``f*`` columns vectorized on the **clean** problem so values
    are comparable across algorithms regardless of surrogate/noise during
    search.
    """
    n_var = clean_problem.n_var
    n_obj = clean_problem.n_obj

    rows = []
    for snap in history:
        g = snap['generation']
        for idx, ind in enumerate(snap['population']):
            geno = ind['genotype']
            row = {
                'algorithm': algorithm,
                'problem': problem_name,
                'seed': seed,
                'generation': g,
                'individual_id': idx,
            }
            for i in range(n_var):
                row[f'x_{i+1}'] = float(geno[i])
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        for j in range(n_obj):
            df[f'f{j+1}'] = pd.Series(dtype=float)
        return df

    # Vectorized clean re-evaluation
    x_cols = [f'x_{i+1}' for i in range(n_var)]
    X = df[x_cols].to_numpy(dtype=float)
    out = {'F': np.zeros((len(X), n_obj))}
    clean_problem._evaluate(X, out)
    for j in range(n_obj):
        df[f'f{j+1}'] = out['F'][:, j]

    return df


# ═══════════════════════════════════════════════════════════════════════════
#  Public entry point
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_SINGLE_DIR = 'data/experiments/single'


def _safe_algo_name(name: str) -> str:
    return name.replace('/', '_').replace(' ', '_').replace('-', '_').lower()


def experiment_cache_path(algorithm: str, problem: str, seed: int,
                          single_dir: str = DEFAULT_SINGLE_DIR,
                          noisy_problem: bool = True) -> str:
    """Path of the per-experiment parquet cache under ``single_dir``.

    When ``noisy_problem=True`` a ``_noisy`` suffix is added so that
    noisy/clean runs don't overwrite each other. When ``noisy_problem=False``
    no suffix is used (clean is the default/canonical cache name).
    """
    suffix = '_noisy' if noisy_problem else ''
    return os.path.join(
        single_dir,
        f'{_safe_algo_name(algorithm)}_{problem}_seed{seed}{suffix}.parquet',
    )


def experiment_sa_moea(
    algorithm: str,
    problem: str,
    seed: int,
    config: dict | None = None,
    *,
    kriging_models=None,
    sampling_method: str = 'sobol',
    load_memory: bool = True,
    single_dir: str = DEFAULT_SINGLE_DIR,
    noisy_problem: bool = True,
) -> pd.DataFrame:
    """Run one (algorithm, problem, seed) experiment with population logging.

    Parameters
    ----------
    algorithm : key of ``ALGORITHM_DISPATCH``.
    problem   : short problem name (key of ``PROBLEM_CLASSES``).
    seed      : integer random seed (sets numpy RNG inside the runner).
    config    : optional config dict override; merged on top of BASE_CONFIG.
    kriging_models : optional pre-trained list of GPs (one per objective);
        skips internal Kriging training (used by ``experiments.py`` cache).
    sampling_method : one of {'sobol', 'latin_hypercube', 'random'} —
        used to locate the cached landscape parquet for the mean_f estimate.
    load_memory : bool, default True
        If True, before running, check ``single_dir`` for a parquet matching
        ``(algorithm, problem, seed)``; if present, load and return it instead
        of recomputing. The freshly computed DataFrame is also saved back to
        ``single_dir`` so the next call can hit the cache.
    single_dir : str, default ``data/experiments/single``
        Directory used for the per-experiment parquet cache.
    noisy_problem : bool, default True
        If True (legado), envolve o problema base com ``NoisyProblem`` —
        Kriging eh treinado sobre amostras ruidosas e os algoritmos online
        (K-RVEA, ParEGO, KTA2) buscam sobre o problema ruidoso. O cache do
        parquet recebe sufixo ``_noisy``.
        If False, usa o problema original sem transformacao: Kriging eh
        treinado sobre fitness limpa e os runners recebem o problema base.
        O cache do parquet NAO recebe sufixo (nome canonico).

    Returns
    -------
    pd.DataFrame in long format with columns
        ``algorithm, problem, seed, generation, individual_id,
        x_1..x_n, f1..fm``
    where ``f*`` are clean (true) fitness values.
    """
    if load_memory:
        cache_path = experiment_cache_path(algorithm, problem, seed, single_dir,
                                            noisy_problem=noisy_problem)
        if os.path.exists(cache_path):
            try:
                df_cached = pd.read_parquet(cache_path)
                print(f'parquet {cache_path} encontrado')
                return df_cached
            except Exception:
                # corrupt cache → fall through and recompute
                pass

    if algorithm not in ALGORITHM_DISPATCH:
        raise ValueError(f"Unknown algorithm '{algorithm}'. "
                         f"Available: {list(ALGORITHM_DISPATCH)}")
    if problem not in PROBLEM_CLASSES:
        raise ValueError(f"Unknown problem '{problem}'. "
                         f"Available: {list(PROBLEM_CLASSES)}")

    clean_problem = _instantiate_problem(problem)
    assert clean_problem.n_var >= 2, "NoisyProblem requires n_var >= 2"

    cfg = _build_config(problem, seed, clean_problem, algorithm, config)

    # 1. Build NoisyProblem from landscape mean_f (apenas se noisy_problem=True).
    #    Caso contrario, os runners online recebem o problema limpo e o
    #    Kriging eh treinado sobre fitness limpa.
    if noisy_problem:
        base_dir = Path('data/dataframes') / problem
        landscape_path = base_dir / f'df_{problem}_landscape_{sampling_method}.parquet'
        df_land = pd.read_parquet(landscape_path)
        f_cols = [f'f{j+1}' for j in range(clean_problem.n_obj)]
        mean_f = df_land[f_cols].mean().to_numpy()
        problem_for_runners = NoisyProblem(clean_problem, NOISE_CONFIG, mean_f)
        assert isinstance(problem_for_runners, NoisyProblem), \
            "noisy_problem=True deve produzir um wrapper NoisyProblem"
    else:
        problem_for_runners = clean_problem
        # Invariante: com noisy_problem=False, NAO deve haver wrapper de ruido.
        # Garante que nenhum caminho acima injetou um NoisyProblem por engano.
        assert not isinstance(problem_for_runners, NoisyProblem), \
            "noisy_problem=False mas problem_for_runners ficou NoisyProblem"
        assert problem_for_runners is clean_problem, \
            "noisy_problem=False exige que os runners recebam o clean_problem"

    # 2. Kriging surrogates for offline_kriging algorithms
    mode = ALGORITHM_DISPATCH[algorithm]['mode']
    if mode == 'offline_kriging' and kriging_models is None:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=ConvergenceWarning)
            kriging_models = _train_kriging_from_landscape(
                clean_problem, problem_for_runners, seed,
                n_train=cfg.get('n_kriging_train', 500))

    # 3. Run with save_history=True
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=ConvergenceWarning)
        history = _invoke_runner(algorithm, cfg, clean_problem,
                                  problem_for_runners, kriging_models)

    if history is None or len(history) == 0:
        # Defensive: return empty DataFrame with expected columns
        cols = (['algorithm', 'problem', 'seed', 'generation', 'individual_id']
                + [f'x_{i+1}' for i in range(clean_problem.n_var)]
                + [f'f{j+1}' for j in range(clean_problem.n_obj)])
        return pd.DataFrame(columns=cols)

    # 4. Convert history → long-DataFrame with clean re-eval
    df_long = _history_to_long_df(history, algorithm, problem, seed,
                                   clean_problem)

    if load_memory:
        cache_path = experiment_cache_path(algorithm, problem, seed, single_dir,
                                            noisy_problem=noisy_problem)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        try:
            df_long.to_parquet(cache_path)
        except Exception:
            pass

    return df_long


# ═══════════════════════════════════════════════════════════════════════════
#  Kriging disk cache (used by experiments.py parallel script)
# ═══════════════════════════════════════════════════════════════════════════

def kriging_cache_path(problem: str, seed: int,
                        cache_dir: str = 'data/experiments/kriging_cache',
                        noisy_problem: bool = True) -> str:
    """Path of the Kriging .pkl cache.

    ``noisy_problem=True`` adds a ``_noisy`` suffix; ``noisy_problem=False``
    uses no suffix (clean is the default/canonical name).
    """
    suffix = '_noisy' if noisy_problem else ''
    return os.path.join(cache_dir, f'{problem}_seed{seed}{suffix}.pkl')


def train_and_cache_kriging(problem: str, seed: int,
                             cache_dir: str = 'data/experiments/kriging_cache',
                             n_train: int = 500,
                             sampling_method: str = 'sobol',
                             skip_existing: bool = True,
                             noisy_problem: bool = True) -> str:
    """Train Kriging models for (problem, seed) and pickle them.

    Returns the path to the pickle file.  Shared across NSGA2_surrogate,
    DR-NSGA-II, Prob-MOEA/D for the same (problem, seed).

    Quando ``noisy_problem=False`` (default) o GP eh treinado sobre fitness
    limpa do problema original (sem o wrapper NoisyProblem) e o cache eh
    gravado SEM sufixo. Quando ``noisy_problem=True`` o cache recebe sufixo
    ``_noisy``.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = kriging_cache_path(problem, seed, cache_dir,
                              noisy_problem=noisy_problem)
    if skip_existing and os.path.exists(path):
        return path

    clean_problem = _instantiate_problem(problem)
    if noisy_problem:
        base_dir = Path('data/dataframes') / problem
        landscape_path = base_dir / f'df_{problem}_landscape_{sampling_method}.parquet'
        df_land = pd.read_parquet(landscape_path)
        f_cols = [f'f{j+1}' for j in range(clean_problem.n_obj)]
        mean_f = df_land[f_cols].mean().to_numpy()
        problem_for_training = NoisyProblem(clean_problem, NOISE_CONFIG, mean_f)
    else:
        problem_for_training = clean_problem

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=ConvergenceWarning)
        models = _train_kriging_from_landscape(
            clean_problem, problem_for_training, seed, n_train=n_train)

    with open(path, 'wb') as f:
        pickle.dump(models, f)
    return path


def load_kriging_cache(problem: str, seed: int,
                        cache_dir: str = 'data/experiments/kriging_cache',
                        noisy_problem: bool = True):
    """Return pickled Kriging models for (problem, seed) or None if missing."""
    path = kriging_cache_path(problem, seed, cache_dir,
                              noisy_problem=noisy_problem)
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)
