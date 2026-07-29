#!/usr/bin/env python
"""F5.3b · b5r (Prob-RVEA, mode 7) — BATERIA A: checagens estruturais U1-U12 +
modulo de familia offline + aspectos especificos do bundle, nas 45 celulas.

Saidas: b5r_A_celulas.csv (1 linha/celula, ~90 colunas) + b5r_A_geracoes.pkl
(DataFrame por celula x geracao: n_pop, sigma medio, mu min etc).
READ-ONLY sobre os dados. Interpretador: mestrado_experimentos_dissertacao.
"""
import json
import os
import sys
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, REPO)
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5r"
OUT = os.path.join(REPO, "f5/baterias/b5r")
SEED = 42
EPS32 = np.finfo(np.float32).eps

PROBS_OFF = sorted(os.listdir(RES))


def celulas():
    out = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, str(SEED))
        if not os.path.isdir(d):
            continue
        if lab.startswith("swap_"):
            tok = lab[len("swap_"):]
            tier_dist, prob = tok.split("_", 1)
            tier, dist = tier_dist.split("-")
            exp = "sweep-%s-%s" % (tier, dist)
        else:
            prob, tier, dist, exp = lab, "main", "lhs", "off"
        out.append(dict(label=lab, dir=d, problema=prob, tier=tier, dist=dist, exp=exp))
    return out


def paths(c):
    p = c["problema"]
    exp = "off" if c["exp"] == "off" else c["exp"]
    stem = "exp_%s_b5r_%s_%d" % (exp, p, SEED)
    f = lambda s: os.path.join(c["dir"], stem + s)
    if not os.path.exists(f(".manifest.json")):
        cand = [x for x in os.listdir(c["dir"]) if x.endswith(".manifest.json")
                and not x.endswith("__final.manifest.json")]
        stem = cand[0][: -len(".manifest.json")]
        f = lambda s: os.path.join(c["dir"], stem + s)
    return dict(man=f(".manifest.json"), jsonl=f(".jsonl"), real=f("__real.parquet"),
                pop=f("__pop.parquet"), sur=f("__surrogate.parquet"),
                tim=f("__timing.parquet"), fin=f("__final.parquet"),
                finman=f("__final.manifest.json"), stem=stem)


def nds_mask(F):
    """mascara de nao-dominancia (minimizacao), O(n^2) — usa src.problems._nds_filter."""
    from src import problems as P
    idx = P._nds_filter(np.asarray(F, dtype=np.float64))
    m = np.zeros(len(F), dtype=bool)
    m[np.asarray(idx, dtype=int)] = True
    return m


