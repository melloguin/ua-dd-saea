#!/usr/bin/env python
"""T11/smsemoa — bateria 6: o RAMO INTERNO do `Reduce` deixa de ser teto T.
Fonte agora legível e LACRADA (repos.lock/PlatEMO sha256_tree fb9ed1d399d4):
  Reduce.m:20-28  M==2  -> deltaS EXATO, extremos com deltaS=inf (protegidos)
                  M>=3  -> CalHV(...,max(PopObj)*1.1, 1, 10000) = MONTE CARLO
                           com 10.000 amostras e referência MÓVEL do ÚLTIMO FRONT
Consequência testável no dado: em M=2 o `ideal` da população NUNCA piora;
em M>=3 pode piorar (nenhum extremo é protegido).
READ-ONLY."""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado'
RES = f'{ROOT}/resultados_experimentos'
OUT = f'{ROOT}/ua-dd-saea/f5/t11/baterias/smsemoa'
PROBS = sorted(os.listdir(f'{RES}/smsemoa'))

rows = []
for alg in ['smsemoa', 'nsga2', 'nsga3', 'moead']:
    for p in PROBS:
        d = f'{RES}/{alg}/{p}/42'
        if not os.path.isdir(d):
            continue
        st = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
        L = [json.loads(l) for l in open(f'{d}/{st}.jsonl')]
        h = [x for x in L if x['rec'] == 'header'][0]
        gens = [x for x in L if x['rec'] == f'{alg}_gen']
        I = np.array([g['ideal'] for g in gens], float)
        dI = np.diff(I, axis=0)
        piora = int((dI > 0).any(axis=1).sum())
        n1 = np.array([g['n_front1'] for g in gens], float)
        npop = np.array([g['n_pop'] for g in gens], float)
        rows.append(dict(alg=alg, problema=p, M=h['M'], D=h['D'], gens=len(gens),
                         trans=len(dI), ideal_piora=piora,
                         pior_piora=float(dI.max()) if len(dI) else 0.0,
                         frac_f1_media=float((n1 / npop).mean()),
                         frac_f1_1_em=int((n1 == npop).sum())))
T = pd.DataFrame(rows)
T.to_csv(f'{OUT}/ramo_reduce_ideal.csv', index=False)

print('===== O `ideal` da população piora alguma vez? (Reduce.m:20-25 protege os extremos em M=2) =====')
g = T.groupby(['alg', 'M']).agg(celulas=('problema', 'size'), trans=('trans', 'sum'),
                                piora=('ideal_piora', 'sum'))
g['%'] = (100 * g.piora / g.trans).round(2)
print(g.to_string())
print()
sm = T[T.alg == 'smsemoa']
print('smsemoa M=2: %d células · %d transições · %d pioras do ideal' % (
    (sm.M == 2).sum(), sm[sm.M == 2].trans.sum(), sm[sm.M == 2].ideal_piora.sum()))
print('smsemoa M=3: %d células · %d transições · %d pioras do ideal' % (
    (sm.M == 3).sum(), sm[sm.M == 3].trans.sum(), sm[sm.M == 3].ideal_piora.sum()))
print()
print('smsemoa · células M=3 (o ramo Monte-Carlo do CalHV, 10.000 amostras, ref móvel 1,1×max):')
print(sm[sm.M == 3][['problema', 'D', 'trans', 'ideal_piora', 'pior_piora',
                     'frac_f1_media', 'frac_f1_1_em', 'gens']].to_string(index=False))
print()
print('smsemoa · fração da população na frente-1 (governa se o ramo de HV roda sobre 20 ou sobre poucos):')
print(sm[['problema', 'M', 'frac_f1_media', 'frac_f1_1_em', 'gens']]
      .sort_values('frac_f1_media', ascending=False).to_string(index=False))
print()
print('média global frac_front1 (smsemoa): %.3f' % (sm.frac_f1_media * sm.gens).sum() / 1 if False else
      '%.3f' % float((sm.frac_f1_media * sm.gens).sum() / sm.gens.sum()))
