#!/usr/bin/env python
"""T11/c262 — BATERIA B: re-medicao do MECANISMO na rodada-42 (21 celulas main).
READ-ONLY absoluto. Nada de data/experiments; so resultados_experimentos/c262/.
Re-mede: U1 (FE), U2 (DoE), U3 (fits), U4 (sonda), U8, U10, F1/F2/F4 (query-joias),
guardas, e o DELTA de instrumentacao s42 x T11.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262"
DOE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe"
rows = []
probs = sorted(os.listdir(ROOT))

for p in probs:
    d = f"{ROOT}/{p}/42"
    if not os.path.isdir(d):
        continue
    base = glob.glob(f"{d}/*.manifest.json")
    if not base:
        continue
    B = base[0][: -len(".manifest.json")]
    m = json.load(open(f"{B}.manifest.json"))
    r = {"problema": p, "status": m.get("status")}

    # ---- DELTA de instrumentacao T11 (o que a s42 NAO tem) ----
    for k in ["params", "campanha_id", "repo_hash", "schema_version",
              "checkpoint", "motivo_parada", "executable"]:
        r[f"m_tem_{k}"] = k in m
    r["m_sonda_keys"] = ",".join(sorted(m.get("sonda", {}).keys()))

    r["maxfe"] = m.get("maxfe"); r["fe_final"] = m.get("fe_final")
    r["n_ger"] = m.get("n_geracoes"); r["cache_hits"] = m.get("cache_hits")
    r["n_retries"] = m.get("n_retries"); r["fallback"] = m.get("fallback_ativado")
    r["n_blocos_sonda_manif"] = m.get("sonda", {}).get("n_blocos")

    # ---- 1) ----
    r1 = pd.read_parquet(f"{B}__real.parquet")
    xcols = [c for c in r1.columns if c.startswith("x") and c[1:].isdigit()]
    fcols = [c for c in r1.columns if c.startswith("f") and c[1:].isdigit()]
    D = len(xcols); M = len(fcols)
    r["D"] = D; r["M"] = M
    r["u1_len1"] = len(r1)
    r["u1_31D_1"] = 31 * D - 1
    r["u1_ok"] = (len(r1) == 31 * D - 1 == m.get("maxfe") == m.get("fe_final"))
    r["u1_fe_index_denso_ord"] = bool((r1["fe_index"].values ==
                                       np.arange(len(r1))).all())
    r["u2_n_init"] = int((r1["fase"] == "init").sum())
    r["u2_11D_1"] = 11 * D - 1
    # DoE bit-a-bit
    dp = f"{DOE}/{p}/doe_{p}_42.parquet"
    if os.path.exists(dp):
        doe = pd.read_parquet(dp)
        dxc = [c for c in doe.columns if c.startswith("x") and c[1:].isdigit()]
        n0 = int((r1["fase"] == "init").sum())
        A = r1.loc[r1["fase"] == "init", xcols].values[:n0].astype(np.float64)
        Bm = doe[dxc].values[:n0].astype(np.float64)
        r["u2_dx_doe_max"] = float(np.max(np.abs(A - Bm)))
    else:
        r["u2_dx_doe_max"] = None

    # ---- 6) ----
    recs = []; bad = 0
    for ln in open(f"{B}.jsonl"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            recs.append(json.loads(ln))
        except Exception:
            bad += 1
    r["u9_linhas_ruins"] = bad
    hdr = [x for x in recs if x.get("rec") == "header"]
    h = hdr[0] if hdr else {}
    r["h_tem_params"] = "params" in h
    r["h_params_n"] = len(h.get("params", {}))
    r["h_params_tem_acqf_hp"] = "acqf_hp" in h.get("params", {})
    r["h_kernel"] = h.get("params", {}).get("kernel")
    r["h_acqf"] = h.get("params", {}).get("acqf")
    r["h_train_Yvar"] = h.get("params", {}).get("train_Yvar")
    r["h_cache_root"] = h.get("params", {}).get("cache_root")
    r["h_mc"] = h.get("params", {}).get("mc_samples")
    r["h_nrest"] = h.get("params", {}).get("num_restarts")
    r["h_fused"] = h.get("fused_kernel")
    r["h_ref_fonte"] = h.get("ref_fonte")
    r["n_footer"] = sum(1 for x in recs if x.get("rec") == "footer")
    ft = [x for x in recs if x.get("rec") == "footer"]
    r["f_hard_stopped"] = ft[0].get("hard_stopped") if ft else None
    r["f_cp_init"] = ft[0].get("cp_init") if ft else None
    r["f_tem_n_checkpoints"] = ("n_checkpoints" in ft[0]) if ft else None

    gu = [x for x in recs if x.get("rec") == "guard"]
    r["n_guard"] = len(gu)
    r["guard_nomes"] = ",".join(sorted({str(g.get("name")) for g in gu}))
    r["n_guard_fit_retries"] = sum(1 for g in gu if g.get("name") == "fit_retries")

    dec = [x for x in recs if x.get("rec") == "decision"]
    tim = [x for x in recs if x.get("rec") == "timing"]
    snd = [x for x in recs if x.get("rec") == "sonda"]
    r["u3_n_dec"] = len(dec); r["u3_n_tim"] = len(tim)
    r["u3_ok"] = (len(dec) == len(tim) == m.get("n_geracoes") ==
                  len(m.get("fit_series", [])))
    r["u4_n_sonda"] = len(snd)
    ng = m.get("n_geracoes")
    esperado = {g for g in range(1, ng + 1) if g == 1 or g % 2 == 0} | {ng}
    obtido = {int(s.get("geracao") or s.get("it")) for s in snd}
    r["u4_formula_ok"] = (esperado == obtido)
    r["u4_ng_par"] = (ng % 2 == 0)

    # fit_retries do 6 (o campo que virou guard no T11)
    fr = [d.get("fit_retries") for d in dec]
    r["fit_retries_soma"] = int(np.nansum([x or 0 for x in fr]))
    r["fit_retries_its_pos"] = int(sum(1 for x in fr if (x or 0) > 0))

    # ---- QUERY-JOIA 1 ----
    ok = tot = 0; dmax = 0.0
    for dd in dec:
        a = dd.get("acqf_todos_restarts"); e = dd.get("acqf_escolhido")
        if a is None or e is None:
            continue
        tot += 1
        delta = abs(float(e) - max(float(x) for x in a))
        dmax = max(dmax, delta)
        ok += (delta == 0.0)
    r["joia1_ok"] = ok; r["joia1_tot"] = tot; r["joia1_dmax"] = dmax
    r["nrest_set"] = ",".join(str(x) for x in sorted(
        {len(dd.get("acqf_todos_restarts") or []) for dd in dec}))
    al = [float(dd["acqf_escolhido"]) for dd in dec
          if dd.get("acqf_escolhido") is not None]
    r["alpha_min"] = min(al); r["alpha_max"] = max(al)
    r["alpha_neg"] = sum(1 for x in al if x < 0)
    r["n_hardstop"] = sum(1 for dd in dec if dd.get("caminho") == "hard_stop")
    r["n_cachehit"] = sum(1 for dd in dec if dd.get("cache_hit"))

    # ---- 3) ----
    r3 = pd.read_parquet(f"{B}__surrogate.parquet")
    r["l3_linhas"] = len(r3)
    vc = r3["regime"].value_counts().to_dict()
    r["l3_online"] = vc.get("online", 0); r["l3_sonda"] = vc.get("sonda", 0)
    r["l3_regimes"] = ",".join(sorted(vc.keys()))
    r["l3_tem_estrat"] = "sonda_estratificada" in vc
    on = r3[r3["regime"] == "online"]
    r["l3_online_eq_10xdec"] = (len(on) == 10 * len(dec))
    tam = on.groupby("geracao").size().unique()
    r["l3_tam_blocos"] = ",".join(str(x) for x in sorted(tam))
    # QUERY-JOIA 2
    marc = on[on["real_solution_id"].notna()]
    r["joia2_marcadas"] = len(marc)
    pos_ult = 0
    for g, blk in on.groupby("geracao"):
        idx = np.where(blk["real_solution_id"].notna().values)[0]
        if len(idx) == 1 and idx[0] == len(blk) - 1:
            pos_ult += 1
    r["joia2_ultima"] = pos_ult
    r1i = r1.set_index("solution_id")
    dmx = 0.0
    sub = marc
    for _, row in sub.iterrows():
        sid = int(row["real_solution_id"])
        if sid in r1i.index:
            a = np.array([row[c] for c in xcols], dtype=np.float64)
            b = np.array([r1i.loc[sid, c] for c in xcols], dtype=np.float64)
            dmx = max(dmx, float(np.max(np.abs(a - b))))
    r["joia2_dx_max"] = dmx
    sc = [c for c in r3.columns if c.startswith("sigma_")]
    r["sigma_nan"] = int(np.isnan(r3[sc].values).sum())
    r["sigma_min"] = float(np.nanmin(r3[sc].values))
    r["sonda_sid_marcada"] = int(
        r3[r3["regime"] == "sonda"]["real_solution_id"].notna().sum())
    # U8 monotonia
    ftm = on.groupby("geracao")["fe_treino_max"].max().dropna().values
    r["u8_monotono"] = bool((np.diff(ftm) >= 0).all())

    # ---- QUERY-JOIA 4: noise == max(1e-6, 1e-6/Var(-f)) ----
    r1o = r1.sort_values("fe_index")
    Y = -r1o[fcols].values.astype(np.float64)
    okn = totn = 0; errmax = 0.0; piso = 0
    for dd in dec:
        mh = dd.get("modelo_hp")
        nt = dd.get("n_train")
        if not mh or nt is None:
            continue
        objs = mh if isinstance(mh, list) else [mh]
        for j, o in enumerate(objs):
            nz = o.get("noise") if isinstance(o, dict) else None
            if nz is None:
                continue
            v = float(np.var(Y[:int(nt), j], ddof=1))
            esp = max(1e-6, 1e-6 / v)
            totn += 1
            e = abs(float(nz) - esp) / max(esp, 1e-30)
            errmax = max(errmax, e)
            okn += (e < 1e-5)
            piso += (esp == 1e-6)
    r["joia4_ok"] = okn; r["joia4_tot"] = totn
    r["joia4_errmax"] = errmax; r["joia4_piso"] = piso

    # ---- 2) off-by-one ----
    r2 = pd.read_parquet(f"{B}__pop.parquet")
    r["l2_blocos"] = int(r2["geracao"].nunique())
    r["l2_eq_ng1"] = (int(r2["geracao"].nunique()) == m.get("n_geracoes") + 1)
    # U10 aritmetica
    r["u10_ok"] = (m.get("n_geracoes") ==
                   (m.get("fe_final") - int((r1["fase"] == "init").sum()))
                   + (m.get("cache_hits") or 0) + 1)
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/"
          "baterias/c262/c262_t11_s42.csv", index=False)

print("CELULAS:", len(df))
print("--- DELTA INSTRUMENTACAO (s42) ---")
for k in ["m_tem_params", "m_tem_campanha_id", "m_tem_repo_hash",
          "m_tem_schema_version", "m_tem_checkpoint", "m_tem_motivo_parada",
          "h_tem_params", "h_params_tem_acqf_hp", "f_tem_n_checkpoints",
          "l3_tem_estrat"]:
    print(f"  {k:26s}: True={int(df[k].sum())}/{len(df)}")
print("  h_params_n set:", sorted(df["h_params_n"].unique()))
print("  m_sonda_keys:", sorted(df["m_sonda_keys"].unique()))
print("  guard_nomes:", sorted(df["guard_nomes"].unique()))
print("  n_guard_fit_retries total:", int(df["n_guard_fit_retries"].sum()))
print("--- UNIVERSAIS ---")
print("  U1 ok:", int(df["u1_ok"].sum()), "/", len(df),
      "| fe_index denso+ord:", int(df["u1_fe_index_denso_ord"].sum()))
print("  U2 init==11D-1:", int((df["u2_n_init"] == df["u2_11D_1"]).sum()),
      "| dx DoE max:", df["u2_dx_doe_max"].max())
print("  U3 ok:", int(df["u3_ok"].sum()), "| Sigma decisoes:",
      int(df["u3_n_dec"].sum()))
print("  U4 formula ok:", int(df["u4_formula_ok"].sum()),
      "| Sigma blocos:", int(df["u4_n_sonda"].sum()),
      "| ng par:", int(df["u4_ng_par"].sum()))
print("  U8 monotono:", int(df["u8_monotono"].sum()))
print("  U10 ok:", int(df["u10_ok"].sum()), "| l2==ng+1:",
      int(df["l2_eq_ng1"].sum()))
print("  jsonl ruins:", int(df["u9_linhas_ruins"].sum()),
      "| footers:", sorted(df["n_footer"].unique()),
      "| n_retries:", sorted(df["n_retries"].unique()),
      "| fallback:", sorted(df["fallback"].astype(str).unique()))
print("--- QUERY-JOIAS ---")
print("  F1 argmax:", int(df["joia1_ok"].sum()), "/", int(df["joia1_tot"].sum()),
      "| dmax:", df["joia1_dmax"].max(), "| nrest:",
      sorted(df["nrest_set"].unique()))
print("  F2 ultima/marcadas:", int(df["joia2_ultima"].sum()), "/",
      int(df["joia2_marcadas"].sum()), "| dx max:", df["joia2_dx_max"].max(),
      "| sonda marcada:", int(df["sonda_sid_marcada"].sum()))
print("  F4 noise:", int(df["joia4_ok"].sum()), "/", int(df["joia4_tot"].sum()),
      "| errmax:", df["joia4_errmax"].max(), "| piso ativo:",
      int(df["joia4_piso"].sum()))
print("--- LOG/ACQF ---")
print("  alpha<0:", int(df["alpha_neg"].sum()), "/", int(df["joia1_tot"].sum()),
      "| min:", df["alpha_min"].min(), "| max:", df["alpha_max"].max())
print("  sigma NaN:", int(df["sigma_nan"].sum()), "| sigma min:",
      df["sigma_min"].min())
print("  3 linhas:", int(df["l3_linhas"].sum()), "| online:",
      int(df["l3_online"].sum()), "| sonda:", int(df["l3_sonda"].sum()),
      "| 10x dec:", int(df["l3_online_eq_10xdec"].sum()))
print("  cache_hits:", int(df["cache_hits"].sum()), "| hard_stop:",
      int(df["n_hardstop"].sum()))
print("  fit_retries s42 soma:", int(df["fit_retries_soma"].sum()),
      "| its com retry:", int(df["fit_retries_its_pos"].sum()))
print(df[["problema", "D", "M", "maxfe", "n_ger", "cache_hits",
          "u4_n_sonda"]].to_string(index=False))
