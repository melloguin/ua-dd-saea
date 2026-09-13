"""T11/moead_media · bateria T2 — a declaracao NOVA `granularidade_③` do sigma_dict.

"ger 1 = pop INICIAL (LHS, PRE-selecao); 2..n = POS-selecao; passos de selecao =
 n_geracoes-1; FE conta init+pop"

Testes (READ-ONLY, 45 celulas da s42):
  (a) estratificacao LHS da geracao 1 nos BOUNDS REAIS do problema — um LHS de N
      pontos ocupa os N estratos de CADA dimensao (score 1,0); amostra uniforme
      qualquer ocupa ~1-1/e = 0,632.
  (b) a mesma metrica na geracao 2 e na ultima (controle: apos selecao a
      estratificacao TEM de cair).
  (c) passos de selecao x N = 40.000 (M=2) — a leitura refinada do orcamento.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import standalone_harness as H  # noqa: E402

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media"
OUT = os.path.dirname(os.path.abspath(__file__))


def lhs_score(X, lo, hi):
    N, D = X.shape
    occ = []
    for j in range(D):
        rng = hi[j] - lo[j]
        u = (X[:, j] - lo[j]) / (rng if rng > 0 else 1.0)
        b = np.clip((u * N).astype(int), 0, N - 1)
        occ.append(len(np.unique(b)) / float(N))
    return float(np.mean(occ)), float(np.min(occ))


rows = []
for d in sorted(glob.glob(os.path.join(RAIZ, "*", "42"))):
    label = os.path.basename(os.path.dirname(d))
    manp = [m for m in glob.glob(os.path.join(d, "*_42.manifest.json"))
            if "__final" not in m][0]
    m = json.load(open(manp))
    prob = m["problema"]
    pref = manp[:-len(".manifest.json")]
    sch = pq.read_schema(pref + "__surrogate.parquet")
    xs = [c for c in sch.names if c.startswith("x") and c[1:].isdigit()]
    t = pq.read_table(pref + "__surrogate.parquet",
                      columns=["regime", "geracao"] + xs).to_pandas()
    off = t[t.regime == "offline"]
    lo, hi = H._bounds(prob)
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    gmax = int(off.geracao.max())
    r = {"label": label, "problema": prob, "D": len(xs), "n_ger": gmax}
    for tag, g in [("g1", 1), ("g2", 2), ("gfin", gmax)]:
        X = off[off.geracao == g][xs].to_numpy(float)
        r["N"] = len(X)
        r[tag + "_lhs_medio"], r[tag + "_lhs_min"] = lhs_score(X, lo, hi)
        r[tag + "_fora_bounds"] = int((~((X >= lo - 1e-6) & (X <= hi + 1e-6))
                                       .all(axis=1)).sum())
        r[tag + "_dup"] = int(len(X) - len(np.unique(X, axis=0)))
    r["passos_selecao"] = (gmax - 1) * r["N"]
    r["aval_total"] = gmax * r["N"]
    rows.append(r)
    print("[ok]", label)
    sys.stdout.flush()

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "t2_granularidade3.csv"), index=False)
print()
print(df[["g1_lhs_medio", "g1_lhs_min", "g2_lhs_medio", "gfin_lhs_medio",
          "g1_fora_bounds", "g2_fora_bounds", "gfin_fora_bounds",
          "g1_dup", "g2_dup", "gfin_dup"]].describe().T[["min", "50%", "max"]])
print()
print("g1_lhs_medio == 1,0 exato em %d/45" % (df.g1_lhs_medio >= 0.999999).sum())
print("g1_lhs_min   == 1,0 exato em %d/45" % (df.g1_lhs_min >= 0.999999).sum())
print("g2_lhs_medio <  g1 em %d/45" % (df.g2_lhs_medio < df.g1_lhs_medio).sum())
print("passos_selecao por N:")
print(df.groupby("N")[["passos_selecao", "aval_total", "n_ger"]]
      .agg(["min", "max", "count"]))
