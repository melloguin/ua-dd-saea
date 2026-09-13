"""T11/nsga3 — bateria 5: RE-MEDICAO do mecanismo nas 25 celulas da s42 + a celula do smoke.
Aspectos: A1 orcamento/hard-stop · A2 DoE bit-a-bit · A4 N_efetivo · A5 lattice ·
A6 decomposicao 1x · A7 semeadura D88 · A8 |pop| · A9 2*floor(N/2) · A10 aritmetica ·
A11/A13 dedup · A12 colisao float32 · A14 sem geracao fantasma · A18 ideal/nadir ·
A19 ausencia de surrogate · A20 timing · A21 U9 · A22 contrato · A23 repo_hash.
READ-ONLY. Saida: mecanismo_t11.csv
"""
import json, math, os, glob, itertools, hashlib
import numpy as np
import pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3"
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/nsga3"
DOE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"


def uniformpoint_nbi(N, M):
    H1 = 1
    while math.comb(H1 + M, M - 1) <= N:
        H1 += 1
    rows = list(itertools.combinations(range(1, H1 + M), M - 1))
    W = np.array(rows, dtype=float) - np.arange(M - 1)[None, :] - 1.0
    W = (np.hstack([W, np.full((len(W), 1), float(H1))]) -
         np.hstack([np.zeros((len(W), 1)), W])) / H1
    return H1, np.maximum(W, 1e-6)


def ndsort(F):
    n = len(F)
    le = (F[:, None, :] <= F[None, :, :]).all(2)
    lt = (F[:, None, :] < F[None, :, :]).any(2)
    Dm = le & lt
    cnt = Dm.sum(0).astype(int)
    rank = np.full(n, -1)
    cur, k = np.where(cnt == 0)[0], 1
    while len(cur):
        rank[cur] = k
        nxt = []
        for i in cur:
            for j in np.where(Dm[i])[0]:
                cnt[j] -= 1
                if cnt[j] == 0:
                    nxt.append(j)
        cur, k = np.array(sorted(set(nxt)), dtype=int), k + 1
    return rank


def crowding(F, rank):
    n, M = F.shape
    cd = np.zeros(n)
    for r in np.unique(rank):
        idx = np.where(rank == r)[0]
        if len(idx) <= 2:
            cd[idx] = np.inf
            continue
        for m in range(M):
            o = idx[np.argsort(F[idx, m], kind="stable")]
            cd[o[0]] = cd[o[-1]] = np.inf
            fmin, fmax = F[o[0], m], F[o[-1], m]
            if fmax > fmin:
                for t in range(1, len(o) - 1):
                    if np.isfinite(cd[o[t]]):
                        cd[o[t]] += (F[o[t + 1], m] - F[o[t - 1], m]) / (fmax - fmin)
    return cd


