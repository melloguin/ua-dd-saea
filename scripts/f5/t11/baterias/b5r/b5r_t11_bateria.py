"""[F5-T11/b5r] Re-medicao da s42 (45 celulas) + auditoria da instrumentacao T11.

READ-ONLY: le `resultados_experimentos/b5r/**` e `data/sonda|datasets`; escreve
SO em f5/t11/baterias/b5r/. Nao chama experiments.py, nao usa AuditLogger.
"""
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5r"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5", "t11", "baterias", "b5r")

T11_MANIF = ["campanha_id", "repo_hash", "params"]
T11_SIGMA = ["granularidade_③"]
T11_DEC = ["p_wrong_stats", "n_substituicoes", "flag_vetores_degenerados"]


def par(n):
    return n + (n % 2)


def lhs_perfeito(X):
    """Cada dimensao com 1 ponto por estrato de largura 1/n (X em [0,1])."""
    n = X.shape[0]
    ok = 0
    for j in range(X.shape[1]):
        b = np.floor(X[:, j] * n).astype(int)
        b = np.clip(b, 0, n - 1)
        ok += int(len(np.unique(b)) == n)
    return ok, X.shape[1]


rows = []
for mani in sorted(glob.glob(os.path.join(ROOT, "*", "42", "*.manifest.json"))):
    if mani.endswith("__final.manifest.json"):
        continue
    base = mani[: -len(".manifest.json")]
    label = os.path.basename(os.path.dirname(os.path.dirname(mani)))
    m = json.load(open(mani))
    r = {"label": label, "status": m.get("status"),
         "motivo": m.get("motivo_parada"), "n_retries": m.get("n_retries"),
         "fallback": m.get("fallback_ativado"), "maxfe": m.get("maxfe"),
         "fe_final": m.get("fe_final"), "n_ger_manif": m.get("n_geracoes"),
         "schema_version": m.get("schema_version"),
         "tempo_aval_real_s": (m.get("timing") or {}).get("tempo_aval_real_s"),
         "tempo_total_s": (m.get("timing") or {}).get("tempo_total_s"),
         "n_fit_series": len(m.get("fit_series") or [])}
    sd = m.get("sigma_dict") or {}
    for k in T11_MANIF:
        r["T11_manif_" + k] = k in m and m.get(k) is not None
    for k in T11_SIGMA:
        r["T11_sigma_granularidade"] = k in sd
    r["n_chaves_sigma"] = len(sd)
    r["doe_ok"] = (m.get("doe_hash") ==
                   (m.get("cp_init_offline") or {}).get("x_hash"))
    r["sonda_nblocos"] = (m.get("sonda") or {}).get("n_blocos")
    r["sonda_S"] = (m.get("sonda") or {}).get("S")

    # ---------- (1) camada 1 ----------
    d1 = pq.read_table(base + "__real.parquet").to_pandas()
    xc = [c for c in d1.columns if c.startswith("x")]
    fc = [c for c in d1.columns if c.startswith("f") and c[1:].isdigit()]
    D, M = len(xc), len(fc)
    r["D"], r["M"] = D, M
    r["n1"] = len(d1)
    r["c1_eq_maxfe"] = int(len(d1)) == int(m.get("maxfe"))
    r["c1_todo_init"] = bool((d1["fase"] == "init").all())
    r["c1_fe_denso"] = bool((np.sort(d1["fe_index"].values) ==
                             np.arange(len(d1))).all())

    # ---------- (2) camada 2 ----------
    r["n2"] = pq.read_table(base + "__pop.parquet").num_rows

    # ---------- (4) timing ----------
    d4 = pq.read_table(base + "__timing.parquet").to_pandas()
    r["n4"] = len(d4)
    r["t_fit"] = float(d4["tempo_fit_s"].iloc[0])
    r["t_busca"] = float(d4["tempo_busca_s"].iloc[0])
    r["t_sonda"] = float(d4["tempo_pred_sonda_s"].iloc[0])
    r["t_ger"] = float(d4["tempo_geracao_s"].iloc[0])
    r["U7_ok"] = bool(r["t_fit"] + r["t_busca"] <= r["t_ger"] + 1e-4)
    r["n_acum_eq_N"] = int(d4["n_acumulado"].iloc[0]) == int(m.get("maxfe"))

    # ---------- (3) surrogate ----------
    d3 = pq.read_table(base + "__surrogate.parquet").to_pandas()
    r["n3"] = len(d3)
    sb = d3[d3["regime"] == "offline"]
    sn = d3[d3["regime"] == "sonda"]
    r["n3_busca"], r["n3_sonda"] = len(sb), len(sn)
    r["regimes"] = "|".join(sorted(d3["regime"].unique()))
    r["sonda_ger_null"] = bool(sn["geracao"].isna().all())
    r["rsid_null_share"] = float(d3["real_solution_id"].isna().mean())
    r["fe_treino_unico"] = int(d3["fe_treino_max"].nunique())
    r["fe_treino_val"] = int(d3["fe_treino_max"].iloc[0])
    r["fe_treino_eq_N1"] = r["fe_treino_val"] == int(m.get("maxfe")) - 1

    muc = ["mu_%d" % j for j in range(M)]
    sgc = ["sigma_%d" % j for j in range(M)]
    SG = sn[sgc].values
    r["sigma_max_sonda"] = float(np.nanmax(SG))
    r["sigma_zero_share_max"] = float(np.max((SG == 0.0).mean(axis=0)))
    r["sigma_teto_share_max"] = float(
        np.max((np.abs(SG - np.sqrt(1e3)) < 1e-6).mean(axis=0)))
    r["sigma_nan"] = int(np.isnan(SG).sum())
    MU = sn[muc].values
    r["mu_const_objs"] = int(sum(np.ptp(MU[:, j]) == 0.0 for j in range(M)))

    # ---------- geracoes da busca ----------
    sb = sb.copy()
    sb["g"] = sb["geracao"].astype("float64").astype(int)
    gs = np.sort(sb["g"].unique())
    tam = sb.groupby("g").size()
    r["n_ger_c3"] = int(len(gs))
    r["ger_eq_manif"] = int(len(gs)) == int(m.get("n_ger_manif") or -1)
    N_RV = 50 if M == 2 else 105
    r["N_RV"] = N_RV
    r["pop1_eq_NRV"] = int(tam.loc[gs[0]]) == N_RV
    r["pop_max"] = int(tam.max())
    r["pop_teto_ok"] = int(tam.max()) <= N_RV
    r["pop_final"] = int(tam.loc[gs[-1]])

    # A13/A30: LHS na geracao 1
    xl = np.array([float(d1[c].min()) for c in xc])
    xu = np.array([float(d1[c].max()) for c in xc])
    # bounds reais do problema: usa o dataset como proxy so p/ normalizar;
    # o teste de estrato usa o hipercubo do proprio ponto-a-ponto
    G1 = sb[sb["g"] == gs[0]][xc].values.astype(np.float64)
    rng = np.where((xu - xl) == 0, 1.0, (xu - xl))
    U1 = (G1 - xl) / rng
    ok1, tot1 = lhs_perfeito(np.clip(U1, 0, 1 - 1e-12))
    r["lhs_ok_g1"], r["lhs_dims"] = ok1, tot1
    if len(gs) > 1:
        G2 = sb[sb["g"] == gs[1]][xc].values.astype(np.float64)
        ok2, _ = lhs_perfeito(np.clip((G2 - xl) / rng, 0, 1 - 1e-12))
        r["lhs_ok_g2"] = ok2
    else:
        r["lhs_ok_g2"] = -1

    # A16: contabilidade dos 40.000
    fe = N_RV
    fe_antes = None
    for g in gs[:-1]:
        fe_antes = fe
        fe += par(int(tam.loc[g]))
    r["FE_antes"] = int(fe_antes) if fe_antes is not None else -1
    r["FE_final"] = int(fe)
    r["FE40k_ok"] = bool(fe_antes is not None and fe_antes <= 40000 < fe)
    r["overshoot"] = int(fe - 40000)
    r["overshoot_le_prole"] = bool(r["overshoot"] <= par(int(tam.loc[gs[-2]]))
                                   if len(gs) > 1 else False)

    # A20/A13: intersecao X busca x dataset
    hx = set(hashlib.blake2b(v.tobytes(), digest_size=8).digest()
             for v in np.ascontiguousarray(d1[xc].values.astype(np.float32)))
    hb = set(hashlib.blake2b(v.tobytes(), digest_size=8).digest()
             for v in np.ascontiguousarray(sb[xc].values.astype(np.float32)))
    r["inter_busca_dataset"] = len(hx & hb)

    # A11: sigma(descartado) vs sigma(mantido) nas transicoes pai->filho
    nsup, ntot, sd_, sm_ = 0, 0, [], []
    prev_key, prev_sig = None, None
    for g in gs:
        blk = sb[sb["g"] == g]
        X32 = np.ascontiguousarray(blk[xc].values.astype(np.float32))
        key = [hashlib.blake2b(v.tobytes(), digest_size=8).digest() for v in X32]
        sig = np.nanmean(blk[sgc].values, axis=1)
        if prev_key is not None:
            cur = set(key)
            keep = np.array([k in cur for k in prev_key])
            if keep.any() and (~keep).any():
                a, b = np.nanmean(prev_sig[~keep]), np.nanmean(prev_sig[keep])
                if np.isfinite(a) and np.isfinite(b):
                    ntot += 1
                    nsup += int(a > b)
                    sd_.append(a)
                    sm_.append(b)
        prev_key, prev_sig = key, sig
    r["sel_n_trans"] = ntot
    r["sel_n_sigma_maior_desc"] = nsup
    r["sel_frac"] = (nsup / ntot) if ntot else np.nan
    r["sel_razao"] = (float(np.mean(sd_) / np.mean(sm_))
                      if ntot and np.mean(sm_) > 0 else np.nan)
    # deriva do sigma da populacao (primeiros 10% x ultimos 10%)
    k = max(1, len(gs) // 10)
    s_ini = np.nanmean([np.nanmean(sb[sb["g"] == g][sgc].values) for g in gs[:k]])
    s_fim = np.nanmean([np.nanmean(sb[sb["g"] == g][sgc].values) for g in gs[-k:]])
    r["sigma_deriva"] = float(s_fim / s_ini) if s_ini else np.nan

    # ---------- (7) final ----------
    d7 = pq.read_table(base + "__final.parquet").to_pandas()
    r["n7"] = len(d7)
    ult = sb[sb["g"] == gs[-1]][xc].values.astype(np.float32)
    r["c7_eq_c3"] = bool(len(d7) == ult.shape[0] and
                         np.array_equal(d7[xc].values.astype(np.float32), ult))
    r["nd_share"] = float(d7["nd_pos_real"].mean())

    # ---------- (6) jsonl ----------
    recs, dec_keys, nfooter = {}, set(), 0
    fbest_ok, nfront_ok, ndec = 0, 0, 0
    t11_dec = {k: 0 for k in T11_DEC}
    fmin = {g: sb[sb["g"] == g][muc].values.astype(np.float32).min(axis=0)
            for g in gs}
    for line in open(base + ".jsonl"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        rc = d.get("rec")
        recs[rc] = recs.get(rc, 0) + 1
        if rc == "footer":
            nfooter += 1
        if rc == "decision":
            ndec += 1
            dec_keys |= set(d.keys())
            for k in T11_DEC:
                t11_dec[k] += int(k in d)
            g = int(d.get("geracao"))
            if g in fmin:
                fb = np.asarray(d.get("f_best"), dtype=np.float32)
                fbest_ok += int(np.array_equal(fb, fmin[g]))
                nd = len(np.unique(
                    sb[sb["g"] == g][muc].values, axis=0)) if False else None
    r["rec_counts"] = json.dumps(recs)
    r["n_decision"] = ndec
    r["n_footer"] = nfooter
    r["dec_keys"] = "|".join(sorted(dec_keys))
    r["fbest_exato"] = fbest_ok
    for k in T11_DEC:
        r["T11_dec_" + k] = t11_dec[k]
    r["T11_dec_todos_ausentes"] = all(t11_dec[k] == 0 for k in T11_DEC)

    rows.append(r)
    print("%-28s ok" % label, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "b5r_t11_celulas.csv"), index=False)
print("\n== %d celulas ==" % len(df))
print(df[["label", "D", "M", "n1", "n3_busca", "n_ger_c3", "FE_antes",
          "FE_final", "sel_frac", "sel_razao"]].to_string())
