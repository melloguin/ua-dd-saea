"""Gerador dos artefatos de inicialização compartilhados (D87/D88/D90/D91).

Este módulo produz os **dados que TODOS os configs carregam** — nunca regeneram
(D88). São dois artefatos, ambos **únicos por `(problema, semente[, tier, dist])`**
e **SEM `alg_id`** (invariante de inicialização unificada, D88):

  1. **DoE online** (§5.2/D87): `11D−1 × D` por **LHS-maximin PRÓPRIO** —
     `data/doe/{problema}/doe_{problema}_{semente}.parquet` (colunas `x0…x{D−1}`).
  2. **Dataset offline** (§7·§9/D90): `31D−1 × (D+M)` (X e F) —
     `data/datasets/{problema}/ds_{problema}_{semente}[_{tier}_{dist}].parquet`
     (colunas `x0…x{D−1}, f0…f{M−1}`); o F sai do `src/problems.py` canônico.

**Por que rotina própria de LHS-maximin (D87).** Nenhuma lib satisfaz os DOIS
requisitos "maximin" + "100% sobre um `Generator` (reprodutível, imune a versão)":
o `scipy.stats.qmc.LatinHypercube` aceita o `Generator` mas não tem criterion
maximin; o `pyDOE` tem maximin mas usa o RNG global. Fazemos ~20 linhas: gerar
`K` candidatos LHS sobre `np.random.Generator(PCG64(SeedSequence(...)))` e escolher
o de **maior distância mínima entre pontos** (empate → menor índice; `K` = 100,
fixado no F0). O `Generator`/`PCG64` do numpy tem stream **bit-estável entre
versões** → reprodutibilidade garantida pela única coisa que importa: a sequência
de sorteios.

**Hash (D87).** O SHA256 do manifesto é sobre o **ARRAY DECODIFICADO** — os
`float64` que cada lado enxerga —, `np.ascontiguousarray(A, '<f8').tobytes()`
(row-major), **não** sobre os bytes do arquivo (writers distintos → arquivos
distintos p/ os mesmos valores). É o que o teste bit-a-bit Python↔MATLAB compara.

**Derivação da semente (harmoniza D87 com D90 — SEM `alg_id`, D88).**
  - DoE online:      `SeedSequence((semente, problema_id))`
  - Dataset offline: `SeedSequence((semente, problema_id, tier_id, dist_id))`   [verbatim D90]
O `problema_id` é o índice 0-based na lista canônica `experiment.ALL_PROBLEMS`
(= ordem do §4). Os mapas `problema_id / tier_id / dist_id` e a fórmula são
publicados em `artifacts/seeds.json` (D91) — canônicos por construção (um único
gerador; ninguém re-deriva o DoE, só CARREGA).

Escritor **único = pyarrow** (o MATLAB só LÊ, com `parquetread`). float64 = parquet
`DOUBLE` = IEEE 754 binary64 exato; compressão `snappy` (lossless, lida pelo MATLAB).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np

from src import naming
from src.atomic_io import atomic_path, atomic_write_text
from src.experiment import ALL_PROBLEMS, _instantiate_problem

# ── Constantes canônicas (F0-02) ────────────────────────────────────────────

#: K candidatos do LHS-maximin (D87 — "fixado no F0, default 100").
K_MAXIMIN = 100

#: Versão da SPEC / do gerador — gravadas no sidecar p/ auditoria.
SPEC_VERSION = "5.2"
GENERATOR_VERSION = 1

#: problema_id (D90/D91): índice 0-based na lista canônica (ordem do §4).
PROBLEMA_ID: dict[str, int] = {name: i for i, name in enumerate(ALL_PROBLEMS)}

#: tier_id / dist_id do dataset offline (D90). small/lhs = offline PRINCIPAL.
TIER_ID: dict[str, int] = {"small": 0, "medium": 1, "big": 2}
DIST_ID: dict[str, int] = {"lhs": 0, "mvns": 1}

#: Tamanho do dataset offline por tier (§7/§9/D38). `small` = 31D−1 (todos);
#: `medium` = 2000 (todos); `big` = 50000 (c311-only; LHS SIMPLES — D87/D90).
_TIER_MEDIUM_N = 2000
_TIER_BIG_N = 50000

#: MVNS (D67): amostrar em [0,1]^D, μ=0,3·𝟙, Σ=diag(0,1); clip [0,1]; mapear nativo.
_MVNS_MU = 0.3
_MVNS_VAR = 0.1


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Núcleo numérico (puro, sem IO) ─────────────────────────────────────────

def decoded_hash(A: np.ndarray) -> str:
    """SHA256 do array DECODIFICADO (D87): `<f8` row-major, exatamente o que
    cada stack enxerga. Independe do writer/codec do parquet."""
    b = np.ascontiguousarray(A, dtype="<f8").tobytes()
    return hashlib.sha256(b).hexdigest()


def _one_lhs(rng: np.random.Generator, n: int, D: int) -> np.ndarray:
    """Um design LHS em [0,1]^D. Ordem de sorteio CANÔNICA e fixa (define o
    stream): por coluna `j`, primeiro `permutation(n)`, depois `random(n)`.
    Ponto da célula `i` da coluna `j`: `(perm[i] + U) / n`."""
    U = np.empty((n, D), dtype=np.float64)
    for j in range(D):
        perm = rng.permutation(n)
        U[:, j] = (perm + rng.random(n)) / n
    return U


def _min_pairwise_sq(U: np.ndarray) -> float:
    """Menor distância euclidiana QUADRADA entre linhas (critério maximin, em
    [0,1]^D). Quadrada = monotônica com a distância → mesmo argmax, sem `sqrt`.

    Usa `scipy.spatial.distance.pdist(U,'sqeuclidean')`: rotina C **sequencial**
    (`Σ_d (a_d−b_d)²` por par, em laço fixo) — SEM `matmul`/BLAS. Isto é o que
    torna a SELEÇÃO do maximin determinística e estável entre versões (o D87 pede
    "imune a versão de biblioteca"): a expansão `‖a‖²+‖b‖²−2a·b` (GEMM) e até o
    `ndarray.sum` (soma *pairwise* do numpy) têm ordem de soma variável e podem
    trocar o candidato vencedor num empate de ULP. Só é chamada no caminho
    maximin (n ≤ 2000; o tier `big`=50k usa LHS simples, sem distância)."""
    from scipy.spatial.distance import pdist
    return float(pdist(U, "sqeuclidean").min())


def lhs_maximin(rng: np.random.Generator, n: int, D: int,
                K: int = K_MAXIMIN) -> np.ndarray:
    """LHS-maximin (D87): `K` candidatos sobre o `rng`, retorna o de maior
    distância mínima (empate → menor índice, pois `>` estrito preserva o 1º)."""
    best_U = None
    best_d = -np.inf
    for _ in range(K):
        cand = _one_lhs(rng, n, D)
        d = _min_pairwise_sq(cand)
        if d > best_d:
            best_d = d
            best_U = cand
    return best_U


def lhs_simple(rng: np.random.Generator, n: int, D: int) -> np.ndarray:
    """LHS simples (1 design) — tier `big` do sweep (50k): maximin inviável (D87/D90)."""
    return _one_lhs(rng, n, D)


def mvns_sample(rng: np.random.Generator, n: int, D: int) -> np.ndarray:
    """MVNS (D67): N(μ=0,3·𝟙, Σ=diag(0,1)) em [0,1]^D, clip a [0,1]. Σ diagonal
    ⇒ `μ + √var·standard_normal` (bit-estável; evita a cholesky do
    `multivariate_normal`). O mapeamento a nativo é feito por `_to_native`."""
    U = _MVNS_MU + np.sqrt(_MVNS_VAR) * rng.standard_normal((n, D))
    return np.clip(U, 0.0, 1.0)


def _to_native(U: np.ndarray, xl: np.ndarray, xu: np.ndarray) -> np.ndarray:
    """Bijeção linear [0,1]^D → bounds nativos (§5.5): `xl + U·(xu−xl)`."""
    return xl + U * (xu - xl)


# ── Semeadura (D87/D90/D91 — SEM alg_id) ────────────────────────────────────

def _ss_online(semente: int, problema_id: int) -> np.random.SeedSequence:
    return np.random.SeedSequence((int(semente), int(problema_id)))


def _ss_offline(semente: int, problema_id: int,
                tier_id: int, dist_id: int) -> np.random.SeedSequence:
    return np.random.SeedSequence(
        (int(semente), int(problema_id), int(tier_id), int(dist_id)))


def _gen(ss: np.random.SeedSequence) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(ss))


# ── DoE online (11D−1 × D) ──────────────────────────────────────────────────

def generate_doe(problema: str, semente: int, *, K: int = K_MAXIMIN):
    """Gera (em memória) o DoE online de `(problema, semente)`. Retorna
    `(X_nativo, meta)`. Puro — sem IO."""
    if problema not in PROBLEMA_ID:
        raise ValueError(f"Problema desconhecido: {problema!r}")
    prob = _instantiate_problem(problema)
    D = int(prob.n_var)
    n = 11 * D - 1
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)
    pid = PROBLEMA_ID[problema]
    rng = _gen(_ss_online(semente, pid))
    U = lhs_maximin(rng, n, D, K)
    X = _to_native(U, xl, xu)
    meta = {
        "artifact": "doe", "spec_version": SPEC_VERSION, "decision": "D87/D88",
        "generator_version": GENERATOR_VERSION,
        "problema": problema, "problema_id": pid, "semente": int(semente),
        "D": D, "n_init": n, "maxfe": 31 * D - 1,
        "bounds": {"xl": xl.tolist(), "xu": xu.tolist()},
        "sampler": "lhs-maximin", "K": int(K),
        "seed_formula": "SeedSequence((semente, problema_id))",
        "seed_tuple": [int(semente), pid],
        "columns": [f"x{i}" for i in range(D)],
        "dtype": "float64", "row_major": True,
        "numpy_version": np.__version__, "bitgen": "PCG64",
    }
    return X, meta


def _write_matrix_parquet(path: str, A: np.ndarray, columns: list[str]) -> None:
    """Escreve `A` (n×len(columns)) como parquet float64/DOUBLE, atomicamente.
    Escritor ÚNICO = pyarrow; `snappy` (lossless; MATLAB `parquetread` lê)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    A = np.ascontiguousarray(A, dtype=np.float64)
    table = pa.table({c: pa.array(A[:, j], type=pa.float64())
                      for j, c in enumerate(columns)})
    # preserva a ordem das colunas (dict do py3.7+ é ordenado)
    table = table.select(columns)
    with atomic_path(path) as tmp:
        pq.write_table(table, tmp, compression="snappy", version="2.6")


