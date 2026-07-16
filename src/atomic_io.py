"""Escrita atômica de arquivos — `*.tmp → os.replace` (D58).

Primitiva da **esteira idempotente e resumível** (§19/§17.7): um arquivo só
aparece no caminho final quando está **inteiro**. Se o processo morre no meio
de uma gravação, sobra no máximo um `*.tmp` órfão (ignorado pelo resume), nunca
um parquet/manifesto/jsonl truncado que o `skip_existing` confundiria com um
run pronto (D58: "run pronto = escrita atômica + fragmento de manifesto").

`os.replace` é atômico no mesmo sistema de arquivos (POSIX rename) — por isso o
`.tmp` é criado **no mesmo diretório** do alvo (nunca em `/tmp`, que pode estar
noutro FS e degradaria o rename a copy+unlink não-atômico).

Módulo **stdlib puro** — F0-03 reusa estas funções para gravar as 3 tabelas
Parquet; F0-01 já as usa no manifesto (§17.2) e no fecho do log (§17.5).
"""

from __future__ import annotations

import os
from contextlib import contextmanager

__all__ = ["atomic_write_bytes", "atomic_write_text", "atomic_path"]


def _tmp_name(path: str) -> str:
    # `.tmp` no MESMO diretório do alvo → rename atômico garantido.
    return f"{path}.{os.getpid()}.tmp"


def atomic_write_bytes(path: str, data: bytes) -> None:
    """Grava `data` em `path` atomicamente (cria o diretório se preciso)."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = _tmp_name(path)
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        # Limpa o `.tmp` se o replace não chegou a consumi-lo (erro no meio).
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    """Versão texto de `atomic_write_bytes`."""
    atomic_write_bytes(path, text.encode(encoding))


@contextmanager
def atomic_path(path: str):
    """Context manager que entrega um caminho `.tmp` e o promove ao final.

    Uso (p.ex. escritores que só aceitam um path — `pyarrow.parquet.write_table`,
    `parquetwrite` etc.):

        with atomic_path(dst) as tmp:
            pq.write_table(table, tmp)
        # aqui `dst` já existe, íntegro; o `.tmp` foi renomeado.

    Se o bloco levantar, o `.tmp` é removido e o alvo final **não** é criado.
    """
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = _tmp_name(path)
    try:
        yield tmp
        if not os.path.exists(tmp):
            raise RuntimeError(
                f"atomic_path: nada foi escrito em {tmp!r} — nada a promover.")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
