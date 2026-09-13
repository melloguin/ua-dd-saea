"""F5.4 · sobol_batch-S23 · R3 — os 4 campos "ausentes": presentes, recuperaveis
ou perdidos?  E qual teria sido o CUSTO de gravar cada um no laco quente.

(1) `ideal`  : o `f_best` logado E o ideal?  (piso_instrument.m:38,58 define
               `ideal` == `f_best` == min por objetivo)  -> comparacao exata.
(2) `n_front1`, `nadir_front1`, `nadir_pop`: recomputados da ① nas 1.000
    geracoes, com a MESMA funcao que o helper canonico usa
    (`problems._nds_filter`, regra A-8 `len`, nunca `count_nonzero`).
(3) Custo: cronometra o recomputo por geracao -> quanto o log teria somado ao
    wall do run (3,16-6,82 s medidos).
(4) `nadir_pop` do piso e degenerado? (max cumulativo => monotono nao-decrescente)
"""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src import problems as _problems

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/sobol_batch"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S23"
CELLS = ["q10_DTLZ2", "q10_MMF16_20", "q10_WFG9", "q10_ZDT1", "q10_ZDT4"]

rows, gen_rows = [], []
for cell in CELLS:
    prob = cell[4:]
    d = os.path.join(ROOT, cell, "42")
    real = [f for f in os.listdir(d) if f.endswith("__real.parquet")][0]
    jl = [f for f in os.listdir(d) if f.endswith(".jsonl")][0]
    df1 = pd.read_parquet(os.path.join(d, real)).sort_values("fe_index")
    fcols = [c for c in df1.columns if c.startswith("f") and c[1:].isdigit()]
    F = df1[fcols].to_numpy(dtype=np.float64)
    gens = []
    with open(os.path.join(d, jl)) as fh:
        for ln in fh:
            e = json.loads(ln)
            if e.get("rec") == "decision" and e.get("caminho") == "sobol_batch_gen":
                gens.append(e)
    assert len(gens) == 200, (cell, len(gens))

    d_ideal_max = 0.0
    t_nds = 0.0
    nf1, nadp, nadf1 = [], [], []
    for e in gens:
        fe = int(e["fe"])
        Fg = F[:fe]                       # "populacao" do piso == arquivo (S17)
        ideal_rec = Fg.min(axis=0)
        d_ideal_max = max(d_ideal_max,
                          float(np.max(np.abs(ideal_rec - np.asarray(e["f_best"])))))
        t0 = time.perf_counter()
        idx = _problems._nds_filter(Fg)
        t_nds += time.perf_counter() - t0
        n1 = int(len(idx))
        nf1.append(n1)
        nadp.append(Fg.max(axis=0))
        nadf1.append(Fg[idx].max(axis=0))
        gen_rows.append(dict(problema=prob, geracao=int(e["geracao"]), fe=fe,
                             n_front1_rec=n1))
    nadp = np.asarray(nadp); nadf1 = np.asarray(nadf1)
    # monotonicidade do nadir_pop (max cumulativo => nao-decrescente por construcao)
    mono_nadp = int(np.all(np.diff(nadp, axis=0) >= -1e-12))
    mono_nadf1 = int(np.all(np.diff(nadf1, axis=0) >= -1e-12))
    # wall real do run
    man = json.load(open(os.path.join(
        d, [f for f in os.listdir(d) if f.endswith("manifest.json")][0])))
    tt = man.get("timing", {}).get("tempo_total_s") or man.get("tempo_total_s")
    rows.append(dict(
        problema=prob, D=len([c for c in df1.columns if c.startswith("x") and c[1:].isdigit()]),
        M=len(fcols), n_linhas_1=len(df1), n_gen=len(gens),
        delta_ideal_vs_fbest_max=d_ideal_max,
        n_front1_min=int(min(nf1)), n_front1_max=int(max(nf1)),
        n_front1_final=int(nf1[-1]),
        nadir_pop_monotono=mono_nadp, nadir_front1_monotono=mono_nadf1,
        custo_nds_200gen_s=round(t_nds, 3),
        tempo_total_s=tt,
        overhead_pct=round(100 * t_nds / float(tt), 1) if tt else None))

R = pd.DataFrame(rows)
R.to_csv(os.path.join(OUT, "r3_recuperabilidade.csv"), index=False)
pd.DataFrame(gen_rows).to_csv(os.path.join(OUT, "r3_n_front1_recomputado.csv"), index=False)
pd.set_option("display.width", 220, "display.max_columns", 40)
print(R.to_string(index=False))
