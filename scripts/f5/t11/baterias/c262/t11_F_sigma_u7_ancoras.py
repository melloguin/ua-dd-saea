#!/usr/bin/env python
"""T11/c262 — BATERIA F: (1) DIFF do sigma_dict s42 x smoke T11 (a regra I-12);
(2) U7 invariante de timing re-medido na s42; (3) as 4 ancoras direcionais.
"""
import glob, json, os
import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262"
SM = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/"
      "experiments/main/c262/exp_main_c262_MMF1_0.manifest.json")

s42m = json.load(open(glob.glob(f"{ROOT}/MMF1/42/*.manifest.json")[0]))
smk = json.load(open(SM))
a, b = s42m["sigma_dict"], smk["sigma_dict"]
print("=== sigma_dict: s42 x smoke T11 ===")
print("chaves NOVAS no T11:", sorted(set(b) - set(a)))
print("chaves PERDIDAS:", sorted(set(a) - set(b)))
for k in sorted(set(a) & set(b)):
    if a[k] != b[k]:
        print(f"  MUDOU [{k}]:\n    s42  : {a[k]}\n    T11  : {b[k]}")
for k in sorted(set(b) - set(a)):
    print(f"  NOVA  [{k}]: {b[k]}")

print()
print("=== U7 invariante de timing (s42, 21 celulas) ===")
inv1 = inv1t = inv2 = inv2t = fp = 0
sonda_zero_fora = sonda_pos_dentro = 0
for p in sorted(os.listdir(ROOT)):
    d = f"{ROOT}/{p}/42"
    if not os.path.isdir(d):
        continue
    g = glob.glob(f"{d}/*.manifest.json")
    if not g:
        continue
    B = g[0][: -len(".manifest.json")]
    t = pd.read_parquet(f"{B}__timing.parquet")
    recs = [json.loads(l) for l in open(f"{B}.jsonl") if l.strip()]
    ger_sonda = {int(r.get("geracao") or r.get("it"))
                 for r in recs if r.get("rec") == "sonda"}
    for _, row in t.iterrows():
        fb = row.tempo_fit_s + row.tempo_busca_s
        inv1t += 1
        inv1 += (fb <= row.tempo_geracao_s)
        tem = int(row.geracao) in ger_sonda
        viola = (fb + row.tempo_pred_sonda_s) > row.tempo_geracao_s
        if tem:
            inv2t += 1
            inv2 += viola
            sonda_pos_dentro += (row.tempo_pred_sonda_s > 0)
        else:
            fp += viola
            sonda_zero_fora += (row.tempo_pred_sonda_s == 0)
print(f"inv-1 (fit+busca <= ger): {inv1}/{inv1t}")
print(f"inv-2 (com sonda estoura): {inv2}/{inv2t} | falsos-positivos fora: {fp}")
print(f"tempo_pred_sonda_s > 0 dentro: {sonda_pos_dentro}/{inv2t} | "
      f"== 0 fora: {sonda_zero_fora}/{inv1t - inv2t}")

print()
print("=== ANCORAS DIRECIONAIS (IGD+ main, F5.2c) ===")
m = pd.read_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/"
                "metricas_finais_f52c.csv")
m = m[m.exp == "main"]
piv = m.pivot_table(index="problema", columns="alg", values="igd_plus")
for rival, sentido in [("c154", "vs entropia (JES) — §9.1 PESMO/MESMO piores"),
                       ("e81", "vs Thompson (qPOTS) — §9.1 TS-TCH no meio"),
                       ("b1", "vs ParEGO — Fig. 3/15a"),
                       ("b3", "vs HV-greedy c/ diversidade (DGEMO~KRVEA) — H.7")]:
    if rival not in piv.columns:
        print(f"  {rival}: ausente")
        continue
    sub = piv[["c262", rival]].dropna()
    win = int((sub.c262 < sub[rival]).sum())
    print(f"  c262 x {rival:5s}: melhor em {win}/{len(sub)}  ({sentido})")
