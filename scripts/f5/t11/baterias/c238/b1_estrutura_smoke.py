#!/usr/bin/env python
"""B1 — estrutura do smoke T11 main/c238/MMF1 + diff contra a rodada-42 (mesma celula).
READ-ONLY. Escreve so em f5/t11/baterias/c238/.
"""
import json, sys, hashlib
import numpy as np, pandas as pd

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42'
BASE = 'exp_main_c238_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c238'


def load(root):
    d = {}
    d['man'] = json.load(open(f'{root}/{BASE}.manifest.json'))
    d['recs'] = [json.loads(l) for l in open(f'{root}/{BASE}.jsonl')]
    for lay, suf in [('real', '__real'), ('pop', '__pop'), ('sur', '__surrogate'), ('tim', '__timing')]:
        d[lay] = pd.read_parquet(f'{root}/{BASE}{suf}.parquet')
    return d


sm, r42 = load(SM), load(R42)

print('=' * 90)
print('B1.0 — SCHEMAS DAS CAMADAS (smoke)')
for lay in ['real', 'pop', 'sur', 'tim']:
    print(f'  {lay:5s} shape={sm[lay].shape}')
    print('        cols:', list(sm[lay].columns))
    print('        dtypes:', {c: str(t) for c, t in sm[lay].dtypes.items()})

print('=' * 90)
print('B1.1 — U1 orcamento FE')
D = sm['recs'][0]['D']; M = sm['recs'][0]['M']
print('  D=%d M=%d  maxfe_manifesto=%d  31D-1=%d  len(1)=%d' % (D, M, sm['man']['maxfe'], 31 * D - 1, len(sm['real'])))
print('  fe_final=%s termino=%s status=%s' % (sm['man']['fe_final'],
      [r for r in sm['recs'] if r['rec'] == 'footer'][0]['termino'], sm['man']['status']))
fi = sm['real']['fe_index'].to_numpy()
print('  fe_index denso 0-based:', bool((fi == np.arange(len(fi))).all()), ' sid unico:', sm['real']['solution_id'].is_unique)
print('  fases:', sm['real']['fase'].value_counts().to_dict(), ' init esperado 11D-1=', 11 * D - 1)

print('=' * 90)
print('B1.2 — U2 DoE bit-a-bit contra o artefato')
import glob
cands = glob.glob('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/*42*')
print('  artefatos DoE encontrados:', cands)
for c in cands:
    if c.endswith('.parquet'):
        A = pd.read_parquet(c)
    elif c.endswith('.npy'):
        A = pd.DataFrame(np.load(c))
    else:
        continue
    xa = A.to_numpy(dtype=np.float64)[:, :D]
    xr = sm['real'][[f'x{i}' for i in range(D)]].to_numpy()[:11 * D - 1]
    print('   ', c.split('/')[-1], 'shape', xa.shape)
    print('    max|dX| vs float64 :', np.abs(xa[:len(xr)] - xr).max())
    print('    max|dX| vs float32 :', np.abs(xa[:len(xr)].astype(np.float32) - xr).max())
    h = hashlib.sha256(np.ascontiguousarray(xa[:11 * D - 1]).tobytes()).hexdigest()
    print('    sha256(f64 raw)    :', h, ' == manifesto?', h == sm['man']['doe_hash'])

print('=' * 90)
print('B1.3 — censo do jsonl + U9 guards + U10 ledger')
import collections
cen = collections.Counter(r['rec'] for r in sm['recs'])
print('  censo:', dict(cen))
g = [r for r in sm['recs'] if r['rec'] == 'c238_gen']
print('  n_gens(6)=%d  n_infills(1 fase=online)=%d  n_fit_series(5)=%d  len(4 timing)=%d'
      % (len(g), int((sm['real']['fase'] != 'init').sum()), len(sm['man']['fit_series']), len(sm['tim'])))
print('  guard events:', [r for r in sm['recs'] if r['rec'] == 'guard'])
print('  manifest.cache_hits =', sm['man']['cache_hits'])
n_opt = int((sm['real']['fase'] != 'init').sum())
print('  ledger: n_gens=%d  n_opt=%d  cache_hits=%d  =>  c0 = n_opt + ch - n_gens = %d'
      % (len(g), n_opt, sm['man']['cache_hits'], n_opt + sm['man']['cache_hits'] - len(g)))
print('  footer.n_geracoes=%d  (vs %d eventos c238_gen)' % (
    [r for r in sm['recs'] if r['rec'] == 'footer'][0]['n_geracoes'], len(g)))
print('  sum(fe_iter)=%d  lote unico?%s' % (sum(r['fe_iter'] for r in g), set(r['lote'] for r in g)))

print('=' * 90)
print('B1.4 — camada 2 (pop) e off-by-one')
pp = sm['pop']
print('  gens na 2:', sorted(pp['geracao'].dropna().unique())[:5], '...', sorted(pp['geracao'].dropna().unique())[-3:])
sz = pp.groupby('geracao').size()
print('  n_gens(2)=%d (esperado n_gens+1=%d)' % (len(sz), len(g) + 1))
ok = all(sz.loc[gg] == (11 * D - 1 - 1) + gg for gg in sz.index)
print('  |2(g)| == (init-1)+g em todas?', ok, ' primeiros:', sz.head(3).to_dict(), ' ultimo:', sz.tail(1).to_dict())
last = pp[pp['geracao'] == sz.index.max()]
print('  duplicatas de solution_id na ultima 2:', int(last['solution_id'].duplicated().sum()))

