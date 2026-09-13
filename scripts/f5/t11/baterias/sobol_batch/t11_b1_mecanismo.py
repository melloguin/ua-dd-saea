"""T11 · sobol_batch · BATERIA 1 — re-medicao do MECANISMO na s42 (READ-ONLY).

Re-mede, do zero, os invariantes que a F5 mediu (o handoff T11 manda desconfiar
de numeros herdados). Nada aqui escreve fora de f5/t11/baterias/sobol_batch/.
"""
import json, os, sys, hashlib
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
DATA = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/sobol_batch"
OUT = os.path.join(REPO, "f5/t11/baterias/sobol_batch")
sys.path.insert(0, REPO)
os.chdir(REPO)

from src import standalone_harness as H          # noqa: E402
from src import problems as _problems            # noqa: E402
from src.budget import maxfe_por_exp             # noqa: E402
from scipy.stats import qmc, kstest              # noqa: E402
import scipy, warnings                           # noqa: E402

PROBS = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]
rows, gen_rows, ks_rows = [], [], []
print("numpy", np.__version__, "scipy", scipy.__version__)

for p in PROBS:
    d = f"{DATA}/q10_{p}/42"
    pre = f"{d}/exp_batch_sobol_batch_{p}_42"
    man = json.load(open(pre + ".manifest.json"))
    L = [json.loads(l) for l in open(pre + ".jsonl")]
    real = pd.read_parquet(pre + "__real.parquet")
    pop = pd.read_parquet(pre + "__pop.parquet")
    surr = pd.read_parquet(pre + "__surrogate.parquet")
    tim = pd.read_parquet(pre + "__timing.parquet")
    D = int(man["env"] and 0) or None
    xc = [c for c in real.columns if c.startswith("x") and c[1:].isdigit()]
    fc = [c for c in real.columns if c.startswith("f") and c[1:].isdigit()]
    D = len(xc); M = len(fc)
    r = {"problema": p, "D": D, "M": M}

    # ---------- U1: orcamento ----------
    maxfe = maxfe_por_exp("batch", D, 10)
    r["maxfe_formula"] = maxfe
    r["maxfe_manifesto"] = man["maxfe"]
    r["fe_final"] = man["fe_final"]
    r["n1_linhas"] = len(real)
    r["U1_orcamento_ok"] = (maxfe == man["maxfe"] == man["fe_final"] == len(real))
    r["U1_fe_index_denso"] = bool((real["fe_index"].values ==
                                   np.arange(len(real))).all())
    r["U1_solution_id_denso"] = bool((real["solution_id"].values ==
                                      np.arange(len(real))).all())
    n_init = 11 * D - 1
    r["n_init"] = n_init
    fase = real["fase"].values
    r["U1_init_prefixo"] = bool((fase[:n_init] == "init").all() and
                                (fase[n_init:] == "opt").all())

    # ---------- U2: DoE bit-a-bit ----------
    doe = H.load_doe(p, 42, data_root="data")
    Xd = np.asarray(doe["X"], dtype=np.float64)
    X1 = real[xc].values[:n_init].astype(np.float64)
    r["U2_doe_bitaBit_f32"] = bool(np.array_equal(
        Xd.astype(np.float32), X1.astype(np.float32)))
    r["U2_doe_dmax_f64"] = float(np.abs(Xd - X1).max())
    hdr = [x for x in L if x.get("rec") == "header"][0]
    r["U2_doehash_igual"] = (man["doe_hash"] == hdr.get("doe_hash") ==
                             doe["doe_hash"])

    # ---------- QUERY-JOIA: recomputo dos lotes ----------
    dec = [x for x in L if x.get("rec") == "decision"]
    r["n_decision"] = len(dec)
    xl, xu = H._bounds(p)
    base = H.seed_base("sobol_batch", 42)
    Xopt = real[xc].values[n_init:].astype(np.float64)
    ok_lote = 0; dmax = 0.0; ok_seed = 0
    seeds = []
    for i, ev in enumerate(dec):
        g = int(ev["geracao"])
        s_exp = H.iteration_seed(base, 22, g, 0, bits32=True)
        ok_seed += int(int(ev["seed_sobol"]) == int(s_exp))
        seeds.append(int(ev["seed_sobol"]))
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*balance properties.*")
            u = np.asarray(qmc.Sobol(d=D, scramble=True,
                                     seed=int(s_exp)).random(10), dtype=np.float64)
        lote = xl + u * (xu - xl)
        obs = Xopt[10 * i: 10 * (i + 1)]
        eq = np.array_equal(lote.astype(np.float32), obs.astype(np.float32))
        ok_lote += int(eq)
        dd = float(np.abs(lote - obs).max())
        dmax = max(dmax, dd)
        gen_rows.append({"problema": p, "geracao": g, "seed_ok":
                         int(ev["seed_sobol"]) == int(s_exp),
                         "lote_bit_igual_f32": eq, "dmax_f64": dd,
                         "fe": ev["fe"], "n_front1_presente": "n_front1" in ev})
    r["JOIA_lotes_ok"] = ok_lote
    r["JOIA_dmax_f64"] = dmax
    r["seeds_ok"] = ok_seed
    r["seeds_distintos"] = len(set(seeds))
    r["seed_g1"] = seeds[0]

    # ---------- scrambling vivo ----------
    Uop = np.round(Xopt, 12)
    r["S6_pontos_distintos"] = len(set(map(tuple, Uop.tolist())))
    r["S6_bounds_ok"] = bool((real[xc].values >= xl - 1e-9).all() and
                             (real[xc].values <= xu + 1e-9).all())

    # ---------- KS uniformidade (fase opt) ----------
    U01 = (Xopt - xl) / (xu - xl)
    rej = 0; pmin = 1.0
    for j in range(D):
        st = kstest(U01[:, j], "uniform")
        rej += int(st.pvalue < 0.05); pmin = min(pmin, float(st.pvalue))
        ks_rows.append({"problema": p, "coord": j, "p": float(st.pvalue)})
    r["KS_rejeicoes"] = rej; r["KS_pmin"] = pmin
    r["KS_media"] = float(U01.mean()); r["KS_var"] = float(U01.var())

    # ---------- oraculo ----------
    prob = H._instantiate(p)
    Fr = _problems.evaluate_problem(prob, real[xc].values.astype(np.float64))
    Fo = real[fc].values.astype(np.float64)
    den = np.maximum(np.abs(Fo), 1e-12)
    rel = np.abs(Fr - Fo) / den
    r["ORACULO_rel_mediana"] = float(np.median(rel))
    r["ORACULO_rel_max"] = float(rel.max())
    r["ORACULO_frac_le_1e6"] = float((rel <= 1e-6).mean())

    # ---------- q=10 ponta a ponta ----------
    r["q_manifesto"] = man.get("q"); r["q_header"] = hdr.get("q")
    r["q_eventos_ok"] = sum(1 for e in dec if e.get("q") == 10)
    r["ger_fe_ok"] = sum(1 for e in dec
                         if int(e["fe"]) == n_init + 10 * int(e["geracao"]))
    r["n_geracoes"] = man["n_geracoes"]

    # ---------- (2) populacao ----------
    gsz = pop.groupby("geracao").size()
    r["POP_n_grupos"] = int(gsz.shape[0])
    r["POP_gmin"] = int(gsz.index.min()); r["POP_gmax"] = int(gsz.index.max())
    r["POP_tam_ok"] = int(sum(1 for g, n in gsz.items()
                              if n == n_init + 10 * int(g)))
    r["POP_linhas"] = len(pop)

    # ---------- (3) vazia ----------
    r["SURR_linhas"] = len(surr); r["SURR_colunas"] = surr.shape[1]

    # ---------- sonda ----------
    r["SONDA_status"] = (man.get("sonda") or {}).get("status")
    r["SONDA_recs"] = sum(1 for x in L if x.get("rec") == "sonda")

    # ---------- (4) timing ----------
    r["TIM_linhas"] = len(tim)
    r["TIM_fit_null"] = int(tim["tempo_fit_s"].isna().sum())
    r["TIM_inv1_ok"] = int((tim["tempo_busca_s"] <= tim["tempo_geracao_s"]).sum())
    r["TIM_soma_ger"] = float(tim["tempo_geracao_s"].sum())
    r["TIM_soma_busca"] = float(tim["tempo_busca_s"].sum())
    r["TIM_proxy_aval"] = float((tim["tempo_geracao_s"] -
                                 tim["tempo_busca_s"]).sum())

    # ---------- guardas / dedup ----------
    r["GUARD_eventos"] = sum(1 for x in L if x.get("rec") == "guard")
    r["CACHE_manifesto"] = man.get("cache_hits")
    foot = [x for x in L if x.get("rec") == "footer"]
    r["N_footers"] = len(foot)
    r["CACHE_footer"] = foot[0].get("cache_hits") if foot else None
    Xall = real[xc].values.astype(np.float64)
    r["DEDUP_x_unicos"] = len(set(map(lambda v: v.tobytes(),
                                      np.ascontiguousarray(Xall))))

    # ---------- termino / T11 fields (PRE-T11) ----------
    r["motivo_parada"] = man.get("motivo_parada")
    r["status"] = man.get("status")
    r["T11_params_no_5"] = "params" in man
    r["T11_campanha_id"] = "campanha_id" in man
    r["T11_repo_hash"] = "repo_hash" in man
    r["T11_schema_version"] = man.get("schema_version")
    r["T11_n_front1_eventos"] = sum(1 for e in dec if "n_front1" in e)
    r["T11_tempo_aval_real_s"] = (man.get("timing") or {}).get("tempo_aval_real_s")
    r["timing_total_s"] = (man.get("timing") or {}).get("tempo_total_s")
    r["timing_busca_s"] = (man.get("timing") or {}).get("tempo_busca_s")
    r["T11_checkpoint_recs"] = sum(1 for x in L if x.get("rec") == "checkpoint")
    r["EV_chaves"] = ",".join(sorted(dec[0].keys()))
    r["JSONL_linhas"] = len(L)
    r["sigma_dict_chaves"] = ",".join(sorted((man.get("sigma_dict") or {}).keys()))
    rows.append(r)
    print(p, "ok")

pd.DataFrame(rows).to_csv(f"{OUT}/b1_celulas.csv", index=False)
pd.DataFrame(gen_rows).to_csv(f"{OUT}/b1_geracoes.csv", index=False)
pd.DataFrame(ks_rows).to_csv(f"{OUT}/b1_ks.csv", index=False)
df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
for c in df.columns:
    print(f"{c:26s}", list(df[c]))
