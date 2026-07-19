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

**Retrofit DI-09/v5.2.1 (cartão DI09-retrofit-R2) — tudo ADITIVO:** a ③ ganhou
`fe_treino_max` (A1 — separa in-sample de out-of-sample na análise) e o `regime`
passou a ser **por linha** (`'sonda'` × o regime da busca — §17.2.2); a ④ ganhou
`tempo_pred_sonda_s` e `tempo_geracao_s` (§17.6 expandida). As 3 colunas são
NULLABLE e os escritores mantêm os defaults antigos ⇒ **runs gravados antes do
retrofit continuam legíveis** (a coluna simplesmente não existe no arquivo
antigo; a leitura por nome trata a ausência). `manifest_timing_block()` monta o
bloco `timing` OBRIGATÓRIO do manifesto e `backfill_timing_from_jsonl()`
reconstrói a ④ de um run JÁ EXECUTADO a partir do seu `.jsonl` (sem re-rodar).

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
import os

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
    # DI-09/A1 (v5.2.1): maior `fe_index` no TREINO do modelo no momento do fit
    # desta predição — o filtro in-sample × out-of-sample da análise (R4 §10.4).
    # NULLABLE: quem não instrumentou (runs pré-retrofit) simplesmente não a tem.
    fields += [pa.field("fe_treino_max", pa.int32(), nullable=True)]
    return pa.schema(fields)


