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
LAYERS: tuple[str, ...] = ("real", "pop", "surrogate", "timing")

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
    if layer not in LAYERS:
        raise ValueError(f"camada inválida: {layer!r}. Esperado uma de {LAYERS}.")
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


def layer_filenames(exp: str, alg: str, problema: str, semente) -> list[str]:
    """As 4 camadas parquet do run (① ② ③ + timing)."""
    return [layer_filename(exp, alg, problema, semente, ly) for ly in LAYERS]


def output_filenames(exp: str, alg: str, problema: str, semente) -> list[str]:
    """As "4 saídas" verificáveis: 3 tabelas + timing + `.jsonl` (§22.6).

    (O fragmento de manifesto é a 5ª peça — checado à parte pela esteira.)
    """
    return (layer_filenames(exp, alg, problema, semente)
            + [jsonl_filename(exp, alg, problema, semente)])


# ── Espelho no bucket (GCS) ────────────────────────────────────────────────

def blob_prefix(exp: str, alg: str) -> str:
    """Prefixo do objeto no bucket (o GCS não tem pastas — §17.7)."""
    check_exp(exp)
    return f"experiments/{exp}/{safe_alg(alg)}"


def blob_path(exp: str, alg: str, filename: str) -> str:
    """Nome do objeto no bucket p/ um arquivo local do run (§17.7)."""
    return f"{blob_prefix(exp, alg)}/{filename}"