def _read_matrix_parquet(path: str, columns: list[str]) -> np.ndarray:
    """Lê o parquet e reconstrói o array (n×len(columns)) na ORDEM de `columns`,
    float64 — para re-hash de verificação (round-trip bit-a-bit)."""
    import pyarrow.parquet as pq
    t = pq.read_table(path, columns=columns)
    cols = [np.asarray(t.column(c).to_numpy(zero_copy_only=False), dtype=np.float64)
            for c in columns]
    return np.ascontiguousarray(np.column_stack(cols), dtype=np.float64)


def ensure_doe(problema: str, semente: int, *, K: int = K_MAXIMIN,
               data_root: str = naming.DEFAULT_DATA_ROOT,
               force: bool = False) -> dict:
    """Get-or-create do DoE. Se já existe e o hash do parquet bate com o sidecar,
    PULA (idempotente). Retorna o dict do sidecar (com `path` e `doe_hash`)."""
    path = naming.doe_path(problema, semente, data_root)
    mpath = naming.doe_manifest_path(problema, semente, data_root)
    cols = [f"x{i}" for i in range(int(_instantiate_problem(problema).n_var))]

    if not force and os.path.exists(path) and os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as _mf:
            side = json.load(_mf)
        back = _read_matrix_parquet(path, cols)
        if decoded_hash(back) == side.get("doe_hash"):
            side["path"] = path
            side["skipped"] = True
            return side  # já pronto e íntegro

    X, meta = generate_doe(problema, semente, K=K)
    _write_matrix_parquet(path, X, meta["columns"])
    # verificação de round-trip: o que foi escrito lê de volta idêntico.
    back = _read_matrix_parquet(path, meta["columns"])
    h_mem = decoded_hash(X)
    h_disk = decoded_hash(back)
    if h_mem != h_disk:
        raise RuntimeError(
            f"DoE {problema}/{semente}: round-trip parquet NÃO bit-exato "
            f"({h_mem} != {h_disk}) — pára-e-loga (D81).")
    meta["doe_hash"] = h_mem
    meta["n_rows"], meta["n_cols"] = X.shape
    meta["created_at"] = _utcnow_iso()
    atomic_write_text(mpath, json.dumps(meta, ensure_ascii=False, indent=2))
    out = dict(meta)
    out["path"] = path
    out["skipped"] = False
    return out


