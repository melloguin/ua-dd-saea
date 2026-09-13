"""T11/nsga3 — bateria 1: RE-MEDIR a errata 5 (I-13/A24) sobre as 25 celulas da s42.
Compara as 4 candidatas de formula para n_geracoes contra o valor observado.
READ-ONLY. Saida: formula_ngeracoes.csv
"""
import json, math, os, glob
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"

rows = []
for prob in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, prob, "42")
    if not os.path.isdir(d):
        continue
    man = glob.glob(os.path.join(d, "*.manifest.json"))[0]
    jl = glob.glob(os.path.join(d, "*.jsonl"))[0]
    m = json.load(open(man))
    real = pd.read_parquet(glob.glob(os.path.join(d, "*__real.parquet"))[0])
    D = len([c for c in real.columns if c.startswith("x")])
    M = len([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    init = 11 * D - 1
    Nef = m["params"]["N_efetivo"]
    n_off = 2 * (Nef // 2)
    ngen = m["n_geracoes"]
    ch_man = m["cache_hits"]

    gens, guards = [], []
    for ln in open(jl):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("rec") == "nsga3_gen":
            gens.append(r)
        if r.get("rec") == "guard":
            guards.append(r)
    ch = [g for g in guards if g.get("name") == "cache_hit"]
    ch_init = [g for g in ch if g.get("fe") == init]
    fe_last = gens[-1]["fe"]
    ch_off = [g for g in ch if init < g.get("fe", 0) <= fe_last]
    dup_off = len(ch_off)               # duplicatas de DESCENDENTE (definicao A24)
    ch_tot = len(ch)                    # total (inclui as N_ef+1 da semeadura)

    infill = 20 * D
    cands = {
        "A24_ceil_dupoff": math.ceil((infill + dup_off) / n_off),
        "T11_floor_chtot": math.floor((infill + ch_tot) / n_off),
        "floor_dupoff": math.floor((infill + dup_off) / n_off),
        "ceil_chtot": math.ceil((infill + ch_tot) / n_off),
        "string_antiga_20D_div_Nef": math.floor(infill / Nef),
    }
    row = dict(prob=prob, D=D, M=M, Nef=Nef, n_off=n_off, init=init, maxfe=m["maxfe"],
               fe_final=m["fe_final"], ngen_obs=ngen, ngen_events=len(gens),
               ch_man=ch_man, ch_tot=ch_tot, ch_init=len(ch_init), dup_off=dup_off,
               fe_last=fe_last)
    for k, v in cands.items():
        row[k] = v
        row["ok_" + k] = int(v == ngen)
    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "formula_ngeracoes.csv"), index=False)
print(df[["prob", "D", "M", "Nef", "n_off", "ngen_obs", "ch_tot", "dup_off",
          "A24_ceil_dupoff", "T11_floor_chtot", "floor_dupoff", "ceil_chtot",
          "string_antiga_20D_div_Nef"]].to_string(index=False))
print()
for k in ["A24_ceil_dupoff", "T11_floor_chtot", "floor_dupoff", "ceil_chtot",
          "string_antiga_20D_div_Nef"]:
    print("%-28s acerta %2d/25" % (k, df["ok_" + k].sum()))
print()
print("ngen_obs == ngen_events em", int((df.ngen_obs == df.ngen_events).sum()), "/25")
print("ch_man == ch_tot em", int((df.ch_man == df.ch_tot).sum()), "/25")
print("total cache_hits =", int(df.ch_tot.sum()), " semeadura =", int(df.ch_init.sum()),
      " descendentes =", int(df.dup_off.sum()))
