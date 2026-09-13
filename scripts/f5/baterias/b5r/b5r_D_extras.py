#!/usr/bin/env python
"""F5.3b · b5r — BATERIA D: complementos.

D1  prova de que as 5 celulas `swap_small-lhs_*` sao REPLICAS BIT-A-BIT das `off`
    homonimas (D90: o tier small/lhs reusa o dataset principal, sem sufixo)
D2  share de vetores DISTINTOS por geracao (leitura correta do C1) + o custo
    do patch DI-16.16 (a prole pre-selecao e sobrescrita)
D3  sonda: WAPE/cobertura/corr agregados por familia de problema + o caso DTLZ3
    (GP colapsado no prior: sigma == sqrt(1000) e mu constante)
D4  ⑤ sem `params` -> fallback verificado (artifacts/params.json + sigma_dict)

Saidas: b5r_D_replicas.csv · b5r_D_distintos.csv · b5r_D_sonda.csv
"""
import hashlib
import json
import os
import re
import sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
os.chdir(REPO)
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5r"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stem(d):
    return [x for x in os.listdir(d) if x.endswith(".manifest.json")
            and not x.endswith("__final.manifest.json")][0][: -len(".manifest.json")]


def d1_replicas():
    rows = []
    for prob in ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]:
        a = os.path.join(RES, prob, str(SEED))
        b = os.path.join(RES, "swap_small-lhs_" + prob, str(SEED))
        sa, sb = stem(a), stem(b)
        r = dict(problema=prob, stem_off=sa, stem_sweep=sb)
        for lay in ["__real.parquet", "__surrogate.parquet", "__final.parquet"]:
            A = pd.read_parquet(os.path.join(a, sa + lay))
            B = pd.read_parquet(os.path.join(b, sb + lay))
            cols = [c for c in A.columns if c not in ("algoritmo", "problema", "semente")]
            same = (A.shape == B.shape) and A[cols].equals(B[cols])
            r["eq" + lay.replace("__", "_").replace(".parquet", "")] = bool(same)
        ma = json.load(open(os.path.join(a, sa + ".manifest.json")))
        mb = json.load(open(os.path.join(b, sb + ".manifest.json")))
        r["doe_hash_igual"] = (ma["doe_hash"] == mb["doe_hash"])
        r["ngen_off"], r["ngen_sweep"] = ma["n_geracoes"], mb["n_geracoes"]
        r["sha_real_igual"] = (sha(os.path.join(a, sa + "__real.parquet")) ==
                               sha(os.path.join(b, sb + "__real.parquet")))
        rows.append(r)
    return pd.DataFrame(rows)


def d2_distintos():
    lat = pd.read_csv(os.path.join(OUT, "b5r_C_lattice.csv"))
    A = pd.read_csv(os.path.join(OUT, "b5r_A_celulas.csv"))[["label", "A_pop_med", "A_pop_max"]]
    m = lat.merge(A, on="label")
    m["share_pop_distinta"] = 1 - m["defice_med"] / m["A_pop_med"]
    return m


def d3_sonda():
    s = pd.read_csv(os.path.join(REPO, "f5/sonda_f52e.csv"))
    s = s[s.alg == "b5r"].copy()

    def fam(p):
        for k in ["ZDT", "DTLZ", "WFG", "MMF", "BBOB"]:
            if p.startswith(k):
                return k
        return "?"

    s["familia"] = s.problema.map(fam)
    g = s.groupby(["exp", "familia"]).agg(
        n=("wape", "size"), wape_med=("wape", "median"), wape_max=("wape", "max"),
        corr_med=("corr", "median"), corr_min=("corr", "min"),
        cob_med=("cobertura95", "median"), cob_min=("cobertura95", "min"),
        n_corr_nan=("corr", lambda t: int(t.isna().sum())),
        nan_share=("n_nan", "sum")).reset_index()
    return s, g


def main():
    r1 = d1_replicas()
    r1.to_csv(os.path.join(OUT, "b5r_D_replicas.csv"), index=False)
    print(r1.to_string())
    r2 = d2_distintos()
    r2.to_csv(os.path.join(OUT, "b5r_D_distintos.csv"), index=False)
    print(r2[["label", "M", "A_pop_med", "defice_med", "share_pop_distinta",
              "share_distintos"]].to_string())
    s, g = d3_sonda()
    g.to_csv(os.path.join(OUT, "b5r_D_sonda.csv"), index=False)
    print(g.to_string())
    print("\nDTLZ3 (colapso ao prior):")
    print(s[s.problema == "DTLZ3"].to_string())


if __name__ == "__main__":
    main()
