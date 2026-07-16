#!/usr/bin/env python3
"""gen_fidelity_doe.py — gera o DoE 11D-1 de uma instância de FIDELIDADE (D97).

As instâncias de `src.experiment.FIDELITY_PROBLEMS` são NÃO-canônicas (fora dos 25
do A2 e do grid) — existem só para o autor reproduzir a config EXATA do paper de um
algoritmo e comparar com a âncora (Anexo J). Como estão FORA de `ALL_PROBLEMS`
(logo de `doe.PROBLEMA_ID`, que os gates F0 exigem == seeds.json), o `doe.ensure_doe`
canônico as rejeita. Este script gera o artefato reusando as MESMAS primitivas do
`src.doe` (LHS-maximin D87, `_to_native`, `decoded_hash`, `_write_matrix_parquet`,
round-trip bit-a-bit) mas por um caminho paralelo, com um `problema_id` de fidelidade
distinto (>=1000, fora dos ids canônicos 0..24) para descolar a semente sem colidir.

Uso:  python3 scripts/gen_fidelity_doe.py [NOME ...] [--semente N] [--force]
      (sem NOME = todas as de FIDELITY_PROBLEMS; default semente 0)

O run MATLAB do algoritmo consome este DoE por `load_doe(NOME, semente, D, 'data')`
(o `_instantiate_problem` já resolve NOME via FIDELITY_PROBLEMS) e grava em exp=main
(`exp_main_<alg>_<NOME>_<semente>__*`) — filtre NOME da análise canônica.
"""
import argparse, os, sys, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
from src import doe, naming
from src.experiment import FIDELITY_PROBLEMS, _instantiate_problem

#: offset dos ids de fidelidade (fora dos canônicos 0..24; sem pareamento cross-stack
#: — só o algoritmo dono usa este DoE, então o id é livre, apenas reprodutível).
_FID_PID_BASE = 1000
FIDELITY_PID = {name: _FID_PID_BASE + i for i, name in enumerate(sorted(FIDELITY_PROBLEMS))}


def gen_one(nome: str, semente: int, force: bool = False) -> dict:
    if nome not in FIDELITY_PROBLEMS:
        raise ValueError(f"{nome!r} não está em FIDELITY_PROBLEMS ({list(FIDELITY_PROBLEMS)})")
    prob = _instantiate_problem(nome)
    D, M = int(prob.n_var), int(prob.n_obj)
    n = 11 * D - 1
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)
    pid = FIDELITY_PID[nome]
    cols = [f"x{i}" for i in range(D)]

    path = naming.doe_path(nome, semente, os.path.join(ROOT, "data"))
    mpath = naming.doe_manifest_path(nome, semente, os.path.join(ROOT, "data"))
    if not force and os.path.exists(path) and os.path.exists(mpath):
        side = json.load(open(mpath, encoding="utf-8"))
        back = doe._read_matrix_parquet(path, cols)
        if doe.decoded_hash(back) == side.get("doe_hash"):
            side["path"], side["skipped"] = path, True
            return side

    rng = doe._gen(np.random.SeedSequence((int(semente), int(pid))))
    U = doe.lhs_maximin(rng, n, D, doe.K_MAXIMIN)
    X = doe._to_native(U, xl, xu)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doe._write_matrix_parquet(path, X, cols)
    back = doe._read_matrix_parquet(path, cols)
    h_mem, h_disk = doe.decoded_hash(X), doe.decoded_hash(back)
    if h_mem != h_disk:
        raise RuntimeError(f"{nome}/{semente}: round-trip NÃO bit-exato ({h_mem} != {h_disk}) — D81")

    cls, kw = FIDELITY_PROBLEMS[nome]
    meta = {
        "artifact": "doe", "decision": "D87/D88 (fidelidade NÃO-canônica, D97)",
        "problema": nome, "problema_id": pid, "semente": int(semente),
        "D": D, "M": M, "n_init": n, "maxfe": 31 * D - 1,
        "bounds": {"xl": xl.tolist(), "xu": xu.tolist()},
        "sampler": "lhs-maximin", "K": int(doe.K_MAXIMIN),
        "seed_formula": "SeedSequence((semente, FIDELITY_PID)) [id>=1000, fora de PROBLEMA_ID]",
        "seed_tuple": [int(semente), int(pid)],
        "columns": cols, "dtype": "float64", "row_major": True,
        "doe_hash": h_mem, "n_rows": int(X.shape[0]), "n_cols": int(X.shape[1]),
        "numpy_version": np.__version__, "bitgen": "PCG64",
        "fidelity_class": cls, "fidelity_kwargs": kw,
        "nota": f"NÃO-canônico: {cls}({kw}) — config de paper; fora do A2/grid; só p/ fidelidade (D97).",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    meta["path"], meta["skipped"] = path, False
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nomes", nargs="*", help="instâncias (default: todas de FIDELITY_PROBLEMS)")
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    nomes = a.nomes or list(FIDELITY_PROBLEMS)
    for nome in nomes:
        r = gen_one(nome, a.semente, force=a.force)
        flag = "skip" if r.get("skipped") else "novo"
        print(f"[{flag}] {nome} s{a.semente}: n={r['n_init']} D={r['D']} M={r['M']} "
              f"hash={r['doe_hash'][:16]}… -> {os.path.relpath(r['path'], ROOT)}")


if __name__ == "__main__":
    main()
