#!/usr/bin/env python
"""F5.4 / e103-A25 - passo 2 (QUERY): recenso independente da camada 7 nas 45 celulas do e103.

READ-ONLY. Implementacao independente (nao reaproveita a bateria e103).
Testa: cardinalidade, duplicidade exata de X, ND recomputado sobre o conjunto
cheio vs deduplicado, e a razao de fantasia sob as duas leituras.
"""
import glob
import json
import os

import numpy as np
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103"
OUT = os.path.dirname(os.path.abspath(__file__))


def xcols(df):
    return [c for c in df.columns if c.startswith("x") and c[1:].isdigit()]


def fcols(df):
    return [c for c in df.columns if c.startswith("f") and c[1:].isdigit()]


def nd_mask(F):
    """ND (minimizacao). i eh dominado se existe j com j<=i em todos e j<i em algum."""
    n = F.shape[0]
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        le = np.all(F <= F[i], axis=1)
        lt = np.any(F < F[i], axis=1)
        dom = le & lt
        dom[i] = False
        if dom.any():
            keep[i] = False
    return keep


linhas = []
for cel in sorted(os.listdir(RAIZ)):
    d = os.path.join(RAIZ, cel, "42")
    if not os.path.isdir(d):
        continue
    fin = sorted(glob.glob(os.path.join(d, "*__final.parquet")))
    sur = sorted(glob.glob(os.path.join(d, "*__surrogate.parquet")))
    if not fin:
        continue
    f7 = pd.read_parquet(fin[0])
    xs, fs = xcols(f7), fcols(f7)
    X7 = f7[xs].to_numpy()
    F7 = f7[fs].to_numpy()
    n = len(f7)
    uX, idx_first = np.unique(X7, axis=0, return_index=True)
    idx_first = np.sort(idx_first)
    nd_full = nd_mask(F7)
    nd_ded = nd_mask(F7[idx_first])

    # camada 3, ultima geracao
    s = pd.read_parquet(sur[0], columns=["regime", "geracao", "modelo_flag"] + xs)
    ot = s[s.regime == "offline"]
    gmax = int(ot.geracao.max())
    u = ot[ot.geracao == gmax].reset_index(drop=True)
    XS = u[xs].to_numpy()
    kri = u.modelo_flag == "Kriging-DACE"
    XK = u.loc[kri, xs].to_numpy()
    XR = u.loc[~kri, xs].to_numpy()

    link_literal = bool(XS.shape == X7.shape and np.array_equal(XS, X7))
    link_kri = bool(XK.shape == X7.shape and np.array_equal(XK, X7))
    intercal = u.modelo_flag.tolist()[:4]

    linhas.append(dict(
        celula=cel, n7=n, n3_ultger=len(u), ger=gmax,
        uniqX_7=len(uX), dupX_7=n - len(uX),
        nd_log=int(f7.nd_pos_real.sum()), nd_recomp=int(nd_full.sum()),
        nd_dedupX=int(nd_ded.sum()),
        fantasia_pub=f7.nd_pos_real.sum() / n,
        fantasia_dedup=nd_ded.sum() / len(uX),
        link_literal_ordem3=link_literal, link_subset_kriging=link_kri,
        ordem3=",".join(x[:3] for x in intercal),
        mtime7=pd.Timestamp(os.path.getmtime(fin[0]), unit="s").tz_localize("UTC").tz_convert("America/Sao_Paulo").strftime("%H:%M:%S"),
    ))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "censo_camada7_45celulas.csv"), index=False)
pd.set_option("display.width", 300)
pd.set_option("display.max_columns", 60)
print(df.to_string(index=False))
print()
print("n7 counts:", df.n7.value_counts().to_dict())
print("n7 != 100:", df.loc[df.n7 != 100, "celula"].tolist())
print("link literal ordem-3 True:", df.link_literal_ordem3.sum(),
      "| link subset Kriging True:", df.link_subset_kriging.sum())
print("celulas com dupX_7 > 0:", int((df.dupX_7 > 0).sum()),
      "| max dupX entre as de n7==100:", int(df.loc[df.n7 == 100, "dupX_7"].max()))
print("|fantasia_pub - fantasia_dedup| max:",
      float((df.fantasia_pub - df.fantasia_dedup).abs().max()))
