#!/usr/bin/env python
"""bateria3_e81 — sonda RECOMPUTADA pela definicao congelada (§5) e conferida contra
o sonda_f52e.csv oficial; aprendizado e calibracao por bloco; trajetorias de 20
checkpoints; tempo; posicao vs pisos e rivais (com a maquina real).

READ-ONLY. Saidas: e81_sonda_recomputada.csv · e81_sonda_resumo.csv ·
e81_trajetorias.csv · e81_posicao.csv · e81_tempo.csv
"""
import json, os, glob
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")
F5 = os.path.join(REPO, "f5")


def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out


# ── 1. sonda recomputada ──────────────────────────────────────────────────
of = pd.read_csv(f"{F5}/sonda_f52e.csv")
of = of[of["alg"] == "e81"].copy()
of["bloco"] = of["bloco"].astype(int)
rows, resumo = [], []
for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    D = int(man["params"]["qpots_kwargs"]["dim"])
    sur = pd.read_parquet(base + "__surrogate.parquet")
    gab = pd.read_parquet(f"{REPO}/data/sonda/sonda_{prob}.parquet")
    M = len([c for c in gab.columns if c.startswith("f")])
    gf = gab[[f"f{j}" for j in range(M)]].values[:2000].astype(np.float64)
    sd = sur[sur["regime"] == "sonda"]
    blocos = sorted(sd["geracao"].unique())
    for bi, g in enumerate(blocos):
        b = sd[sd["geracao"] == g]
        for j in range(M):
            mu = b[f"mu_{j}"].values.astype(np.float64)
            sg = b[f"sigma_{j}"].values.astype(np.float64)
            fv = gf[:, j]
            err = np.abs(mu - fv)
            wape = err.sum() / np.abs(fv).sum()
            cov = float((err <= 1.96 * sg).mean())
            corr = float(np.corrcoef(mu, fv)[0, 1])
            rows.append(dict(label=lab, exp=exp, problema=prob, bloco=int(g), obj=j,
                             ordem=bi, wape=wape, cobertura95=cov, corr=corr,
                             fe_treino_max=int(b["fe_treino_max"].iloc[0]),
                             sigma_med=float(np.median(sg)), erro_med=float(np.median(err)),
                             n_nan_sigma=int(np.isnan(sg).sum())))
    dfl = pd.DataFrame([r for r in rows if r["label"] == lab])
    for j in range(M):
        s = dfl[dfl["obj"] == j].sort_values("ordem")
        w0, w1 = s["wape"].iloc[0], s["wape"].iloc[-1]
        resumo.append(dict(label=lab, exp=exp, problema=prob, obj=j, n_blocos=len(s),
                           wape_ini=w0, wape_fim=w1, dwape=(w1 - w0) / w0,
                           wape_min=s["wape"].min(), cob_ini=s["cobertura95"].iloc[0],
                           cob_fim=s["cobertura95"].iloc[-1], cob_min=s["cobertura95"].min(),
                           corr_fim=s["corr"].iloc[-1], corr_min=s["corr"].min(),
                           sigma_ini=s["sigma_med"].iloc[0], sigma_fim=s["sigma_med"].iloc[-1]))
    print("sonda ok", lab, flush=True)

rec = pd.DataFrame(rows)
rec.to_csv(f"{OUT}/e81_sonda_recomputada.csv", index=False)
pd.DataFrame(resumo).to_csv(f"{OUT}/e81_sonda_resumo.csv", index=False)

# confronto com o oficial
m = rec.merge(of, left_on=["exp", "problema", "bloco", "obj"],
              right_on=["exp", "problema", "bloco", "obj"], suffixes=("", "_of"))
print("\n== CONFRONTO sonda recomputada x sonda_f52e.csv ==")
print("medicoes pareadas:", len(m), "de", len(rec), "recomputadas /", len(of), "oficiais")
print("  |dWAPE| max :", float((m["wape"] - m["wape_of"]).abs().max()))
print("  |dCOB|  max :", float((m["cobertura95"] - m["cobertura95_of"]).abs().max()))
print("  |dCORR| max :", float((m["corr"] - m["corr_of"]).abs().max()))
print("  n_nan sigma total:", int(rec["n_nan_sigma"].sum()))

