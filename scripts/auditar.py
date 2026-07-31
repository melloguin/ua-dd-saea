#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GATE 2 — AUDITORIA das camadas instrumentadas (sonda DI-09 + ④ + ⑤ + DI-10).

Promovido a script PERMANENTE pela torre (DI-21) — cobre o que o `accept.py`
(gate objetivo FE/saídas/CP-init) NÃO enxerga: as 606.000 linhas de sonda do
b1/ZDT1, a invariante de ORDEM do artefato, o NULL dos dois lados.

O que audita (por run):
  ③  blocos de sonda: tamanho EXATO por regime (online 2000 · offline 20000),
     CONTÍGUOS, e na **ORDEM DO ARTEFATO** `data/sonda/sonda_{prob}.parquet`
     (o join do R4 é POR POSIÇÃO — ordem divergente = análise lendo o ponto
     errado); `fe_treino_max` sem NULL e ≤ fe_final; `geracao` NULL na sonda
     OFFLINE e inteira na busca; `espaco_modelo` dentro do enum (DI-19.8).
  ④  as 7 colunas do contrato; `tempo_fit_s`/`n_acumulado` NULL nos pisos.
  ⑤  manifesto: `timing.tempo_total_s` preenchido; bloco `sonda` presente
     (ou `nao_se_aplica` nos pisos online); `sigma_dict` presente quando há
     surrogate (DEF-C4 — regra 3 do R4).
  ⑦  `__final` presente nos 5 configs OFFLINE (D-12/DI-21).

Uso:
    $PY scripts/auditar.py <alg> <problema> <semente> [--exp main]
                           [--regime offline] [--piso]
Exit 0 = verde; 1 = qualquer achado.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

S_ONLINE, S_OFFLINE = 2000, 20000
#: [T6-batch] sobol_batch é PISO ONLINE (③ vazia, SEM sonda — CONTRATO §6.1
#: linha "pisos"), mesma classe dos pisos MATLAB nsga2/moead: o auditar não
#: pode exigir sonda dele.
PISOS_ONLINE = {"nsga2", "nsga3", "moead", "smsemoa", "sobol_batch"}
OFFLINE = {"e103", "b5r", "b5m", "c311", "moead_media", "treed_media"}


