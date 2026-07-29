#!/usr/bin/env python
"""bateria2_e81 — a AMBIGUIDADE B17.5 dissecada por dado (top-q x Eq.6-greedy),
o fallback qmaximin DI-25 ponto a ponto, a semantica de dist_min_arquivo,
a saturacao do front do NSGA-II interno e a nao-unicidade do ranking maximin.

READ-ONLY. Saidas: e81_b175_contrafactual.csv · e81_fallback_pontos.csv ·
e81_front_saturacao.csv · e81_distmin_semantica.csv
"""
import json, os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")


def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out


def decisions(path):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            if o.get("rec") == "decision":
                out.append(o)
    return out


def greedy_eq6(cand01, ds01, q):
    """Eq. 6 LITERAL: sequencia de subproblemas maximin COM diversidade mutua.
    x_{n+k} = argmax_x min( min_j gamma(x, X_obs_j), min_{l<k} gamma(x, x_{n+l}) )"""
    d = cdist(cand01, ds01).min(axis=1)
    sel = []
    cur = d.copy()
    for _ in range(q):
        i = int(np.argmax(cur))
        sel.append(i)
        cur = np.minimum(cur, cdist(cand01, cand01[i:i + 1]).ravel())
        cur[i] = -np.inf
    return sel


rows_cf, rows_fbp, rows_sat, rows_dm, rows_emp = [], [], [], [], []

