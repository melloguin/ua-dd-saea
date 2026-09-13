#!/usr/bin/env python
"""bateria4_e81 — mecanismo fino: (a) o contrafactual G5 do TS (Sigma->0) medido pela
amplitude dos draws; (b) assinatura exploratoria (dist_min_arquivo, sigma no escolhido);
(c) transicoes de fase do GP (saltos de cobertura/WAPE x lengthscale/outputscale);
(d) separacao mutua do lote top-q x Eq.6-greedy em TODAS as gens q=10;
(e) chave de ordenacao da completacao DI-25; (f) proximidade de dedup (D57);
(g) alinhamento posicional da 3a camada (contraste com o J27 do c154).

READ-ONLY. Saidas: e81_ts_draws.csv · e81_exploracao.csv · e81_transicoes.csv ·
e81_sepmutua.csv · e81_alinhamento.csv
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


def greedy_eq6(cand01, ds01, q):
    d = cdist(cand01, ds01).min(axis=1)
    sel, cur = [], d.copy()
    for _ in range(q):
        i = int(np.argmax(cur))
        sel.append(i)
        cur = np.minimum(cur, cdist(cand01, cand01[i:i + 1]).ravel())
        cur[i] = -np.inf
    return sel


rows_ts, rows_ex, rows_tr, rows_sm, rows_al, rows_fbord = [], [], [], [], [], []
rec = pd.read_csv(f"{OUT}/e81_sonda_recomputada.csv")

for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    dec = [json.loads(l) for l in open(base + ".jsonl") if '"rec": "decision"' in l]
    real = pd.read_parquet(base + "__real.parquet")
    sur = pd.read_parquet(base + "__surrogate.parquet")
    D = int(man["params"]["qpots_kwargs"]["dim"]); q = int(man["q"])
    M = len([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    xcols = [f"x{i}" for i in range(D)]
    dm = json.load(open(f"{REPO}/data/doe/{prob}/doe_{prob}_42.manifest.json"))
    xl = np.array(dm["bounds"]["xl"], float); xu = np.array(dm["bounds"]["xu"], float)
    rng = xu - xl
    Xnat = real[xcols].values.astype(np.float64); X01 = (Xnat - xl) / rng
    onl = {g: v for g, v in sur[sur["regime"] == "online"].groupby("geracao")}
    nG = len(dec)

    # ── (a) contrafactual G5: amplitude dos draws de Thompson ─────────────
    amp = np.array([np.mean(np.array(o["draws_thompson"]["max"]) -
                            np.array(o["draws_thompson"]["min"])) for o in dec])
    sg_sel = np.array([np.mean(np.abs(o["sigma_sel_nat"])) for o in dec])
    k = max(1, nG // 4)
    rows_ts.append(dict(label=lab, exp=exp, problema=prob, D=D, q=q, n_ger=nG,
                        amp_q1=float(np.median(amp[:k])), amp_q4=float(np.median(amp[-k:])),
                        amp_razao=float(np.median(amp[-k:]) / np.median(amp[:k])),
                        sg_sel_q1=float(np.median(sg_sel[:k])), sg_sel_q4=float(np.median(sg_sel[-k:])),
                        sg_sel_razao=float(np.median(sg_sel[-k:]) / np.median(sg_sel[:k])),
                        corr_amp_sg=float(np.corrcoef(amp, sg_sel)[0, 1]),
                        amp_min=float(amp.min()), amp_max=float(amp.max())))

    # ── (b) assinatura exploratoria ───────────────────────────────────────
    dma = np.array([o["dist_min_arquivo"] for o in dec])
    mmax = np.array([max(o["maximin_escolhido"]) for o in dec])   # em [0,1]^D
    mmin = np.array([min(o["maximin_escolhido"]) for o in dec])
    sg_glob = float(np.median(sur[sur["regime"] == "sonda"][[f"sigma_{j}" for j in range(M)]].values))
    sg_onl = float(np.median(sur[sur["regime"] == "online"][[f"sigma_{j}" for j in range(M)]].values))
    mk = sur[sur["real_solution_id"].notna()]
    sg_mk = float(np.median(mk[[f"sigma_{j}" for j in range(M)]].values))
    rows_ex.append(dict(label=lab, exp=exp, problema=prob, D=D, q=q,
                        mm_q1=float(np.median(mmax[:k])), mm_q4=float(np.median(mmax[-k:])),
                        mm_razao=float(np.median(mmax[-k:]) / np.median(mmax[:k])),
                        mm_min_global=float(mmin.min()), mm_max_global=float(mmax.max()),
                        dist_min_arquivo_min=float(dma.min()),
                        sigma_sonda_med=sg_glob, sigma_online_med=sg_onl, sigma_escolhido_med=sg_mk,
                        razao_sig_esc_sonda=sg_mk / sg_glob if sg_glob > 0 else np.nan,
                        razao_sig_esc_online=sg_mk / sg_onl if sg_onl > 0 else np.nan,
                        # diametro do dominio normalizado p/ escala
                        diam01=float(np.sqrt(D))))

    # ── (c) transicoes de fase (saltos de cobertura/WAPE) ─────────────────
    hp = {o["geracao"]: o["modelo_hp"] for o in dec}
    sub = rec[rec["label"] == lab]
    for j in range(M):
        s = sub[sub["obj"] == j].sort_values("ordem")
        cv = s["cobertura95"].values; wp = s["wape"].values; gg = s["bloco"].values
        for i in range(1, len(cv)):
            dcov = cv[i] - cv[i - 1]
            dw = (wp[i] - wp[i - 1]) / wp[i - 1] if wp[i - 1] > 0 else 0.0
            if abs(dcov) >= 0.15 or dw <= -0.25:
                h0 = hp.get(int(gg[i - 1])); h1 = hp.get(int(gg[i]))
                if h0 is None or h1 is None:
                    continue
                rows_tr.append(dict(label=lab, obj=j, bloco_de=int(gg[i - 1]), bloco_para=int(gg[i]),
                                    cob_de=cv[i - 1], cob_para=cv[i], dcob=dcov,
                                    wape_de=wp[i - 1], wape_para=wp[i], dwape=dw,
                                    ls_med_de=h0["por_objetivo"][j]["lengthscale_med"],
                                    ls_med_para=h1["por_objetivo"][j]["lengthscale_med"],
                                    ls_razao=h1["por_objetivo"][j]["lengthscale_med"] /
                                             h0["por_objetivo"][j]["lengthscale_med"],
                                    osc_de=h0["por_objetivo"][j]["outputscale"],
                                    osc_para=h1["por_objetivo"][j]["outputscale"],
                                    osc_razao=h1["por_objetivo"][j]["outputscale"] /
                                              h0["por_objetivo"][j]["outputscale"],
                                    sig_de=s["sigma_med"].values[i - 1], sig_para=s["sigma_med"].values[i]))

    # ── (d) separacao mutua do lote (q=10) + (e) ordem da completacao ─────
    if q > 1:
        sep_top, sep_gr, dmin_top, dmin_gr = [], [], [], []
        for o in dec:
            g = o["geracao"]; nfa = int(o["n_front_acq"]); ntr = int(o["n_train"])
            blk = onl[g]
            if len(blk) != nfa:      # fallback: ordem da completacao
                c01 = (blk[xcols].values.astype(np.float64) - xl) / rng
                ds01 = X01[:ntr]
                fill = c01[nfa:]
                dds = cdist(fill, ds01).min(axis=1)
                dsel = cdist(fill, c01[:nfa]).min(axis=1)
                pool = np.vstack([ds01, c01[:nfa]])
                dboth = cdist(fill, pool).min(axis=1)
                rows_fbord.append(dict(label=lab, geracao=g, n_front=nfa, n_fill=len(fill),
                                       asc_dataset=bool((np.diff(dds) >= 0).all()),
                                       asc_selecionados=bool((np.diff(dsel) >= 0).all()),
                                       asc_uniao=bool((np.diff(dboth) >= 0).all()),
                                       desc_dataset=bool((np.diff(dds) <= 0).all()),
                                       desc_selecionados=bool((np.diff(dsel) <= 0).all()),
                                       desc_uniao=bool((np.diff(dboth) <= 0).all()),
                                       d_dataset=str([round(v, 4) for v in dds]),
                                       d_selec=str([round(v, 4) for v in dsel]),
                                       d_uniao=str([round(v, 4) for v in dboth])))
                continue
            if len(blk) <= q:
                continue
            c01 = (blk[xcols].values.astype(np.float64) - xl) / rng
            ds01 = X01[:ntr]
            dmin = cdist(c01, ds01).min(axis=1)
            tq = np.argsort(dmin, kind="stable")[-q:]
            gr = np.array(greedy_eq6(c01, ds01, q))
            iu = np.triu_indices(q, 1)
            sep_top.append(float(cdist(c01[tq], c01[tq])[iu].min()))
            sep_gr.append(float(cdist(c01[gr], c01[gr])[iu].min()))
            dmin_top.append(float(dmin[tq].sum())); dmin_gr.append(float(dmin[gr].sum()))
        rows_sm.append(dict(label=lab, problema=prob, D=D, n=len(sep_top),
                            sep_top_med=float(np.median(sep_top)),
                            sep_greedy_med=float(np.median(sep_gr)),
                            razao_sep=float(np.median(sep_gr)) / float(np.median(sep_top)),
                            sep_top_pior=float(np.min(sep_top)),
                            sep_greedy_pior=float(np.min(sep_gr)),
                            greedy_mais_disperso=int(np.sum(np.array(sep_gr) > np.array(sep_top))),
                            soma_dmin_top_med=float(np.median(dmin_top)),
                            soma_dmin_greedy_med=float(np.median(dmin_gr)),
                            top_maximiza_soma=int(np.sum(np.array(dmin_top) >= np.array(dmin_gr) - 1e-12))))

    # ── (g) alinhamento posicional da 3a camada ───────────────────────────
    pos_rel, ultimo, primeiro = [], 0, 0
    for o in dec:
        g = o["geracao"]; nfa = int(o["n_front_acq"]); blk = onl[g]
        marked = np.where(blk["real_solution_id"].notna().values)[0]
        if len(blk) != nfa:
            continue
        for p in marked:
            pos_rel.append(p / max(1, len(blk) - 1))
        if (len(blk) - 1) in marked:
            ultimo += 1
        if 0 in marked:
            primeiro += 1
    rows_al.append(dict(label=lab, exp=exp, problema=prob, q=q, n_ger=nG,
                        pos_rel_med=float(np.median(pos_rel)),
                        pos_rel_p10=float(np.percentile(pos_rel, 10)),
                        pos_rel_p90=float(np.percentile(pos_rel, 90)),
                        gens_com_ultima_linha=ultimo, gens_com_primeira_linha=primeiro))
    print("ok", lab, flush=True)

pd.DataFrame(rows_ts).to_csv(f"{OUT}/e81_ts_draws.csv", index=False)
pd.DataFrame(rows_ex).to_csv(f"{OUT}/e81_exploracao.csv", index=False)
pd.DataFrame(rows_tr).to_csv(f"{OUT}/e81_transicoes.csv", index=False)
pd.DataFrame(rows_sm).to_csv(f"{OUT}/e81_sepmutua.csv", index=False)
pd.DataFrame(rows_al).to_csv(f"{OUT}/e81_alinhamento.csv", index=False)
pd.DataFrame(rows_fbord).to_csv(f"{OUT}/e81_fallback_ordem.csv", index=False)
print("\nescrito em", OUT)
