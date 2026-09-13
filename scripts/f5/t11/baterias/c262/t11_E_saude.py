#!/usr/bin/env python
"""T11/c262 — BATERIA E: saude (regua Sobol + posicao vs pisos), a partir dos
insumos PRE-COMPUTADOS da F5 (nao recomputa) + o bloco do smoke T11.
Regra 12 do CONTRATO: o c262 nao tem `sonda_estratificada` (medido 0/21) —
so a regua Sobol entra, e ela e o bloco comparavel entre configs.
"""
import glob, json
import numpy as np
import pandas as pd

R = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
s = pd.read_csv(f"{R}/sonda_f52e.csv")
s = s[(s.alg == "c262") & (s.exp == "main")]
print("=== REGUA SOBOL (s42, pre-computada F5.2e) ===")
print("linhas:", len(s), "| celulas:", s.problema.nunique(),
      "| celula-objetivo:", s.groupby(['problema', 'obj']).ngroups)
res = []
for (p, o), g in s.groupby(["problema", "obj"]):
    g = g.sort_values("bloco")
    w0, wN = g.wape.iloc[0], g.wape.iloc[-1]
    res.append(dict(problema=p, obj=o, wape_1=w0, wape_N=wN,
                    d_pct=100 * (wN - w0) / w0 if w0 else np.nan,
                    cob_N=g.cobertura95.iloc[-1], corr_N=g["corr"].iloc[-1],
                    nan=g.n_nan.sum(), val=g.n_validas.min()))
d = pd.DataFrame(res)
print(f"DeltaWAPE 1o->ultimo bloco: mediana {d.d_pct.median():+.2f}% | "
      f"melhoram {int((d.d_pct < 0).sum())}/{len(d)}")
print(f"cobertura final: mediana {d.cob_N.median():.4f} | "
      f">=0,90 em {int((d.cob_N >= .90).sum())}/{len(d)}")
print(f"n_nan total: {int(d.nan.sum())} | n_validas min: {int(d.val.min())}")
print("piores cobertura:")
print(d.nsmallest(6, "cob_N")[["problema", "obj", "cob_N", "wape_N"]]
      .to_string(index=False))
print("melhores DeltaWAPE:")
print(d.nsmallest(4, "d_pct")[["problema", "obj", "wape_1", "wape_N", "d_pct"]]
      .to_string(index=False))
d.to_csv(f"{R}/t11/baterias/c262/c262_t11_sonda.csv", index=False)

# ---- posicao vs pisos (IGD+) ----
m = pd.read_csv(f"{R}/metricas_finais_f52c.csv")
m = m[m.exp == "main"]
PISOS = ["nsga2", "nsga3", "moead", "smsemoa", "sobol_batch"]
c = m[m.alg == "c262"].set_index("problema")["igd_plus"]
pis = m[m.alg.isin(PISOS)].groupby("problema")["igd_plus"].min()
comp = pd.DataFrame({"c262": c, "melhor_piso": pis}).dropna()
comp["delta_pct"] = 100 * (comp.c262 - comp.melhor_piso) / comp.melhor_piso
PISO_RUIDO = 58.98
print()
print("=== POSICAO vs PISOS (IGD+, piso de ruido O-18 = 58,98%) ===")
print("celulas comparadas:", len(comp))
print("  bate ALEM do ruido (<-58,98%):", int((comp.delta_pct < -PISO_RUIDO).sum()))
print("  bate dentro do ruido:",
      int(((comp.delta_pct < 0) & (comp.delta_pct >= -PISO_RUIDO)).sum()))
print("  perde dentro do ruido:",
      int(((comp.delta_pct >= 0) & (comp.delta_pct <= PISO_RUIDO)).sum()))
print("  perde ALEM do ruido (>58,98%):", int((comp.delta_pct > PISO_RUIDO).sum()))
print(comp.sort_values("delta_pct").to_string())
comp.to_csv(f"{R}/t11/baterias/c262/c262_t11_pisos.csv")

# ---- rank entre TODOS os algoritmos ----
piv = m.pivot_table(index="problema", columns="alg", values="igd_plus")
rk = piv.rank(axis=1)
if "c262" in rk.columns:
    rr = rk["c262"].dropna()
    print()
    print(f"=== RANK c262 (IGD+, main) === rank medio {rr.mean():.2f} "
          f"entre {piv.notna().sum(axis=1).median():.0f} algs (mediana) | "
          f"1o lugar em {int((rr == 1).sum())}/{len(rr)} | "
          f"top-3 em {int((rr <= 3).sum())}/{len(rr)}")

# ---- SMOKE T11: a regua no artefato pos-T11 ----
SB = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/"
      "experiments/main/c262/exp_main_c262_MMF1_0")
r3 = pd.read_parquet(f"{SB}__surrogate.parquet")
gab = pd.read_parquet("/Users/gmello/Documents/python_repos/mestrado/"
                      "ua-dd-saea/data/sonda/sonda_MMF1.parquet")
snd = r3[r3.regime == "sonda"]
bl = sorted(snd.geracao.dropna().unique())
print()
print("=== SMOKE T11 (MMF1/s0) — regua Sobol ===")
print("blocos:", len(bl), "| linhas:", len(snd), "| n_nan sigma:",
      int(np.isnan(snd[["sigma_0", "sigma_1"]].values).sum()))
gx = [c for c in gab.columns if c.startswith("x") and c[1:].isdigit()]
gf = [c for c in gab.columns if c.startswith("f") and c[1:].isdigit()]
dmx = 0.0
for g in [bl[0], bl[len(bl) // 2], bl[-1]]:
    b = snd[snd.geracao == g]
    dmx = max(dmx, float(np.max(np.abs(
        b[["x0", "x1"]].values.astype(np.float64) -
        gab[gx].values[:len(b)].astype(np.float64)))))
print("U5 join posicional |dx| max (1o/mediano/ultimo bloco):", dmx)
for g in [bl[0], bl[-1]]:
    b = snd[snd.geracao == g]
    for j in (0, 1):
        mu = b[f"mu_{j}"].values.astype(np.float64)
        f = gab[gf[j]].values[:len(b)].astype(np.float64)
        sg = b[f"sigma_{j}"].values.astype(np.float64)
        wape = np.abs(mu - f).sum() / np.abs(f).sum()
        cob = float(np.mean(np.abs(mu - f) <= 1.96 * sg))
        print(f"  bloco g={int(g):3d} obj{j}: WAPE={wape:.5f} cobertura={cob:.4f}")