print('=' * 90)
print('B1.5 — U4 cadencia da sonda')
son = [r for r in sm['recs'] if r['rec'] == 'sonda']
gs = sorted(r.get('geracao') for r in son)
print('  n_blocos(6)=%d  manifest.sonda.n_blocos=%d  geracoes=%s' % (len(son), sm['man']['sonda']['n_blocos'], gs))
esp = [x for x in range(1, len(g) + 1) if x == 1 or x % 2 == 0]
if len(g) not in esp:
    esp.append(len(g))
print('  esperado (g==1 ou g%%2==0 + finalProbe) =', esp)
print('  cadencia OK?', gs == esp)
sur = sm['sur']
print('  regimes na 3:', sur['regime'].value_counts().to_dict())
sb = sur[sur['regime'] == 'sonda']
print('  linhas por bloco de sonda:', sb.groupby('geracao').size().unique(), ' n_falhas=', sm['man']['sonda']['n_falhas'])

print('=' * 90)
print('B1.6 — U3/U7/U8')
tim = sm['tim']
print('  timing cols:', list(tim.columns))
viol = 0
for r in g:
    if r['tempo_fit_s'] + r['tempo_busca_s'] > r['tempo_geracao_s'] + 1e-12:
        viol += 1
print('  U7 violacoes fit+busca>geracao: %d de %d' % (viol, len(g)))
ft = np.array([r['fe_treino_max'] for r in g])
print('  U8 fe_treino_max monotonico?', bool((np.diff(ft) >= 0).all()), ' == n_amostra-1?',
      bool((ft == np.array([r['n_amostra'] - 1 for r in g])).all()))
print('  n_treino == n_amostra - n_dedup em todas?',
      all(r['n_treino'] == r['n_amostra'] - r['n_dedup'] for r in g))

print('=' * 90)
print('B1.7 — DIFF SMOKE x RODADA-42 (mesma celula, mesma semente)')
for lay in ['real', 'pop', 'sur', 'tim']:
    a, b = sm[lay], r42[lay]
    same_shape = a.shape == b.shape
    print('  %-5s shape %s vs %s  iguais=%s' % (lay, a.shape, b.shape, same_shape), end='')
    if same_shape and list(a.columns) == list(b.columns):
        num = a.select_dtypes(include=[np.number]).columns
        try:
            dif = np.nanmax(np.abs(a[num].to_numpy(dtype=np.float64) - b[num].to_numpy(dtype=np.float64)))
        except Exception as e:
            dif = f'ERR {e}'
        print('  max|delta| numerico =', dif)
    else:
        print('  COLS:', set(a.columns) ^ set(b.columns))

g42 = [r for r in r42['recs'] if r['rec'] == 'c238_gen']
campos = ['eim_best', 'eim_mediana_pool', 'y_best', 'n_front', 'n_front1', 'min_dist_infill',
          'n_amostra', 'n_treino', 'n_dedup', 'infill_sid', 'fe', 'ga_pop', 'ga_gens',
          'n_eim_nan', 'n_range0', 'stall_iters', 'fe_treino_max']
print('  n_gens smoke=%d  r42=%d' % (len(g), len(g42)))
for c in campos:
    va = np.array([r[c] for r in g], dtype=float)
    vb = np.array([r[c] for r in g42], dtype=float)
    d = np.nanmax(np.abs(va - vb)) if len(va) == len(vb) else 'len dif'
    print('    %-20s max|delta| = %s' % (c, d))
for c in ['norm_min', 'norm_max', 'norm_range_efetivo', 'theta_min', 'theta_max', 'theta_media', 'lnL', 'u_best', 's_best', 'f_best']:
    va = np.array([r[c] for r in g], dtype=float)
    vb = np.array([r[c] for r in g42], dtype=float)
    print('    %-20s max|delta| = %s' % (c, np.nanmax(np.abs(va - vb))))

print('=' * 90)
print('B1.8 — manifesto: diff de chaves smoke x r42')
ka, kb = set(sm['man'].keys()), set(r42['man'].keys())
print('  so no smoke:', ka - kb)
print('  so no r42  :', kb - ka)
for k in ['params', 'sigma_dict']:
    pa, pb = sm['man'].get(k, {}), r42['man'].get(k, {})
    print('  %s: chaves so smoke=%s  so r42=%s' % (k, set(pa) - set(pb), set(pb) - set(pa)))
    for kk in sorted(set(pa) & set(pb)):
        if pa[kk] != pb[kk]:
            print('    DIFERE %s:\n      smoke=%r\n      r42  =%r' % (kk, pa[kk], pb[kk]))
print('  timing smoke:', sm['man']['timing'])
print('  timing r42  :', r42['man']['timing'])
