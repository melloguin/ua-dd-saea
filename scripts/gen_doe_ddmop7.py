# -*- coding: utf-8 -*-
"""gen_doe_ddmop7.py — materializa o DoE CONGELADO do DDMOP7 em parquet+sidecar.

[D102.1/REAL-2.1] O DoE do DDMOP7 NÃO é LHS: são os 30 sorteios oficiais de
`DDMOP7('init')` congelados UMA vez (2026-08-13, fila MATLAB B-21..B-25) — o
`init` é ESTOCÁSTICO e irreproduzível, então a reprodutibilidade migra do
gerador para o ARTEFATO (arquivo congelado + sha256). A SeedSequence (D62)
fica INERTE aqui: a semente é o ÍNDICE DE BLOCO no arquivo congelado (D102.2 —
atribuição por ordem de geração: 1º sorteio = semente 0, …, 30º = semente 42).

Este script converte o CSV congelado (`%.17g`, inclui ZEROS NEGATIVOS — o bit
pattern é preservado) no MESMO contrato de artefato dos outros 27 problemas
(D63/D87: parquet float64/snappy + sidecar com hash do array decodificado),
para os `load_doe` dos dois stacks consumirem sem NENHUM caso especial.

Uso:  python scripts/gen_doe_ddmop7.py [--check] [--csv CAMINHO] [--data-root DIR]
      (--check: só confere hashes dos artefatos já materializados)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import doe, naming                      # noqa: E402
from src.atomic_io import atomic_write_text      # noqa: E402

PROBLEMA = "DDMOP7"
D, M = 17, 2
N_INIT = 11 * D - 1          # 186
MAX_FE = 31 * D - 1          # 526
SEEDS = list(range(29)) + [42]

#: Cópia versionada no repo (transporte às VMs); a MASTER vive na árvore de
#: fusão (`mestrado2/_real_experiments/data/`). NUNCA regenerar o CSV.
CSV_DEFAULT = os.path.join(ROOT, "data", "real_sources", "ddmop7",
                           "doe_ddmop7_online_30sementes.csv")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _carrega_csv(csv_path: str) -> dict[int, np.ndarray]:
    """CSV congelado → {semente: X(186×17) float64}, ordem por `ponto`.

    Zeros NEGATIVOS do texto (`-0`) viram -0.0 no float64 — bit pattern
    preservado; o hash do artefato é determinístico a partir do texto."""
    A = np.genfromtxt(csv_path, delimiter=",", names=True)
    blocos: dict[int, np.ndarray] = {}
    sementes = A["semente"].astype(int)
    pontos = A["ponto"].astype(int)
    cols_x = [f"x{i}" for i in range(1, D + 1)]
    X_all = np.stack([A[c] for c in cols_x], axis=1).astype(np.float64)
    for s in sorted(set(sementes.tolist())):
        m = sementes == s
        ordem = np.argsort(pontos[m], kind="stable")
        blocos[int(s)] = X_all[m][ordem]
    return blocos


def gen_one(semente: int, X: np.ndarray, *, csv_sha: str,
            data_root: str, force: bool = False) -> dict:
    cols = [f"x{i}" for i in range(D)]
    path = naming.doe_path(PROBLEMA, semente, data_root)
    mpath = naming.doe_manifest_path(PROBLEMA, semente, data_root)

    if X.shape != (N_INIT, D):
        raise RuntimeError(f"semente {semente}: bloco {X.shape} != "
                           f"({N_INIT},{D}) — pára-e-loga (D81).")
    if not (np.all(X >= -1.0) and np.all(X <= 1.0)):
        raise RuntimeError(f"semente {semente}: pontos fora de [-1,1] — D81.")

    if not force and os.path.exists(path) and os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            side = json.load(fh)
        back = doe._read_matrix_parquet(path, cols)
        if doe.decoded_hash(back) == side.get("doe_hash") == doe.decoded_hash(X):
            side["path"], side["skipped"] = path, True
            return side

    os.makedirs(os.path.dirname(path), exist_ok=True)
    doe._write_matrix_parquet(path, X, cols)
    back = doe._read_matrix_parquet(path, cols)
    h_mem, h_disk = doe.decoded_hash(X), doe.decoded_hash(back)
    if h_mem != h_disk:
        raise RuntimeError(f"{PROBLEMA}/{semente}: round-trip NÃO bit-exato "
                           f"({h_mem} != {h_disk}) — D81.")
    meta = {
        "artifact": "doe",
        "decision": "D102.1/REAL-2.1 (sorteios congelados do DDMOP7('init') "
                    "— NÃO LHS; irreproduzível por construção)",
        "problema": PROBLEMA, "problema_id": doe.PROBLEMA_ID[PROBLEMA],
        "semente": int(semente), "D": D, "M": M,
        "n_init": N_INIT, "maxfe": MAX_FE,
        "bounds": {"xl": [-1.0] * D, "xu": [1.0] * D},
        "sampler": "frozen-ddmop7-init",
        "seed_formula": "INERTE (D102.2): semente = índice de bloco no CSV "
                        "congelado, por ordem de geração dos sorteios",
        "fonte_csv": os.path.basename(CSV_DEFAULT),
        "fonte_csv_sha256": csv_sha,
        "columns": cols, "dtype": "float64", "row_major": True,
        "doe_hash": h_mem, "n_rows": int(X.shape[0]), "n_cols": int(X.shape[1]),
        "numpy_version": np.__version__,
        "created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    atomic_write_text(mpath, json.dumps(meta, ensure_ascii=False, indent=2))
    out = dict(meta)
    out["path"], out["skipped"] = path, False
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--data-root", default=os.path.join(ROOT, "data"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    csv_sha = _sha256_file(a.csv)
    blocos = _carrega_csv(a.csv)
    if sorted(blocos) != sorted(SEEDS):
        print(f"FALHA: sementes do CSV = {sorted(blocos)} != {sorted(SEEDS)}")
        return 1

    fails = 0
    for s in SEEDS:
        cols = [f"x{i}" for i in range(D)]
        if a.check:
            mpath = naming.doe_manifest_path(PROBLEMA, s, a.data_root)
            path = naming.doe_path(PROBLEMA, s, a.data_root)
            try:
                with open(mpath, encoding="utf-8") as fh:
                    side = json.load(fh)
                back = doe._read_matrix_parquet(path, cols)
                ok = (doe.decoded_hash(back) == side["doe_hash"]
                      == doe.decoded_hash(blocos[s])
                      and side["fonte_csv_sha256"] == csv_sha)
            except Exception as e:                       # noqa: BLE001
                ok = False
                print(f"  s{s}: {type(e).__name__}: {e}")
            print(f"  {PROBLEMA} s{s:2d}  {'OK' if ok else 'HASH DIVERGE!'}")
            fails += 0 if ok else 1
        else:
            r = gen_one(s, blocos[s], csv_sha=csv_sha,
                        data_root=a.data_root, force=a.force)
            print(f"  {PROBLEMA} s{s:2d}  "
                  f"{'ja existia (integro)' if r['skipped'] else 'gravado'}  "
                  f"{r['doe_hash'][:16]}")
    if not a.check:
        print(f"\n{len(SEEDS)} DoEs congelados em "
              f"{os.path.join(a.data_root, 'doe', PROBLEMA)} "
              f"(fonte sha256 {csv_sha[:16]}…)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
