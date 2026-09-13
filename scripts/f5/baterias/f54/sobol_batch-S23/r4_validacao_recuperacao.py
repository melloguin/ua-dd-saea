"""F5.4 · sobol_batch-S23 · R4 — a recuperacao a-posteriori e EXATA?

Prova de que `n_front1` recomputado da ① reproduz o valor que o helper canonico
teria gravado: aplico o MESMO recomputo aos rivais do MESMO sub-estudo
(e81/c149 batch, que passam `F_arc` a `minimo_comum_di10`) e comparo com o
`n_front1` LOGADO. Se casar 100%, entao o mesmo recomputo aplicado ao
sobol_batch recupera o campo sem perda -> o defeito e de INSTRUMENTACAO, nao de
informacao.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import problems as _problems

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S23"
CELLS = ["q10_DTLZ2", "q10_MMF16_20", "q10_WFG9", "q10_ZDT1", "q10_ZDT4"]

rows = []
for alg in ["e81", "c149"]:
    for cell in CELLS:
        d = os.path.join(ROOT, alg, cell, "42")
        if not os.path.isdir(d):
            continue
        real = [f for f in os.listdir(d) if f.endswith("__real.parquet")][0]
        jl = [f for f in os.listdir(d) if f.endswith(".jsonl")][0]
        df1 = pd.read_parquet(os.path.join(d, real)).sort_values("fe_index")
        fcols = [c for c in df1.columns if c.startswith("f") and c[1:].isdigit()]
        F = df1[fcols].to_numpy(dtype=np.float64)
        ok = tot = 0
        difs = []
        with open(os.path.join(d, jl)) as fh:
            for ln in fh:
                e = json.loads(ln)
                if e.get("rec") != "decision" or "n_front1" not in e:
                    continue
                fe = int(e["fe"])
                rec = int(len(_problems._nds_filter(F[:fe])))
                tot += 1
                if rec == int(e["n_front1"]):
                    ok += 1
                else:
                    difs.append(rec - int(e["n_front1"]))
        rows.append(dict(alg=alg, problema=cell[4:], n_eventos=tot,
                         casam=ok, pct=round(100 * ok / tot, 2) if tot else None,
                         dif_med=(round(float(np.mean(difs)), 3) if difs else 0.0),
                         dif_absmax=(int(np.max(np.abs(difs))) if difs else 0)))

R = pd.DataFrame(rows)
R.to_csv(os.path.join(OUT, "r4_validacao_recuperacao.csv"), index=False)
pd.set_option("display.width", 200)
print(R.to_string(index=False))
print("\nTOTAL: %d/%d eventos (%.2f%%)" %
      (R.casam.sum(), R.n_eventos.sum(), 100 * R.casam.sum() / R.n_eventos.sum()))
