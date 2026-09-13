"""T11/moead_media · bateria T5 — re-verificacao dos vinculos (U2/U5/C7).

U2: ① x artefato do dataset, bit-a-bit (45 celulas)
U5: X da sonda na ③ x gabarito Sobol, join POSICIONAL (45 x 20.000)
C7: determinismo — off/{p} x swap_small-lhs/{p} (mesmo artefato, 2 processos)
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.dirname(os.path.abspath(__file__))


def ler(pref, layer, cols=None):
    return pq.read_table(pref + layer, columns=cols).to_pandas()


rows = []
cache3 = {}
for d in sorted(glob.glob(os.path.join(RAIZ, "*", "42"))):
    label = os.path.basename(os.path.dirname(d))
    manp = [m for m in glob.glob(os.path.join(d, "*_42.manifest.json"))
            if "__final" not in m][0]
    m = json.load(open(manp))
    prob = m["problema"]
    pref = manp[:-len(".manifest.json")]
    r = {"label": label, "problema": prob, "tier": m.get("tier"),
         "dist": m.get("dist")}

    # ---- U2: artefato do dataset
    tier, dist = m.get("tier"), m.get("dist")
    if tier in (None, "small") and dist in (None, "lhs"):
        dsp = os.path.join(REPO, "data/datasets", prob, "ds_%s_42.parquet" % prob)
    else:
        dsp = os.path.join(REPO, "data/datasets", prob,
                           "ds_%s_42_%s_%s.parquet" % (prob, tier, dist))
    r["ds_path"] = os.path.basename(dsp)
    r["ds_existe"] = os.path.exists(dsp)
    t1 = ler(pref, "__real.parquet")
    xc = [c for c in t1.columns if c.startswith("x") and c[1:].isdigit()]
    fc = [c for c in t1.columns if c.startswith("f") and c[1:].isdigit()]
    if r["ds_existe"]:
        ds = pq.read_table(dsp).to_pandas()
        dxc = [c for c in ds.columns if c.startswith("x") and c[1:].isdigit()]
        dfc = [c for c in ds.columns if c.startswith("f") and c[1:].isdigit()]
        A = ds[dxc].to_numpy(np.float32)
        B = t1[xc].to_numpy(np.float32)
        r["u2_dX"] = float(np.abs(A - B).max()) if A.shape == B.shape else np.nan
        A = ds[dfc].to_numpy(np.float32)
        B = t1[fc].to_numpy(np.float32)
        r["u2_dF"] = float(np.abs(A - B).max()) if A.shape == B.shape else np.nan
        r["u2_n"] = len(ds)

    # ---- U5: gabarito Sobol, join posicional
    gp = os.path.join(REPO, "data/sonda", "sonda_%s.parquet" % prob)
    gab = pq.read_table(gp).to_pandas()
    gxc = [c for c in gab.columns if c.startswith("x") and c[1:].isdigit()]
    sch = pq.read_schema(pref + "__surrogate.parquet")
    xs = [c for c in sch.names if c.startswith("x") and c[1:].isdigit()]
    t3 = ler(pref, "__surrogate.parquet", ["regime"] + xs)
    snd = t3[t3.regime == "sonda"][xs].to_numpy(np.float32)
    G = gab[gxc].to_numpy(np.float32)[:len(snd)]
    r["u5_n"] = len(snd)
    r["u5_dX"] = float(np.abs(snd - G).max()) if snd.shape == G.shape else np.nan
    cache3[label] = pref
    rows.append(r)
    print("[u2/u5]", label, r.get("u2_dX"), r["u5_dX"])
    sys.stdout.flush()

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "t5_binding.csv"), index=False)
print()
print("U2  max|dX| = %s | max|dF| = %s | celulas com artefato = %d/45"
      % (df.u2_dX.max(), df.u2_dF.max(), int(df.ds_existe.sum())))
print("U5  max|dX| = %s em %d pontos (45 celulas)"
      % (df.u5_dX.max(), int(df.u5_n.sum())))

# ---- C7 determinismo: off/{p} x swap_small-lhs/{p}
print()
print("=== C7 determinismo (off x swap_small-lhs) ===")
det = []
for prob in ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]:
    a = cache3.get(prob)
    b = cache3.get("swap_small-lhs_" + prob)
    if not (a and b):
        continue
    o = {"problema": prob}
    for layer, tag in [("__real.parquet", "1"), ("__surrogate.parquet", "3"),
                       ("__final.parquet", "7")]:
        A = pq.read_table(a + layer).to_pandas()
        B = pq.read_table(b + layer).to_pandas()
        num = [c for c in A.columns
               if A[c].dtype.kind in "fiu" and c not in ("semente",)]
        o["n" + tag] = len(A)
        o["d" + tag] = (float(np.nanmax(np.abs(A[num].to_numpy(float)
                                               - B[num].to_numpy(float))))
                        if A.shape == B.shape else np.nan)
    det.append(o)
    print(o)
pd.DataFrame(det).to_csv(os.path.join(OUT, "t5_determinismo.csv"), index=False)
