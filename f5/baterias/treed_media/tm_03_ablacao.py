#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 03: A ANÁLISE-CHAVE — ablação c311 × treed_media no tier big.
Isola o VALOR dos GPs locais: MESMA especificação de árvore, MESMO dataset, MESMOS 20.000
pontos de sonda; diferença = os GPs entram (c311) ou não (treed_media).
Eixos: (a) sonda WAPE/corr por objetivo · (b) quantização de μ (folhas × GP contínuo) ·
(c) σ-NaN · (d) endpoint ⑦ (fantasia + IGD+/HV) · (e) custo (wall/fit/busca) · (f) trajetórias.
Saídas: tm_ablacao.csv, tm_ablacao_sonda.csv, tm_trajetorias.csv
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.join(REPO, "f5/baterias/treed_media")
sys.path.insert(0, REPO); os.chdir(REPO)
from src import metrics as MX  # noqa: E402

DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}
PROBS = ["ZDT4", "ZDT1", "DTLZ2", "MMF16_20", "WFG9"]
REPROVADA = ("sweep-big-mvns", "c311", "MMF16_20")


def stem_de(alg, label):
    pasta = os.path.join(RES, alg, label, "42")
    b = [x for x in glob.glob(os.path.join(pasta, "*.manifest.json")) if "__final" not in x]
    return b[0][: -len(".manifest.json")] if b else None


def perfil(alg, label, prob):
    """Perfil de mecanismo de UMA célula offline treed-família."""
    st = stem_de(alg, label)
    if st is None:
        return None
    D, M = DM[prob]
    mf = json.load(open(st + ".manifest.json"))
    d3 = pd.read_parquet(st + "__surrogate.parquet")
    s = d3[d3.regime == "sonda"]
    b = d3[d3.regime == "offline"]
    out = dict(alg=alg, label=label, problema=prob, D=D, M=M)
    out["wall_s"] = mf["timing"]["tempo_total_s"]
    out["fit_s"] = mf["timing"]["tempo_fit_surrogate_s"]
    out["busca_s"] = mf["timing"]["tempo_busca_s"]
    out["sonda_s"] = mf["timing"]["tempo_pred_sonda_s"]
    out["n_fit_series"] = len(mf.get("fit_series") or [])
    out["n_ger"] = mf["n_geracoes"]
    out["n_linhas_3"] = len(d3); out["n_busca"] = len(b); out["n_sonda"] = len(s)
    sg = [f"sigma_{j}" for j in range(M)]
    out["sigma_nan_pct_sonda"] = round(100 * float(s[sg].isna().values.mean()), 2)
    out["sigma_nan_pct_busca"] = round(100 * float(b[sg].isna().values.mean()), 2)
    out["sigma_nan_pct_total"] = round(100 * float(d3[sg].isna().values.mean()), 2)
    # bloco de sonda: c311 tem 2 (20000 cada) — usar o PRIMEIRO
    s0 = s.iloc[:20000]
    dist = [int(s0[f"mu_{j}"].nunique()) for j in range(M)]
    out["mu_distintos_sonda_max"] = max(dist)
    out["mu_distintos_sonda_min"] = min(dist)
    out["quantizacao_pct"] = round(100 * (1 - max(dist) / 20000), 3)
    out["teto_folhas"] = 50000 // (10 * D)
    out["n_blocos_sonda"] = int(round(len(s) / 20000))
    out["modelo_flags"] = "|".join(sorted(d3.modelo_flag.unique()))
    # ⑦
    d7 = pd.read_parquet(st + "__final.parquet")
    nd = d7.nd_pos_real.values.astype(bool)
    F = d7[[f"f{j}" for j in range(M)]].values.astype(np.float64)
    out["n_final"] = len(d7); out["nd_pos_real"] = int(nd.sum())
    out["fantasia"] = round(float(nd.mean()), 4)
    try:
        mm = MX.metrics_of_set(F[nd] if nd.any() else F, prob)
        out["igd_plus_c7"] = round(float(mm["igd_plus"]), 6)
        out["hv_c7"] = round(float(mm["hv"]), 6)
    except Exception:
        out["igd_plus_c7"] = np.nan; out["hv_c7"] = np.nan
    return out


linhas = []
for dist in ("lhs", "mvns"):
    for p in PROBS:
        label = f"swap_big-{dist}_{p}"
        for alg in ("c311", "treed_media"):
            if (f"sweep-big-{dist}", alg, p) == REPROVADA:
                continue
            r = perfil(alg, label, p)
            if r:
                r["dist"] = dist
                linhas.append(r)
                print("ok", alg, label, flush=True)
A = pd.DataFrame(linhas)
A.to_csv(os.path.join(OUT, "tm_ablacao.csv"), index=False)

# ---------- sonda pareada (pré-computada F5.2e) ----------
S = pd.read_csv(os.path.join(REPO, "f5/sonda_f52e.csv"))
S = S[(S.exp.str.startswith("sweep-big")) & (S.alg.isin(["c311", "treed_media"]))]
S = S[S.bloco == "blk0"]
piv = S.pivot_table(index=["exp", "problema", "obj"], columns="alg",
                    values=["wape", "corr", "cobertura95"], aggfunc="first").reset_index()
piv.columns = ["_".join([c for c in col if c]).strip() for col in piv.columns.values]
piv["wape_delta_pct"] = 100 * (piv["wape_treed_media"] - piv["wape_c311"]) / piv["wape_c311"]
piv["corr_delta"] = piv["corr_treed_media"] - piv["corr_c311"]
piv.to_csv(os.path.join(OUT, "tm_ablacao_sonda.csv"), index=False)

# ---------- trajetórias (20 checkpoints) ----------
tr = []
for dist in ("lhs", "mvns"):
    for p in PROBS:
        for alg in ("c311", "treed_media"):
            f = os.path.join(REPO, f"f5/trajetorias/sweep-big-{dist}_{alg}_{p}_42.json")
            if not os.path.exists(f):
                continue
            j = json.load(open(f))
            ig = [x["igd_plus"] for x in j]
            viol = sum(1 for a, b in zip(ig, ig[1:]) if b > a + 1e-12)
            tr.append(dict(alg=alg, dist=dist, problema=p, n_ckpt=len(ig),
                           viol_monotonia=viol, igd_ini=ig[0], igd_fim=ig[-1],
                           fe_ini=j[0]["fe"], fe_fim=j[-1]["fe"],
                           nd_fim=j[-1]["n_nd"],
                           serie=";".join(f"{v:.5g}" for v in ig)))
T = pd.DataFrame(tr)
T.to_csv(os.path.join(OUT, "tm_trajetorias.csv"), index=False)

# identidade das trajetórias c311 × treed (prova do empate D69)
ident = []
for dist in ("lhs", "mvns"):
    for p in PROBS:
        a = T[(T.alg == "c311") & (T.dist == dist) & (T.problema == p)]
        b = T[(T.alg == "treed_media") & (T.dist == dist) & (T.problema == p)]
        if len(a) and len(b):
            ident.append(dict(dist=dist, problema=p,
                              serie_identica=bool(a.serie.iloc[0] == b.serie.iloc[0])))
pd.DataFrame(ident).to_csv(os.path.join(OUT, "tm_traj_identidade.csv"), index=False)
print(pd.DataFrame(ident).to_string())
print("fim")
