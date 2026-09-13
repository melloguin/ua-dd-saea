#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 07: consolidação (pares da ablação + agregados do relatório).
Saídas: tm_pares_ablacao.csv, tm_resumo.txt
"""
import os
import numpy as np
import pandas as pd

OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"
A = pd.read_csv(os.path.join(OUT, "tm_ablacao.csv"))
S = pd.read_csv(os.path.join(OUT, "tm_ablacao_sonda.csv"))
L = []

c = A[A.alg == "c311"].set_index(["dist", "problema"])
t = A[A.alg == "treed_media"].set_index(["dist", "problema"])
for k in t.index:
    r = dict(dist=k[0], problema=k[1], D=int(t.loc[k, "D"]))
    r["wall_treed_s"] = t.loc[k, "wall_s"]
    r["fit_treed_s"] = t.loc[k, "fit_s"]
    r["ger_treed"] = int(t.loc[k, "n_ger"])
    r["folhas_treed"] = int(t.loc[k, "mu_distintos_sonda_max"])
    r["teto_folhas"] = int(t.loc[k, "teto_folhas"])
    r["folhas_le_teto_treed"] = bool(t.loc[k, "mu_distintos_sonda_max"] <= t.loc[k, "teto_folhas"])
    r["sigmaNaN_treed_pct"] = t.loc[k, "sigma_nan_pct_sonda"]
    r["fantasia_treed"] = t.loc[k, "fantasia"]
    r["igd7_treed"] = t.loc[k, "igd_plus_c7"]
    r["hv7_treed"] = t.loc[k, "hv_c7"]
    if k in c.index:
        r["wall_c311_s"] = c.loc[k, "wall_s"]
        r["fit_c311_s"] = c.loc[k, "fit_s"]
        r["ger_c311"] = int(c.loc[k, "n_ger"])
        r["speedup_wall_x"] = round(c.loc[k, "wall_s"] / t.loc[k, "wall_s"], 2)
        r["speedup_fit_x"] = round(c.loc[k, "fit_s"] / t.loc[k, "fit_s"], 2)
        r["custo_pred_c311_us"] = round(1e6 * c.loc[k, "busca_s"] / c.loc[k, "n_busca"], 2)
        r["custo_pred_treed_us"] = round(1e6 * t.loc[k, "busca_s"] / t.loc[k, "n_busca"], 2)
        r["razao_custo_pred_x"] = round(r["custo_pred_c311_us"] / r["custo_pred_treed_us"], 2)
        r["mu_distintos_c311"] = int(c.loc[k, "mu_distintos_sonda_max"])
        r["c311_folhas_le_teto"] = bool(c.loc[k, "mu_distintos_sonda_max"] <= c.loc[k, "teto_folhas"])
        r["sigmaNaN_c311_pct"] = c.loc[k, "sigma_nan_pct_sonda"]
        r["fantasia_c311"] = c.loc[k, "fantasia"]
        r["igd7_c311"] = c.loc[k, "igd_plus_c7"]
        r["hv7_c311"] = c.loc[k, "hv_c7"]
        r["razao_igd7_treed_sobre_c311"] = round(t.loc[k, "igd_plus_c7"] / c.loc[k, "igd_plus_c7"], 3)
        r["delta_fantasia"] = round(t.loc[k, "fantasia"] - c.loc[k, "fantasia"], 4)
        r["vence_igd7"] = "treed" if t.loc[k, "igd_plus_c7"] < c.loc[k, "igd_plus_c7"] else "c311"
        r["vence_fantasia"] = "treed" if t.loc[k, "fantasia"] > c.loc[k, "fantasia"] else "c311"
        sk = S[(S.exp == "sweep-big-" + k[0]) & (S.problema == k[1])]
        r["wape_delta_pct_med"] = round(float(sk.wape_delta_pct.median()), 2)
        r["wape_delta_pct_max"] = round(float(sk.wape_delta_pct.max()), 2)
    L.append(r)

P = pd.DataFrame(L)
P.to_csv(os.path.join(OUT, "tm_pares_ablacao.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
txt = []
txt.append(P.to_string())
Q = P.dropna(subset=["igd7_c311"])
txt.append("\n--- AGREGADOS (9 pares; exclui mvns/MMF16_20 = c311 REPROVADA-F5.1) ---")
txt.append("speedup wall: mediana %.2fx  faixa %.2f-%.2fx" % (Q.speedup_wall_x.median(), Q.speedup_wall_x.min(), Q.speedup_wall_x.max()))
txt.append("speedup fit : mediana %.2fx  faixa %.2f-%.2fx" % (Q.speedup_fit_x.median(), Q.speedup_fit_x.min(), Q.speedup_fit_x.max()))
txt.append("custo/predicao us: c311 mediana %.2f  treed mediana %.2f  razao mediana %.2fx" % (Q.custo_pred_c311_us.median(), Q.custo_pred_treed_us.median(), Q.razao_custo_pred_x.median()))
txt.append("IGD+ da 7: razao treed/c311 mediana %.3f  faixa %.3f-%.3f ; c311 vence %d/9" % (Q.razao_igd7_treed_sobre_c311.median(), Q.razao_igd7_treed_sobre_c311.min(), Q.razao_igd7_treed_sobre_c311.max(), (Q.vence_igd7 == "c311").sum()))
txt.append("fantasia: c311 mediana %.3f  treed mediana %.3f ; c311 vence %d/9" % (Q.fantasia_c311.median(), Q.fantasia_treed.median(), (Q.vence_fantasia == "c311").sum()))
txt.append("WAPE sonda: delta mediano por celula %s" % list(Q.wape_delta_pct_med.round(1)))
txt.append("folhas treed <= teto: %d/%d ; folhas c311 <= teto: %d/%d" % (P.folhas_le_teto_treed.sum(), len(P), Q.c311_folhas_le_teto.sum(), len(Q)))
txt.append("sigma-NaN sonda: treed %s ; c311 mediana %.2f%% faixa %.2f-%.2f%%" % (sorted(P.sigmaNaN_treed_pct.unique()), Q.sigmaNaN_c311_pct.median(), Q.sigmaNaN_c311_pct.min(), Q.sigmaNaN_c311_pct.max()))
txt.append("\n--- TREED (10 celulas) ---")
txt.append("fantasia mediana %.4f faixa %.4f-%.4f" % (P.fantasia_treed.median(), P.fantasia_treed.min(), P.fantasia_treed.max()))
txt.append("IGD+7 %s" % list(P.igd7_treed))
txt.append("ocupacao do teto de folhas: %s" % list((100 * P.folhas_treed / P.teto_folhas).round(1)))
s = "\n".join(txt)
open(os.path.join(OUT, "tm_resumo.txt"), "w").write(s)
print(s)
