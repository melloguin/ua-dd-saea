"""F5.4 — c154-J27: os TRES contra-exemplos da 'Evidencia 3' do analista, resolvidos.

O analista (c154.md secao 8) apresentou MMF1 it 1, 2 e 4 como prova de que as duas
series 'nao se alinham'. Sob a permutacao real do escritor
(delete-best + append-best) cada um deles ALINHA exatamente.
"""
import json
import os
import numpy as np
import pandas as pd

B = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154/MMF1/42"
recs = [json.loads(l) for l in open(os.path.join(B, "exp_main_c154_MMF1_42.jsonl"))]
df = pd.read_parquet(os.path.join(B, "exp_main_c154_MMF1_42__surrogate.parquet"))
on = df[df.regime == "online"]
real = pd.read_parquet(os.path.join(B, "exp_main_c154_MMF1_42__real.parquet"))
dec = {r["it"]: r for r in recs if r.get("rec") == "decision"}

for it in (1, 2, 4):
    r = dec[it]
    a = np.array(r["acqf_todos_restarts"], dtype=float)
    R = len(a)
    best = int(np.argmax(np.where(np.isfinite(a), a, -np.inf)))
    mp = [k for k in range(R) if k != best] + [best]      # linha -> restart
    blk = on[on.geracao == it]
    X = blk[["x0", "x1"]].to_numpy()
    rs = blk["real_solution_id"].to_numpy()
    print(f"\n=== MMF1 it {it} | R={R} | best(restart)={best} | "
          f"acqf_escolhido={r['acqf_escolhido']!r}")
    print(f"    permutacao linha->restart: {mp}")
    for j in range(R):
        marca = "  <== VENCEDOR (real_solution_id=%d)" % rs[j] if not pd.isna(rs[j]) else ""
        print(f"    linha {j:2d} -> restart {mp[j]:2d} | x=({X[j][0]:.7f},{X[j][1]:.7f}) "
              f"| alpha={a[mp[j]]:.16f}{marca}")
    sid = r.get("solution_id")
    if sid is not None:
        xr = real[real.solution_id == sid][["x0", "x1"]].to_numpy()[0]
        print(f"    (1) do solution_id {sid}: x=({xr[0]:.7f},{xr[1]:.7f})  "
              f"dX vs ultima linha = {np.abs(xr - X[-1]).max():.3e}")
    # a afirmacao do analista, refeita
    idx_ana = int(np.argmax(a))
    print(f"    leitura INGENUA (linha {idx_ana} <-> restart {idx_ana}): "
          f"x=({X[idx_ana][0]:.7f},{X[idx_ana][1]:.7f}) -> e o candidato de OUTRO "
          f"restart; sob a permutacao real o restart {idx_ana} esta na linha "
          f"{mp.index(idx_ana)}")
