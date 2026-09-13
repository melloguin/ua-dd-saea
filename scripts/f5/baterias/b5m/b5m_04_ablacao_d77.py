#!/usr/bin/env python
"""BATERIA b5m #4 — ENDPOINT ⑦ e ABLACAO D77 (b5m x moead_media x b5r x demais offline).

A metrica oficial da F5.2c le a ① (= o dataset, COMPARTILHADO) e por isso EMPATA
entre os 5 offline (achado sistemico da F5.3a). O endpoint discriminante do
offline e a ⑦ (DI-08): o conjunto final avaliado 1x na funcao VERDADEIRA.
Aqui: IGD+/HV/|ND| sobre o ND-pos-real da ⑦, por celula, para todos os configs
offline presentes — e a comparacao b5m x moead_media, que e a ABLACAO EXATA do
paper (Prob-MOEA/D x Gen-MOEA/D, mesma spec de GP, mesmo lattice, mesma rampa).

Tambem: o campo de sigma como REGUA. A sonda do b5m (20.000 pontos, mesmos X
para todos os configs) da sigma(x); avalia-se por 1-NN o sigma medio da
populacao final de cada config -> testa a predicao do paper "a selecao
probabilistica leva a populacao para regioes de MENOR incerteza".

Saida: b5m_endpoint7.csv
"""
import glob, json, os, sys
import numpy as np, pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
sys.path.insert(0, REPO); os.chdir(REPO)
from src import metrics                                        # noqa: E402
OUT = os.path.join(REPO, 'f5', 'baterias', 'b5m')

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6
print('gate D92 OK', flush=True)

ALGS = ['b5m', 'b5r', 'moead_media', 'c311', 'e103', 'treed_media']
labs = [os.path.basename(os.path.dirname(d))
        for d in sorted(glob.glob(os.path.join(RES, 'b5m', '*', '42')))]

_R = {}
def R(p):
    if p not in _R:
        _R[p] = metrics.reference_set(p)
    return _R[p]


def sonda_sigma(lab):
    """(Xs, sigma_medio) do bloco de sonda do b5m — a REGUA de incerteza."""
    st = glob.glob(os.path.join(RES, 'b5m', lab, '42', '*.jsonl'))[0][:-6]
    h = json.loads(open(st + '.jsonl').readline())
    D, M = h['D'], h['M']
    c3 = pd.read_parquet(st + '__surrogate.parquet')
    s = c3[c3.regime == 'sonda']
    Xs = s[[f'x{i}' for i in range(D)]].values.astype(np.float64)
    Sg = s[[f'sigma_{i}' for i in range(M)]].values.astype(np.float64).mean(axis=1)
    return Xs, Sg


rows = []
for lab in labs:
    Xs, Sg = sonda_sigma(lab)
    # normaliza X pelo range do proprio bloco (bounds efetivos) p/ o 1-NN
    lo, hi = Xs.min(axis=0), Xs.max(axis=0)
    rng = np.maximum(hi - lo, 1e-12)
    Xn = (Xs - lo) / rng
    for alg in ALGS:
        d = os.path.join(RES, alg, lab, '42')
        js = glob.glob(d + '/*.jsonl')
        if not js:
            continue
        st = js[0][:-6]
        f7 = st + '__final.parquet'
        if not os.path.exists(f7):
            continue
        c7 = pd.read_parquet(f7)
        prob = lab.split('_', 2)[-1] if lab.startswith('swap_') else lab
        M = sum(1 for c in c7.columns if c.startswith('f') and c[1:].isdigit())
        D = sum(1 for c in c7.columns if c.startswith('x') and c[1:].isdigit())
        F = c7[[f'f{i}' for i in range(M)]].values.astype(np.float64)
        nd = c7.nd_pos_real.values.astype(bool)
        m = metrics.metrics_of_set(F[nd], prob, ref_norm=R(prob))
        Xf = c7[[f'x{i}' for i in range(D)]].values.astype(np.float64)
        Xfn = (Xf - lo) / rng
        # 1-NN sigma (regua da sonda do b5m)
        d2 = ((Xfn[:, None, :] - Xn[None, :, :]) ** 2).sum(axis=2) if len(Xfn) * len(Xn) < 4e7 \
            else None
        if d2 is None:
            nn = np.empty(len(Xfn), int)
            for i in range(len(Xfn)):
                nn[i] = np.argmin(((Xfn[i] - Xn) ** 2).sum(axis=1))
        else:
            nn = d2.argmin(axis=1)
        sig_nn = Sg[nn]
        rows.append(dict(label=lab, problema=prob, alg=alg, n_final=len(c7),
                         n_nd=int(nd.sum()), fantasia=float(nd.mean()),
                         igd_plus=m['igd_plus'], hv=m['hv'], igd=m['igd'],
                         gd=m['gd'], spacing=m['spacing'],
                         sigma_nn_med=float(np.median(sig_nn)),
                         sigma_nn_mean=float(sig_nn.mean()),
                         x_unicos=int(len(np.unique(Xf, axis=0)))))
    print(lab, 'ok', flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b5m_endpoint7.csv'), index=False)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 60)
piv = df.pivot_table(index=['label'], columns='alg', values='igd_plus')
print('=== IGD+ do ND-pos-real da ⑦ (endpoint offline) ===')
print(piv.round(4).to_string())
print()
print('=== fantasia (nd_pos_real/n_final) ===')
print(df.pivot_table(index=['label'], columns='alg', values='fantasia').round(3).to_string())
print()
print('=== sigma 1-NN (regua sonda b5m) da populacao final ===')
print(df.pivot_table(index=['label'], columns='alg', values='sigma_nn_med').round(4).to_string())
print()
b = df[df.alg == 'b5m'].set_index('label')
p = df[df.alg == 'moead_media'].set_index('label')
com = b.index.intersection(p.index)
print('ABLACAO D77 (b5m x moead_media) em %d celulas:' % len(com))
print('  IGD+ b5m < piso: %d/%d' % (int((b.loc[com, 'igd_plus'] < p.loc[com, 'igd_plus']).sum()), len(com)))
print('  HV   b5m > piso: %d/%d' % (int((b.loc[com, 'hv'] > p.loc[com, 'hv']).sum()), len(com)))
print('  sigma_nn b5m < piso: %d/%d' % (int((b.loc[com, 'sigma_nn_med'] < p.loc[com, 'sigma_nn_med']).sum()), len(com)))
print('  fantasia b5m > piso: %d/%d' % (int((b.loc[com, 'fantasia'] > p.loc[com, 'fantasia']).sum()), len(com)))
print('  mediana IGD+ b5m %.4f · piso %.4f' % (b.loc[com, 'igd_plus'].median(), p.loc[com, 'igd_plus'].median()))
print('  mediana sigma_nn b5m %.4f · piso %.4f' % (b.loc[com, 'sigma_nn_med'].median(), p.loc[com, 'sigma_nn_med'].median()))
for alg in ALGS:
    s = df[df.alg == alg]
    print('%-12s celulas=%2d  IGD+ mediana=%.4f  fantasia mediana=%.3f  sigma_nn mediana=%.4f'
          % (alg, len(s), s.igd_plus.median(), s.fantasia.median(), s.sigma_nn_med.median()))
