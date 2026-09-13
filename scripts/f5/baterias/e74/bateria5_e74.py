#!/usr/bin/env python
"""BATERIA 5 e74/CLMEA — cadencia (subset check) + SONDA por cabeca (U6) + PNN drift
+ metricas/trajetorias/contrato/tempo (insumos pre-computados da F5.2).
Escreve: e74_cadencia.csv, e74_wape_cabeca.csv, e74_metricas.csv, e74_trajetorias.csv
"""
import json, os, glob
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/e74'
probs = sorted(os.listdir(ROOT))

# ---------- cadencia: esperado SUBSET do observado ----------
rows = []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    sond = [r for r in recs if r['rec'] == 'sonda']
    obs = {m: sorted({r['geracao'] for r in sond if r['modelo'] == m})
           for m in ['PNN(s1)', 'RBF-global(s2)', 'RBF-local(s3)', 'RBF-global(boot)']}
    gg = {e: sorted(r['geracao'] for r in gens if r['estrategia'] == e) for e in (1, 2, 3)}
    esp = {'PNN(s1)': [g for i, g in enumerate(gg[1]) if i % 3 == 1],
           'RBF-global(s2)': [g for i, g in enumerate(gg[2]) if i % 3 == 0],
           'RBF-local(s3)': [g for i, g in enumerate(gg[3]) if i % 3 == 2]}
    gmax = max(r['geracao'] for r in gens)
    faltando = {k: sorted(set(v) - set(obs[k])) for k, v in esp.items()}
    extra = {k: sorted(set(obs[k]) - set(v)) for k, v in esp.items()}
    rows.append(dict(problema=pr, gmax=gmax,
                     falta_s1=len(faltando['PNN(s1)']), falta_s2=len(faltando['RBF-global(s2)']),
                     falta_s3=len(faltando['RBF-local(s3)']),
                     extra_s1=len(extra['PNN(s1)']), extra_s2=len(extra['RBF-global(s2)']),
                     extra_s3=len(extra['RBF-local(s3)']),
                     extras=json.dumps({k: v for k, v in extra.items() if v}),
                     ultima_coberta=any(gmax in v for v in obs.values()),
                     boot_1x=(obs['RBF-global(boot)'] == [1])))
cad = pd.DataFrame(rows); cad.to_csv(f'{OUT}/e74_cadencia.csv', index=False)
print('=== CADENCIA round-robin (DI-19.1) ===')
print('cadencia esperada SEM buraco (falta==0) em', int(((cad.falta_s1 + cad.falta_s2 + cad.falta_s3) == 0).sum()), '/25')
print('blocos EXTRA (clausula da ultima):', int((cad.extra_s1 + cad.extra_s2 + cad.extra_s3).sum()),
      '| ultima geracao coberta:', int(cad.ultima_coberta.sum()), '/25 | boot 1x em g=1:', int(cad.boot_1x.sum()), '/25')
print(cad[['problema', 'gmax', 'falta_s1', 'falta_s2', 'falta_s3', 'extra_s1', 'extra_s2', 'extra_s3']].to_string())

# ---------- U6 sonda por cabeca ----------
s = pd.read_csv(f'{F5}/sonda_f52e.csv')
e = s[(s.alg == 'e74') & (s.exp == 'main')].copy()
e['bloco'] = e.bloco.astype(int)
out = []
for (pr, mf, obj), b in e.groupby(['problema', 'modelo_flag', 'obj']):
    b = b.sort_values('bloco')
    out.append(dict(problema=pr, cabeca=mf, obj=obj, n_blocos=len(b),
                    wape_1=b.wape.iloc[0], wape_ult=b.wape.iloc[-1],
                    wape_med=b.wape.median(), wape_max=b.wape.max(),
                    dwape_pct=100 * (b.wape.iloc[-1] - b.wape.iloc[0]) / max(b.wape.iloc[0], 1e-12),
                    corr_1=b['corr'].iloc[0], corr_ult=b['corr'].iloc[-1], corr_med=b['corr'].median(),
                    n_validas_min=b.n_validas.min(), n_nan=b.n_nan.sum(),
                    cob=b.cobertura95.notna().sum()))
w = pd.DataFrame(out); w.to_csv(f'{OUT}/e74_wape_cabeca.csv', index=False)
print('\n=== U6 SONDA por CABECA (main/e74, 3.764 medicoes; s1=PNN nao entra: sem mu) ===')
print(w.groupby('cabeca').agg(n=('wape_med', 'size'), wape_1_med=('wape_1', 'median'),
                              wape_ult_med=('wape_ult', 'median'), dwape_med=('dwape_pct', 'median'),
                              wape_max=('wape_max', 'max'), corr_med=('corr_med', 'median'),
                              nan=('n_nan', 'sum'), cob=('cob', 'sum')).round(4).to_string())
