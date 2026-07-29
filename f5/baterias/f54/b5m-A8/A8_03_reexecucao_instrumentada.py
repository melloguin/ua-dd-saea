#!/usr/bin/env python
"""F5.4 / b5m-A8 — RE-EXECUCAO INSTRUMENTADA (o experimento decisivo).

Reproduz o INICIO da celula real (mesmo dataset, mesma semente, mesmo caminho
de importacao do runner `src/b5_prob.py`) e instrumenta, em float64, os elos da
cadeia acusada:

    adapt(fitness) -> amplitude (max-min) EXATA em float64
                   -> norma das linhas de reference_vectors.values DEPOIS
    pbi(...)       -> fracao de NaN nas amostras de PBI
    P_wrong (MC)   -> distribuicao dos valores e quantos > 0.5
    do(...)        -> len(selection) por chamada

Roda apenas N_ITER iterates (10 geracoes cada) e CONFERE bit-a-bit (float32)
que as geracoes reproduzidas sao IDENTICAS as da ③ arquivada — sem isso os
numeros float64 nao provariam nada sobre o run real.

NAO escreve nada: nem no repo (fora desta pasta), nem no diretorio de
resultados. Monkeypatch em memoria; o vendorizado NAO e editado.

uso: A8_03_reexecucao_instrumentada.py <PROBLEMA> [N_ITER]
"""
import os, sys, json, glob, random, time
import numpy as np

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
sys.path.insert(0, REPO)
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')

PROB = sys.argv[1] if len(sys.argv) > 1 else 'DTLZ1'
N_ITER = int(sys.argv[2]) if len(sys.argv) > 2 else 3
# celula do sweep: 3o arg = 'medium-mvns' etc. (label = swap_<tier>-<dist>_<PROB>)
CELULA = sys.argv[3] if len(sys.argv) > 3 else None
LABEL = PROB if CELULA is None else 'swap_%s_%s' % (CELULA, PROB)
SEM = 42
ALG = 'b5m'

from src import b5_prob as R                                       # noqa: E402
from src import standalone_harness as H                            # noqa: E402
import pandas as pd                                                # noqa: E402

R._patch_doe_pyarrow_compat()
base = H.seed_base(ALG, SEM)
random.seed(H.iteration_seed(base, R._ALG_ID[ALG], 0, R.USO_RANDOM, bits32=True))
np.random.seed(H.iteration_seed(base, R._ALG_ID[ALG], 0, R.USO_NUMPY, bits32=True))

DataProblem, SurrogateKriging, evolvers = R._import_vendored()

_t, _d = (None, None) if CELULA is None else tuple(CELULA.split('-'))
from src import naming as _naming
if _naming.is_main_variant(_t, _d):
    _t, _d = None, None
bud, ds = H.load_offline_budget(PROB, SEM, tier=_t, dist=_d)
D, M, n_ds = ds['D'], ds['M'], ds['n']
X_ds = np.asarray(ds['X'], dtype=np.float64)
F_ds = np.asarray(ds['F'], dtype=np.float64)
print('dataset: %s D=%d M=%d N=%d  hash=%s' % (PROB, D, M, n_ds, ds['x_hash'][:12]))

xl, xu = H._bounds(PROB)
xn = ['x%d' % i for i in range(1, D + 1)]
yn = ['f%d' % i for i in range(1, M + 1)]
df = pd.DataFrame(np.hstack((X_ds, F_ds)), columns=xn + yn)
bounds_df = pd.DataFrame(np.vstack((xl, xu)), columns=xn,
                         index=['lower_bound', 'upper_bound'])
problem = DataProblem(data=df, variable_names=xn, objective_names=yn, bounds=bounds_df)
t0 = time.time()
with R._quiet():
    problem.train(SurrogateKriging)
print('fit unico: %.2f s' % (time.time() - t0))

# ─────────────────────────── instrumentacao ────────────────────────────────
from desdeo_emo.othertools.ReferenceVectors import ReferenceVectors     # noqa: E402
from desdeo_emo.selection.ProbMOEAD_select import ProbMOEAD_select      # noqa: E402
from desdeo_emo.othertools.ProbabilityWrong import Probability_wrong    # noqa: E402

LOG = {'adapt': [], 'do': [], 'pbi_nan': 0, 'pbi_tot': 0, 'p': []}
_adapt0, _pbi0, _do0 = ReferenceVectors.adapt, ProbMOEAD_select.pbi, ProbMOEAD_select.do
_mc0 = Probability_wrong.compute_probability_wrong_MC
GEN = {'n': 0}


