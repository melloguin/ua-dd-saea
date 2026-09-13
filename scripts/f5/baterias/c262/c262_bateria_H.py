#!/usr/bin/env python
"""
BATERIA H — c262 qNEHVI: U7 na forma NORMATIVA do CONTRATO_DE_DADOS §17.6 (linha 231)
+ consolidação final dos totais do config. READ-ONLY nos dados.

H1 U7 (DI-13.10 ratificada): `tempo_geracao_s` EXCLUI a sonda ⇒
   (inv-1) fit+busca ≤ tempo_geracao_s em 100% das gerações; e
   (inv-2) fit+busca+sonda > tempo_geracao_s EXATAMENTE nas gerações com sonda.
   (A bateria A testava uma formulação ad-hoc do resíduo — esta é a normativa.)
H2 consolidação: totais do config p/ o cabeçalho do relatório.
H3 posição vs pisos com o piso de ruído entre máquinas (IGD+ 58,98% — O-18):
   c262 = v6; pisos = vm3 ⇒ o piso É aplicável.
"""
import json, glob, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/c262'
PROBS = sorted(os.path.basename(x) for x in glob.glob(f'{ROOT}/*') if os.path.isdir(x))

rows = []
for p in PROBS:
    b = f'{ROOT}/{p}/42/exp_main_c262_{p}_42'
    tim = pd.read_parquet(b + '__timing.parquet')
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    gs = {int(x['geracao']) for x in recs if x.get('rec') == 'sonda'}
    g = tim['geracao'].values
    fit = tim['tempo_fit_s'].values; bus = tim['tempo_busca_s'].values
    ger = tim['tempo_geracao_s'].values; ps = tim['tempo_pred_sonda_s'].values
    com = np.array([int(x) in gs for x in g])
    rows.append(dict(problema=p, n=len(g),
                     inv1_ok=int((fit+bus <= ger+1e-9).sum()),
                     n_sonda=int(com.sum()),
                     inv2_ok=int(((fit+bus+ps > ger+1e-9) & com).sum()),
                     falso_pos=int(((fit+bus+ps > ger+1e-9) & ~com).sum()),
                     ps_zero_fora=bool((ps[~com] == 0).all()),
                     ps_pos_dentro=bool((ps[com] > 0).all()),
                     resid_med=float(np.median(ger-fit-bus)),
                     sonda_med=float(np.median(ps[com]))))
T = pd.DataFrame(rows); T.to_csv(f'{OUT}/c262_H1_u7.csv', index=False)
pd.set_option('display.width', 260)
print('== H1 U7 normativo ==')
print(T.to_string())
print('TOTAL: inv-1 %d/%d | inv-2 %d/%d | falsos-positivos %d | ps=0 fora %s | ps>0 dentro %s'
      % (T.inv1_ok.sum(), T.n.sum(), T.inv2_ok.sum(), T.n_sonda.sum(), T.falso_pos.sum(),
         T.ps_zero_fora.all(), T.ps_pos_dentro.all()))

# ---------------- H3 ----------------
P = pd.read_csv(f'{OUT}/c262_posicao.csv')
PISO = 58.98
P['alem'] = P.delta_pct.abs() > PISO
print('\n== H3 posição vs pisos (piso de ruído IGD+ 58,98%) ==')
print('bate ALÉM do ruído %d | bate DENTRO %d | perde DENTRO %d | perde ALÉM %d (de %d)'
      % (int(((P.delta_pct < 0) & P.alem).sum()), int(((P.delta_pct < 0) & ~P.alem).sum()),
         int(((P.delta_pct > 0) & ~P.alem).sum()), int(((P.delta_pct > 0) & P.alem).sum()), len(P)))
print('vs e81 %d/%d | vs b3 %d/%d | vs b1 %d/%d | vs c154 %d/%d'
      % ((P.igd < P.igd_e81).sum(), P.igd_e81.notna().sum(),
         (P.igd < P.igd_b3).sum(), P.igd_b3.notna().sum(),
         (P.igd < P.igd_b1).sum(), P.igd_b1.notna().sum(),
         (P.igd < P.igd_c154).sum(), P.igd_c154.notna().sum()))
P.to_csv(f'{OUT}/c262_posicao.csv', index=False)
