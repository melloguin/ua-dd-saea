#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 1: estrutura universal U1-U11 + aspectos do bundle.
Executa nas 25 celulas main/semente 42. Somente leitura dos dados.
Saidas: estrutura_celula.csv (1 linha/celula) + gens_c238.csv (1 linha/geracao, todas as celulas).
"""
import json, os, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
EPS = np.finfo(float).eps


def ndmask(Y):
    n = len(Y)
    keep = np.ones(n, bool)
    for i in range(n):
        d = (Y <= Y[i]).all(1) & (Y < Y[i]).any(1)
        if d.any():
            keep[i] = False
    return keep


def do_cell(prob):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    man = json.load(open(f"{b}.manifest.json"))
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    foot = [r for r in recs if r.get("rec") == "footer"]
    gens = [r for r in recs if r.get("rec") == "c238_gen"]
    sond = [r for r in recs if r.get("rec") == "sonda"]
    guards = [r for r in recs if r.get("rec") == "guard"]
    D, M = hdr["D"], hdr["M"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    pop = pq.read_table(f"{b}__pop.parquet").to_pandas()
    tim = pq.read_table(f"{b}__timing.parquet").to_pandas()
    sur = pq.read_table(f"{b}__surrogate.parquet",
                        columns=["regime", "geracao", "real_solution_id", "pred_tipo", "pred_classe",
                                 "pred_score", "pred_confianca", "modelo_flag", "espaco_modelo",
                                 "transf_tipo", "fe_treino_max"] +
                                [f"mu_{i}" for i in range(M)] + [f"sigma_{i}" for i in range(M)]).to_pandas()
    on = sur[sur.regime == "online"]
    so = sur[sur.regime == "sonda"]
    fcols = [f"f{i}" for i in range(M)]
    Fall = real[fcols].values.astype(np.float64)
    init = 11 * D - 1
    maxfe = 31 * D - 1

    G = pd.DataFrame(gens)
    # arrays por geracao
    nm = np.array([r["norm_min"] for r in gens], float)
    nx = np.array([r["norm_max"] for r in gens], float)
    nre = np.array([r["norm_range_efetivo"] for r in gens], float)
    thmin = np.array([r["theta_min"] for r in gens], float)
    thmax = np.array([r["theta_max"] for r in gens], float)
    ubest = np.array([r["u_best"] for r in gens], float)
    sbest = np.array([r["s_best"] for r in gens], float)
    fbest = np.array([r["f_best"] for r in gens], float)
    namo = G.n_amostra.values

    # ---- y-rescaling: norm_min/max == min/max do arquivo PRE-infill
    dmin = np.zeros(len(gens)); dmax = np.zeros(len(gens)); drange = np.zeros(len(gens))
    nf_ok = 0; nf1_ok = 0
    nfront_calc = np.zeros(len(gens), int); nfront1_calc = np.zeros(len(gens), int)
    for i, r in enumerate(gens):
        Y = Fall[:namo[i]]
        dmin[i] = np.max(np.abs(Y.min(0) - nm[i]) / np.maximum(np.abs(nm[i]), 1e-12))
        dmax[i] = np.max(np.abs(Y.max(0) - nx[i]) / np.maximum(np.abs(nx[i]), 1e-12))
        rg = np.maximum(nx[i] - nm[i], EPS)
        drange[i] = np.max(np.abs(rg - nre[i]) / np.maximum(np.abs(nre[i]), 1e-300))
    # ND fronts (custoso -> so onde arquivo <= 1200; todos cabem)
    for i, r in enumerate(gens):
        Y = Fall[:namo[i]]
        nfront_calc[i] = ndmask(Y).sum()
        if namo[i] + 1 <= len(Fall):
            nfront1_calc[i] = ndmask(Fall[:namo[i] + 1]).sum()
        else:
            nfront1_calc[i] = -1
    nf_ok = int((nfront_calc == G.n_front.values).sum())
    nf1_ok = int((nfront1_calc == G.n_front1.values).sum())

    # ---- U11 erro de fantasia: mu do infill (espaco modelo) -> cru vs f real
    inf = on[on.real_solution_id.notna()].copy()
    inf = inf.sort_values("geracao")
    mu = inf[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
    sg = inf[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
    gi = inf.geracao.values.astype(int) - 1
    mu_cru = mu * nre[gi] + nm[gi]
    sid = inf.real_solution_id.values.astype(int)
    f_real = Fall[sid]
    err = mu_cru - f_real
    denom = np.maximum(np.abs(f_real), 1e-12)
    # cobertura 2sigma do infill (sigma no espaco do modelo -> multiplicar por range)
    sg_cru = sg * nre[gi]
    cob_inf = float((np.abs(err) <= 1.96 * sg_cru).mean())
    # u_best/s_best do jsonl == mu/sigma da linha do infill na (3)?
    du = np.max(np.abs(ubest[gi] - mu) / np.maximum(np.abs(ubest[gi]), 1e-12)) if len(mu) else np.nan
    ds = np.max(np.abs(sbest[gi] - sg) / np.maximum(np.abs(sbest[gi]), 1e-12)) if len(sg) else np.nan
    # f_best do jsonl == min por objetivo do arquivo pre-infill (== norm_min)?
    df_best = np.max(np.abs(fbest - nm) / np.maximum(np.abs(nm), 1e-12))

    # ---- U7 timing
    viol = tim[(tim.tempo_fit_s + tim.tempo_busca_s) > tim.tempo_geracao_s]
    gsonda = set(int(r["geracao"]) for r in sond)
    viol_em_sonda = int(viol.geracao.isin(gsonda).sum())

    # ---- pop (2)
    popsz = pop.groupby("geracao").size()
    ult = pop[pop.geracao == pop.geracao.max()]

    # ---- (3) online
    on_sz = on.groupby("geracao").size()
    so_sz = so.groupby("geracao").size()

    # ---- guards
    gnames = pd.Series([g.get("name") for g in guards]).value_counts().to_dict()
    ch_guard = gnames.get("cache_hit", 0)
    c0 = sum(1 for g in guards if g.get("name") == "cache_hit" and g.get("fe", 10**9) <= init)

    # cadencia da sonda
    gs = sorted(gsonda)
    ng = len(gens)
    cad_esp = [g for g in range(1, ng + 1) if g == 1 or g % 2 == 0]
    if ng not in cad_esp:
        cad_esp.append(ng)
    cad_ok = (gs == sorted(cad_esp))

    row = dict(
        problema=prob, D=D, M=M, maxfe=maxfe, init=init,
        man_maxfe=man["maxfe"], man_fe_final=man["fe_final"], man_status=man["status"],
        man_n_geracoes=man["n_geracoes"], man_cache_hits=man["cache_hits"],
        man_fallback=man["fallback_ativado"],
        footer_n=len(foot), footer_termino=foot[0]["termino"] if foot else None,
        footer_status=foot[0]["status"] if foot else None,
        footer_cp_init=foot[0].get("cp_init") if foot else None,
        # U1
        n_real=len(real), u1_len_ok=len(real) == maxfe,
        u1_fe_dense=bool((real.fe_index.values == np.arange(len(real))).all()),
        u1_sid_unique=int(real.solution_id.nunique()) == len(real),
        # U2
        n_init=int((real.fase == "init").sum()), u2_init_ok=int((real.fase == "init").sum()) == init,
        n_opt=int((real.fase == "opt").sum()),
        doe_hash=man["doe_hash"][:12], sonda_x_hash=man["sonda"]["x_hash"][:12],
        # U3/U6-estrutura
        n_gens_jsonl=len(gens), n_rows_timing=len(tim), u3_fit_por_iter=len(tim) == len(gens),
        # U4
        n_blocos_sonda=len(sond), sonda_manifest_blocos=man["sonda"]["n_blocos"],
        u4_cadencia_ok=bool(cad_ok), sonda_S=man["sonda"]["S"], sonda_k=man["sonda"]["k"],
        sonda_n_falhas=man["sonda"]["n_falhas"],
        sonda_linhas_ok=bool((so_sz == man["sonda"]["S"]).all()) and so_sz.shape[0] == len(sond),
        # U7
        u7_viol=len(viol), u7_viol_em_sonda=viol_em_sonda,
        u7_ok=len(viol) == 0,
        # U8
        u8_fe_treino_max_monot=bool((np.diff(G.fe_treino_max.values) >= 0).all()),
        fe_treino_max_ini=int(G.fe_treino_max.iloc[0]), fe_treino_max_fim=int(G.fe_treino_max.iloc[-1]),
        # U9/U10
        guards=json.dumps(gnames), cache_hit_guard=ch_guard, c0=c0,
        u10_ledger=len(gens) == int((real.fase == "opt").sum()) + ch_guard - c0,
        u10_pop_gens=int(pop.geracao.nunique()), u10_pop_offby1=int(pop.geracao.nunique()) == len(gens) + 1,
        u10_pop_sz_ok=bool((popsz.values == (init - 1) + np.arange(1, pop.geracao.nunique() + 1)).all()),
        u10_dup_ultima_pop=int(ult.solution_id.duplicated().sum()),
        # (3) online
        c9_ga_pop_decl=int(G.ga_pop.iloc[0]), c9_ga_pop_esp=10 * D,
        c9_ga_pop_ok=bool((G.ga_pop.values == 10 * D).all()),
        c9_ga_gens=int(G.ga_gens.iloc[0]), c9_ga_gens_ok=bool((G.ga_gens.values == 200).all()),
        c9_pool_rows_ok=bool((on_sz.values == 10 * D).all()),
        c9_aval_aquis_iter=int(G.ga_pop.iloc[0]) * int(G.ga_gens.iloc[0]),
        # (3) metadados
        espaco_modelo=";".join(sorted(map(str, on.espaco_modelo.unique()))),
        transf_tipo=";".join(sorted(map(str, on.transf_tipo.unique()))),
        pred_tipo=";".join(sorted(map(str, on.pred_tipo.unique()))),
        modelo_flag=";".join(sorted(map(str, sur.modelo_flag.unique()))),
        sonda_espaco=";".join(sorted(map(str, so.espaco_modelo.unique()))),
        pred_classe_null=int(sur.pred_classe.isna().sum()) == len(sur),
        pred_score_null=int(sur.pred_score.isna().sum()) == len(sur),
        sigma_null_online=int(on[[f"sigma_{i}" for i in range(M)]].isna().sum().sum()),
        sigma_null_sonda=int(so[[f"sigma_{i}" for i in range(M)]].isna().sum().sum()),
        rsid_online_notna=int(on.real_solution_id.notna().sum()),
        rsid_sonda_notna=int(so.real_solution_id.notna().sum()),
        # y-rescaling (C8)
        c8_dmin_max=float(dmin.max()), c8_dmax_max=float(dmax.max()), c8_drange_max=float(drange.max()),
        c8_ok=bool(dmin.max() < 1e-6 and dmax.max() < 1e-6 and drange.max() < 1e-9),
        c8_range0_total=int(G.n_range0.sum()),
        c8_range_min=float(nre.min()),
        # front (C19 crash latente)
        c19_nfront_min=int(G.n_front.min()), c19_nfront_max=int(G.n_front.max()),
        c19_nfront_eq1=int((G.n_front.values == 1).sum()),
        c19_nfront_calc_ok=nf_ok, c19_nfront1_calc_ok=nf1_ok, n_gens=len(gens),
        nfront_mediana=float(np.median(G.n_front.values)),
        # dedup / treino (C11)
        c11_dedup_total=int(G.n_dedup.sum()), c11_dedup_max=int(G.n_dedup.max()),
        c11_ntreino_ok=bool((G.n_treino.values == G.n_amostra.values - G.n_dedup.values).all()),
        c11_namostra_cresce=bool((np.diff(G.n_amostra.values) >= 0).all()),
        c15_assinatura_mais1=bool((np.diff(G.n_treino.values + G.n_dedup.values) == 1).all()),
        # guards EIM/anti-clustering
        c13_eim_nan_total=int(G.n_eim_nan.sum()),
        c12_mindist_min=float(G.min_dist_infill.min()), c12_mindist_lt1e8=int((G.min_dist_infill.values < 1e-8).sum()),
        c12_mindist_mediana=float(np.median(G.min_dist_infill.values)),
        c18_stall_max=int(G.stall_iters.max()), c18_stall_gt0=int((G.stall_iters.values > 0).sum()),
        # theta (C5)
        c5_theta_min_global=float(thmin.min()), c5_theta_max_global=float(thmax.max()),
        c5_viola_lb=int((thmin < 1e-3 - 1e-15).sum()), c5_viola_ub=int((thmax > 1e3 + 1e-9).sum()),
        c5_sat_lb=int((np.abs(thmin - 1e-3) <= 1e-12).sum()), c5_sat_ub=int((np.abs(thmax - 1e3) <= 1e-6).sum()),
        c5_ncomp=int(thmin.size),
        lnL_min=float(np.min([np.min(r["lnL"]) for r in gens])),
        lnL_max=float(np.max([np.max(r["lnL"]) for r in gens])),
        # eim
        eim_best_min=float(G.eim_best.min()), eim_best_max=float(G.eim_best.max()),
        eim_best_ultimo=float(G.eim_best.iloc[-1]),
        eim_best_monot_desc=int((np.diff(G.eim_best.values) > 0).sum()),
        eim_ybest_ident=bool(np.allclose(G.eim_best.values, G.y_best.values, rtol=0, atol=0)),
        eim_med_pool_razao_ini=float(G.eim_mediana_pool.iloc[0] / max(G.eim_best.iloc[0], 1e-300)),
        eim_med_pool_razao_fim=float(G.eim_mediana_pool.iloc[-1] / max(G.eim_best.iloc[-1], 1e-300)),
        eim_med_pool_decai=float(G.eim_mediana_pool.iloc[-1] / max(G.eim_mediana_pool.iloc[0], 1e-300)),
        # s_best (sigma no infill)
        s_best_zeros=int((sbest == 0).sum()), s_best_min=float(sbest.min()),
        s_best_med=float(np.median(sbest)),
        # u_best/s_best <-> (3)
        du_ubest=float(du), ds_sbest=float(ds), df_best_vs_normmin=float(df_best),
        # U11
        u11_err_mediana=float(np.median(np.abs(err))),
        u11_err_rel_mediana=float(np.median(np.abs(err) / denom)),
        u11_otimista_frac=float((err < 0).mean()),
        u11_cob2sigma_infill=cob_inf,
        # fe
        fe_iter_soma=int(G.fe_iter.sum()), lote_unicos=";".join(map(str, sorted(G.lote.unique()))),
        fe_ultimo=int(G.fe.iloc[-1]),
        # tempos
        tempo_total_s=man["timing"]["tempo_total_s"],
        tempo_fit_s=man["timing"]["tempo_fit_surrogate_s"],
        tempo_busca_s=man["timing"]["tempo_busca_s"],
        tempo_aval_real_s=man["timing"]["tempo_aval_real_s"],
        tempo_pred_sonda_s=man["timing"]["tempo_pred_sonda_s"],
    )
    # gens detail
    Gd = G[["geracao", "iter", "fe", "n_amostra", "n_treino", "n_dedup", "n_front", "n_front1",
            "eim_best", "eim_mediana_pool", "min_dist_infill", "stall_iters", "n_eim_nan",
            "n_range0", "infill_sid", "fe_treino_max", "tempo_fit_s", "tempo_busca_s",
            "tempo_geracao_s"]].copy()
    Gd.insert(0, "problema", prob)
    Gd["nfront_calc"] = nfront_calc
    Gd["nfront1_calc"] = nfront1_calc
    Gd["theta_min"] = thmin.min(1)
    Gd["theta_max"] = thmax.max(1)
    Gd["norm_range_min"] = nre.min(1)
    return row, Gd


if __name__ == "__main__":
    probs = sorted(os.listdir(BASE))
    rows, gd = [], []
    for p in probs:
        try:
            r, g = do_cell(p)
            rows.append(r); gd.append(g)
            print(f"OK {p}", flush=True)
        except Exception as e:
            print(f"ERRO {p}: {type(e).__name__}: {e}", flush=True)
            raise
    pd.DataFrame(rows).to_csv(f"{OUT}/estrutura_celula.csv", index=False)
    pd.concat(gd).to_csv(f"{OUT}/gens_c238.csv", index=False)
    print("gravado")
