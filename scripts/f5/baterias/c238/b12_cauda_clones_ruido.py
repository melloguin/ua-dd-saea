#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 12: fecha as 4 pontas soltas.
(A) AMPLIFICACAO DE CAUDA: a (3) guarda mu/sigma em float32 (D53). Em EI = (f-u)Phi(lam)
    + s phi(lam) com lam=(f-u)/s, d ln(EI) ~ -lam*dlam ~ lam^2 * eps32. Preve-se
    rel(recomputo, eim_best) ~ lam_max^2 * 6e-8. Testa a previsao celula a celula
    (explica o residuo do ZDT6/ZDT1 sem invocar desvio de mecanismo).
(B) CLONES DO POOL: as linhas com real_solution_id nao-nulo sao copias do PROPRIO INFILL
    (colapso do GA interno) ou pontos ja amostrados antes? -> decide a leitura do hazard
    "anti-clustering ausente" (B10.7).
(C) SATURACAO EIM==0 (BBOB_F1): e s==0 (ponto amostrado) ou UNDERFLOW da cauda (lam muito
    negativo com GP quase perfeito)? mede s, lam e o que o GA devolve nesse regime.
(D) RUIDO DE eim_best (DI-18) refinado: atribuicao por geracao entre (i) mudanca de escala
    y, (ii) mudanca de CONTEUDO da frente (o infill anterior entrou), (iii) nenhuma das
    duas (= so o remodelo GP: +1 ponto de treino e theta refeito).
(E) semantica de f_best (o (6) loga f_best != min por objetivo do arquivo).
Saidas: cauda_amplif.csv, clones_diag.csv, ruido_refinado.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy.stats import norm
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)
BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
EPS32 = float(np.finfo(np.float32).eps)

cau, clo, rui = [], [], []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    G = [r for r in recs if r.get("rec") == "c238_gen"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    Xr = real[[f"x{i}" for i in range(D)]].values
    cols = ["regime", "geracao", "real_solution_id"] + [f"x{i}" for i in range(D)] + \
           [f"mu_{i}" for i in range(M)] + [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))

    lam_max, rel_obs, s_arg, eim0_lam, eim0_s = [], [], [], [], []
    n_cl_infill = n_cl_antigo = n_cl = 0
    x_ident_infill = 0
    entrou = np.zeros(len(G), bool)
    for gi, r in enumerate(G):
        npre = r["n_amostra"]
        Y = F[:npre]
        wk = b2.nd_weak_seq(Y)
        mn = np.array(r["norm_min"]); rg = np.array(r["norm_range_efetivo"])
        Fr = (Y[wk] - mn) / rg
        sub = grp[r["geracao"]]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        v = b2.eim_euclidean(u, s, Fr)
        j = int(np.argmax(v))
        lam = (Fr[None, :, :] - u[j][None, None, :]) / s[j][None, None, :]
        lam_max.append(float(np.abs(lam).max()))
        s_arg.append(float(s[j].min()))
        eb = r["eim_best"]
        rel_obs.append(abs(float(v.max()) - eb) / max(abs(eb), 1e-300))
        if eb == 0:
            eim0_lam.append(float(np.abs(lam).max())); eim0_s.append(float(s[j].min()))
        # (B) clones
        rsid = sub.real_solution_id.values
        m = pd.notna(rsid)
        n_cl += int(m.sum())
        n_cl_infill += int((rsid[m] == r["infill_sid"]).sum())
        n_cl_antigo += int((rsid[m] != r["infill_sid"]).sum())
        Xp = sub[[f"x{i}" for i in range(D)]].values
        x_ident_infill += int((Xp == Xr[int(r["infill_sid"])]).all(1).sum())
        # (D) o infill DESTA geracao entra na frente do proximo arquivo?
        if npre + 1 <= len(F):
            entrou[gi] = bool(b2.nd_weak_seq(F[:npre + 1])[npre])

    lam_max = np.array(lam_max); rel_obs = np.array(rel_obs)
    prev = lam_max ** 2 * EPS32
    cau.append(dict(problema=prob, M=M, n_gens=len(G),
                    lam_med=float(np.median(lam_max)), lam_p99=float(np.percentile(lam_max, 99)),
                    lam_max=float(lam_max.max()),
                    rel_med=float(np.median(rel_obs)), rel_max=float(rel_obs.max()),
                    prev_med=float(np.median(prev)), prev_max=float(prev.max()),
                    dentro_prev=int((rel_obs <= np.maximum(prev, 1e-7) * 3).sum()),
                    s_arg_min=float(np.min(s_arg)),
                    eim0_n=len(eim0_lam),
                    eim0_lam_min=float(np.min(eim0_lam)) if eim0_lam else np.nan,
                    eim0_s_min=float(np.min(eim0_s)) if eim0_s else np.nan,
                    eim0_s_max=float(np.max(eim0_s)) if eim0_s else np.nan))
    clo.append(dict(problema=prob, n_gens=len(G), pool=len(grp[G[0]["geracao"]]),
                    n_rsid=n_cl, rsid_do_infill=n_cl_infill, rsid_de_antigo=n_cl_antigo,
                    x_identico_ao_infill=x_ident_infill,
                    frac_pool_colapsado=x_ident_infill / (len(G) * len(grp[G[0]["geracao"]]))))
    eb = np.array([r["eim_best"] for r in G], float)
    nre = np.array([r["norm_range_efetivo"] for r in G], float)
    dr = (np.abs(np.diff(nre, axis=0)) > 0).any(1)
    dfront = entrou[:-1]                       # a frente do passo g+1 muda sse o infill de g entrou
    up = np.diff(eb) > 0
    rui.append(dict(problema=prob, n_trans=len(up), subidas=int(up.sum()),
                    escala_mudou=int(dr.sum()), frente_mudou=int(dfront.sum()),
                    sub_escala=int((up & dr).sum()), sub_frente=int((up & dfront & ~dr).sum()),
                    sub_so_modelo=int((up & ~dr & ~dfront).sum())))
    print("OK", prob, f"lam_med={np.median(lam_max):.1f} rel_med={np.median(rel_obs):.2e} "
                      f"prev={np.median(prev):.2e} colapso={clo[-1]['frac_pool_colapsado']:.1%}", flush=True)

pd.set_option("display.width", 320); pd.set_option("display.max_columns", 60)
C = pd.DataFrame(cau); C.to_csv(f"{OUT}/cauda_amplif.csv", index=False); print(C.to_string(index=False))
K = pd.DataFrame(clo); K.to_csv(f"{OUT}/clones_diag.csv", index=False); print(K.to_string(index=False))
R = pd.DataFrame(rui); R.to_csv(f"{OUT}/ruido_refinado.csv", index=False); print(R.to_string(index=False))
print("\nTOTAIS ruido: subidas", R.subidas.sum(), "| so escala", R.sub_escala.sum(),
      "| so frente", R.sub_frente.sum(), "| SO REMODELO", R.sub_so_modelo.sum())
print("TOTAIS clones: rsid", K.n_rsid.sum(), "| do proprio infill", K.rsid_do_infill.sum(),
      "| de ponto antigo", K.rsid_de_antigo.sum(), "| X identico ao infill", K.x_identico_ao_infill.sum())
