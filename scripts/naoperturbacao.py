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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

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


# ═══════════════════════════════════════════════════════════════════════════
#  [G-6] PAR DE RUNS — a prova que o gate do PLANO §5 pede
# ═══════════════════════════════════════════════════════════════════════════

#: Sentinela: no stack MATLAB a sonda não se desliga por kwarg, e sim pela
#: variável de ambiente lida no construtor do `SondaState`.
MATLAB_ENV = object()

#: [G-6] Nome da variável — o mesmo mecanismo do `UA_DD_SAEA_CAMPANHA_ID` (B-03).
ENV_SONDA_OFF = "UA_DD_SAEA_SONDA_OFF"

#: Config → como desligar a sonda. `sobol_batch` e os 4 pisos ONLINE não têm
#: sonda (sem surrogate ⇒ sem régua §17.2.2) e ficam fora POR DESENHO.
#:
#: Os 13 MATLAB usam `MATLAB_ENV` porque o `experiment.m` recebe
#: (alg, problema, semente, exp, dataRoot) e um 6º posicional obrigaria a tocar
#: os 14 `run_*` + o adapter — muito mais superfície do que o gate justifica.
FLAG_SONDA = {
    # Python — kwarg direto no runner
    "c122": "sonda_on", "c149": "sonda_on", "e81": "sonda_on",
    "c154": "sonda_on", "c262": "sonda_on",
    "b5r": "sonda_on", "b5m": "sonda_on", "moead_media": "sonda_on",
    "c311": "emitir_sonda", "treed_media": "emitir_sonda",
    # MATLAB — variável de ambiente (SondaState desarma no construtor)
    "b1": MATLAB_ENV, "b3": MATLAB_ENV, "b4": MATLAB_ENV, "e7": MATLAB_ENV,
    "c141": MATLAB_ENV, "c217": MATLAB_ENV, "c238": MATLAB_ENV,
    "e74": MATLAB_ENV, "e103": MATLAB_ENV,
}


def par_de_runs(alg: str, prob: str, sem, exp: str = "main",
                *, data_root: str | None = None, **kwargs):
    """[G-6] Roda a MESMA célula 2× — com e sem sonda — e compara a ① BIT-A-BIT.

    É o gate que o PLANO §5 pede e que o `--all` NÃO faz: o `--all` compara
    contra o baseline CONGELADO (`_baseline_pre_retrofit/`), que responde outra
    pergunta ("a instrumentação de 2026-07 mudou a trajetória?"). Este responde a
    do invariante 🔴 do CONTRATO §3.1: *a sonda NÃO PODE alterar a busca* — e a
    prova é o par, na mesma sessão, no mesmo código.

    Por que importa: preditores estocásticos (o MC-dropout do e7 é o caso
    extremo) exigem save/restore do RNG em volta da predição. Sem o par, o que
    existe é a promessa. Está PROVADO bit-a-bit em 8 configs MATLAB (b1, b3, b4,
    e7, c141, c217, c238, e74) e FALTA em 11 — é o item de teto mais repetido do
    estudo (T1 ou T2 em 11 dos 24 relatórios).

    Devolve `(ok, mensagem)`; `None` = não-aplicável (config sem sonda).
    """
    import shutil
    import tempfile
    if alg not in FLAG_SONDA:
        return None, f"{alg} não tem sonda (piso sem surrogate) — não-aplicável"
    from src import experiment as _adapter
    from src import naming as _naming
    flag = FLAG_SONDA[alg]
    hashes = {}
    for rotulo, ligada in (("com_sonda", True), ("sem_sonda", False)):
        dr = tempfile.mkdtemp(prefix=f"g6_{alg}_{rotulo}_")
        env_antes = os.environ.get(ENV_SONDA_OFF)
        try:
            # os artefatos de ENTRADA (DoE/dataset/sonda) nunca se regeneram
            # (D63/D90): o tempdir os enxerga por link.
            for entrada in ("doe", "datasets", "sonda"):
                orig = os.path.join(ROOT, "data", entrada)
                if os.path.isdir(orig):
                    os.symlink(orig, os.path.join(dr, entrada))
            if flag is MATLAB_ENV:
                # [G-6] Nos 13 configs MATLAB a flag não é kwarg: o
                # `experiment.m` recebe (alg, problema, semente, exp, dataRoot) e
                # acrescentar um 6º posicional obrigaria a mexer em TODOS os
                # `run_*` e no adapter. O `SondaState` lê `UA_DD_SAEA_SONDA_OFF`
                # no construtor e se DESARMA (o objeto continua existindo, senão
                # `build_manifest` quebraria em `[].n_blocos`). Mesmo precedente
                # do `UA_DD_SAEA_CAMPANHA_ID` do B-03.
                if ligada:
                    os.environ.pop(ENV_SONDA_OFF, None)
                else:
                    os.environ[ENV_SONDA_OFF] = "1"
                _adapter.run(alg, prob, sem, exp=exp, data_root=dr, **kwargs)
            else:
                _adapter.run(alg, prob, sem, exp=exp, data_root=dr,
                             **{flag: ligada}, **kwargs)
            p1 = _naming.layer_path(exp, alg, prob, sem, "real", dr)
            if not os.path.exists(p1):
                return False, f"{rotulo}: a ① não foi escrita"
            hashes[rotulo] = _sha(p1)
        finally:
            # restaurar SEMPRE: um env vazado deixaria a próxima célula sem
            # sonda em silêncio — exatamente o que este gate existe para impedir.
            if env_antes is None:
                os.environ.pop(ENV_SONDA_OFF, None)
            else:
                os.environ[ENV_SONDA_OFF] = env_antes
            shutil.rmtree(dr, ignore_errors=True)
    if hashes["com_sonda"] == hashes["sem_sonda"]:
        return True, (f"① BIT-IDÊNTICA com e sem sonda "
                      f"(sha256 {hashes['com_sonda'][:16]})")
    return False, (f"🔴 A SONDA PERTURBOU A BUSCA: ① difere "
                   f"({hashes['com_sonda'][:12]} × {hashes['sem_sonda'][:12]}) "
                   f"— invariante 🔴 do CONTRATO §3.1 violado. Pára-e-loga (D81)")


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
    ap.add_argument("--par", action="store_true",
                    help="[G-6] RODA a célula 2x (com e sem sonda) em tempdir e "
                         "compara a ① bit-a-bit — a prova do invariante §3.1")
    a = ap.parse_args()

    if a.par:
        if not (a.alg and a.problema and a.semente is not None):
            ap.error("--par exige <alg> <problema> <semente>")
        ok, msg = par_de_runs(a.alg, a.problema, a.semente, a.exp)
        tag = "ok  " if ok else ("--  " if ok is None else "XXXX")
        print(f"  [{tag}] G-6 par {a.alg}/{a.problema}/{a.semente}: {msg}")
        return 0 if ok is not False else 1

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
