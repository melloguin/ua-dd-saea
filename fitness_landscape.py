"""
Geracao e cache dos parquets de landscape e PF empirico.

Espelha a parte de geracao/salvamento do notebook `1. fitness_landscape.ipynb`,
sem nenhuma visualizacao. Pensado para ser executado via linha de comando,
tipicamente numa VM com mais memoria/CPU.

Dois modos de execucao:
    1. UM problema: passe o nome da classe como argumento.
    2. TODOS os problemas em paralelo (menos BBOB_Gallagher_Mock): rode
       sem argumentos. Usa joblib para spawnar um processo por problema
       (um nucleo por problema por padrao; controlavel via --n-jobs).

Uso basico:
    # Todos os problemas em paralelo (um core por problema):
    python fitness_landscape.py

    # Apenas um problema:
    python fitness_landscape.py MMF16_L3

Outros exemplos:
    # Todos em paralelo com 1M de amostras-alvo cada:
    python fitness_landscape.py --n-samples 1000000

    # Todos em paralelo usando no maximo 4 processos simultaneos:
    python fitness_landscape.py --n-jobs 4

    # Um problema, so um metodo:
    python fitness_landscape.py DTLZ2 --methods sobol

    # Um problema, ignora cache e regera tudo:
    python fitness_landscape.py WFG4 --force

Arquivos gerados em data/dataframes/{name}/:
    df_{name}_landscape_{method}.parquet     (amostras X + F)
    df_{name}_pf_empirico_{method}.parquet   (linhas nao-dominadas, X + F)

O comportamento de cache e identico ao notebook (carrega_resultados):
    - por padrao, le cada parquet existente e recalcula somente o ausente;
    - com --force, sempre recalcula e sobrescreve.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import qmc
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from src import problems as _problems_mod
from src.problems import evaluate_problem


VALID_METHODS = ['sobol', 'latin_hypercube', 'random']

DATA_DIR = 'data/dataframes'

# Todos os problemas do catalogo (src.problems), na ordem de apresentacao
# do notebook `1. fitness_landscape.ipynb`. BBOB_Gallagher_Mock e
# deliberadamente excluido (sem PF analitico e fora do escopo das rodadas
# em massa).
ALL_PROBLEMS: List[str] = [
    'MMF1', 'MMF4', 'MMF11_L', 'MMF16_L3', 'MMF16_20',
    'ZDT1', 'ZDT3', 'ZDT4', 'ZDT6',
    'DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7',
    'WFG1', 'WFG2', 'WFG4', 'WFG5', 'WFG9',
]

# Efficient Non-dominated Sort (ENS, Roy et al. 2016): O(N * log^(M-1) N) e
# sem matriz NxN - necessario para landscapes grandes (N >> 1e5).
_NDS = NonDominatedSorting(method="efficient_non_dominated_sort")


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def generate_samples(problem, n_samples: int = 100_000, method: str = 'sobol'
                     ) -> Tuple[np.ndarray, np.ndarray]:
    """Sample the decision space and evaluate objectives.

    Uses a full grid for n_var <= 3 (regardless of method).
    For n_var > 3:
      'sobol'           - scrambled Sobol sequence; 2^ceil(log2(n_samples)) points.
      'latin_hypercube' - Latin Hypercube Sampling.
      'random'          - uniform random sampling.
    """
    if method not in VALID_METHODS:
        raise ValueError(f"method must be one of {VALID_METHODS}, got '{method}'")
    n = problem.n_var
    if n <= 3:
        n_pts = max(2, int(round(n_samples ** (1.0 / n))))
        grids = [np.linspace(problem.xl[i], problem.xu[i], n_pts) for i in range(n)]
        mesh = np.meshgrid(*grids, indexing='ij')
        X = np.column_stack([m.ravel() for m in mesh])
    else:
        if method == 'sobol':
            m = int(np.ceil(np.log2(n_samples)))
            sampler = qmc.Sobol(d=n, scramble=True, seed=42)
            X = qmc.scale(sampler.random_base2(m), problem.xl, problem.xu)
        elif method == 'latin_hypercube':
            sampler = qmc.LatinHypercube(d=n, seed=42)
            X = qmc.scale(sampler.random(n_samples), problem.xl, problem.xu)
        elif method == 'random':
            rng = np.random.default_rng(42)
            X = rng.uniform(problem.xl, problem.xu, size=(n_samples, n))
    return X, evaluate_problem(problem, X)


# ---------------------------------------------------------------------------
# Cache helpers (mesma semantica que o notebook)
# ---------------------------------------------------------------------------

def _landscape_path(out_dir: str, name: str, method: str) -> str:
    return os.path.join(out_dir, f'df_{name}_landscape_{method}.parquet')


def _pf_empirico_path(out_dir: str, name: str, method: str) -> str:
    return os.path.join(out_dir, f'df_{name}_pf_empirico_{method}.parquet')


def _load_or_generate_landscape(problem, name, method, n_samples, out_dir,
                                x_cols, f_cols, carrega_resultados
                                ) -> Tuple[np.ndarray, np.ndarray]:
    """Try to load the landscape parquet; otherwise generate and save."""
    path = _landscape_path(out_dir, name, method)
    if carrega_resultados and os.path.exists(path):
        df = pd.read_parquet(path)
        X = df[x_cols].to_numpy()
        F = df[f_cols].to_numpy()
        print(f'  Landscape carregado de {path}: {len(X):,} pontos')
    else:
        t0 = time.time()
        X, F = generate_samples(problem, n_samples, method=method)
        df = pd.DataFrame(np.column_stack([X, F]), columns=x_cols + f_cols)
        df.to_parquet(path)
        print(f'  Landscape gerado e salvo em {path}: {len(X):,} pontos '
              f'({time.time() - t0:.1f}s)')
    return X, F


def _load_or_compute_pf(X, F, name, method, out_dir, x_cols, f_cols,
                        carrega_resultados) -> Tuple[np.ndarray, np.ndarray]:
    """Try to load the empirical PF parquet; otherwise compute via NDS and save."""
    path = _pf_empirico_path(out_dir, name, method)
    if carrega_resultados and os.path.exists(path):
        df_pf = pd.read_parquet(path)
        pf_X = df_pf[x_cols].to_numpy()
        pf_F = df_pf[f_cols].to_numpy()
        print(f'  PF empirico carregado de {path}: {len(pf_F)} pontos')
    else:
        t0 = time.time()
        pf_idx = _NDS.do(F, only_non_dominated_front=True)
        pf_X = X[pf_idx]
        pf_F = F[pf_idx]
        df_pf = pd.DataFrame(np.column_stack([pf_X, pf_F]),
                             columns=x_cols + f_cols)
        df_pf.to_parquet(path)
        print(f'  PF empirico calculado e salvo em {path}: {len(pf_F)} pontos '
              f'({time.time() - t0:.1f}s)')
    return pf_X, pf_F


# ---------------------------------------------------------------------------
# Pipeline por problema
# ---------------------------------------------------------------------------

def process_problem(name: str,
                    n_samples: int = 100_000,
                    methods: Optional[List[str]] = None,
                    carrega_resultados: bool = True) -> None:
    """
    Gera/carrega os parquets de landscape e PF empirico para `name`.

    Parameters
    ----------
    name : str
        Nome da classe do problema em `src.problems` (ex: 'MMF16_L3', 'ZDT1').
    n_samples : int
        Numero-alvo de amostras por metodo (Sobol usa a potencia de 2 mais
        proxima; grid 1D/2D/3D quando n_var<=3).
    methods : list of str or None
        Subconjunto de ['sobol', 'latin_hypercube', 'random']. None = todos.
    carrega_resultados : bool
        True  -> le os parquets existentes, so recalcula o que faltar.
        False -> recalcula e sobrescreve tudo.
    """
    if methods is None:
        methods = list(VALID_METHODS)
    for m in methods:
        if m not in VALID_METHODS:
            raise ValueError(f"method invalido: {m!r}. Validos: {VALID_METHODS}")

    if not hasattr(_problems_mod, name):
        raise ValueError(
            f"Problema '{name}' nao encontrado em src.problems. "
            f"Verifique a grafia (ex: 'MMF16_L3', 'ZDT1', 'DTLZ2', 'WFG4')."
        )
    cls = getattr(_problems_mod, name)
    problem = cls()

    x_cols = [f'x_{i+1}' for i in range(problem.n_var)]
    f_cols = [f'f{i+1}' for i in range(problem.n_obj)]
    out_dir = os.path.join(DATA_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    print(f'\n========== {name} '
          f'(n_var={problem.n_var}, n_obj={problem.n_obj}, '
          f'n_samples_alvo={n_samples:,}, carrega_resultados={carrega_resultados}) ==========')

    for method in methods:
        print(f'\n[{method}] Processando {name}...')
        X, F = _load_or_generate_landscape(
            problem, name, method, n_samples, out_dir, x_cols, f_cols,
            carrega_resultados)
        _load_or_compute_pf(
            X, F, name, method, out_dir, x_cols, f_cols,
            carrega_resultados)

    print(f'\n>>> {name}: OK. Arquivos em {out_dir}/')


# ---------------------------------------------------------------------------
# Execucao paralela (todos os problemas)
# ---------------------------------------------------------------------------

def _process_problem_safe(name: str, n_samples: int,
                          methods: Optional[List[str]],
                          carrega_resultados: bool) -> Tuple[str, bool, str]:
    """Wrapper para uso em joblib: captura excecoes para nao matar a pool."""
    try:
        process_problem(name=name, n_samples=n_samples, methods=methods,
                        carrega_resultados=carrega_resultados)
        return (name, True, '')
    except Exception as e:
        return (name, False, f'{type(e).__name__}: {e}')


def run_all_parallel(problems: List[str], n_samples: int,
                     methods: Optional[List[str]], carrega_resultados: bool,
                     n_jobs: int) -> int:
    """Roda `process_problem` para cada item de `problems` em paralelo.

    Retorna o numero de problemas que falharam.
    """
    print(f'\n>>> Rodando {len(problems)} problemas em paralelo '
          f'(n_jobs={n_jobs}, n_samples={n_samples:,}, '
          f'carrega_resultados={carrega_resultados})')
    print(f'>>> Problemas: {", ".join(problems)}\n')

    t0 = time.time()
    # backend='loky' (default) usa multiprocessing isolado, o que evita
    # conflitos de GIL e de cache de Cython entre os processos da pymoo.
    results = Parallel(n_jobs=n_jobs, backend='loky', verbose=5)(
        delayed(_process_problem_safe)(
            name, n_samples, methods, carrega_resultados
        )
        for name in problems
    )
    elapsed = time.time() - t0

    ok = [r for r in results if r[1]]
    fail = [r for r in results if not r[1]]

    print('\n================ RESUMO ================')
    print(f'Tempo total: {elapsed:.1f}s')
    print(f'OK   ({len(ok)}): {", ".join(n for n, _, _ in ok) or "-"}')
    if fail:
        print(f'FAIL ({len(fail)}):')
        for name, _, err in fail:
            print(f'  - {name}: {err}')
    print('========================================')
    return len(fail)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='fitness_landscape.py',
        description=('Gera e salva os parquets de landscape e PF empirico '
                     'para problemas do catalogo (src.problems). Sem argumento '
                     'posicional, roda TODOS os problemas (menos BBOB) em '
                     'paralelo via joblib (um processo por problema).'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Exemplos:\n'
            '  # Todos os problemas em paralelo (um core por problema):\n'
            '  python fitness_landscape.py\n'
            '\n'
            '  # Um problema so:\n'
            '  python fitness_landscape.py MMF16_L3\n'
            '\n'
            '  # Todos em paralelo, 1M de amostras cada:\n'
            '  python fitness_landscape.py --n-samples 1000000\n'
            '\n'
            '  # Todos em paralelo, limitado a 4 processos:\n'
            '  python fitness_landscape.py --n-jobs 4\n'
            '\n'
            '  # Um problema, so um metodo:\n'
            '  python fitness_landscape.py DTLZ2 --methods sobol\n'
            '\n'
            '  # Um problema, forca recalculo:\n'
            '  python fitness_landscape.py WFG4 --force\n'
        ),
    )
    p.add_argument('problem', nargs='?', default=None,
                   help=("Nome da classe do problema (ex: MMF16_L3, ZDT1, "
                         "DTLZ2, WFG4). Omita para rodar TODOS em paralelo."))
    p.add_argument('--n-samples', type=int, default=100_000,
                   help="Numero-alvo de amostras por metodo (default: 100000).")
    p.add_argument('--methods', nargs='+', choices=VALID_METHODS,
                   default=None,
                   help=("Metodos a processar (default: todos). "
                         "Ex: --methods sobol latin_hypercube"))
    p.add_argument('--force', action='store_true',
                   help=("Ignora os parquets existentes e recalcula tudo "
                         "(equivalente a carrega_resultados=False no notebook)."))
    p.add_argument('--n-jobs', type=int, default=-1,
                   help=("Numero de processos paralelos no modo 'todos' "
                         "(default: -1 = todos os cores). Ignorado no modo "
                         "de um unico problema."))
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    # Modo 1: sem argumento posicional -> todos os problemas em paralelo.
    if args.problem is None:
        n_failed = run_all_parallel(
            problems=ALL_PROBLEMS,
            n_samples=args.n_samples,
            methods=args.methods,
            carrega_resultados=not args.force,
            n_jobs=args.n_jobs,
        )
        return 1 if n_failed > 0 else 0

    # Modo 2: um unico problema.
    try:
        process_problem(
            name=args.problem,
            n_samples=args.n_samples,
            methods=args.methods,
            carrega_resultados=not args.force,
        )
    except Exception as e:
        print(f'ERRO: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
