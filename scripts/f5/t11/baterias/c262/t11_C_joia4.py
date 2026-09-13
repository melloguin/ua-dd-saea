#!/usr/bin/env python
"""T11/c262 — BATERIA C: correcao de 2 leituras da bateria B.
(1) modelo_hp e ANINHADO ('por_objetivo') — a mesma armadilha da ERRATA 6 do T11.
(2) DoE: 1 e float32, o artefato e float64 — o diff bit-a-bit exige o cast.
+ ARD vivo, curva de lengthscale, e o mesmo teste no SMOKE T11.
"""
import glob, json, os
import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262"
DOE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe"
SMOKE = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/"
         "smoke_python/experiments/main/c262/exp_main_c262_MMF1_0")


def analisa(B, doe_path, tag):
    m = json.load(open(f"{B}.manifest.json"))
    r1 = pd.read_parquet(f"{B}__real.parquet")
    xcols = [c for c in r1.columns if c.startswith("x") and c[1:].isdigit()]
    fcols = [c for c in r1.columns if c.startswith("f") and c[1:].isdigit()]
    dec = [json.loads(l) for l in open(f"{B}.jsonl")
           if l.strip() and json.loads(l).get("rec") == "decision"]
    r1o = r1.sort_values("fe_index")
    Y = -r1o[fcols].values.astype(np.float64)

    okn = totn = piso = 0
    errmax = 0.0
    ard_viv = ard_tot = 0
    lsc_first = lsc_last = None
    for dd in dec:
        mh = dd.get("modelo_hp") or {}
        po = mh.get("por_objetivo") or []
        nt = dd.get("n_train")
        for j, o in enumerate(po):
            nz = o.get("noise")
            if nz is not None and nt is not None:
                v = float(np.var(Y[: int(nt), j], ddof=1))
                esp = max(1e-6, 1e-6 / v)
                totn += 1
                e = abs(float(nz) - esp) / max(esp, 1e-30)
                errmax = max(errmax, e)
                okn += (e < 1e-5)
                piso += (esp == 1e-6)
            if o.get("lengthscale_max") is not None:
                ard_tot += 1
                ard_viv += (o["lengthscale_max"] > o["lengthscale_min"])
        if po and lsc_first is None:
            lsc_first = [round(o["lengthscale_med"], 4) for o in po]
        if po:
            lsc_last = [round(o["lengthscale_med"], 4) for o in po]

    # determinismo do refit (F5): pares HP identicos <=> cache-hit
    chave = []
    for dd in dec:
        mh = dd.get("modelo_hp") or {}
        po = mh.get("por_objetivo") or []
        chave.append(tuple([round(o["lengthscale_med"], 15) for o in po] +
                           [round(o["outputscale"], 15) for o in po] +
                           [round(mh.get("mll_final") or 0.0, 15)]))
    pares_ig = sum(1 for i in range(1, len(chave)) if chave[i] == chave[i - 1])
    ch_its = sum(1 for dd in dec if dd.get("cache_hit"))

    # DoE bit-a-bit COM cast float32
    dxf32 = None
    if doe_path and os.path.exists(doe_path):
        doe = pd.read_parquet(doe_path)
        dxc = [c for c in doe.columns if c.startswith("x") and c[1:].isdigit()]
        n0 = int((r1["fase"] == "init").sum())
        A = r1.loc[r1["fase"] == "init", xcols].values[:n0].astype(np.float32)
        Bm = doe[dxc].values[:n0].astype(np.float32)
        dxf32 = float(np.max(np.abs(A.astype(np.float64) -
                                    Bm.astype(np.float64))))
    return dict(tag=tag, joia4_ok=okn, joia4_tot=totn, joia4_errmax=errmax,
                joia4_piso=piso, ard_vivo=ard_viv, ard_tot=ard_tot,
                lsc_1=lsc_first, lsc_N=lsc_last, pares_hp_iguais=pares_ig,
                cache_hits=ch_its, doe_dx_f32=dxf32, n_dec=len(dec))


res = []
for p in sorted(os.listdir(ROOT)):
    d = f"{ROOT}/{p}/42"
    if not os.path.isdir(d):
        continue
    b = glob.glob(f"{d}/*.manifest.json")
    if not b:
        continue
    res.append(analisa(b[0][: -len(".manifest.json")],
                       f"{DOE}/{p}/doe_{p}_42.parquet", p))
df = pd.DataFrame(res)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/"
          "baterias/c262/c262_t11_joia4.csv", index=False)
print("=== s42 (21 celulas) ===")
print("F4 noise:", int(df.joia4_ok.sum()), "/", int(df.joia4_tot.sum()),
      "| err rel max:", df.joia4_errmax.max(),
      "| piso 1e-6 ativo:", int(df.joia4_piso.sum()),
      f"({100*df.joia4_piso.sum()/df.joia4_tot.sum():.1f}%)")
print("ARD vivo:", int(df.ard_vivo.sum()), "/", int(df.ard_tot.sum()))
print("DoE dx (cast float32) max:", df.doe_dx_f32.max())
print("pares HP identicos:", int(df.pares_hp_iguais.sum()),
      "| cache-hits:", int(df.cache_hits.sum()),
      "| identidade:", int((df.pares_hp_iguais == df.cache_hits).sum()), "/", len(df))
print(df[["tag", "joia4_ok", "joia4_tot", "joia4_piso", "pares_hp_iguais",
          "cache_hits", "doe_dx_f32"]].to_string(index=False))
print()
print("=== SMOKE T11 (MMF1/s0) ===")
s = analisa(SMOKE, None, "smoke_MMF1_s0")
print(json.dumps(s, indent=1, default=str))
