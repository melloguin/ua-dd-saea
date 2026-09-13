#!/usr/bin/env python
"""probe0_e81 — grounding de schemas ANTES de qualquer query (Etapa 1 do protocolo v1.1).
READ-ONLY sobre resultados_experimentos/e81/.
"""
import json, os, glob
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"

def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out

C = cells()
print("N celulas:", len(C))
print([c[2] for c in C])

for exp, prob, lab, d in C[:1] + [c for c in C if c[0] == "batch"][:1]:
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    print("\n" + "=" * 90)
    print("CELULA", lab)
    man = json.load(open(base + ".manifest.json"))
    print("--- manifest keys:", sorted(man.keys()))
    for k in ("status", "motivo_parada", "maxfe", "fe_final", "n_geracoes", "doe_hash"):
        print("   ", k, "=", man.get(k))
    print("--- params:", json.dumps(man.get("params"), ensure_ascii=False)[:2000])
    print("--- sonda:", json.dumps(man.get("sonda"), ensure_ascii=False)[:800])
    print("--- env:", json.dumps(man.get("env"), ensure_ascii=False)[:1200])
    print("--- timing:", json.dumps(man.get("timing"), ensure_ascii=False)[:400])
    sd = man.get("sigma_dict", {})
    print("--- sigma_dict keys:", sorted(sd.keys()))
    for k, v in sd.items():
        print("    *", k, "=", str(v)[:600])
    for suf in ("__real", "__pop", "__surrogate", "__timing"):
        f = base + suf + ".parquet"
        if os.path.exists(f):
            df = pd.read_parquet(f)
            print(f"--- {suf}: shape={df.shape} cols={list(df.columns)}")
            print(df.head(2).to_string()[:1200])
            if suf == "__surrogate":
                print("    regime:", df["regime"].value_counts().to_dict())
                print("    dtypes:", {c: str(t) for c, t in df.dtypes.items()})
    recs = {}
    with open(base + ".jsonl") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                recs["__BAD__"] = recs.get("__BAD__", 0) + 1
                continue
            r = o.get("rec", "?")
            recs[r] = recs.get(r, 0) + 1
            if r not in ("__seen__",) and recs[r] == 1:
                print(f"--- jsonl rec={r} keys:", sorted(o.keys()))
                if r in ("decision", "footer", "header", "fit", "sonda"):
                    print("      ", json.dumps(o, ensure_ascii=False)[:2500])
    print("--- rec counts:", recs)
