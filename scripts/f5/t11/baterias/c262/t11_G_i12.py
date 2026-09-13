#!/usr/bin/env python
"""T11/c262 — BATERIA G: a regra I-12 (`ordem_terceira_online`) e VERDADEIRA?

A correcao mais importante do T11 neste config: a armadilha (a) da F5 (a ordem
da 3-online) virou REGRA declarada no sigma_dict + utilitario de codigo. Aqui
ela e TESTADA, nao aceita:
  (T1) `best == R-1`? -> quantifica o "89% de falso-mismatch" do texto;
  (T2) teste de refinamento: 2 linhas da 3 com x quase-igual (restarts que
       convergiram ao MESMO otimo) TEM de receber alpha quase-igual sob o
       mapeamento correto. Compara REGRA I-12 x identidade x aleatoria;
  (T3) o mesmo no smoke T11.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src.botorch_harness import restart_de_linha

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262"
SM = ("/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/"
      "experiments/main/c262/exp_main_c262_MMF1_0")
rng = np.random.default_rng(20260731)


def celula(B, tag):
    dec = {}
    for l in open(f"{B}.jsonl"):
        if not l.strip():
            continue
        r = json.loads(l)
        if r.get("rec") == "decision":
            dec[int(r["it"])] = r
    r3 = pd.read_parquet(f"{B}__surrogate.parquet")
    on = r3[r3.regime == "online"]
    xc = [c for c in on.columns if c.startswith("x") and c[1:].isdigit()]
    n_best_ult = n_it = 0
    par_tot = v_i12 = v_id = v_al = 0
    for g, blk in on.groupby("geracao"):
        d = dec.get(int(g))
        if d is None:
            continue
        a = np.array(d["acqf_todos_restarts"], dtype=np.float64)
        R = len(blk)
        if R != len(a):
            continue
        fin = np.where(np.isfinite(a))[0]
        best = int(fin[np.argmax(a[fin])]) if len(fin) else int(np.argmax(a))
        n_it += 1
        n_best_ult += (best == R - 1)
        mapa = restart_de_linha(R, best)
        alpha_i12 = a[mapa]
        alpha_id = a[: R]
        perm = rng.permutation(R)
        alpha_al = a[perm]
        X = blk[xc].values.astype(np.float32)
        # pares de x bit-identicos em float32 dentro do bloco
        _, inv, cnt = np.unique(X, axis=0, return_inverse=True,
                                return_counts=True)
        for gi in np.where(cnt > 1)[0]:
            idx = np.where(inv == gi)[0]
            for i in range(len(idx)):
                for j in range(i + 1, len(idx)):
                    par_tot += 1
                    for al, acc in ((alpha_i12, "i12"), (alpha_id, "id"),
                                    (alpha_al, "al")):
                        d1, d2 = al[idx[i]], al[idx[j]]
                        den = max(abs(d1), abs(d2), 1e-30)
                        viol = abs(d1 - d2) / den > 1e-12
                        if acc == "i12":
                            v_i12 += viol
                        elif acc == "id":
                            v_id += viol
                        else:
                            v_al += viol
    return dict(tag=tag, n_it=n_it, best_eq_ultima=n_best_ult,
                pares=par_tot, viol_I12=v_i12, viol_ident=v_id,
                viol_aleat=v_al)


res = []
for p in sorted(os.listdir(ROOT)):
    d = f"{ROOT}/{p}/42"
    if not os.path.isdir(d):
        continue
    g = glob.glob(f"{d}/*.manifest.json")
    if g:
        res.append(celula(g[0][: -len(".manifest.json")], p))
df = pd.DataFrame(res)
df.to_csv("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/"
          "baterias/c262/c262_t11_i12.csv", index=False)
T = df[["n_it", "best_eq_ultima", "pares", "viol_I12", "viol_ident",
        "viol_aleat"]].sum()
print("=== I-12 na s42 (21 celulas) ===")
print(f"iteracoes: {T.n_it} | best == ultima linha: {T.best_eq_ultima} "
      f"({100*T.best_eq_ultima/T.n_it:.1f}%) -> falso-mismatch do indice "
      f"ingenuo = {100-100*T.best_eq_ultima/T.n_it:.1f}%")
print(f"pares de x-duplicata (float32) no bloco: {T.pares}")
for k, lab in (("viol_I12", "REGRA I-12"), ("viol_ident", "identidade"),
               ("viol_aleat", "aleatoria")):
    print(f"  violacoes sob {lab:12s}: {T[k]:6d}  ({100*T[k]/T.pares:5.2f}%)")
print()
print(df.to_string(index=False))
print()
print("=== I-12 no SMOKE T11 ===")
print(celula(SM, "smoke_MMF1_s0"))
