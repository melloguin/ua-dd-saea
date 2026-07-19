"""Convenção canônica de nomes e caminhos do export (§17.7 / D55).

Fonte ÚNICA da nomenclatura do pipeline — consumida pelo despachante
(`experiments.py`), pelo manifesto (`src/manifest.py`), pelo logger
(`src/audit_log.py`) e pelo runner de aceitação (`scripts/accept.py`).
Ter um só lugar garante que quem **escreve** e quem **verifica** um run
concordam byte-a-byte no nome do arquivo.

Regras (SPEC v5.2):
- `run_id = {exp}_{alg}_{problema}_{semente}`               (D55)
- `exp ∈ {main, off, batch, sweep-{tier}-{dist}}`           (D55) — o token
  `{exp}` evita a colisão principal×sub-estudos (mesmo `(alg,prob,sem)`).
- pasta local  = `data/experiments/{exp}/{alg}/`            (§17.7)
- base do run  = `exp_{run_id}`                             (§17.7)
- camadas      = `{base}__{camada}.parquet`, camada ∈
  {real (①), pop (②), surrogate (③), timing (§17.6)}       (§17.1/§17.6)
  + `final` (⑦) — camada OPCIONAL, **só nos 5 configs offline** (DI-08)
- log auditoria= `{base}.jsonl`                             (§17.5)
- manifesto    = `{base}.manifest.json` (fragmento por run — D58; realiza o
  `{run_id}.manifest.json` do D58 sob a base `exp_{run_id}` do §17.7, de modo
  que TODOS os artefatos do run compartilham o mesmo prefixo)
- espelho GCS  = `experiments/{exp}/{alg}/{arquivo}`        (§17.7; prefixo,
  o bucket não tem pastas de verdade)

Módulo **stdlib puro** (sem numpy/pandas) — importável em qualquer
interpretador, inclusive o `python3` base do Mac.
"""

from __future__ import annotations

import os
import re

# ── Vocabulário fixo ───────────────────────────────────────────────────────

#: Camadas de export por run (§17.1 ①②③ + §17.6 timing).
#: **OBRIGATÓRIAS nos 21 configs** — é esta tupla que o manifesto (`paths`,
#: `is_run_done`), o espelho GCS (`plan_targets`) e o gate (`check_outputs`)
#: iteram. NÃO acrescente camadas opcionais aqui: um run online passaria a ser
#: cobrado por um arquivo que ele nunca escreve (o resume da esteira o daria
#: como "não pronto" e a re-executaria para sempre).
LAYERS: tuple[str, ...] = ("real", "pop", "surrogate", "timing")

#: [R3-00-harness / DI-08] Camada ⑦ `__final.parquet` — o conjunto não-dominado
#: FINAL do regime OFFLINE avaliado UMA vez na função verdadeira (§11/B7.5, "a
#: única chamada real do offline"), em `src/problems.py` (float64), PÓS-HOC e
#: FORA do orçamento (a exceção contábil do §11).
#:
#: É **OPCIONAL por construção**: existe só nos 5 configs offline (e103, b5r,
#: b5m, c311, piso-off) e não tem sentido nos 16 online. Por isso vive FORA de
#: `LAYERS` — quem exige a camada é o branch offline do gate, não o contrato
#: universal do run. `layer_path(..., "final")` funciona (DI-08 §Execução-2);
#: `layer_filenames`/`output_filenames`/`is_run_done` seguem intocados.
FINAL_LAYER: str = "final"

#: Camadas opcionais, por regime (hoje só a ⑦ do offline).
OPTIONAL_LAYERS: tuple[str, ...] = (FINAL_LAYER,)

#: O vocabulário COMPLETO aceito por `check_layer`/`layer_path` (obrigatórias +
#: opcionais). Use `LAYERS` quando a pergunta for "o que todo run deve ter".
ALL_LAYERS: tuple[str, ...] = LAYERS + OPTIONAL_LAYERS

#: Tokens de experimento estáticos (§0/§1.5/D55). O sweep é dinâmico:
#: `sweep-{tier}-{dist}` — use `sweep_exp(tier, dist)`.
STATIC_EXPS: tuple[str, ...] = ("main", "off", "batch")

#: Diretório-raiz padrão das saídas (relativo à raiz do repo).
DEFAULT_DATA_ROOT = "data"

_SWEEP_RE = re.compile(r"^sweep-[A-Za-z0-9]+-[A-Za-z0-9]+$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9]+$")  # tier/dist e componentes simples


# ── Validação/normalização ─────────────────────────────────────────────────

def sweep_exp(tier: str, dist: str) -> str:
    """Token de experimento do sweep offline: `sweep-{tier}-{dist}` (D55)."""
    if not _TOKEN_RE.match(tier) or not _TOKEN_RE.match(dist):
        raise ValueError(f"tier/dist inválidos p/ sweep: {tier!r}, {dist!r}")
    return f"sweep-{tier}-{dist}"