# ── 2. trajetorias ────────────────────────────────────────────────────────
tr = []
for exp, prob, lab, d in cells():
    p = f"{F5}/trajetorias/{exp}_e81_{prob}_42.json"
    if not os.path.exists(p):
        tr.append(dict(label=lab, ok=False)); continue
    t = json.load(open(p))
    ck = t if isinstance(t, list) else t.get("checkpoints", t)
    df = pd.DataFrame(ck)
    col_ig = "igd_plus" if "igd_plus" in df.columns else [c for c in df.columns if "igd" in c][0]
    ig = df[col_ig].values.astype(float)
    hv = df["hv"].values.astype(float) if "hv" in df.columns else np.full(len(ig), np.nan)
    nd = df["n_nd"].values if "n_nd" in df.columns else np.full(len(ig), np.nan)
    tr.append(dict(label=lab, exp=exp, problema=prob, ok=True, n_ck=len(ig),
                   viol_igd=int((np.diff(ig) > 1e-12).sum()),
                   viol_hv=int((np.diff(hv) < -1e-12).sum()),
                   igd_ini=float(ig[0]), igd_fim=float(ig[-1]),
                   ganho=float((ig[-1] - ig[0]) / ig[0]) if ig[0] > 0 else np.nan,
                   hv_ini=float(hv[0]), hv_fim=float(hv[-1]),
                   nd_ini=float(nd[0]), nd_fim=float(nd[-1]),
                   cols=",".join(df.columns)))
tdf = pd.DataFrame(tr)
tdf.to_csv(f"{OUT}/e81_trajetorias.csv", index=False)
print("\n== TRAJETORIAS ==")
print("celulas:", len(tdf), "| violacoes IGD+ totais:", int(tdf["viol_igd"].sum()),
      "| violacoes HV:", int(tdf["viol_hv"].sum()))
print(tdf[["label", "n_ck", "viol_igd", "viol_hv", "igd_ini", "igd_fim", "ganho",
           "nd_ini", "nd_fim"]].to_string())

# ── 3. tempo ──────────────────────────────────────────────────────────────
tp = pd.read_csv(f"{F5}/tempo_f52d.csv")
tpe = tp[tp["alg"] == "e81"].copy()
tpe["h"] = tpe["wall_s"] / 3600
tpe.to_csv(f"{OUT}/e81_tempo.csv", index=False)
print("\n== TEMPO ==")
print("total h-core:", round(tpe["h"].sum(), 2), "| main:", round(tpe[tpe.exp == 'main']["h"].sum(), 2),
      "| batch:", round(tpe[tpe.exp == 'batch']["h"].sum(), 2))
print("maquinas:", tpe["maquina"].value_counts().to_dict())
print(tpe.sort_values("h", ascending=False).head(6)[["exp", "problema", "maquina", "h"]].to_string())

