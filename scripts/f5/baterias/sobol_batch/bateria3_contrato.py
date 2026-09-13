#!/usr/bin/env python
"""BATERIA 3 — contrato, instrumentação e pareamento do `sobol_batch` (comparativos).

(a) varredura de `tempo_aval_real_s` em TODOS os configs ONLINE (quem grava 0.0);
(b) balanço de tempo não-contabilizado nas 5 células do piso;
(c) pareamento do DoE (doe_hash) nos 5 problemas × todos os configs que os rodaram;
(d) auditoria do mínimo-comum DI-10 no evento de geração de TODOS os pisos + batch;
(e) semântica do ② por config (tamanho por geração).
READ-ONLY; escreve só em f5/baterias/sobol_batch/.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
RES = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = REPO / "f5" / "baterias" / "sobol_batch"
sys.path.insert(0, str(REPO))
os.chdir(REPO)

PROBS5 = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]

# ── (a) tempo_aval_real_s em todos os manifests ONLINE ──────────────────────
rows_t = []
for man in sorted(RES.glob("*/*/42/*.manifest.json")):
    if "_bucket_raw" in str(man) or "__final" in man.name:
        continue
    try:
        d = json.loads(man.read_text())
    except Exception:
        continue
    if d.get("regime") != "online":
        continue
    t = d.get("timing") or {}
    rows_t.append({
        "alg": d.get("alg"), "exp": d.get("exp"), "problema": d.get("problema"),
        "tempo_total_s": t.get("tempo_total_s"),
        "tempo_fit_s": t.get("tempo_fit_surrogate_s"),
        "tempo_busca_s": t.get("tempo_busca_s"),
        "tempo_aval_real_s": t.get("tempo_aval_real_s"),
        "aval_zero": (t.get("tempo_aval_real_s") == 0.0),
    })
dt = pd.DataFrame(rows_t)
res_a = (dt.groupby("alg")
           .agg(n_celulas=("aval_zero", "size"), n_aval_zero=("aval_zero", "sum"),
                aval_mediano=("tempo_aval_real_s", "median"))
           .reset_index().sort_values("alg"))
res_a.to_csv(OUT / "tempo_aval_real_por_config.csv", index=False)

# ── (b) balanço de tempo nas 5 células do piso ──────────────────────────────
rows_b = []
for p in PROBS5:
    b = RES / "sobol_batch" / f"q10_{p}" / "42" / f"exp_batch_sobol_batch_{p}_42"
    man = json.loads(Path(str(b) + ".manifest.json").read_text())
    tim = pd.read_parquet(str(b) + "__timing.parquet")
    t = man["timing"]
    contabil = (t["tempo_fit_surrogate_s"] + t["tempo_busca_s"] +
                t["tempo_aval_real_s"] + t["tempo_pred_sonda_s"])
    rows_b.append({
        "problema": p, "tempo_total_s": t["tempo_total_s"],
        "soma_componentes_s": contabil,
        "nao_contabilizado_s": t["tempo_total_s"] - contabil,
        "frac_nao_contabilizada": 1 - contabil / t["tempo_total_s"],
        "soma_tempo_geracao_s": float(tim["tempo_geracao_s"].sum()),
        "soma_tempo_busca_s": float(tim["tempo_busca_s"].sum()),
        "aval_no_loop_opt_s": float((tim["tempo_geracao_s"] - tim["tempo_busca_s"]).sum()),
    })
pd.DataFrame(rows_b).to_csv(OUT / "balanco_tempo.csv", index=False)

# ── (c) pareamento do DoE nos 5 problemas ───────────────────────────────────
rows_c = []
for man in sorted(RES.glob("*/*/42/*.manifest.json")):
    if "__final" in man.name:
        continue
    try:
        d = json.loads(man.read_text())
    except Exception:
        continue
    if d.get("problema") not in PROBS5 or d.get("regime") != "online":
        continue
    rows_c.append({"alg": d["alg"], "exp": d["exp"], "problema": d["problema"],
                   "doe_hash": d.get("doe_hash")})
dc = pd.DataFrame(rows_c)
par = (dc.groupby("problema")["doe_hash"]
         .agg(n_celulas="size", n_hashes_distintos=lambda s: s.nunique(),
              hash=lambda s: s.iloc[0][:16]).reset_index())
par.to_csv(OUT / "pareamento_doe.csv", index=False)

# ── (d) mínimo-comum DI-10 no evento de geração ─────────────────────────────
CAMPOS = ["fe", "f_best", "n_front1", "ideal", "nadir_pop", "nadir_front1",
          "modelo_hp", "tempo_fit_s", "tempo_busca_s", "dist_min_arquivo"]
rows_d = []
alvos = [("nsga2", "ZDT4", "main"), ("nsga3", "ZDT4", "main"),
         ("moead", "ZDT4", "main"), ("smsemoa", "ZDT4", "main"),
         ("sobol_batch", "q10_ZDT4", "batch"), ("e81", "q10_ZDT4", "batch"),
         ("c149", "q10_ZDT4", "batch"), ("moead_media", "ZDT4", "off")]
for alg, lab, exp in alvos:
    fs = list((RES / alg / lab / "42").glob("*.jsonl"))
    if not fs:
        rows_d.append({"alg": alg, "exp": exp, "erro": "sem jsonl"})
        continue
    recs = []
    for line in fs[0].read_text().splitlines():
        try:
            recs.append(json.loads(line))
        except Exception:
            pass
    cnt = Counter(r.get("rec") for r in recs)
    gen_rec = None
    for cand in (f"{alg}_gen", "decision"):
        if cnt.get(cand):
            gen_rec = cand
            break
    evs = [r for r in recs if r.get("rec") == gen_rec]
    campos = {k for e in evs for k in e}
    row = {"alg": alg, "exp": exp, "evento_de_geracao": gen_rec, "n_eventos": len(evs)}
    row.update({c: (c in campos) for c in CAMPOS})
    row["n_campos_di10"] = sum(row[c] for c in CAMPOS)
    rows_d.append(row)
pd.DataFrame(rows_d).to_csv(OUT / "minimo_comum_di10.csv", index=False)

# ── (e) semântica do ② por config no batch ──────────────────────────────────
rows_e = []
for alg in ("sobol_batch", "e81", "c149"):
    for p in PROBS5:
        f = RES / alg / f"q10_{p}" / "42" / f"exp_batch_{alg}_{p}_42__pop.parquet"
        if not f.exists():
            continue
        pop = pd.read_parquet(f)
        g = pop.groupby("geracao").size()
        rows_e.append({"alg": alg, "problema": p, "linhas": len(pop),
                       "ger_min": int(g.index.min()), "ger_max": int(g.index.max()),
                       "tam_primeira": int(g.iloc[0]), "tam_ultima": int(g.iloc[-1]),
                       "cresce_q_por_ger": bool(np.all(np.diff(g.to_numpy()) == 10))})
pd.DataFrame(rows_e).to_csv(OUT / "semantica_pop.csv", index=False)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
print("=== (a) tempo_aval_real_s por config ONLINE ===")
print(res_a.to_string())
print("\n=== (b) balanço de tempo do piso ===")
print(pd.DataFrame(rows_b).to_string())
print("\n=== (c) pareamento do DoE ===")
print(par.to_string())
print("\n=== (d) mínimo comum DI-10 ===")
print(pd.DataFrame(rows_d).to_string())
print("\n=== (e) semântica do ② ===")
print(pd.DataFrame(rows_e).to_string())