# ── Dataset offline (n_tier × (D+M)) ────────────────────────────────────────

def _tier_n(tier: str, D: int) -> int:
    if tier == "small":
        return 31 * D - 1
    if tier == "medium":
        return _TIER_MEDIUM_N
    if tier == "big":
        return _TIER_BIG_N
    raise ValueError(f"tier inválido: {tier!r} (esperado {list(TIER_ID)})")


def generate_dataset(problema: str, semente: int, *,
                     tier: str = "small", dist: str = "lhs",
                     K: int = K_MAXIMIN):
    """Gera (em memória) o dataset offline `(problema, semente, tier, dist)`.
    Retorna `(X_nativo, F, meta)`. O F sai do `problems.py` canônico (D90)."""
    if problema not in PROBLEMA_ID:
        raise ValueError(f"Problema desconhecido: {problema!r}")
    if tier not in TIER_ID:
        raise ValueError(f"tier inválido: {tier!r}")
    if dist not in DIST_ID:
        raise ValueError(f"dist inválido: {dist!r}")
    prob = _instantiate_problem(problema)
    D, M = int(prob.n_var), int(prob.n_obj)
    xl = np.asarray(prob.xl, dtype=np.float64)
    xu = np.asarray(prob.xu, dtype=np.float64)
    pid = PROBLEMA_ID[problema]
    n = _tier_n(tier, D)
    rng = _gen(_ss_offline(semente, pid, TIER_ID[tier], DIST_ID[dist]))

    if dist == "mvns":
        U = mvns_sample(rng, n, D)
        sampler = "mvns"
    elif tier == "big":
        U = lhs_simple(rng, n, D)          # maximin inviável em 50k (D87/D90)
        sampler = "lhs-simple"
    else:
        U = lhs_maximin(rng, n, D, K)
        sampler = "lhs-maximin"
    X = _to_native(U, xl, xu)

    from src import problems as _P
    F = np.ascontiguousarray(_P.evaluate_problem(prob, X), dtype=np.float64)
    if F.shape != (n, M):
        raise RuntimeError(f"F shape {F.shape} != {(n, M)} p/ {problema}")

    cols = [f"x{i}" for i in range(D)] + [f"f{i}" for i in range(M)]
    meta = {
        "artifact": "dataset", "spec_version": SPEC_VERSION, "decision": "D90",
        "generator_version": GENERATOR_VERSION,
        "problema": problema, "problema_id": pid, "semente": int(semente),
        "tier": tier, "dist": dist,
        "tier_id": TIER_ID[tier], "dist_id": DIST_ID[dist],
        "D": D, "M": M, "n": n,
        "bounds": {"xl": xl.tolist(), "xu": xu.tolist()},
        "sampler": sampler, "K": int(K) if sampler == "lhs-maximin" else None,
        "seed_formula": "SeedSequence((semente, problema_id, tier_id, dist_id))",
        "seed_tuple": [int(semente), pid, TIER_ID[tier], DIST_ID[dist]],
        "columns": cols, "dtype": "float64", "row_major": True,
        "numpy_version": np.__version__, "bitgen": "PCG64",
    }
    return X, F, meta