# ── 4. posicao vs pisos e rivais ──────────────────────────────────────────
me = pd.read_csv(f"{F5}/metricas_finais_f52c.csv")
maq = tp.set_index(["exp", "alg", "problema"])["maquina"].to_dict()
PISOS = ["moead", "nsga2", "nsga3", "smsemoa", "moead_media", "treed_media", "sobol_batch"]
main = me[me["exp"] == "main"]
mine = main[main["alg"] == "e81"].set_index("problema")
sa = sorted(set(main["alg"]) - set(PISOS))
rows_pos = []
for prob in mine.index:
    sub = main[main["problema"] == prob]
    pis = sub[sub["alg"].isin(PISOS)]
    sas = sub[sub["alg"].isin(sa)]
    best_p = pis["igd_plus"].min() if len(pis) else np.nan
    best_p_alg = pis.loc[pis["igd_plus"].idxmin(), "alg"] if len(pis) else None
    mv = mine.loc[prob, "igd_plus"]
    rk = int((sas["igd_plus"] < mv).sum()) + 1
    rows_pos.append(dict(problema=prob, igd_e81=mv, hv_e81=mine.loc[prob, "hv"],
                         nd_e81=mine.loc[prob, "n_nd"],
                         melhor_piso=best_p, piso_alg=best_p_alg,
                         piso_maq=maq.get(("main", best_p_alg, prob)),
                         e81_maq=maq.get(("main", "e81", prob)),
                         delta_vs_piso=(mv - best_p) / best_p if best_p and best_p > 0 else np.nan,
                         rank_sa=rk, n_sa=len(sas),
                         melhor_sa=sas["igd_plus"].min(),
                         melhor_sa_alg=sas.loc[sas["igd_plus"].idxmin(), "alg"],
                         igd_c262=float(sub[sub.alg == "c262"]["igd_plus"].iloc[0]) if (sub.alg == "c262").any() else np.nan,
                         hv_c262=float(sub[sub.alg == "c262"]["hv"].iloc[0]) if (sub.alg == "c262").any() else np.nan,
                         igd_c154=float(sub[sub.alg == "c154"]["igd_plus"].iloc[0]) if (sub.alg == "c154").any() else np.nan,
                         igd_c149=float(sub[sub.alg == "c149"]["igd_plus"].iloc[0]) if (sub.alg == "c149").any() else np.nan))
pos = pd.DataFrame(rows_pos)
pos.to_csv(f"{OUT}/e81_posicao.csv", index=False)
PISO_RUIDO = 0.5898
print("\n== POSICAO (main, IGD+) ==")
print("bate o melhor piso:", int((pos["delta_vs_piso"] < 0).sum()), "/", len(pos))
print("perde DENTRO do piso de ruido (<=58,98%):",
      int(((pos["delta_vs_piso"] >= 0) & (pos["delta_vs_piso"] <= PISO_RUIDO)).sum()))
print("perde ALEM do piso:", int((pos["delta_vs_piso"] > PISO_RUIDO).sum()))
print("rank medio SA:", round(pos["rank_sa"].mean(), 2), "de", int(pos["n_sa"].iloc[0]))
print("e81 melhor que c262 (IGD+):", int((pos["igd_e81"] < pos["igd_c262"]).sum()), "/", len(pos))
print("e81 melhor que c154 (IGD+):", int((pos["igd_e81"] < pos["igd_c154"]).sum()), "/", int(pos["igd_c154"].notna().sum()))
print("e81 melhor que c149 (IGD+):", int((pos["igd_e81"] < pos["igd_c149"]).sum()), "/", int(pos["igd_c149"].notna().sum()))
print(pos[["problema", "igd_e81", "melhor_piso", "piso_alg", "piso_maq", "e81_maq",
           "delta_vs_piso", "rank_sa", "melhor_sa_alg", "igd_c262", "nd_e81"]].to_string())

# batch x main
bt = me[me["exp"] == "batch"]
print("\n== BATCH q=10 x MAIN q=1 (mesmos 5 problemas) ==")
for prob in ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]:
    a = mine.loc[prob]
    b = bt[(bt.alg == "e81") & (bt.problema == prob)].iloc[0]
    sb = bt[(bt.alg == "sobol_batch") & (bt.problema == prob)]
    c149 = bt[(bt.alg == "c149") & (bt.problema == prob)]
    print(f"  {prob:10s} IGD+ q1={a['igd_plus']:.4f} q10={b['igd_plus']:.4f} "
          f"| HV q1={a['hv']:.4f} q10={b['hv']:.4f} | ND q1={int(a['n_nd'])} q10={int(b['n_nd'])} "
          f"| sobol_batch IGD+={float(sb['igd_plus'].iloc[0]) if len(sb) else float('nan'):.4f} "
          f"HV={float(sb['hv'].iloc[0]) if len(sb) else float('nan'):.4f} "
          f"| c149b IGD+={float(c149['igd_plus'].iloc[0]) if len(c149) else float('nan'):.4f}")
print("\nescrito em", OUT)
