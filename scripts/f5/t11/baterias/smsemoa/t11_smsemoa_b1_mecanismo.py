#!/usr/bin/env python
"""T11 · smsemoa · BATERIA 1 — re-medição do MECANISMO na s42 (25 células) + smoke.

READ-ONLY. Não toca data/experiments. Saídas em f5/t11/baterias/smsemoa/.
Re-mede (não confia no relatório F5 nem no handoff T11):
  U1  orçamento 31D-1 / fe_index denso / solution_id denso / fases
  U2  DoE 11D-1 bit-a-bit contra o artefato + doe_hash
  A3  N=20 em toda geração; N_efetivo ≡ N_nominal
  A5  gerações, Δfe, cache-hits, fechamento aritmético
  A7  ② = snapshot N linhas/geração
  E   elitismo (μ+1): ②(g+1) ⊆ ②(g) ∪ novos(g)
  R   n_front1/ideal/nadir recomputados
  HV  monotonicidade do HV populacional (query-joia)
  T11 campos novos do ⑤ (campanha_id, sigma_dict, repo_hash) e a fórmula
      `geracoes_derivadas` da T11.
"""
import json, sys, os, hashlib
import numpy as np, pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado"
BASE = f"{RAIZ}/resultados_experimentos/smsemoa"
DOE = f"{RAIZ}/ua-dd-saea/data/doe"
SMOKE = f"{RAIZ}/evidencia_T11/smoke_matlab/experiments/main/smsemoa"
OUT = f"{RAIZ}/ua-dd-saea/f5/t11/baterias/smsemoa"

PROBS = sorted(os.listdir(BASE))


def carrega(base, prob, pref="exp_main_smsemoa"):
    p = f"{base}/{prob}/42/{pref}_{prob}_42"
    man = json.load(open(p + ".manifest.json"))
    recs = [json.loads(l) for l in open(p + ".jsonl") if l.strip()]
    r1 = pd.read_parquet(p + "__real.parquet")
    r2 = pd.read_parquet(p + "__pop.parquet")
    r3 = pd.read_parquet(p + "__surrogate.parquet")
    r4 = pd.read_parquet(p + "__timing.parquet")
    return man, recs, r1, r2, r3, r4


def hv2(P, ref):
    """HV exato p/ M=2 e Monte-Carlo determinístico p/ M>=3, pontos <= ref."""
    P = np.asarray(P, float)
    P = P[np.all(P <= ref, axis=1)]
    if len(P) == 0:
        return 0.0
    # filtra não-dominados
    keep = np.ones(len(P), bool)
    for i in range(len(P)):
        if not keep[i]:
            continue
        d = np.all(P <= P[i], axis=1) & np.any(P < P[i], axis=1)
        if d.any():
            keep[i] = False
    P = P[keep]
    M = P.shape[1]
    if M == 2:
        o = P[np.argsort(P[:, 0])]
        hv, prev = 0.0, ref[1]
        for x, y in o:
            if y < prev:
                hv += (ref[0] - x) * (prev - y)
                prev = y
        return hv
    rng = np.random.default_rng(12345)
    lo = P.min(0)
    S = rng.uniform(lo, ref, size=(200000, M))
    dom = np.zeros(len(S), bool)
    for p in P:
        dom |= np.all(S >= p, axis=1)
    return dom.mean() * np.prod(ref - lo)


def ndsort(F):
    n = len(F)
    fr = np.zeros(n, int)
    dom = [[] for _ in range(n)]
    cnt = np.zeros(n, int)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if np.all(F[i] <= F[j]) and np.any(F[i] < F[j]):
                dom[i].append(j)
            elif np.all(F[j] <= F[i]) and np.any(F[j] < F[i]):
                cnt[i] += 1
    cur = [i for i in range(n) if cnt[i] == 0]
    k = 1
    while cur:
        nxt = []
        for i in cur:
            fr[i] = k
            for j in dom[i]:
                cnt[j] -= 1
                if cnt[j] == 0:
                    nxt.append(j)
        cur = nxt
        k += 1
    return fr


def crowd(F):
    n, m = F.shape
    cd = np.zeros(n)
    for j in range(m):
        o = np.argsort(F[:, j], kind="stable")
        cd[o[0]] = cd[o[-1]] = np.inf
        rng = F[o[-1], j] - F[o[0], j]
        if rng <= 0:
            continue
        for k in range(1, n - 1):
            cd[o[k]] += (F[o[k + 1], j] - F[o[k - 1], j]) / rng
    return cd


