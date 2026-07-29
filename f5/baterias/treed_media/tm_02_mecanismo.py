#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 02: o MECANISMO (árvore pura) + camada ⑦ + U5/U12.
- quantização de μ (assinatura da árvore-pura: μ_j é constante por folha) → nº de folhas TOCADAS
- teto de folhas N/(10D); banda de N_min
- ⑦: recomputo do ND, link posicional (ger,linha)→③ bit-a-bit, fantasia, IGD+/HV do endpoint
- U5: join posicional sonda × gabarito (data/sonda/sonda_{prob}.parquet)
Saídas: tm_mecanismo.csv, tm_camada7.csv, tm_folhas.csv
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = os.path.join(REPO, "f5/baterias/treed_media")
sys.path.insert(0, REPO); os.chdir(REPO)
from src import metrics as MX  # noqa: E402

DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}

mec, c7, folhas = [], [], []
for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
    label = os.path.basename(d)
    dist = label.split("-")[1].split("_")[0]
    prob = label.split("_", 1)[1].split("_", 1)[1]
    D, M = DM[prob]
    pasta = os.path.join(d, "42")
    stem = [b for b in glob.glob(os.path.join(pasta, "*.manifest.json")) if "__final" not in b][0]
    stem = stem[: -len(".manifest.json")]
    r = dict(label=label, dist=dist, problema=prob, D=D, M=M)

    d3 = pd.read_parquet(stem + "__surrogate.parquet")
    b = d3[d3.regime == "offline"].reset_index(drop=True)
    s = d3[d3.regime == "sonda"].reset_index(drop=True)
    xs = [f"x{i}" for i in range(D)]
    mus = [f"mu_{j}" for j in range(M)]

    # ---------- quantização da árvore (assinatura ablação) ----------
    nmin = 10 * D
    teto_folhas = 50000 // nmin
    r["N_min"] = nmin; r["teto_folhas_N_sobre_10D"] = teto_folhas
    for j in range(M):
        r[f"mu{j}_distintos_sonda"] = int(s[f"mu_{j}"].nunique())
        r[f"mu{j}_distintos_busca"] = int(b[f"mu_{j}"].nunique())
    dsonda = [int(s[f"mu_{j}"].nunique()) for j in range(M)]
    dbusca = [int(b[f"mu_{j}"].nunique()) for j in range(M)]
    r["folhas_tocadas_sonda_max"] = max(dsonda)
    r["folhas_tocadas_sonda_min"] = min(dsonda)
    r["folhas_tocadas_busca_max"] = max(dbusca)
    r["folhas_le_teto"] = bool(max(dsonda + dbusca) <= teto_folhas)
    r["ocupacao_teto_pct"] = round(100 * max(dsonda) / teto_folhas, 1)
    r["quantizacao_sonda_pct"] = round(100 * (1 - max(dsonda) / len(s)), 3)
    r["quantizacao_busca_pct"] = round(100 * (1 - max(dbusca) / len(b)), 3)
    # pontos por "folha" implícita na sonda (uniformidade Sobol)
    vc = s[f"mu_0"].value_counts()
    r["sonda_pts_por_folha_med"] = float(vc.median())
    r["sonda_pts_por_folha_max"] = int(vc.max())
    # μ da folha ∈ envelope do dataset (média de folha nunca extrapola)
    d1 = pd.read_parquet(stem + "__real.parquet")
    for j in range(M):
        lo, hi = float(d1[f"f{j}"].min()), float(d1[f"f{j}"].max())
        r[f"mu{j}_dentro_envelope"] = bool(d3[f"mu_{j}"].min() >= lo - 1e-4 * abs(lo) - 1e-9
                                           and d3[f"mu_{j}"].max() <= hi + 1e-4 * abs(hi) + 1e-9)
        r[f"mu{j}_min"] = float(d3[f"mu_{j}"].min()); r[f"mu{j}_max"] = float(d3[f"mu_{j}"].max())
        r[f"f{j}_ds_min"] = lo; r[f"f{j}_ds_max"] = hi
    r["mu_dentro_envelope_todos"] = all(r[f"mu{j}_dentro_envelope"] for j in range(M))
    for j in range(M):
        folhas.append(dict(label=label, problema=prob, dist=dist, obj=j, D=D, N_min=nmin,
                           teto=teto_folhas, distintos_sonda=dsonda[j],
                           distintos_busca=dbusca[j],
                           pts_por_folha_med=float(s[f"mu_{j}"].value_counts().median())))

    # ---------- U5: join posicional sonda × gabarito ----------
    gab = pd.read_parquet(os.path.join(REPO, f"data/sonda/sonda_{prob}.parquet"))
    r["gab_linhas"] = len(gab)
    Xs = s[xs].values.astype(np.float64)
    Xg = gab[xs].values.astype(np.float64)
    r["U5_maxabs_dX"] = float(np.abs(Xs - Xg.astype(np.float32).astype(np.float64)).max())
    r["U5_maxabs_dX_f64"] = float(np.abs(Xs - Xg).max())
    r["U5_ok_eps32"] = bool(r["U5_maxabs_dX"] <= 1e-6)
    # WAPE recomputado (espaço cru; transf NULL) — conferência da régua F5.2e
    for j in range(M):
        fg = gab[f"f{j}"].values.astype(np.float64)
        mu = s[f"mu_{j}"].values.astype(np.float64)
        r[f"WAPE_recomp_obj{j}"] = float(np.abs(mu - fg).sum() / np.abs(fg).sum())
        r[f"corr_recomp_obj{j}"] = float(np.corrcoef(mu, fg)[0, 1])
    r["sigma_todos_nan_sonda"] = bool(s[[f"sigma_{j}" for j in range(M)]].isna().values.all())
    r["cobertura95"] = "N/A (σ NULL por desenho DI-16.1)"

    # ---------- ⑦ camada final ----------
    d7 = pd.read_parquet(stem + "__final.parquet")
    fcols = [f"f{j}" for j in range(M)]
    F = d7[fcols].values.astype(np.float64)
    nd_gravado = d7.nd_pos_real.values.astype(bool)
    # recomputo do ND (dominância estrita padrão)
    n = len(F)
    dom = np.zeros(n, dtype=bool)
    for i in range(n):
        le = (F <= F[i]).all(axis=1)
        lt = (F < F[i]).any(axis=1)
        dom[i] = bool((le & lt).any())
    nd_rec = ~dom
    r["c7_n_final"] = n
    r["c7_nd_gravado"] = int(nd_gravado.sum())
    r["c7_nd_recomputado"] = int(nd_rec.sum())
    r["c7_ND_identico"] = bool((nd_rec == nd_gravado).all())
    r["c7_fantasia"] = round(float(nd_gravado.mean()), 4)
    r["c7_origem_ger_unica"] = int(d7.origem_geracao.nunique())
    r["c7_origem_ger"] = int(d7.origem_geracao.iloc[0])
    r["c7_origem_ger_eh_1000"] = bool(set(d7.origem_geracao.unique()) == {1000})
    r["c7_origem_solid_null"] = float(d7.origem_solution_id.isna().mean())
    # link posicional (origem_geracao, origem_linha) → ③
    ult = b[b.geracao == 1000].reset_index(drop=True)
    r["c7_n_final_eq_pop_ultima"] = bool(len(ult) == n)
    lin = d7.origem_linha.values
    r["c7_origem_linha_denso"] = bool((np.sort(lin) == np.arange(n)).all())
    X7 = d7[xs].values
    X3 = ult.iloc[lin][xs].values
    r["c7_link_maxabs_dX"] = float(np.abs(X7.astype(np.float64) - X3.astype(np.float64)).max())
    r["c7_link_bit_a_bit"] = bool((X7 == X3).all())
    # métricas do endpoint
    try:
        mm = MX.metrics_of_set(F[nd_gravado] if nd_gravado.any() else F, prob)
        r["c7_igd_plus"] = round(float(mm["igd_plus"]), 6)
        r["c7_hv"] = round(float(mm["hv"]), 6)
    except Exception as e:
        r["c7_igd_plus"] = np.nan; r["c7_hv"] = np.nan; r["c7_erro"] = str(e)[:60]
    # erro de FANTASIA: |μ previsto do ponto na ③ - f real da ⑦| (U11 substituto do offline)
    MU3 = ult.iloc[lin][mus].values.astype(np.float64)
    err = np.abs(MU3 - F)
    denom = np.abs(F).mean(axis=0)
    r["c7_WAPE_fantasia"] = float(np.abs(MU3 - F).sum() / np.abs(F).sum())
    for j in range(M):
        r[f"c7_erro_mediano_obj{j}"] = float(np.median(err[:, j]))
        r[f"c7_wape_obj{j}"] = float(np.abs(MU3[:, j] - F[:, j]).sum() / np.abs(F[:, j]).sum())
    c7.append(dict(label=label, problema=prob, dist=dist, D=D, M=M, n_final=n,
                   nd=int(nd_gravado.sum()), fantasia=r["c7_fantasia"],
                   igd_plus_c7=r["c7_igd_plus"], hv_c7=r["c7_hv"],
                   wape_fantasia=round(r["c7_WAPE_fantasia"], 5),
                   ND_identico=r["c7_ND_identico"], link_bit=r["c7_link_bit_a_bit"]))
    mec.append(r)
    print("ok", label, flush=True)

pd.DataFrame(mec).to_csv(os.path.join(OUT, "tm_mecanismo.csv"), index=False)
pd.DataFrame(c7).to_csv(os.path.join(OUT, "tm_camada7.csv"), index=False)
pd.DataFrame(folhas).to_csv(os.path.join(OUT, "tm_folhas.csv"), index=False)
print("fim")
