#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 7: (a) ledger da frente n_front1(g) == n_front(g+1) e taxa de
troca da frente (o motor do ruido do eim_best, DI-18); (b) saturacao EIM==0; (c) U11 erro de
fantasia do infill no ESPACO DO MODELO ([0,1] da iteracao); (d) mapa do salto tardio do ZDT1.
Saidas: frente_ledger.csv, fantasia_modelo.csv, zdt1_salto.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq
import importlib.util

spec = importlib.util.spec_from_file_location(
    "b2", "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238/b2_eim_identidade.py")
b2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b2)
BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"

rows, fant = [], []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    G = [json.loads(l) for l in open(f"{b}.jsonl") if '"c238_gen"' in l]
    hdr = json.loads(open(f"{b}.jsonl").readline()); M, D = hdr["M"], hdr["D"]
    real = pq.read_table(f"{b}__real.parquet").to_pandas()
    F = real[[f"f{i}" for i in range(M)]].values.astype(np.float64)
    nf = np.array([r["n_front"] for r in G]); nf1 = np.array([r["n_front1"] for r in G])
    ledger = int((nf1[:-1] == nf[1:]).sum())
    entrou = 0
    for r in G:
        n = r["n_amostra"]
        if n + 1 <= len(F):
            entrou += bool(b2.nd_weak_seq(F[:n + 1])[n])
    eb = np.array([r["eim_best"] for r in G])
    # fantasia no espaco do modelo
    cols = ["regime", "geracao", "real_solution_id"] + [f"mu_{i}" for i in range(M)] + \
           [f"sigma_{i}" for i in range(M)]
    sur = pq.read_table(f"{b}__surrogate.parquet", columns=cols).to_pandas()
    grp = dict(list(sur[sur.regime == "online"].groupby("geracao")))
    e_all, cob, otim = [], 0, 0
    for r in G:
        sub = grp[r["geracao"]]
        pos = np.where(sub.real_solution_id.values == r["infill_sid"])[0]
        j = int(pos[0]) if len(pos) else 0
        u = sub[[f"mu_{i}" for i in range(M)]].values[j].astype(np.float64)
        s = sub[[f"sigma_{i}" for i in range(M)]].values[j].astype(np.float64)
        mn = np.array(r["norm_min"]); rg = np.array(r["norm_range_efetivo"])
        y = (F[int(r["infill_sid"])] - mn) / rg          # verdade no espaco do modelo
        e = u - y
        e_all.append(np.abs(e)); cob += int((np.abs(e) <= 1.96 * s).sum()); otim += int((e < 0).sum())
    e_all = np.concatenate(e_all)
    fant.append(dict(problema=prob, M=M, n_gens=len(G), err_med=float(np.median(e_all)),
                     err_p90=float(np.percentile(e_all, 90)), err_max=float(e_all.max()),
                     cob_frac=cob / (len(G) * M), otim_frac=otim / (len(G) * M)))
    rows.append(dict(problema=prob, n_gens=len(G), ledger_ok=ledger, ledger_n=len(G) - 1,
                     infill_entra_frente=entrou, frac_entra=entrou / len(G),
                     nf_muda=int((nf1[:-1] != nf[:-1]).sum()),
                     eim_zero=int((eb == 0).sum()), eim_lt1e12=int((eb < 1e-12).sum()),
                     subidas=int((np.diff(eb) > 0).sum())))
    print("OK", prob, rows[-1], flush=True)
L = pd.DataFrame(rows); L.to_csv(f"{OUT}/frente_ledger.csv", index=False)
Fz = pd.DataFrame(fant); Fz.to_csv(f"{OUT}/fantasia_modelo.csv", index=False)
print(L.to_string(index=False))
print("\nledger n_front1(g)==n_front(g+1):", int(L.ledger_ok.sum()), "/", int(L.ledger_n.sum()))
print("infill ENTRA na frente:", int(L.infill_entra_frente.sum()), "/", int(L.n_gens.sum()),
      f"({L.infill_entra_frente.sum()/L.n_gens.sum():.1%})")
print("gens com eim_best == 0 exato:", int(L.eim_zero.sum()), "| < 1e-12:", int(L.eim_lt1e12.sum()))
print("\n", Fz.to_string(index=False))
print("erro de fantasia (espaco do modelo) mediano global:", f"{Fz.err_med.median():.4f}",
      "| cobertura 1,96s mediana:", f"{Fz.cob_frac.median():.3f}",
      "| otimista mediano:", f"{Fz.otim_frac.median():.3f}")

# ZDT1: mapa do salto tardio
G = [json.loads(l) for l in open(f"{BASE}/ZDT1/42/exp_main_c238_ZDT1_42.jsonl") if '"c238_gen"' in l]
z = pd.DataFrame(dict(g=[r["geracao"] for r in G], eim=[r["eim_best"] for r in G],
                      nfront=[r["n_front"] for r in G],
                      rmin=[r["norm_range_efetivo"][0] for r in G],
                      rmax=[r["norm_range_efetivo"][1] for r in G]))
z["salto"] = z.eim.pct_change()
z.to_csv(f"{OUT}/zdt1_salto.csv", index=False)
print("\nZDT1 top-8 saltos de eim_best:")
print(z.reindex(z.salto.abs().sort_values(ascending=False).index).head(8).to_string(index=False))
