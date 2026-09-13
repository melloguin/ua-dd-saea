#!/usr/bin/env python3
# r4_loteria_semente.py — F5.4 / ataque adversarial a moead_media-C9b.
# Passo 4 (controle): dado que a UNICA diferenca entre os dois lados da ablacao
# e a semente global (piso_offline.py:295 vs b5_prob.py:288, alg_id 21 vs 18) e
# que essa semente NAO depende da celula, a "taxa de colapso do config" e UMA
# realizacao. Aqui monto a distribuicao nula dessa realizacao com 24 sementes
# arbitrarias e vejo onde caem as sementes reais do piso e do b5m.
import json
import os

import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(OUT + '/r3_semente_experimento.json'))

cels = sorted(R)
sem = sorted(next(iter(R.values()))['sementes'])
# matriz sementes x (celula,obj) de colapso
cols, mat = [], []
for c in cels:
    M = R[c]['M']
    for j in range(M):
        cols.append('%s#o%d' % (c, j))
        mat.append([R[c]['sementes'][s][j]['colapso'] for s in sem])
X = np.array(mat, bool).T          # (n_sementes, n_pares)
tot = X.sum(1)
idx = {s: i for i, s in enumerate(sem)}
arb = [s for s in sem if s.startswith('s')]
ia = [idx[s] for s in arb]

res = {
    'celulas': cels, 'n_pares_testados': int(X.shape[1]),
    'n_sementes': int(X.shape[0]), 'n_sementes_arbitrarias': len(arb),
    'total_por_semente': {s: int(tot[idx[s]]) for s in sem},
    'nula_arbitrarias': {
        'min': int(tot[ia].min()), 'q25': float(np.percentile(tot[ia], 25)),
        'mediana': float(np.median(tot[ia])), 'q75': float(np.percentile(tot[ia], 75)),
        'max': int(tot[ia].max()), 'media': round(float(tot[ia].mean()), 2),
        'dp': round(float(tot[ia].std(ddof=1)), 2)},
    'piso_vs_b5m': {
        'piso': int(tot[idx['piso(21)']]), 'b5m': int(tot[idx['b5m(18)']]),
        'b5r': int(tot[idx['b5r(17)']]),
        'percentil_piso_na_nula': round(float((tot[ia] <= tot[idx['piso(21)']]).mean()), 3),
        'percentil_b5m_na_nula': round(float((tot[ia] <= tot[idx['b5m(18)']]).mean()), 3)},
}
# Prob. de que 2 sementes arbitrarias difiram >= o observado (piso - b5m)
obs = int(tot[idx['piso(21)']] - tot[idx['b5m(18)']])
dif = np.abs(tot[ia][:, None] - tot[ia][None, :])
iu = np.triu_indices(len(ia), 1)
res['par_de_sementes_arbitrarias'] = {
    'delta_observado_piso_menos_b5m': obs,
    'n_pares': int(len(iu[0])),
    'frac_pares_com_|delta|>=obs': round(float((dif[iu] >= abs(obs)).mean()), 4),
    'delta_mediano': float(np.median(dif[iu])), 'delta_max': int(dif[iu].max())}
# correlacao entre celulas: uma semente "ruim" e ruim em varias celulas?
percel = {c: [int(sum(R[c]['sementes'][s][j]['colapso'] for j in range(R[c]['M'])))
              for s in sem] for c in cels}
res['por_celula'] = {c: {'piso': percel[c][idx['piso(21)']],
                         'b5m': percel[c][idx['b5m(18)']],
                         'M': R[c]['M'],
                         'sementes_arbitrarias_com_colapso':
                             int(sum(1 for i in ia if percel[c][i] > 0)),
                         'de': len(ia)} for c in cels}
Xa = X[ia]
res['correlacao_media_entre_pares'] = round(float(np.nanmean(
    np.corrcoef(Xa.T.astype(float))[np.triu_indices(X.shape[1], 1)])), 4)
with open(OUT + '/r4_loteria_semente.json', 'w') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
