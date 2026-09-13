#!/usr/bin/env python
"""B05 — saude em escala: sonda (regua comum F5.2e + analise propria), trajetorias de 20 checkpoints,
posicao vs pisos, e a divergencia numerica do RBF (mu fora do envelope de f)."""
import json, os, sys, glob
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = os.path.dirname(os.path.abspath(__file__))
PISOS = ['nsga2', 'nsga3', 'smsemoa', 'moead']

son = pd.read_csv(os.path.join(F5, 'sonda_f52e.csv'))
son = son[(son.alg == 'c141') & (son.exp == 'main')]
met = pd.read_csv(os.path.join(F5, 'metricas_finais_f52c.csv'))
met = met[met.exp == 'main']

rows = []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]
    D, M = h['D'], h['M']
    mc = [f'mu_{i}' for i in range(M)]
    fc = [f'f{i}' for i in range(M)]
    so = sur[sur.regime == 'sonda']
    gab = pd.read_parquet(os.path.join(SND, f'sonda_{pb}.parquet'))
    gfc = [c for c in gab.columns if c.startswith('f') and c[1:].isdigit()]
    Fg = gab[gfc].values.astype(np.float64)[:2000]

    blocos = sorted(so.geracao.unique())
    wa, co, sp, amp = [], [], [], []
    from scipy.stats import spearmanr
    for gnum in blocos:
        mu = so[so.geracao == gnum][mc].values.astype(np.float64)
        wa.append(np.abs(mu - Fg).sum(0) / np.abs(Fg).sum(0))
        co.append([np.corrcoef(mu[:, j], Fg[:, j])[0, 1] for j in range(M)])
        sp.append([spearmanr(mu[:, j], Fg[:, j]).statistic for j in range(M)])
        amp.append((mu.min(), mu.max()))
    wa = np.array(wa); co = np.array(co); sp = np.array(sp)
    s = son[son.problema == pb]
    # trajetoria
    tj = json.load(open(os.path.join(F5, 'trajetorias', f'main_c141_{pb}_42.json')))
    tv = np.array([x['igd_plus'] for x in tj], float)
    thv = np.array([x['hv'] for x in tj], float)
    tnd = np.array([x['n_nd'] for x in tj], float)
    viol = int((np.diff(tv) > 1e-12).sum())

    mm = met[met.problema == pb]
    c = mm[mm.alg == 'c141']
    pis = mm[mm.alg.isin(PISOS)].sort_values('igd_plus')
    sa = mm[~mm.alg.isin(PISOS)].sort_values('igd_plus')
    rows.append(dict(
        problema=pb, D=D, M=M, n_blocos=len(blocos),
        wape_1o=float(wa[0].mean()), wape_ult=float(wa[-1].mean()),
        dwape_pct=float(100 * (wa[-1].mean() / wa[0].mean() - 1)),
        wape_min=float(wa.mean(1).min()), wape_max=float(wa.mean(1).max()),
        corr_1o=float(co[0].mean()), corr_ult=float(co[-1].mean()),
        sp_1o=float(sp[0].mean()), sp_ult=float(sp[-1].mean()), sp_min=float(sp.mean(1).min()),
        mu_min=float(min(a for a, b in amp)), mu_max=float(max(b for a, b in amp)),
        f_min=float(Fg.min()), f_max=float(Fg.max()),
        fora_envelope=float(max(b for a, b in amp) > 1.5 * Fg.max() or min(a for a, b in amp) < Fg.min() - 0.5 * abs(Fg.max())),
        wape_oficial_1o=float(s[s.bloco == s.bloco.min()].wape.mean()) if len(s) else np.nan,
        wape_oficial_ult=float(s[s.bloco == s.bloco.max()].wape.mean()) if len(s) else np.nan,
        cob_oficial=float(s.cobertura95.mean()) if len(s) and s.cobertura95.notna().any() else np.nan,
        n_ckpt=len(tv), viol_traj=viol, igd_ini=float(tv[0]), igd_fim=float(tv[-1]),
        viol_hv=int((np.diff(thv) < -1e-12).sum()), nd_ini=int(tnd[0]), nd_fim=int(tnd[-1]),
        ganho_igd=float(tv[0] / tv[-1]) if tv[-1] > 0 else np.nan,
        igd_plus=float(c.igd_plus.iloc[0]), hv=float(c.hv.iloc[0]), n_nd=int(c.n_nd.iloc[0]),
        rank=int((mm.sort_values('igd_plus').alg.values == 'c141').argmax() + 1), n_alg=len(mm),
        piso_melhor=pis.alg.iloc[0], piso_igd=float(pis.igd_plus.iloc[0]),
        razao_piso=float(c.igd_plus.iloc[0] / pis.igd_plus.iloc[0]) if pis.igd_plus.iloc[0] > 0 else np.nan,
        melhor_sa=sa.alg.iloc[0], melhor_sa_igd=float(sa.igd_plus.iloc[0]),
    ))
    print('ok', pb, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b05_saude.csv'), index=False)
pd.set_option('display.width', 320, 'display.max_columns', 200)
print(df.round(4).to_string())
print()
print('viol traj TOTAL:', df.viol_traj.sum(), 'de', (df.n_ckpt - 1).sum(), 'transicoes')
print('dwape mediano: %.1f%%' % df.dwape_pct.median())
print('bate melhor piso:', (df.razao_piso < 1).sum(), '/', len(df), ' rank medio %.2f' % df['rank'].mean())
