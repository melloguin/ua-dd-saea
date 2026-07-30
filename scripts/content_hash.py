#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[G-9] Content-hash na propagação canônico→espelho→bucket [T11-G6].

**O defeito.** A mescla das 4 máquinas (`scripts/tabela42.py:120-134`) decidia "é
o mesmo arquivo" por **tamanho + mtime dentro de 2 s** — uma heurística — e, quando
ela dizia "diferente", **apagava o destino** e re-linkava a origem, silenciosamente.
Dois arquivos de mesmo tamanho com conteúdo diferente (o caso típico: a MESMA
célula rodada 2×, ou uma cópia obsoleta de outra semente) passam por idênticos; e
uma diferença real de conteúdo é resolvida por sobrescrita cega, sem ninguém saber
qual venceu. Amostra da F5: **605 arquivos, 2 divergências** — e 4 dos 5 arquivos
obsoletos do `_bucket_raw` eram de **semente 0** (`main/off · MMF1, DTLZ2, ZDT1`,
todos com 200 linhas), que entrariam no M8 por essa mesma porta.

**A regra.** Conteúdo decide, não metadado — e sem pagar hash onde não precisa:

| situação | veredito | custo |
|---|---|---|
| mesmo inode (hard link) | IDÊNTICOS | zero |
| tamanhos diferentes | **DIVERGENTES** | zero |
| mesmo tamanho, inodes diferentes | md5 dos dois decide | 1 leitura de cada |

Uso:
    python3 scripts/content_hash.py <origem> <destino>          # compara 2 árvores
    python3 scripts/content_hash.py --arquivo a.parquet b.parquet
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

#: Blocos de 1 MiB — o gargalo é I/O, não CPU.
_BLOCO = 1 << 20


def md5(path: str) -> str:
    h = hashlib.md5()                    # noqa: S324 — checksum, não criptografia
    with open(path, "rb") as fh:
        for bloco in iter(lambda: fh.read(_BLOCO), b""):
            h.update(bloco)
    return h.hexdigest()


def mesmo_conteudo(a: str, b: str) -> tuple[bool, str]:
    """`(idênticos?, motivo)` — a decisão do G-9, na ordem barata→caro."""
    try:
        sa, sb = os.stat(a), os.stat(b)
    except OSError as e:
        return False, f"stat falhou ({e})"
    if sa.st_ino == sb.st_ino and sa.st_dev == sb.st_dev:
        return True, "mesmo inode (hard link)"
    if sa.st_size != sb.st_size:
        return False, f"tamanhos diferentes ({sa.st_size} × {sb.st_size})"
    ha, hb = md5(a), md5(b)
    if ha == hb:
        return True, f"md5 igual ({ha[:12]})"
    return False, f"MESMO TAMANHO, md5 DIFERENTE ({ha[:12]} × {hb[:12]})"


def comparar_arvores(origem: str, destino: str, *,
                     ignorar=("_baseline_pre_retrofit", "__pycache__")) -> dict:
    """Compara os arquivos que existem NOS DOIS lados.

    Devolve `{'iguais': n, 'divergentes': [(rel, motivo)], 'so_origem': n,
    'so_destino': n, 'conferidos': n}`. Não copia nada — é verificador.
    """
    def _rels(raiz):
        out = {}
        for dirpath, dirs, arqs in os.walk(raiz):
            dirs[:] = [d for d in dirs if d not in ignorar]
            for f in arqs:
                p = os.path.join(dirpath, f)
                out[os.path.relpath(p, raiz)] = p
        return out

    A, B = _rels(origem), _rels(destino)
    comuns = sorted(set(A) & set(B))
    divergentes, iguais = [], 0
    for rel in comuns:
        ok, motivo = mesmo_conteudo(A[rel], B[rel])
        if ok:
            iguais += 1
        else:
            divergentes.append((rel, motivo))
    return {"conferidos": len(comuns), "iguais": iguais,
            "divergentes": divergentes,
            "so_origem": len(set(A) - set(B)),
            "so_destino": len(set(B) - set(A))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("origem"), ap.add_argument("destino")
    ap.add_argument("--arquivo", action="store_true",
                    help="compara DOIS ARQUIVOS em vez de duas árvores")
    a = ap.parse_args(argv)
    if a.arquivo:
        ok, motivo = mesmo_conteudo(a.origem, a.destino)
        print(f"{'IDÊNTICOS' if ok else 'DIVERGENTES'}: {motivo}")
        return 0 if ok else 1
    r = comparar_arvores(a.origem, a.destino)
    print(f"conferidos={r['conferidos']} iguais={r['iguais']} "
          f"divergentes={len(r['divergentes'])} "
          f"só-origem={r['so_origem']} só-destino={r['so_destino']}")
    for rel, motivo in r["divergentes"][:40]:
        print(f"  🔴 {rel}: {motivo}")
    if len(r["divergentes"]) > 40:
        print(f"  ... +{len(r['divergentes']) - 40}")
    return 0 if not r["divergentes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
