#!/usr/bin/env python
"""bateria5_e81 — (1) criterio EXATO da completacao DI-25 (greedy sobre selecionados
+ ja-completados); (2) o elo causal dos saltos de aprendizado (WAPE x lengthscale x
outputscale) em TODOS os blocos; (3) assinatura do nugget 1e-12: sigma x distancia ao
dataset na sonda; (4) fantasia x sonda (assimetria in-sample); (5) crescimento do
arquivo nao-dominado (n_front1).

READ-ONLY. Saidas: e81_di25_greedy.csv · e81_elo_causal.csv · e81_nugget_sigma.csv ·
e81_fantasia_vs_sonda.csv · e81_nd_arquivo.csv
"""
import json, os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")


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


rec = pd.read_csv(f"{OUT}/e81_sonda_recomputada.csv")
rows_g, rows_e, rows_n, rows_f, rows_nd = [], [], [], [], []

for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    hdr = json.loads(open(base + ".jsonl").readline())
    dec = [json.loads(l) for l in open(base + ".jsonl") if '"rec": "decision"' in l]
    real = pd.read_parquet(base + "__real.parquet")
    sur = pd.read_parquet(base + "__surrogate.parquet")
    D, M = int(hdr["D"]), int(hdr["M"]); q = int(man["q"])
    xcols = [f"x{i}" for i in range(D)]
    dm = json.load(open(f"{REPO}/data/doe/{prob}/doe_{prob}_42.manifest.json"))
    xl = np.array(dm["bounds"]["xl"], float); xu = np.array(dm["bounds"]["xu"], float)
    rng = xu - xl
    Xnat = real[xcols].values.astype(np.float64); X01 = (Xnat - xl) / rng
    onl = {g: v for g, v in sur[sur["regime"] == "online"].groupby("geracao")}

    # ── (1) criterio exato da completacao DI-25 ───────────────────────────
    for o in dec:
        g = o["geracao"]; nfa = int(o["n_front_acq"]); ntr = int(o["n_train"])
        blk = onl[g]
        if len(blk) == nfa:
            continue
        c01 = (blk[xcols].values.astype(np.float64) - xl) / rng
        fill = c01[nfa:]
        seq_sel, seq_uni = [], []
        for kk in range(len(fill)):
            base_sel = np.vstack([c01[:nfa], fill[:kk]]) if kk else c01[:nfa]
            base_uni = np.vstack([X01[:ntr], base_sel])
            seq_sel.append(float(cdist(fill[kk:kk + 1], base_sel).min()))
            seq_uni.append(float(cdist(fill[kk:kk + 1], base_uni).min()))
        rows_g.append(dict(label=lab, geracao=g, n_front=nfa, n_fill=len(fill),
                           desc_sel=bool((np.diff(seq_sel) <= 1e-12).all()),
                           desc_uni=bool((np.diff(seq_uni) <= 1e-12).all()),
                           seq_sel=str([round(v, 4) for v in seq_sel]),
                           seq_uni=str([round(v, 4) for v in seq_uni])))

    # ── (2) elo causal: DlogWAPE x Dlog(ls) x Dlog(osc) por bloco ─────────
    hp = {o["geracao"]: o["modelo_hp"] for o in dec}
    sub = rec[rec["label"] == lab]
    for j in range(M):
        s = sub[sub["obj"] == j].sort_values("ordem")
        gg = s["bloco"].values.astype(int)
        w = s["wape"].values; cv = s["cobertura95"].values; sm = s["sigma_med"].values
        ls = np.array([hp[g]["por_objetivo"][j]["lengthscale_med"] for g in gg])
        osc = np.array([hp[g]["por_objetivo"][j]["outputscale"] for g in gg])
        dw = np.diff(np.log(np.maximum(w, 1e-15)))
        dls = np.diff(np.log(ls)); dosc = np.diff(np.log(osc))
        dcv = np.diff(cv); dsm = np.diff(np.log(np.maximum(sm, 1e-15)))
        ok = np.isfinite(dw) & np.isfinite(dls) & np.isfinite(dosc)
        if ok.sum() < 5:
            continue
        rows_e.append(dict(label=lab, exp=exp, problema=prob, obj=j, n=int(ok.sum()),
                           rho_dw_dls=float(spearmanr(dw[ok], dls[ok]).statistic),
                           rho_dw_dosc=float(spearmanr(dw[ok], dosc[ok]).statistic),
                           rho_dcv_dls=float(spearmanr(dcv[ok], dls[ok]).statistic),
                           rho_dsm_dosc=float(spearmanr(dsm[ok], dosc[ok]).statistic),
                           rho_dsm_dls=float(spearmanr(dsm[ok], dls[ok]).statistic),
                           ls_ini=float(ls[0]), ls_fim=float(ls[-1]), ls_razao=float(ls[-1] / ls[0]),
                           osc_ini=float(osc[0]), osc_fim=float(osc[-1]), osc_razao=float(osc[-1] / osc[0]),
                           # o maior salto de aprendizado do bloco
                           maior_queda_wape=float(dw[ok].min()),
                           ls_no_maior_salto=float(dls[ok][np.argmin(dw[ok])]),
                           osc_no_maior_salto=float(dosc[ok][np.argmin(dw[ok])])))

    # ── (3) nugget 1e-12: sigma x distancia ao dataset (ultimo bloco) ─────
    sd = sur[sur["regime"] == "sonda"]
    gl = int(sd["geracao"].max())
    b = sd[sd["geracao"] == gl]
    b01 = (b[xcols].values.astype(np.float64) - xl) / rng
    ntr_fim = int(b["fe_treino_max"].iloc[0]) + 1
    dmin = cdist(b01, X01[:ntr_fim]).min(axis=1)
    for j in range(M):
        sg = b[f"sigma_{j}"].values.astype(np.float64)
        rows_n.append(dict(label=lab, exp=exp, problema=prob, obj=j, bloco=gl, n_train=ntr_fim,
                           rho_sigma_dist=float(spearmanr(sg, dmin).statistic),
                           sigma_p05=float(np.percentile(sg, 5)), sigma_p95=float(np.percentile(sg, 95)),
                           sigma_prox_med=float(np.median(sg[dmin <= np.percentile(dmin, 10)])),
                           sigma_long_med=float(np.median(sg[dmin >= np.percentile(dmin, 90)])),
                           dmin_p10=float(np.percentile(dmin, 10)), dmin_p90=float(np.percentile(dmin, 90))))

    # ── (4) fantasia x sonda ──────────────────────────────────────────────
    mk = sur[sur["real_solution_id"].notna()]
    jj = mk.merge(real[["solution_id"] + [f"f{k}" for k in range(M)]],
                  left_on="real_solution_id", right_on="solution_id", how="left")
    for j in range(M):
        err = np.abs(jj[f"mu_{j}"].values.astype(np.float64) - jj[f"f{j}"].values.astype(np.float64))
        den = np.abs(jj[f"f{j}"].values.astype(np.float64)).sum()
        wape_inf = err.sum() / den if den > 0 else np.nan
        sfin = sub[(sub["obj"] == j)].sort_values("ordem")["wape"].iloc[-1]
        rows_f.append(dict(label=lab, exp=exp, problema=prob, obj=j,
                           wape_infill=wape_inf, wape_sonda_fim=float(sfin),
                           razao=wape_inf / sfin if sfin > 0 else np.nan))

    # ── (5) crescimento do arquivo ND ─────────────────────────────────────
    nf1 = np.array([o["n_front1"] for o in dec])
    rows_nd.append(dict(label=lab, exp=exp, problema=prob, D=D, M=M, q=q,
                        nd_ini=int(nf1[0]), nd_fim=int(nf1[-1]), nd_max=int(nf1.max()),
                        nd_monotono=bool((np.diff(nf1) >= 0).all()),
                        nd_quedas=int((np.diff(nf1) < 0).sum()),
                        frac_arquivo=float(nf1[-1] / int(man["maxfe"]))))
    print("ok", lab, flush=True)

pd.DataFrame(rows_g).to_csv(f"{OUT}/e81_di25_greedy.csv", index=False)
pd.DataFrame(rows_e).to_csv(f"{OUT}/e81_elo_causal.csv", index=False)
pd.DataFrame(rows_n).to_csv(f"{OUT}/e81_nugget_sigma.csv", index=False)
pd.DataFrame(rows_f).to_csv(f"{OUT}/e81_fantasia_vs_sonda.csv", index=False)
pd.DataFrame(rows_nd).to_csv(f"{OUT}/e81_nd_arquivo.csv", index=False)
print("\nescrito em", OUT)
