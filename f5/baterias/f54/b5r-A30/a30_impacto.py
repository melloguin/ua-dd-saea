"""[F5.4 / b5r-A30] Parte 2 — magnitude, invariante DI-16.16 e impacto.

  I1  volumetria: ΣK, Σ|ger 1|, fracao das linhas da ③-busca que sao a pop inicial.
  I2  invariante DI-16.16 (a promessa REAL do patch): ⑦.X == ③ da ULTIMA geracao,
      bit-a-bit float32 — se fecha, o patch cumpre o que declarou.
  I3  ⑥: o evento `decision` da geracao 1 descreve a pop inicial (f_best == min mu
      da geracao 1) — consequencia instrumental do achado.
  I4  contraste do achado: |pop| da ger 1 vs as demais; e o erro relativo de contar
      n_geracoes como "passos de selecao".
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.join(REPO, "f5", "baterias", "f54", "b5r-A30")

linhas = []
for pdir in sorted(glob.glob(os.path.join(RES, "b5r", "*"))):
    cel = os.path.join(pdir, "42")
    g = glob.glob(os.path.join(cel, "*__surrogate.parquet"))
    if not g:
        continue
    prob = os.path.basename(pdir)
    df = pd.read_parquet(g[0])
    b = df[df["regime"] != "sonda"]
    xc = sorted([c for c in df.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    mc = [c for c in df.columns if c.startswith("mu_")]
    ger = b["geracao"].astype(int).values
    K = int(ger.max())
    n1 = int((ger == 1).sum())
    fin = glob.glob(os.path.join(cel, "*__final.parquet"))
    X7 = pd.read_parquet(fin[0])[xc].to_numpy() if fin else None
    Xlast = b[ger == K][xc].to_numpy()
    inv = (X7 is not None and X7.shape == Xlast.shape
           and np.array_equal(X7.astype(np.float32), Xlast.astype(np.float32)))
    # ⑥ f_best da geracao 1
    jl = glob.glob(os.path.join(cel, "*.jsonl"))
    fb1 = None
    with open(jl[0]) as fh:
        for line in fh:
            if '"decision"' in line:
                ev = json.loads(line)
                if ev.get("rec") == "decision" and ev.get("geracao") == 1:
                    fb1 = np.asarray(ev.get("f_best"), dtype=np.float64)
                    break
    mu1 = b[ger == 1][mc].to_numpy().astype(np.float64)
    fb_ok = fb1 is not None and np.allclose(
        fb1, mu1.min(axis=0), rtol=1e-6, atol=0)
    linhas.append(dict(celula=prob, K=K, n_ger1=n1, n_busca=len(b),
                       frac_linhas_ger1=n1 / len(b),
                       erro_rel_n_ger=1.0 / K,
                       inv_DI1616_ok=bool(inv),
                       fbest_g1_eq_min_mu_g1=bool(fb_ok)))
    print(linhas[-1], flush=True)

d = pd.DataFrame(linhas)
d.to_csv(os.path.join(OUT, "b5r_A30_impacto.csv"), index=False)
print("\nΣK = %d · Σ|ger1| = %d · Σ linhas busca = %d · fracao ger1 = %.5f"
      % (d.K.sum(), d.n_ger1.sum(), d.n_busca.sum(),
         d.n_ger1.sum() / d.n_busca.sum()))
print("passos de selecao reais = ΣK - 45 = %d" % (d.K.sum() - len(d)))
print("erro relativo max de n_geracoes = %.4f%% (celula %s)"
      % (100 * d.erro_rel_n_ger.max(), d.loc[d.erro_rel_n_ger.idxmax(), "celula"]))
print("invariante DI-16.16 (⑦==ultima ger): %d/%d" % (d.inv_DI1616_ok.sum(), len(d)))
print("f_best(g=1) == min mu(g=1): %d/%d" % (d.fbest_g1_eq_min_mu_g1.sum(), len(d)))
