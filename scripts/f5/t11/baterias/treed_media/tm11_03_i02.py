#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 03: o I-02 (`tempo_aval_real_s`) no OFFLINE.
O comentario do codigo (treed_media.py:520-524) diz NULL; o dado diz nao. READ-ONLY."""
import json, os, glob
import numpy as np, pandas as pd

SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments"
S42R = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.dirname(os.path.abspath(__file__))

rows = []
for mf in sorted(glob.glob(os.path.join(SMK, "*", "*", "*.manifest.json"))):
    if mf.endswith("__final.manifest.json"):
        continue
    m = json.load(open(mf))
    t = m.get("timing", {})
    rows.append(dict(corpus="smokeT11", exp=m.get("exp"), alg=m.get("alg"),
                     prob=m.get("problema"), sem=m.get("semente"),
                     regime=m.get("regime"), maxfe=m.get("maxfe"),
                     n_ds=m.get("n_dataset", m.get("maxfe")),
                     t_aval_real=t.get("tempo_aval_real_s"),
                     t_total=t.get("tempo_total_s"),
                     us_por_fe=(1e6 * t["tempo_aval_real_s"] / m["maxfe"]
                                if t.get("tempo_aval_real_s") not in (None, 0.0) and m.get("maxfe")
                                else None)))
df = pd.DataFrame(rows).sort_values(["regime", "alg"])
pd.set_option("display.width", 220, "display.max_columns", 30)
print("=== smoke T11 (11 celulas Python) — tempo_aval_real_s ===")
print(df.to_string(index=False))
print("\nOFFLINE: t_aval_real NULL? ->",
      df[df.regime == "offline"][["alg", "t_aval_real"]].to_dict("records"))

# s42: como era ANTES, em TODOS os offline
rows2 = []
for alg in ["treed_media", "c311", "moead_media", "b5r", "b5m", "e103"]:
    d = os.path.join(S42R, alg)
    if not os.path.isdir(d):
        continue
    for lab in sorted(os.listdir(d)):
        for mf in glob.glob(os.path.join(d, lab, "42", "*_42.manifest.json")):
            m = json.load(open(mf))
            if m.get("regime") != "offline":
                continue
            rows2.append(dict(alg=alg, label=lab,
                              t_aval_real=m["timing"].get("tempo_aval_real_s"),
                              maxfe=m.get("maxfe")))
d2 = pd.DataFrame(rows2)
print("\n=== s42 (PRE-T11) — tempo_aval_real_s nos offline ===")
print(d2.groupby("alg").t_aval_real.describe()[["count", "min", "max"]].to_string())
print("zeros exatos: %d de %d" % (int((d2.t_aval_real == 0.0).sum()), len(d2)))
d2.to_csv(os.path.join(OUT, "tm11_i02_s42_offline.csv"), index=False)
df.to_csv(os.path.join(OUT, "tm11_i02_smoke.csv"), index=False)