for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    dec = decisions(base + ".jsonl")
    real = pd.read_parquet(base + "__real.parquet")
    sur = pd.read_parquet(base + "__surrogate.parquet")
    D = int(man["params"]["qpots_kwargs"]["dim"]); q = int(man["q"])
    M = len([c for c in real.columns if c.startswith("f")])
    xcols = [f"x{i}" for i in range(D)]
    dm = json.load(open(f"{REPO}/data/doe/{prob}/doe_{prob}_42.manifest.json"))
    xl = np.array(dm["bounds"]["xl"], float); xu = np.array(dm["bounds"]["xu"], float)
    rng = xu - xl
    pop_nsga = int(man["params"]["nsga2_interno"]["pop"])

    onl = {g: v for g, v in sur[sur["regime"] == "online"].groupby("geracao")}
    Xnat = real[xcols].values.astype(np.float64)
    X01 = (Xnat - xl) / rng

    n_cf_diff = n_cf_same = 0
    n_sat = 0
    dm_rel_err = []
    empates = 0
    for o in dec:
        g = o["geracao"]; nfa = int(o["n_front_acq"]); ntr = int(o["n_train"])
        idx = list(o["idx_escolhidos"]); mm = np.array(o["maximin_escolhido"], float)
        blk = onl[g]
        cand01 = (blk[xcols].values.astype(np.float64) - xl) / rng
        ds01 = X01[:ntr]
        dmin = cdist(cand01, ds01).min(axis=1)
        fb = (len(blk) != nfa)
        # saturacao do front
        if nfa >= pop_nsga:
            n_sat += 1
        # semantica de dist_min_arquivo (espaco NATIVO x [0,1]^D)
        dnat = cdist(blk[xcols].values.astype(np.float64), Xnat[:ntr]).min(axis=1)
        dma = float(o["dist_min_arquivo"])
        dm_rel_err.append(abs(float(np.max(dnat[np.array(idx)])) - dma) / max(dma, 1e-12))
        # empates numericos no ranking maximin (top-q vs (q+1)-esimo)
        if not fb and len(dmin) > q:
            srt = np.sort(dmin)
            if abs(srt[-q] - srt[-q - 1]) <= 1e-12 * max(1.0, abs(srt[-q])):
                empates += 1
        # contrafactual B17.5 (so onde q>1 e ha folga: len(front) > q)
        if q > 1 and not fb and len(dmin) > q:
            topq = sorted(np.argsort(dmin, kind="stable")[-q:].tolist())
            gr = sorted(greedy_eq6(cand01, ds01, q))
            if topq == gr:
                n_cf_same += 1
            else:
                n_cf_diff += 1
                if n_cf_diff <= 3:
                    tq = set(topq); gg = set(gr)
                    rows_cf.append(dict(label=lab, geracao=g, tipo="exemplo",
                                        n_front=nfa, topq=str(sorted(tq)), greedy=str(sorted(gg)),
                                        so_topq=str(sorted(tq - gg)), so_greedy=str(sorted(gg - tq)),
                                        n_diferentes=len(tq ^ gg) // 2,
                                        dmin_min_topq=float(dmin[list(tq)].min()),
                                        dmin_min_greedy=float(dmin[list(gg)].min()),
                                        # dispersao mutua do lote (em [0,1]^D)
                                        sep_mutua_topq=float(cdist(cand01[list(tq)], cand01[list(tq)])[
                                            np.triu_indices(q, 1)].min()),
                                        sep_mutua_greedy=float(cdist(cand01[list(gg)], cand01[list(gg)])[
                                            np.triu_indices(q, 1)].min())))
        # fallback: pontos de completacao
        if fb:
            nfill = len(blk) - nfa
            selec01 = cand01[:nfa]
            fill01 = cand01[nfa:]
            for k in range(nfill):
                p = fill01[k:k + 1]
                dds = float(cdist(p, ds01).min())
                dsel = float(cdist(p, selec01).min())
                dprev = float(cdist(p, fill01[:k]).min()) if k > 0 else np.nan
                rows_fbp.append(dict(label=lab, geracao=g, n_front_acq=nfa, k=k,
                                     dist_dataset01=dds, dist_selecionados01=dsel,
                                     dist_completados_prev01=dprev,
                                     dist_min_global01=min(dds, dsel,
                                                           dprev if dprev == dprev else np.inf),
                                     marcado=bool(blk["real_solution_id"].notna().values[nfa + k])))
    rows_sat.append(dict(label=lab, exp=exp, problema=prob, D=D, q=q, pop_nsga=pop_nsga,
                         n_ger=len(dec), n_front_saturado=n_sat,
                         front_max=int(max(o["n_front_acq"] for o in dec)),
                         front_med=float(np.median([o["n_front_acq"] for o in dec])),
                         front_min=int(min(o["n_front_acq"] for o in dec)),
                         front_frac_pop_med=float(np.median([o["n_front_acq"] for o in dec]) / pop_nsga),
                         empates_topq=empates))
    rows_dm.append(dict(label=lab, exp=exp, problema=prob, D=D, q=q,
                        dist_min_arquivo_rel_err_max=float(np.max(dm_rel_err)),
                        razao_nativo_norm=float(np.median(rng)) if np.ptp(rng) == 0 else np.nan,
                        bounds_heterogeneos=bool(np.ptp(rng) > 0),
                        rng_min=float(rng.min()), rng_max=float(rng.max())))
    if q > 1:
        rows_cf.append(dict(label=lab, geracao=-1, tipo="RESUMO", n_front=-1,
                            topq="", greedy="", so_topq="", so_greedy="",
                            n_diferentes=n_cf_diff,
                            dmin_min_topq=n_cf_same, dmin_min_greedy=len(dec),
                            sep_mutua_topq=np.nan, sep_mutua_greedy=np.nan))
    print(f"OK {lab:16s} cf_diff={n_cf_diff} cf_same={n_cf_same} sat={n_sat} "
          f"empates={empates} dm_rel_max={np.max(dm_rel_err):.2e}", flush=True)

pd.DataFrame(rows_cf).to_csv(f"{OUT}/e81_b175_contrafactual.csv", index=False)
pd.DataFrame(rows_fbp).to_csv(f"{OUT}/e81_fallback_pontos.csv", index=False)
pd.DataFrame(rows_sat).to_csv(f"{OUT}/e81_front_saturacao.csv", index=False)
pd.DataFrame(rows_dm).to_csv(f"{OUT}/e81_distmin_semantica.csv", index=False)
print("\nescrito em", OUT)
