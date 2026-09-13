"""B2 — Regra I-12, teste DIRECIONAL correto.

O plateau da alphaJES (J28) faz "acqf quase-igual" acontecer em pontos
DIFERENTES => a implicacao  same_acqf -> same_x  NAO vale e polui o teste B1.
A implicacao VALIDA e a outra:  same_x -> same_acqf (exatamente, float64).

Estatistica: sobre os PARES de linhas da 3a com X float32 IDENTICO, medir
|delta acqf| relativo sob o mapa DECLARADO e sob o mapa INGENUO.
Mapa correto => ~0. Mapa errado => valores arbitrarios.
READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154")
TETO = Path("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/teto_c154"
            "/experiments/main/c154")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c154")


def restart_de_linha(R, best):
    return [(j if j < best else j + 1) for j in range(R - 1)] + [best]


def roda(prob, base, tag):
    sur = pd.read_parquet(base / f"exp_main_c154_{prob}_42__surrogate.parquet")
    on = sur[sur.regime == "online"]
    xcols = sorted([c for c in on.columns
                    if c.startswith("x") and c[1:].isdigit()],
                   key=lambda c: int(c[1:]))
    dec = [json.loads(l) for l in open(base / f"exp_main_c154_{prob}_42.jsonl")]
    dec = [d for d in dec if d.get("rec") == "decision"]
    pares = []
    for d in dec:
        it = d["it"]
        acq = np.asarray(d["acqf_todos_restarts"], dtype=float)
        blk = on[on.geracao == it]
        R = len(blk)
        if R != len(acq):
            continue
        X = blk[xcols].to_numpy()
        fin = np.isfinite(acq)
        best = int(np.argmax(np.where(fin, acq, -np.inf)))
        m_decl = restart_de_linha(R, best)
        m_nv = list(range(R))
        keys = [np.asarray(r, dtype=np.float32).tobytes() for r in X]
        for i in range(R):
            for j in range(i + 1, R):
                if keys[i] != keys[j]:
                    continue
                for nome, m in (("decl", m_decl), ("naive", m_nv)):
                    a1, a2 = acq[m[i]], acq[m[j]]
                    if not (np.isfinite(a1) and np.isfinite(a2)):
                        continue
                    den = max(abs(a1), abs(a2), 1e-300)
                    pares.append(dict(prob=prob, tag=tag, it=it, i=i, j=j,
                                      mapa=nome, rel=abs(a1 - a2) / den,
                                      exato=(a1 == a2)))
    return pd.DataFrame(pares)


if __name__ == "__main__":
    fr = [roda(p, ROOT / p / "42", "s42")
          for p in sorted(x.name for x in ROOT.iterdir() if x.is_dir())]
    fr.append(roda("DTLZ2", TETO, "teto_T11"))
    df = pd.concat(fr, ignore_index=True)
    df.to_csv(OUT / "c154_I12_pares_xtied.csv", index=False)

    print("=" * 78)
    print("REGRA I-12 — pares de linhas da 3a com X float32 IDENTICO")
    print("=" * 78)
    for tag, g in df.groupby("tag"):
        n = len(g) // 2
        print(f"\n### {tag}: {n} pares X-empatados "
              f"em {g.it.nunique()} iteracoes, {g.prob.nunique()} celulas")
        for mapa, gg in g.groupby("mapa"):
            print(f"  mapa {mapa:6s}: acqf EXATAMENTE igual em "
                  f"{int(gg.exato.sum())}/{len(gg)} "
                  f"({100*gg.exato.mean():.2f}%) | "
                  f"|drel| mediana={gg.rel.median():.3e} "
                  f"max={gg.rel.max():.3e}")
    print("\n### por celula (todos os corpora)")
    piv = df.pivot_table(index="prob", columns="mapa",
                         values="exato", aggfunc=["sum", "count"])
    print(piv)
