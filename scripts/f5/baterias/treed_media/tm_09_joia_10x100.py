#!/usr/bin/env python
"""F5.3b · treed_media — BATERIA 09: A QUERY-JOIA — provar a decomposição 10×100 do RVEA
final a partir dos DADOS (o manifesto só a DECLARA: n_iter_final=10, n_gen_final=100).

Mecanismo: o RVEA do DESDEO ADAPTA os vetores de referência no INÍCIO de cada `iterate`
(bundle c311: "adapt no INÍCIO de cada iterate"). Com 10 iterações de 100 gerações, a
adaptação cai nas gerações 1, 101, 201, …, 901. Uma readaptação muda quem sobrevive à
seleção APD ⇒ salto no tamanho da população e/ou na estatística de μ EXATAMENTE nessas
gerações. Testamos: os saltos de |Δpop| concentram-se em g≡1 (mod 100)?
Saída: tm_joia_10x100.csv
"""
import glob, os
import numpy as np
import pandas as pd

RAIZ = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/treed_media"
DM = {"DTLZ2": (12, 3), "MMF16_20": (20, 3), "WFG9": (22, 2), "ZDT1": (30, 2), "ZDT4": (10, 2)}
FRONT = [1 + 100 * i for i in range(10)]           # 1,101,…,901
FRONT_SET = set(FRONT)

L = []
for d in sorted(glob.glob(os.path.join(RAIZ, "swap_big-*"))):
    label = os.path.basename(d)
    prob = label.split("_", 1)[1].split("_", 1)[1]
    D, M = DM[prob]
    stem = [b for b in glob.glob(os.path.join(d, "42", "*.manifest.json")) if "__final" not in b][0]
    stem = stem[: -len(".manifest.json")]
    d3 = pd.read_parquet(stem + "__surrogate.parquet")
    b = d3[d3.regime == "offline"].copy()
    b["g"] = b.geracao.astype(int)
    mus = [f"mu_{j}" for j in range(M)]
    pop = b.groupby("g").size()
    soma = b.groupby("g")[mus].sum().sum(axis=1) / pop
    dpop = pop.diff().abs().dropna()          # índice = geração de CHEGADA (g)
    dsoma = soma.diff().abs().dropna()
    r = dict(label=label, problema=prob, D=D, M=M)
    # ranking dos 9 maiores saltos de população (transições 2..1000 → 999 candidatos)
    top = dpop.sort_values(ascending=False)
    r["n_transicoes"] = int(len(dpop))
    for k in (9, 20, 50):
        tk = set(top.head(k).index)
        r[f"top{k}_em_g_mod100_eq1"] = int(len(tk & FRONT_SET))
    r["saltos_pop_nas_9_fronteiras"] = ";".join(f"{g}:{int(dpop.get(g, 0))}" for g in FRONT[1:])
    r["dpop_mediano_geral"] = float(dpop.median())
    r["dpop_mediano_fronteira"] = float(dpop.loc[[g for g in FRONT[1:] if g in dpop.index]].median())
    r["dpop_medio_geral"] = round(float(dpop.mean()), 3)
    r["dpop_medio_fronteira"] = round(float(dpop.loc[[g for g in FRONT[1:] if g in dpop.index]].mean()), 3)
    r["razao_fronteira_sobre_geral"] = round(r["dpop_medio_fronteira"] / max(r["dpop_medio_geral"], 1e-9), 2)
    r["dsoma_medio_geral"] = float(dsoma.mean())
    r["dsoma_medio_fronteira"] = float(dsoma.loc[[g for g in FRONT[1:] if g in dsoma.index]].mean())
    r["razao_dsoma"] = round(r["dsoma_medio_fronteira"] / max(r["dsoma_medio_geral"], 1e-12), 2)
    # teste de permutação: P(9 gerações aleatórias terem soma de |Δpop| ≥ observada)
    obs = float(dpop.loc[[g for g in FRONT[1:] if g in dpop.index]].sum())
    rng = np.random.default_rng(20260729)
    vals = dpop.values
    sims = np.array([rng.choice(vals, size=9, replace=False).sum() for _ in range(20000)])
    r["soma_dpop_fronteira"] = obs
    r["p_permutacao"] = float((sims >= obs).mean())
    L.append(r)
    print("ok", label, flush=True)

df = pd.DataFrame(L)
df.to_csv(os.path.join(OUT, "tm_joia_10x100.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(df.drop(columns=["saltos_pop_nas_9_fronteiras"]).to_string())
print()
print(df[["label", "saltos_pop_nas_9_fronteiras"]].to_string())
