#!/usr/bin/env python
"""QUERY-JOIA do smsemoa: a selecao e realmente por contribuicao de hipervolume?
Teste discriminativo — serie de HV da POPULACAO (camada ②) ao longo das geracoes,
com ponto de referencia FIXO comum aos 4 pisos por problema.
SMS-EMOA (S-metric selection) deve ser quase-monotono nao-decrescente; NSGA-II
(dominancia+crowding), NSGA-III (referencia) e MOEA/D (decomposicao) NAO tem essa garantia.
Tambem: HV final da populacao por piso (papel de regua)."""
import os, glob, json, sys
import numpy as np, pandas as pd
from pymoo.indicators.hv import HV

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.dirname(os.path.abspath(__file__))
ALGS = ['smsemoa', 'nsga2', 'nsga3', 'moead']
PROBS = sorted(os.path.basename(p) for p in glob.glob(ROOT + '/smsemoa/*') if os.path.isdir(p))


def load(alg, prob):
    b = f'{ROOT}/{alg}/{prob}/42/exp_main_{alg}_{prob}_42'
    real = pd.read_parquet(b + '__real.parquet')
    pop = pd.read_parquet(b + '__pop.parquet')
    return real, pop


rows, series = [], {}
for p in PROBS:
    dat = {}
    Fs = []
    for a in ALGS:
        try:
            real, pop = load(a, p)
        except Exception as e:
            continue
        fcols = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))
        F = real[fcols].values.astype(np.float64)
        dat[a] = (F, pop)
        Fs.append(F)
    ref = np.vstack(Fs).max(axis=0)
    ref = ref + 0.01 * np.abs(ref) + 1e-9
    ind = HV(ref_point=ref)
    for a, (F, pop) in dat.items():
        gs = sorted(pop.geracao.unique())
        hvs = []
        for g in gs:
            ids = pop.loc[pop.geracao == g, 'solution_id'].values
            hvs.append(ind(F[ids]))
        hvs = np.array(hvs)
        dh = np.diff(hvs)
        rel = dh / np.maximum(np.abs(hvs[:-1]), 1e-15)
        rows.append(dict(problema=p, alg=a, N=len(pop.loc[pop.geracao == gs[0]]), n_ger=len(gs),
                         n_trans=len(dh), viol=int((rel < -1e-9).sum()),
                         viol_pct=100.0 * (rel < -1e-9).sum() / max(len(dh), 1),
                         viol_1pct=int((rel < -0.01).sum()), pior_rel=float(rel.min()) if len(rel) else np.nan,
                         hv_pop_ini=float(hvs[0]), hv_pop_fim=float(hvs[-1]),
                         ganho=float(hvs[-1] - hvs[0]), ref=json.dumps(np.round(ref, 4).tolist())))
        series[(p, a)] = hvs.tolist()

df = pd.DataFrame(rows)
df.to_csv(OUT + '/diag_hv_selecao.csv', index=False)
json.dump({f'{k[0]}|{k[1]}': v for k, v in series.items()}, open(OUT + '/serie_hv_pop.json', 'w'))
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print('=== violacoes de monotonicidade do HV populacional (ref FIXO por problema) ===')
agg = df.groupby('alg').agg(n_trans=('n_trans', 'sum'), viol=('viol', 'sum'),
                            viol_1pct=('viol_1pct', 'sum'), pior=('pior_rel', 'min')).reset_index()
agg['pct'] = 100 * agg.viol / agg.n_trans
print(agg.to_string(index=False))
print()
print('=== por problema (viol / n_trans) ===')
piv = df.pivot(index='problema', columns='alg', values='viol')
piv2 = df.pivot(index='problema', columns='alg', values='n_trans')
print((piv.astype(str) + '/' + piv2.astype(str)).to_string())
print()
print('=== HV final da POPULACAO (mesmo ref por problema) — quem termina com a melhor pop ===')
pf = df.pivot(index='problema', columns='alg', values='hv_pop_fim')
pf['vencedor'] = pf.idxmax(axis=1)
print(pf.round(4).to_string())
print()
print('vitorias:', pf.vencedor.value_counts().to_dict())
