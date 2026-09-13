#!/usr/bin/env python
"""F5.3b · b5r — BATERIA C: a SELECAO Prob-APD media-MC nos dados (query-joia).

C1  estrutura RVEA: reconstroi o lattice Das-Dennis (H=49 M=2 / H=13 M=3) e testa
    que os sobreviventes de cada geracao ocupam vetores de referencia DISTINTOS
    (1 individuo por subpopulacao — Alg. 1 passo 11) e que #vetores usados == |pop|
C2  o σ na selecao (mecanismo Jensen do v3): por geracao, pais MANTIDOS x pais
    DESCARTADOS — compara σ; se a media-MC penaliza incerteza, σ(descartado) >
    σ(mantido) sistematicamente
C3  pares offline: endpoint ⑦ REAL de b5r x b5m x moead_media x e103 x c311
    (a metrica oficial empata por desenho — D69 le a ①)

Saidas: b5r_C_lattice.csv · b5r_C_sigma_sel.csv · b5r_C_pares7.csv
"""
import json
import os
import re
import sys
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.special import comb

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
os.chdir(REPO)
RESROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42
ISX = lambda t: bool(re.fullmatch(r"x\d+", t))
ISF = lambda t: bool(re.fullmatch(r"f\d+", t))

from src import metrics  # noqa: E402


def lattice(H, M):
    """Das-Dennis do desdeo (ReferenceVectors._create 'Uniform') + normalize L2."""
    nv = comb(H + M - 1, M - 1, exact=True)
    t1 = np.array(list(combinations(range(1, M + H), M - 1)))
    t2 = np.array([range(M - 1)] * nv)
    t = t1 - t2 - 1
    w = np.zeros((nv, M), dtype=int)
    w[:, 0] = t[:, 0]
    for i in range(1, M - 1):
        w[:, i] = t[:, i] - t[:, i - 1]
    w[:, -1] = H - t[:, -1]
    V = w / H
    return V / np.linalg.norm(V, axis=1)[:, None]


