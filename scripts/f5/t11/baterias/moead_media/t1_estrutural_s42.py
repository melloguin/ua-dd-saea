"""T11/moead_media · bateria T1 — re-medicao estrutural das 45 celulas da s42.

READ-ONLY. Nao escreve nada em resultados_experimentos/ nem data/.
Saida: t1_estrutural_s42.csv na propria pasta.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead_media"
OUT = os.path.dirname(os.path.abspath(__file__))
DS_DIR = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets"
SONDA_DIR = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda"


def celulas():
    for d in sorted(glob.glob(os.path.join(RAIZ, "*", "42"))):
        label = os.path.basename(os.path.dirname(d))
        man = glob.glob(os.path.join(d, "*_42.manifest.json"))
        man = [m for m in man if "__final" not in m]
        yield label, d, man[0]


def lhs_score(X, lo, hi):
    """Fracao de estratos ocupados por dimensao (LHS perfeito => 1.0).

    Um LHS de N pontos poe exatamente 1 ponto em cada um dos N estratos de
    cada dimensao. Amostra qualquer (uniforme) ocupa ~1-1/e = 63,2%.
    """
    N, D = X.shape
    occ = []
    for j in range(D):
        u = (X[:, j] - lo[j]) / (hi[j] - lo[j])
        b = np.clip((u * N).astype(int), 0, N - 1)
        occ.append(len(np.unique(b)) / float(N))
    return float(np.mean(occ)), float(np.min(occ))


linhas = []
for label, d, manp in celulas():
    m = json.load(open(manp))
    pref = manp[:-len(".manifest.json")]
    r = {"label": label, "problema": m["problema"]}

    # ---- (5) manifesto
    r["schema_version"] = m.get("schema_version")
    r["tem_params"] = "params" in m
    r["tem_campanha_id"] = bool(m.get("campanha_id"))
    r["repo_hash"] = m.get("repo_hash")
    r["status"] = m.get("status")
    r["motivo_parada"] = m.get("motivo_parada")
    r["n_geracoes"] = m.get("n_geracoes")
    r["maxfe"] = m.get("maxfe")
    r["fe_final"] = m.get("fe_final")
    r["cache_hits"] = m.get("cache_hits")
    r["n_retries"] = m.get("n_retries")
    r["fallback"] = m.get("fallback_ativado")
    r["stack_trace"] = m.get("stack_trace")
    r["env_exec"] = os.path.basename(os.path.dirname(os.path.dirname(
        m["env"]["executable"])))
    t = m.get("timing", {})
    r["t_total"] = t.get("tempo_total_s")
    r["t_fit"] = t.get("tempo_fit_surrogate_s")
    r["t_busca"] = t.get("tempo_busca_s")
    r["t_sonda"] = t.get("tempo_pred_sonda_s")
    r["tempo_aval_real_s"] = t.get("tempo_aval_real_s")
    r["n_fit_series"] = len(m.get("fit_series") or [])
    sd = m.get("sigma_dict") or {}
    r["n_sigma_dict"] = len(sd)
    r["tem_granularidade3"] = "granularidade_③" in sd
    sn = m.get("sonda") or {}
    r["sonda_S"] = sn.get("S")
    r["sonda_nblocos"] = sn.get("n_blocos")
    cp = m.get("cp_init_offline") or {}
    r["cp_x_hash"] = cp.get("x_hash")
    r["doe_hash"] = m.get("doe_hash")
    r["doe_eq_cp"] = (m.get("doe_hash") == cp.get("x_hash"))
    r["tier"] = m.get("tier")
    r["dist"] = m.get("dist")

    # ---- (1) catalogo real
    t1 = pq.read_table(pref + "__real.parquet")
    n1 = t1.num_rows
    fase = pd.Series(t1.column("fase").to_pylist())
    fei = np.asarray(t1.column("fe_index").to_pylist())
    sid = np.asarray(t1.column("solution_id").to_pylist())
    r["n1"] = n1
    r["n1_init_frac"] = float((fase == "init").mean())
    r["fe_index_denso"] = bool(np.array_equal(fei, np.arange(n1)))
    r["sid_denso"] = bool(np.array_equal(sid, np.arange(n1)))
    r["n1_eq_maxfe"] = (n1 == m.get("maxfe") == m.get("fe_final"))
    Dcols = [c for c in t1.schema.names if c.startswith("x")]
    Fcols = [c for c in t1.schema.names if c.startswith("f") and c != "fase"]
    r["D"] = len(Dcols)
    r["M"] = len(Fcols)
    X1 = np.column_stack([np.asarray(t1.column(c).to_pylist()) for c in Dcols])
    F1 = np.column_stack([np.asarray(t1.column(c).to_pylist()) for c in Fcols])

    # ---- (2) pop
    r["n2"] = pq.read_metadata(pref + "__pop.parquet").num_rows

    # ---- (4) timing
    t4 = pq.read_table(pref + "__timing.parquet").to_pandas()
    r["n4"] = len(t4)
    r["t4_n_acumulado"] = int(t4["n_acumulado"].iloc[0])
    r["t4_inv_delta"] = float(abs(t4["tempo_fit_s"].iloc[0]
                                  + t4["tempo_busca_s"].iloc[0]
                                  - t4["tempo_geracao_s"].iloc[0]))
    r["t4_sonda_pos"] = bool(t4["tempo_pred_sonda_s"].iloc[0] > 0)

    # ---- (3) surrogate — projecao de colunas
    sch = pq.read_schema(pref + "__surrogate.parquet")
    mus = [c for c in sch.names if c.startswith("mu_")]
    sgs = [c for c in sch.names if c.startswith("sigma_")]
    xs = [c for c in sch.names if c.startswith("x") and c[1:].isdigit()]
    cols = ["regime", "geracao", "fe_treino_max", "real_solution_id",
            "pred_tipo", "pred_classe", "pred_score", "pred_confianca",
            "modelo_flag", "espaco_modelo", "transf_tipo", "transf_params"]
    t3 = pq.read_table(pref + "__surrogate.parquet",
                       columns=cols + mus + sgs + xs).to_pandas()
    r["n3"] = len(t3)
    off = t3[t3.regime == "offline"]
    snd = t3[t3.regime == "sonda"]
    r["n3_offline"] = len(off)
    r["n3_sonda"] = len(snd)
    r["n3_regimes"] = "|".join(sorted(t3.regime.unique()))
    r["sigma_nan_frac"] = float(t3[sgs].isna().all(axis=1).mean())
    r["mu_nan_frac"] = float(t3[mus].isna().any(axis=1).mean())
    r["fe_treino_max_uniq"] = int(t3.fe_treino_max.nunique())
    r["fe_treino_max_val"] = int(t3.fe_treino_max.iloc[0])
    r["fe_treino_max_eq_n1m1"] = (int(t3.fe_treino_max.iloc[0]) == n1 - 1)
    r["rsid_null_frac"] = float(t3.real_solution_id.isna().mean())
    r["sonda_geracao_nan"] = float(snd.geracao.isna().mean())
    r["pred_tipo_uniq"] = "|".join(sorted(t3.pred_tipo.dropna().unique()))
    r["pred_classe_null"] = float(t3.pred_classe.isna().mean())
    r["espaco_modelo_uniq"] = "|".join(sorted(t3.espaco_modelo.dropna().unique()))
    r["transf_null"] = float(t3.transf_tipo.isna().mean())
    r["modelo_flag_uniq"] = "|".join(sorted(t3.modelo_flag.dropna().unique()))

    # populacao por geracao
    g = off.geracao.dropna().astype(int)
    vc = g.value_counts()
    r["pop_uniq"] = int(vc.nunique())
    r["pop_N"] = int(vc.iloc[0])
    r["n_ger3"] = int(g.max())
    r["ger_densa"] = bool(set(g.unique()) == set(range(1, int(g.max()) + 1)))
    r["n3off_eq_NxG"] = (len(off) == r["pop_N"] * r["n_ger3"])
    # C3 refinado (granularidade_③): passos de SELECAO = n_ger-1
    r["aval_selecao"] = (r["n_ger3"] - 1) * r["pop_N"]
    r["aval_total"] = r["n_ger3"] * r["pop_N"]

    # ---- NOVO: teste de LHS na geracao 1 (a declaracao granularidade_③)
    lo = X1.min(axis=0)
    hi = X1.max(axis=0)
    try:
        from src import standalone_harness as H  # bounds reais
        bl, bu = H._bounds(m["problema"])
        lo, hi = np.asarray(bl, float), np.asarray(bu, float)
    except Exception:
        pass
    g1 = off[off.geracao == 1]
    gl = off[off.geracao == r["n_ger3"]]
    Xg1 = g1[xs].to_numpy(dtype=float)
    Xgl = gl[xs].to_numpy(dtype=float)
    r["lhs_g1_medio"], r["lhs_g1_min"] = lhs_score(Xg1, lo, hi)
    r["lhs_gfinal_medio"], r["lhs_gfinal_min"] = lhs_score(Xgl, lo, hi)
    r["g1_dentro_bounds"] = float(((Xg1 >= lo - 1e-6) & (Xg1 <= hi + 1e-6)).all(axis=1).mean())
    r["gfinal_dentro_bounds"] = float(((Xgl >= lo - 1e-6) & (Xgl <= hi + 1e-6)).all(axis=1).mean())

    # ---- (7) final
    t7 = pq.read_table(pref + "__final.parquet").to_pandas()
    r["n7"] = len(t7)
    f7 = t7[[c for c in t7.columns if c.startswith("f") and c[1:].isdigit()]].to_numpy(float)
    # recomputo ND (nao-dominancia estrita, sobre a vista float32 persistida)
    nd = np.ones(len(f7), bool)
    for i in range(len(f7)):
        if not nd[i]:
            continue
        dom = np.all(f7 <= f7[i], axis=1) & np.any(f7 < f7[i], axis=1)
        if dom.any():
            nd[i] = False
    r["nd_recomputo_ok"] = bool(np.array_equal(nd, t7.nd_pos_real.to_numpy(bool)))
    r["n_nd"] = int(t7.nd_pos_real.sum())
    r["razao_fantasia"] = float(t7.nd_pos_real.mean())
    r["origem_linha_densa"] = bool(np.array_equal(
        t7.origem_linha.to_numpy(), np.arange(len(t7))))
    r["origem_geracao_uniq"] = int(t7.origem_geracao.nunique())
    r["origem_geracao_val"] = int(t7.origem_geracao.iloc[0])
    r["origem_sid_null"] = float(t7.origem_solution_id.isna().mean())
    x7 = t7[[c for c in t7.columns if c.startswith("x") and c[1:].isdigit()]].to_numpy(float)
    r["link7_dX"] = float(np.abs(x7 - Xgl[t7.origem_linha.to_numpy()]).max())
    r["n7_eq_popN"] = (len(t7) == r["pop_N"])

    # ---- (6) jsonl
    recs = {}
    keys_dec = None
    n_ds_membros_max = 0
    caminhos = set()
    motivos = set()
    p_wrong = 0
    fe_set = set()
    footers = []
    with open(pref + ".jsonl") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                recs["MALFORMADA"] = recs.get("MALFORMADA", 0) + 1
                continue
            k = o.get("rec", "?")
            recs[k] = recs.get(k, 0) + 1
            if k == "decision":
                if keys_dec is None:
                    keys_dec = set(o.keys())
                n_ds_membros_max = max(n_ds_membros_max, o.get("n_ds_membros", 0) or 0)
                caminhos.add(o.get("caminho"))
                motivos.add(o.get("motivo"))
                fe_set.add(o.get("fe"))
                if "p_wrong_stats" in o:
                    p_wrong += 1
            if k == "footer":
                footers.append(o)
    r["j_decision"] = recs.get("decision", 0)
    r["j_header"] = recs.get("header", 0)
    r["j_sonda"] = recs.get("sonda", 0)
    r["j_footer"] = recs.get("footer", 0)
    r["j_guard"] = recs.get("guard", 0)
    r["j_malformada"] = recs.get("MALFORMADA", 0)
    r["j_recs"] = "|".join(sorted(recs))
    r["dec_keys"] = "|".join(sorted(keys_dec or []))
    r["n_ds_membros_max"] = n_ds_membros_max
    r["caminho"] = "|".join(sorted(x for x in caminhos if x))
    r["p_wrong_no_6"] = p_wrong
    r["fe_dec_uniq"] = len(fe_set)
    r["fe_dec_val"] = list(fe_set)[0] if len(fe_set) == 1 else None
    r["dec_eq_nger"] = (r["j_decision"] == r["n_ger3"])
    r["footer_status"] = "|".join(sorted(str(f.get("status")) for f in footers))

    linhas.append(r)
    print("[ok] %-28s n3=%-8d ger=%-5d N=%-4d" % (label, r["n3"], r["n_ger3"], r["pop_N"]))
    sys.stdout.flush()

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "t1_estrutural_s42.csv"), index=False)
print("\n=== %d celulas ===" % len(df))
