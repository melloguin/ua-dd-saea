"""F5.4 · S24 — medicao FINAL (5 repeticoes, mediana) do que o zero esconde.

Substitui as versoes 02/04 (1 repeticao) — o WFG9 tem variancia de ~15% entre
repeticoes e a 1a passada subestimou. Para cada uma das 5 celulas:
  busca_mac : refaz os 200 lotes Sobol + projecao (o MESMO trabalho que o
              `tempo_busca_s` do manifesto mede) -> fator de maquina VM/Mac;
  aval_mac  : refaz as 11D-1+2000 avaliacoes reais PONTO A PONTO (o que o
              `tempo_aval_real_s` deveria ter medido);
  aval_vm   : aval_mac * fator -> o valor que o manifesto zerou, em s-VM.
Confronta ainda o proxy recomendado pela armadilha (e) do §9 do relatorio.
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
REP = 5

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
    prob = H._instantiate(p)

    def uma_busca():
        t0 = time.perf_counter()
        for g in range(1, 201):
            s = H.iteration_seed(base, ALG_ID, g, USO_SOBOL, bits32=True)
            _ = xl + _sobol_batch01(D, 10, s) * (xu - xl)
        return time.perf_counter() - t0

    def uma_aval():
        t0 = time.perf_counter()
        for i in range(X.shape[0]):
            _problems.evaluate_problem(prob, X[i].reshape(1, -1))
        return time.perf_counter() - t0

    uma_busca(); uma_aval()                                   # aquecimento
    busca_mac = float(np.median([uma_busca() for _ in range(REP)]))
    avals = [uma_aval() for _ in range(REP)]
    aval_mac = float(np.median(avals))

    busca_vm = float(m["timing"]["tempo_busca_s"])
    fator = busca_vm / busca_mac
    n_init = X.shape[0] - 2000
    proxy = float(tim.tempo_geracao_s.sum() - tim.tempo_busca_s.sum())
    lin.append(dict(
        problema=p, D=D, n=X.shape[0], n_init=n_init,
        wall_vm=m["timing"]["tempo_total_s"], busca_vm=busca_vm,
        aval_gravado=m["timing"]["tempo_aval_real_s"],
        busca_mac=round(busca_mac, 4), fator_vm_mac=round(fator, 3),
        aval_mac_med=round(aval_mac, 4),
        aval_mac_min=round(min(avals), 4), aval_mac_max=round(max(avals), 4),
        us_por_aval=round(1e6 * aval_mac / X.shape[0], 1),
        aval_vm_est=round(aval_mac * fator, 4),
        aval_vm_init=round(aval_mac * fator * n_init / X.shape[0], 4),
        frac_wall=round(aval_mac * fator / m["timing"]["tempo_total_s"], 4),
        proxy_relatorio=round(proxy, 4),
        proxy_sobre_medido=round(proxy / (aval_mac * fator), 2)))

R = pd.DataFrame(lin).sort_values("problema")
R.to_csv(OUT / "G_medicao_final.csv", index=False)
pd.set_option("display.width", 250)
print(R.to_string(index=False))
print(f"\nSOMA 5 celulas: aval real estimado = {R.aval_vm_est.sum():.3f} s-VM "
      f"de {R.wall_vm.sum():.3f} s de wall ({100*R.aval_vm_est.sum()/R.wall_vm.sum():.1f}%); "
      f"gravado no manifesto = {R.aval_gravado.sum():.1f} s")
print(f"parcela do DoE init (a 'irrecuperavel'): {R.aval_vm_init.sum():.3f} s-VM "
      f"({100*R.aval_vm_init.sum()/R.wall_vm.sum():.2f}% do wall das 5 celulas)")
print(f"proxy §9(e) do relatorio = {R.proxy_relatorio.sum():.3f} s; "
      f"razao proxy/medido por celula: "
      f"{R.proxy_sobre_medido.min():.2f}x a {R.proxy_sobre_medido.max():.2f}x")