def audita(alg, prob, sem, exp="main", data_root="data", *,
           regime=None, piso=None) -> list[str]:
    import pyarrow.parquet as pq
    from src import naming
    from src.export import ESPACOS

    piso = piso if piso is not None else alg in PISOS_ONLINE
    offline = (regime == "offline") or alg in OFFLINE
    achados: list[str] = []
    base = naming.layer_path(exp, alg, prob, sem, "surrogate", data_root)
    man = json.load(open(naming.manifest_path(exp, alg, prob, sem, data_root)))
    fe_final = man.get("fe_final")

    # ── [DI-34] OFFLINE: binding por HASH do ① à CÉLULA do grid ─────────────
    # O ① de um run offline tem de ser O DATASET do (tier, dist) do token exp
    # — comparado por hash contra o SIDECAR do artefato, não por contagem de
    # linhas (o catch-all do accept só contava; a assimetria deixava o e103
    # dos sweeps sem binding forte — achado da validação final da torre).
    if offline:
        # dataset_variant (não parse_sweep): sweep-small-lhs ≡ o PRINCIPAL —
        # não existe sidecar `_small_lhs`; a variante normaliza p/ (None,None).
        _tier, _dist = naming.dataset_variant(exp)
        try:
            _sc = json.load(open(naming.dataset_manifest_path(
                prob, sem, tier=_tier, dist=_dist, data_root=data_root)))
        except FileNotFoundError:
            _sc = None
            achados.append(f"⑤ sidecar do dataset da célula ({exp}) ausente")
        if _sc:
            _cp = man.get("cp_init_offline") or {}          # stack Python
            _dm = man.get("dataset") or {}                   # stack MATLAB
            _xm = _cp.get("x_hash") or _dm.get("x_hash")
            _fm = _cp.get("f_hash") or _dm.get("f_hash")
            if _xm != _sc.get("x_hash"):
                achados.append(
                    "⑤ CP-init x_hash ≠ sidecar do dataset da CÉLULA "
                    f"({exp}: tier={_tier or 'principal'}) — o run pode ter "
                    "lido o dataset ERRADO")
            if _fm != _sc.get("f_hash"):
                achados.append(
                    "⑤ CP-init f_hash ≠ sidecar do dataset da CÉLULA "
                    f"({exp}: tier={_tier or 'principal'})")

    # ── ③ ───────────────────────────────────────────────────────────────────
    t = pq.read_table(base)
    reg = t.column("regime").to_pylist()
    ger = t.column("geracao").to_pylist()
    ftm = t.column("fe_treino_max").to_pylist() \
        if "fe_treino_max" in t.schema.names else None
    idx_sonda = [i for i, r in enumerate(reg) if r == "sonda"]

    if piso:
        if idx_sonda:
            achados.append(f"③ piso ONLINE com {len(idx_sonda)} linhas de "
                           f"sonda (contrato: nenhuma)")
    else:
        if not idx_sonda:
            achados.append("③ SEM nenhuma linha de sonda (retrofit ausente?)")
        else:
            S = S_OFFLINE if offline else S_ONLINE
            # trechos contíguos — ATENÇÃO: blocos podem ser ADJACENTES (e103
            # grava Kriging+RBFN em sequência; o e74 grava 3 cabeças), então
            # cada trecho contíguo é fatiado em pedaços de S. O invariante é:
            # todo trecho contíguo tem comprimento MÚLTIPLO de S.
            trechos = []
            ini = idx_sonda[0]
            for a, b in zip(idx_sonda, idx_sonda[1:]):
                if b != a + 1:
                    trechos.append((ini, a))
                    ini = b
            trechos.append((ini, idx_sonda[-1]))
            blocos = []
            for a, b in trechos:
                n = b - a + 1
                if n % S != 0:
                    achados.append(f"③ trecho contíguo de sonda com {n} linhas "
                                   f"(não é múltiplo de S={S})")
                    continue
                blocos += [(a + k * S, a + (k + 1) * S - 1)
                           for k in range(n // S)]
            # ordem do artefato (bit-exata, TODOS os blocos)
            art = pq.read_table(f"{data_root}/sonda/sonda_{prob}.parquet")
            xcols = [c for c in art.schema.names if c.startswith("x")]
            ax = np.column_stack([np.asarray(art.column(c)) for c in xcols])
            tx = np.column_stack(
                [np.asarray(t.column(c).to_pandas()) for c in xcols])
            for a, b in blocos:
                n = b - a + 1
                if not np.array_equal(tx[a:b + 1],
                                      ax[:n].astype(tx.dtype)):
                    achados.append(f"③ bloco @{a}: ORDEM ≠ artefato "
                                   f"(join por posição QUEBRADO)")
                    break
            # geracao: NULL no offline, inteira no online
            g_sonda = [ger[i] for i in idx_sonda]
            if offline:
                nn = sum(1 for g in g_sonda if g is not None)
                if nn:
                    achados.append(f"③ sonda OFFLINE com geracao NÃO-nula em "
                                   f"{nn} linhas (DI-13.5: NULL)")
            else:
                nn = sum(1 for g in g_sonda if g is None)
                if nn:
                    achados.append(f"③ sonda ONLINE com geracao NULL em {nn}")
            # fe_treino_max
            if ftm is None:
                achados.append("③ sem a coluna fe_treino_max (DI-09/A1)")
            else:
                f_sonda = [ftm[i] for i in idx_sonda]
                if any(v is None for v in f_sonda):
                    achados.append("③ fe_treino_max NULL em linhas de sonda")
                elif fe_final is not None and \
                        max(v for v in f_sonda) > int(fe_final):
                    achados.append("③ fe_treino_max > fe_final")
        # enum do espaco_modelo (DI-19.8)
        if "espaco_modelo" in t.schema.names:
            fora = {v for v in t.column("espaco_modelo").to_pylist()
                    if v not in (None, "")} - set(ESPACOS)
            if fora:
                achados.append(f"③ espaco_modelo fora do enum: {sorted(fora)}")

    # ── ④ ───────────────────────────────────────────────────────────────────
    t4 = pq.read_table(naming.layer_path(exp, alg, prob, sem, "timing",
                                         data_root))
    exigidas = {"run_id", "geracao", "n_acumulado", "tempo_fit_s",
                "tempo_busca_s"}
    faltam = exigidas - set(t4.schema.names)
    if faltam:
        achados.append(f"④ colunas ausentes: {sorted(faltam)}")
    if piso and "tempo_fit_s" in t4.schema.names and t4.num_rows:
        vals = t4.column("tempo_fit_s").to_pylist()
        if any(v is not None for v in vals):
            achados.append("④ piso com tempo_fit_s ≠ NULL (DI-13.2)")

    # ── ⑤ ───────────────────────────────────────────────────────────────────
    tim = man.get("timing") or {}
    if not tim.get("tempo_total_s"):
        achados.append("⑤ timing.tempo_total_s vazio (CONTRATO §4 OBRIGA)")
    snd = man.get("sonda")
    if piso:
        if not (isinstance(snd, dict)
                and snd.get("status") == "nao_se_aplica"):
            achados.append("⑤ piso sem o bloco sonda 'nao_se_aplica'")
    else:
        if not snd:
            achados.append("⑤ manifesto sem o bloco sonda")
        if not man.get("sigma_dict"):
            achados.append("⑤ sigma_dict ausente (DEF-C4 — a ③ vira leitura "
                           "proibida pela regra 3 do R4)")

    # ── ⑦ (offline) ─────────────────────────────────────────────────────────
    if alg in OFFLINE:
        p7 = naming.layer_path(exp, alg, prob, sem, "final", data_root)
        if not os.path.exists(p7):
            achados.append("⑦ __final AUSENTE (D-12: o endpoint oficial do "
                           "offline)")
    return achados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("alg")
    ap.add_argument("problema")
    ap.add_argument("semente", type=int)
    ap.add_argument("--exp", default="main")
    # [conserto 2026-07-30 · achado #42] Sem esta flag o `auditar` lia SEMPRE
    # `data/experiments`, mesmo quando o `portao.py` mandava gatear outro
    # corpus. Provado: gatear uma célula INEXISTENTE num sandbox devolvia
    # `auditar=VERDE`, porque ele foi olhar a célula de mesmo nome em produção.
    # A função `audita()` já recebia `data_root` — só o CLI não expunha.
    ap.add_argument("--data-root", default="data",
                    help="raiz dos dados a auditar (default: data/). O F4 do "
                         "RUNBOOK gateia o corpus CONSOLIDADO, que não é data/")
    ap.add_argument("--regime", choices=["online", "offline"], default=None)
    ap.add_argument("--piso", action="store_true", default=None)
    a = ap.parse_args()
    achados = audita(a.alg, a.problema, a.semente, a.exp,
                     regime=a.regime, piso=a.piso, data_root=a.data_root)
    for x in achados:
        print(f"  XXXX {x}")
    print(f"AUDITORIA {a.alg}/{a.problema}/{a.semente}: "
          f"{'VERDE' if not achados else f'{len(achados)} achado(s)'}")
    return 0 if not achados else 1


if __name__ == "__main__":
    sys.exit(main())
