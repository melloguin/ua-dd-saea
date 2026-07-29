#!/usr/bin/env python3
# r3_semente_experimento.py — F5.4 / ataque adversarial a moead_media-C9b.
# Passo 3+4 do roteiro (CODIGO + controle): o colapso do GPR e funcao do
# DATASET ou do ESTADO DO RandomState GLOBAL no instante do fit?
#
# Fato de codigo (piso_offline.py:294-295 / b5_prob.py:287-288): o runner faz
#   np.random.seed(iteration_seed(seed_base(alg,42), ALG_ID, 0, USO_NUMPY))
# imediatamente antes de problem.train(SurrogateKriging); ALG_ID = 21 (piso),
# 18 (b5m), 17 (b5r) => o UNICO delta entre os dois lados da ablacao e um
# inteiro de 32 bits. E `iteration_seed` NAO depende do problema/exp/celula:
# a MESMA semente vale para as 45 celulas de um config.
# SurrogateKriging.fit usa GaussianProcessRegressor(random_state=None) =>
# os 9 restarts saem do RandomState GLOBAL.
#
# Experimento: mesmo dataset, mesma especificacao, K sementes => taxa de
# colapso por semente. READ-ONLY nos dados.
import json
import os
import sys
import time
import warnings

import numpy as np
import pyarrow.parquet as pq
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

warnings.filterwarnings('ignore')
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = os.path.dirname(os.path.abspath(__file__))

EXPMAP = {'off': 'off', 'sweep-small-mvns': 'swap_small-mvns',
          'sweep-medium-lhs': 'swap_medium-lhs', 'sweep-medium-mvns': 'swap_medium-mvns',
          'sweep-small-lhs': 'swap_small-lhs'}
SEM = {'moead_media': 4248879191, 'b5m': 3248766207, 'b5r': 2863622864}


def carrega(exp, prob, cfg='moead_media'):
    lab = EXPMAP[exp] + ('_' + prob if exp != 'off' else '')
    d = '%s/%s/%s/42' % (RES, cfg, lab if exp != 'off' else prob)
    tag = 'off' if exp == 'off' else EXPMAP[exp].replace('swap_', 'sweep-')
    f = [x for x in os.listdir(d) if x.endswith('__real.parquet')][0]
    t = pq.read_table(os.path.join(d, f)).to_pandas()
    xc = sorted([c for c in t.columns if c[0] == 'x' and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    fc = sorted([c for c in t.columns if c[0] == 'f' and c[1:].isdigit()],
                key=lambda c: int(c[1:]))
    X = t[xc].to_numpy(float); F = t[fc].to_numpy(float)
    g = pq.read_table('%s/sonda_%s.parquet' % (SND, prob)).to_pandas()
    Xs = g[xc].to_numpy(float); Fs = g[fc].to_numpy(float)
    return X, F, Xs, Fs, tag


def fit_e_mede(X, F, Xs, Fs, seed, sub):
    """Replica SurrogateKriging.fit: 1 GPR por objetivo, na ORDEM f1..fM,
    consumindo o RandomState GLOBAL (random_state=None)."""
    np.random.seed(int(seed))
    M = F.shape[1]
    out = []
    for j in range(M):
        k = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        m = GaussianProcessRegressor(alpha=0, kernel=k, n_restarts_optimizer=9)
        m.fit(X, F[:, j].reshape(-1, 1))
        mu = np.asarray(m.predict(Xs[sub])).ravel()
        f = Fs[sub, j]
        wape = float(np.abs(mu - f).sum() / max(np.abs(f).sum(), 1e-12))
        sd = float(np.std(mu))
        corr = float(np.corrcoef(mu, f)[0, 1]) if sd > 0 else float('nan')
        th = np.exp(m.kernel_.theta)
        out.append({'obj': j, 'wape': round(wape, 6),
                    'corr': None if corr != corr else round(corr, 6),
                    'std_mu_rel': round(sd / max(np.std(f), 1e-12), 8),
                    'amp': round(float(th[0]), 6), 'ls': round(float(th[1]), 6),
                    'colapso': bool(abs(wape - 1.0) <= 1e-4)})
    return out


if __name__ == '__main__':
    ALVOS = [('off', 'DTLZ2'), ('off', 'ZDT6'), ('off', 'DTLZ1'),
             ('off', 'DTLZ4'), ('off', 'BBOB_F17')]
    if len(sys.argv) > 1:
        ALVOS = [tuple(a.split(':')) for a in sys.argv[1].split(',')]
    NSEEDS = int(os.environ.get('NSEEDS', '24'))
    rng = np.random.default_rng(7)
    extras = list(rng.integers(0, 2 ** 32 - 1, NSEEDS))
    sementes = ([('piso(21)', SEM['moead_media']), ('b5m(18)', SEM['b5m']),
                 ('b5r(17)', SEM['b5r'])] + [('s%02d' % i, int(s))
                                             for i, s in enumerate(extras)])
    res = {}
    for exp, prob in ALVOS:
        X, F, Xs, Fs, tag = carrega(exp, prob)
        sub = np.arange(0, 20000, 10)          # 2.000 pontos da sonda (regua)
        cel = {'n': int(len(X)), 'D': int(X.shape[1]), 'M': int(F.shape[1]),
               'f_max': [round(float(v), 4) for v in F.max(0)],
               'f_std': [round(float(v), 4) for v in F.std(0)], 'sementes': {}}
        t0 = time.time()
        for nome, s in sementes:
            cel['sementes'][nome] = fit_e_mede(X, F, Xs, Fs, s, sub)
        cel['wall_s'] = round(time.time() - t0, 1)
        n_col = {k: sum(o['colapso'] for o in v) for k, v in cel['sementes'].items()}
        cel['colapsos_por_semente'] = n_col
        cel['resumo'] = {
            'M': int(F.shape[1]),
            'sementes_com_>=1_colapso': int(sum(v > 0 for v in n_col.values())),
            'sementes_totais': len(n_col),
            'frac_obj_colapsados': round(
                sum(n_col.values()) / (len(n_col) * F.shape[1]), 4)}
        res['%s/%s' % (exp, prob)] = cel
        print(json.dumps({('%s/%s' % (exp, prob)): cel['resumo'],
                          'piso': n_col['piso(21)'], 'b5m': n_col['b5m(18)'],
                          'wall_s': cel['wall_s']}), flush=True)
    with open(OUT + '/r3b_controles.json', 'w') as f:
        json.dump(res, f, indent=1)
    print('OK')
