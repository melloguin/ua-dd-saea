#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 08: o motor BUSCA de fato? (comportamento no espaço do
surrogate FIXO ao longo das 1.000 gerações). Métrica interna: média de Σμ_j por geração
(minimização) + nº de pontos não-dominados em μ na geração 1 × 1000.
Complementa: distância entre o front do MODELO (μ da última geração) e a REALIDADE (f da ⑦).
Saída: tm_convergencia.csv
"""
import glob, os
import numpy as np
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"
DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}


def nd_count(F):
    n = len(F); dom = np.zeros(n, bool)
    for i in range(n):
        dom[i] = bool((((F <= F[i]).all(1)) & ((F < F[i]).any(1))).any())
    return int((~dom).sum())


L = []
for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
    label = os.path.basename(d)
    prob = label.split("_", 1)[1].split("_", 1)[1]
    D, M = DM[prob]
    stem = [b for b in glob.glob(os.path.join(d, "42", "*.manifest.json")) if "__final" not in b][0]
    stem = stem[: -len(".manifest.json")]
    d3 = pd.read_parquet(stem + "__surrogate.parquet")
    b = d3[d3.regime == "offline"].copy()
    b["g"] = b.geracao.astype(int)
    mus = [f"mu_{j}" for j in range(M)]
    b["_soma"] = b[mus].sum(axis=1)
    ser = b.groupby("g")["_soma"].mean()
    r = dict(label=label, problema=prob, D=D, M=M)
    r["soma_mu_ger1"] = float(ser.loc[1]); r["soma_mu_ger1000"] = float(ser.loc[1000])
    r["soma_mu_min"] = float(ser.min()); r["ger_do_min"] = int(ser.idxmin())
    r["melhora_pct"] = round(100 * (ser.loc[1] - ser.loc[1000]) / abs(ser.loc[1]), 2)
    r["monotona_decrescente_pct"] = round(100 * float((ser.diff().dropna() <= 1e-9).mean()), 2)
    # 20 checkpoints da curva interna
    ck = [int(round(x)) for x in np.linspace(1, 1000, 20)]
    r["curva_20ck"] = ";".join(f"{ser.loc[g]:.5g}" for g in ck)
    g1 = b[b.g == 1][mus].values.astype(np.float64)
    g1000 = b[b.g == 1000][mus].values.astype(np.float64)
    r["pop_ger1"] = len(g1); r["pop_ger1000"] = len(g1000)
    r["nd_mu_ger1"] = nd_count(g1); r["nd_mu_ger1000"] = nd_count(g1000)
    # o front do MODELO na última geração × a realidade (⑦)
    d7 = pd.read_parquet(stem + "__final.parquet")
    F = d7[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    r["nd_real_da_ultima_pop"] = int(d7.nd_pos_real.sum())
    r["colapso_nd"] = round(r["nd_real_da_ultima_pop"] / max(r["nd_mu_ger1000"], 1), 4)
    L.append(r)
    print("ok", label, flush=True)

df = pd.DataFrame(L)
df.to_csv(os.path.join(OUT, "tm_convergencia.csv"), index=False)
pd.set_option("display.width", 260)
print(df.drop(columns=["curva_20ck"]).to_string())