print('\ndWAPE% por problema x cabeca (mediana dos objetivos):')
print(w.pivot_table(index='problema', columns='cabeca', values='dwape_pct', aggfunc='median').round(1).to_string())
print('\nWAPE ultimo bloco por problema x cabeca:')
print(w.pivot_table(index='problema', columns='cabeca', values='wape_ult', aggfunc='median').round(3).to_string())
print('\ncorrelacao mediana por problema x cabeca:')
print(w.pivot_table(index='problema', columns='cabeca', values='corr_med', aggfunc='median').round(3).to_string())

# ---------- metricas + posicao vs pisos ----------
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
print('\ncolunas metricas:', m.columns.tolist())
mm = m[(m.exp == 'main') & (m.semente == 42)] if 'semente' in m.columns else m[m.exp == 'main']
pisos = ['moead', 'nsga2', 'nsga3', 'smsemoa']
key = 'igdplus' if 'igdplus' in m.columns else ('igd_plus' if 'igd_plus' in m.columns else 'igd+')
res = []
for pr in probs:
    sub = mm[mm.problema == pr]
    if not len(sub):
        continue
    me = sub[sub.alg == 'e74']
    if not len(me):
        continue
    v = float(me[key].iloc[0])
    pv = {p: (float(sub[sub.alg == p][key].iloc[0]) if len(sub[sub.alg == p]) else np.nan) for p in pisos}
    best = np.nanmin(list(pv.values()))
    sa = sub[~sub.alg.isin(pisos + ['sobol_batch'])]
    rk = int((sa[key] < v).sum() + 1)
    res.append(dict(problema=pr, e74=v, melhor_piso=best, bate_piso=(v <= best),
                    gap_pct=100 * (v - best) / best if best == best and best > 0 else np.nan,
                    rank_sa=rk, n_sa=len(sa), **{f'piso_{k}': vv for k, vv in pv.items()}))
r = pd.DataFrame(res); r.to_csv(f'{OUT}/e74_metricas.csv', index=False)
print('\n=== IGD+ e74 vs pisos (F5.2c) ===')
print(r.round(4).to_string())
print('bate o melhor piso em', int(r.bate_piso.sum()), '/', len(r),
      '| rank SA medio', round(r.rank_sa.mean(), 2), 'de', r.n_sa.max())
rk_all = []
for pr in probs:
    sub = mm[mm.problema == pr]
    if not len(sub) or not len(sub[sub.alg == 'e74']): continue
    v = float(sub[sub.alg == 'e74'][key].iloc[0])
    rk_all.append(int((sub[key] < v).sum() + 1))
print('rank medio e74 no conjunto COMPLETO (SA+pisos, denominador variavel):', round(np.mean(rk_all), 2),
      '| n medio de algs por problema:', round(mm.groupby('problema').size().mean(), 1))
print('derrotas fora do piso de ruido O-18 (gap>58,98%):', int((r.gap_pct > 58.98).sum()))

# ---------- trajetorias ----------
tr = []
for pr in probs:
    f = f'{F5}/trajetorias/main_e74_{pr}_42.json'
    if not os.path.exists(f):
        print('SEM trajetoria', pr); continue
    j = json.load(open(f))
    v = np.array([c['igd_plus'] for c in j], float)
    fe = np.array([c['fe'] for c in j], float)
    d = np.diff(v)
    tr.append(dict(problema=pr, n=len(v), fe_ini=fe[0], fe_fim=fe[-1], inicio=v[0], fim=v[-1],
                   melhora_pct=100 * (v[0] - v[-1]) / v[0] if v[0] else np.nan,
                   violacoes=int((d > 1e-12).sum()), pior_salto=float(d.max())))
t = pd.DataFrame(tr); t.to_csv(f'{OUT}/e74_trajetorias.csv', index=False)
print('\n=== TRAJETORIAS (20 checkpoints IGD+) ===')
print(t.round(4).to_string())
print('violacoes de monotonicidade:', int(t.violacoes.sum()), 'em', int((t.n - 1).sum()), 'transicoes')

# ---------- contrato / integridade / tempo ----------
for nm in ['contrato_f52b', 'integridade_f52a']:
    c = pd.read_csv(f'{F5}/{nm}.csv')
    col = 'alg' if 'alg' in c.columns else c.columns[1]
    print(f'\n{nm}: linhas e74 =', int((c[col] == 'e74').sum()), '| colunas:', c.columns.tolist()[:8])
    if (c[col] == 'e74').sum():
        print(c[c[col] == 'e74'].to_string())
tp = pd.read_csv(f'{F5}/tempo_f52d.csv')
te = tp[(tp.alg == 'e74')] if 'alg' in tp.columns else tp
print('\ntempo_f52d e74:', len(te), 'colunas', tp.columns.tolist())
if len(te):
    print(te.groupby('maquina').agg(n=('problema', 'size'), horas=('tempo_total_s', lambda x: x.sum() / 3600)).to_string()
          if 'maquina' in te.columns and 'tempo_total_s' in te.columns else te.head(30).to_string())
