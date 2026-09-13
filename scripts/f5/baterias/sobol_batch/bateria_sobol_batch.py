#!/usr/bin/env python
"""BATERIA DE FIDELIDADE — config `sobol_batch` (piso do batch, alg_id=22, D37/D66/DI-33).

F5.3b · protocolo v1.1 · semente 42 · 5 células q10_{DTLZ2,MMF16_20,WFG9,ZDT1,ZDT4}.
READ-ONLY sobre dados/artefatos; escreve SÓ em f5/baterias/sobol_batch/.

Executa: universais U1–U12 (aplicáveis), módulo de família (piso online sem modelo),
específicos do bundle (Sobol scrambled/Owen, q=10, orçamento 11D−1+200q, CP-init,
uniformidade/discrepância) e a QUERY-JOIA: recomputo bit-a-bit do lote Sobol de cada
iteração a partir do `seed_sobol` gravado no ⑥ e da receita `iteration_seed(base,22,g,0)`.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
RES = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = REPO / "f5" / "baterias" / "sobol_batch"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from src import standalone_harness as H          # noqa: E402
from scipy.stats import qmc, kstest              # noqa: E402

ALG = "sobol_batch"
ALG_ID = 22
SEED = 42
Q = 10
K = 200
PROBS = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]

EPS32 = np.finfo(np.float32).eps


def cell_paths(prob: str) -> dict:
    d = RES / ALG / f"q10_{prob}" / str(SEED)
    b = d / f"exp_batch_{ALG}_{prob}_{SEED}"
    return {
        "dir": d, "manifest": Path(str(b) + ".manifest.json"),
        "jsonl": Path(str(b) + ".jsonl"),
        "real": Path(str(b) + "__real.parquet"),
        "pop": Path(str(b) + "__pop.parquet"),
        "surr": Path(str(b) + "__surrogate.parquet"),
        "timing": Path(str(b) + "__timing.parquet"),
    }


def read_jsonl(p: Path):
    recs, bad = [], 0
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            bad += 1
    return recs, bad


def sobol_batch01(D: int, q: int, seed: int) -> np.ndarray:
    """Réplica EXATA de src/sobol_batch.py::_sobol_batch01."""
    sob = qmc.Sobol(d=int(D), scramble=True, seed=int(seed))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*balance properties.*")
        return np.asarray(sob.random(int(q)), dtype=np.float64)


rows = []          # 1 linha por célula, dezenas de colunas de check
gen_rows = []      # 1 linha por (célula, geração)
disc_rows = []     # discrepância / uniformidade
ks_rows = []       # KS por dimensão

for prob in PROBS:
    P = cell_paths(prob)
    r = {"alg": ALG, "problema": prob, "semente": SEED}

    man = json.loads(P["manifest"].read_text())
    recs, badlines = read_jsonl(P["jsonl"])
    real = pd.read_parquet(P["real"])
    pop = pd.read_parquet(P["pop"])
    surr = pd.read_parquet(P["surr"])
    tim = pd.read_parquet(P["timing"])

    xl, xu = H._bounds(prob)
    probobj = H._instantiate(prob)
    D, M = len(xl), int(probobj.n_obj)
    n_init = 11 * D - 1
    maxfe = n_init + K * Q

    r.update(D=D, M=M, n_init_esperado=n_init, maxfe_esperado=maxfe)

    # ───────── ⑤ manifesto ─────────
    r["m_status"] = man.get("status")
    r["m_motivo_parada"] = man.get("motivo_parada")
    r["m_n_retries"] = man.get("n_retries")
    r["m_fallback"] = man.get("fallback_ativado")
    r["m_maxfe"] = man.get("maxfe")
    r["m_fe_final"] = man.get("fe_final")
    r["m_n_geracoes"] = man.get("n_geracoes")
    r["m_q"] = man.get("q")
    r["m_exp"] = man.get("exp")
    r["m_regime"] = man.get("regime")
    r["m_algo_version"] = man.get("algo_version")
    r["m_cache_hits"] = man.get("cache_hits")
    r["m_tem_params"] = "params" in man
    r["m_tem_sigma_dict"] = "sigma_dict" in man
    r["m_sonda_status"] = (man.get("sonda") or {}).get("status")
    r["m_sonda_nblocos"] = (man.get("sonda") or {}).get("n_blocos")
    r["m_tier"] = man.get("tier")
    r["m_dist"] = man.get("dist")
    r["m_doe_hash"] = man.get("doe_hash")
    r["m_repo_hash"] = man.get("repo_hash")
    r["m_env_python"] = man["env"]["python"]
    r["m_env_exec"] = man["env"]["executable"]
    r["m_env_numpy"] = man["env"]["numpy"]
    r["m_env_scipy"] = man["env"]["scipy"]
    r["m_env_torch"] = man["env"].get("torch")
    r["m_pin_omp"] = man["env"]["pinning"]["OMP_NUM_THREADS"]
    r["m_pin_threads"] = man["env"]["pinning"].get("torch_num_threads")
    r["m_tempo_total_s"] = man["timing"]["tempo_total_s"]
    r["m_tempo_fit_s"] = man["timing"]["tempo_fit_surrogate_s"]
    r["m_tempo_busca_s"] = man["timing"]["tempo_busca_s"]
    r["m_tempo_sonda_s"] = man["timing"]["tempo_pred_sonda_s"]
    r["m_tempo_desp_s"] = man["timing"]["tempo_total_despachante_s"]
    fs = man["fit_series"]
    r["m_fit_series_len"] = len(fs)
    r["m_fit_series_all_null"] = all(x["tempo_fit_s"] is None for x in fs)
    r["m_fit_series_nacum_ok"] = all(
        x["n_acumulado"] == n_init + Q * x["iter"] for x in fs)
    r["m_upload_all"] = all(v == "uploaded" for k, v in
                            man["upload_status"].items() if not k.endswith("final.parquet")
                            and not k.endswith("final.manifest.json"))
    r["m_final_absent"] = all(v == "absent" for k, v in man["upload_status"].items()
                              if "final" in k)

    # ───────── ⑥ jsonl ─────────
    r["j_badlines"] = badlines
    r["j_nlinhas"] = len(recs)
    hdr = [x for x in recs if x.get("rec") == "header"]
    dec = [x for x in recs if x.get("rec") == "decision"]
    ftr = [x for x in recs if x.get("rec") == "footer"]
    grd = [x for x in recs if x.get("rec") == "guard"]
    snd = [x for x in recs if x.get("rec") == "sonda"]
    r["j_n_header"] = len(hdr)
    r["j_n_decision"] = len(dec)
    r["j_n_footer"] = len(ftr)
    r["j_n_guard"] = len(grd)
    r["j_n_sonda"] = len(snd)
    r["j_recs_distintos"] = "|".join(sorted({x.get("rec") for x in recs}))
    h = hdr[0]
    r["j_hdr_tem_params"] = "params" in h
    r["j_hdr_tem_sigma_dict"] = "sigma_dict" in h
    r["j_hdr_q"] = h.get("q")
    r["j_hdr_maxfe"] = h.get("maxfe")
    r["j_hdr_D"] = h.get("D")
    r["j_hdr_M"] = h.get("M")
    r["j_hdr_regime"] = h.get("regime")
    r["j_hdr_doe_hash"] = h.get("doe_hash")
    r["j_hdr_versao"] = h.get("versao")
    r["j_sigma_lote"] = (h.get("sigma_dict") or {}).get("lote")
    # footer duplo (runner + despachante)
    r["j_footer_status"] = [f.get("status") for f in ftr]
    f0 = ftr[0]
    r["j_ftr_motivo_parada"] = f0.get("motivo_parada")
    r["j_ftr_fe_final"] = f0.get("fe_final")
    r["j_ftr_cp_init"] = f0.get("cp_init")
    r["j_ftr_cache_hits"] = f0.get("cache_hits")
    r["j_ftr_ngen"] = f0.get("n_geracoes")
    r["j_ftr_q"] = f0.get("q")
    r["j_ftr_tem_termino"] = "termino" in f0 or "termino" in ftr[-1]
    r["j_ftr2_n_retries"] = ftr[-1].get("n_retries")
    r["j_ftr2_stack"] = ftr[-1].get("stack_trace")
    r["j_ftr2_tempo_total_s"] = ftr[-1].get("tempo_total_s")
    # campos do evento de geração
    campos = sorted({k for d in dec for k in d})
    r["j_dec_campos"] = "|".join(campos)
    r["j_dec_tem_n_front1"] = "n_front1" in campos
    r["j_dec_tem_ideal"] = "ideal" in campos
    r["j_dec_tem_nadir"] = ("nadir_pop" in campos) or ("nadir_front1" in campos)
    r["j_dec_tem_f_best"] = "f_best" in campos
    r["j_dec_caminhos"] = "|".join(sorted({d.get("caminho") for d in dec}))
    r["j_dec_motivos_distintos"] = len({d.get("motivo") for d in dec})
    r["j_dec_q_todos_10"] = all(d.get("q") == Q for d in dec)
    ger = np.array([d["geracao"] for d in dec])
    fe_ev = np.array([d["fe"] for d in dec])
    r["j_ger_1_a_K"] = bool(np.array_equal(ger, np.arange(1, K + 1)))
    r["j_fe_formula_ok"] = bool(np.array_equal(fe_ev, n_init + Q * np.arange(1, K + 1)))
    r["j_fe_ultimo"] = int(fe_ev[-1])

    # ───────── ① real ─────────
    r["r_linhas"] = len(real)
    r["r_fe_exato"] = bool(len(real) == maxfe == man["fe_final"] == f0["fe_final"])
    r["r_fe_index_denso"] = bool(
        np.array_equal(np.sort(real["fe_index"].to_numpy()), np.arange(maxfe)))
    r["r_fe_index_ordenado"] = bool(
        np.array_equal(real["fe_index"].to_numpy(), np.arange(maxfe)))
    r["r_solution_id_denso"] = bool(
        np.array_equal(np.sort(real["solution_id"].to_numpy()), np.arange(maxfe)))
    fases = real["fase"].value_counts().to_dict()
    r["r_fases"] = json.dumps(fases, sort_keys=True)
    r["r_n_init"] = int((real["fase"] == "init").sum())
    r["r_n_opt"] = int((real["fase"] == "opt").sum())
    r["r_init_eh_prefixo"] = bool(
        (real["fase"].to_numpy()[:n_init] == "init").all()
        and (real["fase"].to_numpy()[n_init:] == "opt").all())
    xcols = [f"x{i}" for i in range(D)]
    fcols = [f"f{j}" for j in range(M)]
    r["r_dtype_x"] = str(real[xcols[0]].dtype)
    r["r_dtype_f"] = str(real[fcols[0]].dtype)
    X = real[xcols].to_numpy()
    F = real[fcols].to_numpy()
    r["r_nan_x"] = int(np.isnan(X).sum())
    r["r_nan_f"] = int(np.isnan(F).sum())
    r["r_x_dentro_bounds"] = bool(
        (X >= xl.astype(np.float32) - 1e-6).all() and (X <= xu.astype(np.float32) + 1e-6).all())
    # duplicatas exatas de X (dedup D57 / cache-hits)
    r["r_x_duplicados"] = int(len(X) - len(np.unique(X, axis=0)))

    # ───────── U2 · CP-init bit-a-bit vs artefato do DoE ─────────
    doe = pd.read_parquet(REPO / "data" / "doe" / prob / f"doe_{prob}_{SEED}.parquet")
    doe_man = json.loads((REPO / "data" / "doe" / prob /
                          f"doe_{prob}_{SEED}.manifest.json").read_text())
    Xdoe = doe[[c for c in doe.columns if c.startswith("x")]].to_numpy()
    Xinit = X[:n_init]
    r["cp_doe_linhas"] = len(Xdoe)
    r["cp_hash_sidecar"] = doe_man.get("doe_hash") or doe_man.get("hash")
    r["cp_hash_bate"] = bool(r["cp_hash_sidecar"] == man["doe_hash"] == h["doe_hash"])
    d_init = np.abs(Xinit.astype(np.float64) - Xdoe[:n_init].astype(np.float64))
    r["cp_max_absdiff"] = float(d_init.max())
    r["cp_bit_a_bit"] = bool(np.array_equal(Xinit.astype(np.float32),
                                            Xdoe[:n_init].astype(np.float32)))

    # ───────── QUERY-JOIA · recomputo do lote Sobol ─────────
    base = H.seed_base(ALG, SEED)
    r["qj_base"] = base
    seeds_log = np.array([d["seed_sobol"] for d in dec], dtype=np.int64)
    seeds_calc = np.array([H.iteration_seed(base, ALG_ID, g, 0, bits32=True)
                           for g in range(1, K + 1)], dtype=np.int64)
    r["qj_seeds_iguais"] = bool(np.array_equal(seeds_log, seeds_calc))
    r["qj_seeds_distintos"] = int(len(np.unique(seeds_log)))
    r["qj_seed_min"] = int(seeds_log.min())
    r["qj_seed_max"] = int(seeds_log.max())

    max_abs_nat = 0.0
    n_bit = 0
    n_pts = 0
    U_all = np.empty((K * Q, D), dtype=np.float64)
    for g in range(1, K + 1):
        s = int(seeds_calc[g - 1])
        u = sobol_batch01(D, Q, s)
        U_all[(g - 1) * Q:g * Q] = u
        xnat = xl + u * (xu - xl)
        obs = X[n_init + (g - 1) * Q: n_init + g * Q].astype(np.float32)
        exp32 = xnat.astype(np.float32)
        n_bit += int(np.array_equal(obs, exp32))
        max_abs_nat = max(max_abs_nat,
                          float(np.abs(obs.astype(np.float64) - xnat).max()))
        n_pts += Q
        gen_rows.append({
            "problema": prob, "geracao": g, "seed_log": int(seeds_log[g - 1]),
            "seed_calc": s, "seed_ok": bool(seeds_log[g - 1] == s),
            "lote_bit_a_bit": bool(np.array_equal(obs, exp32)),
            "max_absdiff_nat": float(np.abs(obs.astype(np.float64) - xnat).max()),
            "fe_evento": int(fe_ev[g - 1]),
            "n_linhas_lote_real": int(Q),
            "u_min": float(u.min()), "u_max": float(u.max()),
        })
    r["qj_gens_bit_a_bit"] = n_bit
    r["qj_gens_total"] = K
    r["qj_max_absdiff_nativo"] = max_abs_nat
    r["qj_pontos_reproduzidos"] = n_pts

    # lotes distintos entre si (scrambling de Owen vivo)
    U_rounded = np.round(U_all, 12)
    r["sob_pontos_unicos"] = int(len(np.unique(U_rounded, axis=0)))
    prim = U_all[::Q]
    r["sob_primeiro_ponto_unico"] = int(len(np.unique(np.round(prim, 12), axis=0)))
    r["sob_algum_ponto_zero"] = int((np.abs(U_all).sum(axis=1) == 0).sum())

    # ───────── uniformidade / discrepância (fase opt) ─────────
    rng = np.random.default_rng(20260729)
    d_obs = qmc.discrepancy(U_all, method="CD", workers=-1)
    unif = [qmc.discrepancy(rng.random((K * Q, D)), method="CD", workers=-1)
            for _ in range(5)]
    sob_single = qmc.Sobol(d=D, scramble=True, seed=12345).random(K * Q)
    d_sob1 = qmc.discrepancy(sob_single, method="CD", workers=-1)
    lhs = qmc.LatinHypercube(d=D, seed=999).random(K * Q)
    d_lhs = qmc.discrepancy(lhs, method="CD", workers=-1)
    disc_rows.append({
        "problema": prob, "D": D, "n": K * Q,
        "CD_observado": d_obs,
        "CD_uniforme_med": float(np.mean(unif)), "CD_uniforme_std": float(np.std(unif)),
        "CD_sobol_unico": d_sob1, "CD_lhs": d_lhs,
        "razao_obs_unif": d_obs / float(np.mean(unif)),
        "razao_obs_sobolunico": d_obs / d_sob1,
    })
    r["disc_CD_obs"] = d_obs
    r["disc_CD_unif"] = float(np.mean(unif))
    r["disc_CD_sobol1"] = d_sob1
    r["disc_razao_obs_unif"] = d_obs / float(np.mean(unif))

    # KS por dimensão vs U(0,1) + momentos
    ps = []
    for j in range(D):
        st, p = kstest(U_all[:, j], "uniform")
        ps.append(p)
        ks_rows.append({"problema": prob, "dim": j, "ks_stat": float(st),
                        "p": float(p), "media": float(U_all[:, j].mean()),
                        "var": float(U_all[:, j].var())})
    ps = np.array(ps)
    r["ks_p_min"] = float(ps.min())
    r["ks_n_rej_005"] = int((ps < 0.05).sum())
    r["ks_n_rej_bonf"] = int((ps < 0.05 / D).sum())
    r["ks_media_global"] = float(U_all.mean())
    r["ks_var_global"] = float(U_all.var())

    # ───────── ② pop ─────────
    r["p_linhas"] = len(pop)
    gsizes = pop.groupby("geracao").size()
    r["p_gen_min"] = int(gsizes.index.min())
    r["p_gen_max"] = int(gsizes.index.max())
    r["p_n_geracoes"] = int(len(gsizes))
    esperado = {0: n_init}
    esperado.update({g: n_init + Q * g for g in range(1, K + 1)})
    r["p_arquivo_cumulativo_ok"] = bool(
        all(int(gsizes.get(g, -1)) == v for g, v in esperado.items()))
    r["p_soma_esperada"] = int(sum(esperado.values()))
    r["p_soma_ok"] = bool(len(pop) == sum(esperado.values()))
    ids_g = pop[pop["geracao"] == K]["solution_id"].to_numpy()
    r["p_ultima_ger_eh_dataset"] = bool(
        np.array_equal(np.sort(ids_g), np.arange(maxfe)))

    # ───────── ③ surrogate ─────────
    r["s_linhas"] = len(surr)
    r["s_colunas"] = len(surr.columns)
    r["s_tem_schema_completo"] = bool(
        {"mu_0", "sigma_0", "modelo_flag", "fe_treino_max", "regime"} <= set(surr.columns))

    # ───────── ④ timing ─────────
    r["t_linhas"] = len(tim)
    r["t_fit_null_frac"] = float(tim["tempo_fit_s"].isna().mean())
    r["t_sonda_zero_frac"] = float((tim["tempo_pred_sonda_s"].fillna(-1) == 0).mean())
    r["t_busca_le_gen"] = int((tim["tempo_busca_s"] <= tim["tempo_geracao_s"] + 1e-9).sum())
    r["t_n_acum_ok"] = bool(np.array_equal(
        tim.sort_values("geracao")["n_acumulado"].to_numpy(),
        n_init + Q * np.arange(1, K + 1)))
    r["t_ger_1_a_K"] = bool(np.array_equal(
        np.sort(tim["geracao"].to_numpy()), np.arange(1, K + 1)))
    r["t_soma_busca_s"] = float(tim["tempo_busca_s"].sum())
    r["t_soma_gen_s"] = float(tim["tempo_geracao_s"].sum())
    r["t_max_gen_s"] = float(tim["tempo_geracao_s"].max())

    # ───────── U9 · reconciliação de guardas ─────────
    r["u9_cache_hits_ok"] = bool(
        man.get("cache_hits") == f0.get("cache_hits") == 0 and len(grd) == 0)

    # ───────── f_best monotônico (running ideal) ─────────
    fb = np.array([d["f_best"] for d in dec], dtype=np.float64)
    r["fb_monotonico"] = bool((np.diff(fb, axis=0) <= 1e-12).all())
    Fall = F.astype(np.float64)
    fb_calc = np.array([Fall[:n_init + Q * g].min(axis=0) for g in range(1, K + 1)])
    r["fb_max_absdiff_vs_camada1"] = float(np.abs(fb - fb_calc).max())
    r["fb_igual_min_arquivo"] = bool(np.abs(fb - fb_calc).max() < 1e-5)

    rows.append(r)
    print(f"[ok] {prob}: joia {n_bit}/{K} lotes bit-a-bit · CD {d_obs:.3e} "
          f"(unif {np.mean(unif):.3e}) · seeds {r['qj_seeds_iguais']}", flush=True)

df = pd.DataFrame(rows)
df.to_csv(OUT / "bateria_celulas.csv", index=False)
pd.DataFrame(gen_rows).to_csv(OUT / "bateria_geracoes.csv", index=False)
pd.DataFrame(disc_rows).to_csv(OUT / "discrepancia.csv", index=False)
pd.DataFrame(ks_rows).to_csv(OUT / "ks_uniformidade.csv", index=False)
print("\n=== AGREGADOS ===")
print(df[["problema", "D", "r_fe_exato", "cp_bit_a_bit", "qj_seeds_iguais",
          "qj_gens_bit_a_bit", "ks_n_rej_bonf", "disc_razao_obs_unif",
          "p_arquivo_cumulativo_ok", "m_tem_params", "j_dec_tem_n_front1"]].to_string())
