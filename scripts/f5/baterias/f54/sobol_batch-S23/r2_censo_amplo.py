"""F5.4 · sobol_batch-S23 · R2 — censo AMPLO (formulacao alternativa).

Diferenca vs R1: o "evento de geracao" NAO e reconhecido por sufixo `_gen`;
e reconhecido como *o registro mais numeroso que carrega `fe` e `f_best`*.
Isso captura c154/c262 (`rec=decision, caminho=infill`), c311 (`c311_build`),
e81/c149/c122 (`decision, caminho=<alg>_gen:<rota>`) — que o filtro do R1
perdia. Serve de controle contra "artefato de query" no censo do analista.
"""
import json, os, collections
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S23"

DI10 = ["fe", "f_best", "n_front1", "modelo_hp", "tempo_fit_s",
        "tempo_busca_s", "dist_min_arquivo"]
PISOS = ["ideal", "nadir_pop", "nadir_front1"]

rows = []
for alg in sorted(os.listdir(ROOT)):
    d0 = os.path.join(ROOT, alg)
    if not os.path.isdir(d0) or alg.startswith("_"):
        continue
    for prob in sorted(os.listdir(d0)):
        d1 = os.path.join(d0, prob)
        if not os.path.isdir(d1):
            continue
        d2 = os.path.join(d1, "42")
        if not os.path.isdir(d2):
            continue
        for fn in sorted(os.listdir(d2)):
            if not fn.endswith(".jsonl"):
                continue
            exp = fn.split("_")[1]
            grp = collections.defaultdict(list)
            with open(os.path.join(d2, fn)) as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        e = json.loads(ln)
                    except Exception:
                        continue
                    if "fe" in e and "f_best" in e:
                        grp[(e.get("rec"), str(e.get("caminho", "")).split(":")[0])].append(e)
            if not grp:
                continue
            # o "evento de geracao" = a familia mais numerosa; mas somamos TODAS
            # as familias que tenham f_best (c149 tem 2 rotas)
            todas = [e for v in grp.values() for e in v]
            n = len(todas)
            keys = collections.Counter()
            for e in todas:
                for k, v in e.items():
                    if v is not None:
                        keys[k] += 1
            pres = {k: (keys[k] == n) for k in DI10 + PISOS}
            rows.append(dict(alg=alg, exp=exp, problema=prob, n_ev=n,
                             familias=";".join(sorted(f"{a}/{b}" for a, b in grp)),
                             **{("has_" + k): pres[k] for k in pres}))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "r2_censo_amplo_celula.csv"), index=False)
g = (df.groupby(["alg", "exp"])
       .agg(n_cel=("problema", "count"), n_ev=("n_ev", "sum"),
            familias=("familias", lambda s: ";".join(sorted(set(s)))[:70]),
            **{c: (c, "all") for c in df.columns if c.startswith("has_")})
       .reset_index())
g["n_di10"] = g[["has_" + k for k in DI10]].sum(axis=1)
g["n_pisos"] = g[["has_" + k for k in PISOS]].sum(axis=1)
g.to_csv(os.path.join(OUT, "r2_censo_amplo_alg.csv"), index=False)
pd.set_option("display.width", 260, "display.max_columns", 60)
print(g[["alg", "exp", "n_cel", "n_ev", "has_n_front1", "has_ideal",
         "has_nadir_pop", "has_nadir_front1", "n_di10", "n_pisos", "familias"]]
      .to_string(index=False))
