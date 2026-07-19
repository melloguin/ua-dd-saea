# -*- coding: utf-8 -*-
"""gen_sonda.py — gera o artefato da SONDA canônica (DI-09 / SPEC §17.2.2, v5.2.1).

Os 2000 pontos FIXOS por problema que TODOS os algoritmos com surrogate predizem
(regime='sonda' na ③) — a régua única da comparação entre modelos. Gerado UMA vez;
os instrumentadores CARREGAM o parquet e conferem o hash do sidecar (disciplina
D63/D87). O `f` verdadeiro é pré-computado aqui (float64, `src/problems.py`
canônico) — ZERO FE do orçamento (exceção contábil §11/DI-08).

Definição EXATA (CONTRATO_DE_DADOS §3.1): S=2000 pontos Sobol EMBARALHADO,
`scipy.stats.qmc.Sobol(d=D, scramble=True, seed=SeedSequence((4242, problema_id))
truncada a 32 bits)`, re-escalados aos bounds NATIVOS. `problema_id` = índice
0-based em `experiment.ALL_PROBLEMS` (a MESMA convenção do DoE/D91).

Uso:  python scripts/gen_sonda.py [--check]   (--check: só verifica hashes)
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.experiment import ALL_PROBLEMS, _instantiate_problem  # noqa: E402

S = 2000            #: nº de pontos (decisão do autor, DI-09: S=2000, k=2)
BASE_SEED = 4242    #: base da SeedSequence da sonda (≠ DoE/dataset — sem colisão)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'data', 'sonda')


def _decoded_hash(arr: np.ndarray) -> str:
    """sha256 dos bytes float64 row-major — a MESMA convenção do DoE (D87)."""
    return hashlib.sha256(np.ascontiguousarray(arr, dtype=np.float64).tobytes()).hexdigest()


def gen_one(problema: str, pid: int):
    from scipy.stats import qmc
    prob = _instantiate_problem(problema)
    D, M = prob.n_var, prob.n_obj
    lower, upper = np.asarray(prob.xl, float), np.asarray(prob.xu, float)
    seed = int(np.random.SeedSequence((BASE_SEED, pid)).generate_state(1, dtype=np.uint64)[0]) & 0xFFFFFFFF
    eng = qmc.Sobol(d=D, scramble=True, seed=seed)
    U = eng.random(S)                       # [0,1]^D, ordem = ordem de geração
    X = lower + U * (upper - lower)         # bounds nativos
    F = prob.evaluate(X, return_values_of=["F"])  # f verdadeiro, float64
    assert X.shape == (S, D) and F.shape == (S, M)
    assert np.all(X >= lower - 1e-12) and np.all(X <= upper + 1e-12)
    assert np.all(np.isfinite(F)), f"{problema}: F não-finito na sonda"
    return X, F, D, M, seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    import pandas as pd
    os.makedirs(OUT, exist_ok=True)
    fails = 0
    for pid, problema in enumerate(ALL_PROBLEMS):
        X, F, D, M, seed = gen_one(problema, pid)
        xh, fh = _decoded_hash(X), _decoded_hash(F)
        pdir = os.path.join(OUT)
        fpq = os.path.join(pdir, f'sonda_{problema}.parquet')
        fmn = os.path.join(pdir, f'sonda_{problema}.manifest.json')
        if args.check:
            man = json.load(open(fmn))
            ok = (man['x_hash'] == xh and man['f_hash'] == fh)
            print(f"  {problema:12} {'OK' if ok else 'HASH DIVERGE!'}")
            fails += 0 if ok else 1
            continue
        df = pd.DataFrame({'sonda_id': np.arange(S, dtype=np.int32)})
        for j in range(D):
            df[f'x{j}'] = X[:, j]
        for j in range(M):
            df[f'f{j}'] = F[:, j]
        df.to_parquet(fpq, index=False)     # float64 — o GABARITO não perde precisão
        json.dump({'schema_version': 1, 'problema': problema, 'problema_id': pid,
                   'S': S, 'D': D, 'M': M, 'base_seed': BASE_SEED,
                   'sobol_seed_32': seed, 'scramble': True,
                   'x_hash': xh, 'f_hash': fh,
                   'convencao': 'sha256 dos bytes float64 row-major (D87); '
                                'ordem das linhas = ordem de geração Sobol (join por posição)'},
                  open(fmn, 'w'), indent=1)
        print(f"  {problema:12} D={D:2d} M={M} seed32={seed:>10} x_hash={xh[:12]}…")
    if args.check and fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