def is_valid_exp(exp: str) -> bool:
    """`exp` é um token de experimento válido (estático ou sweep)?"""
    return exp in STATIC_EXPS or bool(_SWEEP_RE.match(exp))


def check_exp(exp: str) -> str:
    if not is_valid_exp(exp):
        raise ValueError(
            f"exp inválido: {exp!r}. Esperado {STATIC_EXPS} ou 'sweep-<tier>-<dist>' (D55).")
    return exp


def check_layer(layer: str) -> str:
    """Valida um token de camada contra o vocabulário COMPLETO (`ALL_LAYERS`).

    [R3-00-harness] Aceita as 4 obrigatórias **e** as opcionais (`final` — DI-08).
    A distinção "toda run tem" × "só o offline tem" é de quem CONSOME a lista
    (`LAYERS` vs `ALL_LAYERS`), não de quem valida um nome de arquivo.
    """
    if layer not in ALL_LAYERS:
        raise ValueError(f"camada inválida: {layer!r}. Esperado uma de {ALL_LAYERS}.")
    return layer


def safe_alg(alg: str) -> str:
    """Id-acrônimo canônico do algoritmo (§17.7).

    Os ids do estudo já são limpos (`b1, c217, e103, b5r, b5m, ...`). Ainda
    assim, normaliza defensivamente `/` e espaço que apareceriam em nomes
    legados (ex.: 'Prob-MOEA/D') para não estourar o caminho de arquivo.
    """
    return alg.replace("/", "_").replace(" ", "_")


# ── run_id e base ──────────────────────────────────────────────────────────

def run_id(exp: str, alg: str, problema: str, semente) -> str:
    """`{exp}_{alg}_{problema}_{semente}` (D55)."""
    check_exp(exp)
    return f"{exp}_{safe_alg(alg)}_{problema}_{semente}"


def base(exp: str, alg: str, problema: str, semente) -> str:
    """Base física do run: `exp_{run_id}` (§17.7)."""
    return f"exp_{run_id(exp, alg, problema, semente)}"


# ── Caminhos locais ────────────────────────────────────────────────────────

def experiments_root(data_root: str = DEFAULT_DATA_ROOT) -> str:
    return os.path.join(data_root, "experiments")


def run_dir(exp: str, alg: str, data_root: str = DEFAULT_DATA_ROOT) -> str:
    """`data/experiments/{exp}/{alg}/` (§17.7)."""
    check_exp(exp)
    return os.path.join(experiments_root(data_root), exp, safe_alg(alg))


def layer_filename(exp: str, alg: str, problema: str, semente, layer: str) -> str:
    check_layer(layer)
    return f"{base(exp, alg, problema, semente)}__{layer}.parquet"


def layer_path(exp: str, alg: str, problema: str, semente, layer: str,
               data_root: str = DEFAULT_DATA_ROOT) -> str:
    return os.path.join(run_dir(exp, alg, data_root),
                        layer_filename(exp, alg, problema, semente, layer))


def jsonl_filename(exp: str, alg: str, problema: str, semente) -> str:
    return f"{base(exp, alg, problema, semente)}.jsonl"


def jsonl_path(exp: str, alg: str, problema: str, semente,
               data_root: str = DEFAULT_DATA_ROOT) -> str:
    return os.path.join(run_dir(exp, alg, data_root),
                        jsonl_filename(exp, alg, problema, semente))


def manifest_filename(exp: str, alg: str, problema: str, semente) -> str:
    """Fragmento de manifesto por run (D58; base compartilhada — §17.7)."""
    return f"{base(exp, alg, problema, semente)}.manifest.json"


def manifest_path(exp: str, alg: str, problema: str, semente,
                  data_root: str = DEFAULT_DATA_ROOT) -> str:
    return os.path.join(run_dir(exp, alg, data_root),
                        manifest_filename(exp, alg, problema, semente))


def final_filename(exp: str, alg: str, problema: str, semente) -> str:
    """`{base}__final.parquet` — a camada ⑦ do offline (DI-08)."""
    return layer_filename(exp, alg, problema, semente, FINAL_LAYER)


def final_path(exp: str, alg: str, problema: str, semente,
               data_root: str = DEFAULT_DATA_ROOT) -> str:
    """Caminho da camada ⑦ `__final.parquet` (DI-08 — só os 5 configs offline).

    Atalho legível para `layer_path(..., "final")`; é o caminho que o avaliador
    pós-hoc (`scripts/final_eval.py`) escreve e que o branch offline do gate lê.
    """
    return layer_path(exp, alg, problema, semente, FINAL_LAYER, data_root)