def analisa(d, prob, rotulo):
    base = glob.glob(os.path.join(d, "*.manifest.json"))[0][:-len(".manifest.json")]
    man = json.load(open(base + ".manifest.json"))
    recs = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    dec = [r for r in recs if r.get("rec") == "decomposicao"]
    sd = [r for r in recs if r.get("rec") == "seeding"]
    foot = [r for r in recs if r.get("rec") == "footer"]
    gens = [r for r in recs if r.get("rec") == "nsga3_gen"]
    guards = [r for r in recs if r.get("rec") == "guard"]
    D, M = hdr["D"], hdr["M"]
    init, maxfe = 11 * D - 1, 31 * D - 1
    Nn, Nef = man["params"]["N_nominal"], man["params"]["N_efetivo"]
    n_off = 2 * (Nef // 2)
    R = pd.read_parquet(base + "__real.parquet")
    P = pd.read_parquet(base + "__pop.parquet")
    S = pd.read_parquet(base + "__surrogate.parquet")
    T = pd.read_parquet(base + "__timing.parquet")
    xc = ["x%d" % i for i in range(D)]
    fc = ["f%d" % i for i in range(M)]

    o = dict(fonte=rotulo, prob=prob, D=D, M=M, Nnom=Nn, Nef=Nef, n_off=n_off)
    # A1 orcamento
    o["A1_maxfe_ok"] = int(man["maxfe"] == maxfe == man["fe_final"] == len(R))
    o["A1_feindex_denso"] = int((R.fe_index.values == np.arange(len(R))).all())
    hs = [g for g in guards if g.get("name") == "hard_stop"]
    o["A1_hardstop"] = len(hs)
    o["A1_hs_fe"] = hs[0]["fe"] if hs else -1
    o["A1_hs_em_maxfe"] = int(bool(hs) and hs[0]["fe"] == maxfe)
    # A2 DoE bit-a-bit
    p = os.path.join(DOE, prob, "doe_%s_42.parquet" % prob)
    if os.path.exists(p):
        Xd = pd.read_parquet(p)[xc].values.astype(np.float32)
        o["A2_dX"] = float(np.abs(Xd - R.iloc[:init][xc].values).max())
        sc = os.path.join(DOE, prob, "doe_%s_42.manifest.json" % prob)
        o["A2_hash_ok"] = int(json.load(open(sc)).get("doe_hash") == man["doe_hash"]) \
            if os.path.exists(sc) else -1
    else:
        o["A2_dX"], o["A2_hash_ok"] = np.nan, -1
    o["A2_n_init"] = int((R.fase == "init").sum())
    o["A2_init_ok"] = int(o["A2_n_init"] == init)
    o["A2_n_opt"] = int((R.fase == "opt").sum())
    o["A2_opt_ok"] = int(o["A2_n_opt"] == 20 * D)
    # A5 lattice
    H1, Wr = uniformpoint_nbi(Nn, M)
    Wl = np.array(dec[0]["vetores"], dtype=float)
    o["A5_H1"] = H1
    o["A5_nref"] = len(Wr)
    o["A5_nlog"] = len(Wl)
    o["A5_dW"] = float(np.abs(Wr - Wl).max()) if Wr.shape == Wl.shape else np.nan
    o["A5_Nlattice_eq_Nef"] = int(dec[0]["N_lattice"] == Nef)
    # A6
    o["A6_n_decomposicao"] = len(dec)
    # A4/A8 |pop|
    npop = sorted(set(g["n_pop"] for g in gens))
    o["A8_npop_unicos"] = str(npop)
    o["A8_npop_eq_Nef"] = int(npop == [Nef])
    g2 = P.groupby("geracao").size()
    o["A8_grupos2"] = len(g2)
    o["A8_grupos2_eq_Nef"] = int(set(g2.values) == {Nef})
    o["A8_gen_densa"] = int(list(P.geracao.unique()) == list(range(1, len(g2) + 1)))
    o["A8_sid_validos"] = int(P.solution_id.max() < len(R))
    # A7 semeadura D88
    F0 = R.iloc[:init][fc].values.astype(np.float64)
    rk = ndsort(F0)
    cd = crowding(F0, rk)
    ordem = sorted(range(init), key=lambda i: (rk[i], -cd[i], i))
    sel = set(ordem[:Nef])
    pop1 = set(P[P.geracao == 1].solution_id.astype(int).tolist())
    o["A7_conjunto_igual"] = int(sel == pop1)
    o["A7_nfrentes_log"] = sd[0]["n_frentes"]
    o["A7_nfrentes_rec"] = int(rk.max())
    o["A7_nf1_log"] = sd[0]["n_frente1"]
    o["A7_nf1_rec"] = int((rk == 1).sum())
    o["A7_pop1_no_doe"] = int(max(pop1) < init)
    # A9/A10 aritmetica
    ch = [g for g in guards if g.get("name") == "cache_hit"]
    fe_last = gens[-1]["fe"]
    ch_init = [g for g in ch if g.get("fe") == init]
    ch_off = [g for g in ch if init < g.get("fe", 0) <= fe_last]
    ch_tail = [g for g in ch if g.get("fe", 0) > fe_last]
    ngen = len(gens)
    off_full = (ngen - 1) * n_off
    fe_cons = fe_last - init
    o["A10_off_full"] = off_full
    o["A10_fe_cons"] = fe_cons
    o["A10_dup_off"] = len(ch_off)
    o["A10_fecha"] = int(off_full - fe_cons == len(ch_off))
    o["A10_parcial"] = maxfe - fe_last + len(ch_tail)
    o["A10_parcial_le_noff"] = int(maxfe - fe_last <= n_off)
    o["A13_ch_init"] = len(ch_init)
    o["A13_eq_Nef_mais1"] = int(len(ch_init) == Nef + 1)
    o["A13_sids_distintos"] = len(set(g["solution_id"] for g in ch_init))
    o["A13_sids_eq_Nef"] = int(len(set(g["solution_id"] for g in ch_init)) == Nef)
    o["A11_dup_pct"] = 100.0 * len(ch_off) / off_full if off_full else np.nan
    # A21 U9
    o["A21_ch_manifesto"] = man["cache_hits"]
    o["A21_ch_jsonl"] = len(ch)
    o["A21_bate"] = int(man["cache_hits"] == len(ch))
    o["A21_nomes_guard"] = str(sorted(set(g.get("name") for g in guards)))
    # A12 colisao float32
    Xs = R[xc].values
    vistos, col = {}, 0
    for i in range(len(Xs)):
        k = Xs[i].tobytes()
        if k in vistos:
            col += 1
        else:
            vistos[k] = i
    o["A12_colisoes"] = col
    # A14 sem geracao fantasma
    o["A14_ngen_man"] = man["n_geracoes"]
    o["A14_ngen_ev"] = ngen
    o["A14_t4_rows"] = len(T)
    o["A14_tudo_igual"] = int(man["n_geracoes"] == ngen == len(T) == len(g2))
    # A18 ideal/nadir
    dif = 0
    naomono = 0
    for g in gens:
        if not np.allclose(np.array(g["f_best"], dtype=float),
                           np.array(g["ideal"], dtype=float), rtol=0, atol=0):
            dif += 1
    idl = np.array([g["ideal"] for g in gens], dtype=float)
    nad = np.array([g["nadir_pop"] for g in gens], dtype=float)
    naomono = int((np.diff(idl, axis=0) > 0).sum())
    o["A18_ideal_ne_fbest"] = dif
    o["A18_nao_monotonias"] = naomono
    o["A18_transicoes"] = (ngen - 1) * M
    o["A18_nadir_ge_ideal"] = int((nad >= idl).all())
    # A19 sem surrogate
    o["A19_terceira_linhas"] = len(S)
    o["A19_fit_series_vazia"] = int(man["fit_series"] == [])
    o["A19_sonda_status"] = man["sonda"]["status"]
    o["A19_sigma_dict"] = str(man.get("sigma_dict", "<AUSENTE>"))[:60]
    o["A19_header_surrogate"] = hdr.get("surrogate")
    # A20 timing
    o["A20_t4_nan_fit"] = int(T.tempo_fit_s.isna().sum())
    o["A20_t4_nan_busca"] = int(T.tempo_busca_s.isna().sum())
    o["A20_t4_nan_sonda"] = int(T.tempo_pred_sonda_s.isna().sum())
    tg4 = T.sort_values("geracao").tempo_geracao_s.values.astype(float)
    tg6 = np.array([g["tempo_geracao_s"] for g in gens], dtype=float)
    o["A20_dt_max"] = float(np.abs(tg4 - tg6).max()) if len(tg4) == len(tg6) else np.nan
    o["A20_soma4"] = float(np.nansum(tg4))
    o["A20_total"] = float(man["timing"]["tempo_total_s"])
    o["A20_aval"] = float(man["timing"]["tempo_aval_real_s"] or np.nan)
    o["A20_soma4_le_total"] = int(o["A20_soma4"] <= o["A20_total"])
    # A22/A23 contrato
    o["A22_params_chaves"] = len(man["params"])
    o["A22_n_footer"] = len(foot)
    o["A22_termino"] = foot[0].get("termino")
    o["A22_status"] = man["status"]
    o["A23_repo_hash"] = man.get("repo_hash", "")
    o["T11_campanha_id"] = man.get("campanha_id", "<AUSENTE>")
    o["T11_schema"] = man.get("schema_version")
    o["T11_gerderiv_prefixo"] = man["params"]["geracoes_derivadas"][:24]
    return o


linhas = []
for prob in sorted(os.listdir(S42)):
    d = os.path.join(S42, prob, "42")
    if os.path.isdir(d):
        linhas.append(analisa(d, prob, "s42"))
linhas.append(analisa(SMK, "DTLZ2", "smokeT11"))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "mecanismo_t11.csv"), index=False)
s = df[df.fonte == "s42"]
print("=== s42 (%d celulas) — agregados ===" % len(s))
bools = [c for c in df.columns if c.startswith(("A", "T11")) and
         df[c].dtype != object and set(np.unique(s[c].dropna())) <= {0, 1}]
