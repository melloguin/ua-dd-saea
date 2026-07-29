#!/usr/bin/env python
"""F5.3b · b5r — BATERIA B: o MECANISMO (Prob-APD media-MC) nos dados.

B1  contabilidade exata do orcamento interno de 40.000 aval-surrogate
B2  reconciliacao ⑥×③ de f_best/n_front1 com a semantica float32/float64 correta
B3  diagnostico do σ (zero-σ, degeneracao ao prior, σ selecionado × σ da regua)
B4  ASSINATURA DINAMICA da Fig. 10 do paper: HV-surrogate (μ) × HV-real dos MESMOS
    X, por checkpoint — o sanity-check declarado na ancora J do bundle
B5  endpoint offline: metricas REAIS da ⑦ (b5r x pares offline)
B6  prova do empate por desenho das metricas oficiais entre os 5 algs offline

Saidas: b5r_B_fe40k.csv · b5r_B_reconc.csv · b5r_B_sigma.csv ·
        b5r_B_fig10.csv · b5r_B_endpoint7.csv · b5r_B_empate.csv
"""
import json
import os
import re
import sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
os.chdir(REPO)
RESROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42
ISX = lambda t: bool(re.fullmatch(r"x\d+", t))
ISF = lambda t: bool(re.fullmatch(r"f\d+", t))

from src import metrics  # noqa: E402
from src import experiment as EXP  # noqa: E402
from src import problems as PBL  # noqa: E402

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, "GATE D92 FALHOU: %r" % v
print("gate D92 OK %.5f" % v, flush=True)


