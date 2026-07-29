"""F5.4 — c154-J27: RECONSTRUCAO da 'paisagem da aquisicao' que o achado deu por perdida.

Regra de leitura (derivada de src/c154_jes.py:735-757 + :686-713, e confirmada no dado
pelos testes A/B de refuta_j27_b.py):

    R    = len(acqf_todos_restarts)                    # == 5*D no main (q=1)
    best = argmax mascarado por isfinite(acqf_todos_restarts)   # == indice de acqf_escolhido
    linha j do bloco 3-online (geracao == it), j = 0..R-1:
        restart(j) = j                se j <  best
        restart(j) = j + 1            se best <= j <= R-2
        restart(R-1) = best           # o vencedor, re-anexado apos o FE

Produz `c154_paisagem_reconstruida.csv` com (candidato, mu, sigma, alpha) POR RESTART.
"""
import json
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/c154-J27"


def restart_de_linha(R, best):
    """linha -> indice de restart (a permutacao 'delete-best + append-best')."""
    return [k for k in range(R) if k != best] + [best]


def main():
    out = []
    diag = []
    for prob in sorted(os.listdir(ROOT)):
        b = os.path.join(ROOT, prob, "42")
        if not os.path.isdir(b):
            continue
        jl = [f for f in os.listdir(b) if f.endswith(".jsonl")][0]
        sg = [f for f in os.listdir(b) if f.endswith("__surrogate.parquet")][0]
        recs = [json.loads(l) for l in open(os.path.join(b, jl))]
        df = pd.read_parquet(os.path.join(b, sg))
        on = df[df.regime == "online"]
        xc = [c for c in on.columns if c[0] == "x" and c[1:].isdigit()]
        mc = [c for c in on.columns if c.startswith("mu_")]
        sc = [c for c in on.columns if c.startswith("sigma_")]
        rho_as, rho_am = [], []
        for r in recs:
            if r.get("rec") != "decision":
                continue
            it = r["it"]
            a = np.array(r["acqf_todos_restarts"], dtype=float)
            R = len(a)
            blk = on[on.geracao == it]
            assert len(blk) == R, (prob, it, len(blk), R)
            fin = np.isfinite(a)
            best = int(np.argmax(np.where(fin, a, -np.inf)))
            assert float(a[best]) == float(r["acqf_escolhido"]), (prob, it)
            mp = restart_de_linha(R, best)
            X = blk[xc].to_numpy()
            MU = blk[mc].to_numpy()
            SG = blk[sc].to_numpy()
            rsid = blk["real_solution_id"].to_numpy()
            for j in range(R):
                out.append(dict(
                    problema=prob, it=it, linha_3=j, restart=mp[j],
                    vencedor=(mp[j] == best),
                    alpha=a[mp[j]],
                    real_solution_id=(None if pd.isna(rsid[j]) else int(rsid[j])),
                    **{f"x{k}": X[j][k] for k in range(len(xc))},
                    **{f"mu_{k}": MU[j][k] for k in range(len(mc))},
                    **{f"sigma_{k}": SG[j][k] for k in range(len(sc))}))
            if fin.all() and R >= 6:
                al = a[np.array(mp)]
                sbar = SG.mean(axis=1)
                mbar = MU.mean(axis=1)
                if np.std(al) > 0 and np.std(sbar) > 0:
                    rho_as.append(spearmanr(al, sbar).statistic)
                if np.std(al) > 0 and np.std(mbar) > 0:
                    rho_am.append(spearmanr(al, mbar).statistic)
        diag.append(dict(problema=prob, n_it=len(rho_as),
                         rho_alpha_sigma=np.median(rho_as) if rho_as else np.nan,
                         rho_alpha_mu=np.median(rho_am) if rho_am else np.nan))
        print(f"{prob:10s} rho(alpha,sigma_med)={diag[-1]['rho_alpha_sigma']:+.3f}  "
              f"rho(alpha,mu_med)={diag[-1]['rho_alpha_mu']:+.3f}")
    d = pd.DataFrame(out)
    d.to_csv(os.path.join(OUT, "c154_paisagem_reconstruida.csv"), index=False)
    pd.DataFrame(diag).to_csv(os.path.join(OUT, "c154_paisagem_diag.csv"),
                              index=False)
    print(f"\nlinhas reconstruidas: {len(d)}  "
          f"(iteracoes {d.groupby(['problema','it']).ngroups}, "
          f"vencedores {int(d.vencedor.sum())})")


if __name__ == "__main__":
    main()
