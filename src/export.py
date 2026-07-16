"""Export §17 — as 4 camadas Parquet do run (① real, ② pop, ③ surrogate, timing).

Escreve o "filme" da execução (§17.1) no formato físico decidido (§17.2/§17.3):

- **① `__real`** — Catálogo REAL (§17.2): as soluções reais DISTINTAS (dedup por
  X, D57), fonte das métricas oficiais (§12). Uma linha por `solution_id`.
  `algoritmo, problema, semente, solution_id, x0..x{D-1}, f0..f{M-1}, fe_index, fase`.
- **② `__pop`** — Registro de POPULAÇÃO REAL / geração (§17.2, membership-only,
  D31): `algoritmo, problema, semente, geracao, solution_id` — 100% das gerações,
  `x/f` vêm do ① por join (a camada mais leve, <1 GB — §17.4).
- **③ `__surrogate`** — Tabela SURROGATE única (§17.2, schema C1/C3, D35): cada
  avaliação do modelo por `(candidato, geração)`, 100% das gerações, SEM dedup (a
  predição é datada). Schema ÚNICO com colunas opcionais (DEF-C1): o regressor
  preenche `mu_*`/`sigma_*`, o classificador `pred_classe`/`pred_score`, o híbrido
  os dois; `real_solution_id` liga ao ① quando o candidato foi avaliado. As
  colunas C3 (`espaco_modelo/transf_tipo/transf_params`) guardam cru+transformado.
- **`__timing`** — Série de tempo de fit por retreino (§17.6): `(n_acumulado,
  tempo_fit_s)` = a ⭐ curva de escalabilidade; uma linha por evento de retreino.

**Invariantes de formato (D53/D54/§17.7):**
- **float32 SEM arredondamento (D53).** Colunas numéricas em `float32` — que é
  metade dos bytes e ~7 dígitos (suficiente no benchmark determinístico). O
  `round(X,3)` foi MORTO (D53): quantizava IGD/HV, colapsava o σ 10⁻⁴–10⁻⁶ e
  colidia o dedup-por-X. Aqui `astype(np.float32)` NÃO é arredondamento decimal —
  é o cast IEEE que a decisão manda.
- **Codec zstd** (§17.2/D53): ~1,5–2× sobre o snappy default. O MATLAB grava
  `brotli` (sem zstd no R2025a) e a consolidação re-encoda — o codec é livre
  por-nó; o Python grava zstd direto.
- **salvar TUDO, sem teto (D54).** Nada é amostrado no eixo de gerações.
- **Escrita ATÔMICA** (`src/atomic_io.atomic_path`, D58): um arquivo só aparece
  inteiro; um crash deixa no máximo um `.tmp` órfão (ignorado pelo resume).
- **Run pronto = manifesto ok + camadas presentes + footers válidos** (D58) —
  `run_done` (= `manifest.is_run_done`); o despachante PULA o que já está pronto.

A nomenclatura vem toda de `src.naming` (fonte única §17.7/D55). Módulo
numpy/pyarrow-dependente (roda no env-main dentro de um run).
"""

from __future__ import annotations

import json

import numpy as np

from src import naming
from src.atomic_io import atomic_path
from src.budget import RealEval
from src.manifest import is_run_done as run_done  # D58 (skip) — re-export

#: Codec do export Python (§17.2/D53). O MATLAB grava brotli; consolidação re-encoda.
PARQUET_CODEC = "zstd"

#: Valores válidos de `fase` (①) e `pred_tipo`/`espaco_modelo` (③).
FASES = ("init", "opt")
PRED_TIPOS = ("valor", "classe", "score", "híbrido")
ESPACOS = ("transformado", "cru")


# ── Nomes de coluna (0-based — harmoniza com o DoE/dataset do F0-02) ─────────
# NB: o §17.2 escreve `x_1..x_D`/`f_1..f_M` como NOTAÇÃO matemática. O F0-02 já
# materializou o DoE/dataset compartilhados em `x0..x{D-1}, f0..f{M-1}` (0-based)
# e o MATLAB os lê assim; o export usa a MESMA convenção p/ o join com o ① ser
# trivial. O CP-init compara HASH DO ARRAY (não nomes) → indiferente ao gate.
# Trocar a convenção = editar só estas 4 funções.

def x_cols(D: int) -> list[str]:
    return [f"x{i}" for i in range(int(D))]


def f_cols(M: int) -> list[str]:
    return [f"f{i}" for i in range(int(M))]


