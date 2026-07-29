#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 10: qual semantica de nao-dominancia reproduz `n_front`?
3 candidatas sobre o arquivo pre-infill (float32 da (1)):
  weak-seq : rotina do paper (`paretofront` FEX-17251), dominancia FRACA com varredura
             sequencial -> duplicatas exatas COLAPSAM na primeira;
  std      : i cai sse exists j com (Yj<=Yi).all e (Yj<Yi).any -> duplicatas SOBREVIVEM;
  strict   : i cai sse exists j com (Yj<Yi).all -> so dominancia estrita.
E teste de RECONSTRUCAO por adicao: quando n_front_log > nd_weak, devolve a frente os
(log - weak) pontos de MAIOR margem entre os excluidos e refaz a identidade EIM.
Saidas: front_semantica.csv (celulas discordantes: DTLZ4, MMF11_L, ZDT6 + controles)
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)
BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
ALVO = ["DTLZ4", "MMF11_L", "ZDT6", "WFG5", "ZDT1"]


def nd_std_mask(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y <= Y[i]).all(1) & (Y < Y[i]).any(1)).any():
            keep[i] = False
    return keep


def nd_strict_mask(Y):
    keep = np.ones(len(Y), bool)
    for i in range(len(Y)):
        if ((Y < Y[i]).all(1)).any():
            keep[i] = False
    return keep


def margens(Y):
    n = len(Y); Mg = np.empty(n)
    for i in range(n):
        d = (Y[i] - Y).max(1); d[i] = np.inf; Mg[i] = d.min()
    return Mg


rows = []
for prob in ALVO:
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M = hdr["M"]
    G = [r for r in recs if r.get("rec") == "c238_gen"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))
    for r in G:
        Y = F[:r["n_amostra"]]
        wk = b2.nd_weak_seq(Y); st = nd_std_mask(Y); sr = nd_strict_mask(Y)
        nlog = r["n_front"]
        mn = np.array(r["norm_min"]); rg = np.array(r["norm_range_efetivo"])
        sub = grp[r["geracao"]]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        eb = r["eim_best"]; den = max(abs(eb), 1e-300)
        rel = {}
        for nome, mk in (("weak", wk), ("std", st), ("strict", sr)):
            Fr = (Y[mk] - mn) / rg
            rel[nome] = abs(float(b2.eim_euclidean(u, s, Fr).max()) - eb) / den
        # reconstrucao por ADICAO
        rel_add = np.nan; n_add_dup = -1
        k = nlog - int(wk.sum())
        if k > 0:
            mg = margens(Y)
            fora = np.flatnonzero(~wk)
            add = fora[np.argsort(-mg[fora])][:k]
            keep = np.union1d(np.flatnonzero(wk), add)
            Fr = (Y[keep] - mn) / rg
            rel_add = abs(float(b2.eim_euclidean(u, s, Fr).max()) - eb) / den
            # quantos dos adicionados sao DUPLICATA EXATA de um ponto ja na frente
            n_add_dup = int(sum(bool(((Y[np.flatnonzero(wk)] == Y[a]).all(1)).any()) for a in add))
        rows.append(dict(problema=prob, geracao=r["geracao"], n=r["n_amostra"],
                         n_front_log=nlog, weak=int(wk.sum()), std=int(st.sum()),
                         strict=int(sr.sum()),
                         bate_weak=int(wk.sum()) == nlog, bate_std=int(st.sum()) == nlog,
                         bate_strict=int(sr.sum()) == nlog,
                         rel_weak=rel["weak"], rel_std=rel["std"], rel_strict=rel["strict"],
                         rel_add=rel_add, k_add=k, n_add_dup=n_add_dup))
    print("OK", prob, flush=True)

A = pd.DataFrame(rows); A.to_csv(f"{OUT}/front_semantica.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60)
g = A.groupby("problema")
print(pd.DataFrame(dict(
    n=g.size(), bate_weak=g.bate_weak.sum(), bate_std=g.bate_std.sum(), bate_strict=g.bate_strict.sum(),
    k_med=g.k_add.median(), k_max=g.k_add.max(), add_dup_med=g.n_add_dup.median(),
    rel_weak_lt1e5=g.apply(lambda x: int((x.rel_weak < 1e-5).sum()), include_groups=False),
    rel_std_lt1e5=g.apply(lambda x: int((x.rel_std < 1e-5).sum()), include_groups=False),
    rel_strict_lt1e5=g.apply(lambda x: int((x.rel_strict < 1e-5).sum()), include_groups=False),
    rel_add_lt1e5=g.apply(lambda x: int((x.rel_add < 1e-5).sum()), include_groups=False),
    rel_add_med=g.rel_add.median(), rel_add_max=g.rel_add.max(),
)).to_string())
