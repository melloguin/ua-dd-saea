"""F5.4 · S24 — varredura INDEPENDENTE de `timing.tempo_aval_real_s`.

Reimplementacao do zero (nao reusa `bateria3_contrato.py`). Difere do analista em:
  - varre TODAS as celulas de TODOS os configs (nao so a s42);
  - classifica regime pelo campo `regime` do MANIFESTO (nao por lista fixa);
  - distingue 0.0 de None/ausente (o teste `== 0.0` do analista da False p/ None);
  - mede tambem `tempo_fit_surrogate_s`, `tempo_busca_s`, `tempo_pred_sonda_s`
    p/ ver se o zero e' isolado ou se o bloco inteiro e' "0.0 por default";
  - calcula a fracao do wall coberta pelos 4 componentes.
READ-ONLY sobre os resultados.
"""
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S24")

rows = []
for man in sorted(ROOT.rglob("*.manifest.json")):
    if "_old" in man.parts or "__final" in man.name:
        continue
    try:
        m = json.loads(man.read_text())
    except Exception as e:
        rows.append(dict(arquivo=str(man), erro=repr(e)))
        continue
    t = m.get("timing") or {}
    rows.append(dict(
        config=man.parts[len(ROOT.parts)],
        alg=m.get("alg"), exp=m.get("exp"), problema=m.get("problema"),
        semente=m.get("semente"), regime=m.get("regime"), status=m.get("status"),
        q=m.get("q"), tier=m.get("tier"),
        tem_bloco_timing=bool(t),
        t_total=t.get("tempo_total_s"),
        t_fit=t.get("tempo_fit_surrogate_s"),
        t_busca=t.get("tempo_busca_s"),
        t_aval=t.get("tempo_aval_real_s"),
        t_sonda=t.get("tempo_pred_sonda_s"),
        t_desp=t.get("tempo_total_despachante_s"),
        aval_ausente=("tempo_aval_real_s" not in t),
        aval_none=(t.get("tempo_aval_real_s", "SENTINELA") is None),
        aval_zero_estrito=(t.get("tempo_aval_real_s") == 0.0
                           and t.get("tempo_aval_real_s") is not None),
        arquivo=str(man),
    ))

df = pd.DataFrame(rows)
df.to_csv(OUT / "varredura_timing_TODAS_celulas.csv", index=False)
print(f"manifestos lidos: {len(df)}")
print(df.groupby("regime", dropna=False).size().to_string())

on = df[df.regime == "online"].copy()
off = df[df.regime == "offline"].copy()

def resumo(d, nome):
    print(f"\n=== {nome}: {len(d)} celulas ===")
    g = d.groupby("config").agg(
        n=("t_aval", "size"),
        n_zero=("aval_zero_estrito", "sum"),
        n_none=("aval_none", "sum"),
        n_ausente=("aval_ausente", "sum"),
        aval_min=("t_aval", "min"), aval_med=("t_aval", "median"),
        aval_max=("t_aval", "max"),
        total_med=("t_total", "median"),
    )
    g["frac_aval_med"] = (g.aval_med / g.total_med).round(4)
    print(g.to_string())
    return g

g_on = resumo(on, "ONLINE")
g_off = resumo(off, "OFFLINE")
g_on.to_csv(OUT / "resumo_online_por_config.csv")
g_off.to_csv(OUT / "resumo_offline_por_config.csv")

# --- teste do analista, replicado E na formulacao alternativa -----------------
s42_on = on[on.semente == 42]
print(f"\n--- recorte s42 online: {len(s42_on)} celulas, "
      f"{s42_on.config.nunique()} configs ---")
print(f"zeros estritos: {int(s42_on.aval_zero_estrito.sum())} "
      f"({sorted(s42_on[s42_on.aval_zero_estrito].config.unique())})")
print(f"None/ausente  : {int(s42_on.aval_none.sum())}/"
      f"{int(s42_on.aval_ausente.sum())}")

# --- o zero e' isolado no campo aval, ou o bloco inteiro? ---------------------
print("\n--- bloco timing dos 4 PISOS EA (MATLAB) + sobol_batch, s42 ---")
alvo = on[on.config.isin(["nsga2", "nsga3", "moead", "smsemoa", "sobol_batch"])
          & (on.semente == 42)]
print(alvo.groupby("config")[["t_total", "t_fit", "t_busca", "t_aval", "t_sonda"]]
      .agg(["median", "count"]).to_string())
print("\nNULOS por campo (pisos EA + sobol_batch, s42):")
for c in ["nsga2", "nsga3", "moead", "smsemoa", "sobol_batch"]:
    d = alvo[alvo.config == c]
    print(f"  {c:12s} n={len(d):3d} "
          f"fit_none={int(d.t_fit.isna().sum())} busca_none={int(d.t_busca.isna().sum())} "
          f"aval_none={int(d.t_aval.isna().sum())} "
          f"aval_zero={int((d.t_aval == 0.0).sum())}")
