"""[F5-T11/b5r] PROVA EMPÍRICA: `_vetores_degenerados` do src/b5_prob.py devolve
sempre None porque o caminho de atributo está errado.

`src/b5_prob.py:118` lê `evolver.population.problem.reference_vectors.values`.
Os vetores de referência moram no EVOLVER (`BaseEA.py:182`:
`self.reference_vectors = ReferenceVectors(...)`), NÃO no problema
(`desdeo_problem/` tem ZERO ocorrências do nome). O `except Exception` da função
engole o AttributeError.

READ-ONLY: nao escreve em data/, nao chama experiments.py, nao usa AuditLogger.
Roda em tempdir. Interpretador: env_b5 (py3.7.12).
"""
import os
import sys
import tempfile

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
os.chdir(tempfile.mkdtemp(prefix="b5r_probe_"))
sys.path.insert(0, REPO)

import numpy as np                                        # noqa: E402
import pandas as pd                                       # noqa: E402
from src import b5_prob as B                               # noqa: E402

DataProblem, SurrogateKriging, evolvers = B._import_vendored()

rng = np.random.RandomState(42)
n, D, M = 40, 3, 2
X = rng.rand(n, D)
F = np.column_stack([X.sum(axis=1), ((X - 0.5) ** 2).sum(axis=1)])
xn = ["x%d" % i for i in range(D)]
fn = ["f%d" % j for j in range(M)]
df = pd.DataFrame(np.column_stack([X, F]), columns=xn + fn)
bounds = pd.DataFrame(np.vstack([np.zeros(D), np.ones(D)]), columns=xn,
                      index=["lower_bound", "upper_bound"])
prob = DataProblem(data=df, variable_names=xn, objective_names=fn,
                   bounds=bounds)
prob.train(SurrogateKriging)

ev = evolvers[7](prob, use_surrogates=True, n_gen_per_iter=10,
                 total_function_evaluations=40000)

print("== 1. o que a funcao do runner devolve HOJE ==")
print("   _vetores_degenerados(evolver) =", B._vetores_degenerados(ev))

print("== 2. a excecao que o `except Exception` engole ==")
try:
    _ = ev.population.problem.reference_vectors.values
    print("   NENHUMA — o caminho resolveu (hipotese REFUTADA)")
except Exception as e:                                     # noqa: BLE001
    print("   %s: %s" % (type(e).__name__, e))

print("== 3. o caminho CORRETO (o evolver) ==")
V = np.asarray(ev.reference_vectors.values, dtype=float)
nrm = np.linalg.norm(V, axis=1)
print("   n_vetores=%d  norma_min=%.12f  norma_max=%.12f  amplitude=%.3e  "
      "n_norma_zero=%d" % (V.shape[0], nrm.min(), nrm.max(),
                           nrm.max() - nrm.min(), int((nrm == 0).sum())))
print("   hasattr(problem,'reference_vectors') =",
      hasattr(prob, "reference_vectors"))
print("   hasattr(evolver ,'reference_vectors') =",
      hasattr(ev, "reference_vectors"))

print("== 4. p_wrong_stats / n_substituicoes no mode 7 ==")
print("   _pw_stats_da_geracao(1) =", B._pw_stats_da_geracao(1))
print("   _n_subs_da_geracao(1)   =", B._n_subs_da_geracao(1))

print("== 5. |pop| inicial == N_RV (o A30/granularidade_③) ==")
print("   N_RV=%d  |pop_inicial|=%d  chaves do archive=%s"
      % (ev.reference_vectors.number_of_vectors,
         ev.population.individuals.shape[0],
         sorted(ev.population.individuals_archive.keys())))