def main():
    from src import problems as P
    cs = celulas()
    print("celulas:", len(cs))
    rows, gens = [], {}
    for c in cs:
        pt = paths(c)
        r = dict(label=c["label"], problema=c["problema"], tier=c["tier"],
                 dist=c["dist"], exp=c["exp"])
        man = json.load(open(pt["man"]))
        sd = man.get("sigma_dict", {})
        r.update(status=man["status"], n_retries=man["n_retries"],
                 fallback=man["fallback_ativado"], motivo=man.get("motivo_parada"),
                 maxfe=man["maxfe"], fe_final=man["fe_final"],
                 n_ger_man=man["n_geracoes"], cache_hits=man.get("cache_hits"),
                 algo_version=man.get("algo_version"),
                 py=man["env"]["python"], sklearn=man["env"]["sklearn"],
                 numpy=man["env"]["numpy"], pymoo=man["env"]["pymoo"],
                 t_total=man["timing"]["tempo_total_s"],
                 t_fit=man["timing"]["tempo_fit_surrogate_s"],
                 t_busca=man["timing"]["tempo_busca_s"],
                 t_real=man["timing"]["tempo_aval_real_s"],
                 t_sonda=man["timing"]["tempo_pred_sonda_s"],
                 n_fitseries=len(man.get("fit_series", [])),
                 fit_nacum=man["fit_series"][0]["n_acumulado"] if man.get("fit_series") else None,
                 sonda_S=man["sonda"]["S"], sonda_nblocos=man["sonda"]["n_blocos"],
                 sd_keys=len(sd), sd_modo=sd.get("fidelidade_por_modo", "")[:40],
                 has_params_5=("params" in man),
                 doe_hash=man["doe_hash"],
                 cp_x=man["cp_init_offline"]["x_hash"],
                 cp_f=man["cp_init_offline"]["f_hash"])
        r["doe_eq_cp"] = (man["doe_hash"] == man["cp_init_offline"]["x_hash"])

        # ---------- (1) real ----------
        d1 = pd.read_parquet(pt["real"])
        import re as _re
        _isx = lambda t: bool(_re.fullmatch(r"x\d+", t))
        _isf = lambda t: bool(_re.fullmatch(r"f\d+", t))
        xc = [x for x in d1.columns if _isx(x)]
        fc = [x for x in d1.columns if _isf(x)]
        D, M = len(xc), len(fc)
        r.update(D=D, M=M, n1=len(d1))
        r["U1_n1_eq_maxfe"] = (len(d1) == man["maxfe"] == man["fe_final"])
        r["U1_fase_init"] = bool((d1["fase"] == "init").all())
        r["U1_feidx_denso"] = bool(np.array_equal(d1["fe_index"].values, np.arange(len(d1))))
        r["U1_solid_denso"] = bool(np.array_equal(np.sort(d1["solution_id"].values), np.arange(len(d1))))
        X1 = d1[xc].values.astype(np.float32)
        F1 = d1[fc].values.astype(np.float64)

        # binding com o dataset do tier/dist (hash do artefato)
        tds = None if c["tier"] == "main" else c["tier"]
        dds = None if c["tier"] == "main" else c["dist"]
        suf = "" if (tds is None or (tds == "small" and dds == "lhs")) else "_%s_%s" % (tds, dds)
        dsp = os.path.join(REPO, "data/datasets", c["problema"],
                           "ds_%s_%d%s.parquet" % (c["problema"], SEED, suf))
        if os.path.exists(dsp):
            dds_df = pd.read_parquet(dsp)
            xcd = [x for x in dds_df.columns if _isx(x)]
            fcd = [x for x in dds_df.columns if _isf(x)]
            Xd = dds_df[xcd].values.astype(np.float32)
            Fd = dds_df[fcd].values.astype(np.float32)
            r["U2_dsX_bitaabit"] = bool(np.array_equal(Xd, X1))
            r["U2_dsF_bitaabit"] = bool(np.array_equal(Fd, d1[fc].values.astype(np.float32)))
            r["U2_ds_path"] = os.path.basename(dsp)
        else:
            r["U2_dsX_bitaabit"] = None
            r["U2_ds_path"] = "AUSENTE:" + os.path.basename(dsp)

        # ---------- (2) pop ----------
        d2 = pd.read_parquet(pt["pop"])
        r["F_2_vazia"] = (len(d2) == 0)

        # ---------- (3) surrogate ----------
        d3 = pd.read_parquet(pt["sur"])
        s3 = d3[d3.regime == "sonda"]
        b3 = d3[d3.regime == "offline"]
        r.update(n3=len(d3), n3_sonda=len(s3), n3_busca=len(b3),
                 n3_regimes="|".join(sorted(d3.regime.unique())))
        r["U4_sonda_20k"] = (len(s3) == 20000)
        r["U4_sonda_ger_null"] = bool(s3["geracao"].isna().all())
        r["U4_sonda_1bloco"] = (man["sonda"]["n_blocos"] == 1)
        r["U8_fetreino_const"] = (d3["fe_treino_max"].nunique() == 1)
        r["U8_fetreino_val"] = int(d3["fe_treino_max"].iloc[0])
        r["U8_fetreino_eq_N1"] = (r["U8_fetreino_val"] == len(d1) - 1)
        r["F_rsid_null"] = bool(d3["real_solution_id"].isna().all())
        r["F_espaco_cru"] = bool((d3["espaco_modelo"] == "cru").all())
        r["F_transf_null"] = bool(d3["transf_tipo"].isna().all() and d3["transf_params"].isna().all())
        r["F_predtipo_valor"] = bool((d3["pred_tipo"] == "valor").all())
        r["F_predclasse_null"] = bool(d3["pred_classe"].isna().all())
        r["F_modelo_flag"] = d3["modelo_flag"].iloc[0]
        r["F_modelo_flag_uni"] = (d3["modelo_flag"].nunique() == 1)
        muc = ["mu_%d" % j for j in range(M)]
        sgc = ["sigma_%d" % j for j in range(M)]
        r["F_sigma_nan_share"] = float(np.isnan(d3[sgc].values).mean())
        r["F_sigma_min"] = float(np.nanmin(d3[sgc].values))
        r["F_sigma_pos"] = bool(np.nanmin(d3[sgc].values) > 0)
        # sonda: media dos sigma
        r["F_sigma_sonda_med"] = float(np.nanmean(s3[sgc].values))
        r["F_sigma_busca_med"] = float(np.nanmean(b3[sgc].values))

        g = b3["geracao"].dropna().astype(int)
        ngen3 = int(g.max()) if len(g) else 0
        r["n_ger3"] = ngen3
        r["U10_ger_densa"] = bool(set(g.unique()) == set(range(1, ngen3 + 1)))
        r["U10_ngen_eq_man"] = (ngen3 == man["n_geracoes"])
        popsz = b3.groupby(b3["geracao"].astype(int)).size()
        NRV = 50 if M == 2 else 105
        r["NRV"] = NRV
        r["A_pop_max"] = int(popsz.max())
        r["A_pop_min"] = int(popsz.min())
        r["A_pop_med"] = float(popsz.median())
        r["A_pop_last"] = int(popsz.iloc[-1])
        r["A_pop_le_NRV"] = bool((popsz <= NRV).all())
        r["A_pop_eq_NRV_share"] = float((popsz == NRV).mean())
        r["A_pop_g1"] = int(popsz.iloc[0])

        # FE interno 40k previsto: init NRV + sum(par(|pop_{g-1}|))
        par = lambda n: n + (n % 2)
        seq = [NRV] + list(popsz.values[:-1])
        fe_prev = NRV + int(sum(par(int(n)) for n in seq))
        fe_prev_pre = NRV + int(sum(par(int(n)) for n in seq[:-1]))
        r["A_fe40k_prev"] = fe_prev
        r["A_fe40k_pre_ultima"] = fe_prev_pre
        r["A_fe40k_ok"] = bool(fe_prev_pre <= 40000 < fe_prev)
        r["A_overshoot"] = fe_prev - 40000

        # ---------- (4) timing ----------
        d4 = pd.read_parquet(pt["tim"])
        r["U3_n4_linhas"] = len(d4)
        r["U3_n4_eq_1"] = (len(d4) == 1)
        r["U3_n4_nacum"] = int(d4["n_acumulado"].iloc[0])
        r["U3_nacum_eq_N"] = (int(d4["n_acumulado"].iloc[0]) == len(d1))
        fit_s, bus_s, ger_s = (float(d4["tempo_fit_s"].iloc[0]),
                               float(d4["tempo_busca_s"].iloc[0]),
                               float(d4["tempo_geracao_s"].iloc[0]))
        snd_s = float(d4["tempo_pred_sonda_s"].iloc[0])
        r.update(t4_fit=fit_s, t4_busca=bus_s, t4_ger=ger_s, t4_sonda=snd_s)
        r["U7_fit_busca_le_ger"] = bool(fit_s + bus_s <= ger_s + 1e-3)
        r["U7_delta"] = ger_s - (fit_s + bus_s)
        r["U7_sonda_fora"] = bool(abs(ger_s - (fit_s + bus_s)) < 1e-2 and snd_s > 0)

        # ---------- (6) jsonl ----------
        L = [json.loads(x) for x in open(pt["jsonl"])]
        recs = pd.Series([x.get("rec") for x in L]).value_counts().to_dict()
        r["n6_linhas"] = len(L)
        r["n6_recs"] = json.dumps(recs, sort_keys=True)
        r["U9_guard"] = recs.get("guard", 0)
        r["U9_cachehits_5"] = man.get("cache_hits")
        dec = [x for x in L if x.get("rec") == "decision"]
        r["n6_decision"] = len(dec)
        r["U10_dec_eq_ngen"] = (len(dec) == ngen3)
        gd = [x["geracao"] for x in dec]
        r["U10_dec_densa"] = bool(gd == list(range(1, len(dec) + 1)))
        r["F_ndsmembros0"] = bool(all(x.get("n_ds_membros") == 0 for x in dec))
        r["F_fe_const"] = bool(len(set(x["fe"] for x in dec)) == 1 and dec[0]["fe"] == man["maxfe"])
        r["F_tfit_so_g1"] = bool(("tempo_fit_s" in dec[0]) and
                                 all("tempo_fit_s" not in x for x in dec[1:]))
        r["F_caminho"] = dec[0]["caminho"]
        r["F_motivo_dec"] = dec[0]["motivo"]
        foot = [x for x in L if x.get("rec") == "footer"]
        r["n6_footer"] = len(foot)
        r["F_footer_status"] = foot[0]["status"] if foot else None
        r["F_footer_nfinal"] = foot[0].get("n_final") if foot else None
        r["F_footer_nnd"] = foot[0].get("n_nd_pos_real") if foot else None
        snd_ev = [x for x in L if x.get("rec") == "sonda"]
        r["n6_sonda_ev"] = len(snd_ev)
        r["U4_hash_check"] = snd_ev[0].get("hash_check") if snd_ev else None

        # f_best/n_front1 do ⑥ x ③ (reconciliacao camada a camada)
        okfb = oknf = 0
        arrmu = {int(k): v[muc].values.astype(np.float64) for k, v in b3.groupby(b3["geracao"].astype(int))}
        for x in dec:
            gg = x["geracao"]
            Mu = arrmu[gg]
            fb = np.asarray(x["f_best"], dtype=np.float64)
            if np.allclose(fb, Mu.min(axis=0), rtol=1e-9, atol=1e-12):
                okfb += 1
            if x.get("n_front1") == int(nds_mask(Mu).sum()):
                oknf += 1
        r["U10_fbest_ok"] = okfb
        r["U10_nfront1_ok"] = oknf

        # ---------- (7) final ----------
        d7 = pd.read_parquet(pt["fin"])
        X7 = d7[[x for x in d7.columns if _isx(x)]].values.astype(np.float32)
        F7 = d7[[x for x in d7.columns if _isf(x)]].values.astype(np.float64)
        r["n7"] = len(d7)
        r["U12_n7_eq_poplast"] = (len(d7) == int(popsz.iloc[-1]))
        last = b3[b3["geracao"].astype(int) == ngen3]
        X3l = last[xc].values.astype(np.float32)
        r["U12_X_bitaabit"] = bool(X7.shape == X3l.shape and np.array_equal(X7, X3l))
        r["U12_origem_ger"] = bool((d7["origem_geracao"] == ngen3).all())
        r["U12_origem_linha"] = bool(np.array_equal(d7["origem_linha"].values, np.arange(len(d7))))
        r["U12_origem_solid_null"] = bool(d7["origem_solution_id"].isna().all())
        ndrec = nds_mask(F7.astype(np.float32).astype(np.float64))
        r["U12_nd_recomputa"] = bool(np.array_equal(ndrec, d7["nd_pos_real"].values))
        r["n7_nd"] = int(d7["nd_pos_real"].sum())
        r["F_fantasia"] = float(d7["nd_pos_real"].mean())
        r["U12_footer_bate"] = bool(foot and foot[0].get("n_final") == len(d7)
                                    and foot[0].get("n_nd_pos_real") == int(d7["nd_pos_real"].sum()))
        # ⑦ recomputada na verdade (round-trip float32)
        try:
            from src import experiment as _E
            Fchk = P.evaluate_problem(_E._instantiate_problem(c["problema"]),
                                      X7.astype(np.float64))
            r["U12_f_roundtrip_maxrel"] = float(np.max(np.abs(Fchk - F7) /
                                                       np.maximum(np.abs(F7), 1e-12)))
        except Exception as e:
            r["U12_f_roundtrip_maxrel"] = np.nan
            r["U12_f_err"] = str(e)[:80]

        # ---------- sonda posicional (U5) ----------
        sp = os.path.join(REPO, "data/sonda", "sonda_%s.parquet" % c["problema"])
        if os.path.exists(sp):
            ds_ = pd.read_parquet(sp)
            xcs = [x for x in ds_.columns if _isx(x)]
            Xs = ds_[xcs].values.astype(np.float32)
            X3s = s3[xc].values.astype(np.float32)
            r["U5_sonda_maxdx"] = float(np.max(np.abs(Xs - X3s))) if Xs.shape == X3s.shape else np.nan
            r["U5_sonda_bitaabit"] = bool(Xs.shape == X3s.shape and np.array_equal(Xs, X3s))
        else:
            r["U5_sonda_maxdx"] = np.nan
            r["U5_sonda_bitaabit"] = None

        # ---------- LHS-novo: intersecao busca x dataset ----------
        s1 = set(map(bytes, np.ascontiguousarray(X1)))
        Xg1 = b3[b3["geracao"].astype(int) == 1][xc].values.astype(np.float32)
        s2_ = set(map(bytes, np.ascontiguousarray(Xg1)))
        r["A_inter_g1_ds"] = len(s1 & s2_)
        Xall = b3[xc].values.astype(np.float32)
        r["A_inter_busca_ds"] = len(s1 & set(map(bytes, np.ascontiguousarray(Xall))))

        # ---------- por geracao (pickle) ----------
        gg = b3.groupby(b3["geracao"].astype(int))
        gdf = pd.DataFrame({
            "n_pop": gg.size(),
            "sigma_mean": gg.apply(lambda t: float(np.nanmean(t[sgc].values))),
            "sigma_max": gg.apply(lambda t: float(np.nanmax(t[sgc].values))),
            "mu_min0": gg[muc[0]].min(),
        })
        gens[c["label"]] = gdf

        rows.append(r)
        print("ok", c["label"], r["n_ger3"], r["n7"], flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "b5r_A_celulas.csv"), index=False)
    pd.to_pickle(gens, os.path.join(OUT, "b5r_A_geracoes.pkl"))
    print("gravado", df.shape)


def _inst(P, nome, D, M):
    import inspect
    cls = getattr(P, nome)
    sig = inspect.signature(cls.__init__).parameters
    kw = {}
    if "n_var" in sig:
        kw["n_var"] = D
    if "n_obj" in sig:
        kw["n_obj"] = M
    try:
        return cls(**kw)
    except Exception:
        return cls()


if __name__ == "__main__":
    main()
