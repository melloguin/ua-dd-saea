#!/usr/bin/env python
"""
BATERIA DE FIDELIDADE — c154 (JES) — F5.3b, protocolo v1.1
READ-ONLY sobre os dados. Escreve APENAS em f5/baterias/c154/.
Interpretador: /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
"""
import json, os, math, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")
EPS32 = np.finfo(np.float32).eps

PROBS = sorted(os.listdir(ROOT))
PROBS = [p for p in PROBS if not p.startswith('.')]

rows = []          # 1 linha/celula com todos os checks
dec_rows = []      # 1 linha/decisao (agregacao fina)
hp_rows = []       # 1 linha/(celula,iter,obj) com hiperparametros do GP
guard_rows = []    # eventos de guarda
sonda_rows = []    # 1 linha/(celula,bloco)

for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    man = json.load(open(base + ".manifest.json"))
    L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    hdr = [r for r in L if r.get("rec") == "header"][0]
    dec = [r for r in L if r.get("rec") == "decision"]
    son = [r for r in L if r.get("rec") == "sonda"]
    tim = [r for r in L if r.get("rec") == "timing"]
    ftr = [r for r in L if r.get("rec") == "footer"]
    grd = [r for r in L if r.get("rec") == "guard"]
    other = [r for r in L if r.get("rec") not in
             ("header", "decision", "sonda", "timing", "footer", "guard")]

    D = hdr["D"]; M = hdr["M"]
    real = pq.read_table(base + "__real.parquet").to_pandas()
    pop = pq.read_table(base + "__pop.parquet").to_pandas()
    sur = pq.read_table(base + "__surrogate.parquet").to_pandas()
    tpq = pq.read_table(base + "__timing.parquet").to_pandas()

    r = dict(problema=prob, D=D, M=M)
    r["status"] = man["status"]; r["n_retries"] = man["n_retries"]
    r["fallback_ativado"] = man.get("fallback_ativado")
    r["algo_version"] = man["algo_version"]
    r["botorch"] = man["env"]["botorch"]; r["torch"] = man["env"]["torch"]
    r["gpytorch"] = man["env"]["gpytorch"]; r["pymoo"] = man["env"]["pymoo"]
    r["dtype"] = man["env"]["pinning"]["default_dtype"]
    r["threads"] = man["env"]["pinning"]["torch_num_threads"]
    r["fused_kernel"] = man.get("fused_kernel")
    r["manifest_tem_params"] = "params" in man
    r["header_tem_params"] = "params" in hdr
    r["n_recs_outros"] = len(other)
    r["recs_outros_nomes"] = ";".join(sorted({o["rec"] for o in other}))
    r["n_guard"] = len(grd)
    r["guard_nomes"] = ";".join(sorted({g.get("name", "?") for g in grd}))
    r["n_footer"] = len(ftr)

    # --- params/jes declarados
    jes = man.get("jes", {})
    P = hdr["params"]
    r["S"] = jes.get("S"); r["P"] = jes.get("P")
    r["estimation_type"] = jes.get("estimation_type")
    r["rota_b95"] = jes.get("rota_b95")
    r["num_restarts_man"] = jes.get("num_restarts")
    r["raw_samples_man"] = jes.get("raw_samples")
    r["rs_fallbacks_total"] = jes.get("rs_fallbacks_total")
    r["nsgaii_pop_declarado"] = P.get("nsgaii_pop")
    r["nsgaii_gen_declarado"] = P.get("nsgaii_gen")
    r["rs_ladder"] = json.dumps(P.get("rs_ladder"))
    r["kernel"] = P.get("kernel"); r["refit"] = P.get("refit")
    r["init_batch_limit"] = P.get("init_batch_limit")
    r["acqf"] = P.get("acqf"); r["q_param"] = P.get("q")
    r["ruido_decl"] = hdr.get("ruido"); r["acqf_ref_decl"] = hdr.get("acqf_ref")

    # ---------- U1: FE ----------
    maxfe = 31 * D - 1
    r["maxfe_formula"] = maxfe
    r["U1_maxfe_man"] = man["maxfe"] == maxfe
    r["U1_fe_final"] = man["fe_final"] == maxfe
    r["U1_len_real"] = len(real) == maxfe
    r["U1_fe_index_denso"] = bool((real["fe_index"].values ==
                                   np.arange(len(real))).all())
    r["U1_solid_denso"] = bool((real["solution_id"].values ==
                                np.arange(len(real))).all())
    r["U1_footer_fe"] = ftr[0]["fe_final"] == maxfe

    # ---------- U2: init ----------
    n_init = 11 * D - 1
    r["n_init_formula"] = n_init
    r["U2_init_count"] = int((real["fase"] == "init").sum()) == n_init
    r["U2_fases"] = ";".join(sorted(real["fase"].unique()))
    r["U2_cp_init"] = ftr[0].get("cp_init")
    r["U2_doe_hash_igual"] = man["doe_hash"] == hdr["doe_hash"]
    # DoE bit-a-bit vs artefato
    doep = f"{REPO}/data/doe/{prob}/doe_{prob}_42.parquet"
    if os.path.exists(doep):
        doe = pq.read_table(doep).to_pandas()
        xc = [c for c in real.columns if c.startswith("x")]
        dc = [c for c in doe.columns if c.startswith("x")]
        A = real.loc[real["fase"] == "init", xc].values.astype(np.float64)
        B = doe[dc].values.astype(np.float64)[:len(A)]
        r["U2_doe_dX_max"] = float(np.abs(A - B).max())
    else:
        r["U2_doe_dX_max"] = np.nan

    # ---------- U3 / U10: fits e off-by-one ----------
    n_ger = man["n_geracoes"]
    n_infill = sum(1 for d in dec if d.get("caminho") == "infill")
    n_hardstop = sum(1 for d in dec if d.get("caminho") == "hard_stop")
    r["n_geracoes"] = n_ger
    r["n_decisions"] = len(dec)
    r["n_infill"] = n_infill
    r["n_hardstop_dec"] = n_hardstop
    r["U10_infill_eq_maxfe_minus_init"] = (n_infill == maxfe - n_init)
    r["U10_ger_eq_infill_mais1"] = (n_ger == n_infill + 1)
    r["U3_n_fits_timing_jsonl"] = len(tim)
    r["U3_n_fits_manifest"] = len(man["fit_series"])
    r["U3_fits_eq_ger"] = (len(tim) == n_ger == len(man["fit_series"]) ==
                           len(tpq))
    r["U3_n_train_eq_n_acum"] = bool(all(
        d["n_train"] == t["n_acumulado"] for d, t in zip(dec, tim)))
    # n_train cresce +1 por iteracao (dataset inteiro)
    nt = np.array([d["n_train"] for d in dec])
    r["U3_n_train_passo1"] = bool((np.diff(nt) == 1).all())
    r["U3_n_train_ini"] = int(nt[0]); r["U3_n_train_fim"] = int(nt[-1])
    r["U3_n_train_eq_11D_1"] = int(nt[0]) == n_init

    # ---------- U8: fe_treino_max ----------
    ftm = sur.loc[sur["regime"] == "online"].groupby("geracao")["fe_treino_max"].max()
    r["U8_ftm_monotonico"] = bool((np.diff(ftm.values) >= 0).all())
    r["U8_ftm_min"] = int(ftm.min()); r["U8_ftm_max"] = int(ftm.max())
    r["U8_ftm_eq_ntrain_menos1"] = bool(
        (ftm.values == nt[:len(ftm)] - 1).all())

    # ---------- ③ estrutura: restarts ----------
    on = sur[sur["regime"] == "online"]
    cnt = on.groupby("geracao").size()
    r["n_restarts_5D"] = 5 * D
    r["raw_1000D"] = 1000 * D
    r["U_restarts_man_eq_5D"] = (jes.get("num_restarts") == 5 * D)
    r["U_raw_man_eq_1000D"] = (jes.get("raw_samples") == 1000 * D)
    r["S3_online_linhas_por_ger"] = ";".join(map(str, sorted(cnt.unique())))
    r["S3_online_ok"] = bool((cnt.values == 5 * D).all())
    r["S3_online_gers"] = int(cnt.shape[0])
    r["S3_n_restarts_dec_ok"] = bool(all(d["n_restarts"] == 5 * D for d in dec))
    r["S3_raw_dec_ok"] = bool(all(d["raw_samples"] == 1000 * D for d in dec))
    # exatamente 1 real_solution_id por geracao com infill
    rsid = on.dropna(subset=["real_solution_id"]).groupby("geracao").size()
    r["S3_rsid_1_por_ger"] = bool((rsid.values == 1).all())
    r["S3_rsid_n_gers"] = int(rsid.shape[0])
    r["S3_rsid_total"] = int(on["real_solution_id"].notna().sum())
    r["S3_rsid_eq_ninfill"] = (int(rsid.shape[0]) == n_infill)
    r["S3_espaco_modelo"] = ";".join(sorted(on["espaco_modelo"].dropna().unique())) or "NULL"
    r["S3_modelo_flag"] = ";".join(sorted(on["modelo_flag"].dropna().unique()))
    r["S3_pred_tipo"] = ";".join(sorted(on["pred_tipo"].dropna().unique()))
    r["S3_sigma_notna_pct"] = float(on[[f"sigma_{j}" for j in range(M)]].notna().all(1).mean())
    r["S3_transf_tipo_online"] = ";".join(sorted(on["transf_tipo"].dropna().unique())) or "NULL"

    # ---------- QUERY-JOIA A: argmax dos restarts ----------
    ok_argmax = 0; ok_pos = 0; tot = 0; nan_iters = 0; nan_count = 0
    nan_per_iter = []
    dmax_choice = 0.0
    for d in dec:
        if "acqf_todos_restarts" not in d:
            continue
        a = np.array(d["acqf_todos_restarts"], dtype=float)
        tot += 1
        nfin = int((~np.isfinite(a)).sum())
        nan_count += nfin
        if nfin:
            nan_iters += 1
            nan_per_iter.append((d["it"], nfin))
        fin = a[np.isfinite(a)]
        if len(fin) and math.isclose(d["acqf_escolhido"], float(fin.max()),
                                     rel_tol=0, abs_tol=1e-12):
            ok_argmax += 1
        # posicao do argmax x linha escolhida na ③
        g = d.get("it")
        blk = on[on["geracao"] == g]
        if len(blk) == len(a) and blk["real_solution_id"].notna().any():
            pos_sur = int(np.flatnonzero(blk["real_solution_id"].notna().values)[0])
            pos_acq = int(np.nanargmax(np.where(np.isfinite(a), a, -np.inf)))
            if pos_sur == pos_acq:
                ok_pos += 1
    r["QJ_argmax_ok"] = ok_argmax; r["QJ_argmax_tot"] = tot
    r["QJ_posicao_ok"] = ok_pos
    r["QJ_nan_iters"] = nan_iters; r["QJ_nan_valores"] = nan_count
    r["QJ_nan_detalhe"] = json.dumps(nan_per_iter[:40])

    # ---------- QUERY-JOIA B: link ③(escolhido) → ① bit-a-bit ----------
    xcols = [c for c in real.columns if c.startswith("x")]
    fcols = [c for c in real.columns if c.startswith("f")]
    ch = on.dropna(subset=["real_solution_id"]).copy()
    ch["real_solution_id"] = ch["real_solution_id"].astype(int)
    j = ch.merge(real[["solution_id"] + xcols + fcols],
                 left_on="real_solution_id", right_on="solution_id",
                 suffixes=("", "_real"))
    dX = np.abs(j[xcols].values.astype(np.float64) -
                j[[c + "_real" for c in xcols]].values.astype(np.float64)).max() if len(j) else np.nan
    r["QJ_link_dX_max"] = float(dX)
    r["QJ_link_n"] = int(len(j))
    # U11 erro de fantasia
    for m in range(M):
        e = np.abs(j[f"mu_{m}"].values.astype(float) - j[f"f{m}"].values.astype(float))
        r[f"U11_fantasia_med_obj{m}"] = float(np.nanmedian(e))
        r[f"U11_fantasia_max_obj{m}"] = float(np.nanmax(e))
        fr = np.abs(j[f"f{m}"].values.astype(float))
        r[f"U11_fantasia_wape_obj{m}"] = float(np.nansum(e) / max(np.nansum(fr), 1e-12))

    # ---------- U4 / sonda cadencia ----------
    gs = sorted(s["geracao"] for s in son)
    esperado = sorted({g for g in range(1, n_ger + 1) if g == 1 or g % 2 == 0} | {n_ger})
    r["U4_blocos"] = len(son)
    r["U4_blocos_formula"] = len(esperado)
    r["U4_cadencia_ok"] = (gs == esperado)
    r["U4_ultima_coberta"] = (n_ger in gs)
    r["U4_n_pontos_ok"] = all(s["n_pontos"] == 2000 for s in son)
    r["U4_hash_ok"] = all(str(s.get("hash_check", "")).startswith("ok") for s in son)
    r["U4_manifest_nblocos"] = man["sonda"]["n_blocos"]
    r["U4_manifest_nlinhas"] = man["sonda"]["n_linhas"]
    sd = sur[sur["regime"] == "sonda"]
    r["U4_sonda_linhas_③"] = int(len(sd))
    r["U4_sonda_linhas_ok"] = (len(sd) == 2000 * len(son))

    # ---------- U5: join posicional sonda × gabarito ----------
    sp = f"{REPO}/data/sonda/sonda_{prob}.parquet"
    gab = pq.read_table(sp).to_pandas().iloc[:2000].reset_index(drop=True)
    gx = [c for c in gab.columns if c.startswith("x")]
    gf = [c for c in gab.columns if c.startswith("f")]
    blocos = sorted(sd["geracao"].dropna().unique())
    dmax = 0.0
    for g in blocos:
        b = sd[sd["geracao"] == g]
        if len(b) != len(gab):
            dmax = np.inf; break
        dmax = max(dmax, float(np.abs(b[gx].values.astype(np.float64) -
                                      gab[gx].values.astype(np.float64)).max()))
    r["U5_dX_max"] = dmax
    r["U5_ok"] = bool(dmax <= EPS32 * max(1.0, float(np.abs(gab[gx].values).max())))

    # ---------- U6: WAPE / cobertura por bloco (definicao congelada) ----------
    for g in blocos:
        b = sd[sd["geracao"] == g]
        row = dict(problema=prob, D=D, bloco=int(g), n=len(b),
                   fe_treino_max=int(b["fe_treino_max"].max()))
        for m in range(M):
            mu = b[f"mu_{m}"].values.astype(np.float64)
            sg = b[f"sigma_{m}"].values.astype(np.float64)
            fv = gab[gf[m]].values.astype(np.float64)
            e = np.abs(mu - fv)
            row[f"wape{m}"] = float(np.nansum(e) / max(np.nansum(np.abs(fv)), 1e-12))
            row[f"cov{m}"] = float(np.nanmean(e <= 1.96 * sg))
            row[f"sigma_med{m}"] = float(np.nanmedian(sg))
            row[f"nan_sigma{m}"] = int(np.isnan(sg).sum())
        sonda_rows.append(row)

    # ---------- U7: invariante de timing ----------
    tt = tpq.copy()
    v1 = (tt["tempo_fit_s"] + tt["tempo_busca_s"]) <= tt["tempo_geracao_s"] + 1e-9
    r["U7_inv1_viol"] = int((~v1).sum()); r["U7_inv1_tot"] = int(len(tt))
    com_sonda = set(gs)
    excede = tt[(tt["tempo_fit_s"] + tt["tempo_busca_s"] + tt["tempo_pred_sonda_s"])
                > tt["tempo_geracao_s"] + 1e-9]["geracao"].tolist()
    r["U7_gers_excedem"] = len(excede)
    r["U7_excedem_subset_sonda"] = set(excede).issubset(com_sonda)
    r["U7_sonda_sem_excesso"] = len(com_sonda - set(excede))
    # tempo de paths dentro de busca
    tp = np.array([d.get("t_paths_s", np.nan) for d in dec], dtype=float)
    tb = np.array([d.get("tempo_busca_s", np.nan) for d in dec], dtype=float)
    r["T_paths_frac_med"] = float(np.nanmedian(tp / tb))
    r["T_paths_s_total"] = float(np.nansum(tp))
    r["T_busca_s_total"] = float(np.nansum(tb))
    r["T_paths_le_busca"] = bool(np.all(tp <= tb + 1e-6))
    r["wall_s"] = man["timing"]["tempo_total_s"]
    r["tempo_paths_man"] = man["timing"].get("tempo_paths_s")

    # ---------- U9: reconciliacao contadores ----------
    r["U9_cache_hits_man"] = man["cache_hits"]
    r["U9_cache_hits_footer"] = ftr[0]["cache_hits"]
    r["U9_cache_hit_dec"] = sum(1 for d in dec if d.get("cache_hit"))
    r["U9_fit_retries_dec"] = sum(d.get("fit_retries", 0) for d in dec)
    r["U9_acqf_warnings_dec"] = sum(d.get("acqf_warnings", 0) for d in dec)
    r["U9_rs_fb_footer"] = ftr[0]["rs_fallbacks_total"]
    r["U9_nblocos_footer"] = ftr[0]["n_blocos_sonda"]
    r["U9_hard_stopped"] = ftr[0].get("hard_stopped")
    r["U9_footer_status"] = ftr[0]["status"]
    r["U9_footer2_status"] = ftr[-1]["status"]
    r["U9_nblocos_footer_ok"] = (ftr[0]["n_blocos_sonda"] == len(son))
    r["motivo_parada_man"] = man.get("motivo_parada", "AUSENTE")
    r["motivo_hard_stop_dec"] = dec[-1].get("motivo") if dec else None
    r["caminho_ultima_dec"] = dec[-1].get("caminho") if dec else None

    # ---------- ② pop ----------
    r["pop_linhas"] = int(len(pop))
    pg = pop.groupby("geracao").size()
    r["pop_gers"] = int(pg.shape[0])
    r["pop_g0"] = int(pg.iloc[0]) if len(pg) else 0
    r["pop_passo1"] = bool((np.diff(pg.values) == 1).all()) if len(pg) > 1 else None
    r["pop_ultima"] = int(pg.iloc[-1]) if len(pg) else 0
    r["pop_soma_formula"] = int(sum(range(n_init, maxfe + 1)))
    r["pop_eq_dataset_acumulado"] = (int(len(pop)) == r["pop_soma_formula"])

    # ---------- JES: shapes, seeds, S/P ----------
    pfs = {tuple(d["pf_shape"]) for d in dec if "pf_shape" in d}
    pss = {tuple(d["ps_shape"]) for d in dec if "ps_shape" in d}
    r["JES_pf_shapes"] = ";".join(str(s) for s in sorted(pfs))
    r["JES_ps_shapes"] = ";".join(str(s) for s in sorted(pss))
    r["JES_pf_ok"] = (pfs == {(10, 10, M)})
    r["JES_ps_ok"] = (pss == {(10, 10, D)})
    hs = [d["hs_paths"] for d in dec if "hs_paths" in d]
    r["JES_hs_len_ok"] = all(len(h) == 10 for h in hs)
    flat = [x for h in hs for x in h]
    r["JES_hs_unicos"] = len(set(flat)); r["JES_hs_total"] = len(flat)
    ts = [d["torch_seed"] for d in dec if "torch_seed" in d]
    r["JES_torch_seed_unicos"] = len(set(ts)); r["JES_torch_seed_n"] = len(ts)
    r["JES_rota_a"] = all(d.get("rota") == "a" for d in dec)
    r["JES_motivos"] = ";".join(sorted({d.get("motivo", "") for d in dec}))
    # valores dos fronts amostrados
    npf = 0; pf_fin = 0
    for d in dec:
        if "pf_amostrados_f" in d:
            arr = np.array(d["pf_amostrados_f"], dtype=float)
            npf += arr.size; pf_fin += int(np.isfinite(arr).sum())
    r["JES_pf_valores"] = npf; r["JES_pf_finitos"] = pf_fin

    # ---------- modelo_hp: ruido inferido, lengthscales ----------
    noises = {m: [] for m in range(M)}
    lsmed = {m: [] for m in range(M)}
    lsmin = {m: [] for m in range(M)}
    lsmax = {m: [] for m in range(M)}
    outs = {m: [] for m in range(M)}
    mlls = []
    for d in dec:
        hp = d.get("modelo_hp", {})
        mlls.append(hp.get("mll_final", np.nan))
        for m, o in enumerate(hp.get("por_objetivo", [])):
            noises[m].append(o.get("noise", np.nan))
            lsmed[m].append(o.get("lengthscale_med", np.nan))
            lsmin[m].append(o.get("lengthscale_min", np.nan))
            lsmax[m].append(o.get("lengthscale_max", np.nan))
            outs[m].append(o.get("outputscale", np.nan))
            hp_rows.append(dict(problema=prob, it=d["it"], obj=m,
                                noise=o.get("noise"),
                                ls_min=o.get("lengthscale_min"),
                                ls_med=o.get("lengthscale_med"),
                                ls_max=o.get("lengthscale_max"),
                                outputscale=o.get("outputscale"),
                                mll=hp.get("mll_final"),
                                n_train=d.get("n_train")))
    for m in range(M):
        nz = np.array(noises[m], dtype=float)
        r[f"HP_noise_min_obj{m}"] = float(np.nanmin(nz))
        r[f"HP_noise_max_obj{m}"] = float(np.nanmax(nz))
        r[f"HP_noise_ini_obj{m}"] = float(nz[0])
        r[f"HP_noise_fim_obj{m}"] = float(nz[-1])
        r[f"HP_noise_razao_obj{m}"] = float(np.nanmax(nz) / max(np.nanmin(nz), 1e-30))
        r[f"HP_noise_piso1e4_obj{m}"] = int((nz < 1e-4 - 1e-12).sum())
        r[f"HP_noise_ge1e4_obj{m}"] = int((nz >= 1e-4 - 1e-12).sum())
        lm = np.array(lsmed[m], dtype=float)
        r[f"HP_ls_muda_obj{m}"] = int((np.diff(lm) != 0).sum())
        r[f"HP_ls_pares_obj{m}"] = int(len(lm) - 1)
        r[f"HP_ard_vivo_obj{m}"] = int(
            (np.array(lsmin[m]) != np.array(lsmax[m])).sum())
        r[f"HP_ard_tot_obj{m}"] = len(lsmin[m])
        r[f"HP_outscale_ini_obj{m}"] = float(outs[m][0])
        r[f"HP_outscale_fim_obj{m}"] = float(outs[m][-1])
    r["HP_mll_ini"] = float(mlls[0]); r["HP_mll_fim"] = float(mlls[-1])
    r["HP_mll_n"] = len(mlls)

    # ---------- acqf: paisagem ----------
    ae = np.array([d["acqf_escolhido"] for d in dec if "acqf_escolhido" in d], float)
    r["ACQ_escolhido_ini"] = float(ae[0]); r["ACQ_escolhido_fim"] = float(ae[-1])
    r["ACQ_escolhido_med"] = float(np.nanmedian(ae))
    r["ACQ_positivo_pct"] = float((ae > 0).mean())
    spread = []
    for d in dec:
        a = np.array(d.get("acqf_todos_restarts", []), float)
        a = a[np.isfinite(a)]
        if len(a) > 1:
            spread.append(float(a.max() - a.min()))
    r["ACQ_spread_med"] = float(np.median(spread)) if spread else np.nan
    # diversidade / distancia ao arquivo
    dm = np.array([d.get("dist_min_arquivo", np.nan) for d in dec], float)
    r["DIST_min_arquivo_med"] = float(np.nanmedian(dm))
    r["DIST_min_arquivo_min"] = float(np.nanmin(dm))
    r["DIST_zero"] = int((dm == 0).sum())
    nf1 = np.array([d.get("n_front1", np.nan) for d in dec], float)
    r["NFRONT1_ini"] = float(nf1[0]); r["NFRONT1_fim"] = float(nf1[-1])
    r["NFRONT1_max"] = float(np.nanmax(nf1))

    for d in dec:
        dec_rows.append(dict(
            problema=prob, D=D, M=M, it=d["it"], caminho=d.get("caminho"),
            fe=d.get("fe"), n_train=d.get("n_train"),
            acqf_escolhido=d.get("acqf_escolhido"),
            n_nan_restarts=int((~np.isfinite(
                np.array(d.get("acqf_todos_restarts", []), float))).sum()),
            n_restarts=d.get("n_restarts"), raw_samples=d.get("raw_samples"),
            t_paths_s=d.get("t_paths_s"), tempo_busca_s=d.get("tempo_busca_s"),
            tempo_fit_s=d.get("tempo_fit_s"),
            dist_min_arquivo=d.get("dist_min_arquivo"),
            n_front1=d.get("n_front1"), rota=d.get("rota"),
            solution_id=d.get("solution_id")))
    for g in grd:
        guard_rows.append(dict(problema=prob, **{k: v for k, v in g.items()
                                                 if k != "ts"}))
    rows.append(r)
    print(f"[ok] {prob:10s} D={D:2d} M={M} decisoes={len(dec)} blocos={len(son)}")

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "c154_celulas.csv"), index=False)
pd.DataFrame(dec_rows).to_csv(os.path.join(OUT, "c154_decisoes.csv"), index=False)
pd.DataFrame(hp_rows).to_csv(os.path.join(OUT, "c154_modelo_hp.csv"), index=False)
pd.DataFrame(guard_rows).to_csv(os.path.join(OUT, "c154_guards.csv"), index=False)
pd.DataFrame(sonda_rows).to_csv(os.path.join(OUT, "c154_sonda_recomputada.csv"), index=False)
print("\nescritos em", OUT)
