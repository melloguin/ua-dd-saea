#!/usr/bin/env python
"""C6 — a COTA RIGOROSA de sigma^2 a partir do lnL logado, nas 25 celulas da s42.

Fatos verbatim do codigo:
  MultiObjective_EIM.m:31,57 -> sample_y_scaled = (y-min(y))./(max(y)-min(y))  => Y in [0,1] EXATO
  GP_Train.m                 -> lnL = -0.5*n*log(sigma2) - sum(log(abs(diag(L))))
                                R = R0 + eye(n)*(10+n)*eps, diag(R)=1+nugget, R PD
Hadamard (R PD): |R| <= prod(R_ii) = (1+nug)^n  =>  -0.5*log|R| >= -0.5*n*log(1+nug) ~ 0
  =>  lnL >= -0.5*n*log(sigma2)  =>  sigma2 >= exp(-2*lnL/n)
Em particular:  lnL <= 0  =>  sigma2 >= 1, isto e, a variancia de processo ESTIMADA
e >= a AMPLITUDE INTEIRA de uma variavel confinada a [0,1]  => o fit e numericamente
invalido (R^-1 amplificando), nao um modelo com pouca informacao.
READ-ONLY.
"""
import json, os
import numpy as np, pandas as pd

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'
S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238'

rows = []
for prob in sorted(os.listdir(S42)):
    b = f'{S42}/{prob}/42/exp_main_c238_{prob}_42'
    recs = [json.loads(l) for l in open(f'{b}.jsonl') if l.strip()]
    hdr = [r for r in recs if r.get('rec') == 'header'][0]
    M, D = hdr['M'], hdr['D']
    gl = sorted([r for r in recs if r.get('rec') == 'c238_gen'], key=lambda r: r['geracao'])
    for r in gl:
        n = r['n_treino']
        for j in range(M):
            L = float(r['lnL'][j])
            s2 = float(np.exp(np.clip(-2.0 * L / n, -700, 700)))
            rows.append(dict(problema=prob, D=D, geracao=r['geracao'], n=n, obj=j,
                             lnL=L, sigma2_cota=s2,
                             tmin=float(r['theta_min'][j]), tmax=float(r['theta_max'][j]),
                             tmed=float(r['theta_media'][j])))
A = pd.DataFrame(rows)
A.to_csv(f'{OUT}/sigma2_cota_s42.csv', index=False)
N = len(A)
print('=' * 100)
print('C6 — COTA INFERIOR RIGOROSA DE sigma^2 (Y in [0,1] por construcao), %d componentes-geracao' % N)
print('=' * 100)
print('  lnL <= 0  (=> sigma2 >= 1 = amplitude INTEIRA de Y) : %d/%d (%.2f%%)' % (
    int((A.lnL <= 0).sum()), N, 100 * (A.lnL <= 0).mean()))
print('  sigma2_cota > 0.25 (variancia maxima possivel de Y) : %d/%d (%.2f%%)' % (
    int((A.sigma2_cota > .25).sum()), N, 100 * (A.sigma2_cota > .25).mean()))
print('  sigma2_cota > 1e2                                   : %d ; > 1e4 : %d ; maximo = %.3g' % (
    int((A.sigma2_cota > 1e2).sum()), int((A.sigma2_cota > 1e4).sum()), A.sigma2_cota.max()))
print()
g = A.groupby(['problema', 'D']).agg(
    n_comp=('lnL', 'size'), lnL_min=('lnL', 'min'),
    neg=('lnL', lambda s: int((s <= 0).sum())),
    s2max=('sigma2_cota', 'max'), tmed_fim=('tmed', 'last')).reset_index()
g['frac_neg'] = g.neg / g.n_comp
print('  por celula (ordenado pelo pior):')
print(g.sort_values('s2max', ascending=False).to_string(index=False))
print()
print('  RESUMO: %d de 25 celulas tem ao menos 1 fit com lnL<=0 -> %s' % (
    int((g.neg > 0).sum()), g[g.neg > 0].problema.tolist()))

# perfil temporal nas celulas afetadas
print()
print('  perfil temporal nas celulas afetadas (a partir de qual geracao o lnL vira negativo):')
for p in g[g.neg > 0].problema:
    s = A[A.problema == p]
    for j in sorted(s.obj.unique()):
        t = s[s.obj == j].sort_values('geracao')
        neg = t[t.lnL <= 0]
        if len(neg):
            print('    %-9s obj%d: 1a geracao com lnL<=0 = %d de %d (n_treino=%d) ; lnL final=%.1f ; sigma2>=%.3g' % (
                p, j, int(neg.geracao.iloc[0]), int(t.geracao.max()), int(neg.n.iloc[0]),
                t.lnL.iloc[-1], t.sigma2_cota.iloc[-1]))

# cruzamento com a fracao de exploracao do c1
mec = pd.read_csv(f'{OUT}/mecanismo_s42.csv')
ex = mec.groupby('problema').agg(frac_expl_med=('frac_exploracao', 'median'),
                                 s0muda=('sigma0_muda_argmax', 'mean'),
                                 gens=('geracao', 'size')).reset_index()
J = g.merge(ex, on='problema')
print()
print('  CRUZAMENTO — as celulas com kriging degenerado exploram MAIS?')
print(J[['problema', 'D', 'neg', 'frac_neg', 's2max', 'frac_expl_med', 's0muda']]
      .sort_values('frac_neg', ascending=False).to_string(index=False))
afet = J[J.neg > 0]; sadi = J[J.neg == 0]
print('  fracao de exploracao mediana: celulas AFETADAS=%.3f  x  SADIAS=%.3f' % (
    afet.frac_expl_med.median(), sadi.frac_expl_med.median()))
print('  sigma decide o argmax: AFETADAS=%.3f  x  SADIAS=%.3f' % (afet.s0muda.median(), sadi.s0muda.median()))
