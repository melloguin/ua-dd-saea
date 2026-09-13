#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 13: fechamentos finais.
(A) LEDGER PÓS-INFILL: f_best(g) == norm_min(g+1) e n_front1(g) == n_front(g+1)
    (os dois campos do (6) sao gravados DEPOIS da avaliacao real -> qualquer query que os
    leia como "pre-infill" erra; armadilha p/ o protocolo);
(B) escada norm_min/norm_max monotona (min nao-crescente, max nao-decrescente);
(C) comparacao canonica: recorte dos 4 problemas do paper presentes no grid + regua de
    orcamento/dimensao;
(D) totais da campanha.
Saidas: ledger_posinfill.csv, canonica.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
F5 = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
OUT = f"{F5}/baterias/c238"

rows = []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    recs = [json.loads(l) for l in open(f"{b}.jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    M, D = hdr["M"], hdr["D"]
    G = [r for r in recs if r.get("rec") == "c238_gen"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    fb = np.array([r["f_best"] for r in G], float)
    nm = np.array([r["norm_min"] for r in G], float)
    nx = np.array([r["norm_max"] for r in G], float)
    nf = np.array([r["n_front"] for r in G], int)
    nf1 = np.array([r["n_front1"] for r in G], int)
    namo = np.array([r["n_amostra"] for r in G], int)
    ymin_pos = np.array([F[:n + 1].min(0) for n in namo])   # ideal APOS o infill
    ymax_pos = np.array([F[:n + 1].max(0) for n in namo])
    rows.append(dict(
        problema=prob, D=D, M=M, n_gens=len(G),
        fbest_eq_nmin_prox=int((np.abs(fb[:-1] - nm[1:]) <= 0).all(1).sum()), n_pares=len(G) - 1,
        fbest_eq_ymin_pos=float(np.abs(fb - ymin_pos).max()),
        nmin_eq_ymin_pre=float(np.abs(nm - np.array([F[:n].min(0) for n in namo])).max()),
        nf1_eq_nf_prox=int((nf1[:-1] == nf[1:]).sum()),
        nmin_naocresce=int((np.diff(nm, axis=0) <= 0).all(1).sum()),
        nmax_naodecresce=int((np.diff(nx, axis=0) >= 0).all(1).sum()),
        maxfe=31 * D - 1, init=11 * D - 1, pool=10 * D,
        aval_aquis=200 * 10 * D * len(G), linhas_pool=10 * D * len(G)))
    print("OK", prob, flush=True)

L = pd.DataFrame(rows); L.to_csv(f"{OUT}/ledger_posinfill.csv", index=False)
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
print(L.to_string(index=False))
print("\nf_best(g)==norm_min(g+1):", L.fbest_eq_nmin_prox.sum(), "/", L.n_pares.sum())
print("n_front1(g)==n_front(g+1):", L.nf1_eq_nf_prox.sum(), "/", L.n_pares.sum())
print("max|f_best - ymin POS-infill|:", L.fbest_eq_ymin_pos.max())
print("max|norm_min - ymin PRE-infill|:", L.nmin_eq_ymin_pre.max())
print("norm_min nao-cresce:", L.nmin_naocresce.sum(), "/", L.n_pares.sum(),
      "| norm_max nao-decresce:", L.nmax_naodecresce.sum(), "/", L.n_pares.sum())
print("\nTOTAIS: FE reais", L.maxfe.sum(), "| gens", L.n_gens.sum(),
      "| linhas de pool", L.linhas_pool.sum(), "| aval. de aquisicao", L.aval_aquis.sum())

# (C) comparacao canonica
met = pd.read_csv(f"{F5}/metricas_finais_f52c.csv")
main = met[met.exp == "main"]
PAPER = {"ZDT1": dict(m=2, n=6, fe=100, doe=65, igd_med=0.0181, igd_mean=0.0178, hv=120.64),
         "ZDT3": dict(m=2, n=6, fe=100, doe=65, igd_med=0.0380, igd_mean=0.0425, hv=128.24),
         "DTLZ2": dict(m=3, n=6, fe=200, doe=65, igd_med=None, igd_mean=None, hv=15.026),
         "DTLZ7": dict(m=3, n=6, fe=200, doe=65, igd_med=None, igd_mean=None, hv=None)}
can = []
for p, d in PAPER.items():
    m = main[(main.alg == "c238") & (main.problema == p)].iloc[0]
    sub = main[main.problema == p]
    D = int(L[L.problema == p].D.iloc[0]); Mo = int(L[L.problema == p].M.iloc[0])
    can.append(dict(problema=p, nosso_D=D, nosso_M=Mo, paper_n=d["n"], paper_m=d["m"],
                    nosso_fe=31 * D - 1, paper_fe=d["fe"],
                    nosso_doe_frac=(11 * D - 1) / (31 * D - 1), paper_doe_frac=d["doe"] / d["fe"],
                    fe_por_dim_nosso=(31 * D - 1) / D, fe_por_dim_paper=d["fe"] / d["n"],
                    razao_D=D / d["n"], razao_fe=(31 * D - 1) / d["fe"],
                    nosso_igd=m.igd, nosso_igdplus=m.igd_plus, nosso_hv=m.hv,
                    paper_igd_med=d["igd_med"], paper_hv=d["hv"],
                    rank=int((sub.igd_plus.values < m.igd_plus).sum()) + 1, n_algs=len(sub)))
C = pd.DataFrame(can); C.to_csv(f"{OUT}/canonica.csv", index=False)
print("\n", C.to_string(index=False))
