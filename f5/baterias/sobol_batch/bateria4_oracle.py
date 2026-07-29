#!/usr/bin/env python
"""BATERIA 4 — o ORÁCULO do piso: a ① é mesmo f(x) REAL? + grid/env/hard-stop.

(1) recomputo de f = problems.evaluate_problem(X) sobre TODAS as linhas da ① das 5
    células e comparação com o f gravado (roundtrip float32);
(2) grid do `sobol_batch` no runs_matrix (q, problemas, sementes) e roteamento de env;
(3) cobertura do caminho de hard-stop (por que 0 guardas).
READ-ONLY; escreve só em f5/baterias/sobol_batch/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
RES = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = REPO / "f5" / "baterias" / "sobol_batch"
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from src import standalone_harness as H     # noqa: E402
from src import problems as P               # noqa: E402

PROBS = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]
rows = []
for prob in PROBS:
    b = RES / "sobol_batch" / f"q10_{prob}" / "42" / f"exp_batch_sobol_batch_{prob}_42"
    real = pd.read_parquet(str(b) + "__real.parquet")
    xl, xu = H._bounds(prob)
    po = H._instantiate(prob)
    D, M = len(xl), int(po.n_obj)
    X = real[[f"x{i}" for i in range(D)]].to_numpy().astype(np.float64)
    F = real[[f"f{j}" for j in range(M)]].to_numpy().astype(np.float64)
    Fr = np.asarray(P.evaluate_problem(po, X), dtype=np.float64)
    Fr32 = Fr.astype(np.float32).astype(np.float64)
    absd = np.abs(F - Fr32)
    escala = np.maximum(np.abs(F), 1e-12)
    reld = absd / escala
    rows.append({
        "problema": prob, "D": D, "M": M, "n_linhas": len(real),
        "max_abs_diff": float(absd.max()),
        "max_rel_diff": float(reld.max()),
        "mediana_rel_diff": float(np.median(reld)),
        "frac_bit_a_bit": float((absd == 0).mean()),
        "frac_rel_le_1e6": float((reld <= 1e-6).mean()),
        "n_linhas_init": int((real["fase"] == "init").sum()),
        "n_linhas_opt": int((real["fase"] == "opt").sum()),
    })
    print(f"[oracle] {prob}: max_rel {reld.max():.3e} · bit-a-bit "
          f"{(absd == 0).mean():.4f}", flush=True)

d = pd.DataFrame(rows)
d.to_csv(OUT / "oracle_recomputo.csv", index=False)

# ── grid + env ─────────────────────────────────────────────────────────────
rm = pd.read_csv(REPO / "claude_code_context" / "artifacts" / "runs_matrix.csv")
sb = rm[rm.alg == "sobol_batch"]
grid = {
    "linhas_no_grid": int(len(sb)),
    "exps": sorted(sb.exp.unique().tolist()),
    "q_distintos": sorted(pd.unique(sb.q).tolist()),
    "problemas": sorted(sb.problema.unique().tolist()),
    "n_sementes": int(sb.semente.nunique()),
    "stacks": sorted(sb["stack"].unique().tolist()),
    "envs": sorted(sb["env"].unique().tolist()),
}
envs = json.loads((REPO / "claude_code_context" / "artifacts" / "envs.json").read_text())
grid["env_declarado_envs_json"] = (envs.get("alg_env") or envs.get("algs") or
                                   {}).get("sobol_batch", "n/d")
(OUT / "grid_env.json").write_text(json.dumps(grid, indent=1, ensure_ascii=False))

# ── cobertura do hard-stop ─────────────────────────────────────────────────
hs = []
for prob in PROBS:
    xl, _ = H._bounds(prob)
    D = len(xl)
    n_init, maxfe = 11 * D - 1, 11 * D - 1 + 2000
    hs.append({"problema": prob, "D": D, "n_init": n_init, "maxfe": maxfe,
               "orcamento_infill": maxfe - n_init,
               "divide_por_q": (maxfe - n_init) % 10 == 0,
               "lotes_inteiros": (maxfe - n_init) // 10,
               "hard_stop_no_meio_do_lote_possivel": (maxfe - n_init) % 10 != 0})
pd.DataFrame(hs).to_csv(OUT / "cobertura_hardstop.csv", index=False)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
print("\n=== ORÁCULO ===")
print(d.to_string())
print("\n=== GRID/ENV ===")
print(json.dumps(grid, indent=1, ensure_ascii=False))
print("\n=== HARD-STOP ===")
print(pd.DataFrame(hs).to_string())
