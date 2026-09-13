#!/usr/bin/env python
"""F5.4 / e103-A25 - o teste que derruba (ou nao) o achado: ESPELHO x ARVORE CANONICA.

A F5 leu as celulas em /Users/.../resultados_experimentos/e103/{label}/42/ (espelho).
A arvore CANONICA de producao - a que o gate DI-08, o `final_eval` e o `accept.py`
leem - eh ua-dd-saea/data/experiments/{exp}/e103/.
Compara, celula a celula: inode, mtime, n de linhas, n_final do sidecar, hash.
"""
import glob
import hashlib
import json
import os
import datetime

import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
CANON = os.path.join(REPO, "data", "experiments")
ESP = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103"
OUT = os.path.dirname(os.path.abspath(__file__))


def exp_de(label):
    if label.startswith("swap_"):
        return "sweep-" + label.split("_")[1]      # swap_medium-lhs_ZDT4 -> sweep-medium-lhs
    return "off"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def info(p):
    st = os.stat(p)
    df = pd.read_parquet(p)
    side = p[:-len(".parquet")] + ".manifest.json"
    sd = json.load(open(side)) if os.path.exists(side) else {}
    return dict(n=len(df), nd=int(df.nd_pos_real.sum()), ino=st.st_ino,
                nlink=st.st_nlink, size=st.st_size, md5=md5(p)[:12],
                mtime=datetime.datetime.fromtimestamp(st.st_mtime).strftime("%H:%M:%S.%f")[:-3],
                side_n=sd.get("n_final"), side_nd=sd.get("n_nd_pos_real"))


rows = []
for label in sorted(os.listdir(ESP)):
    d = os.path.join(ESP, label, "42")
    if not os.path.isdir(d):
        continue
    fe_esp = glob.glob(os.path.join(d, "*__final.parquet"))
    if not fe_esp:
        continue
    fe_esp = fe_esp[0]
    nome = os.path.basename(fe_esp)
    fe_can = os.path.join(CANON, exp_de(label), "e103", nome)
    a = info(fe_esp)
    b = info(fe_can) if os.path.exists(fe_can) else {}
    rows.append(dict(
        celula=label, existe_canonico=bool(b),
        n_esp=a["n"], n_can=b.get("n"), nd_esp=a["nd"], nd_can=b.get("nd"),
        sideN_esp=a["side_n"], sideN_can=b.get("side_n"),
        mesmo_inode=(a["ino"] == b.get("ino")), md5_igual=(a["md5"] == b.get("md5")),
        nlink_esp=a["nlink"], nlink_can=b.get("nlink"),
        mtime_esp=a["mtime"], mtime_can=b.get("mtime"),
    ))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "espelho_vs_canonico.csv"), index=False)
pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 40)
print(df.to_string(index=False))
print()
print("celulas com md5 DIFERENTE entre espelho e canonico:",
      df.loc[~df.md5_igual, "celula"].tolist())
print("celulas com mesmo inode (hardlink vivo):", int(df.mesmo_inode.sum()), "/", len(df))
print("n_esp != 100:", df.loc[df.n_esp != 100, ["celula", "n_esp"]].to_dict("records"))
print("n_can != 100:", df.loc[df.n_can != 100, ["celula", "n_can"]].to_dict("records"))
print("sidecar do espelho != linhas do espelho:",
      df.loc[df.sideN_esp != df.n_esp, "celula"].tolist())