def timing_schema():
    """Schema da camada de tempo (§17.6) — a ⭐ série de escalabilidade.

    Pós-retrofit v5.2.1 (§17.6 expandida): `tempo_busca_s` virou OBRIGATÓRIO de
    PREENCHIMENTO (o tipo segue nullable — pisos/runs antigos), e entram
    `tempo_pred_sonda_s` (custo da sonda na iteração; 0 quando não roda) e
    `tempo_geracao_s` (wall TOTAL da geração = fit+busca+aval+overhead)."""
    pa = _pa()
    return pa.schema([
        pa.field("run_id", pa.string(), nullable=False),
        pa.field("geracao", pa.int32(), nullable=False),
        pa.field("n_acumulado", pa.int32(), nullable=False),
        pa.field("tempo_fit_s", pa.float32(), nullable=False),
        pa.field("tempo_busca_s", pa.float32(), nullable=True),
        pa.field("tempo_pred_sonda_s", pa.float32(), nullable=True),
        pa.field("tempo_geracao_s", pa.float32(), nullable=True),
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
                  transf_params=None,
                  fe_treino_max: int | None = None,
                  regime: str | None = None) -> dict:
    """Monta uma linha da ③ com defaults NULL (§17.2/DEF-C1/C3). O regressor passa
    `mu`(+`sigma`); o classificador `pred_classe`/`pred_score`; o híbrido os dois.
    `transf_params` (dict/list) é serializado em JSON (coluna string).

    `fe_treino_max` (DI-09/A1) = maior `fe_index` no TREINO do modelo no momento
    do fit que produziu ESTA predição. `regime` (DI-09/§17.2.2) sobrepõe, LINHA A
    LINHA, o regime default do `write_surrogate` — é assim que as 2000 linhas da
    sonda (`regime='sonda'`) convivem com as da busca na MESMA tabela ③."""
    if pred_tipo is not None and pred_tipo not in PRED_TIPOS:
        raise ValueError(f"pred_tipo inválido: {pred_tipo!r} (esperado {PRED_TIPOS})")
    if espaco_modelo is not None and espaco_modelo not in ESPACOS:
        raise ValueError(f"espaco_modelo inválido: {espaco_modelo!r}")
    return {
        "geracao": int(geracao),
        "fe_treino_max": (None if fe_treino_max is None else int(fe_treino_max)),
        "regime": regime,
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
    sempre preenchido. Guarda 100% das gerações (sem teto — D54).

    `regime` é o DEFAULT do arquivo; uma linha que traga `regime` próprio (a
    sonda — §17.2.2) manda sobre ele. **A ORDEM DAS LINHAS É PRESERVADA** — é o
    invariante do writer que permite o join do bloco de sonda com o gabarito
    POR POSIÇÃO (CONTRATO §3.1 / R4 regra 5)."""
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
        # regime POR LINHA (DI-09): a linha manda; o parâmetro é só o default.
        "regime": pa.array([(r.get("regime") or regime) for r in rows],
                           type=pa.string()),
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
    cols["fe_treino_max"] = pa.array(                      # DI-09/A1
        [None if r.get("fe_treino_max") is None else int(r["fe_treino_max"])
         for r in rows], type=pa.int32())

    table = pa.table(cols).cast(surrogate_schema(D, M))
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "surrogate", data_root), table)


# ── Camada de tempo (§17.6) ──────────────────────────────────────────────────

def write_timing(exp: str, alg: str, problema: str, semente,
                 timing_rows, *, run_id: str | None = None,
                 data_root: str = naming.DEFAULT_DATA_ROOT) -> str:
    """Escreve a série `(n_acumulado, tempo_fit_s)` por retreino (§17.6). Nos
    algoritmos sem retreino a série tem 1 linha; nos pisos MOEA é vazia.

    Pós-retrofit: além de `tempo_busca_s`, aceita `tempo_pred_sonda_s` e
    `tempo_geracao_s` nas linhas (ausentes ⇒ NULL — a ④ de um instrumentador
    que ainda não os produz segue válida)."""
    pa = _pa()
    rid = run_id or naming.run_id(exp, alg, problema, semente)
    rows = list(timing_rows)
    n = len(rows)

    def opt(key):
        """Coluna float32 opcional: ausente ou None ⇒ NULL tipado."""
        return pa.array([None if r.get(key) is None else float(r[key])
                         for r in rows], type=pa.float32())

    table = pa.table({
        "run_id": pa.array([rid] * n, type=pa.string()),
        "geracao": pa.array([int(r["geracao"]) for r in rows], type=pa.int32()),
        "n_acumulado": pa.array([int(r["n_acumulado"]) for r in rows], type=pa.int32()),
        "tempo_fit_s": pa.array([float(r["tempo_fit_s"]) for r in rows], type=pa.float32()),
        "tempo_busca_s": opt("tempo_busca_s"),
        "tempo_pred_sonda_s": opt("tempo_pred_sonda_s"),
        "tempo_geracao_s": opt("tempo_geracao_s"),
    }).cast(timing_schema())
    return _write_table(
        naming.layer_path(exp, alg, problema, semente, "timing", data_root), table)


# ── Bloco `timing` do MANIFESTO (§17.6 — OBRIGATÓRIO pós-v5.2.1) ─────────────

def manifest_timing_block(*, tempo_total_s: float, tempo_fit_surrogate_s: float,
                          tempo_busca_s: float, tempo_aval_real_s: float,
                          tempo_pred_sonda_s: float | None = None,
                          casas: int = 4, **extra) -> dict:
    """Monta o bloco `timing` agregado do manifesto (§17.6(1) / CONTRATO §4).

    As 4 chaves do contrato são OBRIGATÓRIAS nos 21 configs (a auditoria da
    torre achou o bloco ZERADO em 10/12). `tempo_pred_sonda_s` é o agregado da
    sonda (DI-09) — omitido quando o config não tem sonda (os 4 pisos online,
    §R1 da PROPOSTA). `**extra` deixa cada runner anexar o seu desdobramento
    próprio (ex.: `tempo_paths_s` do c154) sem duplicar este helper."""
    blk = {
        "tempo_total_s": round(float(tempo_total_s), casas),
        "tempo_fit_surrogate_s": round(float(tempo_fit_surrogate_s), casas),
        "tempo_busca_s": round(float(tempo_busca_s), casas),
        "tempo_aval_real_s": round(float(tempo_aval_real_s), casas),
    }
    if tempo_pred_sonda_s is not None:
        blk["tempo_pred_sonda_s"] = round(float(tempo_pred_sonda_s), casas)
    blk.update({k: v for k, v in extra.items() if v is not None})
    return blk


# ── Backfill da ④ a partir do `.jsonl` (D-4 do c154 — sem re-rodar) ──────────

#: Chaves de `tempo_busca_s` aceitas no `decision` do jsonl, em ordem de
#: preferência: a canônica (pós-retrofit) e a legada do c154 (`t_busca_s`).
_BUSCA_KEYS = ("tempo_busca_s", "t_busca_s")


def _jsonl_ts(rec: dict) -> float:
    from datetime import datetime
    return datetime.fromisoformat(rec["ts"]).timestamp()


def backfill_timing_from_jsonl(exp: str, alg: str, problema: str, semente, *,
                               data_root: str = naming.DEFAULT_DATA_ROOT,
                               dry_run: bool = False) -> dict:
    """Reconstrói a ④ de um run JÁ EXECUTADO a partir do seu `.jsonl` (§17.6
    expandida; gap D-4 do c154 — o DTLZ2 custou 14h37, re-rodar está fora).

    **O que é EXATO e o que é DERIVADO** (a distinção vai no relatório de
    retorno e deve ser propagada ao manifesto — dado de tese não se maquia):
    - `geracao`/`n_acumulado`/`tempo_fit_s`: EXATOS (evento `timing` do jsonl).
    - `tempo_busca_s`: EXATO quando a `decision` da iteração traz a grandeza
      (`tempo_busca_s` ou o legado `t_busca_s`); DERIVADO como
      `ts(decision) − ts(timing)` quando não traz — é o caso da ÚLTIMA iteração,
      cuja `decision` é o `hard_stop` (D61), que fecha antes de o wall da busca
      ser logado. O derivado foi calibrado contra as iterações de valor
      conhecido do c154/DTLZ2: erro +8 ms em ~450 s (2×10⁻⁵ relativo).
    - `tempo_geracao_s`: DERIVADO. A âncora de início da iteração é
      `ts(timing_it) − tempo_fit_s(it)` (o `timing` é emitido imediatamente após
      o fit, que abre a iteração); o wall da geração é a diferença entre âncoras
      consecutivas, e o da última vai até o `footer`.
    - `tempo_pred_sonda_s`: NULL quando o run é PRÉ-sonda (não existia grandeza
      a medir); preenchido a partir do evento `sonda` quando existir.

    **Guarda anti-reescrita-às-cegas:** se já houver ④ no disco, as colunas
    EXATAS reconstruídas são conferidas contra ela; divergência ⇒ RuntimeError
    (pára-e-loga D81) — nada é sobrescrito.

    `dry_run=True` calcula e confere sem escrever. Retorna o relatório."""
    jpath = naming.jsonl_path(exp, alg, problema, semente, data_root)
    if not os.path.exists(jpath):
        raise FileNotFoundError(
            f"backfill da ④ exige o `.jsonl` do run: {jpath} ausente. "
            f"Pára-e-loga (D81).")

    timing_recs: dict[int, dict] = {}
    decision_recs: dict[int, dict] = {}
    sonda_recs: dict[int, dict] = {}
    footer_ts: float | None = None
    with open(jpath, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:     # última linha parcial (crash) —
                continue                     # tolerada na leitura (audit_log)
            rec, it = r.get("rec"), r.get("it")
            if rec == "timing" and it is not None:
                timing_recs[int(it)] = r
            elif rec == "decision" and it is not None:
                decision_recs[int(it)] = r
            elif rec == "sonda" and it is not None:
                sonda_recs[int(it)] = r
            elif rec == "footer":
                footer_ts = _jsonl_ts(r)
    if not timing_recs:
        raise RuntimeError(
            f"backfill da ④: nenhum evento `timing` em {jpath} — nada a "
            f"reconstruir. Pára-e-loga (D81).")

    its = sorted(timing_recs)
    ancora = {it: _jsonl_ts(timing_recs[it]) - float(timing_recs[it]["tempo_fit_s"])
              for it in its}
    fim = footer_ts if footer_ts is not None else _jsonl_ts(timing_recs[its[-1]])

    rows, exatos, derivados = [], 0, 0
    for i, it in enumerate(its):
        dec = decision_recs.get(it)
        busca = next((dec[k] for k in _BUSCA_KEYS
                      if dec is not None and dec.get(k) is not None), None)
        if busca is not None:
            exatos += 1
        elif dec is not None:
            busca = _jsonl_ts(dec) - _jsonl_ts(timing_recs[it])
            derivados += 1
        prox = ancora[its[i + 1]] if i + 1 < len(its) else fim
        snd = sonda_recs.get(it)
        rows.append({
            "geracao": it,
            "n_acumulado": int(timing_recs[it]["n_acumulado"]),
            "tempo_fit_s": float(timing_recs[it]["tempo_fit_s"]),
            "tempo_busca_s": (None if busca is None else float(busca)),
            "tempo_pred_sonda_s": (None if snd is None
                                   else float(snd.get("tempo_pred_sonda_s", 0.0))),
            "tempo_geracao_s": max(prox - ancora[it], 0.0),
        })

    # guarda: confere as colunas EXATAS contra a ④ que já está no disco.
    tpath = naming.layer_path(exp, alg, problema, semente, "timing", data_root)
    conferidas = 0
    if os.path.exists(tpath):
        import pyarrow.parquet as pq
        old = pq.read_table(tpath).to_pydict()
        if len(old["geracao"]) != len(rows):
            raise RuntimeError(
                f"backfill da ④ ({tpath}): a ④ no disco tem "
                f"{len(old['geracao'])} linhas e o jsonl reconstrói "
                f"{len(rows)} — divergência estrutural, NADA foi sobrescrito. "
                f"Pára-e-loga (D81).")
        for k, novo in enumerate(rows):
            if (int(old["geracao"][k]) != novo["geracao"]
                    or int(old["n_acumulado"][k]) != novo["n_acumulado"]
                    or abs(float(old["tempo_fit_s"][k])
                           - novo["tempo_fit_s"]) > 1e-3):
                raise RuntimeError(
                    f"backfill da ④ ({tpath}): linha {k} diverge da ④ no disco "
                    f"nas colunas EXATAS (geracao/n_acumulado/tempo_fit_s) — o "
                    f"jsonl não é deste run. NADA foi sobrescrito. "
                    f"Pára-e-loga (D81).")
        conferidas = len(rows)

    if not dry_run:
        write_timing(exp, alg, problema, semente, rows, data_root=data_root)
    return {
        "path": tpath, "n_linhas": len(rows), "dry_run": dry_run,
        "busca_exatas": exatos, "busca_derivadas": derivados,
        "busca_nulas": sum(1 for r in rows if r["tempo_busca_s"] is None),
        "linhas_conferidas_vs_disco": conferidas,
        "procedencia": {
            "exato": "geracao, n_acumulado, tempo_fit_s, tempo_busca_s "
                     "(iterações com a grandeza na `decision`)",
            "derivado": "tempo_geracao_s (âncoras ts do jsonl) e o "
                        "tempo_busca_s das iterações sem a grandeza logada "
                        "(ts(decision)−ts(timing))",
        },
    }


__all__ = [
    "PARQUET_CODEC", "FASES", "PRED_TIPOS", "ESPACOS",
    "x_cols", "f_cols", "mu_cols", "sigma_cols",
    "real_schema", "pop_schema", "surrogate_schema", "timing_schema",
    "write_real", "write_pop", "write_surrogate", "write_timing",
    "surrogate_row", "run_done",
    "manifest_timing_block", "backfill_timing_from_jsonl",
]
