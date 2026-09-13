"""B3 — Re-medicao do MECANISMO do c154 (JES) sobre a s42 (11 celulas) + o
smoke de teto (DTLZ2 D=12, truncada). Cobre os aspectos J1..J28 do relatorio F5.
READ-ONLY: le parquet/jsonl/manifest, nao invoca experiments.py.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154")
TETO = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
            "/experiments/main/c154")
DOE = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")


def celula(prob, base, tag):
    st = f"exp_main_c154_{prob}_42"
    man = json.load(open(base / f"{st}.manifest.json"))
    L = [json.loads(l) for l in open(base / f"{st}.jsonl")]
    hdr = [x for x in L if x.get("rec") == "header"][0]
    dec = [x for x in L if x.get("rec") == "decision"]
    grd = [x for x in L if x.get("rec") == "guard"]
    snd = [x for x in L if x.get("rec") == "sonda"]
    wrn = [x for x in L if x.get("rec") == "optimize_acqf_warning"]
    ftr = [x for x in L if x.get("rec") == "footer"]
    real = pd.read_parquet(base / f"{st}__real.parquet")
    sur = pd.read_parquet(base / f"{st}__surrogate.parquet")
    tim = pd.read_parquet(base / f"{st}__timing.parquet")
    pop = pd.read_parquet(base / f"{st}__pop.parquet")
    on = sur[sur.regime == "online"]
    sn = sur[sur.regime == "sonda"]
    D, M = hdr["D"], hdr["M"]
    xc = sorted([c for c in real.columns if c.startswith("x")
                 and c[1:].isdigit()], key=lambda c: int(c[1:]))
    fc = [f"f{j}" for j in range(M)]

    r = dict(prob=prob, tag=tag, D=D, M=M, status=man["status"],
             maxfe=man["maxfe"], fe_final=man["fe_final"],
             n_ger=man["n_geracoes"], cache_hits=man["cache_hits"])

    # --- J1 orcamento -------------------------------------------------------
    r["J1_len1"] = len(real)
    r["J1_31D_1"] = 31 * D - 1
    r["J1_fe_bate"] = (len(real) == man["fe_final"])
    r["J1_fe_index_denso"] = bool((real.fe_index.to_numpy() ==
                                   np.arange(len(real))).all())
    r["J1_sid_denso"] = bool((real.solution_id.to_numpy() ==
                              np.arange(len(real))).all())
    r["J1_motivo_parada"] = man.get("motivo_parada", "<AUSENTE>")
    r["J1_hard_stopped"] = ftr[0].get("hard_stopped") if ftr else None
    r["J1_ger_eq_infill_mais1"] = (man["n_geracoes"] ==
                                   len([d for d in dec
                                        if d.get("caminho") == "infill"]) + 1)

    # --- J2 DoE -------------------------------------------------------------
    ninit = int((real.fase == "init").sum())
    r["J2_init"] = ninit
    r["J2_11D_1"] = 11 * D - 1
    art = DOE / prob / f"doe_{prob}_42.npy"
    if art.exists():
        A = np.load(art)
        r["J2_dX_max"] = float(np.abs(
            real.loc[real.fase == "init", xc].to_numpy() - A[:ninit]).max())
    else:
        r["J2_dX_max"] = None
    r["J2_cp_init"] = ftr[0].get("cp_init") if ftr else None
    r["J2_doe_hash_bate"] = (man["doe_hash"] == hdr["doe_hash"])

    # --- J3/J5/J6 modelo ----------------------------------------------------
    ard = mud = ntr_ok = ftm_ok = 0
    ls_prev = None
    noises, outs, ntot = [], [], 0
    for d in dec:
        hp = d.get("modelo_hp") or {}
        po = hp.get("por_objetivo") or []
        for o in po:
            ntot += 1
            if o.get("lengthscale_min") != o.get("lengthscale_max"):
                ard += 1
            if o.get("noise") is not None:
                noises.append((prob, d["it"], o.get("noise"),
                               o.get("outputscale")))
        cur = tuple(round(o.get("lengthscale_med", 0), 15) for o in po)
        if ls_prev is not None and cur != ls_prev:
            mud += 1
        ls_prev = cur
        if d.get("n_train") is not None:
            ntr_ok += 1
    r["J3_ard_viva"] = f"{ard}/{ntot}"
    r["J5_muda_ls"] = f"{mud}/{max(len(dec)-1,1)}"
    r["J5_fits_eq_ger"] = (len(tim) == man["n_geracoes"] == len(dec))
    r["J21_n_train_pres"] = f"{ntr_ok}/{len(dec)}"
    r["J21_n_baseline_aus"] = sum(1 for d in dec if "n_baseline" not in d)
    ftm = on.fe_treino_max.dropna().to_numpy()
    r["J6_ftm_monot"] = bool((np.diff(ftm) >= 0).all()) if len(ftm) else None
    ok = sum(1 for d in dec
             if any(on[(on.geracao == d["it"])].fe_treino_max.dropna()
                    == d.get("n_train", -1) - 1))
    r["J6_ftm_eq_ntrain_1"] = f"{ok}/{len(dec)}"

    # --- J4 ruido -----------------------------------------------------------
    nz = pd.DataFrame(noises, columns=["prob", "it", "noise", "outputscale"])
    r["J4_n_iter_obj"] = len(nz)
    r["J4_no_piso_1e4"] = int((nz.noise <= 1.0001e-4).sum())
    r["J4_razao_max"] = (float(nz.noise.max() / nz.noise.min())
                         if len(nz) and nz.noise.min() > 0 else None)

    # --- J8 shapes ----------------------------------------------------------
    sh = Counter((tuple(d.get("pf_shape", [])), tuple(d.get("ps_shape", [])))
                 for d in dec)
    r["J8_shapes"] = str(dict(sh))
    r["J8_ok"] = all(k[0] == (10, 10, M) and k[1] == (10, 10, D) for k in sh)

    # --- J9/J10 escada ------------------------------------------------------
    esc = [g for g in grd if g.get("name") == "rs_runtimeerror_fallback"] + \
          [x for x in L if x.get("rec") == "rs_runtimeerror_fallback"]
    r["J10_escada"] = len(esc)
    r["J10_footer"] = ftr[0].get("rs_fallbacks_total") if ftr else None
    r["J9_rota_a"] = sum(1 for d in dec if d.get("rota") == "a")
    r["J9_rota_b95"] = man.get("jes", {}).get("rota_b95")

    # --- J11 restarts -------------------------------------------------------
    nr = set(d.get("n_restarts") for d in dec)
    rs = set(d.get("raw_samples") for d in dec)
    r["J11_num_restarts"] = str(nr)
    r["J11_raw_samples"] = str(rs)
    r["J11_5D_1000D"] = (nr == {5 * D} and rs == {1000 * D})
    lin = on.groupby("geracao").size().unique()
    r["J11_linhas_por_ger"] = str(sorted(lin.tolist()))

    # --- J12 NaN guards -----------------------------------------------------
    r["J12_ics"] = sum(1 for g in grd if g.get("name") == "nan_guard_ics")
    r["J12_argmax"] = sum(1 for g in grd if g.get("name") == "nan_guard_argmax")
    naofin = sum(int((~np.isfinite(np.asarray(d["acqf_todos_restarts"],
                                              float))).sum())
                 for d in dec if d.get("acqf_todos_restarts"))
    r["J12_naofin_export"] = naofin

    # --- query-joia: argmax + identidade ------------------------------------
    jo = joid = tot = 0
    for d in dec:
        a = d.get("acqf_todos_restarts")
        if a is None or d.get("acqf_escolhido") is None:
            continue
        a = np.asarray(a, float)
        f = np.isfinite(a)
        tot += 1
        if abs(float(d["acqf_escolhido"]) - float(a[f].max())) <= 1e-12:
            jo += 1
    r["QJ_argmax"] = f"{jo}/{tot}"
    # identidade do ponto escolhido (ultima linha marcada vs 1a)
    mk = on[on.real_solution_id.notna()]
    if len(mk):
        idx = mk.real_solution_id.astype(int).to_numpy()
        dx = np.abs(mk[xc].to_numpy() - real.loc[idx, xc].to_numpy()).max()
        r["QJ_dX_marcada"] = float(dx)
        r["QJ_n_marcadas"] = len(mk)
    # J28 plateau
    pl = 0
    for d in dec:
        a = d.get("acqf_todos_restarts")
        if not a:
            continue
        a = np.asarray(a, float)
        a = a[np.isfinite(a)]
        if len(a) >= 2:
            mx = a.max()
            if (np.abs(a - mx) <= 1e-9 * max(abs(mx), 1e-300)).sum() >= 2:
                pl += 1
    r["J28_plateau"] = f"{pl}/{len(dec)}"
    r["J28_acqf_pos"] = sum(1 for d in dec
                            if (d.get("acqf_escolhido") or 0) > 0)

    # --- J16 seeds ----------------------------------------------------------
    hs = [h for d in dec for h in (d.get("hs_paths") or [])]
    r["J16_hs_total"] = len(hs)
    r["J16_hs_distintos"] = len(set(hs))
    r["J16_torch_seed_dist"] = len(set(d.get("torch_seed") for d in dec))

    # --- J17 fronts amostrados ---------------------------------------------
    nv = nf = 0
    for d in dec:
        pf = d.get("pf_amostrados_f")
        if pf is None:
            continue
        A = np.asarray(pf, float)
        nv += A.size
        nf += int(np.isfinite(A).sum())
    r["J17_valores"] = nv
    r["J17_finitos"] = nf

    # --- J14/J15 sinal e sigma ---------------------------------------------
    r["J15_sigma_nonnull"] = int(sur[[f"sigma_{j}" for j in range(M)]]
                                 .notna().all(1).sum())
    r["J15_sur_linhas"] = len(sur)
    r["J14_transf_null"] = bool(sur.transf_tipo.isna().all())

    # --- J19 sonda ----------------------------------------------------------
    gs = sorted(sn.geracao.dropna().astype(int).unique().tolist())
    go = sorted(on.geracao.dropna().astype(int).unique().tolist())
    esp = [g for g in go if g == 1 or g % 2 == 0]
    r["J19_blocos"] = len(gs)
    r["J19_blocos_ftr"] = ftr[0].get("n_blocos_sonda") if ftr else None
    r["J19_ultima_coberta"] = (go[-1] in gs) if go else None
    r["J19_cadencia_pura"] = (gs == esp)
    r["J19_linhas_bloco"] = str(sn.groupby("geracao").size().unique().tolist())
    r["J19_hash_ok"] = sum(1 for s in snd if s.get("hash_check") == "ok")
    r["J19_n_eventos"] = len(snd)

    # --- J20 timing ---------------------------------------------------------
    som = tim.tempo_fit_s + tim.tempo_busca_s
    r["J20_inv1"] = int((som <= tim.tempo_geracao_s + 1e-9).sum())
    cs = tim[tim.geracao.isin(gs)]
    ss = tim[~tim.geracao.isin(gs)]
    r["J20_inv2_com"] = (f"{int(((cs.tempo_fit_s+cs.tempo_busca_s+cs.tempo_pred_sonda_s)>cs.tempo_geracao_s).sum())}"
                         f"/{len(cs)}")
    r["J20_inv2_sem"] = int(((ss.tempo_fit_s + ss.tempo_busca_s +
                              ss.tempo_pred_sonda_s) > ss.tempo_geracao_s).sum())
    tt = man.get("timing", {})
    r["J20_h_core"] = round(tt.get("tempo_total_s", 0) / 3600, 3)
    r["J20_paths_s"] = tt.get("tempo_paths_s")
    r["J20_busca_s"] = tt.get("tempo_busca_s")
    r["J20_pct_paths"] = (round(100 * tt["tempo_paths_s"] / tt["tempo_busca_s"], 2)
                          if tt.get("tempo_busca_s") else None)
    r["J20_aval_real_s"] = tt.get("tempo_aval_real_s")

    # --- J23 pop ------------------------------------------------------------
    sz = pop.groupby("geracao").size()
    r["J23_pop_gen0"] = int(sz.iloc[0])
    r["J23_pop_final"] = int(sz.iloc[-1])
    r["J23_pop_total"] = len(pop)
    r["J23_pop_esperado"] = int(ninit + sum(ninit - 1 + g
                                            for g in range(1, len(sz))))

    # --- J26 warnings -------------------------------------------------------
    r["J26_warn_ev"] = len(wrn)
    r["J26_warn_soma"] = sum(d.get("acqf_warnings") or 0 for d in dec)

    # --- J18 cache ----------------------------------------------------------
    r["J18_cache_dec"] = sum(1 for d in dec if d.get("cache_hit"))
    r["J18_cache_man"] = man["cache_hits"]

    # --- T11: campos novos --------------------------------------------------
    r["T11_params_manifesto"] = "params" in man
    r["T11_campanha_id"] = man.get("campanha_id", "<AUSENTE>")
    r["T11_repo_hash"] = (man.get("repo_hash") or "<AUSENTE>")[:12]
    r["T11_checkpoint"] = json.dumps(man.get("checkpoint", "<AUSENTE>"))
    r["T11_ordem3a"] = ("ordem_terceira_online" in hdr.get("sigma_dict", {}))
    return r


if __name__ == "__main__":
    linhas = [celula(p, ROOT / p / "42", "s42")
              for p in sorted(x.name for x in ROOT.iterdir() if x.is_dir())]
    linhas.append(celula("DTLZ2", TETO, "teto_T11"))
    df = pd.DataFrame(linhas)
    df.to_csv(OUT / "c154_mecanismo_t11.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 200)
    for c in df.columns:
        print(f"{c:24s}", df[c].tolist())