def ensure_dataset(problema: str, semente: int, *,
                   tier: str = "small", dist: str = "lhs",
                   K: int = K_MAXIMIN,
                   data_root: str = naming.DEFAULT_DATA_ROOT,
                   force: bool = False) -> dict:
    """Get-or-create do dataset offline. small/lhs = offline PRINCIPAL (nome sem
    sufixo). Idempotente por hash. Retorna o sidecar (`path`, hashes)."""
    is_main = (tier == "small" and dist == "lhs")
    t = None if is_main else tier
    d = None if is_main else dist
    path = naming.dataset_path(problema, semente, t, d, data_root)
    mpath = naming.dataset_manifest_path(problema, semente, t, d, data_root)

    prob = _instantiate_problem(problema)
    D, M = int(prob.n_var), int(prob.n_obj)
    cols = [f"x{i}" for i in range(D)] + [f"f{i}" for i in range(M)]

    if not force and os.path.exists(path) and os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as _mf:
            side = json.load(_mf)
        back = _read_matrix_parquet(path, cols)
        if decoded_hash(back) == side.get("dataset_hash"):
            side["path"] = path
            side["skipped"] = True
            return side

    X, F, meta = generate_dataset(problema, semente, tier=tier, dist=dist, K=K)
    XF = np.ascontiguousarray(np.column_stack([X, F]), dtype=np.float64)
    _write_matrix_parquet(path, XF, meta["columns"])
    back = _read_matrix_parquet(path, meta["columns"])
    if decoded_hash(XF) != decoded_hash(back):
        raise RuntimeError(
            f"Dataset {problema}/{semente} ({tier}/{dist}): round-trip NÃO "
            f"bit-exato — pára-e-loga (D81).")
    meta["x_hash"] = decoded_hash(X)
    meta["f_hash"] = decoded_hash(F)
    meta["dataset_hash"] = decoded_hash(XF)
    meta["n_rows"], meta["n_cols"] = XF.shape
    meta["created_at"] = _utcnow_iso()
    atomic_write_text(mpath, json.dumps(meta, ensure_ascii=False, indent=2))
    out = dict(meta)
    out["path"] = path
    out["skipped"] = False
    return out


