"""T11 · sobol_batch · BATERIA 3 — transversais RE-MEDIDAS na s42 (READ-ONLY).

(a) `tempo_aval_real_s` em TODAS as celulas online da s42 (a alegacao do
    comentario de codigo `sobol_batch.py:200-204`: "0 zeros em 416 celulas
    alheias" / "4,110 s-VM nas 5 / 20,6% do wall / 57,15% no WFG9").
(b) minimo-comum DI-10 por config (o `n_front1` que faltava).
(c) pareamento do DoE por problema (doe_hash unico).
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

RE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
OUT = ("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/"
       "f5/t11/baterias/sobol_batch")

rows = []
for man_path in sorted(glob.glob(f"{RE}/*/*/42/*.manifest.json")):
    if "/_old/" in man_path or "__final" in man_path:
        continue
    try:
        m = json.load(open(man_path))
    except Exception as e:
        rows.append({"path": man_path, "erro": repr(e)}); continue
    t = m.get("timing") or {}
    rows.append({
        "alg": m.get("alg"), "exp": m.get("exp"), "problema": m.get("problema"),
        "regime": m.get("regime"), "status": m.get("status"),
        "tempo_aval_real_s": t.get("tempo_aval_real_s"),
        "tempo_total_s": t.get("tempo_total_s"),
        "tempo_busca_s": t.get("tempo_busca_s"),
        "tempo_fit_s": t.get("tempo_fit_surrogate_s"),
        "tem_params": "params" in m, "schema": m.get("schema_version"),
        "campanha_id": m.get("campanha_id"),
        "repo_hash": (m.get("repo_hash") or "")[:8],
        "doe_hash": (m.get("doe_hash") or "")[:16],
        "path": man_path})
df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/b3_manifestos_s42.csv", index=False)
on = df[df["regime"] == "online"]
print("celulas s42 totais:", len(df), "| online:", len(on),
      "| configs:", on["alg"].nunique())

z = on[on["tempo_aval_real_s"].fillna(-1) == 0.0]
print("\n--- online com tempo_aval_real_s == 0.0 EXATO ---")
print(z.groupby("alg").size().to_string())
print("online com NULL:", int(on["tempo_aval_real_s"].isna().sum()))
print("\nmediana de tempo_aval_real_s por config (online):")
print(on.groupby("alg")["tempo_aval_real_s"].median().sort_values().to_string())

sb = on[on["alg"] == "sobol_batch"]
print("\n--- sobol_batch: params/schema/campanha ---")
print(sb[["problema", "tem_params", "schema", "campanha_id", "repo_hash",
          "tempo_aval_real_s", "tempo_total_s"]].to_string(index=False))

# --- proxy do tempo de avaliacao pela (4) + extrapolacao do DoE
print("\n--- proxy Σ(tempo_geracao−tempo_busca) por celula do sobol_batch ---")
tot_proxy = tot_wall = 0.0
for p in ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]:
    d = f"{RE}/sobol_batch/q10_{p}/42/exp_batch_sobol_batch_{p}_42"
    tim = pd.read_parquet(d + "__timing.parquet")
    m = json.load(open(d + ".manifest.json"))
    real = pd.read_parquet(d + "__real.parquet")
    D = len([c for c in real.columns if c.startswith("x") and c[1:].isdigit()])
    n_init = 11 * D - 1
    proxy = float((tim["tempo_geracao_s"] - tim["tempo_busca_s"]).sum())
    wall = m["timing"]["tempo_total_s"]
    extrap = proxy * (1 + n_init / 2000.0)
    tot_proxy += proxy; tot_wall += wall
    print(f"  {p:10s} D={D:2d} proxy={proxy:7.4f}s  wall={wall:6.4f}s  "
          f"proxy/wall={proxy/wall:6.2%}  extrapDoE={extrap:7.4f}s "
          f"({extrap/wall:6.2%})")
print(f"  TOTAL proxy={tot_proxy:.4f}s / wall={tot_wall:.4f}s = "
      f"{tot_proxy/tot_wall:.2%}   (comentario do codigo diz 4,110 s / 20,6%)")

# --- DI-10 por config (o evento de geracao)
print("\n--- minimo comum DI-10 no ⑥ por config (s42) ---")
CAMPOS = ["fe", "f_best", "n_front1", "ideal", "nadir_pop", "nadir_front1",
          "modelo_hp", "tempo_fit_s", "tempo_busca_s", "dist_min_arquivo"]
lin = []
for alg in sorted(on["alg"].unique()):
    sub = on[on["alg"] == alg]
    jl = sub.iloc[0]["path"].replace(".manifest.json", ".jsonl")
    ev = None
    try:
        for l in open(jl):
            o = json.loads(l)
            if o.get("rec") in ("decision",) or str(o.get("rec", "")).endswith("_gen"):
                ev = o; break
    except Exception:
        pass
    if ev is None:
        continue
    lin.append({"alg": alg, "rec": ev.get("rec"),
                **{c: int(c in ev) for c in CAMPOS},
                "n_campos": sum(int(c in ev) for c in CAMPOS)})
t = pd.DataFrame(lin).sort_values("n_campos")
print(t.to_string(index=False))
t.to_csv(f"{OUT}/b3_di10_por_config.csv", index=False)

# --- pareamento do DoE
print("\n--- doe_hash unico por problema (celulas online da s42) ---")
for p in ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]:
    s = on[on["problema"] == p]
    print(f"  {p:10s} celulas={len(s):3d}  hashes distintos="
          f"{s['doe_hash'].nunique()}  ({s['doe_hash'].iloc[0]})")