def mu_cols(M: int) -> list[str]:
    return [f"mu_{i}" for i in range(int(M))]


def sigma_cols(M: int) -> list[str]:
    return [f"sigma_{i}" for i in range(int(M))]


# ── Schemas Arrow (autoridade do formato §17.2) ─────────────────────────────

def _pa():
    import pyarrow as pa
    return pa


def real_schema(D: int, M: int):
    """Schema da camada ① (§17.2). Todas as colunas obrigatórias (não-nulas)."""
    pa = _pa()
    fields = [
        pa.field("algoritmo", pa.string(), nullable=False),
        pa.field("problema", pa.string(), nullable=False),
        pa.field("semente", pa.int32(), nullable=False),
        pa.field("solution_id", pa.int32(), nullable=False),
    ]
    fields += [pa.field(c, pa.float32(), nullable=False) for c in x_cols(D)]
    fields += [pa.field(c, pa.float32(), nullable=False) for c in f_cols(M)]
    fields += [
        pa.field("fe_index", pa.int32(), nullable=False),
        pa.field("fase", pa.string(), nullable=False),
    ]
    return pa.schema(fields)


def pop_schema():
    """Schema da camada ② (§17.2, membership-only, D31)."""
    pa = _pa()
    return pa.schema([
        pa.field("algoritmo", pa.string(), nullable=False),
        pa.field("problema", pa.string(), nullable=False),
        pa.field("semente", pa.int32(), nullable=False),
        pa.field("geracao", pa.int32(), nullable=False),
        pa.field("solution_id", pa.int32(), nullable=False),
    ])


def surrogate_schema(D: int, M: int):
    """Schema da camada ③ — base ÚNICA com colunas opcionais (DEF-C1/C3, §17.2)."""
    pa = _pa()
    fields = [
        pa.field("algoritmo", pa.string(), nullable=False),
        pa.field("problema", pa.string(), nullable=False),
        pa.field("semente", pa.int32(), nullable=False),
        pa.field("regime", pa.string(), nullable=False),
        pa.field("geracao", pa.int32(), nullable=False),
    ]
    fields += [pa.field(c, pa.float32(), nullable=False) for c in x_cols(D)]
    # liga ao ① quando o candidato foi avaliado (senão NULL) — §17.2.
    fields += [pa.field("real_solution_id", pa.int32(), nullable=True)]
    # regressor (μ/σ por objetivo; σ NULL p/ RBF puro) — DEF-C1.
    fields += [pa.field(c, pa.float32(), nullable=True) for c in mu_cols(M)]
    fields += [pa.field(c, pa.float32(), nullable=True) for c in sigma_cols(M)]
    # classificador / híbrido (colunas opcionais que estendem o schema) — DEF-C1.
    fields += [
        pa.field("pred_tipo", pa.string(), nullable=True),
        pa.field("pred_classe", pa.string(), nullable=True),
        pa.field("pred_score", pa.float32(), nullable=True),
        pa.field("pred_confianca", pa.float32(), nullable=True),
        pa.field("modelo_flag", pa.string(), nullable=True),
    ]
    # espaços transformados (cru + transformado + parâmetros) — DEF-C3.
    fields += [
        pa.field("espaco_modelo", pa.string(), nullable=True),
        pa.field("transf_tipo", pa.string(), nullable=True),
        pa.field("transf_params", pa.string(), nullable=True),   # JSON
    ]
    return pa.schema(fields)


def timing_schema():
    """Schema da camada de tempo (§17.6) — a ⭐ série de escalabilidade."""
    pa = _pa()
    return pa.schema([
        pa.field("run_id", pa.string(), nullable=False),
        pa.field("geracao", pa.int32(), nullable=False),
        pa.field("n_acumulado", pa.int32(), nullable=False),
        pa.field("tempo_fit_s", pa.float32(), nullable=False),
        pa.field("tempo_busca_s", pa.float32(), nullable=True),
    ])


# ── Escritor físico (atômico + zstd) ────────────────────────────────────────

def _write_table(path: str, table) -> str:
    """Grava a `table` Arrow em `path` como Parquet zstd, ATOMICAMENTE (D58)."""
    import pyarrow.parquet as pq
    with atomic_path(path) as tmp:
        pq.write_table(table, tmp, compression=PARQUET_CODEC, version="2.6")
    return path


def _f32(a) -> np.ndarray:
    """Cast a float32 SEM arredondamento decimal (D53)."""
    return np.ascontiguousarray(a, dtype=np.float32)


