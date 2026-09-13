#!/usr/bin/env python
"""F5.4 / e103-A25 - passos 3 (CODIGO) e 4 (controle): o portao atual e o impacto metrico.

(1) Roda `check_final` (o gate DI-08, ja com o filtro DI-41) na celula suspeita e
    em controles -> o portao de HOJE reprova ou aprova a camada 7 de 200 linhas?
(2) Reconstroi a camada 7 CORRETA (subconjunto do 1o modelo_flag, exatamente o
    que `read_final_candidates` faz hoje) e compara as 5 metricas oficiais
    (igd, igd_plus, hv, gd, spacing) e a razao de fantasia contra a 7 de 200.

READ-ONLY: nao escreve nenhum parquet; so le e recomputa em memoria.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, "data")
RES = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103"
OUT = os.path.dirname(os.path.abspath(__file__))

from scripts import final_eval as fe  # noqa: E402
from src import metrics as mt  # noqa: E402
from src import problems as _problems  # noqa: E402

ALVOS = [
    ("sweep-medium-lhs", "ZDT4", "swap_medium-lhs_ZDT4", "ALVO"),
    ("sweep-medium-mvns", "ZDT4", "swap_medium-mvns_ZDT4", "controle-neg (mesma familia)"),
    ("sweep-small-lhs", "ZDT4", "swap_small-lhs_ZDT4", "controle-neg (mesmo dist)"),
    ("sweep-medium-lhs", "ZDT1", "swap_medium-lhs_ZDT1", "controle-neg (mesma celula-tier)"),
    ("off", "ZDT4", "ZDT4", "controle-neg (off)"),
    ("sweep-medium-lhs", "DTLZ2", "swap_medium-lhs_DTLZ2", "controle-neg (M=3)"),
]

print("=" * 100)
print("PASSO 3 - o portao DI-08 de HOJE (check_final, ja com o filtro DI-41) sobre cada celula")
print("=" * 100)
gate = []
for exp, prob, cel, papel in ALVOS:
    ok, msg = fe.check_final(exp, "e103", prob, 42, data_root=DATA)
    gate.append(dict(celula=cel, papel=papel, gate_ok=ok, msg=msg))
    print(f"  [{'VERDE' if ok else 'VERMELHO'}] {cel:26s} ({papel}) :: {msg}")

pd.DataFrame(gate).to_csv(os.path.join(OUT, "gate_check_final_hoje.csv"), index=False)

print()
print("=" * 100)
print("PASSO 4 - impacto metrico: camada 7 gravada (200) vs camada 7 CORRETA (100)")
print("=" * 100)


def xcols(df):
    return [c for c in df.columns if c.startswith("x") and c[1:].isdigit()]


def fcols(df):
    return [c for c in df.columns if c.startswith("f") and c[1:].isdigit()]


linhas = []
for exp, prob, cel, papel in ALVOS:
    f7 = pd.read_parquet(glob.glob(os.path.join(RES, cel, "42", "*__final.parquet"))[0])
    F_grav = f7[fcols(f7)].to_numpy(dtype=np.float64)
    nd_grav = f7.nd_pos_real.to_numpy()

    # camada 7 CORRETA: reconstruida pelo caminho oficial de hoje (filtro DI-41)
    cand = fe.read_final_candidates(exp, "e103", prob, 42, data_root=DATA)
    F_ok = fe.evaluate_final(prob, cand["X"]).astype(np.float32).astype(np.float64)
    nd_ok = np.zeros(len(F_ok), dtype=bool)
    nd_ok[list(int(i) for i in _problems._nds_filter(F_ok))] = True

    m_grav = mt.metrics_of_set(F_grav, prob)
    m_ok = mt.metrics_of_set(F_ok, prob)
    linhas.append(dict(
        celula=cel, papel=papel,
        n_grav=len(F_grav), n_ok=len(F_ok),
        nd_grav=int(nd_grav.sum()), nd_ok=int(nd_ok.sum()),
        fantasia_grav=nd_grav.sum() / len(F_grav),
        fantasia_ok=nd_ok.sum() / len(F_ok),
        **{f"{k}_grav": m_grav[k] for k in ("igd", "igd_plus", "hv", "gd", "spacing")},
        **{f"{k}_ok": m_ok[k] for k in ("igd", "igd_plus", "hv", "gd", "spacing")},
    ))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, "impacto_metrico_camada7.csv"), index=False)
pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 60)
print(df[["celula", "n_grav", "n_ok", "nd_grav", "nd_ok", "fantasia_grav",
          "fantasia_ok"]].to_string(index=False))
print()
for k in ("igd", "igd_plus", "hv", "gd", "spacing"):
    sub = df[["celula", f"{k}_grav", f"{k}_ok"]].copy()
    sub["delta_abs"] = (sub[f"{k}_grav"] - sub[f"{k}_ok"]).abs()
    print(f"--- {k}")
    print(sub.to_string(index=False))
    print()
