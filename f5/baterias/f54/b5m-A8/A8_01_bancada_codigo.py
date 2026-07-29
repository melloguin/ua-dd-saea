#!/usr/bin/env python
"""F5.4 / b5m-A8 — BANCADA ADVERSARIAL da cadeia do congelamento.

Roda o CODIGO OFICIAL VENDORIZADO (env_b5: py3.7.12 / numpy 1.21.6 /
scipy 1.7.3 / sklearn 0.21.3) e mede, elo a elo:

  E1  ReferenceVectors.adapt(fitness) com max(fitness)==min(fitness)
      -> o que acontece com self.values? (zero? NaN? inalterado?)
  E2  ProbMOEAD_select.pbi(weights=linha zerada) -> NaN?
  E3  Probability_wrong.compute_probability_wrong_MC(NaN, NaN) -> 0.0?
  E4  ProbMOEAD_select.do(...) REAL, fim a fim, com pop degenerada
      -> selection vazia?
  E5  CONTRAFACTUAL (controle negativo): mesma pop, amplitude eps>0
      -> selection NAO vazia (~50% dos vizinhos)?
  E6  DEGENERACAO PARCIAL: amplitude zero SO no obj0 -> quantas linhas
      de values ficam com norma zero? (previsao falsificavel de quais
      subproblemas congelam)
  E7  contrafactual do proprio adapt: amplitude identica em todos os
      objetivos mas != 0 -> values muda?

Escrita: SOMENTE stdout (nenhum arquivo no repo).
"""
import sys, os
import numpy as np

VEND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/algorithms/b5_Prob-RVEA'
sys.path.insert(0, VEND)

# shims IDENTICOS aos do runner (src/b5_prob.py:34 e _stub_pygmo)
import typing as _typing, types                                      # noqa: E402
if not hasattr(_typing, 'Literal'):
    import typing_extensions as _te
    _typing.Literal = _te.Literal
if 'pygmo' not in sys.modules:
    _m = types.ModuleType('pygmo')
    _m.fast_non_dominated_sorting = lambda *a, **k: None
    sys.modules['pygmo'] = _m

from desdeo_emo.othertools.ReferenceVectors import ReferenceVectors      # noqa: E402
from desdeo_emo.othertools.ProbabilityWrong import Probability_wrong     # noqa: E402
from desdeo_emo.selection.ProbMOEAD_select import ProbMOEAD_select       # noqa: E402
from desdeo_emo.selection.MOEAD_select import MOEAD_select               # noqa: E402

np.random.seed(42)
S = 1000
SEP = '=' * 78


def head(t):
    print('\n' + SEP + '\n' + t + '\n' + SEP)


# ---------------------------------------------------------------- E1
head('E1 — ReferenceVectors.adapt com fitness CONSTANTE (max==min)')
for M, H, npop in ((2, 49, 50), (3, 13, 105)):
    rv = ReferenceVectors(lattice_resolution=H, number_of_objectives=M)
    print('M=%d H=%d -> number_of_vectors=%d (esperado %d)  |values| linha0=%.6f'
          % (M, H, rv.number_of_vectors, npop, np.linalg.norm(rv.values[0])))
    fit_const = np.tile(np.array([0.0] * M), (npop, 1))       # mu identico
    rv.adapt(fit_const)
    v = rv.values
    print('   apos adapt(const): nan=%d  inf=%d  zeros=%d/%d  norma_max=%.3e '
          'norma_min=%.3e  linhas_norma0=%d/%d'
          % (np.isnan(v).sum(), np.isinf(v).sum(), int((v == 0).sum()), v.size,
             np.linalg.norm(v, axis=1).max(), np.linalg.norm(v, axis=1).min(),
             int((np.linalg.norm(v, axis=1) == 0).sum()), v.shape[0]))
    # o guard do normalize(): norm_2[norm_2==0] = eps  => 0/eps = 0 (nao NaN)
    print('   values_planar: nan=%d  (adapt nao toca values_planar)'
          % np.isnan(rv.values_planar).sum())

# ---------------------------------------------------------------- E7
head('E7 — CONTRAFACTUAL do adapt: amplitude != 0 (identica nos M objetivos)')
rv = ReferenceVectors(lattice_resolution=49, number_of_objectives=2)
v0 = rv.values.copy()
fit = np.vstack([np.zeros(2), np.full(2, 1e-12)])            # amplitude 1e-12
rv.adapt(np.tile(fit, (25, 1)))
print('amplitude 1e-12 -> nan=%d ; ||values-values_iniciais||_max=%.3e '
      '(normalizacao CANCELA o fator escalar)'
      % (np.isnan(rv.values).sum(), np.abs(rv.values - v0).max()))
rv2 = ReferenceVectors(lattice_resolution=49, number_of_objectives=2)
fit2 = np.vstack([np.zeros(2), np.array([0.0, 1e-300])])     # SO obj1 varia
rv2.adapt(np.tile(fit2, (25, 1)))
nz = (np.linalg.norm(rv2.values, axis=1) == 0).sum()
print('amplitude (0, 1e-300) -> linhas com norma 0: %d/50 ; nan=%d'
      % (nz, np.isnan(rv2.values).sum()))