def adapt_spy(self, fitness):
    f = np.asarray(fitness, dtype=np.float64)
    amp = f.max(axis=0) - f.min(axis=0)
    _adapt0(self, fitness)
    nr = np.linalg.norm(self.values, axis=1)
    LOG['adapt'].append(dict(
        gen_arquivada=GEN['n'] + 1, amp=amp.tolist(),
        amp_min=float(amp.min()), amp_exato_zero=bool((amp == 0).all()),
        n_amp_zero=int((amp == 0).sum()),
        linhas_norma0=int((nr == 0).sum()), n_linhas=int(len(nr)),
        norma_min=float(nr.min()), norma_max=float(nr.max()),
        nan_values=int(np.isnan(self.values).sum())))
    d = LOG['adapt'][-1]
    print('  [adapt @ ger %3d] amp=%s  amp_exato_zero=%s | linhas com norma 0: '
          '%d/%d | norma_min=%.3e norma_max=%.3e | NaN em values=%d'
          % (d['gen_arquivada'], np.array2string(amp, precision=3),
             d['amp_exato_zero'], d['linhas_norma0'], d['n_linhas'],
             d['norma_min'], d['norma_max'], d['nan_values']), flush=True)


def pbi_spy(self, objective_values, weights, ideal_point, pw, theta):
    with np.errstate(all='ignore'):
        out = _pbi0(self, objective_values, weights, ideal_point, pw, theta)
    LOG['pbi_tot'] += 1
    if np.isnan(out).any():
        LOG['pbi_nan'] += 1
    return out


def mc_spy(self, a, b):
    v = _mc0(self, a, b)
    LOG['p'].append(v)
    return v


def do_spy(self, pop, vectors, ideal, nbh, off_fx, off_unc, theta):
    with np.errstate(all='ignore'):
        out = _do0(self, pop, vectors, ideal, nbh, off_fx, off_unc, theta)
    LOG['do'].append(len(out))
    return out


ReferenceVectors.adapt = adapt_spy
ProbMOEAD_select.pbi = pbi_spy
ProbMOEAD_select.do = do_spy
Probability_wrong.compute_probability_wrong_MC = mc_spy

EVOLVER = evolvers[72]
evolver = EVOLVER(problem, use_surrogates=True, n_gen_per_iter=10,
                  total_function_evaluations=40000)
print('pop=%d  vetores=%d' % (evolver.population.pop_size,
                              evolver.reference_vectors.number_of_vectors))

marca = []
with R._quiet():
    for it in range(N_ITER):
        n_do0, n_p0 = len(LOG['do']), len(LOG['p'])
        evolver.iterate()
        GEN['n'] = evolver.population.gen_count - 1
        sel = LOG['do'][n_do0:]
        ps = np.asarray(LOG['p'][n_p0:])
        marca.append(dict(iterate=it + 1, chamadas_do=len(sel),
                          subst=int(np.sum(sel)),
                          p_nan=int(np.isnan(ps).sum()), p_zero=int((ps == 0).sum()),
                          p_maior05=int((ps > 0.5).sum()), p_n=len(ps),
                          p_med=float(np.nanmedian(ps)) if len(ps) else np.nan))
        m = marca[-1]
        print('  [iterate %d] chamadas do()=%d  substituicoes=%d | P: n=%d '
              'zeros=%d  >0,5=%d  mediana=%.4f | pbi NaN=%d/%d'
              % (m['iterate'], m['chamadas_do'], m['subst'], m['p_n'],
                 m['p_zero'], m['p_maior05'], m['p_med'],
                 LOG['pbi_nan'], LOG['pbi_tot']), flush=True)

# ─────────────────── conferencia bit-a-bit contra a ③ real ─────────────────
st = glob.glob(os.path.join(RES, ALG, LABEL, '42') + '/*.jsonl')[0][:-6]
c3 = pd.read_parquet(st + '__surrogate.parquet')
b = c3[c3.regime == 'offline']
n_arq = int(b.geracao.max()); pop = len(b) // n_arq
Xarq = b[['x%d' % i for i in range(D)]].values.reshape(n_arq, pop, D)
arc = evolver.population.individuals_archive
print('\ngeracoes reproduzidas: %d (arquivo tem %d)' % (len(arc), n_arq))
iguais, difs = 0, []
for k in sorted(arc, key=int):
    g = int(k)
    if g > n_arq:
        break
    Xr = np.asarray(arc[k], dtype=np.float64).astype(np.float32)
    if np.array_equal(Xr, Xarq[g - 1]):
        iguais += 1
    else:
        difs.append((g, float(np.abs(Xr - Xarq[g - 1]).max())))
print('geracoes BIT-A-BIT identicas a ③: %d/%d  |  divergentes: %s'
      % (iguais, min(len(arc), n_arq), difs[:5]))

print('\nRESUMO adapt (float64, o numero que a ③ float32 NAO consegue mostrar):')
for d in LOG['adapt']:
    print('  ger %3d: amp=%s exato_zero=%s linhas_norma0=%d/%d'
          % (d['gen_arquivada'], ['%.6e' % a for a in d['amp']],
             d['amp_exato_zero'], d['linhas_norma0'], d['n_linhas']))
out = dict(problema=LABEL, adapt=LOG['adapt'], iterates=marca,
           pbi_nan=LOG['pbi_nan'], pbi_tot=LOG['pbi_tot'],
           gens_iguais=iguais, n_gens_conferidas=min(len(arc), n_arq))
with open(os.path.join(REPO, 'f5', 'baterias', 'f54', 'b5m-A8',
                       'A8_03_%s.json' % LABEL), 'w') as fh:
    json.dump(out, fh, indent=1)
print('\nOK')
