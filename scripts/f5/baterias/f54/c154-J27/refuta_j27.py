"""F5.4 — refutacao adversarial do achado c154-J27.

Hipotese do analista (J27): a 3-online e o `acqf_todos_restarts` do jsonl NAO sao
alinhaveis (perda do pareamento (candidato, mu, sigma, alpha) por restart).

Hipotese da refutacao (H1, lida no codigo `src/c154_jes.py`): o bloco 3-online e a
lista de restarts NA ORDEM ORIGINAL com o VENCEDOR REMOVIDO e RE-ANEXADO NO FIM.
Logo a permutacao e deterministica e conhecida:
    linha j (j < R-1) -> restart  j      se j <  best
                         restart  j+1    se j >= best
    linha R-1         -> restart  best
H0 (o que o analista testou): linha j -> restart j.

Teste discriminante (nao usa o codigo, so o dado): restarts que convergem ao mesmo
otimo local produzem alpha IDENTICO (ate ~1e-13 relativo) E x IDENTICO. A PARTICAO
por empate de alpha tem de bater, posicao a posicao, com a PARTICAO por empate de x.
Comparo H1, H0 e um nulo de permutacoes aleatorias.

READ-ONLY sobre resultados_experimentos/. Escreve so nesta pasta.
"""
import json
import os
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/c154-J27"
RNG = np.random.default_rng(20260729)


def clusters_rel(v, rtol):
    """Particao por empate relativo (clustering 1-D em vetor ordenado)."""
    v = np.asarray(v, dtype=float)
    n = len(v)
    lab = np.full(n, -1)
    order = np.argsort(v, kind="stable")
    cur = 0
    lab[order[0]] = 0
    for k in range(1, n):
        a, b = v[order[k - 1]], v[order[k]]
        den = max(abs(a), abs(b), 1e-300)
        if np.isfinite(a) and np.isfinite(b) and abs(b - a) / den <= rtol:
            lab[order[k]] = cur
        else:
            cur += 1
            lab[order[k]] = cur
    return canon(lab)


def clusters_rows(X):
    """Particao por igualdade EXATA das tuplas float32 de x."""
    seen, lab = {}, []
    for row in X:
        key = tuple(np.asarray(row, dtype=np.float32).tobytes() for _ in (0,))
        key = np.asarray(row, dtype=np.float32).tobytes()
        if key not in seen:
            seen[key] = len(seen)
        lab.append(seen[key])
    return canon(np.array(lab))


def canon(lab):
    """Rotulagem canonica por primeira ocorrencia (torna particoes comparaveis)."""
    m, out, nxt = {}, [], 0
    for v in lab:
        if v not in m:
            m[v] = nxt
            nxt += 1
        out.append(m[v])
    return tuple(out)


def perm_h1(R, best):
    """linha -> indice de restart, sob H1 (delete-best + append-best)."""
    idx = [k for k in range(R) if k != best] + [best]
    return idx


def perm_h0(R, best):
    return list(range(R))


def main():
    cells = sorted(os.listdir(os.path.join(ROOT, "c154")))
    rows = []
    per_cell = []
    for prob in cells:
        base = os.path.join(ROOT, "c154", prob, "42")
        if not os.path.isdir(base):
            continue
        jl = [f for f in os.listdir(base) if f.endswith(".jsonl")]
        sg = [f for f in os.listdir(base) if f.endswith("__surrogate.parquet")]
        if not jl or not sg:
            continue
        recs = [json.loads(l) for l in open(os.path.join(base, jl[0]))]
        dec = [r for r in recs if r.get("rec") == "decision"]
        df = pd.read_parquet(os.path.join(base, sg[0]))
        on = df[df.regime == "online"].copy()
        xcols = [c for c in on.columns if c.startswith("x") and c[1:].isdigit()]
        D = len(xcols)
        n_h1 = n_h0 = n_inf = n_tot = 0
        n_null_hits = 0
        n_null_draws = 0
        n_winner_last = 0
        n_argmax_ok = 0
        for r in dec:
            it = r["it"]
            a = np.array(r["acqf_todos_restarts"], dtype=float)
            R = len(a)
            blk = on[on.geracao == it]
            if len(blk) != R:
                rows.append(dict(problema=prob, it=it, erro=f"len {len(blk)} != R {R}"))
                continue
            n_tot += 1
            fin = np.isfinite(a)
            best = int(np.argmax(np.where(fin, a, -np.inf)))
            # coerencia do argmax com o `acqf_escolhido` logado (bit-a-bit)
            if "acqf_escolhido" in r and float(a[best]) == float(r["acqf_escolhido"]):
                n_argmax_ok += 1
            # a linha marcada e a ultima?
            rsid = blk["real_solution_id"].to_numpy()
            marked = np.where(~pd.isna(rsid))[0]
            if len(marked) == 1 and marked[0] == R - 1:
                n_winner_last += 1
            X = blk[xcols].to_numpy()
            p_rows = clusters_rows(X)
            p_a = clusters_rel(a, 1e-10)
            ok1 = canon(np.array([p_a[i] for i in perm_h1(R, best)])) == p_rows
            ok0 = canon(np.array([p_a[i] for i in perm_h0(R, best)])) == p_rows
            informativo = len(set(p_a)) < R  # ha pelo menos um empate de alpha
            n_h1 += int(ok1)
            n_h0 += int(ok0)
            n_inf += int(informativo)
            if informativo:
                # nulo: permuta as R-1 posicoes nao-vencedoras ao acaso
                hits = 0
                for _ in range(200):
                    pm = perm_h1(R, best)
                    head = pm[:-1]
                    RNG.shuffle(head)
                    cand = canon(np.array([p_a[i] for i in list(head) + [pm[-1]]]))
                    hits += int(cand == p_rows)
                n_null_hits += hits
                n_null_draws += 200
            rows.append(dict(problema=prob, D=D, it=it, R=R, best=best,
                             n_clusters_alpha=len(set(p_a)),
                             n_clusters_x=len(set(p_rows)),
                             informativo=informativo, H1=ok1, H0=ok0,
                             winner_last=(len(marked) == 1 and marked[0] == R - 1),
                             n_naofinitos=int((~fin).sum())))
        per_cell.append(dict(problema=prob, D=D, n_iters=n_tot,
                             argmax_bitexato=n_argmax_ok,
                             winner_last=n_winner_last,
                             informativos=n_inf, H1_ok=n_h1, H0_ok=n_h0,
                             nulo_hits=n_null_hits, nulo_draws=n_null_draws))
        print(f"{prob:10s} D={D:2d} iters={n_tot:4d} argmax_bit={n_argmax_ok:4d} "
              f"winner_last={n_winner_last:4d} inform={n_inf:4d} "
              f"H1={n_h1:4d} H0={n_h0:4d} nulo={n_null_hits}/{n_null_draws}")
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "j27_por_iteracao.csv"), index=False)
    pc = pd.DataFrame(per_cell)
    pc.to_csv(os.path.join(OUT, "j27_por_celula.csv"), index=False)
    print("\n=== TOTAIS ===")
    print(pc[["n_iters", "argmax_bitexato", "winner_last", "informativos",
              "H1_ok", "H0_ok", "nulo_hits", "nulo_draws"]].sum().to_string())


if __name__ == "__main__":
    main()
