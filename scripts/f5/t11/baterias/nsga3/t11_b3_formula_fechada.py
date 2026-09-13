"""T11/nsga3 — bateria 3: a FORMULA FECHADA de n_geracoes nos 4 pisos.
Hipotese: n_ger = floor((20D + dup_descendentes) / n_off) + 1
  com n_off = 2*floor(N_ef/2) (OperatorGA pareado: nsga2/nsga3/smsemoa)
            = N_ef            (MOEA/D: 1 prole por subproblema)
n_off e' tambem MEDIDO empiricamente (delta de FE entre eventos + cache-hits no intervalo).
READ-ONLY. Saida: formula_fechada_4pisos.csv
"""
import json, math, os, glob
from collections import Counter
import pandas as pd

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"

rows = []
for alg in ["nsga2", "nsga3", "moead", "smsemoa"]:
    root = os.path.join(BASE, alg)
    for prob in sorted(os.listdir(root)):
        d = os.path.join(root, prob, "42")
        if not os.path.isdir(d):
            continue
        m = json.load(open(glob.glob(os.path.join(d, "*.manifest.json"))[0]))
        real = pd.read_parquet(glob.glob(os.path.join(d, "*__real.parquet"))[0])
        D = len([c for c in real.columns if c.startswith("x")])
        init = 11 * D - 1
        Nef = m["params"]["N_efetivo"]
        ngen = m["n_geracoes"]
        gens, ch = [], []
        for ln in open(glob.glob(os.path.join(d, "*.jsonl"))[0]):
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            rec = r.get("rec", "")
            if rec.endswith("_gen"):
                gens.append(r)
            elif rec == "guard" and r.get("name") == "cache_hit":
                ch.append(r)
        fes = [g["fe"] for g in gens]
        fe_last = fes[-1]
        dup_off = len([g for g in ch if init < g.get("fe", 0) <= fe_last])
        # n_off EMPIRICO: por transicao, (delta FE) + (cache-hits no intervalo)
        deltas = []
        for i in range(len(fes) - 1):
            lo, hi = fes[i], fes[i + 1]
            nch = len([g for g in ch if lo < g.get("fe", 0) <= hi])
            deltas.append(hi - lo + nch)
        n_off_emp = Counter(deltas).most_common(1)[0][0] if deltas else None
        n_off_par = 2 * (Nef // 2)
        n_off_use = Nef if alg == "moead" else n_off_par
        pred = math.floor((20 * D + dup_off) / n_off_use) + 1
        rows.append(dict(alg=alg, prob=prob, D=D, Nef=Nef, n_off_par=n_off_par,
                         n_off_emp=n_off_emp, n_off_use=n_off_use,
                         deltas_unicos=len(set(deltas)), ngen=ngen, dup_off=dup_off,
                         pred=pred, ok=int(pred == ngen)))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "formula_fechada_4pisos.csv"), index=False)
print(df.groupby("alg")[["ok"]].agg(["sum", "count"]).to_string())
print("TOTAL fechada: %d/%d" % (df.ok.sum(), len(df)))
print("\nn_off empirico (moda) x n_off usado, por alg:")
print(df.groupby("alg")[["n_off_emp", "n_off_use", "Nef"]].agg(lambda s: sorted(set(s))).to_string())
print("\nfalhas:")
print(df[df.ok == 0].to_string(index=False))
print("\nSO nsga3:")
print(df[df.alg == "nsga3"][["prob", "D", "Nef", "n_off_emp", "n_off_use", "dup_off", "ngen", "pred", "ok"]].to_string(index=False))
