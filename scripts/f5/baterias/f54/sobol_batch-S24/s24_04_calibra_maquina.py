"""F5.4 · S24 — calibracao Mac x VM-v6 e o proxy do analista posto a prova.

O `tempo_busca_s` gravado e' 100% scipy (`qmc.Sobol(...).random(q)` + projecao):
reproduzo o MESMO trabalho aqui e uso a razao como fator de maquina, p/ traduzir
o custo de avaliacao medido no Mac em "segundos-VM" e estimar quanto valeria o
`tempo_aval_real_s` que o manifesto zerou.
Tambem confronto o proxy recomendado pelo relatorio (armadilha (e) do §9),
`Sigma(tempo_geracao_s) - Sigma(tempo_busca_s)`, com a medicao direta.
READ-ONLY.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

from src import standalone_harness as H
from src import problems as _problems
from src.sobol_batch import _sobol_batch01, ALG_ID, USO_SOBOL

ROOT = Path("/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/sobol_batch")
OUT = Path("/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S24")

lin = []
for cel in sorted(ROOT.glob("q10_*/42")):
    m = json.loads(next(cel.glob("*.manifest.json")).read_text())
    p = m["problema"]
    real = pd.read_parquet(next(cel.glob("*__real.parquet")))
    tim = pd.read_parquet(next(cel.glob("*__timing.parquet")))
    xc = sorted([c for c in real.columns if c.startswith("x") and c[1:].isdigit()],
                key=lambda s: int(s[1:]))
    X = real[xc].to_numpy(dtype=np.float64)
    D = X.shape[1]
    xl, xu = H._bounds(p)
    base = H.seed_base("sobol_batch", 42)

    # (1) refaz a BUSCA (200 lotes Sobol + projecao) — o mesmo trabalho medido
    #     pelo `tempo_busca_s` do manifesto. Fator de maquina = VM / Mac.
    for g in range(1, 6):                                    # aquecimento
        _sobol_batch01(D, 10, H.iteration_seed(base, ALG_ID, g, USO_SOBOL, bits32=True))
    t0 = time.perf_counter()
    for g in range(1, 201):
        s = H.iteration_seed(base, ALG_ID, g, USO_SOBOL, bits32=True)
        _ = xl + _sobol_batch01(D, 10, s) * (xu - xl)
    busca_mac = time.perf_counter() - t0

    # (2) refaz a AVALIACAO ponto a ponto (o que o manifesto zerou)
    prob = H._instantiate(p)
    for i in range(20):
        _problems.evaluate_problem(prob, X[i].reshape(1, -1))
    t0 = time.perf_counter()
    for i in range(X.shape[0]):
        _problems.evaluate_problem(prob, X[i].reshape(1, -1))
    aval_mac = time.perf_counter() - t0

    busca_vm = float(m["timing"]["tempo_busca_s"])
    fator = busca_vm / busca_mac
    proxy = float(tim.tempo_geracao_s.sum() - tim.tempo_busca_s.sum())
    aval_vm_est = aval_mac * fator
    lin.append(dict(problema=p, D=D, n=X.shape[0],
                    busca_vm=round(busca_vm, 4), busca_mac=round(busca_mac, 4),
                    fator_vm_mac=round(fator, 3),
                    aval_mac=round(aval_mac, 4),
                    aval_vm_estimado=round(aval_vm_est, 4),
                    wall_vm=m["timing"]["tempo_total_s"],
                    frac_wall_vm=round(aval_vm_est / m["timing"]["tempo_total_s"], 4),
                    proxy_relatorio=round(proxy, 4),
                    proxy_sobre_medido=round(proxy / aval_vm_est, 2)))
R = pd.DataFrame(lin).sort_values("problema")
R.to_csv(OUT / "F_calibracao_maquina.csv", index=False)
print(R.to_string(index=False))
print(f"\nSoma nas 5 celulas — aval estimado em segundos-VM: "
      f"{R.aval_vm_estimado.sum():.3f} s de {R.wall_vm.sum():.3f} s de wall "
      f"({100*R.aval_vm_estimado.sum()/R.wall_vm.sum():.1f}%)")
print(f"Proxy do relatorio soma {R.proxy_relatorio.sum():.3f} s "
      f"=> superestima em {R.proxy_relatorio.sum()/R.aval_vm_estimado.sum():.2f}x")
