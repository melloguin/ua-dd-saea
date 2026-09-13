#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 04: RE-MEDIDA do mecanismo nas 10 celulas da s42. READ-ONLY.
Nada e citado da F5: tudo aqui e recomputado."""
import json, os, glob, hashlib
import numpy as np, pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
DSD = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets"
SND = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda"
OUT = os.path.dirname(os.path.abspath(__file__))


def sha_f64(A):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(A, dtype="<f8")).tobytes()).hexdigest()


def nds(F):
    """indices nao-dominados (minimizacao), O(n^2) — n pequeno."""
    n = F.shape[0]; keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        d = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if d.any():
            keep[i] = False
    return np.where(keep)[0]


rows = []
for lab in sorted(os.listdir(S42)):
    d = os.path.join(S42, lab, "42")
    mfp = glob.glob(os.path.join(d, "*_42.manifest.json"))[0]
    base = os.path.basename(mfp).replace(".manifest.json", "")
    m = json.load(open(mfp))
    prob, dist = m["problema"], m["dist"]
    r1 = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
    r3 = pd.read_parquet(os.path.join(d, base + "__surrogate.parquet"))
    r4 = pd.read_parquet(os.path.join(d, base + "__timing.parquet"))
    r7 = pd.read_parquet(os.path.join(d, base + "__final.parquet"))
    ev = [json.loads(x) for x in open(os.path.join(d, base + ".jsonl")) if x.strip()]
    D = int(m["params"]["min_samples_leaf"] // 10)
    M = len([c for c in r3.columns if c.startswith("mu_")])
    xc = [c for c in r3.columns if c.startswith("x")]
    xc = sorted([c for c in xc if c[1:].isdigit()], key=lambda s: int(s[1:]))
    muc = ["mu_%d" % j for j in range(M)]
    sgc = ["sigma_%d" % j for j in range(M)]
    bs = r3[r3.regime != "sonda"]
    sd = r3[r3.regime == "sonda"]

    # -- U1 offline puro
    u1 = dict(fe_ok=(m["fe_final"] == m["maxfe"] == 50000),
              fase_init=int((r1.fase == "init").sum()) == len(r1),
              fe_dense=bool(np.array_equal(np.sort(r1.fe_index.to_numpy()), np.arange(len(r1)))))
    # -- U2 binding ①<->artefato
    dsp = os.path.join(DSD, prob, "ds_%s_42_big_%s.parquet" % (prob, dist))
    ds = pd.read_parquet(dsp)
    dxc = sorted([c for c in ds.columns if c.startswith("x") and c[1:].isdigit()],
                 key=lambda s: int(s[1:]))
    dfc = sorted([c for c in ds.columns if c.startswith("f") and c[1:].isdigit()],
                 key=lambda s: int(s[1:]))
    Xds, Fds = ds[dxc].to_numpy("f8"), ds[dfc].to_numpy("f8")
    hx, hf = sha_f64(Xds), sha_f64(Fds)
    X1 = r1[[c for c in r1.columns if c.startswith("x") and c[1:].isdigit()]].to_numpy("f8")
    F1 = r1[["f%d" % j for j in range(M)]].to_numpy("f8")
    u2 = dict(x_hash_ok=(hx == m["doe_hash"]), f_hash_ok=(hf == m["cp_init_offline"]["f_hash"]),
              dX=float(np.abs(X1 - Xds.astype("f4").astype("f8")).max()),
              dF=float(np.abs(F1 - Fds.astype("f4").astype("f8")).max()))
    # -- U3/U8
    u3 = dict(n4=len(r4), fit_series=len(m["fit_series"]),
              fe_tr_uni=int(r3.fe_treino_max.nunique()),
              fe_tr_val=int(r3.fe_treino_max.dropna().iloc[0]))
    # -- U4 sonda
    sev = [e for e in ev if e.get("rec") == "sonda"]
    u4 = dict(n_blocos=len(sev), n_sonda=len(sd), ger_null=int(sd.geracao.isna().sum()),
              hash_ok=(sev[0]["sonda_x_hash"] == m["sonda"]["x_hash"]) if sev else None)
    # -- U5/U6 join posicional + WAPE
    sg = pd.read_parquet(os.path.join(SND, "sonda_%s.parquet" % prob))
    sxc = sorted([c for c in sg.columns if c.startswith("x") and c[1:].isdigit()],
                 key=lambda s: int(s[1:]))
    Xs = sd[xc].to_numpy("f8"); Xg = sg[sxc].to_numpy("f8")[:len(sd)]
    dxs = float(np.abs(Xs - Xg.astype("f4").astype("f8")).max())
    sfc = ["f%d" % j for j in range(M)]
    Fg = sg[sfc].to_numpy("f8")[:len(sd)]
    MU = sd[muc].to_numpy("f8")
    wape = [float(np.abs(MU[:, j] - Fg[:, j]).sum() / np.abs(Fg[:, j]).sum()) for j in range(M)]
    corr = [float(np.corrcoef(MU[:, j], Fg[:, j])[0, 1]) for j in range(M)]
    # -- U7 timing
    t = r4.iloc[0]
    u7 = dict(soma=float(t.tempo_fit_s + t.tempo_busca_s), tg=float(t.tempo_geracao_s),
              d=float(t.tempo_fit_s + t.tempo_busca_s - t.tempo_geracao_s),
              com_sonda_estoura=bool(t.tempo_fit_s + t.tempo_busca_s + t.tempo_pred_sonda_s > t.tempo_geracao_s))
    # -- F2 sigma
    f2 = dict(sig_nan=int(r3[sgc].isna().all(axis=1).sum()), n3=len(r3),
              mu_nan=int(r3[muc].isna().any(axis=1).sum()))
    # -- F1 congelamento: mu unico por X (bit-a-bit)
    key = [tuple(v) for v in bs[xc].to_numpy("f4").view(np.uint32)]
    dfb = pd.DataFrame({"k": key})
    for j in range(M):
        dfb["mu%d" % j] = bs[muc[j]].to_numpy()
    g = dfb.groupby("k")
    nun = g[["mu%d" % j for j in range(M)]].nunique()
    reav = g.size()
    f1 = dict(n_X_uni=int(len(nun)), n_X_reav=int((reav > 1).sum()),
              linhas_cobertas=int(reav[reav > 1].sum()), max_reav=int(reav.max()),
              n_X_mu_divergente=int((nun > 1).any(axis=1).sum()))
    # -- C1/C2 folhas: nº de mu distintos na sonda vs teto N/(10D)
    teto = 50000 // (10 * D)
    folhas = [int(pd.unique(sd[muc[j]].to_numpy()).size) for j in range(M)]
    quant = float(1 - np.mean([pd.Series(sd[muc[j]].to_numpy()).duplicated(keep=False).mean()
                               for j in range(M)]))
    # -- C7 pop
    pg = bs.groupby("geracao").size()
    # -- C9 envelope
    env_ok = all(MU[:, j].min() >= Fds[:, j].min() - 1e-9 and MU[:, j].max() <= Fds[:, j].max() + 1e-9
                 for j in range(M))
    # -- U12 ⑦
    F7 = r7[["f%d" % j for j in range(M)]].to_numpy("f8")
    nd = nds(F7.astype("f4").astype("f8"))
    ndv = np.zeros(len(r7), bool); ndv[nd] = True
    x7 = sorted([c for c in r7.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda s: int(s[1:]))
    gl = int(r7.origem_geracao.iloc[0])
    b_last = bs[bs.geracao == gl]
    dX7 = float(np.abs(r7[x7].to_numpy("f8") -
                       b_last[xc].to_numpy("f8")[r7.origem_linha.to_numpy().astype(int)]).max())
    # -- C17 convergencia
    som = bs.groupby("geracao")[muc].sum().sum(axis=1) / bs.groupby("geracao").size()
    melhora = float((som.loc[1] - som.loc[gl]) / abs(som.loc[1]))
    # -- C5 joia 10x100 (s42): |Dpop| nas fronteiras g=101,201,...
    tam = bs.groupby("geracao").size().reindex(range(1, gl + 1)).to_numpy()
    dpop = np.abs(np.diff(tam))
    fron = np.array([g - 2 for g in range(101, gl + 1, 100)])  # indice da transicao g-1 -> g
    c5 = dict(dpop_front=float(dpop[fron].mean()), dpop_glob=float(dpop.mean()),
              razao=float(dpop[fron].mean() / max(dpop.mean(), 1e-12)))
    rows.append(dict(label=lab, prob=prob, dist=dist, D=D, M=M, **u1, **u2, **u3, **u4,
                     dX_sonda=dxs, wape=[round(w, 6) for w in wape],
                     corr=[round(c, 4) for c in corr], **u7, **f2, **f1,
                     msl=m["params"]["min_samples_leaf"], msl_ok=(m["params"]["min_samples_leaf"] == 10 * D),
                     teto_folhas=teto, folhas=folhas, folhas_ok=all(f <= teto for f in folhas),
                     ocup=round(max(folhas) / teto, 3), quant_share=round(1 - quant, 4),
                     pop_max=int(pg.max()), pop_min=int(pg.min()),
                     lattice=(105 if M == 3 else 50), env_ok=env_ok,
                     n7=len(r7), nd_rec=int(ndv.sum()), nd_grav=int(r7.nd_pos_real.sum()),
                     nd_ok=bool(np.array_equal(ndv, r7.nd_pos_real.to_numpy().astype(bool))),
                     dX7=dX7, orig_ger=gl, fantasia=round(int(r7.nd_pos_real.sum()) / len(r7), 4),
                     melhora_mu=round(melhora, 4), **c5,
                     wall=m["timing"]["tempo_total_s"]))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "tm11_mecanismo_s42.csv"), index=False)
pd.set_option("display.width", 300, "display.max_columns", 80)
cols = [["label", "fe_ok", "fase_init", "fe_dense", "x_hash_ok", "f_hash_ok", "dX", "dF",
         "n4", "fit_series", "fe_tr_uni", "fe_tr_val", "n_blocos", "n_sonda", "ger_null", "hash_ok"],
        ["label", "dX_sonda", "wape", "corr", "soma", "tg", "d", "com_sonda_estoura",
         "sig_nan", "n3", "mu_nan"],
        ["label", "n_X_uni", "n_X_reav", "linhas_cobertas", "max_reav", "n_X_mu_divergente",
         "msl", "msl_ok", "teto_folhas", "folhas", "folhas_ok", "ocup", "quant_share"],
        ["label", "pop_max", "pop_min", "lattice", "env_ok", "n7", "nd_rec", "nd_grav", "nd_ok",
         "dX7", "orig_ger", "fantasia", "melhora_mu", "dpop_front", "dpop_glob", "razao", "wall"]]
for c in cols:
    print(df[c].to_string(index=False)); print()
