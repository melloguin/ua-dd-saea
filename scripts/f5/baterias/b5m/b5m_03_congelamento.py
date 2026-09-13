#!/usr/bin/env python
"""BATERIA b5m #3 — CONGELAMENTO DA BUSCA + ablacao D77 (b5m x moead_media).

Hipotese testada (mecanismo inferido do codigo oficial):
  GP degenerado (mu constante na populacao) => amplitude (max-min) da fitness = 0
  => ReferenceVectors.adapt zera TODOS os vetores => pbi faz weights/||weights||
  = 0/0 = NaN => compute_probability_wrong_MC devolve 0.0 => `>0.5` nunca => ZERO
  substituicoes => populacao CONGELA.
Assinatura verificavel nos dados: o inicio do congelamento cai SEMPRE numa
fronteira de `iterate()` (n_gen_per_iter=10), i.e. geracao == 1 (mod 10), porque
`manage_preferences->adapt` so roda 1x por iterate.

Saida: b5m_congelamento.csv
"""
import glob, json, os, sys
import numpy as np, pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.join(REPO, 'f5', 'baterias', 'b5m')


def carrega(alg, lab):
    d = os.path.join(RES, alg, lab, '42')
    st = glob.glob(d + '/*.jsonl')[0][:-6]
    h = json.loads(open(st + '.jsonl').readline())
    c3 = pd.read_parquet(st + '__surrogate.parquet')
    b = c3[c3.regime == 'offline']
    D, M = h['D'], h['M']
    n = int(b.geracao.max())
    pop = len(b) // n
    if pop * n != len(b):
        return None
    X = b[[f'x{i}' for i in range(D)]].values.reshape(n, pop, D)
    MU = b[[f'mu_{i}' for i in range(M)]].values.astype(np.float64).reshape(n, pop, M)
    cs = [f'sigma_{i}' for i in range(M)]
    SG = (b[cs].values.astype(np.float64).reshape(n, pop, M)
          if not b[cs].isna().all().all() else None)
    return dict(X=X, MU=MU, SG=SG, D=D, M=M, n=n, pop=pop, N=h['n_dataset'])


def diag(dd):
    X, MU = dd['X'], dd['MU']
    chg = (X[1:] != X[:-1]).any(axis=2)          # (n-1, pop)
    frac = chg.mean(axis=1)
    ativo = frac > 0
    # inicio do congelamento terminal: 1a geracao g tal que nao ha mudanca de g em diante
    if ativo.any():
        ult = int(np.nonzero(ativo)[0][-1])       # transicao g->g+1 (0-based)
        onset = ult + 2                           # geracao (1-based) a partir da qual congela
    else:
        onset = 1
    congeladas = dd['n'] - onset + 1
    # amplitude (max-min) da fitness/mu por geracao
    amp = (MU.max(axis=1) - MU.min(axis=1))       # (n, M)
    amp_tot = amp.sum(axis=1)
    amp_zero_desde = int(np.nonzero(amp_tot > 0)[0][-1] + 2) if (amp_tot > 0).any() else 1
    return dict(n_ger=dd['n'], pop=dd['pop'],
                turn_1=float(frac[0]) if len(frac) else np.nan,
                turn_mean=float(frac.mean()), turn_last=float(frac[-1]),
                gers_ativas=int(ativo.sum()), gers_congeladas=int(congeladas),
                onset_congelamento=int(onset), onset_mod10=int(onset % 10),
                amp_mu_g1=float(amp_tot[0]), amp_mu_last=float(amp_tot[-1]),
                amp_zero_desde=amp_zero_desde,
                mu_unicos=int(len(np.unique(MU))),
                sg_unicos=(int(len(np.unique(dd['SG']))) if dd['SG'] is not None else None),
                X_igual_ger1=bool((X == X[0]).all()))


labs = [os.path.basename(os.path.dirname(d))
        for d in sorted(glob.glob(os.path.join(RES, 'b5m', '*', '42')))]
rows = []
for lab in labs:
    r = {'label': lab}
    for alg in ['b5m', 'moead_media']:
        try:
            dd = carrega(alg, lab)
            d = diag(dd) if dd else {}
        except Exception as e:                       # noqa: BLE001
            d = {'erro': repr(e)[:60]}
        for k, v in d.items():
            r[f'{alg}_{k}'] = v
    rows.append(r)
    print(lab, {k: v for k, v in r.items() if 'onset' in k or 'congel' in k or 'turn_mean' in k}, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b5m_congelamento.csv'), index=False)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 60)
cols = ['label', 'b5m_n_ger', 'b5m_turn_1', 'b5m_turn_mean', 'b5m_turn_last',
        'b5m_gers_congeladas', 'b5m_onset_congelamento', 'b5m_onset_mod10',
        'b5m_mu_unicos', 'b5m_sg_unicos', 'b5m_amp_mu_last',
        'moead_media_turn_mean', 'moead_media_gers_congeladas',
        'moead_media_onset_congelamento', 'moead_media_onset_mod10',
        'moead_media_mu_unicos']
print(df[cols].to_string())
print()
print('b5m: onset ≡1 (mod 10):', int((df.b5m_onset_mod10 == 1).sum()), '/', len(df))
print('piso: onset ≡1 (mod 10):', int((df.moead_media_onset_mod10 == 1).sum()), '/', len(df))
print('b5m turnover medio (mediana das 45): %.4f' % df.b5m_turn_mean.median())
print('piso turnover medio (mediana das 45): %.4f' % df.moead_media_turn_mean.median())
print('b5m turn_1 mediana %.4f · piso turn_1 mediana %.4f' %
      (df.b5m_turn_1.median(), df.moead_media_turn_1.median()))
