"""F5.4 — refutacao c154-J27, bateria B (dois testes ortogonais, so DADO).

H1 (lida no codigo): linha j do bloco 3-online  ->  restart  j (j<best) | j+1 (j>=best)
                     linha R-1                  ->  restart  best
H0 (o que o analista testou): linha j -> restart j.

TESTE A — PARES DUPLICADOS (exato, alta precisao).
  Restarts que convergem ao MESMO otimo dao x bit-identico (float32) E alpha
  identico. Para cada par de LINHAS com x/mu/sigma bit-identicos, o par de
  RESTARTS correspondente (sob H) tem de ter alpha relativamente identico
  (rtol 1e-9). Mede-se a precisao |acertos|/|pares duplicados|.

TESTE B — SUAVIDADE (geral, vale em toda iteracao).
  alpha e funcao deterministica e suave de x. Sob o alinhamento CORRETO,
  ||x_i-x_j|| e |alpha_i-alpha_j| tem de correlacionar positivamente.
  Spearman sobre os C(R,2) pares, por iteracao. Compara H1, H0 e nulo aleatorio.
"""
import json
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/c154-J27"
RNG = np.random.default_rng(7)
NPERM = 30


def perm_h1(R, best):
    return [k for k in range(R) if k != best] + [best]


def run(config="c154", seed="42"):
    out_rows, cell_rows = [], []
    for prob in sorted(os.listdir(os.path.join(ROOT, config))):
        base = os.path.join(ROOT, config, prob, seed)
        if not os.path.isdir(base):
            continue
        jl = [f for f in os.listdir(base) if f.endswith(".jsonl")]
        sg = [f for f in os.listdir(base) if f.endswith("__surrogate.parquet")]
        if not jl or not sg:
            continue
        recs = [json.loads(l) for l in open(os.path.join(base, jl[0]))]
        dec = [r for r in recs if r.get("rec") == "decision"
               and "acqf_todos_restarts" in r]
        df = pd.read_parquet(os.path.join(base, sg[0]))
        on = df[df.regime == "online"]
        xcols = [c for c in on.columns if c.startswith("x") and c[1:].isdigit()]
        mcols = [c for c in on.columns if c.startswith("mu_")]
        scols = [c for c in on.columns if c.startswith("sigma_")]
        D = len(xcols)
        # escala por dimensao (para a distancia do teste B)
        scale = on[xcols].to_numpy().std(axis=0)
        scale[scale == 0] = 1.0
        agg = dict(problema=prob, D=D, n_it=0,
                   dupA_pares=0, dupA_H1=0, dupA_H0=0, dupA_nulo=0, dupA_nulo_n=0,
                   rhoB_H1=[], rhoB_H0=[], rhoB_nulo=[])
        for r in dec:
            it = r["it"]
            a = np.array(r["acqf_todos_restarts"], dtype=float)
            R = len(a)
            blk = on[on.geracao == it]
            if len(blk) != R:
                continue
            agg["n_it"] += 1
            fin = np.isfinite(a)
            best = int(np.argmax(np.where(fin, a, -np.inf)))
            p1 = perm_h1(R, best)
            p0 = list(range(R))
            X = blk[xcols].to_numpy(dtype=np.float32)
            MS = np.hstack([blk[mcols].to_numpy(dtype=np.float32),
                            blk[scols].to_numpy(dtype=np.float32)])
            key = [X[i].tobytes() + MS[i].tobytes() for i in range(R)]

            def a_eq(p, q):
                if not (np.isfinite(a[p]) and np.isfinite(a[q])):
                    return np.isnan(a[p]) and np.isnan(a[q])
                den = max(abs(a[p]), abs(a[q]), 1e-300)
                return abs(a[p] - a[q]) / den <= 1e-9

            dup = [(i, j) for i in range(R) for j in range(i + 1, R)
                   if key[i] == key[j]]
            nperm_local = 0
            for (i, j) in dup:
                agg["dupA_pares"] += 1
                agg["dupA_H1"] += int(a_eq(p1[i], p1[j]))
                agg["dupA_H0"] += int(a_eq(p0[i], p0[j]))
            if dup:
                for _ in range(NPERM):
                    head = p1[:-1].copy()
                    RNG.shuffle(head)
                    pr = list(head) + [p1[-1]]
                    for (i, j) in dup:
                        agg["dupA_nulo"] += int(a_eq(pr[i], pr[j]))
                        agg["dupA_nulo_n"] += 1

            # TESTE B
            if R >= 6 and fin.all():
                Xn = X / scale
                dx, ii, jj = [], [], []
                for i in range(R):
                    for j in range(i + 1, R):
                        dx.append(np.linalg.norm(Xn[i] - Xn[j]))
                        ii.append(i)
                        jj.append(j)
                dx = np.array(dx)
                ii = np.array(ii)
                jj = np.array(jj)
                if dx.std() > 0:
                    for tag, pm in (("H1", p1), ("H0", p0)):
                        da = np.abs(a[np.array(pm)[ii]] - a[np.array(pm)[jj]])
                        if da.std() > 0:
                            agg[f"rhoB_{tag}"].append(
                                spearmanr(dx, da).statistic)
                    for _ in range(3):
                        head = p1[:-1].copy()
                        RNG.shuffle(head)
                        pr = np.array(list(head) + [p1[-1]])
                        da = np.abs(a[pr[ii]] - a[pr[jj]])
                        if da.std() > 0:
                            agg["rhoB_nulo"].append(spearmanr(dx, da).statistic)
            out_rows.append(dict(problema=prob, it=it, R=R, best=best,
                                 n_dup=len(dup)))
        cell_rows.append(dict(
            problema=prob, D=D, n_it=agg["n_it"],
            dup_pares=agg["dupA_pares"],
            A_H1=agg["dupA_H1"], A_H0=agg["dupA_H0"],
            A_nulo=agg["dupA_nulo"], A_nulo_n=agg["dupA_nulo_n"],
            B_H1=np.median(agg["rhoB_H1"]) if agg["rhoB_H1"] else np.nan,
            B_H0=np.median(agg["rhoB_H0"]) if agg["rhoB_H0"] else np.nan,
            B_nulo=np.median(agg["rhoB_nulo"]) if agg["rhoB_nulo"] else np.nan,
            B_n=len(agg["rhoB_H1"])))
        c = cell_rows[-1]
        print(f"{prob:10s} D={D:2d} it={c['n_it']:4d} | A: dup={c['dup_pares']:5d} "
              f"H1={c['A_H1']:5d} H0={c['A_H0']:5d} "
              f"nulo={c['A_nulo']}/{c['A_nulo_n']} | "
              f"B: rho_H1={c['B_H1']:+.3f} rho_H0={c['B_H0']:+.3f} "
              f"rho_nulo={c['B_nulo']:+.3f}")
    cd = pd.DataFrame(cell_rows)
    cd.to_csv(os.path.join(OUT, f"j27_testeAB_{config}.csv"), index=False)
    pd.DataFrame(out_rows).to_csv(
        os.path.join(OUT, f"j27_iters_{config}.csv"), index=False)
    tot = cd[["n_it", "dup_pares", "A_H1", "A_H0", "A_nulo", "A_nulo_n"]].sum()
    print(f"\n=== {config} TOTAIS ===")
    print(tot.to_string())
    if tot["dup_pares"]:
        print(f"precisao A: H1={tot['A_H1']/tot['dup_pares']:.4f}  "
              f"H0={tot['A_H0']/tot['dup_pares']:.4f}  "
              f"nulo={tot['A_nulo']/max(tot['A_nulo_n'],1):.4f}")
    print("mediana rho B: H1=%.3f H0=%.3f nulo=%.3f" %
          (cd.B_H1.median(), cd.B_H0.median(), cd.B_nulo.median()))
    return cd


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else "c154")
