"""BANCADA A8 (a confirmacao que a F5.4 pediu) + prova de que o
`flag_vetores_degenerados` da T11 e CODIGO MORTO.
Somente funcoes puras do desdeo vendorizado — NAO roda celula, nao toca data/.
"""
import sys, os
import typing as _t, typing_extensions as _te
_t.Literal = getattr(_t, "Literal", _te.Literal)
import types as _ty
_st = _ty.ModuleType("pygmo"); _st.fast_non_dominated_sorting = lambda *a, **k: None
sys.modules.setdefault("pygmo", _st)
V = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/algorithms/b5_Prob-RVEA"
sys.path.insert(0, V)
import numpy as np
np.seterr(all="ignore")
from desdeo_emo.othertools.ReferenceVectors import ReferenceVectors
from desdeo_emo.othertools.ProbabilityWrong import Probability_wrong
from desdeo_emo.selection.ProbMOEAD_select import ProbMOEAD_select, P_WRONG_STATS

M, H = 2, 49
rv = ReferenceVectors(lattice_resolution=H, number_of_objectives=M)
print("[1] lattice M=%d H=%d -> n_vetores = %d   (esperado 50)" % (M, H, rv.number_of_vectors))
print("    norma dos vetores ANTES do adapt: min=%.6f max=%.6f" %
      (np.linalg.norm(rv.values, axis=1).min(), np.linalg.norm(rv.values, axis=1).max()))

# --- gatilho A8: fitness CONSTANTE na populacao (mu identico = GP degenerado) --
fit_const = np.zeros((rv.number_of_vectors, M))       # amplitude max-min = 0
rv.adapt(fit_const)
n = np.linalg.norm(rv.values, axis=1)
print("[2] apos adapt(fitness constante): norma min=%.10g max=%.10g  n_zero=%d/%d"
      % (n.min(), n.max(), int((n == 0).sum()), n.size))

# --- a jusante: pbi com weights nulo --------------------------------------
sel = ProbMOEAD_select.__new__(ProbMOEAD_select); sel.SF_type = "PBI"
mu = np.zeros((1, M)); sd = np.full((1, M), 31.622776601683793)   # o teto sqrt(1000)
pw = Probability_wrong(mean_values=mu, stddev_values=sd, n_samples=1000)
pw.vect_sample_f()
amostras = pw.f_samples[0]                     # (M, n_samples)
w_zero = rv.values[0]
val = sel.pbi(mu[0], w_zero, np.zeros(M), amostras, 500.0)
print("[3] pbi(weights=vetor nulo) -> %d/%d amostras NaN" %
      (int(np.count_nonzero(~np.isfinite(val))), val.size))

# --- o elo final: P_wrong -------------------------------------------------
p = pw.compute_probability_wrong_MC(val, val)
print("[4] compute_probability_wrong_MC(NaN, NaN) = %r   -> substitui? %s"
      % (p, bool(p > 0.5)))

# --- contraste: MESMO mu/sigma SEM o NaN (vetor sadio) --------------------
rv2 = ReferenceVectors(lattice_resolution=H, number_of_objectives=M)
val_ok = sel.pbi(mu[0], rv2.values[0], np.zeros(M), amostras, 500.0)
ps = [pw.compute_probability_wrong_MC(
        sel.pbi(mu[0], rv2.values[0], np.zeros(M),
                Probability_wrong(mean_values=mu, stddev_values=sd,
                                  n_samples=1000).__class__(
                    mean_values=mu, stddev_values=sd, n_samples=1000).__class__ and amostras, 500.0),
        val_ok) for _ in range(1)]
print("[5] contraste (vetor SADIO, mesmo mu/sigma): P_wrong = %.4f  (nao e 0,0)"
      % ps[0])

# --- o que a telemetria T11 REGISTRARIA nesse estado ----------------------
from desdeo_emo.selection.ProbMOEAD_select import _pw_registra
P_WRONG_STATS.clear()
probs = np.zeros(20)                      # o que `probabilities` vale sob NaN
_pw_registra(7, probs, int((probs > 0.5).sum()))
print("[6] p_wrong_stats no estado congelado:", P_WRONG_STATS[7][0])

# --- flag_vetores_degenerados: o caminho de atributo -----------------------
from desdeo_problem.Problem import DataProblem
print("[7] DataProblem tem .reference_vectors? %s   -> "
      "`evolver.population.problem.reference_vectors` (b5_prob.py:118) SEMPRE "
      "levanta AttributeError, capturado pelo `except Exception: return None`"
      % hasattr(DataProblem, "reference_vectors"))
class _P: pass
class _E: pass
e = _E(); e.population = _P(); e.population.problem = DataProblem.__new__(DataProblem)
sys.path.insert(0, "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea")
from src.b5_prob import _vetores_degenerados
print("[8] _vetores_degenerados(evolver_simulado) = %r   (esperado None)"
      % (_vetores_degenerados(e),))
# e o caminho CORRETO devolveria numero:
e2 = _E(); e2.reference_vectors = rv
print("[9] o caminho CORRETO (`evolver.reference_vectors`) daria: "
      "n_norma_zero=%d norma_min=%.10g norma_max=%.10g amplitude=%.10g"
      % (int((n == 0).sum()), n.min(), n.max(), n.max() - n.min()))
