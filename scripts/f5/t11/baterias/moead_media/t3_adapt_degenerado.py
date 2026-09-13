"""T11/moead_media · bateria T3 — a CADEIA `adapt` -> vetores degenerados -> PBI NaN
-> zero substituicao -> CONGELAMENTO. (o analogo A8 do b5m, no piso)

Codigo lido:
  desdeo_emo/EAs/BaseEA.py:55-62   `iterate()` chama `manage_preferences()` SEMPRE
  desdeo_emo/EAs/BaseEA.py:243-244 `manage_preferences` -> `reference_vectors.adapt(fitness)`
  desdeo_emo/othertools/ReferenceVectors.py:249-262
      `values = initial_values * (max(fit)-min(fit))`  -> coluna j ZERADA se ptp_j==0
      `normalize()`: norm_2==0 -> eps  => vetor NULO se TODAS as colunas zeram
  desdeo_emo/selection/MOEAD_select.py:72-74  `pbi`: weights/||weights|| = 0/0 = NaN
  desdeo_emo/selection/MOEAD_select.py:59     `np.where(off < cur)`: NaN<NaN = False
                                              => selection VAZIA => nunca substitui

Medida (READ-ONLY, 45 celulas da s42): nos pontos de `adapt` (geracoes 1, 11, 21, ...,
porque n_gen_per_iter=10) qual o ptp de cada mu_j na populacao arquivada.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.dirname(os.path.abspath(__file__))
GEN_PER_ITER = 10

rows = []
det = []
for cfg in ["moead_media", "b5m", "b5r"]:
    for d in sorted(glob.glob(os.path.join(RAIZ, cfg, "*", "42"))):
        label = os.path.basename(os.path.dirname(d))
        manp = [m for m in glob.glob(os.path.join(d, "*_42.manifest.json"))
                if "__final" not in m][0]
        m = json.load(open(manp))
        pref = manp[:-len(".manifest.json")]
        sch = pq.read_schema(pref + "__surrogate.parquet")
        mus = [c for c in sch.names if c.startswith("mu_")]
        xs = [c for c in sch.names if c.startswith("x") and c[1:].isdigit()]
        t = pq.read_table(pref + "__surrogate.parquet",
                          columns=["regime", "geracao"] + mus + xs).to_pandas()
        off = t[t.regime == "offline"].copy()
        off["g"] = off.geracao.astype(int)
        gmax = int(off.g.max())
        MU = off[mus].to_numpy(float)
        X = off[xs].to_numpy(float)
        G = off.g.to_numpy()

        # ptp por geracao x objetivo
        dfp = pd.DataFrame(MU, columns=mus)
        dfp["g"] = G
        ptp = dfp.groupby("g")[mus].agg(lambda s: float(np.ptp(s.to_numpy())))
        adapt_gs = [g for g in range(1, gmax + 1, GEN_PER_ITER)]
        ptp_ad = ptp.loc[[g for g in adapt_gs if g in ptp.index]]
        zero_col = (ptp_ad == 0.0)
        r = {"config": cfg, "label": label, "problema": m["problema"],
             "M": len(mus), "n_ger": gmax, "n_adapt": len(ptp_ad)}
        r["adapt_com_col_zerada"] = int(zero_col.any(axis=1).sum())
        r["adapt_TODAS_zeradas"] = int(zero_col.all(axis=1).sum())
        r["objs_sempre_zerados"] = int(zero_col.all(axis=0).sum())
        r["frac_adapt_col_zerada"] = float(zero_col.any(axis=1).mean())
        pz = zero_col.any(axis=1)
        r["primeiro_adapt_zerado"] = int(pz.index[pz.to_numpy().argmax()]) if pz.any() else None
        pt = zero_col.all(axis=1)
        r["primeiro_adapt_TODAS"] = int(pt.index[pt.to_numpy().argmax()]) if pt.any() else None

        # congelamento posicional: X(g) == X(g+1) exatamente
        gs = sorted(set(G))
        Xg = {g: X[G == g] for g in gs}
        cong = 0
        trans = 0
        primeiro_cong = None
        cong_apos = 0
        for a, b in zip(gs[:-1], gs[1:]):
            Xa, Xb = Xg[a], Xg[b]
            trans += 1
            if Xa.shape == Xb.shape and np.array_equal(Xa, Xb):
                cong += 1
                if primeiro_cong is None:
                    primeiro_cong = b
        r["transicoes"] = trans
        r["congeladas"] = cong
        r["frac_congelada"] = cong / float(trans) if trans else np.nan
        r["primeira_congelada"] = primeiro_cong
        # congelamento TERMINAL: a partir de que geracao nunca mais muda
        term = gmax
        for a, b in zip(gs[:-1][::-1], gs[1:][::-1]):
            if Xg[a].shape == Xg[b].shape and np.array_equal(Xg[a], Xg[b]):
                term = a
            else:
                break
        r["congelado_desde"] = term
        r["frac_run_congelado"] = (gmax - term) / float(gmax)
        rows.append(r)
        for g, row in zero_col.iterrows():
            if row.any():
                det.append({"config": cfg, "label": label, "g": int(g),
                            "objs_zerados": int(row.sum()), "M": len(mus)})
        print("[ok] %-12s %-26s adapt_zerado=%d/%d congel=%d/%d desde=%d"
              % (cfg, label, r["adapt_com_col_zerada"], r["n_adapt"],
                 cong, trans, term))
        sys.stdout.flush()

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "t3_adapt_degenerado.csv"), index=False)
pd.DataFrame(det).to_csv(os.path.join(OUT, "t3_adapt_detalhe.csv"), index=False)
print()
print(df.groupby("config")[["adapt_com_col_zerada", "n_adapt", "congeladas",
                            "transicoes", "frac_congelada",
                            "frac_run_congelado"]].sum())
print()
print(df.groupby("config").apply(
    lambda g: pd.Series({
        "celulas": len(g),
        "com_adapt_zerado": int((g.adapt_com_col_zerada > 0).sum()),
        "com_TODAS_zeradas": int((g.adapt_TODAS_zeradas > 0).sum()),
        "frac_congel_mediana": g.frac_congelada.median(),
        "congelado_ate_o_fim": int((g.frac_run_congelado > 0).sum()),
    })))
