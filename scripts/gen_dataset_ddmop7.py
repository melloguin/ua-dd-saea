# -*- coding: utf-8 -*-
"""gen_dataset_ddmop7.py — Processo A: o DATASET OFFLINE do DDMOP7 (D90/D102).

[T15.7 §3] Os runners offline (b5m, b5r, moead_media, e103) consomem
`data/datasets/DDMOP7/ds_DDMOP7_{s}.parquet` (X+F, contrato D90) pelos
`load_dataset` oficiais — com o artefato no lugar, ZERO mudança nos runners.
Este script MATERIALIZA o artefato:

  1. X vem CONGELADO de `data/real_sources/ddmop7/
     dataset_ddmop7_offline_30sementes.csv` (30 x 526 x 17, sorteios oficiais
     de DDMOP7('init') gravados com %.17g — zeros NEGATIVOS preservados;
     sha256 do arquivo conferido). A semente e o INDICE DE BLOCO no CSV
     (D102.2 — a SeedSequence fica INERTE, como no DoE online);
  2. F sai do DDMOP7.p oficial via `src.ddmop7_bridge` (MATLAB Engine,
     fatiamento <=64 pontos/chamada) — ~6 s/ponto => ~53 min/semente.
     UM engine POR SEMENTE: 526 chamadas < teto 600 do .p; DUAS sementes no
     mesmo processo (1052) NAO cabem (D88.5);
  3. grava parquet + sidecar no MESMO contrato do `src/doe.py::ensure_dataset`
     (colunas x0..x16,f0,f1; x_hash/f_hash/dataset_hash sobre o array
     DECODIFICADO; round-trip bit-a-bit conferido).

⚠ D102.14: os F que VALEM para o estudo sao os das VMs Linux — este script
roda LA, no provisionamento. Na maquina local so se TESTA com `--limite`
(poucos pontos) em tempdir: com `--limite` o script EXIGE `--data-root`
explicito (recusa gravar artefato parcial na data/ de producao) e o sidecar
carrega `PARCIAL_LIMITE`. O motor `--engine mock` existe SO para exercitar o
arnes (sidecar leva engine='mock' + AVISO — numeros nunca vao para a tese).

CONTRATO tier/dist [decisao T desta sessao]: o sidecar declara
`tier='small'/dist='lhs'` porque esse e o SLOT do offline principal que os
dois `load_dataset` (Python e MATLAB :2870) exigem para o nome sem sufixo —
sao ids de CONTRATO, nao a proveniencia. A proveniencia REAL fica nos campos
`sampler='frozen-ddmop7-init-offline'` + `seed_formula` (INERTE) +
`fonte_csv`/`fonte_csv_sha256`, exatamente como o DoE online do DDMOP7 ja
declara `sampler='frozen-ddmop7-init'` (gen_doe_ddmop7.py).

Uso:
  python scripts/gen_dataset_ddmop7.py [--check] [--sementes 0 1 42]
      [--csv CAMINHO] [--data-root DIR] [--engine matlab|mock]
      [--problems-dir DIR] [--limite N] [--force]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import platform
import socket
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import doe, naming                      # noqa: E402
from src.atomic_io import atomic_write_text      # noqa: E402

PROBLEMA = "DDMOP7"
D, M = 17, 2
N_OFFLINE = 31 * D - 1       # 526  (= tier small; o dataset E o orcamento, D90)
P_CODE_CAP = 600             # teto interno do DDMOP7.p (D88.5)
SEEDS = list(range(29)) + [42]

#: Copia versionada no repo (transporte as VMs); a MASTER vive na arvore de
#: fusao (`mestrado2/_real_experiments/data/`). NUNCA regenerar o CSV.
CSV_DEFAULT = os.path.join(ROOT, "data", "real_sources", "ddmop7",
                           "dataset_ddmop7_offline_30sementes.csv")

#: sha256 CONGELADO do CSV (cartao T15.7 §3.2) — o gerador confere e ABORTA
#: em divergencia (arquivo trocado/corrompido nao passa despercebido).
CSV_SHA256_ESPERADO = ("03056b6eb76a5c40362547cdc0c31869"
                       "e70a11088efefefde1c46317fb2ea085")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _carrega_csv(csv_path: str) -> dict[int, np.ndarray]:
    """CSV congelado → {semente: X(526×17) float64}, ordem por `ponto`.

    Zeros NEGATIVOS do texto (`-0`) viram -0.0 no float64 — bit pattern
    preservado; o hash do artefato e deterministico a partir do texto."""
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


def _valida_bloco(semente: int, X: np.ndarray, n_esperado: int) -> None:
    if X.shape != (n_esperado, D):
        raise RuntimeError(f"semente {semente}: bloco {X.shape} != "
                           f"({n_esperado},{D}) — pára-e-loga (D81).")
    if not (np.all(X >= -1.0) and np.all(X <= 1.0)):
        raise RuntimeError(f"semente {semente}: pontos fora de [-1,1] — D81.")
    if np.unique(X, axis=0).shape[0] != X.shape[0]:
        raise RuntimeError(
            f"semente {semente}: X com linhas DUPLICADAS — duplicata no "
            f"dataset offline quebra o ajuste do surrogate (hazard L.15). "
            f"Pára-e-loga (D81).")


def _monta_motor(engine: str, semente: int, problems_dir: str | None):
    """UM motor por SEMENTE (D88.5: 526 < 600; 2 sementes nao cabem)."""
    from src import ddmop7_bridge as B
    if engine == "matlab":
        return B._MotorMatlab(problems_dir)
    if engine == "mock":
        return B._MotorMock(semente)
    raise ValueError(f"engine desconhecido: {engine!r}")


def _avalia(motor, X: np.ndarray) -> np.ndarray:
    """F = motor.avalia(X) (a ponte fatia em <=64) + guards D81."""
    if X.shape[0] > P_CODE_CAP:
        raise RuntimeError(f"{X.shape[0]} pontos > teto {P_CODE_CAP} do .p "
                           f"num processo (D88.5)")
    F = np.atleast_2d(np.asarray(motor.avalia(X), dtype=np.float64))
    if F.shape != (X.shape[0], M):
        raise RuntimeError(f"DDMOP7('value') devolveu {F.shape}, esperado "
                           f"({X.shape[0]}, {M}) — pára-e-loga (D81).")
    if not np.all(np.isfinite(F)):
        raise RuntimeError("DDMOP7('value') devolveu nao-finito — D81.")
    return F


def gen_one(semente: int, X: np.ndarray, *, csv_sha: str, data_root: str,
            engine: str = "matlab", problems_dir: str | None = None,
            limite: int | None = None, force: bool = False) -> dict:
    """Materializa `ds_DDMOP7_{semente}.parquet` + sidecar (contrato D90)."""
    _valida_bloco(semente, X, N_OFFLINE)
    if limite is not None:
        limite = int(limite)
        if not 0 < limite <= N_OFFLINE:
            raise ValueError(f"--limite {limite} fora de 1..{N_OFFLINE}")
        X = X[:limite]

    cols = [f"x{i}" for i in range(D)] + [f"f{i}" for i in range(M)]
    path = naming.dataset_path(PROBLEMA, semente, None, None, data_root)
    mpath = naming.dataset_manifest_path(PROBLEMA, semente, None, None,
                                         data_root)

    if not force and limite is None and os.path.exists(path) \
            and os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            side = json.load(fh)
        back = doe._read_matrix_parquet(path, cols)
        if (doe.decoded_hash(back) == side.get("dataset_hash")
                and doe.decoded_hash(back[:, :D]) == side.get("x_hash")
                == doe.decoded_hash(X)):
            side["path"], side["skipped"] = path, True
            return side

    t0 = time.time()
    motor = _monta_motor(engine, semente, problems_dir)
    try:
        F = _avalia(motor, X)
    finally:
        motor.encerra()                      # D86 — inclusive em falha
    wall_s = time.time() - t0

    XF = np.ascontiguousarray(np.column_stack([X, F]), dtype=np.float64)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doe._write_matrix_parquet(path, XF, cols)
    back = doe._read_matrix_parquet(path, cols)
    if doe.decoded_hash(XF) != doe.decoded_hash(back):
        raise RuntimeError(f"{PROBLEMA}/{semente}: round-trip NAO bit-exato "
                           f"— pára-e-loga (D81).")

    meta = {
        "artifact": "dataset",
        "spec_version": doe.SPEC_VERSION,
        "decision": "D90 + D102 (X congelado dos sorteios oficiais do "
                    "DDMOP7('init'); F do DDMOP7.p via MATLAB Engine — "
                    "D102.14: os F validos sao os das VMs Linux)",
        "generator_version": doe.GENERATOR_VERSION,
        "problema": PROBLEMA, "problema_id": doe.PROBLEMA_ID[PROBLEMA],
        "semente": int(semente),
        # ── slot de CONTRATO do offline principal (docstring do modulo) ──
        "tier": "small", "dist": "lhs",
        "tier_id": doe.TIER_ID["small"], "dist_id": doe.DIST_ID["lhs"],
        # ── proveniencia REAL ────────────────────────────────────────────
        "sampler": "frozen-ddmop7-init-offline",
        "seed_formula": "INERTE (D102.2): semente = indice de bloco no CSV "
                        "congelado, por ordem de geracao dos sorteios",
        "fonte_csv": os.path.basename(CSV_DEFAULT),
        "fonte_csv_sha256": csv_sha,
        "engine": engine,
        "avaliador": "DDMOP7.p oficial (D102.5)" if engine == "matlab"
                     else "MOCK — NAO e o DDMOP7.p",
        "host": socket.gethostname().split(".")[0],
        "plataforma": f"{platform.system()}-{platform.machine()}",
        "wall_clock_s": round(wall_s, 3),
        "D": D, "M": M, "n": int(X.shape[0]),
        "bounds": {"xl": [-1.0] * D, "xu": [1.0] * D},
        "columns": cols, "dtype": "float64", "row_major": True,
        "x_hash": doe.decoded_hash(np.ascontiguousarray(X, np.float64)),
        "f_hash": doe.decoded_hash(np.ascontiguousarray(F, np.float64)),
        "dataset_hash": doe.decoded_hash(XF),
        "n_rows": int(XF.shape[0]), "n_cols": int(XF.shape[1]),
        "numpy_version": np.__version__,
        "created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    if engine == "mock":
        meta["AVISO"] = ("motor MOCK — o F NAO e o DDMOP7.p; artefato serve "
                         "SO para testar o arnes, nunca para a tese")
    if limite is not None:
        meta["PARCIAL_LIMITE"] = limite
        meta["AVISO_PARCIAL"] = (f"artefato PARCIAL ({limite}/{N_OFFLINE} "
                                 f"pontos) — teste local; o artefato do "
                                 f"estudo tem {N_OFFLINE} linhas (D90)")
    atomic_write_text(mpath, json.dumps(meta, ensure_ascii=False, indent=2))
    out = dict(meta)
    out["path"], out["skipped"] = path, False
    return out


def check_one(semente: int, X: np.ndarray, *, csv_sha: str,
              data_root: str) -> bool:
    """--check: integridade do artefato ja materializado (hashes + fonte)."""
    cols = [f"x{i}" for i in range(D)] + [f"f{i}" for i in range(M)]
    path = naming.dataset_path(PROBLEMA, semente, None, None, data_root)
    mpath = naming.dataset_manifest_path(PROBLEMA, semente, None, None,
                                         data_root)
    try:
        with open(mpath, encoding="utf-8") as fh:
            side = json.load(fh)
        back = doe._read_matrix_parquet(path, cols)
        n = int(side["n"])
        ok = (back.shape[0] == n
              and doe.decoded_hash(back) == side["dataset_hash"]
              and doe.decoded_hash(
                  np.ascontiguousarray(back[:, :D])) == side["x_hash"]
              and doe.decoded_hash(
                  np.ascontiguousarray(back[:, D:])) == side["f_hash"]
              and np.array_equal(back[:, :D], X[:n])
              and side["fonte_csv_sha256"] == csv_sha)
        if side.get("engine") == "mock":
            print(f"  s{semente}: AVISO — artefato de motor MOCK")
        if side.get("PARCIAL_LIMITE") is not None:
            print(f"  s{semente}: AVISO — artefato PARCIAL "
                  f"({side['PARCIAL_LIMITE']}/{N_OFFLINE})")
        return bool(ok)
    except Exception as e:                                   # noqa: BLE001
        print(f"  s{semente}: {type(e).__name__}: {e}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--csv", default=CSV_DEFAULT)
    ap.add_argument("--data-root", default=None,
                    help="default: <repo>/data (PROIBIDO com --limite)")
    ap.add_argument("--sementes", type=int, nargs="*", default=None)
    ap.add_argument("--engine", choices=["matlab", "mock"], default="matlab")
    ap.add_argument("--problems-dir", default=None,
                    help="pasta do DDMOP7.p (default: UA_DD_SAEA_DDMOP_DIR "
                         "-> ~/DDMOP/DDMOP_Exp/Problems)")
    ap.add_argument("--limite", type=int, default=None,
                    help="avalia so os N primeiros pontos (TESTE local; "
                         "exige --data-root explicito)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.limite is not None and a.data_root is None:
        print("FALHA: --limite exige --data-root explicito (tempdir) — "
              "artefato PARCIAL nao pode cair na data/ de producao (D81).")
        return 1
    data_root = a.data_root or os.path.join(ROOT, "data")

    csv_sha = _sha256_file(a.csv)
    if os.path.abspath(a.csv) == os.path.abspath(CSV_DEFAULT) \
            and csv_sha != CSV_SHA256_ESPERADO:
        print(f"FALHA: sha256 do CSV congelado diverge do esperado\n"
              f"  medido:   {csv_sha}\n  esperado: {CSV_SHA256_ESPERADO}\n"
              f"— arquivo trocado/corrompido; pára-e-loga (D81).")
        return 1
    blocos = _carrega_csv(a.csv)
    if sorted(blocos) != sorted(SEEDS):
        print(f"FALHA: sementes do CSV = {sorted(blocos)} != {sorted(SEEDS)}")
        return 1
    sementes = a.sementes if a.sementes else SEEDS
    desconhecidas = set(sementes) - set(SEEDS)
    if desconhecidas:
        print(f"FALHA: sementes fora do estudo: {sorted(desconhecidas)}")
        return 1

    fails = 0
    for s in sementes:
        if a.check:
            ok = check_one(s, blocos[s], csv_sha=csv_sha, data_root=data_root)
            print(f"  {PROBLEMA} s{s:2d}  {'OK' if ok else 'HASH DIVERGE!'}")
            fails += 0 if ok else 1
        else:
            r = gen_one(s, blocos[s], csv_sha=csv_sha, data_root=data_root,
                        engine=a.engine, problems_dir=a.problems_dir,
                        limite=a.limite, force=a.force)
            rot = ("ja existia (integro)" if r.get("skipped")
                   else f"gravado ({r['n']} pts, {r.get('wall_clock_s', '?')} s)")
            print(f"  {PROBLEMA} s{s:2d}  {rot}  "
                  f"{r['dataset_hash'][:16]}  engine={r.get('engine')}")
    if not a.check and not fails:
        print(f"\n{len(sementes)} dataset(s) em "
              f"{os.path.join(data_root, 'datasets', PROBLEMA)} "
              f"(fonte sha256 {csv_sha[:16]}…)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
