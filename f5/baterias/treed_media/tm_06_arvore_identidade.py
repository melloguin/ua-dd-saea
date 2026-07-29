#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 06: a ÁRVORE do treed_media É a mesma do c311?
Resolve empiricamente o caveat DI-28 ("mesma ESPECIFICAÇÃO, treino INDEPENDENTE —
NUNCA 'idêntico'") e mede o CONFUNDIMENTO da ablação: se as árvores forem idênticas, a
diferença c311×treed é atribuível SÓ aos GPs locais.

Teste: join POSICIONAL dos 20.000 pontos da sonda (mesma régua §17.2.2, mesmo x_hash).
Nos pontos em que o c311 tem sigma_j = NaN (folha SEM GP), o μ_j do c311 É a média da
folha — exatamente o que o treed_media prediz SEMPRE. Se as árvores coincidem, μ deve
bater bit-a-bit nesses pontos.
Saída: tm_arvore_identidade.csv
"""
import glob, json, os
import numpy as np
import pandas as pd

RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"
DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}


def stem(alg, label):
    b = [x for x in glob.glob(os.path.join(RES, alg, label, "42", "*.manifest.json"))
         if "__final" not in x]
    return b[0][: -len(".manifest.json")] if b else None


linhas = []
for dist in ("lhs", "mvns"):
    for prob in ("ZDT4", "ZDT1", "DTLZ2", "MMF16_20", "WFG9"):
        label = f"swap_big-{dist}_{prob}"
        if (dist, prob) == ("mvns", "MMF16_20"):
            continue  # c311 REPROVADA-F5.1 (aborto gpy_bfgs_linalg, 0 blocos de sonda)
        sc, st = stem("c311", label), stem("treed_media", label)
        if sc is None or st is None:
            continue
        D, M = DM[prob]
        mc = json.load(open(sc + ".manifest.json"))
        mt = json.load(open(st + ".manifest.json"))
        r = dict(dist=dist, problema=prob, D=D, M=M)
        r["mesmo_dataset_hash"] = (mc["doe_hash"] == mt["doe_hash"])
        r["mesma_sonda_x_hash"] = (mc["sonda"]["x_hash"] == mt["sonda"]["x_hash"])
        r["msl_c311"] = mc.get("params", {}).get("min_samples_leaf")
        r["msl_treed"] = mt.get("params", {}).get("min_samples_leaf")
        dc = pd.read_parquet(sc + "__surrogate.parquet", columns=None)
        dt_ = pd.read_parquet(st + "__surrogate.parquet")
        sC = dc[dc.regime == "sonda"].reset_index(drop=True).iloc[:20000]
        sT = dt_[dt_.regime == "sonda"].reset_index(drop=True)
        xs = [f"x{i}" for i in range(D)]
        r["join_posicional_X_identico"] = bool((sC[xs].values == sT[xs].values).all())
        tot_sem_gp = 0; tot_igual = 0
        for j in range(M):
            semgp = sC[f"sigma_{j}"].isna().values
            muC = sC[f"mu_{j}"].values[semgp]
            muT = sT[f"mu_{j}"].values[semgp]
            ig = int((muC == muT).sum())
            r[f"obj{j}_n_sem_gp"] = int(semgp.sum())
            r[f"obj{j}_pct_sem_gp"] = round(100 * float(semgp.mean()), 2)
            r[f"obj{j}_n_mu_identico"] = ig
            r[f"obj{j}_pct_mu_identico"] = round(100 * ig / max(int(semgp.sum()), 1), 3)
            d = np.abs(muC.astype(np.float64) - muT.astype(np.float64))
            r[f"obj{j}_maxabs_dmu"] = float(d.max()) if len(d) else np.nan
            r[f"obj{j}_folhas_c311_semgp"] = int(pd.Series(muC).nunique())
            r[f"obj{j}_folhas_treed_nesses_pts"] = int(pd.Series(muT).nunique())
            tot_sem_gp += int(semgp.sum()); tot_igual += ig
        r["TOTAL_pts_sem_gp"] = tot_sem_gp
        r["TOTAL_mu_identico"] = tot_igual
        r["TOTAL_pct_identico"] = round(100 * tot_igual / max(tot_sem_gp, 1), 3)
        # alfabeto de folhas (todos os pontos, não só os sem GP)
        for j in range(M):
            setC = set(np.unique(sC[f"mu_{j}"].values[sC[f"sigma_{j}"].isna().values]))
            setT = set(np.unique(sT[f"mu_{j}"].values))
            r[f"obj{j}_alfabeto_c311_em_treed_pct"] = round(100 * len(setC & setT) / max(len(setC), 1), 2)
        linhas.append(r)
        print("ok", label, flush=True)

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "tm_arvore_identidade.csv"), index=False)
print(df[["dist", "problema", "mesmo_dataset_hash", "mesma_sonda_x_hash",
          "join_posicional_X_identico", "TOTAL_pts_sem_gp", "TOTAL_mu_identico",
          "TOTAL_pct_identico"]].to_string())
