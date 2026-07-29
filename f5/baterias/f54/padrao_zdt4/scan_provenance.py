#!/usr/bin/env python
"""F5.4 - varredura de proveniencia nas 666 celulas. READ-ONLY."""
import json, os, sys, datetime as dt
from pathlib import Path

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/padrao_zdt4")

def parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

rows = []
cells = sorted([p for p in ROOT.glob("*/*/42") if p.is_dir()])
print(f"celulas: {len(cells)}", file=sys.stderr)

for cell in cells:
    alg = cell.parts[-3]
    label = cell.parts[-2]
    rec = {"alg": alg, "label": label, "dir": str(cell)}
    files = sorted([f for f in cell.iterdir() if f.is_file()])
    rec["n_files"] = len(files)
    mt = {}
    for f in files:
        st = f.stat()
        key = f.name
        # camada
        if key.endswith(".jsonl"):
            k = "jsonl"
        elif key.endswith("__final.manifest.json"):
            k = "final_manifest"
        elif key.endswith(".manifest.json"):
            k = "manifest"
        elif key.endswith("__real.parquet"):
            k = "real"
        elif key.endswith("__pop.parquet"):
            k = "pop"
        elif key.endswith("__surrogate.parquet"):
            k = "surrogate"
        elif key.endswith("__timing.parquet"):
            k = "timing"
        elif key.endswith("__final.parquet"):
            k = "final"
        else:
            k = "outro:" + key
        mt[k] = st.st_mtime
        rec["size_" + k] = st.st_size
        rec["nlink_" + k] = st.st_nlink
    for k, v in mt.items():
        rec["mtime_" + k] = v
    if mt:
        rec["mtime_min"] = min(mt.values())
        rec["mtime_max"] = max(mt.values())
        rec["mtime_spread_s"] = rec["mtime_max"] - rec["mtime_min"]

    # ---- manifest
    man = [f for f in files if f.name.endswith(".manifest.json") and not f.name.endswith("__final.manifest.json")]
    if man:
        try:
            m = json.loads(man[0].read_text())
        except Exception as e:
            m = {}
            rec["manifest_erro"] = str(e)
        rec["run_id"] = m.get("run_id")
        rec["exp"] = m.get("exp")
        rec["status"] = m.get("status")
        rec["n_retries"] = m.get("n_retries")
        rec["n_geracoes"] = m.get("n_geracoes")
        rec["fe_final"] = m.get("fe_final")
        rec["maxfe"] = m.get("maxfe")
        rec["motivo_parada"] = m.get("motivo_parada")
        rec["created_at"] = m.get("created_at")
        rec["updated_at"] = m.get("updated_at")
        ca, ua = parse_ts(m.get("created_at")), parse_ts(m.get("updated_at"))
        if ca and ua:
            rec["upd_minus_created_s"] = (ua - ca).total_seconds()
        env = m.get("env") or {}
        rec["env_exec"] = env.get("executable")
        rec["env_python"] = env.get("python")
        paths = (m.get("paths") or {}).get("local") or {}
        rec["path_jsonl"] = paths.get("jsonl")
        rec["path_real"] = paths.get("real")
        rec["bucket"] = (m.get("paths") or {}).get("bucket")
        rec["upload_status"] = json.dumps(m.get("upload_status")) if m.get("upload_status") else None
        tim = m.get("timing") or {}
        rec["tempo_total_s"] = tim.get("tempo_total_s")
        rec["tempo_total_despachante_s"] = tim.get("tempo_total_despachante_s")
        fs = m.get("fit_series") or []
        rec["n_fit_series"] = len(fs)

    # ---- final manifest
    fman = [f for f in files if f.name.endswith("__final.manifest.json")]
    if fman:
        try:
            fm = json.loads(fman[0].read_text())
            rec["final_n"] = fm.get("n_final")
            rec["final_created_at"] = fm.get("created_at") or fm.get("gerado_em")
            rec["final_keys"] = ",".join(sorted(fm.keys()))[:200]
        except Exception as e:
            rec["final_erro"] = str(e)

    # ---- jsonl
    jl = [f for f in files if f.name.endswith(".jsonl")]
    if jl:
        counts = {}
        ts_all = []
        hdr_ts, ftr_ts = [], []
        ftr_kinds = []
        bad = 0
        nlines = 0
        with open(jl[0], "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                nlines += 1
                try:
                    o = json.loads(line)
                except Exception:
                    bad += 1
                    continue
                r = o.get("rec")
                counts[r] = counts.get(r, 0) + 1
                t = parse_ts(o.get("ts"))
                if t:
                    ts_all.append(t)
                if r == "header":
                    hdr_ts.append(o.get("ts"))
                    if o.get("D") is None:
                        counts["__header_null"] = counts.get("__header_null", 0) + 1
                if r == "footer":
                    ftr_ts.append(o.get("ts"))
                    ftr_kinds.append((o.get("tempo_total_s"), o.get("fe_final"), o.get("status")))
        rec["jsonl_linhas"] = nlines
        rec["jsonl_bad"] = bad
        rec["n_header"] = counts.get("header", 0)
        rec["n_footer"] = counts.get("footer", 0)
        rec["n_header_null"] = counts.get("__header_null", 0)
        rec["n_fit"] = counts.get("fit", 0)
        rec["n_decision"] = counts.get("decision", 0)
        rec["n_sonda"] = counts.get("sonda", 0)
        rec["n_guard"] = counts.get("guard", 0)
        rec["recs"] = json.dumps({k: v for k, v in sorted(counts.items())})
        if ts_all:
            rec["ts_min"] = ts_all[0].isoformat()
            rec["ts_max"] = max(ts_all).isoformat()
            rec["ts_first"] = ts_all[0].isoformat()
            rec["ts_last"] = ts_all[-1].isoformat()
            rec["ts_span_s"] = (max(ts_all) - min(ts_all)).total_seconds()
            # retrocessos
            back = 0
            maxback = 0.0
            gaps = []
            for i in range(1, len(ts_all)):
                d = (ts_all[i] - ts_all[i - 1]).total_seconds()
                if d < -1e-6:
                    back += 1
                    maxback = max(maxback, -d)
                gaps.append(d)
            rec["n_retro"] = back
            rec["max_retro_s"] = maxback
            rec["max_gap_s"] = max(gaps) if gaps else 0.0
            # janelas (cluster por gap > 900 s)
            jan = 1
            for d in gaps:
                if d > 900:
                    jan += 1
            rec["n_janelas_900s"] = jan
        rec["hdr_ts"] = json.dumps(hdr_ts[:3] + (["..."] if len(hdr_ts) > 4 else []) + (hdr_ts[-1:] if len(hdr_ts) > 3 else []))
        rec["ftr_ts_last"] = ftr_ts[-1] if ftr_ts else None
        rec["ftr_ts_first"] = ftr_ts[0] if ftr_ts else None
    rows.append(rec)

# escreve
keys = []
for r in rows:
    for k in r:
        if k not in keys:
            keys.append(k)
import csv
with open(OUT / "scan_cells.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("ok", len(rows), file=sys.stderr)