# ── Camada ① real ────────────────────────────────────────────────────────────

def write_real(exp: str, alg: str, problema: str, semente,
               records: list[RealEval], *,
               data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve o Catálogo REAL ① a partir dos `records` do `FEBudget` (§17.2).

    `x/f` vêm em float64 dos records e caem a float32 no Parquet (D53). A ordem
    das linhas = ordem de avaliação (fe_index)."""
    if not records:
        raise ValueError("catálogo ① vazio — um run tem exatamente 31D−1 linhas.")
    pa = _pa()
    D = records[0].x.shape[0]
    M = records[0].f.shape[0]
    n = len(records)
    X = _f32(np.vstack([r.x for r in records]))
    F = _f32(np.vstack([r.f for r in records]))
    cols = {
        "algoritmo": pa.array([alg] * n, type=pa.string()),
        "problema": pa.array([problema] * n, type=pa.string()),
        "semente": pa.array([int(semente)] * n, type=pa.int32()),
        "solution_id": pa.array([r.solution_id for r in records], type=pa.int32()),
    }
    for j, c in enumerate(x_cols(D)):
        cols[c] = pa.array(X[:, j], type=pa.float32())
    for j, c in enumerate(f_cols(M)):
        cols[c] = pa.array(F[:, j], type=pa.float32())
    cols["fe_index"] = pa.array([r.fe_index for r in records], type=pa.int32())
    cols["fase"] = pa.array([r.fase for r in records], type=pa.string())
    table = pa.table(cols).cast(real_schema(D, M))
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "real", data_root), table)


# ── Camada ② pop (membership) ────────────────────────────────────────────────

def write_pop(exp: str, alg: str, problema: str, semente,
              pop_rows, *, data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve o Registro de POPULAÇÃO REAL ② (§17.2). `pop_rows` = iterável de
    `(geracao:int, solution_id:int)` — membership; `x/f` vêm do ① por join."""
    pa = _pa()
    rows = list(pop_rows)
    ger = [int(g) for g, _ in rows]
    sid = [int(s) for _, s in rows]
    n = len(rows)
    table = pa.table({
        "algoritmo": pa.array([alg] * n, type=pa.string()),
        "problema": pa.array([problema] * n, type=pa.string()),
        "semente": pa.array([int(semente)] * n, type=pa.int32()),
        "geracao": pa.array(ger, type=pa.int32()),
        "solution_id": pa.array(sid, type=pa.int32()),
    }).cast(pop_schema())
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "pop", data_root), table)


# ── Camada ③ surrogate (schema único C1/C3) ──────────────────────────────────

def surrogate_row(geracao: int, x, *,
                  real_solution_id: int | None = None,
                  mu=None, sigma=None,
                  pred_tipo: str | None = None,
                  pred_classe: str | None = None,
                  pred_score: float | None = None,
                  pred_confianca: float | None = None,
                  modelo_flag: str | None = None,
                  espaco_modelo: str | None = None,
                  transf_tipo: str | None = None,
                  transf_params=None) -> dict:
    """Monta uma linha da ③ com defaults NULL (§17.2/DEF-C1/C3). O regressor passa
    `mu`(+`sigma`); o classificador `pred_classe`/`pred_score`; o híbrido os dois.
    `transf_params` (dict/list) é serializado em JSON (coluna string)."""
    if pred_tipo is not None and pred_tipo not in PRED_TIPOS:
        raise ValueError(f"pred_tipo inválido: {pred_tipo!r} (esperado {PRED_TIPOS})")
    if espaco_modelo is not None and espaco_modelo not in ESPACOS:
        raise ValueError(f"espaco_modelo inválido: {espaco_modelo!r}")
    return {
        "geracao": int(geracao),
        "x": np.asarray(x, dtype=np.float64).reshape(-1),
        "real_solution_id": real_solution_id,
        "mu": None if mu is None else np.asarray(mu, dtype=np.float64).reshape(-1),
        "sigma": None if sigma is None else np.asarray(sigma, dtype=np.float64).reshape(-1),
        "pred_tipo": pred_tipo,
        "pred_classe": pred_classe,
        "pred_score": pred_score,
        "pred_confianca": pred_confianca,
        "modelo_flag": modelo_flag,
        "espaco_modelo": espaco_modelo,
        "transf_tipo": transf_tipo,
        "transf_params": (None if transf_params is None
                          else json.dumps(transf_params, ensure_ascii=False)),
    }