def layer_filenames(exp: str, alg: str, problema: str, semente) -> list[str]:
    """As 4 camadas parquet OBRIGATÓRIAS do run (① ② ③ + timing).

    Não inclui a ⑦ `final` de propósito — ela é opcional/offline (DI-08); quem a
    exige é o branch offline do gate. Ver `FINAL_LAYER`/`final_path`.
    """
    return [layer_filename(exp, alg, problema, semente, ly) for ly in LAYERS]


def output_filenames(exp: str, alg: str, problema: str, semente) -> list[str]:
    """As "4 saídas" verificáveis: 3 tabelas + timing + `.jsonl` (§22.6).

    (O fragmento de manifesto é a 5ª peça — checado à parte pela esteira.)
    """
    return (layer_filenames(exp, alg, problema, semente)
            + [jsonl_filename(exp, alg, problema, semente)])


# ── Artefatos de inicialização compartilhados: DoE + dataset offline ───────
#  (§5.2/D87 online · §7·§9/D90 offline). ÚNICOS por (problema, semente[,tier,dist]),
#  SEM alg_id (D88): todos os configs CARREGAM os mesmos pontos físicos.

def doe_dir(problema: str, data_root: str = DEFAULT_DATA_ROOT) -> str:
    """`data/doe/{problema}/` (D87)."""
    return os.path.join(data_root, "doe", problema)


def doe_filename(problema: str, semente) -> str:
    """`doe_{problema}_{semente}.parquet` (D87)."""
    return f"doe_{problema}_{semente}.parquet"


def doe_path(problema: str, semente, data_root: str = DEFAULT_DATA_ROOT) -> str:
    """Caminho do artefato DoE online (11D−1 × D, colunas x0…x{D−1}) — D87/D88."""
    return os.path.join(doe_dir(problema, data_root), doe_filename(problema, semente))


def doe_manifest_path(problema: str, semente,
                      data_root: str = DEFAULT_DATA_ROOT) -> str:
    """Sidecar do DoE com o hash do array decodificado (D87) — fonte-de-verdade
    do CP-init; o manifesto do run apenas ecoa este `doe_hash`."""
    return os.path.join(doe_dir(problema, data_root),
                        f"doe_{problema}_{semente}.manifest.json")


def dataset_dir(problema: str, data_root: str = DEFAULT_DATA_ROOT) -> str:
    """`data/datasets/{problema}/` (D90)."""
    return os.path.join(data_root, "datasets", problema)


def dataset_filename(problema: str, semente,
                     tier: str | None = None, dist: str | None = None) -> str:
    """`ds_{problema}_{semente}[_{tier}_{dist}].parquet` (D90).

    O offline PRINCIPAL (§7/§9 — tier `small`, dist `lhs`) usa o nome SEM sufixo;
    as variantes do sweep (§11.5) carregam `_{tier}_{dist}`. O `[tier,dist]` é
    opcional em par (ambos ou nenhum).
    """
    if (tier is None) != (dist is None):
        raise ValueError("tier e dist devem vir juntos (ambos ou nenhum).")
    if tier is None:
        return f"ds_{problema}_{semente}.parquet"
    if not _TOKEN_RE.match(tier) or not _TOKEN_RE.match(dist):
        raise ValueError(f"tier/dist inválidos: {tier!r}, {dist!r}")
    return f"ds_{problema}_{semente}_{tier}_{dist}.parquet"


def dataset_path(problema: str, semente, tier: str | None = None,
                 dist: str | None = None,
                 data_root: str = DEFAULT_DATA_ROOT) -> str:
    """Caminho do dataset offline (X+F, colunas x0…x{D−1},f0…f{M−1}) — D90."""
    return os.path.join(dataset_dir(problema, data_root),
                        dataset_filename(problema, semente, tier, dist))


def dataset_manifest_path(problema: str, semente, tier: str | None = None,
                          dist: str | None = None,
                          data_root: str = DEFAULT_DATA_ROOT) -> str:
    """Sidecar do dataset offline com o hash do array decodificado (D90)."""
    fn = dataset_filename(problema, semente, tier, dist)
    return os.path.join(dataset_dir(problema, data_root),
                        fn[:-len(".parquet")] + ".manifest.json")


# ── Espelho no bucket (GCS) ────────────────────────────────────────────────

def blob_prefix(exp: str, alg: str) -> str:
    """Prefixo do objeto no bucket (o GCS não tem pastas — §17.7)."""
    check_exp(exp)
    return f"experiments/{exp}/{safe_alg(alg)}"


def blob_path(exp: str, alg: str, filename: str) -> str:
    """Nome do objeto no bucket p/ um arquivo local do run (§17.7)."""
    return f"{blob_prefix(exp, alg)}/{filename}"