def celulas(alg="b5r"):
    root = os.path.join(RESROOT, alg)
    out = []
    for lab in sorted(os.listdir(root)):
        d = os.path.join(root, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        if lab.startswith("swap_"):
            tok = lab[len("swap_"):]
            td, prob = tok.split("_", 1)
            tier, dist = td.split("-")
            exp = "sweep-%s-%s" % (tier, dist)
        else:
            prob, tier, dist, exp = lab, "main", "lhs", "off"
        stem = [x for x in os.listdir(d) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")][0][: -len(".manifest.json")]
        out.append(dict(label=lab, dir=d, problema=prob, tier=tier, dist=dist,
                        exp=exp, stem=stem, alg=alg))
    return out


def par(n):
    return int(n) + int(n) % 2


REFCACHE = {}


def main():
    cs = celulas()
    fe_rows, rec_rows, sig_rows, f10_rows, e7_rows = [], [], [], [], []
    for c in cs:
        p = lambda s: os.path.join(c["dir"], c["stem"] + s)
        man = json.load(open(p(".manifest.json")))
        d3 = pd.read_parquet(p("__surrogate.parquet"))
        b3 = d3[d3.regime == "offline"].copy()
        s3 = d3[d3.regime == "sonda"]
        xc = [x for x in b3.columns if ISX(x)]
        M = len([x for x in b3.columns if re.fullmatch(r"mu_\d+", x)])
        muc = ["mu_%d" % j for j in range(M)]
        sgc = ["sigma_%d" % j for j in range(M)]
        b3["g"] = b3["geracao"].astype(int)
        popsz = b3.groupby("g").size()
        NRV = 50 if M == 2 else 105
        ngen = int(popsz.index.max())

        # ── B1: contabilidade do orcamento interno ──────────────────────────
        pops = [NRV] + list(popsz.values)            # pop_0 = init LHS (NRV)
        off = [par(pops[g - 1]) for g in range(1, ngen + 1)]
        cum0 = np.cumsum(off)                        # modelo A: FE0 = 0
        cumN = NRV + cum0                            # modelo B: FE0 = NRV
        rowfe = dict(label=c["label"], problema=c["problema"], tier=c["tier"],
                     dist=c["dist"], M=M, NRV=NRV, ngen=ngen,
                     fe_A_final=int(cum0[-1]), fe_A_pre=int(cum0[-2]),
                     fe_B_final=int(cumN[-1]), fe_B_pre=int(cumN[-2]),
                     off_last=off[-1], off_med=float(np.median(off)))
        rowfe["invar_A"] = bool(cum0[-2] <= 40000 < cum0[-1])
        rowfe["invar_B"] = bool(cumN[-2] <= 40000 < cumN[-1])
        rowfe["overshoot_A"] = int(cum0[-1] - 40000)
        rowfe["overshoot_B"] = int(cumN[-1] - 40000)
        fe_rows.append(rowfe)

        # ── B2: reconciliacao ⑥×③ ───────────────────────────────────────────
        L = [json.loads(x) for x in open(p(".jsonl"))]
        dec = [x for x in L if x.get("rec") == "decision"]
        grp = {g: t for g, t in b3.groupby("g")}
        okfb = 0
        dn = []
        for x in dec:
            t = grp[x["geracao"]]
            Mu = t[muc].values.astype(np.float32)
            fb32 = np.asarray(x["f_best"], dtype=np.float64).astype(np.float32)
            if np.array_equal(fb32, Mu.min(axis=0)):
                okfb += 1
            nd32 = len(PBL._nds_filter(Mu.astype(np.float64)))
            dn.append(x["n_front1"] - nd32)
        dn = np.asarray(dn)
        rec_rows.append(dict(label=c["label"], problema=c["problema"], ngen=ngen,
                             fbest_exato32=okfb, fbest_share=okfb / len(dec),
                             nfront1_igual=int((dn == 0).sum()),
                             nfront1_share=float((dn == 0).mean()),
                             dn_min=int(dn.min()), dn_max=int(dn.max()),
                             dn_absmed=float(np.abs(dn).mean())))

        # ── B3: sigma ───────────────────────────────────────────────────────
        Sb = b3[sgc].values.astype(np.float64)
        Ss = s3[sgc].values.astype(np.float64)
        gser = b3["g"].values
        first = gser <= max(1, ngen // 10)
        lastq = gser >= ngen - max(1, ngen // 10)
        sig_rows.append(dict(
            label=c["label"], problema=c["problema"], tier=c["tier"], dist=c["dist"],
            M=M, sig_busca_med=float(np.nanmean(Sb)),
            sig_busca_mediana=float(np.nanmedian(Sb)),
            sig_sonda_med=float(np.nanmean(Ss)),
            sig_sonda_mediana=float(np.nanmedian(Ss)),
            razao_busca_sonda=float(np.nanmean(Sb) / np.nanmean(Ss)),
            zero_share_busca=float((Sb == 0).mean()),
            zero_share_sonda=float((Ss == 0).mean()),
            sig_ini10=float(np.nanmean(Sb[first])),
            sig_fim10=float(np.nanmean(Sb[lastq])),
            deriva=float(np.nanmean(Sb[lastq]) / np.nanmean(Sb[first])),
            sig_cv_sonda=float(np.nanstd(Ss) / max(np.nanmean(Ss), 1e-300)),
            prior_sqrt1000=bool(abs(np.nanmean(Ss) - np.sqrt(1000.0)) < 1e-2),
        ))

        # ── B4: assinatura dinamica (Fig. 10) ───────────────────────────────
        prob = EXP._instantiate_problem(c["problema"])
        if c["problema"] not in REFCACHE:
            REFCACHE[c["problema"]] = metrics.reference_set(c["problema"])
        RN = REFCACHE[c["problema"]]
        cps = np.unique(np.linspace(1, ngen, 25).astype(int))
        for g in cps:
            t = grp[int(g)]
            Mu = t[muc].values.astype(np.float64)
            Xg = t[xc].values.astype(np.float64)
            Fr = np.asarray(PBL.evaluate_problem(prob, Xg), dtype=np.float64)
            ms = metrics.metrics_of_set(Mu, c["problema"], ref_norm=RN)
            mr = metrics.metrics_of_set(Fr, c["problema"], ref_norm=RN)
            f10_rows.append(dict(label=c["label"], problema=c["problema"],
                                 tier=c["tier"], dist=c["dist"], g=int(g),
                                 frac=float(g / ngen), n_pop=len(t),
                                 hv_sur=ms["hv"], igdp_sur=ms["igd_plus"],
                                 hv_real=mr["hv"], igdp_real=mr["igd_plus"],
                                 sig_med=float(np.nanmean(t[sgc].values)),
                                 rmse=float(np.sqrt(np.mean((Mu - Fr) ** 2))),
                                 wape=float(np.abs(Mu - Fr).sum() /
                                            max(np.abs(Fr).sum(), 1e-300))))
        print("B4 ok", c["label"], flush=True)

        # ── B5: endpoint ⑦ (real) ───────────────────────────────────────────
        d7 = pd.read_parquet(p("__final.parquet"))
        F7 = d7[[x for x in d7.columns if ISF(x)]].values.astype(np.float64)
        m7 = metrics.metrics_of_set(F7, c["problema"], ref_norm=RN)
        m7nd = metrics.metrics_of_set(F7[d7["nd_pos_real"].values], c["problema"], ref_norm=RN)
        # linha de base: o ND do proprio dataset (①) — "Init" do paper
        d1 = pd.read_parquet(p("__real.parquet"))
        F1 = d1[[x for x in d1.columns if ISF(x)]].values.astype(np.float64)
        m1 = metrics.metrics_of_set(F1, c["problema"], ref_norm=RN)
        e7_rows.append(dict(label=c["label"], problema=c["problema"], tier=c["tier"],
                            dist=c["dist"], alg="b5r", n7=len(d7),
                            n7_nd=int(d7["nd_pos_real"].sum()),
                            fantasia=float(d7["nd_pos_real"].mean()),
                            igdp_7=m7["igd_plus"], hv_7=m7["hv"],
                            igdp_7nd=m7nd["igd_plus"], hv_7nd=m7nd["hv"],
                            igdp_init=m1["igd_plus"], hv_init=m1["hv"],
                            ganho_igdp=m1["igd_plus"] - m7["igd_plus"],
                            ganho_hv=m7["hv"] - m1["hv"]))

    pd.DataFrame(fe_rows).to_csv(os.path.join(OUT, "b5r_B_fe40k.csv"), index=False)
    pd.DataFrame(rec_rows).to_csv(os.path.join(OUT, "b5r_B_reconc.csv"), index=False)
    pd.DataFrame(sig_rows).to_csv(os.path.join(OUT, "b5r_B_sigma.csv"), index=False)
    pd.DataFrame(f10_rows).to_csv(os.path.join(OUT, "b5r_B_fig10.csv"), index=False)
    pd.DataFrame(e7_rows).to_csv(os.path.join(OUT, "b5r_B_endpoint7.csv"), index=False)
    print("B gravado", flush=True)


if __name__ == "__main__":
    main()
