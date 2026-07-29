#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 5: papel da incerteza (contrafactual sigma->0) e
monotonicidade N2 do paper, medidos no pool FINAL do GA de TODAS as geracoes.
- EIM_e completa  vs  EIM_e com s->0+ (colapsa em min_j ||max(F^j-u,0)||_2 = melhoria PREDITA):
  em quantas geracoes o argmax MUDA => sigma decidiu o infill.
- N2 (paper §IV-C): s maior => EIM maior. Testa s*1.01 no proprio pool.
Saidas: contrafactual.csv
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


def eim_greedy(u, Fr):
    E = np.maximum(Fr[None, :, :] - u[:, None, :], 0.0)
    return np.sqrt((E ** 2).sum(2)).min(1)


rows = []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    gens = {r["geracao"]: r for r in recs if r.get("rec") == "c238_gen"}
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))
    muda = 0; n2ok = 0; tot = 0; frac_expl = []; greedy_zero = 0
    for g, r in gens.items():
        Y = F[:r["n_amostra"]]
        Fr = (Y[b2.nd_weak_seq(Y)] - np.array(r["norm_min"])) / np.array(r["norm_range_efetivo"])
        sub = grp[g]
        u = sub[[f"mu_{i}" for i in range(M)]].values.astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values.astype(np.float64)
        v = b2.eim_euclidean(u, s, Fr)
        vg = eim_greedy(u, Fr)
        v2 = b2.eim_euclidean(u, s * 1.01, Fr)
        tot += 1
        if int(np.argmax(vg)) != int(np.argmax(v)):
            muda += 1
        if (v2 >= v - 1e-15).all():
            n2ok += 1
        if vg.max() <= 0:
            greedy_zero += 1
        # fracao do criterio que vem do termo de exploracao, no ponto escolhido
        j = int(np.argmax(v))
        frac_expl.append(1.0 - vg[j] / max(v[j], 1e-300))
    rows.append(dict(problema=prob, D=D, M=M, n_gens=tot,
                     argmax_muda_sem_sigma=muda, frac_muda=muda / tot,
                     n2_monotona=n2ok, frac_n2=n2ok / tot,
                     greedy_totalmente_zero=greedy_zero,
                     frac_exploracao_med=float(np.median(frac_expl)),
                     frac_exploracao_min=float(np.min(frac_expl))))
    print("OK", prob, rows[-1]["frac_muda"], rows[-1]["frac_n2"],
          round(rows[-1]["frac_exploracao_med"], 4), flush=True)
S = pd.DataFrame(rows)
S.to_csv(f"{OUT}/contrafactual.csv", index=False)
print(S.to_string(index=False))
print("\nTOTAIS: gens", S.n_gens.sum(), "| argmax muda sem sigma:", S.argmax_muda_sem_sigma.sum(),
      f"({S.argmax_muda_sem_sigma.sum()/S.n_gens.sum():.1%})",
      "| N2 monotona:", S.n2_monotona.sum(), "| greedy identicamente 0:", S.greedy_totalmente_zero.sum())
