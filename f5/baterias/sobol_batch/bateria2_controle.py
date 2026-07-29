#!/usr/bin/env python
"""BATERIA 2 — papel de CONTROLE, saúde em escala e CONTRAFACTUAIS do `sobol_batch`.

(1) gate D92 antes de qualquer métrica; (2) trajetórias 20-checkpoints (violações);
(3) truncamento a-FEs-iguais (fe ≤ 31D−1) — a lente §V-B.5; (4) CONTRAFACTUAL A:
"Sobol ÚNICO por semente" (a LETRA da D37) × "Sobol por ITERAÇÃO" (o implementado,
DI-33); (5) CONTRAFACTUAL B: scrambling DESLIGADO (o que a D37 evita); (6) ablação
do q potência-de-2 (o caveat do runner); (7) régua vs os SA-batch sobreviventes.
READ-ONLY; escreve só em f5/baterias/sobol_batch/.
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
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from src import standalone_harness as H     # noqa: E402
from src import metrics                     # noqa: E402
from src import problems as P               # noqa: E402
from scipy.stats import qmc                 # noqa: E402

SEED, Q, K, ALG_ID = 42, 10, 200, 22
PROBS = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, f"GATE D92 FALHOU: {v!r}"
print(f"gate D92 OK: {v:.5f}", flush=True)


def sobol01(D, q, seed):
    sob = qmc.Sobol(d=int(D), scramble=True, seed=int(seed))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        return np.asarray(sob.random(int(q)), dtype=np.float64)


traj_rows, trunc_rows, cf_rows, qabl_rows, regua_rows = [], [], [], [], []

for prob in PROBS:
    d = RES / "sobol_batch" / f"q10_{prob}" / str(SEED)
    b = d / f"exp_batch_sobol_batch_{prob}_{SEED}"
    real = pd.read_parquet(str(b) + "__real.parquet")
    xl, xu = H._bounds(prob)
    probobj = H._instantiate(prob)
    D, M = len(xl), int(probobj.n_obj)
    n_init, maxfe = 11 * D - 1, 11 * D - 1 + K * Q
    xcols = [f"x{i}" for i in range(D)]
    fcols = [f"f{j}" for j in range(M)]
    Xr = real[xcols].to_numpy().astype(np.float64)
    Fr = real[fcols].to_numpy().astype(np.float64)

    # ── (2) trajetória 20 checkpoints ────────────────────────────────────────
    tj = json.loads((REPO / "f5" / "trajetorias" /
                     f"batch_sobol_batch_{prob}_42.json").read_text())
    ig = np.array([t["igd_plus"] for t in tj])
    hvv = np.array([t["hv"] for t in tj])
    nnd = np.array([t["n_nd"] for t in tj])
    fes = np.array([t["fe"] for t in tj])
    dif = np.diff(ig)
    traj_rows.append({
        "problema": prob, "D": D, "n_checkpoints": len(tj),
        "fe_primeiro": int(fes[0]), "fe_ultimo": int(fes[-1]),
        "igd_ini": float(ig[0]), "igd_fim": float(ig[-1]),
        "violacoes_monotonicidade": int((dif > 0).sum()),
        "pior_violacao_abs": float(dif.max()) if (dif > 0).any() else 0.0,
        "hv_ini": float(hvv[0]), "hv_fim": float(hvv[-1]),
        "hv_violacoes": int((np.diff(hvv) < -1e-12).sum()),
        "nnd_ini": int(nnd[0]), "nnd_fim": int(nnd[-1]),
        "melhora_rel_igd": float((ig[0] - ig[-1]) / ig[0]),
    })

    # ── (3) truncamento a-FEs-iguais: fe_index ≤ 31D−1 ───────────────────────
    corte = 31 * D - 1
    m_tr = metrics.metrics_of_set(Fr[:corte], prob)
    m_fim = metrics.metrics_of_set(Fr, prob)
    m_init = metrics.metrics_of_set(Fr[:n_init], prob)
    trunc_rows.append({
        "problema": prob, "D": D, "corte_31D_1": corte,
        "igd_plus_DoE_11D_1": m_init["igd_plus"], "hv_DoE": m_init["hv"],
        "igd_plus_at_31D_1": m_tr["igd_plus"], "hv_at_31D_1": m_tr["hv"],
        "n_nd_at_31D_1": m_tr["n_nd"],
        "igd_plus_final_2000": m_fim["igd_plus"], "hv_final": m_fim["hv"],
        "n_nd_final": m_fim["n_nd"],
        "ganho_rel_31D1_para_final": (m_tr["igd_plus"] - m_fim["igd_plus"]) / m_tr["igd_plus"],
    })

    # ── (4) CONTRAFACTUAL A — Sobol ÚNICO por semente (letra da D37) ─────────
    base = H.seed_base("sobol_batch", SEED)
    s1 = H.iteration_seed(base, ALG_ID, 1, 0, bits32=True)
    U_uni = sobol01(D, K * Q, s1)                      # 1 sequência contínua
    X_uni = xl + U_uni * (xu - xl)
    F_uni = np.asarray(P.evaluate_problem(probobj, X_uni), dtype=np.float64)
    F_cf_A = np.vstack([Fr[:n_init], F_uni])
    m_A = metrics.metrics_of_set(F_cf_A, prob)
    # o observado (por iteração)
    U_obs = np.vstack([sobol01(D, Q, H.iteration_seed(base, ALG_ID, g, 0, bits32=True))
                       for g in range(1, K + 1)])
    cd_obs = qmc.discrepancy(U_obs, method="CD", workers=-1)
    cd_uni = qmc.discrepancy(U_uni, method="CD", workers=-1)
    # ── (5) CONTRAFACTUAL B — scrambling DESLIGADO ──────────────────────────
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        u_puro = np.asarray(qmc.Sobol(d=D, scramble=False).random(Q))
    U_nos = np.vstack([u_puro] * K)
    cf_rows.append({
        "problema": prob, "D": D,
        "igd_plus_obs": m_fim["igd_plus"], "hv_obs": m_fim["hv"], "nnd_obs": m_fim["n_nd"],
        "igd_plus_cfA_sobol_unico": m_A["igd_plus"], "hv_cfA": m_A["hv"],
        "nnd_cfA": m_A["n_nd"],
        "delta_rel_igd_cfA": (m_fim["igd_plus"] - m_A["igd_plus"]) / m_A["igd_plus"],
        "CD_obs_por_iteracao": cd_obs, "CD_cfA_sobol_unico": cd_uni,
        "razao_CD_obs_sobre_unico": cd_obs / cd_uni,
        "cfB_pontos_unicos_sem_scramble": int(len(np.unique(np.round(U_nos, 12), axis=0))),
        "cfB_primeiro_ponto_eh_origem": bool(np.all(u_puro[0] == 0.0)),
    })

    # ── (6) ablação do q potência-de-2 (n≈2000 fixo) ─────────────────────────
    for qq, kk in ((8, 250), (10, 200), (16, 125)):
        Uq = np.vstack([sobol01(D, qq, H.iteration_seed(base, ALG_ID, g, 0, bits32=True))
                        for g in range(1, kk + 1)])
        qabl_rows.append({"problema": prob, "D": D, "q": qq, "K": kk, "n": qq * kk,
                          "CD": qmc.discrepancy(Uq, method="CD", workers=-1)})

    print(f"[ok] {prob}", flush=True)

# ── (7) régua: o controle cumpre a função? ──────────────────────────────────
met = pd.read_csv(REPO / "f5" / "metricas_finais_f52c.csv")
bat = met[met.exp == "batch"]
main = met[met.exp == "main"]
for prob in PROBS:
    sb = bat[(bat.alg == "sobol_batch") & (bat.problema == prob)].iloc[0]
    row = {"problema": prob, "sobol_igd": sb.igd_plus, "sobol_hv": sb.hv,
           "sobol_nnd": sb.n_nd}
    for a in ("e81", "c149"):
        sub = bat[(bat.alg == a) & (bat.problema == prob)]
        if len(sub):
            row[f"{a}_igd"] = sub.iloc[0].igd_plus
            row[f"{a}_hv"] = sub.iloc[0].hv
            row[f"{a}_bate_controle_igd"] = bool(sub.iloc[0].igd_plus < sb.igd_plus)
            row[f"{a}_bate_controle_hv"] = bool(sub.iloc[0].hv > sb.hv)
    mm = main[main.problema == prob].dropna(subset=["igd_plus"])
    if len(mm):
        row["main_melhor_alg"] = mm.loc[mm.igd_plus.idxmin(), "alg"]
        row["main_melhor_igd"] = float(mm.igd_plus.min())
        row["main_n_configs"] = int(len(mm))
    regua_rows.append(row)

pd.DataFrame(traj_rows).to_csv(OUT / "trajetorias.csv", index=False)
pd.DataFrame(trunc_rows).to_csv(OUT / "truncamento_fes_iguais.csv", index=False)
pd.DataFrame(cf_rows).to_csv(OUT / "contrafactuais.csv", index=False)
pd.DataFrame(qabl_rows).to_csv(OUT / "ablacao_q_potencia2.csv", index=False)
pd.DataFrame(regua_rows).to_csv(OUT / "regua_controle.csv", index=False)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
for nm, dfx in (("TRAJ", traj_rows), ("TRUNC", trunc_rows), ("CONTRAFACTUAIS", cf_rows),
                ("ABL q", qabl_rows), ("REGUA", regua_rows)):
    print(f"\n=== {nm} ===")
    print(pd.DataFrame(dfx).to_string())