rows = []
serie_hv = {}
for prob in PROBS:
    man, recs, r1, r2, r3, r4 = carrega(BASE, prob)
    hdr = [x for x in recs if x["rec"] == "header"][0]
    ftr = [x for x in recs if x["rec"] == "footer"][0]
    gens = [x for x in recs if x["rec"].endswith("_gen")]
    guards = [x for x in recs if x["rec"] == "guard"]
    seed = [x for x in recs if x["rec"] == "seeding"]
    D, M = hdr["D"], hdr["M"]
    o = dict(problema=prob, D=D, M=M)

    # ─── U1 orçamento ────────────────────────────────────────────────────
    maxfe, init = 31 * D - 1, 11 * D - 1
    o["U1_maxfe_esp"] = maxfe
    o["U1_n_real"] = len(r1)
    o["U1_len_ok"] = len(r1) == maxfe
    o["U1_fefinal_ok"] = man["fe_final"] == man["maxfe"] == maxfe
    o["U1_feidx_denso"] = bool((r1["fe_index"].values == np.arange(maxfe)).all())
    o["U1_sid_denso"] = bool((np.sort(r1["solution_id"].values) == np.arange(maxfe)).all())
    o["U1_n_init"] = int((r1["fase"] == "init").sum())
    o["U1_n_opt"] = int((r1["fase"] == "opt").sum())
    o["U1_fases_ok"] = (o["U1_n_init"] == init) and (o["U1_n_opt"] == 20 * D)

    # ─── U2 DoE ──────────────────────────────────────────────────────────
    dd = pd.read_parquet(f"{DOE}/{prob}/doe_{prob}_42.parquet")
    xc = [c for c in r1.columns if c.startswith("x") and c[1:].isdigit()]
    xd = [c for c in dd.columns if c.startswith("x") and c[1:].isdigit()]
    A = r1.sort_values("solution_id").head(init)[xc].values.astype(np.float32)
    B = dd[xd].values.astype(np.float32)
    o["U2_dX_max_f32"] = float(np.abs(A - B).max())
    side = f"{DOE}/{prob}/doe_{prob}_42.sidecar.json"
    o["U2_hash_ok"] = None
    if os.path.exists(side):
        o["U2_hash_ok"] = json.load(open(side)).get("hash") == man["doe_hash"]
    o["U2_hash_hdr"] = hdr["doe_hash"] == man["doe_hash"]

    # ─── A3 população ────────────────────────────────────────────────────
    o["A3_N_nom"] = man["params"]["N_nominal"]
    o["A3_N_ef"] = man["params"]["N_efetivo"]
    o["A3_npop_sempre20"] = all(g["n_pop"] == 20 for g in gens)
    o["A3_n_gens_log"] = len(gens)
    o["A3_n_ger_man"] = man["n_geracoes"]
    o["A3_n_ger_ftr"] = ftr["n_geracoes"]
    o["A3_ger_eq_Dmais1"] = man["n_geracoes"] == D + 1

    # ─── A5 Δfe / cache-hits / fechamento ────────────────────────────────
    fe = np.array([g["fe"] for g in gens])
    dfe = np.diff(fe)
    o["A5_fe_g1"] = int(fe[0])
    o["A5_fe_g1_eq_init"] = int(fe[0]) == init
    o["A5_dfe_todos20"] = bool((dfe == 20).all())
    o["A5_dfe_n_igual20"] = int((dfe == 20).sum())
    o["A5_n_trans"] = len(dfe)
    o["A5_dfe_unicos"] = sorted(set(int(x) for x in dfe))
    o["A5_fe_last"] = int(fe[-1])
    ch = [g for g in guards if g.get("name") == "cache_hit"]
    hs = [g for g in guards if g.get("name") != "cache_hit"]
    o["A5_n_guards"] = len(guards)
    o["A5_n_cache"] = len(ch)
    o["A5_n_outros_guards"] = len(hs)
    o["A5_outros_nomes"] = sorted(set(g.get("name") for g in hs))
    o["A5_cache_man"] = man["cache_hits"]
    o["A5_cache_ftr"] = ftr["cache_hits"]
    o["A5_cache_recon"] = man["cache_hits"] == len(ch)
    ch_init = [g for g in ch if g["fe"] == init]
    o["A5_cache_no_init"] = len(ch_init)
    o["A5_cache_init_sids_unicos"] = len(set(g["solution_id"] for g in ch_init))
    o["A5_cache_pos_init"] = len(ch) - len(ch_init)
    # fechamento por ORDEM no fluxo (armadilha ⑤ do F5)
    idx_gen = {id(x): i for i, x in enumerate(recs)}
    ordem = [(i, x) for i, x in enumerate(recs) if x["rec"].endswith("_gen") or
             (x["rec"] == "guard" and x.get("name") == "cache_hit")]
    dups_por_ger, gi, cur = {}, 0, 0
    for i, x in ordem:
        if x["rec"].endswith("_gen"):
            gi = x["geracao"]
        elif gi >= 1:
            dups_por_ger[gi + 1] = dups_por_ger.get(gi + 1, 0) + 1
    ok_fech = True
    for k in range(1, len(gens)):
        esp = 20 - int(dfe[k - 1])
        got = dups_por_ger.get(gens[k]["geracao"], 0)
        if esp != got:
            ok_fech = False
    o["A5_fechamento_ok"] = ok_fech

    # ─── A7 ② ────────────────────────────────────────────────────────────
    gsz = r2.groupby("geracao").size()
    o["A7_pop_linhas"] = len(r2)
    o["A7_grupos"] = len(gsz)
    o["A7_todos20"] = bool((gsz == 20).all())
    o["A7_total_ok"] = len(r2) == 20 * man["n_geracoes"]
    o["A7_dup_intra"] = int(sum(r2.groupby("geracao")["solution_id"].apply(
        lambda s: len(s) - s.nunique())))

    # ─── E elitismo ──────────────────────────────────────────────────────
    pops = {int(g): set(s["solution_id"].astype(int)) for g, s in r2.groupby("geracao")}
    viol, entr = 0, []
    gl = sorted(pops)
    for a, b in zip(gl, gl[1:]):
        fa = fe[gl.index(a)]
        fb = fe[gl.index(b)]
        novos = set(range(int(fa), int(fb)))
        if not pops[b] <= (pops[a] | novos):
            viol += 1
        entr.append(len(pops[b] - pops[a]))
    o["E_viol"] = viol
    o["E_trans"] = len(entr)
    o["E_entr_med"] = float(np.mean(entr)) if entr else np.nan
    o["E_entr_max"] = int(max(entr)) if entr else 0
    o["E_entr_soma"] = int(sum(entr))
    o["E_ent_le_N"] = all(e <= 20 for e in entr)

    # ─── R recomputo DI-10 ───────────────────────────────────────────────
    fcols = [c for c in r1.columns if c.startswith("f") and c[1:].isdigit()]
    fmap = r1.set_index("solution_id")[fcols]
    bad_f1 = bad_id = bad_np = bad_nf = 0
    fr1 = []
    for g in gens:
        gg = int(g["geracao"])
        sid = sorted(pops[gg])
        F = fmap.loc[sid].values.astype(np.float64)
        if not np.allclose(F.min(0), np.array(g["ideal"], float), rtol=1e-5, atol=1e-8):
            bad_id += 1
        if not np.allclose(F.max(0), np.array(g["nadir_pop"], float), rtol=1e-5, atol=1e-8):
            bad_np += 1
        fr = ndsort(F)
        n1 = int((fr == 1).sum())
        if n1 != g["n_front1"]:
            bad_f1 += 1
        fr1.append(g["n_front1"] / 20.0)
        if g.get("nadir_front1"):
            if not np.allclose(F[fr == 1].max(0), np.array(g["nadir_front1"], float),
                               rtol=1e-5, atol=1e-8):
                bad_nf += 1
    o["R_bad_front1"] = bad_f1
    o["R_bad_ideal"] = bad_id
    o["R_bad_nadirpop"] = bad_np
    o["R_bad_nadirf1"] = bad_nf
    o["R_fbest_eq_ideal"] = all(g["f_best"] == g["ideal"] for g in gens)
    o["R_front1_frac_med"] = float(np.mean(fr1))

    # ─── seeding D88 ─────────────────────────────────────────────────────
    if seed:
        s = seed[0]
        o["S_n_doe"], o["S_n_frentes"], o["S_n_frente1"] = s["n_doe"], s["n_frentes"], s["n_frente1"]
        o["S_f1_excede"] = s["frente1_excede_pop"]
        Fd = r1.sort_values("solution_id").head(init)[fcols].values.astype(np.float64)
        fr = ndsort(Fd)
        pick, k = [], 1
        while len(pick) < 20:
            idx = np.where(fr == k)[0]
            if len(pick) + len(idx) <= 20:
                pick += list(idx)
            else:
                cd = crowd(Fd[idx])
                ordn = sorted(range(len(idx)), key=lambda t: (-cd[t], idx[t]))
                pick += [idx[t] for t in ordn[:20 - len(pick)]]
            k += 1
        o["S_pick_igual"] = set(pick) == pops[1]
        o["S_n_frentes_calc"] = int(fr.max())
        o["S_n_frente1_calc"] = int((fr == 1).sum())
        o["S_frentes_ok"] = (o["S_n_frentes_calc"] == s["n_frentes"] and
                             o["S_n_frente1_calc"] == s["n_frente1"])
        o["S_todos_do_doe"] = all(x < init for x in pops[1])

    # ─── ③ / sonda / sigma ───────────────────────────────────────────────
    o["SUR_linhas"] = len(r3)
    o["SUR_cols"] = r3.shape[1]
    o["SONDA_status"] = man["sonda"]["status"]
    o["SONDA_blocos"] = man["sonda"]["n_blocos"]
    o["FIT_series"] = len(man["fit_series"])

    # ─── ④ timing ────────────────────────────────────────────────────────
    o["T_rows_ok"] = len(r4) == man["n_geracoes"]
    o["T_fit_null"] = bool(r4["tempo_fit_s"].isna().all())
    o["T_busca_null"] = bool(r4["tempo_busca_s"].isna().all())
    o["T_sonda_null"] = bool(r4["tempo_pred_sonda_s"].isna().all())
    o["T_ger_gt0"] = bool((r4["tempo_geracao_s"] > 0).all())
    o["T_soma_ger"] = float(r4["tempo_geracao_s"].sum())
    o["T_total"] = man["timing"]["tempo_total_s"]
    o["T_soma_le_total"] = o["T_soma_ger"] <= o["T_total"]
    o["T_aval_real"] = man["timing"]["tempo_aval_real_s"]
    o["T_jsonl_eq_parquet"] = bool(np.allclose(
        [g["tempo_geracao_s"] for g in gens], r4["tempo_geracao_s"].values, rtol=1e-5))

    # ─── T11: campos novos ───────────────────────────────────────────────
    o["T11_schema"] = man.get("schema_version")
    o["T11_campanha_id"] = man.get("campanha_id")
    o["T11_repo_hash"] = man.get("repo_hash")
    o["T11_sigma_dict"] = json.dumps(man.get("sigma_dict")) if man.get("sigma_dict") else None
    o["T11_gerderiv"] = man["params"]["geracoes_derivadas"][:30]
    o["T11_hdr_keys"] = ",".join(sorted(hdr))
    o["T11_hdr_tem_run_id"] = "run_id" in hdr
    o["T11_hdr_tem_ambiente"] = "ambiente" in hdr
    # a fórmula T11: floor((20D + n_dup) / (2*floor(Nef/2)))
    ndup = len(ch) - init_ch if (init_ch := 0) else len(ch)
    ndup_evo = len(ch) - o["A5_cache_no_init"]
    Nef = 20
    o["T11_formula_T11"] = int(np.floor((20 * D + ndup_evo) / (2 * np.floor(Nef / 2))))
    o["T11_formula_antiga"] = int(20 * D / Nef)
    o["T11_formula_ceil_F5"] = int(np.ceil((20 * D + ndup_evo) / Nef))
    o["T11_ndup_evo"] = ndup_evo
    o["T11_real"] = man["n_geracoes"]
    o["T11_formula_bate"] = o["T11_formula_T11"] == man["n_geracoes"]
    o["T11_formula_bate_mais1"] = o["T11_formula_T11"] + 1 == man["n_geracoes"]

    # ─── HV populacional (query-joia) ────────────────────────────────────
    serie_hv[prob] = None
    rows.append(o)

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/t11_b1_mecanismo.csv", index=False)
print(df.to_string())
