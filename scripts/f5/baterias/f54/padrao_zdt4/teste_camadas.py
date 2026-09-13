#!/usr/bin/env python
"""Bateria de coerencia entre camadas nas 666 celulas. READ-ONLY.
T1  ①.nrows == manifest.fe_final
T2  ④.nrows == manifest.n_geracoes (quando ④ e por geracao)
T3  ⑦.nrows == cardinalidade modal do config
T4  jsonl.n_decision vs manifest.n_geracoes
T5  footer.fe_final == manifest.fe_final
T6  ③ geracao maxima == manifest.n_geracoes-1 (ou n_geracoes)
"""
import os, glob, csv, json, sys, collections
import numpy as np
import pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/padrao_zdt4/teste_camadas.csv"

rows = []
for cell in sorted(glob.glob(os.path.join(ROOT, "*", "*", "42"))):
    alg, label = cell.split(os.sep)[-3], cell.split(os.sep)[-2]
    r = {"alg": alg, "label": label}
    g = lambda pat: (glob.glob(os.path.join(cell, pat)) or [None])[0]
    man = g("*[!_]*.manifest.json")
    man = [p for p in glob.glob(os.path.join(cell, "*.manifest.json")) if not p.endswith("__final.manifest.json")]
    man = man[0] if man else None
    m = json.load(open(man)) if man else {}
    r["fe_final_man"] = m.get("fe_final"); r["n_ger_man"] = m.get("n_geracoes")
    for tag, pat in [("real", "*__real.parquet"), ("pop", "*__pop.parquet"),
                     ("sur", "*__surrogate.parquet"), ("tim", "*__timing.parquet"),
                     ("fin", "*__final.parquet")]:
        p = g(pat)
        if p:
            try:
                pf = pq.ParquetFile(p)
                r["n_" + tag] = pf.metadata.num_rows
            except Exception as e:
                r["n_" + tag] = "ERRO"
    # jsonl footer
    jl = g("*.jsonl")
    if jl:
        ndec = 0; ftr = []
        with open(jl) as fh:
            for line in fh:
                line = line.strip()
                if not line: continue
                try: o = json.loads(line)
                except Exception: continue
                if o.get("rec") == "decision": ndec += 1
                if o.get("rec") == "footer": ftr.append(o)
        r["n_decision"] = ndec
        fe = [f.get("fe_final") for f in ftr if f.get("fe_final") is not None]
        r["footer_fe_final"] = fe[0] if fe else None
    # geracao max da (3)
    p = g("*__surrogate.parquet")
    if p:
        try:
            sch = pq.ParquetFile(p).schema_arrow.names
            if "geracao" in sch:
                t = pq.read_table(p, columns=["geracao"]).to_pandas()
                r["ger_max_sur"] = int(t.geracao.max()); r["ger_min_sur"] = int(t.geracao.min())
        except Exception:
            pass
    rows.append(r)

keys = []
for x in rows:
    for k in x:
        if k not in keys: keys.append(k)
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
print("ok", len(rows), file=sys.stderr)