for c in bools:
    print("  %-26s %d/%d" % (c, int(s[c].sum()), len(s)))
print()
print("  A5_dW  max = %r     A2_dX max = %r" % (float(s.A5_dW.max()), float(s.A2_dX.max())))
print("  A7 conjunto igual: %d/25 (falhas: %s)" % (int(s.A7_conjunto_igual.sum()),
      list(s[s.A7_conjunto_igual == 0].prob)))
print("  A10 fecha: %d/25 · dup_off total = %d · off_full total = %d"
      % (int(s.A10_fecha.sum()), int(s.A10_dup_off.sum()), int(s.A10_off_full.sum())))
print("  A12 colisoes float32 = %d em %d linhas de ①" % (int(s.A12_colisoes.sum()),
      int(s.A2_n_init.sum() + s.A2_n_opt.sum())))
print("  A13 cache-hits de semeadura = %d · A21 total guards cache = %d"
      % (int(s.A13_ch_init.sum()), int(s.A21_ch_jsonl.sum())))
print("  A18 nao-monotonias = %d em %d transicoes" % (int(s.A18_nao_monotonias.sum()),
      int(s.A18_transicoes.sum())))
print("  A20 soma4 = %.2f s · total = %.2f s (%.1f%%) · aval = %.2f s"
      % (s.A20_soma4.sum(), s.A20_total.sum(),
         100 * s.A20_soma4.sum() / s.A20_total.sum(), s.A20_aval.sum()))
print("  geracoes: %d · |②| = %d · |①| = %d" % (s.A14_ngen_ev.sum(),
      s.A8_grupos2.sum() * 0 + int((s.A8_grupos2 * s.Nef).sum()), int(s.A2_n_init.sum() + s.A2_n_opt.sum())))
print("  A23 repo_hash unicos: %s" % sorted(set(s.A23_repo_hash)))
print("  T11 campanha_id unicos: %s · schema %s" % (sorted(set(s.T11_campanha_id)), sorted(set(s.T11_schema))))
print("  ger_deriv prefixo: %s" % sorted(set(s.T11_gerderiv_prefixo)))
print()
print("=== SMOKE T11 ===")
k = df[df.fonte == "smokeT11"].iloc[0]
for c in df.columns:
    print("  %-26s %r" % (c, k[c]))
