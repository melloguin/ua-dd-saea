#!/usr/bin/env python
"""F5.4 / b5m-A8 — TESTE ADVERSARIAL POR DADO (independente do analista).

Prediccao FALSIFICAVEL derivada do codigo oficial (bancada A8_01):

  P1  (bicondicional) a busca congela a partir da geracao G  <=>  existe uma
      FRONTEIRA de iterate B = 10k+1 (k>=0) com amplitude(mu) EXATAMENTE 0 em
      TODOS os M objetivos na geracao B, e G = o menor B nessa condicao.
      -> se congelar sem amplitude-zero: cadeia REFUTADA
      -> se houver amplitude-zero numa fronteira e a busca NAO congelar: REFUTADA
  P2  (degeneracao PARCIAL) se apenas um subconjunto J de objetivos tem
      amplitude 0 numa fronteira, entao congelam SOMENTE os slots i cujo vetor
      inicial do lattice tem suporte contido em J (norma zerada pelo adapt) —
      p.ex. J={obj0} => so o slot do vetor (1,0,...,0).
  P3  (controle cruzado, fora da amostra) o piso `moead_media` (MOEAD_select,
      media) usa o MESMO adapt e o MESMO pbi => tem de congelar exatamente nas
      SUAS celulas de GP degenerado (p.ex. DTLZ2), e nao nas do b5m.

Reimplementacao INDEPENDENTE do lattice Das-Dennis (nao usa o repo vendorizado).
Escrita: SOMENTE em f5/baterias/f54/b5m-A8/.
"""
import glob, json, os
from itertools import combinations

import numpy as np
import pandas as pd

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A8'
GEN_PER_ITER = 10


def lattice(H, M):
    """Das-Dennis / simplex-lattice, reimplementado do zero (espelha _create)."""
    nv = 0
    from math import comb as _c
    nv = _c(H + M - 1, M - 1)
    t1 = np.array(list(combinations(range(1, M + H), M - 1)))
    t2 = np.array([list(range(M - 1))] * nv)
    t = t1 - t2 - 1
    w = np.zeros((nv, M), dtype=int)
    w[:, 0] = t[:, 0]
    for i in range(1, M - 1):
        w[:, i] = t[:, i] - t[:, i - 1]
    w[:, -1] = H - t[:, -1]
    v = w / H
    return v / np.linalg.norm(v, axis=1)[:, None]


LAT = {2: lattice(49, 2), 3: lattice(13, 3)}


def carrega(alg, lab):
    d = os.path.join(RES, alg, lab, '42')
    js = glob.glob(d + '/*.jsonl')
    if not js:
        return None
    st = js[0][:-6]
    h = json.loads(open(st + '.jsonl').readline())
    c3 = pd.read_parquet(st + '__surrogate.parquet')
    b = c3[c3.regime == 'offline']
    D, M = h['D'], h['M']
    n = int(b.geracao.max())
    pop = len(b) // n
    assert pop * n == len(b), (alg, lab, len(b), n)
    X = b[['x%d' % i for i in range(D)]].values.reshape(n, pop, D)
    MU = b[['mu_%d' % i for i in range(M)]].values.astype(np.float64).reshape(n, pop, M)
    SG = b[['sigma_%d' % i for i in range(M)]].values.astype(np.float64).reshape(n, pop, M)
    return dict(X=X, MU=MU, SG=SG, D=D, M=M, n=n, pop=pop)