# ---------------------------------------------------------------- E6
head('E6 — DEGENERACAO PARCIAL: amplitude 0 so no obj0 (M=2 e M=3)')
for M, H in ((2, 49), (3, 13)):
    rv = ReferenceVectors(lattice_resolution=H, number_of_objectives=M)
    ini = rv.initial_values.copy()
    amp = np.ones(M); amp[0] = 0.0
    rv.adapt(np.vstack([np.zeros(M), amp]))
    norms = np.linalg.norm(rv.values, axis=1)
    idx = np.where(norms == 0)[0]
    print('M=%d: linhas com norma 0 -> %d/%d  indices=%s'
          % (M, len(idx), rv.number_of_vectors, idx.tolist()[:10]))
    for i in idx[:5]:
        print('      vetor inicial %d = %s (suporte so no obj degenerado)'
              % (i, np.round(ini[i], 6).tolist()))

# ---------------------------------------------------------------- E2/E3
head('E2/E3 — pbi(weights zerado) -> NaN ; compute_probability_wrong_MC(NaN,NaN)')
sel = ProbMOEAD_select(None, SF_type='PBI')
pw = Probability_wrong(mean_values=np.zeros((1, 2)), stddev_values=np.full((1, 2), 31.6227766),
                       n_samples=S)
pw.vect_sample_f()
samples = pw.f_samples[0]                 # (M, S)
w_zero = np.zeros(2)
with np.errstate(all='ignore'):
    fval_zero = sel.pbi(np.zeros(2), w_zero, np.zeros(2), samples, 250.0)
    fval_ok = sel.pbi(np.zeros(2), np.array([0.6, 0.8]), np.zeros(2), samples, 250.0)
print('pbi com w=0     : nan=%d/%d  (0/0 em weights/norm_weights)'
      % (np.isnan(fval_zero).sum(), fval_zero.size))
print('pbi com w=(.6,.8): nan=%d/%d  min=%.4f max=%.4f'
      % (np.isnan(fval_ok).sum(), fval_ok.size, np.nanmin(fval_ok), np.nanmax(fval_ok)))
print('MC(NaN,NaN) = %r   | MC(ok,ok) = %r'
      % (pw.compute_probability_wrong_MC(fval_zero, fval_zero),
         pw.compute_probability_wrong_MC(fval_ok, fval_ok)))
print('MC(NaN, ok) = %r   | MC(ok, NaN) = %r'
      % (pw.compute_probability_wrong_MC(fval_zero, fval_ok),
         pw.compute_probability_wrong_MC(fval_ok, fval_zero)))

# ---------------------------------------------------------------- E4/E5
head('E4/E5 — ProbMOEAD_select.do REAL (degenerado x contrafactual eps>0)')


class _P:                                  # stub minimo do problema
    def __init__(self, M): self.n_of_objectives = M


class _Pop:                                # stub minimo da Population
    def __init__(self, obj, unc, M):
        self.objectives = obj
        self.uncertainity = unc
        self.problem = _P(M)


class _RV:
    def __init__(self, values): self.values = values


def roda_do(amp_por_objetivo, tag, n_rep=20, M=2, H=49, npop=50, nb=20, seed=7):
    """Monta a populacao com mu = 0 + amp*ruido, roda adapt REAL e do() REAL."""
    rng = np.random.RandomState(seed)
    rv = ReferenceVectors(lattice_resolution=H, number_of_objectives=M)
    base = np.zeros((npop, M))
    for j in range(M):
        if amp_por_objetivo[j] > 0:
            base[:, j] = rng.rand(npop) * amp_por_objetivo[j]
    rv.adapt(base)                                       # <-- adapt OFICIAL
    sig = np.full((npop, M), 31.6227766)                 # sigma saturado (sqrt(1000))
    pop = _Pop(base, sig, M)
    ideal = base.min(axis=0)
    tot_sel, tot_cmp, nan_prob = 0, 0, 0
    for r in range(n_rep):
        nbh = rv.values[:0]                              # placeholder
        neigh = np.arange(nb) + (r % (npop - nb))
        off_fx = base[rng.randint(npop)].copy()          # offspring com o MESMO mu
        off_unc = sig[0].copy()
        with np.errstate(all='ignore'):
            out = sel.do(pop, _RV(rv.values), ideal, neigh, off_fx, off_unc, 250.0)
        tot_sel += len(out); tot_cmp += nb
    print('%-28s: substituicoes=%4d / %4d comparacoes (%.1f%%)  '
          '|linhas de values com norma 0 = %d/%d'
          % (tag, tot_sel, tot_cmp, 100.0 * tot_sel / tot_cmp,
             int((np.linalg.norm(rv.values, axis=1) == 0).sum()), npop))
    return tot_sel, tot_cmp


roda_do([0.0, 0.0], 'DEGENERADO amp=(0,0)')
roda_do([1e-12, 1e-12], 'contrafactual amp=1e-12')
roda_do([1e-3, 1e-3], 'contrafactual amp=1e-3')
roda_do([0.0, 1.0], 'parcial amp=(0,1)')

# ---------------------------------------------------------------- E4b
head('E4b — MOEAD_select (o PISO, mode 12) sob a MESMA condicao degenerada')
try:
    sel_m = MOEAD_select(None, SF_type='PBI')
    rv = ReferenceVectors(lattice_resolution=49, number_of_objectives=2)
    base = np.zeros((50, 2))
    rv.adapt(base)
    pop = _Pop(base, np.full((50, 2), 31.6227766), 2)
    tot = 0
    for r in range(20):
        neigh = np.arange(20) + (r % 30)
        with np.errstate(all='ignore'):
            out = sel_m.do(pop, _RV(rv.values), base.min(axis=0), neigh,
                           base[0].copy(), 250.0)
        tot += len(out)
    print('MOEAD_select (media) degenerado: substituicoes=%d / 400 comparacoes' % tot)
except Exception as e:                                             # noqa: BLE001
    print('MOEAD_select: %r' % (e,))
print('\nFIM DA BANCADA')