def celulas(alg):
    root = os.path.join(RESROOT, alg)
    out = []
    for lab in sorted(os.listdir(root)):
        d = os.path.join(root, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        if lab.startswith("swap_"):
            td, prob = lab[len("swap_"):].split("_", 1)
            tier, dist = td.split("-")
            exp = "sweep-%s-%s" % (tier, dist)
        else:
            prob, tier, dist, exp = lab, "main", "lhs", "off"
        cand = [x for x in os.listdir(d) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")]
        out.append(dict(label=lab, dir=d, problema=prob, tier=tier, dist=dist,
                        exp=exp, stem=cand[0][: -len(".manifest.json")], alg=alg))
    return out


def main():
    lat_rows, sig_rows, par_rows = [], [], []
    REF = {}
    for c in celulas("b5r"):
        p = lambda s: os.path.join(c["dir"], c["stem"] + s)
        d3 = pd.read_parquet(p("__surrogate.parquet"))
        b3 = d3[d3.regime == "offline"].copy()
        M = len([x for x in b3.columns if re.fullmatch(r"mu_\d+", x)])
        muc = ["mu_%d" % j for j in range(M)]
        sgc = ["sigma_%d" % j for j in range(M)]
        xc = [x for x in b3.columns if ISX(x)]
        b3["g"] = b3["geracao"].astype(int)
        H = 49 if M == 2 else 13
        V = lattice(H, M)
        NRV = len(V)
        grp = {g: t for g, t in b3.groupby("g")}
        ngen = max(grp)

        # ── C1: 1 individuo por subpopulacao ────────────────────────────────
        ok_dist = 0
        nviz = []
        for g in range(1, ngen + 1):
            t = grp[g]
            F = t[muc].values.astype(np.float64)
            Fp = F - F.min(axis=0)
            nrm = np.linalg.norm(Fp, axis=1)
            nrm[nrm == 0] = 1.0
            cosm = (Fp / nrm[:, None]) @ V.T
            a = np.argmax(cosm, axis=1)
            nu = len(np.unique(a))
            nviz.append(nu)
            if nu == len(t):
                ok_dist += 1
        nviz = np.asarray(nviz)
        lat_rows.append(dict(label=c["label"], problema=c["problema"], M=M,
                             NRV=NRV, ngen=ngen, ok_distintos=ok_dist,
                             share_distintos=ok_dist / ngen,
                             defice_med=float(np.mean([len(grp[g]) for g in
                                                       range(1, ngen + 1)] - nviz)),
                             defice_max=int(np.max([len(grp[g]) for g in
                                                    range(1, ngen + 1)] - nviz))))

        # ── C2: σ dos pais mantidos x descartados ───────────────────────────
        nk, nd_, sk, sd = 0, 0, [], []
        gens_maior = 0
        gens_val = 0
        for g in range(2, ngen + 1):
            pa, ch = grp[g - 1], grp[g]
            kx = set(map(bytes, np.ascontiguousarray(ch[xc].values.astype(np.float32))))
            Xp = np.ascontiguousarray(pa[xc].values.astype(np.float32))
            keep = np.array([bytes(r) in kx for r in Xp])
            if keep.all() or (~keep).all():
                continue
            Sp = pa[sgc].values.astype(np.float64).mean(axis=1)
            a, b = float(Sp[keep].mean()), float(Sp[~keep].mean())
            sk.append(a)
            sd.append(b)
            nk += int(keep.sum())
            nd_ += int((~keep).sum())
            gens_val += 1
            gens_maior += int(b > a)
        sig_rows.append(dict(label=c["label"], problema=c["problema"], ngen=ngen,
                             gens_validas=gens_val, gens_desc_maior=gens_maior,
                             share_desc_maior=(gens_maior / gens_val) if gens_val else np.nan,
                             n_mantidos=nk, n_descartados=nd_,
                             sigma_mantido=float(np.mean(sk)) if sk else np.nan,
                             sigma_descartado=float(np.mean(sd)) if sd else np.nan,
                             razao=float(np.mean(sd) / np.mean(sk)) if sk else np.nan))
        print("C ok", c["label"], flush=True)

    pd.DataFrame(lat_rows).to_csv(os.path.join(OUT, "b5r_C_lattice.csv"), index=False)
    pd.DataFrame(sig_rows).to_csv(os.path.join(OUT, "b5r_C_sigma_sel.csv"), index=False)

    # ── C3: endpoint ⑦ dos 5 offline ────────────────────────────────────────
    for alg in ["b5r", "b5m", "moead_media", "e103", "c311"]:
        for c in celulas(alg):
            p = lambda s: os.path.join(c["dir"], c["stem"] + s)
            fp = p("__final.parquet")
            if not os.path.exists(fp):
                continue
            d7 = pd.read_parquet(fp)
            F7 = d7[[x for x in d7.columns if ISF(x)]].values.astype(np.float64)
            if c["problema"] not in REF:
                REF[c["problema"]] = metrics.reference_set(c["problema"])
            m = metrics.metrics_of_set(F7, c["problema"], ref_norm=REF[c["problema"]])
            mnd = metrics.metrics_of_set(F7[d7["nd_pos_real"].values], c["problema"],
                                         ref_norm=REF[c["problema"]])
            par_rows.append(dict(alg=alg, label=c["label"], problema=c["problema"],
                                 tier=c["tier"], dist=c["dist"], n7=len(d7),
                                 n7_nd=int(d7["nd_pos_real"].sum()),
                                 fantasia=float(d7["nd_pos_real"].mean()),
                                 igdp7=m["igd_plus"], hv7=m["hv"],
                                 igdp7nd=mnd["igd_plus"], hv7nd=mnd["hv"]))
        print("C3 ok", alg, flush=True)
    pd.DataFrame(par_rows).to_csv(os.path.join(OUT, "b5r_C_pares7.csv"), index=False)
    print("C gravado")


if __name__ == "__main__":
    main()