def analisa(alg, lab):
    dd = carrega(alg, lab)
    if dd is None:
        return None
    X, MU, M, n, pop = dd['X'], dd['MU'], dd['M'], dd['n'], dd['pop']
    chg = (X[1:] != X[:-1]).any(axis=2)            # (n-1, pop) mudou o slot?
    ativo = chg.any(axis=1)
    onset = int(np.nonzero(ativo)[0][-1]) + 2 if ativo.any() else 1   # 1-based
    congeladas = n - onset + 1
    amp = MU.max(axis=1) - MU.min(axis=1)          # (n, M)
    zero_all = (amp == 0).all(axis=1)              # amplitude EXATA 0 nos M obj
    # fronteiras de iterate: geracoes 1, 11, 21, ... (1-based)
    bnd = np.arange(1, n + 1, GEN_PER_ITER)
    b_zero = [int(g) for g in bnd if zero_all[g - 1]]
    onset_pred = b_zero[0] if b_zero else None
    # P2 — degeneracao parcial: objetivos com amplitude 0 na 1a fronteira
    # que tenha ALGUM objetivo zerado (mas nao todos)
    V = LAT[M]
    parcial_b, parcial_J, slots_pred = None, None, []
    for g in bnd:
        z = np.where(amp[g - 1] == 0)[0]
        if len(z) and len(z) < M:
            parcial_b, parcial_J = int(g), z.tolist()
            sup_ok = (V[:, [j for j in range(M) if j not in z]] == 0).all(axis=1)
            slots_pred = np.where(sup_ok)[0].tolist()
            break
    # slots que param de mudar cedo (ultima transicao em que cada slot mudou)
    ult_slot = np.where(chg.any(axis=0), chg.shape[0] - np.argmax(chg[::-1], axis=0), 0)
    slots_mortos_apos = None
    if parcial_b is not None and onset > parcial_b:
        # slots congelados a partir de parcial_b (nenhuma mudanca de parcial_b em diante)
        slots_mortos_apos = np.where(~chg[parcial_b - 1:].any(axis=0))[0].tolist()
    return dict(
        alg=alg, label=lab, M=M, pop=pop, n_ger=n,
        onset_obs=onset, congeladas=congeladas,
        turn_1=float(chg[0].mean()), turn_mean=float(chg.mean()),
        amp_g1=float(amp[0].sum()), amp_last=float(amp[-1].sum()),
        n_ger_amp_zero=int(zero_all.sum()),
        onset_pred=onset_pred,
        casa=(onset_pred == onset) if (onset_pred is not None or congeladas == 0)
        else (congeladas == 0),
        mu_unicos=int(len(np.unique(MU))),
        sg_unicos=int(len(np.unique(dd['SG']))),
        X_ident_ultima=bool((X[-1] == X[-1][0]).all()),
        parcial_bnd=parcial_b, parcial_J=str(parcial_J), slots_pred=str(slots_pred),
        slots_mortos=str(slots_mortos_apos if slots_mortos_apos is None
                         else slots_mortos_apos[:8]),
        n_slots_mortos=(None if slots_mortos_apos is None else len(slots_mortos_apos)),
    )


labs = sorted(os.path.basename(os.path.dirname(d))
              for d in glob.glob(os.path.join(RES, 'b5m', '*', '42')))
rows = []
for alg in ('b5m', 'moead_media'):
    for lab in labs:
        try:
            r = analisa(alg, lab)
        except Exception as e:                                    # noqa: BLE001
            r = dict(alg=alg, label=lab, erro=repr(e)[:80])
        if r:
            rows.append(r)
            print('%-12s %-28s onset_obs=%-4s onset_pred=%-6s congel=%-4s '
                  'amp_last=%.3e turn_mean=%.4f' %
                  (r['alg'], r['label'], r.get('onset_obs'), r.get('onset_pred'),
                   r.get('congeladas'), r.get('amp_last', np.nan),
                   r.get('turn_mean', np.nan)), flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'A8_dados_predicao.csv'), index=False)

print('\n===== P1 — bicondicional congelamento <-> amplitude zero em fronteira =====')
for alg in ('b5m', 'moead_media'):
    d = df[df.alg == alg]
    congela = d.congeladas > 0
    tem_pred = d.onset_pred.notna()
    ok = (d.onset_pred == d.onset_obs) | ((~congela) & (~tem_pred))
    print('%-12s celulas=%d | congelam=%d | tem fronteira amp-zero=%d | '
          'onset_pred==onset_obs em %d/%d | FALSOS POS=%d | FALSOS NEG=%d'
          % (alg, len(d), int(congela.sum()), int(tem_pred.sum()),
             int((d.onset_pred == d.onset_obs).sum()), len(d),
             int((tem_pred & ~congela).sum()), int((congela & ~tem_pred).sum())))
    ruim = d[~ok]
    if len(ruim):
        print(ruim[['label', 'onset_obs', 'onset_pred', 'congeladas',
                    'n_ger_amp_zero']].to_string())

print('\n===== total de geracoes congeladas (b5m) =====')
d = df[df.alg == 'b5m']
print('soma congeladas=%d de %d geracoes arquivadas; celulas com congelamento=%d'
      % (d.congeladas.sum(), d.n_ger.sum(), int((d.congeladas > 0).sum())))
print(d[d.congeladas > 0][['label', 'n_ger', 'onset_obs', 'onset_pred',
                           'congeladas', 'mu_unicos', 'sg_unicos',
                           'X_ident_ultima']].to_string())

print('\n===== P2 — degeneracao PARCIAL (slots previstos x slots mortos) =====')
p = df[df.parcial_bnd.notna()]
print(p[['alg', 'label', 'M', 'parcial_bnd', 'parcial_J', 'slots_pred',
         'n_slots_mortos', 'slots_mortos', 'congeladas']].to_string())

print('\n===== P3 — controle cruzado: quem congela em cada config =====')
print(df[df.congeladas > 0][['alg', 'label', 'onset_obs', 'congeladas',
                             'mu_unicos']].to_string())
