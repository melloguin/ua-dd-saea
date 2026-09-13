#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 01: estrutura das 10 celulas s42 + o smoke T11. READ-ONLY."""
import json, os, glob, hashlib
import numpy as np, pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media"
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/sweep-big-mvns/treed_media"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/treed_media"


def cells():
    r = []
    for lab in sorted(os.listdir(S42)):
        d = os.path.join(S42, lab, "42")
        if not os.path.isdir(d):
            continue
        mf = glob.glob(os.path.join(d, "*_42.manifest.json"))
        assert len(mf) == 1, (lab, mf)
        r.append((lab, d, mf[0]))
    return r


def layers(d, base):
    p = lambda s: os.path.join(d, base + s)
    return dict(real=p("__real.parquet"), pop=p("__pop.parquet"),
                sur=p("__surrogate.parquet"), tim=p("__timing.parquet"),
                fin=p("__final.parquet"), jl=p(".jsonl"))


rows = []
for lab, d, mfp in cells():
    base = os.path.basename(mfp).replace(".manifest.json", "")
    L = layers(d, base)
    m = json.load(open(mfp))
    r1 = pd.read_parquet(L["real"]); r2 = pd.read_parquet(L["pop"])
    r3 = pd.read_parquet(L["sur"]); r4 = pd.read_parquet(L["tim"])
    r7 = pd.read_parquet(L["fin"]) if os.path.exists(L["fin"]) else None
    ev = [json.loads(x) for x in open(L["jl"]) if x.strip()]
    sig = [c for c in r3.columns if c.startswith("sigma_")]
    mus = [c for c in r3.columns if c.startswith("mu_")]
    busca = r3[r3.regime != "sonda"]
    sonda = r3[r3.regime == "sonda"]
    rows.append(dict(
        label=lab, status=m.get("status"), motivo=m.get("motivo_parada"),
        maxfe=m.get("maxfe"), fe_final=m.get("fe_final"), n_ger=m.get("n_geracoes"),
        t_aval_real=m["timing"].get("tempo_aval_real_s"),
        t_total=m["timing"].get("tempo_total_s"),
        t_fit=m["timing"].get("tempo_fit_surrogate_s"),
        t_busca=m["timing"].get("tempo_busca_s"),
        t_sonda=m["timing"].get("tempo_pred_sonda_s"),
        campanha_id=m.get("campanha_id", "<AUSENTE>"),
        repo_hash=(m.get("repo_hash") or "<AUSENTE>")[:12],
        schema=m.get("schema_version"),
        msl=m["params"].get("min_samples_leaf"), maxd=m["params"].get("max_depth"),
        n1=len(r1), n2=len(r2), n3=len(r3), n4=len(r4), n7=(len(r7) if r7 is not None else -1),
        n3_busca=len(busca), n3_sonda=len(sonda),
        n_ev=len(ev), recs="|".join(sorted(set(e.get("rec", "?") for e in ev))),
        regimes="|".join(sorted(set(r3.regime.unique()))),
        sigma_nan=int(r3[sig].isna().all(axis=1).sum()), sigma_cols=len(sig),
        mu_nan=int(r3[mus].isna().any(axis=1).sum()),
        rsid_null=int(r3.real_solution_id.isna().sum()),
        fe_tr_uni=sorted(set(pd.unique(r3.fe_treino_max.dropna()).tolist()))[:3],
        ger_min=int(busca.geracao.min()), ger_max=int(busca.geracao.max()),
        ger_uni=int(busca.geracao.nunique()),
        sonda_ger_null=int(sonda.geracao.isna().sum()),
        modelo_flags="|".join(sorted(set(r3.modelo_flag.dropna().unique()))),
        esp_modelo="|".join(sorted(set(r3.espaco_modelo.dropna().unique()))) if "espaco_modelo" in r3 else "?",
        colunas_n=len(r3.columns),
        tem_sonda_estrat=int((r3.regime == "sonda_estratificada").sum()),
        cols_novas="|".join([c for c in r3.columns if c in
                             ("pmid_ids", "ref_ids", "n_ref", "sonda_id", "rotulo_verdadeiro")]),
    ))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "tm11_estrutura_s42.csv"), index=False)
pd.set_option("display.width", 250, "display.max_columns", 60)
print("=== s42 (10 celulas) ===")
print(df.to_string(index=False))

# ---- o smoke T11 ----
base = "exp_sweep-big-mvns_treed_media_ZDT4_42"
L = layers(SMK, base)
m = json.load(open(os.path.join(SMK, base + ".manifest.json")))
r1 = pd.read_parquet(L["real"]); r3 = pd.read_parquet(L["sur"]); r4 = pd.read_parquet(L["tim"])
r7 = pd.read_parquet(L["fin"]); r2 = pd.read_parquet(L["pop"])
ev = [json.loads(x) for x in open(L["jl"]) if x.strip()]
print("\n=== SMOKE T11 (sweep-big-mvns/ZDT4/42) ===")
print("campanha_id:", m.get("campanha_id"), "| repo_hash:", m.get("repo_hash"), "| schema:", m.get("schema_version"))
print("n1=%d n2=%d n3=%d n4=%d n7=%d  regimes=%s" % (len(r1), len(r2), len(r3), len(r4), len(r7),
                                                     sorted(set(r3.regime.unique()))))
print("colunas ③ =", len(r3.columns))
print("eventos ⑥ =", len(ev), " recs =", sorted(set(e.get("rec", "?") for e in ev)))
print("chaves manifesto NOVAS vs s42:")
m42 = json.load(open(glob.glob(os.path.join(S42, "swap_big-mvns_ZDT4", "42", "*_42.manifest.json"))[0]))
print("  smoke-only:", sorted(set(m) - set(m42)))
print("  s42-only  :", sorted(set(m42) - set(m)))
print("  sigma_dict smoke-only:", sorted(set(m.get("sigma_dict", {})) - set(m42.get("sigma_dict", {}))))
print("  sonda smoke-only:", sorted(set(m.get("sonda", {})) - set(m42.get("sonda", {}))))
r3_42 = pd.read_parquet(glob.glob(os.path.join(S42, "swap_big-mvns_ZDT4", "42", "*__surrogate.parquet"))[0])
print("  colunas ③ smoke-only:", sorted(set(r3.columns) - set(r3_42.columns)))
print("  colunas ③ s42-only  :", sorted(set(r3_42.columns) - set(r3.columns)))
print("  timing smoke-only:", sorted(set(m["timing"]) - set(m42["timing"])))
print("  timing s42:", m42["timing"])
print("  timing smk:", m["timing"])
