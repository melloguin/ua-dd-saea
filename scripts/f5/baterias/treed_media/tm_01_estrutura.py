#!/usr/bin/env python
"""F5.3b · treed_media (piso-big, alg_id=23) — BATERIA 01: estrutura, manifesto, ⑥, camadas ①②③④.
Saída: tm_estrutura.csv (1 linha/célula, ~70 colunas de checagem).
READ-ONLY sobre os dados. Escreve SÓ em f5/baterias/treed_media/.
"""
import json, glob, os, sys
import numpy as np
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"
DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}
LATTICE = {2: 50, 3: 105}


def celulas():
    for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
        label = os.path.basename(d)
        dist = label.split("-")[1].split("_")[0]
        prob = label.split("_", 1)[1].split("_", 1)[1] if label.count("_") > 1 else None
        # label = swap_big-{dist}_{problema}
        prob = label.split("_", 1)[1]
        prob = prob.split("_", 1)[1]
        pasta = os.path.join(d, "42")
        base = glob.glob(os.path.join(pasta, "*.manifest.json"))
        base = [b for b in base if "__final" not in b][0]
        stem = base[: -len(".manifest.json")]
        yield label, dist, prob, stem


linhas = []
for label, dist, prob, stem in celulas():
    D, M = DM[prob]
    r = dict(label=label, dist=dist, problema=prob, D=D, M=M)
    mf = json.load(open(stem + ".manifest.json"))
    r["status"] = mf["status"]
    r["motivo_parada"] = mf.get("motivo_parada")
    r["maxfe"] = mf["maxfe"]
    r["fe_final"] = mf["fe_final"]
    r["n_geracoes_mf"] = mf["n_geracoes"]
    r["tier"] = mf.get("tier")
    r["dist_mf"] = mf.get("dist")
    r["q"] = mf.get("q")
    r["regime"] = mf.get("regime")
    r["n_retries"] = mf.get("n_retries")
    r["cache_hits"] = mf.get("cache_hits")
    r["algo_version"] = mf.get("algo_version", "")[:60]
    r["py"] = mf["env"]["python"]
    r["exe"] = os.path.basename(os.path.dirname(os.path.dirname(mf["env"]["executable"])))
    r["sklearn"] = mf["env"]["sklearn"]
    r["gpy_torch"] = str(mf["env"].get("torch")) + "/" + str(mf["env"].get("gpytorch"))
    r["pin_omp"] = mf["env"]["pinning"]["OMP_NUM_THREADS"]
    t = mf["timing"]
    r["t_total"] = t["tempo_total_s"]; r["t_fit"] = t["tempo_fit_surrogate_s"]
    r["t_busca"] = t["tempo_busca_s"]; r["t_aval_real"] = t["tempo_aval_real_s"]
    r["t_sonda"] = t["tempo_pred_sonda_s"]
    fs = mf.get("fit_series") or []
    r["n_fit_series"] = len(fs)
    r["fit_series_iter"] = fs[0]["iter"] if fs else None
    r["fit_series_nacum"] = fs[0]["n_acumulado"] if fs else None
    r["fallback_ativado"] = mf.get("fallback_ativado")
    p = mf.get("params", {})
    r["p_min_samples_leaf"] = p.get("min_samples_leaf")
    r["p_max_depth"] = p.get("max_depth")
    r["p_n_iter_final"] = p.get("n_iter_final")
    r["p_n_gen_final"] = p.get("n_gen_final")
    r["p_n_gen_total"] = p.get("n_gen_total_final")
    r["p_selection_type"] = p.get("selection_type")
    r["p_alpha"] = p.get("alpha")
    r["p_sigma"] = str(p.get("sigma"))[:40]
    r["p_ablacao_de"] = p.get("ablacao_de")
    r["p_msl_eq_10D"] = (p.get("min_samples_leaf") == 10 * D)
    sd = mf.get("sigma_dict", {})
    r["sigma_dict_chaves"] = len(sd)
    r["sd_tem_DI16.1"] = "DI-16.1" in json.dumps(sd, ensure_ascii=False)
    r["sd_tem_DI35.5"] = "DI-35.5" in json.dumps(sd, ensure_ascii=False)
    r["sd_tem_DI28"] = "DI-28" in json.dumps(sd, ensure_ascii=False)
    r["sd_teto_43200"] = "43200" in json.dumps(sd, ensure_ascii=False)
    r["sd_modelo_flag"] = sd.get("modelo_flag", "")[:45]
    so = mf.get("sonda", {})
    r["sonda_S"] = so.get("S"); r["sonda_nblocos"] = so.get("n_blocos")
    r["sonda_flags"] = ",".join(so.get("modelo_flags", []))
    r["sonda_x_hash"] = so.get("x_hash", "")[:12]
    cp = mf.get("cp_init_offline", {})
    r["cp_x_hash_eq_doe"] = (cp.get("x_hash") == mf.get("doe_hash"))
    r["upload_status"] = mf.get("upload_status")
    r["mf_tem_params"] = "params" in mf

    # ------- ⑥ jsonl -------
    recs = [json.loads(l) for l in open(stem + ".jsonl") if l.strip()]
    r["n_eventos"] = len(recs)
    from collections import Counter
    c = Counter(x.get("rec") for x in recs)
    r["ev_header"] = c.get("header", 0); r["ev_sonda"] = c.get("sonda", 0)
    r["ev_footer"] = c.get("footer", 0); r["ev_guard"] = c.get("guard", 0)
    r["ev_decision"] = c.get("decision", 0)
    r["ev_outros"] = len(recs) - sum(c.get(k, 0) for k in ("header", "sonda", "footer", "guard", "decision"))
    hd = [x for x in recs if x.get("rec") == "header"][0]
    r["hd_D"] = hd["D"]; r["hd_M"] = hd["M"]; r["hd_ndataset"] = hd["n_dataset"]
    r["hd_D_ok"] = hd["D"] == D and hd["M"] == M
    r["hd_dataset_hash"] = hd.get("dataset_hash", "")[:12]
    sv = [x for x in recs if x.get("rec") == "sonda"]
    r["sonda_ev_npontos"] = sv[0]["n_pontos"] if sv else None
    r["sonda_ev_fetreino"] = sv[0]["fe_treino_max"] if sv else None
    r["sonda_ev_hashcheck"] = (sv[0].get("hash_check", "")[:2] == "ok") if sv else None
    r["sonda_ev_flag"] = sv[0].get("modelo_flag") if sv else None
    r["sonda_ev_hash_eq_mf"] = (sv[0]["sonda_x_hash"] == so.get("x_hash")) if sv else None
    ft = [x for x in recs if x.get("rec") == "footer"]
    r["tem_footer"] = bool(ft)
    if ft:
        f = ft[0]
        r["ft_status"] = f["status"]; r["ft_motivo"] = f["motivo"]
        r["ft_fe_final"] = f["fe_final"]; r["ft_cp_init"] = f["cp_init"]
        r["ft_n_ger"] = f["n_geracoes"]; r["ft_n_final"] = f["n_final"]
        r["ft_n_nd"] = f["n_nd_pos_real"]; r["ft_cache_hits"] = f.get("cache_hits")

    # ------- ① real -------
    d1 = pd.read_parquet(stem + "__real.parquet")
    r["n1"] = len(d1)
    r["n1_eq_maxfe"] = (len(d1) == mf["maxfe"])
    r["fase_init_pct"] = float((d1.fase == "init").mean())
    r["fe_index_denso"] = bool((d1.fe_index.values == np.arange(len(d1))).all())
    r["solid_denso"] = bool((np.sort(d1.solution_id.values) == np.arange(len(d1))).all())
    r["n1_dup_x"] = int(len(d1) - d1[[c for c in d1.columns if c.startswith("x")]].drop_duplicates().shape[0])

    # ------- ② pop -------
    d2 = pd.read_parquet(stem + "__pop.parquet")
    r["n2"] = len(d2)

    # ------- ③ surrogate -------
    d3 = pd.read_parquet(stem + "__surrogate.parquet")
    r["n3"] = len(d3)
    r["n3_regimes"] = ",".join(sorted(d3.regime.unique()))
    b = d3[d3.regime == "offline"]; s = d3[d3.regime == "sonda"]
    r["n3_busca"] = len(b); r["n3_sonda"] = len(s)
    g = b.geracao.dropna().astype(int)
    r["ger_min"] = int(g.min()); r["ger_max"] = int(g.max()); r["ger_nunique"] = int(g.nunique())
    r["ger_denso_1_1000"] = bool(set(g.unique()) == set(range(1, 1001)))
    r["sonda_ger_null"] = float(s.geracao.isna().mean())
    mus = [f"mu_{j}" for j in range(M)]; sgs = [f"sigma_{j}" for j in range(M)]
    r["sigma_nan_busca"] = float(b[sgs].isna().values.mean())
    r["sigma_nan_sonda"] = float(s[sgs].isna().values.mean())
    r["sigma_nan_total"] = float(d3[sgs].isna().values.mean())
    r["mu_nan_total"] = float(d3[mus].isna().values.mean())
    r["rsid_null_pct"] = float(d3.real_solution_id.isna().mean())
    r["modelo_flags_3"] = ",".join(sorted(d3.modelo_flag.unique()))
    r["n_modelo_flags"] = d3.modelo_flag.nunique()
    r["espaco_modelo"] = ",".join(sorted(d3.espaco_modelo.unique()))
    r["transf_tipo_null"] = float(d3.transf_tipo.isna().mean())
    r["transf_params_null"] = float(d3.transf_params.isna().mean())
    r["fe_treino_max_u"] = ",".join(map(str, sorted(d3.fe_treino_max.unique())))
    r["fe_treino_eq_N1"] = bool(set(d3.fe_treino_max.unique()) == {len(d1) - 1})
    r["pred_tipo_u"] = ",".join(sorted(d3.pred_tipo.dropna().unique()))
    r["pred_score_null"] = float(d3.pred_score.isna().mean())
    r["pred_classe_null"] = float(d3.pred_classe.isna().mean())
    r["pred_conf_null"] = float(d3.pred_confianca.isna().mean())
    pg = b.groupby(b.geracao.astype(int)).size()
    r["pop_lattice"] = LATTICE[M]
    r["pop_max"] = int(pg.max()); r["pop_min"] = int(pg.min())
    r["pop_ultima"] = int(pg.loc[1000]) if 1000 in pg.index else None
    r["pop_nunca_excede"] = bool(pg.max() <= LATTICE[M])
    r["pop_encolheu"] = bool(pg.min() < LATTICE[M])
    r["n3_busca_esperado"] = int(pg.sum())

    # bounds do X na busca
    xs = [f"x{i}" for i in range(D)]
    r["x_busca_min"] = float(b[xs].values.min()); r["x_busca_max"] = float(b[xs].values.max())
    r["x_dataset_min"] = float(d1[xs].values.min()); r["x_dataset_max"] = float(d1[xs].values.max())

    # ------- ④ timing -------
    d4 = pd.read_parquet(stem + "__timing.parquet")
    r["n4"] = len(d4)
    r["t4_geracao"] = int(d4.geracao.iloc[0])
    r["t4_nacum"] = int(d4.n_acumulado.iloc[0])
    r["t4_fit"] = float(d4.tempo_fit_s.iloc[0]); r["t4_busca"] = float(d4.tempo_busca_s.iloc[0])
    r["t4_sonda"] = float(d4.tempo_pred_sonda_s.iloc[0]); r["t4_ger"] = float(d4.tempo_geracao_s.iloc[0])
    r["U7_fit_busca_le_ger"] = bool(d4.tempo_fit_s.iloc[0] + d4.tempo_busca_s.iloc[0] <= d4.tempo_geracao_s.iloc[0] + 1e-9)
    r["U7_com_sonda_excede"] = bool(d4.tempo_fit_s.iloc[0] + d4.tempo_busca_s.iloc[0] + d4.tempo_pred_sonda_s.iloc[0] > d4.tempo_geracao_s.iloc[0])
    r["t4_nacum_eq_N"] = (int(d4.n_acumulado.iloc[0]) == len(d1))
    r["teto_43200_folga_x"] = round(43200.0 / t["tempo_total_s"], 1)
    linhas.append(r)
    print("ok", label, flush=True)

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "tm_estrutura.csv"), index=False)
print(df.shape)