# ── Materialização em lote (CLI) ────────────────────────────────────────────

# 30 sementes {0..28} ∪ {42} (§5.3).
DEFAULT_SEEDS: list[int] = list(range(29)) + [42]


def materialize_all(*, kind: str = "both",
                    problemas: list[str] | None = None,
                    seeds: list[int] | None = None,
                    data_root: str = naming.DEFAULT_DATA_ROOT,
                    force: bool = False,
                    verbose: bool = True) -> dict:
    """Materializa o DoE online e/ou o dataset offline PRINCIPAL (small/lhs)
    p/ o grid `problemas × seeds`. `kind ∈ {doe, dataset, both}`."""
    problemas = problemas or list(ALL_PROBLEMS)
    seeds = seeds if seeds is not None else DEFAULT_SEEDS
    n_doe = n_ds = skip = 0
    for prob in problemas:
        for s in seeds:
            if kind in ("doe", "both"):
                r = ensure_doe(prob, s, data_root=data_root, force=force)
                n_doe += 1
                skip += int(r.get("skipped", False))
            if kind in ("dataset", "both"):
                r = ensure_dataset(prob, s, data_root=data_root, force=force)
                n_ds += 1
                skip += int(r.get("skipped", False))
        if verbose:
            print(f"  [{prob}] pronto ({len(seeds)} sementes)", flush=True)
    summary = {"doe": n_doe, "dataset": n_ds, "skipped": skip,
               "problemas": len(problemas), "seeds": len(seeds)}
    if verbose:
        print(f"[materialize_all] {summary}", flush=True)
    return summary


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Gera DoE (D87) + dataset offline (D90).")
    ap.add_argument("--kind", choices=["doe", "dataset", "both"], default="both")
    ap.add_argument("--problems", nargs="+", default=None)
    ap.add_argument("--seeds", nargs="+", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--data-root", default=naming.DEFAULT_DATA_ROOT)
    a = ap.parse_args(argv)
    materialize_all(kind=a.kind, problemas=a.problems, seeds=a.seeds,
                    data_root=a.data_root, force=a.force)


if __name__ == "__main__":
    _main()
