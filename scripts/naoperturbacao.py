#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GATE 1 — NÃO-PERTURBAÇÃO da camada ① (o invariante central do DI-09).

Promovido a script PERMANENTE pela torre (DI-21): as duas sessões de retrofit
tiveram de RECONSTRUIR este validador no scratchpad porque a 1ª o deixou fora
do repo — a evidência central do gate não era reproduzível por terceiros.

O que prova: a ① (`__real.parquet`) do run ATUAL é IDÊNTICA à do baseline
congelado em `data/experiments/_baseline_pre_retrofit/` — ou seja, a
instrumentação (sonda DI-09, DI-10, timing) NÃO alterou a trajetória da busca.
Compara em DUAS camadas independentes:
  1. bytes do arquivo (sha256) — a prova mais forte;
  2. conteúdo lógico coluna a coluna (pandas .equals sobre colunas comuns) —
     diagnóstico quando (1) difere (metadado/codec ≠ dado).

Uso:
    $PY scripts/naoperturbacao.py <alg> <problema> <semente> [--exp main]
    $PY scripts/naoperturbacao.py --all          # todos os runs com baseline
Exit 0 = verde; 1 = divergência (ou baseline ausente sem --tolerar-ausente).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASELINE = "data/experiments/_baseline_pre_retrofit"


def _sha(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def checa(alg: str, prob: str, sem, exp: str = "main",
          data_root: str = "data") -> tuple[bool, str]:
    from src import naming
    atual = naming.layer_path(exp, alg, prob, sem, "real", data_root)
    rel = os.path.relpath(atual, os.path.join(data_root, "experiments"))
    base = os.path.join(BASELINE, *rel.split(os.sep)[1:])
    if not os.path.exists(atual):
        return False, f"① ATUAL ausente: {atual}"
    if not os.path.exists(base):
        return None, f"sem baseline ({base}) — run novo pós-congelamento"
    h1, h2 = _sha(atual), _sha(base)
    if h1 == h2:
        return True, f"bytes idênticos (sha256 {h1[:16]}…)"
    # bytes diferem — diagnostica no conteúdo lógico
    import pyarrow.parquet as pq
    ta, tb = pq.read_table(atual), pq.read_table(base)
    if ta.num_rows != tb.num_rows:
        return False, (f"BYTES E LINHAS diferem: {ta.num_rows} × {tb.num_rows}")
    comuns = [c for c in ta.schema.names if c in tb.schema.names]
    difs = [c for c in comuns
            if not ta.column(c).to_pandas().equals(tb.column(c).to_pandas())]
    if difs:
        return False, f"CONTEÚDO difere nas colunas: {difs}"
    return False, ("bytes diferem mas conteúdo lógico idêntico (codec/metadado)"
                   " — investigar antes de aceitar")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("alg", nargs="?")
    ap.add_argument("problema", nargs="?")
    ap.add_argument("semente", nargs="?", type=int)
    ap.add_argument("--exp", default="main")
    ap.add_argument("--all", action="store_true",
                    help="varre todos os runs que têm baseline")
    ap.add_argument("--tolerar-ausente", action="store_true",
                    help="baseline ausente conta como aviso, não falha")
    a = ap.parse_args()

    alvos = []
    if a.all:
        for f in sorted(glob.glob(f"{BASELINE}/*/*__real.parquet")):
            fn = os.path.basename(f)                 # exp_main_alg_prob_sem__real
            parts = fn.replace("__real.parquet", "").split("_")
            # exp_{exp}_{alg}_{prob...}_{sem} — prob pode ter '_' (DTLZ2_d15)
            exp, alg = parts[1], parts[2]
            sem = int(parts[-1])
            prob = "_".join(parts[3:-1])
            alvos.append((alg, prob, sem, exp))
    elif a.alg and a.problema and a.semente is not None:
        alvos = [(a.alg, a.problema, a.semente, a.exp)]
    else:
        ap.error("informe <alg> <problema> <semente> ou --all")

    verdes = fails = avisos = 0
    for alg, prob, sem, exp in alvos:
        ok, msg = checa(alg, prob, sem, exp)
        tag = "ok  " if ok else ("--  " if ok is None else "XXXX")
        print(f"  [{tag}] {alg}/{prob}/{sem}: {msg}")
        if ok is True:
            verdes += 1
        elif ok is None:
            avisos += 1
            if not a.tolerar_ausente and not a.all:
                fails += 1
        else:
            fails += 1
    print(f"\nNÃO-PERTURBAÇÃO: {verdes} verdes · {avisos} sem baseline · "
          f"{fails} falhas → {'VERDE' if fails == 0 else 'VERMELHO'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
