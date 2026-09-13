"""B4 — A CURVA PARCIAL DA CELULA TRUNCADA E UTILIZAVEL?

Mede, sobre `evidencia_T11/teto_c154` (main/c154/DTLZ2/42, D=12, truncada em
teto_wall com 282/371 FE):
  (a) join posicional sonda x gabarito (regra 5 do CONTRATO) — max|dX|;
  (b) WAPE e cobertura +-1.96 sigma por bloco e por objetivo (def. congelada
      do PROTOCOLO §5) — primeiro bloco, ultimo bloco, tendencia;
  (c) trajetoria do front nao-dominado sobre a ① parcial.
READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

T = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
         "/experiments/main/c154")
ART = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda"
           "/sonda_DTLZ2.parquet")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")
ST = "exp_main_c154_DTLZ2_42"
M = 3

sur = pd.read_parquet(T / f"{ST}__surrogate.parquet")
sn = sur[sur.regime == "sonda"].copy()
gab = pd.read_parquet(ART)
xc = [f"x{i}" for i in range(12)]

# (a) join posicional
dmax = 0.0
for g, blk in sn.groupby("geracao"):
    d = np.abs(blk[xc].to_numpy() - gab[xc].to_numpy()[:2000]).max()
    dmax = max(dmax, float(d))
print(f"(a) join POSICIONAL sonda x gabarito[0:2000]: {sn.geracao.nunique()} "
      f"blocos, max|dX| = {dmax:.6e}  (eps-float32 = 2.384186e-07)")
print(f"    artefato tem {len(gab)} linhas; regime online le [0:2000] "
      f"(DI-13.5) -> {'OK' if dmax <= 2.3842e-7 else 'FALHA'}")

# (b) WAPE + cobertura
F = gab[[f"f{j}" for j in range(M)]].to_numpy()[:2000]
rows = []
for g, blk in sn.groupby("geracao"):
    mu = blk[[f"mu_{j}" for j in range(M)]].to_numpy()
    sg = blk[[f"sigma_{j}" for j in range(M)]].to_numpy()
    for j in range(M):
        err = np.abs(mu[:, j] - F[:, j])
        rows.append(dict(geracao=int(g), obj=j,
                         wape=float(err.sum() / np.abs(F[:, j]).sum()),
                         cob=float((err <= 1.96 * sg[:, j]).mean()),
                         sigma_med=float(np.median(sg[:, j]))))
S = pd.DataFrame(rows)
S.to_csv(OUT / "c154_teto_sonda.csv", index=False)
print("\n(b) SONDA da celula truncada — WAPE e cobertura por objetivo")
print(f"{'obj':>4} {'WAPE 1o':>10} {'WAPE ult':>10} {'delta%':>8} "
      f"{'cob 1o':>8} {'cob ult':>8}")
g0, g1 = S.geracao.min(), S.geracao.max()
for j in range(M):
    a = S[(S.obj == j) & (S.geracao == g0)].iloc[0]
    b = S[(S.obj == j) & (S.geracao == g1)].iloc[0]
    print(f"{j:>4} {a.wape:>10.4f} {b.wape:>10.4f} "
          f"{100*(b.wape/a.wape-1):>7.1f}% {a.cob:>8.4f} {b.cob:>8.4f}")
print(f"    (1o bloco = geracao {g0}; ultimo = geracao {g1}; "
      f"{S.geracao.nunique()} blocos x {M} obj = {len(S)} medicoes)")
mono = S.groupby("obj").apply(
    lambda d: (d.sort_values("geracao").wape.diff().dropna() < 0).mean(),
    include_groups=False)
print(f"    fracao de blocos com WAPE caindo: "
      f"{[round(float(v),3) for v in mono]}")

# (c) trajetoria do front na ① parcial
real = pd.read_parquet(T / f"{ST}__real.parquet")
Y = real[[f"f{j}" for j in range(M)]].to_numpy()


def nd(Y):
    n = len(Y)
    keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        dom = ((Y <= Y[i]).all(1) & (Y < Y[i]).any(1))
        if dom.any():
            keep[i] = False
    return int(keep.sum())


print("\n(c) trajetoria do front nao-dominado na ① PARCIAL (282 pts)")
for fe in [131, 150, 180, 210, 240, 270, 282]:
    print(f"    FE={fe:>4}  |ND| = {nd(Y[:fe]):>3}")
print(f"    f finitos: {int(np.isfinite(Y).all(1).sum())}/{len(Y)} | "
      f"NaN: {int(np.isnan(Y).sum())}")