def write_surrogate(exp: str, alg: str, problema: str, semente,
                    rows: list[dict], *, D: int, M: int, regime: str = "online",
                    data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve a Tabela SURROGATE ③ (§17.2). `rows` = lista de `surrogate_row(...)`.

    Colunas numéricas em float32 (D53); `mu/sigma` ausentes viram NULL tipado; x
    sempre preenchido. Guarda 100% das gerações (sem teto — D54)."""
    pa = _pa()
    n = len(rows)
    xc, mc, sc = x_cols(D), mu_cols(M), sigma_cols(M)

    def col_num(key_arr):
        return pa.array([None if r[key_arr] is None else float(r[key_arr])
                         for r in rows], type=pa.float32())

    cols: dict = {
        "algoritmo": pa.array([alg] * n, type=pa.string()),
        "problema": pa.array([problema] * n, type=pa.string()),
        "semente": pa.array([int(semente)] * n, type=pa.int32()),
        "regime": pa.array([regime] * n, type=pa.string()),
        "geracao": pa.array([int(r["geracao"]) for r in rows], type=pa.int32()),
    }
    def opt_obj(key_arr, j):
        # μ/σ por objetivo j; None (NULL) quando ausente OU mais curto que M —
        # é o caso mono-output do b1 (ParEGO): mu_0 preenchido, mu_1.. NULL (§17.2).
        return [None if (r[key_arr] is None or j >= len(r[key_arr]))
                else float(r[key_arr][j]) for r in rows]

    for j, c in enumerate(xc):
        cols[c] = pa.array([float(r["x"][j]) for r in rows], type=pa.float32())
    cols["real_solution_id"] = pa.array(
        [None if r["real_solution_id"] is None else int(r["real_solution_id"])
         for r in rows], type=pa.int32())
    for j, c in enumerate(mc):
        cols[c] = pa.array(opt_obj("mu", j), type=pa.float32())
    for j, c in enumerate(sc):
        cols[c] = pa.array(opt_obj("sigma", j), type=pa.float32())
    cols["pred_tipo"] = pa.array([r["pred_tipo"] for r in rows], type=pa.string())
    cols["pred_classe"] = pa.array([r["pred_classe"] for r in rows], type=pa.string())
    cols["pred_score"] = col_num("pred_score")
    cols["pred_confianca"] = col_num("pred_confianca")
    cols["modelo_flag"] = pa.array([r["modelo_flag"] for r in rows], type=pa.string())
    cols["espaco_modelo"] = pa.array([r["espaco_modelo"] for r in rows], type=pa.string())
    cols["transf_tipo"] = pa.array([r["transf_tipo"] for r in rows], type=pa.string())
    cols["transf_params"] = pa.array([r["transf_params"] for r in rows], type=pa.string())

    table = pa.table(cols).cast(surrogate_schema(D, M))
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "surrogate", data_root), table)


# ── Camada de tempo (§17.6) ──────────────────────────────────────────────────

def write_timing(exp: str, alg: str, problema: str, semente,
                 timing_rows, *, run_id: str | None = None,
                 data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve a série `(n_acumulado, tempo_fit_s)` por retreino (§17.6). Nos
    algoritmos sem retreino a série tem 1 linha; nos pisos MOEA é vazia."""
    pa = _pa()
    rid = run_id or naming.run_id(exp, alg, problema, semente)
    rows = list(timing_rows)
    n = len(rows)

    def get(k, default=None):
        return [r.get(k, default) for r in rows]

    table = pa.table({
        "run_id": pa.array([rid] * n, type=pa.string()),
        "geracao": pa.array([int(r["geracao"]) for r in rows], type=pa.int32()),
        "n_acumulado": pa.array([int(r["n_acumulado"]) for r in rows], type=pa.int32()),
        "tempo_fit_s": pa.array([float(r["tempo_fit_s"]) for r in rows], type=pa.float32()),
        "tempo_busca_s": pa.array(
            [None if r.get("tempo_busca_s") is None else float(r["tempo_busca_s"])
             for r in rows], type=pa.float32()),
    }).cast(timing_schema())
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "timing", data_root), table)


__all__ = [
    "PARQUET_CODEC", "FASES", "PRED_TIPOS", "ESPACOS",
    "x_cols", "f_cols", "mu_cols", "sigma_cols",
    "real_schema", "pop_schema", "surrogate_schema", "timing_schema",
    "write_real", "write_pop", "write_surrogate", "write_timing",
    "surrogate_row", "run_done",
]
