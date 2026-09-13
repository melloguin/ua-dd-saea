"""F5.4 · S24 — controles positivo/negativo.

(D) cobertura do wall pelos 4 componentes em TODOS os 18 configs online:
    o "92-96% nao contabilizado" e' exclusivo do sobol_batch ou e' regra da casa?
(E) as 15 celulas do sub-estudo BATCH (sobol_batch/e81/c149, q=10, s42):
    o breakdown fit x busca x aval e' comparavel entre os 3? quanto o zero custa?
READ-ONLY.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S24")

rows = []
for man in sorted(ROOT.rglob("*.manifest.json")):
    if "_old" in man.parts or "__final" in man.name:
        continue
    m = json.loads(man.read_text())
    if m.get("regime") != "online":
        continue
    t = m.get("timing") or {}
    tot = t.get("tempo_total_s")
    comp = sum(float(t.get(k) or 0.0) for k in
               ("tempo_fit_surrogate_s", "tempo_busca_s",
                "tempo_aval_real_s", "tempo_pred_sonda_s"))
    rows.append(dict(config=man.parts[len(ROOT.parts)], exp=m.get("exp"),
                     problema=m.get("problema"), q=m.get("q"),
                     t_total=tot, t_fit=t.get("tempo_fit_surrogate_s"),
                     t_busca=t.get("tempo_busca_s"),
                     t_aval=t.get("tempo_aval_real_s"),
                     t_sonda=t.get("tempo_pred_sonda_s"),
                     cobertura=comp / tot if tot else None,
                     frac_aval=(float(t.get("tempo_aval_real_s") or 0.0) / tot)
                     if tot else None))
D = pd.DataFrame(rows)
D.to_csv(OUT / "D_cobertura_online.csv", index=False)

print("=== (D) cobertura do wall pelos 4 componentes — 18 configs ONLINE ===")
g = D.groupby("config").agg(n=("t_total", "size"),
                            cob_min=("cobertura", "min"),
                            cob_med=("cobertura", "median"),
                            cob_max=("cobertura", "max"),
                            frac_aval_med=("frac_aval", "median"))
g["nao_contab_med"] = 1 - g.cob_med
print(g.sort_values("cob_med").round(4).to_string())

print("\n=== (E) sub-estudo BATCH (q=10, s42): os 3 configs sobreviventes ===")
B = D[(D.exp == "batch")].copy()
print(B.sort_values(["config", "problema"])
      [["config", "problema", "t_total", "t_fit", "t_busca", "t_aval",
        "cobertura"]].round(4).to_string(index=False))
B.to_csv(OUT / "E_batch_q10.csv", index=False)
print("\nresumo por config (batch q=10):")
print(B.groupby("config").agg(n=("t_total", "size"),
                              wall_med=("t_total", "median"),
                              fit_med=("t_fit", "median"),
                              busca_med=("t_busca", "median"),
                              aval_med=("t_aval", "median"),
                              cob_med=("cobertura", "median")).round(4).to_string())
