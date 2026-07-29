#!/usr/bin/env python
"""
F5.4 / moead-M16 — reproducao INDEPENDENTE do gap de n_front1.

Objetivo: refutar (ou confirmar) "n_front1 diverge de +-1 em 16/469 geracoes sem
mecanismo identificado".

Metodo proprio (nao reusa nada da bateria do analista):
  - ② (pop.parquet) -> solution_id por geracao
  - ① (real.parquet) -> F float32 por solution_id
  - recomputo do nao-dominado com dominancia ESTRITA (>= em todos + > em um),
    contando DUPLICATAS (o NDSort do PlatEMO faz unique+expande via Loc,
    portanto duplicatas ficam TODAS na frente 1)
  - discriminante NOVO: `nadir_front1` do ⑥ = max componentwise da frente-1 que
    o MATLAB viu. Ele identifica QUAL individuo entra/sai.
Saidas: r1_gap.csv, r1_nadir.csv
"""
import json, os, sys
import numpy as np
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead-M16"


def nd_mask(F):
    """mascara booleana do nao-dominado, dominancia estrita, duplicatas incluidas."""
    n = len(F)
    dom = np.zeros(n, dtype=bool)
    for j in range(n):
        if dom[j]:
            continue
        le = np.all(F <= F[j], axis=1)
        lt = np.any(F < F[j], axis=1)
        # j dominado por algum i
        if np.any(le & lt & (np.arange(n) != j)):
            dom[j] = True
    return ~dom


def nd_mask_full(F):
    n = len(F)
    out = np.ones(n, dtype=bool)
    for j in range(n):
        le = np.all(F <= F[j], axis=1)
        lt = np.any(F < F[j], axis=1)
        m = le & lt
        m[j] = False
        if np.any(m):
            out[j] = False
    return out


def main():
    probs = sorted(os.listdir(RAIZ))
    rows = []
    nad = []
    for prob in probs:
        d = os.path.join(RAIZ, prob, "42")
        base = f"exp_main_moead_{prob}_42"
        pop = pd.read_parquet(os.path.join(d, base + "__pop.parquet"))
        real = pd.read_parquet(os.path.join(d, base + "__real.parquet"))
        fcols = [c for c in real.columns if c.startswith("f") and c[1:].isdigit()]
        fcols = sorted(fcols, key=lambda c: int(c[1:]))
        Fmap = {int(s): real.loc[i, fcols].to_numpy(dtype=np.float64)
                for i, s in zip(real.index, real["solution_id"].to_numpy())}
        recs = [json.loads(l) for l in open(os.path.join(d, base + ".jsonl"))]
        gens = [r for r in recs if r.get("rec") == "moead_gen"]
        for r in gens:
            g = r["geracao"]
            sids = pop.loc[pop["geracao"] == g, "solution_id"].to_numpy()
            F = np.vstack([Fmap[int(s)] for s in sids])   # float32 promovido a f64
            m = nd_mask_full(F)
            mine = int(m.sum())
            logged = int(r["n_front1"])
            # nadir da frente-1 pelo meu recomputo, em float32 (o ① e f32)
            my_nf1 = F[m].max(axis=0)
            log_nf1 = np.asarray(r["nadir_front1"], dtype=np.float64)
            log_nadpop = np.asarray(r["nadir_pop"], dtype=np.float64)
            log_ideal = np.asarray(r["ideal"], dtype=np.float64)
            rows.append(dict(problema=prob, M=len(fcols), ger=g, n_pop=r["n_pop"],
                             n_sids=len(sids), n_uniq=len(set(sids.tolist())),
                             log=logged, meu=mine, delta=logged - mine))
            nad.append(dict(problema=prob, ger=g, log=logged, meu=mine,
                            nf1_log=list(log_nf1), nf1_meu=list(my_nf1),
                            nadpop_log=list(log_nadpop),
                            nadpop_meu=list(F.max(axis=0)),
                            ideal_log=list(log_ideal),
                            ideal_meu=list(F.min(axis=0))))
        print(f"{prob}: {len(gens)} ger", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "r1_gap.csv"), index=False)
    pd.DataFrame(nad).to_csv(os.path.join(OUT, "r1_nadir.csv"), index=False)
    bad = df[df.delta != 0]
    print("\n=== TOTAL ger:", len(df), " batem:", int((df.delta == 0).sum()),
          " divergem:", len(bad))
    print(bad.to_string(index=False))


if __name__ == "__main__":
    main()
