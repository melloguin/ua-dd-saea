"""B1 — Testa a REGRA I-12 (ordem_terceira_online) contra o DADO.

Regra declarada (sigma_dict / botorch_harness.restart_de_linha):
    linha j -> restart j      (j <  best)
    linha j -> restart j+1    (j >= best, j < R-1)
    linha R-1 -> restart best
Hipotese nula (a leitura da F5/J27): mapa = identidade.

Teste discriminante: alpha^JES e funcao deterministica de x DENTRO da iteracao
(caminhos fixos). Logo  X_i == X_j  <=>  acqf[m(i)] == acqf[m(j)].
Medimos a taxa de consistencia dessa implicacao sob os DOIS mapas.
READ-ONLY.
"""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154")
TETO = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
            "/experiments/main/c154")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")


def restart_de_linha(R, best):
    return [(j if j < best else j + 1) for j in range(R - 1)] + [best]


def carrega(base, prob):
    sur = pd.read_parquet(base / f"exp_main_c154_{prob}_42__surrogate.parquet")
    dec = []
    for ln in open(base / f"exp_main_c154_{prob}_42.jsonl"):
        r = json.loads(ln)
        if r.get("rec") == "decision":
            dec.append(r)
    return sur, dec


def analisa(prob, base, tag):
    sur, dec = carrega(base, prob)
    on = sur[sur.regime == "online"].copy()
    xcols = [c for c in on.columns if c.startswith("x") and c[1:].isdigit()]
    xcols.sort(key=lambda c: int(c[1:]))
    linhas = []
    for d in dec:
        it = d["it"]
        acq = d.get("acqf_todos_restarts")
        if acq is None:
            continue
        acq = np.asarray(acq, dtype=float)
        blk = on[on.geracao == it]
        R = len(blk)
        if R == 0 or R != len(acq):
            linhas.append(dict(prob=prob, it=it, R=R, nacq=len(acq),
                               erro="shape"))
            continue
        X = blk[xcols].to_numpy()
        fin = np.isfinite(acq)
        best = int(np.argmax(np.where(fin, acq, -np.inf)))
        # chaves
        xkey = [tuple(np.asarray(r, dtype=np.float32).tobytes() for r in [row])
                for row in X]
        xkey = [np.asarray(row, dtype=np.float32).tobytes() for row in X]
        res = {}
        for nome, m in (("decl", restart_de_linha(R, best)),
                        ("naive", list(range(R)))):
            ok = True
            npares = 0
            for i in range(R):
                for j in range(i + 1, R):
                    same_x = xkey[i] == xkey[j]
                    a1, a2 = acq[m[i]], acq[m[j]]
                    if not (np.isfinite(a1) and np.isfinite(a2)):
                        continue
                    same_a = (a1 == a2) or (abs(a1 - a2) <=
                                            1e-9 * max(abs(a1), abs(a2), 1e-300))
                    if same_x or same_a:
                        npares += 1
                    if same_x != same_a:
                        ok = False
            res[nome] = ok
            res[nome + "_pares"] = npares
        # poder: ha algum par duplicado (em X ou em acqf)?
        nx = len(set(xkey))
        na = len(set(acq[fin].tolist()))
        linhas.append(dict(
            prob=prob, tag=tag, it=it, R=R, best=best,
            n_x_distintos=nx, n_acqf_distintos=na,
            tem_dup=(nx < R or na < int(fin.sum())),
            decl_ok=res["decl"], naive_ok=res["naive"],
            decl_pares=res["decl_pares"], naive_pares=res["naive_pares"],
            best_eh_ultimo=(best == R - 1),
            marcada_ultima=bool(blk.real_solution_id.notna().to_numpy()[-1])
            if blk.real_solution_id.notna().any() else None,
            n_marcadas=int(blk.real_solution_id.notna().sum()),
        ))
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    todos = []
    for p in sorted(x.name for x in ROOT.iterdir() if x.is_dir()):
        todos.append(analisa(p, ROOT / p / "42", "s42"))
    todos.append(analisa("DTLZ2", TETO, "teto_T11"))
    df = pd.concat(todos, ignore_index=True)
    df.to_csv(OUT / "c154_regra_I12.csv", index=False)

    print("=" * 78)
    print("TESTE DA REGRA I-12 — corpus s42 (11 celulas) + smoke teto (DTLZ2)")
    print("=" * 78)
    for tag, g in df.groupby("tag"):
        print(f"\n### {tag} — {len(g)} iteracoes, {g.prob.nunique()} celulas")
        disc = g[g.tem_dup]
        print(f"  iteracoes COM duplicata (poder discriminante): {len(disc)}"
              f" ({100*len(disc)/len(g):.1f}%)")
        print(f"  regra DECLARADA consistente : {int(g.decl_ok.sum())}/{len(g)}"
              f"  ({100*g.decl_ok.mean():.2f}%)")
        print(f"  mapa INGENUO   consistente : {int(g.naive_ok.sum())}/{len(g)}"
              f"  ({100*g.naive_ok.mean():.2f}%)")
        if len(disc):
            print(f"  -- so nas discriminantes: decl {int(disc.decl_ok.sum())}"
                  f"/{len(disc)} ({100*disc.decl_ok.mean():.2f}%) | "
                  f"naive {int(disc.naive_ok.sum())}/{len(disc)} "
                  f"({100*disc.naive_ok.mean():.2f}%)")
        print(f"  best == R-1 (mapas coincidem): {int(g.best_eh_ultimo.sum())}"
              f"/{len(g)} ({100*g.best_eh_ultimo.mean():.2f}%)")
        print(f"  linhas marcadas por iteracao: "
              f"{sorted(g.n_marcadas.unique().tolist())}")
        mk = g[g.n_marcadas > 0]
        print(f"  marcada e a ULTIMA linha: {int(mk.marcada_ultima.sum())}"
              f"/{len(mk)}")

    print("\n### por celula (s42)")
    s = df[df.tag == "s42"]
    for p, g in s.groupby("prob"):
        d = g[g.tem_dup]
        print(f"  {p:10s} n={len(g):4d} disc={len(d):4d}  "
              f"decl={100*g.decl_ok.mean():6.2f}%  "
              f"naive={100*g.naive_ok.mean():6.2f}%  "
              f"(disc: decl {100*d.decl_ok.mean() if len(d) else float('nan'):6.2f}%"
              f" naive {100*d.naive_ok.mean() if len(d) else float('nan'):6.2f}%)")
