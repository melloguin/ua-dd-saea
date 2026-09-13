"""F5.4 · S24 — quanto VALE o zero? Medicao direta do custo de avaliacao real.

Tres perguntas independentes:
 (A) proxy da ④: Sigma(tempo_geracao_s) - Sigma(tempo_busca_s) por celula, e a
     cobertura do wall pelos 4 componentes do manifesto (formulacao propria).
 (B) medicao DIRETA: cronometro em volta de `problems.evaluate_problem` chamado
     PONTO A PONTO (exatamente como o runner faz via FEBudget), sobre os X reais
     da ① das 5 celulas => o valor que `tempo_aval_real_s` DEVERIA ter.
 (C) controle: o mesmo cronometro aplicado aos problemas dos 4 pisos EA (MATLAB),
     comparado ao `tempo_aval_real_s` que ELES gravam => a ordem de grandeza do
     campo bate com a medicao? (se nao batesse, o campo dos outros e' que seria
     suspeito e o achado cairia).
READ-ONLY.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

from src import standalone_harness as H       # pina threads ANTES do numpy
from src import problems as _problems

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S24")
SB = ROOT / "sobol_batch"

# ── (A) proxy da ④ + cobertura do wall ───────────────────────────────────────
lin = []
for cel in sorted(SB.glob("q10_*/42")):
    man = next(cel.glob("*.manifest.json"))
    m = json.loads(man.read_text())
    t = m["timing"]
    tim = pd.read_parquet(next(cel.glob("*__timing.parquet")))
    real = pd.read_parquet(next(cel.glob("*__real.parquet")))
    sg = float(tim["tempo_geracao_s"].sum())
    sb = float(tim["tempo_busca_s"].sum())
    comp = sum(float(t[k] or 0.0) for k in
               ("tempo_fit_surrogate_s", "tempo_busca_s",
                "tempo_aval_real_s", "tempo_pred_sonda_s"))
    lin.append(dict(problema=m["problema"],
                    D=sum(1 for c in real.columns
                          if c.startswith("x") and c[1:].isdigit()),
                    n_real=len(real), n_ger=len(tim),
                    wall=t["tempo_total_s"], man_busca=t["tempo_busca_s"],
                    man_aval=t["tempo_aval_real_s"],
                    sum4_ger=sg, sum4_busca=sb, proxy_aval_opt=sg - sb,
                    cobertura=comp / t["tempo_total_s"],
                    nao_contab=1 - comp / t["tempo_total_s"]))
A = pd.DataFrame(lin).sort_values("problema")
A.to_csv(OUT / "A_proxy_e_cobertura.csv", index=False)
print("=== (A) proxy da ④ e cobertura do wall (5 celulas sobol_batch) ===")
print(A.to_string(index=False))

# ── (B) medicao DIRETA do custo de avaliacao ponto-a-ponto ───────────────────
print("\n=== (B) cronometro direto: evaluate_problem PONTO A PONTO ===")
linB = []
for cel in sorted(SB.glob("q10_*/42")):
    man = next(cel.glob("*.manifest.json"))
    m = json.loads(man.read_text())
    p = m["problema"]
    real = pd.read_parquet(next(cel.glob("*__real.parquet")))
    xc = sorted([c for c in real.columns
                 if c.startswith("x") and c[1:].isdigit()],
                key=lambda s: int(s[1:]))
    X = real[xc].to_numpy(dtype=np.float64)
    prob = H._instantiate(p)
    # aquece (JIT/import/cache do pymoo) fora do cronometro
    for i in range(20):
        _problems.evaluate_problem(prob, X[i].reshape(1, -1))
    t0 = time.perf_counter()
    for i in range(X.shape[0]):
        _problems.evaluate_problem(prob, X[i].reshape(1, -1))
    dt = time.perf_counter() - t0
    n_init = X.shape[0] - 2000
    # separa init x opt reaproveitando o custo medio (mesma f, mesmo D)
    linB.append(dict(problema=p, D=X.shape[1], n=X.shape[0], n_init=n_init,
                     t_aval_medido_s=round(dt, 4),
                     us_por_aval=round(1e6 * dt / X.shape[0], 1),
                     t_aval_init_s=round(dt * n_init / X.shape[0], 4),
                     t_aval_opt_s=round(dt * 2000 / X.shape[0], 4),
                     wall_run=m["timing"]["tempo_total_s"],
                     frac_do_wall=round(dt / m["timing"]["tempo_total_s"], 4)))
B = pd.DataFrame(linB).sort_values("problema")
B.to_csv(OUT / "B_medicao_direta_aval.csv", index=False)
print(B.to_string(index=False))
print(f"\nTOTAL medido nas 5 celulas: {B.t_aval_medido_s.sum():.3f} s "
      f"(gravado no manifesto: 0.0 s em 5/5)")

# ── (C) controle: pisos EA (MATLAB) — o campo bate com a medicao? ────────────
print("\n=== (C) controle: 4 pisos EA MATLAB, t_aval gravado x medido aqui ===")
linC = []
for cfg in ("nsga2", "nsga3", "moead", "smsemoa"):
    for man in sorted((ROOT / cfg).rglob("*.manifest.json")):
        if "__final" in man.name:
            continue
        m = json.loads(man.read_text())
        if m.get("regime") != "online":
            continue
        cel = man.parent
        try:
            real = pd.read_parquet(next(cel.glob("*__real.parquet")))
        except StopIteration:
            continue
        linC.append(dict(config=cfg, problema=m["problema"], n_real=len(real),
                         t_aval_gravado=m["timing"]["tempo_aval_real_s"],
                         us_por_aval_gravado=1e6 * m["timing"]["tempo_aval_real_s"] / len(real)))
C = pd.DataFrame(linC)
C.to_csv(OUT / "C_controle_pisos_matlab.csv", index=False)
print(C.groupby("config").agg(n_cel=("n_real", "size"),
                              n_aval_med=("n_real", "median"),
                              t_aval_med=("t_aval_gravado", "median"),
                              us_por_aval_med=("us_por_aval_gravado", "median"),
                              us_min=("us_por_aval_gravado", "min"),
                              us_max=("us_por_aval_gravado", "max")).to_string())
print("\n(us/aval do sobol_batch medido aqui, p/ comparacao:",
      f"{B.us_por_aval.min():.1f}–{B.us_por_aval.max():.1f} us)")
