"""T04 — quanto o critério do CÓDIGO custa contra o critério do PAPER, agora que a
grandeza `c(k)` (nº de folhas visitadas SEM GP, somado nos objetivos) é reconstruível.

Critério do paper (§3.1): parar quando TODAS as soluções da população caem em folhas
COM GPR  ⟺  c(k) == 0.
Critério do código (B15.8): parar quando c(k)+c(k-1) == 0 E k > 5.

Mede, por célula: k_paper = 1ª iteração com c(k)==0 · k_codigo = I_eff observado ·
gerações de busca gastas a mais/a menos (51 por iteração).
READ-ONLY. Escreve só nesta pasta.
"""
import os
import numpy as np, pandas as pd

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'
r = pd.read_csv(os.path.join(OUT, 't01_delta_iter.csv'))
c = pd.read_csv(os.path.join(OUT, 't01_delta_cel.csv'))

rows = []
for lab, g in r.groupby('label'):
    g = g.sort_values('it')
    cel = c[c.label == lab].iloc[0]
    zer = g[g.c_k == 0]
    k_paper = int(zer.it.min()) if len(zer) else None      # 1ª it com cobertura total
    I = int(cel.I_eff); Imax = int(np.ceil(cel.N / (10 * cel.D)))
    rows.append(dict(label=lab, tier=cel.tier, dist=cel.dist, problema=cel.problema,
                     D=int(cel.D), N=int(cel.N), I_eff=I, I_max=Imax,
                     k_paper=k_paper, es=bool(cel.early_stop_disparou),
                     delta_it=(I - k_paper) if k_paper else None,
                     ger_extra=51 * (I - k_paper) if k_paper else None))
d = pd.DataFrame(rows).sort_values(['tier', 'label'])
d.to_csv(os.path.join(OUT, 't04_criterio.csv'), index=False)
print(d.to_string(index=False))
sub = d[d.k_paper.notna()]
print('\ncélulas em que o critério do PAPER seria satisfeito: %d/%d' % (len(sub), len(d)))
print('iterações a MAIS que o código roda: mediana %.0f  (min %d  máx %d)'
      % (sub.delta_it.median(), sub.delta_it.min(), sub.delta_it.max()))
print('gerações de busca a MAIS: Σ = %d (de %d gerações de construção)'
      % (sub.ger_extra.sum(), (d.I_eff * 51).sum()))
print('\npor tier:')
print(sub.groupby('tier').agg(n=('label', 'size'), k_paper_med=('k_paper', 'median'),
                              I_eff_med=('I_eff', 'median'),
                              extra_med=('delta_it', 'median'),
                              extra_ger=('ger_extra', 'sum')).to_string())
print('\ncélulas em que o código NUNCA atinge c(k)=0 (roda até I_max ou early-stop parcial):')
print(d[d.k_paper.isna()][['label', 'I_eff', 'I_max', 'es']].to_string(index=False))
