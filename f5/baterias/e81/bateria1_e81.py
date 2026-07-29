#!/usr/bin/env python
"""bateria1_e81 — universais U1-U12 + módulo de família GP-BO (query-joia maximin)
+ aspectos específicos do bundle, executados nas 30 células da semente 42.

READ-ONLY sobre resultados_experimentos/e81/ e ua-dd-saea/data/.
Saídas: e81_celulas.csv (30 linhas × N checks) · e81_decisoes.csv (8.020) ·
        e81_joia.csv (por geração) · e81_fallback.csv · e81_modelo_hp.csv
"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")


def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out


def load_jsonl(path):
    recs = {"header": [], "fit": [], "sonda": [], "decision": [], "footer": [], "outros": []}
    bad = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                bad += 1
                continue
            r = o.get("rec")
            recs.setdefault(r if r in recs else "outros", []).append(o)
    return recs, bad


def doe_bounds(prob):
    m = json.load(open(f"{REPO}/data/doe/{prob}/doe_{prob}_42.manifest.json"))
    return np.array(m["bounds"]["xl"], float), np.array(m["bounds"]["xu"], float), m


rows_cell, rows_dec, rows_joia, rows_fb, rows_hp = [], [], [], [], []

for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    recs, bad = load_jsonl(base + ".jsonl")
    hdr = recs["header"][0]
    foots = recs["footer"]
    fo = foots[0]
    dec = recs["decision"]
    fits = recs["fit"]
    sondas = recs["sonda"]
    real = pd.read_parquet(base + "__real.parquet")
    pop = pd.read_parquet(base + "__pop.parquet")
    sur = pd.read_parquet(base + "__surrogate.parquet")
    tim = pd.read_parquet(base + "__timing.parquet")

    D, M = int(hdr["D"]), int(hdr["M"])
    q = int(man["q"])
    maxfe, n_init = int(man["maxfe"]), int(hdr["n_init"])
    xcols = [f"x{i}" for i in range(D)]
    fcols = [f"f{j}" for j in range(M)]
    xl, xu, doeman = doe_bounds(prob)
    rng = xu - xl

    r = dict(exp=exp, problema=prob, label=lab, D=D, M=M, q=q, maxfe=maxfe,
             n_init=n_init, n_ger=len(dec), status=man["status"],
             motivo_parada=man.get("motivo_parada"), n_retries=man.get("n_retries"),
             fallback_ativado=man.get("fallback_ativado"), jsonl_bad=bad,
             n_footers=len(foots), recs_outros=len(recs["outros"]),
             algo_version=man.get("algo_version"))

    # ── U1: orçamento ─────────────────────────────────────────────────────
    r["U1_len_real"] = len(real)
    r["U1_fe_exato"] = (len(real) == maxfe == int(man["fe_final"]) == int(fo["fe_final"])
                        == 31 * D - 1 if exp == "main" else
                        len(real) == maxfe == int(man["fe_final"]) == int(fo["fe_final"])
                        == 11 * D - 1 + 2000)
    r["U1_formula"] = "31D-1" if exp == "main" else "11D-1+2000"
    r["U1_fe_index_denso"] = bool((real["fe_index"].values == np.arange(len(real))).all())
    r["U1_solid_denso"] = bool((real["solution_id"].values == np.arange(len(real))).all())

    # ── U2: DoE ───────────────────────────────────────────────────────────
    init = real[real["fase"] == "init"]
    r["U2_n_init_ok"] = bool(len(init) == 11 * D - 1 == n_init)
    r["U2_doe_hash_ok"] = bool(man["doe_hash"] == hdr["doe_hash"])
    # o artefato do DoE e gravado em espaco NATIVO (manifesto traz bounds)
    doenat = pd.read_parquet(f"{REPO}/data/doe/{prob}/doe_{prob}_42.parquet")[xcols].values
    dXdoe = np.abs(init[xcols].values.astype(np.float64) - doenat)
    r["U2_dX_doe_max"] = float(dXdoe.max())
    r["U2_dX_doe_max_rel"] = float((dXdoe / rng).max())
    r["U2_doe_shape_ok"] = bool(doenat.shape == (11 * D - 1, D))
    r["U2_cp_init"] = bool(fo.get("cp_init"))
    r["U2_bounds_ok"] = bool((real[xcols].values >= xl - 1e-4).all() and
                             (real[xcols].values <= xu + 1e-4).all())

    # ── U3/U8/U10: fits, treino, aritmética ───────────────────────────────
    r["U3_fits"] = len(fits)
    r["U3_fits_eq_ger"] = bool(len(fits) == len(dec) == len(tim) == int(man["n_geracoes"])
                               == int(fo["n_geracoes"]))
    r["U3_fit_series_len"] = len(man.get("fit_series", []) or [])
    ntr = np.array([f["n_treino"] for f in fits])
    r["U3_ntreino_passo_q"] = bool((np.diff(ntr) == q).all())
    r["U3_ntreino_ini"] = int(ntr[0]); r["U3_ntreino_fim"] = int(ntr[-1])
    ftm = np.array([f["fe_treino_max"] for f in fits])
    r["U8_ftm_monotonico"] = bool((np.diff(ftm) >= 0).all())
    r["U8_ftm_min"] = int(ftm.min()); r["U8_ftm_max"] = int(ftm.max())
    r["U8_ftm_eq_ntr_1"] = bool((ftm == ntr - 1).all())
    r["U8_ftm_faixa_ok"] = bool(ftm.min() == 11 * D - 2 and ftm.max() == maxfe - q - 1)
    fe_arr = np.array([o["fe"] for o in dec])
    ntrain_arr = np.array([o["n_train"] for o in dec])
    r["U10_fe_eq_ntrain_q"] = bool((fe_arr == ntrain_arr + q).all())
    r["U10_fe_cresce"] = bool((np.diff(fe_arr) == q).all())
    r["U10_ger_x_q"] = bool(len(dec) * q == maxfe - n_init)
    # ③ fe_treino_max vs ⑥
    ftm3 = sur.groupby("geracao")["fe_treino_max"].nunique()
    r["U8_ftm3_unico_por_ger"] = bool((ftm3 == 1).all())
    ftm3v = sur.groupby("geracao")["fe_treino_max"].first()
    r["U8_ftm3_bate_jsonl"] = bool((ftm3v.reindex([f["geracao"] for f in fits]).values == ftm).all())

    # ── U4/U5: sonda ──────────────────────────────────────────────────────
    gens = sorted({o["geracao"] for o in dec})
    esperado = sorted({g for g in gens if g == 1 or g % 2 == 0} | {max(gens)})
    gsonda = sorted({o["geracao"] for o in sondas})
    r["U4_cadencia_ok"] = bool(gsonda == esperado)
    r["U4_n_blocos"] = len(gsonda)
    r["U4_n_blocos_man"] = int(man["sonda"]["n_blocos"])
    r["U4_ultima_coberta"] = bool(max(gens) in gsonda)
    r["U4_n_pontos_ok"] = bool(all(o["n_pontos"] == 2000 for o in sondas))
    r["U4_hash_ok"] = bool(all(str(o["hash_check"]).startswith("ok") for o in sondas))
    sd = sur[sur["regime"] == "sonda"]
    r["U4_linhas_sonda"] = len(sd)
    r["U4_linhas_ok"] = bool(len(sd) == 2000 * len(gsonda))
    gab = pd.read_parquet(f"{REPO}/data/sonda/sonda_{prob}.parquet")
    gabx = gab[xcols].values[:2000].astype(np.float64)
    dmax = 0.0
    for g in gsonda:
        blk = sd[sd["geracao"] == g][xcols].values.astype(np.float64)
        dmax = max(dmax, float(np.abs(blk - gabx).max()))
    r["U5_dX_sonda_max"] = dmax
    r["U5_dX_sonda_max_rel"] = float(dmax / rng.max())
    r["U5_sonda_gab_linhas"] = int(len(gab))

    # ── U7: invariante de timing ──────────────────────────────────────────
    t = tim.set_index("geracao")
    inv1 = (t["tempo_fit_s"] + t["tempo_busca_s"] <= t["tempo_geracao_s"] + 1e-9)
    r["U7_inv1_violacoes"] = int((~inv1).sum())
    sset = set(gsonda)
    exc = (t["tempo_fit_s"] + t["tempo_busca_s"] + t["tempo_pred_sonda_s"] > t["tempo_geracao_s"])
    r["U7_inv2_sonda_excede"] = int(exc[[g in sset for g in t.index]].sum())
    r["U7_inv2_sonda_total"] = len(gsonda)
    r["U7_inv2_semsonda_excede"] = int(exc[[g not in sset for g in t.index]].sum())

    # ── U9: guardas/contadores ────────────────────────────────────────────
    r["U9_cache_hits_foot"] = int(fo.get("cache_hits", -1))
    r["U9_cache_hits_man"] = int(man.get("cache_hits", -1))
    r["U9_cache_hit_dec"] = int(sum(1 for o in dec if o.get("cache_hit")))
    r["U9_n_cache_infill"] = int(fo.get("n_cache_infill", -1))
    r["U9_fit_retries"] = int(sum(o.get("fit_retries", 0) for o in dec))
    r["U9_n_lote_menor"] = int(fo.get("n_lote_menor", -1))
    r["U9_n_lote_completado"] = int(fo.get("n_lote_completado", -1))
    r["U9_assert_lote_all"] = bool(all(o.get("assert_lote_eq_q") for o in dec))
    r["U9_n_lote_eq_q"] = int(sum(1 for o in dec if o.get("n_lote") == q))
    r["U9_n_front1_foot"] = int(fo.get("n_front1", -1))
    r["U9_motivo_parada_foot"] = fo.get("motivo_parada")
    r["U9_status_foot"] = fo.get("status")

    # ── ②: dataset acumulado ──────────────────────────────────────────────
    pg = pop.groupby("geracao").size()
    r["POP_linhas_eq_ntrain"] = bool((pg.values == ntrain_arr).all())
    r["POP_linhas_eq_fe"] = bool((pg.values == fe_arr).all())
    r["POP_final_eq_maxfe"] = bool(pg.values[-1] == maxfe)
    r["POP_total"] = int(len(pop))
    r["POP_ger_min"] = int(pg.index.min()); r["POP_ger_max"] = int(pg.index.max())
    r["POP_max_linhas"] = int(pg.max())
    r["POP_cresce_q"] = bool((np.diff(pg.values) == q).all())

    # ── config-echo do bundle ─────────────────────────────────────────────
    pr = man["params"]
    r["CFG_nystrom"] = pr["qpots_kwargs"]["nystrom"]
    r["CFG_ngen_kw"] = pr["qpots_kwargs"]["ngen"]
    r["CFG_q_kw"] = pr["qpots_kwargs"]["q"]
    r["CFG_pop"] = pr["nsga2_interno"]["pop"]
    r["CFG_pop_eq_100D"] = bool(pr["nsga2_interno"]["pop"] == 100 * D)
    r["CFG_ngen_nsga"] = pr["nsga2_interno"]["n_gen"]
    r["CFG_kernel"] = pr["kernel"][:80]
    r["CFG_torch"] = man["env"]["torch"]
    r["CFG_botorch"] = man["env"]["botorch"]
    r["CFG_gpytorch"] = man["env"]["gpytorch"]
    r["CFG_pymoo"] = man["env"]["pymoo"]
    r["CFG_numpy"] = man["env"]["numpy"]
    r["CFG_python"] = man["env"]["python"]
    r["CFG_env_path"] = man["env"]["executable"].split("/")[-3]
    r["CFG_dtype"] = man["env"]["pinning"]["default_dtype"]
    r["CFG_threads"] = man["env"]["pinning"]["torch_num_threads"]
    r["CFG_omp"] = man["env"]["pinning"]["OMP_NUM_THREADS"]
    r["CFG_dtype_check_hdr"] = hdr.get("dtype_check")

    # ── por-decisão ───────────────────────────────────────────────────────
    nystrom_ok = all(o["nystrom"] == 0 for o in dec)
    ngen_ok = all(o["ngen"] == 10 for o in dec)
    q_ok = all(o["q"] == q for o in dec)
    seedgp = np.array([o["seed_gp"] for o in dec])
    seedns = np.array([o["seed_nsga2"] for o in dec])
    iters = np.array([o["iteracao"] for o in dec])
    r["DEC_nystrom0"] = bool(nystrom_ok)
    r["DEC_ngen10"] = bool(ngen_ok)
    r["DEC_q_ok"] = bool(q_ok)
    r["DEC_seedgp_formula"] = bool((seedgp == 1024 + iters + 1000 * 42).all())
    r["DEC_seedns_const"] = bool((seedns == 2430 + 1000 * 42).all())
    r["DEC_dtype64"] = bool(all(o["dtype_check"] == "torch.float64" for o in dec))
    r["DEC_caminho"] = dec[0]["caminho"]
    r["DEC_trainYvar"] = float(dec[0]["modelo_hp"]["train_Yvar"])
    r["DEC_trainYvar_1e12_all"] = bool(all(o["modelo_hp"]["train_Yvar"] == 1e-12 for o in dec))
    r["DEC_kernel_hp"] = dec[0]["modelo_hp"]["kernel"]
    r["DEC_kernel_all"] = bool(all(o["modelo_hp"]["kernel"] == "Matern5/2 ARD" for o in dec))
    r["FIT_kernel_all"] = bool(all(f["kernel"] == "get_matern_kernel_with_gamma_prior(D)" for f in fits))
    r["FIT_nmodelos_M"] = bool(all(f["n_modelos"] == M for f in fits))
    r["FIT_dtype64"] = bool(all(f["dtype"] == "torch.float64" for f in fits))
    r["SON_modelo_flag"] = sondas[0]["modelo_flag"]
    r["SUR_modelo_flag_unico"] = sur["modelo_flag"].nunique()
    r["SUR_espaco_modelo"] = sur["espaco_modelo"].iloc[0]
    r["SUR_transf_tipo"] = sur["transf_tipo"].iloc[0]
    r["SUR_pred_tipo_valor"] = bool((sur["pred_tipo"] == "valor").all())
    r["SUR_pred_classe_null"] = bool(sur["pred_classe"].isna().all())

    # draws de Thompson
    nch = np.array([o["draws_thompson"]["n_chamadas"] for o in dec])
    npt = np.array([o["draws_thompson"]["n_pontos"] for o in dec])
    r["TS_nchamadas_10"] = bool((nch == 10).all())
    r["TS_npontos_eq_popM10"] = bool((npt == 100 * D * 10 * (M if False else 1)).all())
    r["TS_npontos"] = int(npt[0])
    r["TS_npontos_popx10"] = int(100 * D * 10)
    # ARD vivo + curva de aprendizado
    lsmin = np.array([[o["modelo_hp"]["por_objetivo"][j]["lengthscale_min"] for j in range(M)] for o in dec])
    lsmed = np.array([[o["modelo_hp"]["por_objetivo"][j]["lengthscale_med"] for j in range(M)] for o in dec])
    lsmax = np.array([[o["modelo_hp"]["por_objetivo"][j]["lengthscale_max"] for j in range(M)] for o in dec])
    osc = np.array([[o["modelo_hp"]["por_objetivo"][j]["outputscale"] for j in range(M)] for o in dec])
    r["HP_ard_vivo_frac"] = float((lsmin < lsmax).mean())
    r["HP_ard_vivo_n"] = int((lsmin < lsmax).sum())
    r["HP_ard_total"] = int(lsmin.size)
    dif = np.abs(np.diff(lsmed, axis=0)).max(axis=1)
    r["HP_lsmed_muda_n"] = int((dif > 0).sum()); r["HP_lsmed_pares"] = int(len(dif))
    r["HP_lsmed_ini"] = float(np.median(lsmed[0])); r["HP_lsmed_fim"] = float(np.median(lsmed[-1]))
    r["HP_osc_ini"] = float(np.median(osc[0])); r["HP_osc_fim"] = float(np.median(osc[-1]))
    for j in range(M):
        rows_hp.append(dict(label=lab, exp=exp, problema=prob, obj=j,
                            ls_med_ini=lsmed[0, j], ls_med_fim=lsmed[-1, j],
                            ls_med_min=lsmed[:, j].min(), ls_med_max=lsmed[:, j].max(),
                            osc_ini=osc[0, j], osc_fim=osc[-1, j],
                            ard_ratio_med=float(np.median(lsmax[:, j] / lsmin[:, j])),
                            ard_ratio_max=float((lsmax[:, j] / lsmin[:, j]).max())))

    # ── QUERY-JOIA: recomputo do maximin em [0,1]^D ────────────────────────
    onl = sur[sur["regime"] == "online"]
    onl_by_gen = {g: v for g, v in onl.groupby("geracao")}
    Xall01 = (real[xcols].values.astype(np.float64) - xl) / rng
    n_gen_ok_val = n_gen_ok_set = n_gen_ok_ord = n_gen_ok_mark = 0
    n_gen_ok_front = 0
    n_fb = 0
    dmax_joia = 0.0
    dmax_nat = 0.0
    ordem_asc = 0
    for o in dec:
        g = o["geracao"]
        blk = onl_by_gen[g]
        nfa = int(o["n_front_acq"])
        ntr_g = int(o["n_train"])
        idx = list(o["idx_escolhidos"])
        mm = np.array(o["maximin_escolhido"], float)
        cand01 = (blk[xcols].values.astype(np.float64) - xl) / rng
        ds01 = Xall01[:ntr_g]
        dmin = cdist(cand01, ds01).min(axis=1)
        fb = len(blk) != nfa or nfa < q
        # (a) linhas da ③-online == n_front_acq?
        front_ok = (len(blk) == nfa)
        if front_ok:
            n_gen_ok_front += 1
        # (b) valores: maximin_escolhido == dmin[idx]
        if max(idx) < len(dmin):
            dv = float(np.abs(dmin[np.array(idx)] - mm).max())
            dmax_joia = max(dmax_joia, dv)
            ok_val = dv < 1e-5
        else:
            dv = np.nan; ok_val = False
        # (c) conjunto: top-q do ranking
        topq = list(np.argsort(dmin, kind="stable")[-q:]) if len(dmin) >= q else []
        ok_set = set(topq) == set(idx) if topq else False
        ok_ord = list(topq) == list(idx) if topq else False
        # (d) ordem ascendente do maximin_escolhido
        if (np.diff(mm) >= -1e-12).all():
            ordem_asc += 1
        # (e) linhas marcadas na ③ == posições idx
        marked = np.where(blk["real_solution_id"].notna().values)[0].tolist()
        ok_mark = (marked == sorted(idx))
        # (f) dist_min_arquivo em espaço NATIVO
        dnat = cdist(blk[xcols].values.astype(np.float64), real[xcols].values.astype(np.float64)[:ntr_g]).min(axis=1)
        dma = o.get("dist_min_arquivo")
        if dma is not None and max(idx) < len(dnat):
            dnat_sel = dnat[np.array(idx)]
            dmax_nat = max(dmax_nat, float(abs(float(np.max(dnat_sel)) - float(dma))))
        n_gen_ok_val += int(ok_val); n_gen_ok_set += int(ok_set)
        n_gen_ok_ord += int(ok_ord); n_gen_ok_mark += int(ok_mark)
        if fb:
            n_fb += 1
            # completação: front inteiro + (q-nfa) pontos extra
            rows_fb.append(dict(label=lab, geracao=g, n_front_acq=nfa, n_online=len(blk),
                                q=q, n_lote=o["n_lote"], idx=str(idx),
                                mm=str([round(v, 6) for v in mm]),
                                front_todo_selecionado=bool(set(range(nfa)) <= set(idx)),
                                ok_val=ok_val, dv=dv, marked=str(marked)))
        rows_joia.append(dict(label=lab, exp=exp, problema=prob, geracao=g, q=q,
                              n_front_acq=nfa, n_online=len(blk), n_train=ntr_g,
                              fallback=fb, ok_val=ok_val, dv=dv, ok_set=ok_set,
                              ok_ord=ok_ord, ok_mark=ok_mark,
                              mm_min=float(mm.min()), mm_max=float(mm.max()),
                              dmin_max_recalc=float(dmin.max()),
                              dist_min_arquivo=dma))
    nG = len(dec)
    r["JOIA_n_ger"] = nG
    r["JOIA_front_ok"] = n_gen_ok_front
    r["JOIA_val_ok"] = n_gen_ok_val
    r["JOIA_set_ok"] = n_gen_ok_set
    r["JOIA_ord_ok"] = n_gen_ok_ord
    r["JOIA_mark_ok"] = n_gen_ok_mark
    r["JOIA_dmax"] = dmax_joia
    r["JOIA_dmax_nat_vs_distmin"] = dmax_nat
    r["JOIA_mm_ordem_asc"] = ordem_asc
    r["JOIA_n_fallback"] = n_fb

    # ── U11: erro de fantasia ─────────────────────────────────────────────
    mk = sur[sur["real_solution_id"].notna()]
    r["U11_n_marcadas"] = len(mk)
    r["U11_marcadas_ok"] = bool(len(mk) == nG * q)
    j = mk.merge(real[["solution_id"] + fcols], left_on="real_solution_id",
                 right_on="solution_id", how="left")
    for jj in range(M):
        err = np.abs(j[f"mu_{jj}"].values.astype(np.float64) - j[f"f{jj}"].values.astype(np.float64))
        r[f"U11_med_abs_err_obj{jj}"] = float(np.median(err))
        denom = np.abs(j[f"f{jj}"].values.astype(np.float64)).sum()
        r[f"U11_wape_infill_obj{jj}"] = float(err.sum() / denom) if denom > 0 else np.nan
        sg = j[f"sigma_{jj}"].values.astype(np.float64)
        r[f"U11_cob_infill_obj{jj}"] = float((err <= 1.96 * sg).mean())
        r[f"U11_z_med_obj{jj}"] = float(np.median(err / np.where(sg > 0, sg, np.nan)))
    # X do marcado == X da ① (identidade do ponto)
    jx = mk.merge(real[["solution_id"] + xcols], left_on="real_solution_id",
                  right_on="solution_id", how="left", suffixes=("", "_r"))
    dxid = np.abs(jx[xcols].values.astype(np.float64) -
                  jx[[c + "_r" for c in xcols]].values.astype(np.float64)).max()
    r["JOIA_dX_ponto_id"] = float(dxid)

    # sigma/ mu sanidade
    scols = [f"sigma_{jj}" for jj in range(M)]
    r["SIG_notna_frac"] = float(sur[scols].notna().all(axis=1).mean())
    r["SIG_pos_frac"] = float((sur[scols].values > 0).all(axis=1).mean())
    r["SIG_min"] = float(sur[scols].values.min())
    mus = [f"mu_{jj}" for jj in range(M)]
    r["MU_notna_frac"] = float(sur[mus].notna().all(axis=1).mean())
    # correlação mu×f na sonda (sinal)
    gf = gab[fcols].values[:2000].astype(np.float64)
    gl = sd[sd["geracao"] == gsonda[-1]]
    corr = [float(np.corrcoef(gl[f"mu_{jj}"].values.astype(np.float64), gf[:, jj])[0, 1]) for jj in range(M)]
    r["SINAL_corr_ultimo_bloco"] = str([round(c, 5) for c in corr])
    r["SINAL_corr_min"] = float(min(corr))

    # tempo
    r["T_total_s"] = float(man["timing"]["tempo_total_s"])
    r["T_fit_s"] = float(man["timing"]["tempo_fit_surrogate_s"])
    r["T_busca_s"] = float(man["timing"]["tempo_busca_s"])
    r["T_sonda_s"] = float(man["timing"]["tempo_pred_sonda_s"])
    r["T_aval_s"] = float(man["timing"]["tempo_aval_real_s"])

    rows_cell.append(r)
    for o in dec:
        rows_dec.append(dict(label=lab, exp=exp, problema=prob, D=D, M=M, q=q,
                             geracao=o["geracao"], iteracao=o["iteracao"],
                             n_train=o["n_train"], fe=o["fe"],
                             n_front_acq=o["n_front_acq"], n_front1=o["n_front1"],
                             n_lote=o["n_lote"], cache_hit=o["cache_hit"],
                             dist_min_arquivo=o.get("dist_min_arquivo"),
                             mm_min=float(min(o["maximin_escolhido"])),
                             mm_max=float(max(o["maximin_escolhido"])),
                             ts_min=float(np.min(o["draws_thompson"]["min"])),
                             ts_max=float(np.max(o["draws_thompson"]["max"])),
                             ts_med=float(np.mean(o["draws_thompson"]["med"])),
                             tempo_fit_s=o["tempo_fit_s"], tempo_busca_s=o["tempo_busca_s"],
                             seed_gp=o["seed_gp"], seed_nsga2=o["seed_nsga2"],
                             ls_med0=o["modelo_hp"]["por_objetivo"][0]["lengthscale_med"],
                             osc0=o["modelo_hp"]["por_objetivo"][0]["outputscale"]))
    print(f"OK {lab:16s} D={D:2d} M={M} q={q:2d} gens={nG:4d} joia_val={n_gen_ok_val}/{nG} "
          f"set={n_gen_ok_set}/{nG} mark={n_gen_ok_mark}/{nG} dmax={dmax_joia:.3e} fb={n_fb}", flush=True)

pd.DataFrame(rows_cell).to_csv(f"{OUT}/e81_celulas.csv", index=False)
pd.DataFrame(rows_dec).to_csv(f"{OUT}/e81_decisoes.csv", index=False)
pd.DataFrame(rows_joia).to_csv(f"{OUT}/e81_joia.csv", index=False)
pd.DataFrame(rows_fb).to_csv(f"{OUT}/e81_fallback.csv", index=False)
pd.DataFrame(rows_hp).to_csv(f"{OUT}/e81_modelo_hp.csv", index=False)
print("\nescrito em", OUT)
