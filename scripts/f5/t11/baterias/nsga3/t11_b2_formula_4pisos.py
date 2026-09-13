"""T11/nsga3 — bateria 2: a errata 5 nos 4 PISOS (100 celulas) — qual formula fecha?
READ-ONLY. Saida: formula_4pisos.csv
"""
import json, math, os, glob
import pandas as pd

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"
EV = {"nsga3": "nsga3_gen", "nsga2": "nsga2_gen", "moead": "moead_gen", "smsemoa": "smsemoa_gen"}

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
        n_off = 2 * (Nef // 2)
        ngen = m["n_geracoes"]
        gens, ch = [], []
        evname = None
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
                evname = rec
                gens.append(r)
            elif rec == "guard" and r.get("name") == "cache_hit":
                ch.append(r)
        fe_last = gens[-1]["fe"] if gens else init
        dup_off = len([g for g in ch if init < g.get("fe", 0) <= fe_last])
        ch_tot = len(ch)
        infill = 20 * D
        rows.append(dict(alg=alg, prob=prob, D=D, Nef=Nef, n_off=n_off, ngen=ngen,
                         ev=evname, ch_tot=ch_tot, dup_off=dup_off,
                         ch_init=len([g for g in ch if g.get("fe") == init]),
                         A24_ceil_dupoff=math.ceil((infill + dup_off) / n_off),
                         T11_floor_chtot=math.floor((infill + ch_tot) / n_off)))

df = pd.DataFrame(rows)
df["ok_A24"] = (df.A24_ceil_dupoff == df.ngen).astype(int)
df["ok_T11"] = (df.T11_floor_chtot == df.ngen).astype(int)
df.to_csv(os.path.join(OUT, "formula_4pisos.csv"), index=False)
print(df.groupby("alg")[["ok_A24", "ok_T11"]].agg(["sum", "count"]).to_string())
print("\nTOTAL A24(ceil,dup_off) %d/%d  ·  T11(floor,cache_total) %d/%d"
      % (df.ok_A24.sum(), len(df), df.ok_T11.sum(), len(df)))
print("\nonde T11 falha:")
print(df[df.ok_T11 == 0][["alg", "prob", "D", "Nef", "n_off", "ngen", "ch_tot",
                          "dup_off", "ch_init", "A24_ceil_dupoff", "T11_floor_chtot"]].to_string(index=False))
print("\nonde A24 falha:")
print(df[df.ok_A24 == 0][["alg", "prob", "D", "Nef", "n_off", "ngen", "ch_tot",
                          "dup_off", "ch_init", "A24_ceil_dupoff", "T11_floor_chtot"]].to_string(index=False))
