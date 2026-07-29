#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 3: sonda (U5 join posicional + U6 WAPE/cobertura recomputados
no espaco CRU) e curva de calibracao por bloco. Confere contra f5/sonda_f52e.csv (pre-computado).
Saidas: sonda_join.csv (1 linha/celula) + sonda_blocos.csv (1 linha/celula x bloco x objetivo).
"""
import json, os
import warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
SOND = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"


def do_cell(prob):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    man = json.load(open(f"{b}.manifest.json"))
    hdr = json.loads(open(f"{b}.jsonl").readline())
    M, D = hdr["M"], hdr["D"]
    gab = pq.read_table(f"{SOND}/sonda_{prob}.parquet").to_pandas()
    xg = [c for c in gab.columns if c.startswith("x")]
    fg = [c for c in gab.columns if c.startswith("f")]
    Xg = gab[xg].values.astype(np.float64)
    Fg = gab[fg].values.astype(np.float64)
    cols = ["regime", "geracao"] + [f"x{i}" for i in range(D)] + \
           [f"mu_{i}" for i in range(M)] + [f"sigma_{i}" for i in range(M)] + ["fe_treino_max"]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    so = sur[sur.regime == "sonda"]
    S = man["sonda"]["S"]
    dxmax = 0.0
    rows = []
    for bi, (g, sub) in enumerate(so.groupby("geracao"), start=1):
        Xs = sub[[f"x{i}" for i in range(D)]].values.astype(np.float64)
        dx = np.abs(Xs - Xg[:len(Xs)]).max()
        dxmax = max(dxmax, dx)
        mu = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        sg = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        for j in range(M):
            e = mu[:, j] - Fg[:len(Xs), j]
            rows.append(dict(problema=prob, bloco=bi, geracao=int(g), obj=j,
                             wape=float(np.abs(e).sum() / max(np.abs(Fg[:len(Xs), j]).sum(), 1e-300)),
                             correl=float(np.corrcoef(mu[:, j], Fg[:len(Xs), j])[0, 1]),
                             cob=float((np.abs(e) <= 1.96 * sg[:, j]).mean()),
                             mu_max=float(np.abs(mu[:, j]).max()), sig_med=float(np.median(sg[:, j])),
                             fe_treino_max=int(sub.fe_treino_max.iloc[0]), n=len(Xs)))
    B = pd.DataFrame(rows)
    n_bl = B.bloco.nunique()
    p = B[B.bloco == 1]; u = B[B.bloco == n_bl]
    res = dict(problema=prob, D=D, M=M, n_blocos=n_bl, S=S,
               u5_dx_max=dxmax, u5_ok=dxmax <= np.finfo(np.float32).eps * 10,
               wape_1=float(p.wape.median()), wape_n=float(u.wape.median()),
               dwape=float(u.wape.median() / max(p.wape.median(), 1e-300) - 1),
               corr_1=float(p.correl.median()), corr_n=float(u.correl.median()),
               cob_1=float(p.cob.median()), cob_n=float(u.cob.median()),
               mu_max=float(B.mu_max.max()), sig_med_1=float(p.sig_med.median()),
               sig_med_n=float(u.sig_med.median()),
               wape_min=float(B.groupby("bloco").wape.median().min()),
               wape_min_bloco=int(B.groupby("bloco").wape.median().idxmin()),
               cob_max=float(B.groupby("bloco").cob.median().max()))
    return res, B


if __name__ == "__main__":
    rows, blocos = [], []
    for prob in sorted(os.listdir(BASE)):
        r, B = do_cell(prob)
        rows.append(r); blocos.append(B)
        print("OK", prob, f"dx={r['u5_dx_max']:.3e} wape {r['wape_1']:.3f}->{r['wape_n']:.3f} "
                          f"cob {r['cob_1']:.2f}->{r['cob_n']:.2f}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/sonda_join.csv", index=False)
    pd.concat(blocos).to_csv(f"{OUT}/sonda_blocos.csv", index=False)
    # confronto com o pre-computado f5/sonda_f52e.csv
    pre = pd.read_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/sonda_f52e.csv")
    pre = pre[(pre.alg == "c238") & (pre.exp == "main")]
    mine = pd.concat(blocos)
    pre = pre.rename(columns={"bloco": "geracao"})
    pre["geracao"] = pre.geracao.astype(int)
    mg = pre.merge(mine, on=["problema", "geracao", "obj"], suffixes=("_pre", "_meu"))
    d1 = (mg.wape_pre - mg.wape_meu).abs().max()
    d2 = (mg.cobertura95 - mg.cob).abs().max()
    print(f"\nconfronto f5/sonda_f52e.csv: n={len(mg)} maxdif WAPE={d1:.3e} maxdif cobertura={d2:.3e}")
