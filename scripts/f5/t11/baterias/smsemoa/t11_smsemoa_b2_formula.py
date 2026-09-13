#!/usr/bin/env python
"""T11 · smsemoa · BATERIA 2 — re-medição da fórmula `geracoes_derivadas` da T11.

Claim auditado (src/experiment.m:2516-2527, gravado em 100% dos manifestos dos
4 pisos): "Melhor aproximacao MEDIDA: floor((20D + n_dup) / (2*floor(N_efetivo/2))),
que acerta 103/112 celulas da s42; ... A string antiga ('20D / N_efetivo') acerta
2/112 e a formula com ceil do plano F5 acerta 0/112."

READ-ONLY: só lê manifestos + ⑥. Não roda nada.
"""
import json, glob, os
import numpy as np, pandas as pd

DX = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/smsemoa"
PISOS = ["nsga2", "nsga3", "moead", "smsemoa"]

rows = []
for alg in PISOS:
    for mp in sorted(glob.glob(f"{DX}/**/{alg}/**/*.manifest.json", recursive=True)):
        if "_baseline_pre_retrofit" in mp:
            continue
        man = json.load(open(mp))
        jp = mp.replace(".manifest.json", ".jsonl")
        if not os.path.exists(jp):
            continue
        recs = [json.loads(l) for l in open(jp) if l.strip()]
        hdr = [x for x in recs if x["rec"] == "header"][0]
        gens = [x for x in recs if x["rec"].endswith("_gen")]
        ch = [x for x in recs if x["rec"] == "guard" and x.get("name") == "cache_hit"]
        D, M = hdr["D"], hdr["M"]
        init = 11 * D - 1
        Nef = man["params"]["N_efetivo"]
        ch_init = [g for g in ch if g["fe"] == init]
        ndup = len(ch) - len(ch_init)          # duplicatas da EVOLUÇÃO
        ndup_tot = len(ch)                     # todos os cache-hits
        real = man["n_geracoes"]
        par = 2 * (Nef // 2)
        fe1 = gens[0]["fe"] if gens else None
        r = dict(alg=alg, problema=man["problema"], semente=man["semente"], D=D, M=M,
                 N_ef=Nef, par=par, n_ger_real=real, cache_total=ndup_tot,
                 cache_init=len(ch_init), n_dup_evo=ndup,
                 fe_g1=fe1, g1_eh_snapshot=(fe1 == init),
                 f_T11_dupevo=int(np.floor((20 * D + ndup) / par)),
                 f_T11_duptot=int(np.floor((20 * D + ndup_tot) / par)),
                 f_antiga=int(20 * D / Nef),
                 f_ceilF5=int(np.ceil((20 * D + ndup) / Nef)),
                 f_D_mais_1=int(20 * D / Nef) + 1)
        for k in ["f_T11_dupevo", "f_T11_duptot", "f_antiga", "f_ceilF5", "f_D_mais_1"]:
            r["ok_" + k] = (r[k] == real)
        rows.append(r)

df = pd.DataFrame(rows).sort_values(["alg", "semente", "problema"])
df.to_csv(f"{OUT}/t11_b2_formula.csv", index=False)

N = len(df)
print(f"CÉLULAS DE PISO AUDITADAS: {N} (4 pisos; s42 + semente-0 de main)")
print(f"  s42: {(df.semente==42).sum()} · s0: {(df.semente==0).sum()}")
print()
print("=== ACERTO DE CADA FÓRMULA (todas as células) ===")
for k in ["f_T11_dupevo", "f_T11_duptot", "f_antiga", "f_ceilF5", "f_D_mais_1"]:
    print(f"  {k:16s} {df['ok_'+k].sum():3d}/{N}")
print()
print("=== POR PISO (só s42) ===")
s = df[df.semente == 42]
print(s.groupby("alg")[["ok_f_T11_dupevo", "ok_f_T11_duptot", "ok_f_antiga",
                        "ok_f_ceilF5", "ok_f_D_mais_1"]].sum().to_string())
print()
print("=== SMSEMOA s42 detalhe ===")
ss = s[s.alg == "smsemoa"]
print(ss[["problema", "D", "N_ef", "n_dup_evo", "n_ger_real", "f_T11_dupevo",
          "f_antiga", "f_ceilF5", "f_D_mais_1", "g1_eh_snapshot"]].to_string(index=False))
print()
print("g1 é snapshot do DoE (fe == 11D-1) por piso, s42:")
print(s.groupby("alg")["g1_eh_snapshot"].agg(["sum", "count"]).to_string())
