#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 04: prova de CONGELAMENTO do surrogate (substituta dos
2 blocos bit-idênticos do c311, que aqui não existem por desenho — 1 bloco só) +
U2 offline (binding ① ↔ artefato de dataset, bit-a-bit) + higiene do ⑥ (footers/ts).

Prova de congelamento sem 2º bloco: o modelo é uma FUNÇÃO determinística x↦μ; se o
surrogate mudasse entre gerações, um MESMO x reavaliado em gerações diferentes teria μ
diferente. Varremos as 1.000 gerações da ③, agrupamos por X (bit-a-bit) e conferimos que
μ é ÚNICO por X. Complemento: μ(sonda) e μ(busca) vêm do MESMO conjunto de valores de
folha (interseção dos suportes) — o modelo da sonda é o mesmo da busca.
Saídas: tm_congelamento.csv, tm_u2_binding.csv, tm_footers.csv
"""
import glob, hashlib, json, os, sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = os.path.join(REPO, "f5/baterias/treed_media")
DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}

cong, u2, foot = [], [], []
for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
    label = os.path.basename(d)
    dist = label.split("-")[1].split("_")[0]
    prob = label.split("_", 1)[1].split("_", 1)[1]
    D, M = DM[prob]
    stem = [b for b in glob.glob(os.path.join(d, "42", "*.manifest.json")) if "__final" not in b][0]
    stem = stem[: -len(".manifest.json")]
    mf = json.load(open(stem + ".manifest.json"))
    xs = [f"x{i}" for i in range(D)]
    mus = [f"mu_{j}" for j in range(M)]

    # ---------- congelamento ----------
    d3 = pd.read_parquet(stem + "__surrogate.parquet")
    b = d3[d3.regime == "offline"].copy()
    s = d3[d3.regime == "sonda"].copy()
    b["_g"] = b.geracao.astype(int)
    # chave X bit-a-bit (bytes float32)
    kx = [tuple(v) for v in b[xs].values]
    b["_kx"] = kx
    b["_km"] = [tuple(v) for v in b[mus].values]
    gr = b.groupby("_kx")
    tam = gr.size()
    r = dict(label=label, dist=dist, problema=prob, D=D, M=M)
    r["n_busca"] = len(b)
    r["n_X_unicos"] = int(len(tam))
    r["n_X_repetidos"] = int((tam > 1).sum())
    r["n_reaval_totais"] = int(tam[tam > 1].sum())
    r["max_reaval_de_um_X"] = int(tam.max())
    nmu = gr["_km"].nunique()
    r["n_X_com_mu_divergente"] = int((nmu > 1).sum())
    r["CONGELADO_mu_unico_por_X"] = bool((nmu <= 1).all())
    # amplitude de gerações cobertas por X repetido (quanto tempo o modelo ficou igual)
    if (tam > 1).any():
        span = gr["_g"].agg(lambda v: v.max() - v.min())
        r["span_ger_max_de_X_repetido"] = int(span.max())
        r["span_ger_mediano"] = float(span[tam > 1].median())
    else:
        r["span_ger_max_de_X_repetido"] = 0; r["span_ger_mediano"] = 0.0
    # suporte de valores de folha: sonda ⊆ busca? busca ⊆ sonda?
    for j in range(M):
        vb = set(np.unique(b[f"mu_{j}"].values))
        vs = set(np.unique(s[f"mu_{j}"].values))
        r[f"suporte_obj{j}_busca"] = len(vb)
        r[f"suporte_obj{j}_sonda"] = len(vs)
        r[f"suporte_obj{j}_busca_em_sonda_pct"] = round(100 * len(vb & vs) / len(vb), 2)
    r["suporte_min_busca_em_sonda_pct"] = min(r[f"suporte_obj{j}_busca_em_sonda_pct"] for j in range(M))
    r["n_fit_series"] = len(mf.get("fit_series") or [])
    r["n_linhas_4"] = len(pd.read_parquet(stem + "__timing.parquet"))

    # ---------- U2 offline: binding ① ↔ artefato ----------
    art = os.path.join(REPO, f"data/datasets/{prob}/ds_{prob}_42_big_{dist}.parquet")
    am = json.load(open(art.replace(".parquet", ".manifest.json")))
    ds = pd.read_parquet(art)
    d1 = pd.read_parquet(stem + "__real.parquet")
    fs = [f"f{j}" for j in range(M)]
    Xa = ds[xs].values.astype(np.float64)
    Xr = d1[xs].values.astype(np.float64)
    Fa = ds[fs].values.astype(np.float64)
    Fr = d1[fs].values.astype(np.float64)
    xh = hashlib.sha256(np.ascontiguousarray(Xa, dtype=np.float64).tobytes()).hexdigest()
    fh = hashlib.sha256(np.ascontiguousarray(Fa, dtype=np.float64).tobytes()).hexdigest()
    u2.append(dict(label=label, problema=prob, dist=dist, n_artefato=len(ds), n_camada1=len(d1),
                   x_hash_recomputado=xh[:16], x_hash_manifesto=mf["doe_hash"][:16],
                   x_hash_bate=(xh == mf["doe_hash"]),
                   f_hash_recomputado=fh[:16],
                   f_hash_manifesto=mf["cp_init_offline"]["f_hash"][:16],
                   f_hash_bate=(fh == mf["cp_init_offline"]["f_hash"]),
                   dataset_hash_art=am["dataset_hash"][:16],
                   maxabs_dX_f32=float(np.abs(Xr - Xa.astype(np.float32).astype(np.float64)).max()),
                   maxabs_dF_f32=float(np.abs(Fr - Fa.astype(np.float32).astype(np.float64)).max()),
                   ordem_preservada=bool((Xr == Xa.astype(np.float32).astype(np.float64)).all()),
                   sampler=am["sampler"], seed_tuple=str(am["seed_tuple"]),
                   tier=am["tier"], dist_art=am["dist"]))

    # ---------- ⑥ footers/ts ----------
    recs = [json.loads(l) for l in open(stem + ".jsonl") if l.strip()]
    fs_ = [x for x in recs if x.get("rec") == "footer"]
    foot.append(dict(label=label, n_footer=len(fs_),
                     ts_header=recs[0]["ts"], ts_ultimo=recs[-1]["ts"],
                     tem_footer_despachante=any("tempo_total_s" in x for x in fs_),
                     tem_footer_runner=any("motivo" in x for x in fs_),
                     upload_status=str(mf.get("upload_status"))[:30],
                     created_at=mf.get("created_at"), updated_at=mf.get("updated_at")))
    cong.append(r)
    print("ok", label, flush=True)

pd.DataFrame(cong).to_csv(os.path.join(OUT, "tm_congelamento.csv"), index=False)
pd.DataFrame(u2).to_csv(os.path.join(OUT, "tm_u2_binding.csv"), index=False)
pd.DataFrame(foot).to_csv(os.path.join(OUT, "tm_footers.csv"), index=False)
print("fim")
