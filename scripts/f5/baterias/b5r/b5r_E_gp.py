#!/usr/bin/env python
"""F5.3b · b5r — BATERIA E: censo do GP (SurrogateKriging DESDEO).

Para CADA par (celula, objetivo) mede, no bloco de sonda de 20.000 e na busca:
  - sigma constante?  sigma == sqrt(1e3) (=31,6228, TETO do ConstantKernel)?
  - mu constante (colapso ao prior de media ZERO — `normalize_y=False`)?
  - amplitude de mu x amplitude do dataset (o GP consegue representar a escala?)
Saida: b5r_E_gp.csv
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
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5r"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42
TETO = np.sqrt(1e3)          # 31,6228 — sqrt do limite superior de C(1.0,(1e-3,1e3))
PISO = np.sqrt(1e-3)


def main():
    rows = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        stem = [x for x in os.listdir(d) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")][0][: -len(".manifest.json")]
        d3 = pd.read_parquet(os.path.join(d, stem + "__surrogate.parquet"))
        d1 = pd.read_parquet(os.path.join(d, stem + "__real.parquet"))
        s3 = d3[d3.regime == "sonda"]
        b3 = d3[d3.regime == "offline"]
        M = len([x for x in d3.columns if re.fullmatch(r"mu_\d+", x)])
        prob = lab.split("_", 2)[-1] if lab.startswith("swap_") else lab
        for j in range(M):
            mu, sg = s3["mu_%d" % j].values, s3["sigma_%d" % j].values
            fj = d1["f%d" % j].values.astype(np.float64)
            rows.append(dict(
                label=lab, problema=prob, obj=j, M=M,
                mu_uniq=int(pd.Series(mu).nunique()),
                mu_amp=float(np.ptp(mu)), f_amp=float(np.ptp(fj)),
                razao_amp=float(np.ptp(mu) / max(np.ptp(fj), 1e-300)),
                f_media=float(fj.mean()), mu_media=float(mu.mean()),
                sig_uniq=int(pd.Series(sg).nunique()),
                sig_med=float(sg.mean()), sig_cv=float(sg.std() / max(abs(sg.mean()), 1e-300)),
                sig_no_teto=float(np.mean(np.isclose(sg, TETO, rtol=1e-6))),
                sig_zero=float(np.mean(sg == 0)),
                mu_colapso=bool(pd.Series(mu).nunique() <= 2),
                sig_busca_uniq=int(pd.Series(b3["sigma_%d" % j].values).nunique()),
            ))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "b5r_E_gp.csv"), index=False)
    print("pares (celula,objetivo):", len(df))
    print("mu colapsado (<=2 valores em 20k):", int(df.mu_colapso.sum()))
    print("sigma no TETO sqrt(1e3) em >99% da sonda:", int((df.sig_no_teto > .99).sum()))
    print("sigma praticamente constante (cv<1e-6):", int((df.sig_cv < 1e-6).sum()))
    print("razao_amp < 0,05 (GP nao representa a escala):", int((df.razao_amp < .05).sum()))
    print()
    print(df[(df.mu_colapso) | (df.sig_no_teto > .5) | (df.razao_amp < .05)]
          .to_string(index=False))
    print()
    print("sigma_zero > 0 (posterior colapsa a 0 em pontos da sonda):")
    print(df[df.sig_zero > 0][["label", "obj", "sig_zero", "sig_med"]].to_string(index=False))


if __name__ == "__main__":
    main()
