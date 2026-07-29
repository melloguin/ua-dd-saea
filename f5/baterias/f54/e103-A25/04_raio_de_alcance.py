#!/usr/bin/env python
"""F5.4 / e103-A25 - raio de alcance da defasagem espelho-x-canonico.

(A) e103: TODOS os arquivos das 45 celulas (7 por celula), espelho x canonico.
(B) camada 7 de TODOS os configs offline presentes no espelho.
Criterio: md5 identico (nao mtime, nao tamanho).
"""
import glob
import hashlib
import json
import os

import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
CANON = os.path.join(REPO, "data", "experiments")
ESP = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = os.path.dirname(os.path.abspath(__file__))


def exp_de(label):
    if label.startswith("swap_"):
        return "sweep-" + label.split("_")[1]
    return "off"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------- (A) e103 completo ----------
divs, tot = [], 0
for label in sorted(os.listdir(os.path.join(ESP, "e103"))):
    d = os.path.join(ESP, "e103", label, "42")
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        pe = os.path.join(d, f)
        pc = os.path.join(CANON, exp_de(label), "e103", f)
        tot += 1
        if not os.path.exists(pc):
            divs.append(dict(config="e103", celula=label, arquivo=f,
                             problema="AUSENTE no canonico"))
            continue
        if os.stat(pe).st_ino == os.stat(pc).st_ino:
            continue                                # hardlink vivo => identico
        if md5(pe) != md5(pc):
            divs.append(dict(config="e103", celula=label, arquivo=f,
                             problema="CONTEUDO DIVERGENTE",
                             size_esp=os.path.getsize(pe), size_can=os.path.getsize(pc)))
print(f"(A) e103: {tot} arquivos comparados; divergentes = {len(divs)}")
for r in divs:
    print("   ", r)

# ---------- (B) camada 7 de todos os configs ----------
rows = []
for cfg in sorted(os.listdir(ESP)):
    base = os.path.join(ESP, cfg)
    if not os.path.isdir(base) or cfg.startswith("_"):
        continue
    for label in sorted(os.listdir(base)):
        d = os.path.join(base, label, "42")
        if not os.path.isdir(d):
            continue
        for pe in sorted(glob.glob(os.path.join(d, "*__final.parquet"))):
            f = os.path.basename(pe)
            pc = os.path.join(CANON, exp_de(label), cfg, f)
            ne = len(pd.read_parquet(pe, columns=["nd_pos_real"]))
            nc = len(pd.read_parquet(pc, columns=["nd_pos_real"])) if os.path.exists(pc) else None
            side = json.load(open(pe[:-8] + ".manifest.json")) if os.path.exists(pe[:-8] + ".manifest.json") else {}
            rows.append(dict(config=cfg, celula=label, n_esp=ne, n_can=nc,
                             sideN=side.get("n_final"),
                             igual=(os.path.exists(pc) and
                                    (os.stat(pe).st_ino == os.stat(pc).st_ino or md5(pe) == md5(pc)))))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "raio_camada7_todos_configs.csv"), index=False)
print()
print(f"(B) camada 7: {len(df)} arquivos em {df.config.nunique()} configs")
print("   por config, n_esp:", df.groupby("config").n_esp.agg(["min", "max", "count"]).to_dict("index"))
ruins = df[~df.igual]
print("   ESPELHO != CANONICO:", ruins[["config", "celula", "n_esp", "n_can"]].to_dict("records"))
print("   n_esp != n_can:", df[df.n_esp != df.n_can][["config", "celula", "n_esp", "n_can"]].to_dict("records"))
