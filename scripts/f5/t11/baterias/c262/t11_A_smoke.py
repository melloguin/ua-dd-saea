#!/usr/bin/env python
"""T11/c262 — BATERIA A: o smoke PYTHON preservado (evidencia_T11/smoke_python).
READ-ONLY. Verifica as 3 correcoes A4 (params no 5, acqf_hp/T1, guard fit_retries)
e re-mede o mecanismo (query-joias) no artefato POS-T11.
"""
import json, sys
import numpy as np
import pandas as pd

D = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/main/c262"
B = f"{D}/exp_main_c262_MMF1_0"

out = {}

# ---------- 5) manifesto ----------
m = json.load(open(f"{B}.manifest.json"))
out["A1_params_no_5"] = "params" in m
out["A1_params_chaves"] = sorted(m.get("params", {}).keys())
out["A1_acqf_hp"] = m.get("params", {}).get("acqf_hp")
out["A1_n_acqf_hp"] = len(m.get("params", {}).get("acqf_hp", {}))
out["A1_campanha_id"] = m.get("campanha_id")
out["A1_repo_hash"] = m.get("repo_hash")
out["A1_schema_version"] = m.get("schema_version")
out["A1_status"] = m.get("status")
out["A1_fe_final"] = m.get("fe_final")
out["A1_maxfe"] = m.get("maxfe")
out["A1_n_geracoes"] = m.get("n_geracoes")
out["A1_cache_hits"] = m.get("cache_hits")
out["A1_fused"] = m.get("fused_kernel")
out["A1_acqf_ref_f"] = m.get("acqf_ref_f")
out["A1_sonda"] = m.get("sonda")
out["A1_q"] = m.get("q")
out["A1_topkeys"] = sorted(m.keys())
out["A1_sigma_keys"] = sorted(m.get("sigma_dict", {}).keys())

# ---------- 6) jsonl ----------
recs = []
bad = 0
for ln in open(f"{B}.jsonl"):
    ln = ln.strip()
    if not ln:
        continue
    try:
        recs.append(json.loads(ln))
    except Exception:
        bad += 1
out["A2_linhas_ruins"] = bad
out["A2_recs"] = pd.Series([r.get("rec") for r in recs]).value_counts().to_dict()

hdr = [r for r in recs if r.get("rec") == "header"]
out["A2_n_header"] = len(hdr)
h = hdr[0] if hdr else {}
out["A2_header_params"] = h.get("params")
out["A2_header_keys"] = sorted(h.keys())
# fonte unica: header.params == manifest.params ?
out["A2_header_eq_manifest_params"] = (h.get("params") == m.get("params"))

foot = [r for r in recs if r.get("rec") == "footer"]
out["A2_n_footer"] = len(foot)
out["A2_footer"] = foot[0] if foot else None

guards = [r for r in recs if r.get("rec") == "guard"]
out["A3_guards"] = pd.Series([g.get("guard") or g.get("tipo") or g.get("nome")
                              for g in guards]).value_counts().to_dict() if guards else {}
out["A3_guards_raw"] = guards[:12]
out["A3_guard_fit_retries"] = [g for g in guards
                               if "fit_retries" in json.dumps(g)]

dec = [r for r in recs if r.get("rec") == "decision"]
out["A4_n_decisoes"] = len(dec)
if dec:
    out["A4_chaves_decisao"] = sorted(dec[0].keys())
    fr = [d.get("fit_retries") for d in dec]
    out["A4_fit_retries_presente"] = sum(x is not None for x in fr)
    out["A4_fit_retries_soma"] = int(np.nansum([x or 0 for x in fr]))
    # QUERY-JOIA 1: escolhido == max(restarts), bit-a-bit
    ok = 0; tot = 0; dmax = 0.0
    for d in dec:
        a = d.get("acqf_todos_restarts"); e = d.get("acqf_escolhido")
        if a is None or e is None:
            continue
        tot += 1
        dd = abs(float(e) - max(float(x) for x in a))
        dmax = max(dmax, dd)
        ok += (dd == 0.0)
    out["A4_joia1_argmax"] = f"{ok}/{tot}"
    out["A4_joia1_dmax"] = dmax
    out["A4_n_restarts_set"] = sorted({len(d.get("acqf_todos_restarts") or []) for d in dec})
    out["A4_alpha_min"] = min(float(d["acqf_escolhido"]) for d in dec if d.get("acqf_escolhido") is not None)
    out["A4_alpha_max"] = max(float(d["acqf_escolhido"]) for d in dec if d.get("acqf_escolhido") is not None)
    out["A4_alpha_neg"] = sum(1 for d in dec if (d.get("acqf_escolhido") or 0) < 0)
    out["A4_n_baseline"] = [d.get("n_baseline") for d in dec[:5]]
    out["A4_caminhos"] = pd.Series([d.get("caminho") for d in dec]).value_counts().to_dict()

# ---------- 1) e 3) ----------
r1 = pd.read_parquet(f"{B}__real.parquet")
r3 = pd.read_parquet(f"{B}__surrogate.parquet")
r4 = pd.read_parquet(f"{B}__timing.parquet")
r2 = pd.read_parquet(f"{B}__pop.parquet")
out["A5_1_linhas"] = len(r1)
out["A5_1_cols"] = list(r1.columns)
out["A5_1_fases"] = r1["fase"].value_counts().to_dict() if "fase" in r1 else None
out["A5_3_linhas"] = len(r3)
out["A5_3_cols"] = list(r3.columns)
out["A5_3_regimes"] = r3["regime"].value_counts().to_dict() if "regime" in r3 else None
out["A5_4_linhas"] = len(r4)
out["A5_4_cols"] = list(r4.columns)
out["A5_2_blocos"] = int(r2["geracao"].nunique()) if "geracao" in r2 else None

# QUERY-JOIA 2: linha marcada == ultima das 10; |dx| 3x1 == 0
on = r3[r3["regime"] == "online"].copy()
xcols = [c for c in r3.columns if c.startswith("x") and c[1:].isdigit()]
out["A5_xcols"] = xcols
marc = on[on["real_solution_id"].notna()]
out["A6_marcadas"] = len(marc)
pos_ultima = 0
for g, blk in on.groupby("geracao"):
    idx = np.where(blk["real_solution_id"].notna().values)[0]
    if len(idx) == 1 and idx[0] == len(blk) - 1:
        pos_ultima += 1
out["A6_ultima_das_10"] = f"{pos_ultima}/{on['geracao'].nunique()}"
r1i = r1.set_index("solution_id")
dmx = 0.0
for _, row in marc.iterrows():
    sid = int(row["real_solution_id"])
    if sid in r1i.index:
        a = np.array([row[c] for c in xcols], dtype=np.float64)
        b = np.array([r1i.loc[sid, c] for c in xcols], dtype=np.float64)
        dmx = max(dmx, float(np.max(np.abs(a - b))))
out["A6_dx_3x1_max"] = dmx
out["A6_sonda_real_sid_nula"] = int(r3[r3["regime"] == "sonda"]["real_solution_id"].notna().sum())
out["A6_sigma_min"] = float(np.nanmin(r3[[c for c in r3.columns if c.startswith("sigma")]].values))
out["A6_sigma_nan"] = int(np.isnan(r3[[c for c in r3.columns if c.startswith("sigma")]].values).sum())

print(json.dumps(out, indent=1, default=str))
