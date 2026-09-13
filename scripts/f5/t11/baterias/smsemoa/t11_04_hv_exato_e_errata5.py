#!/usr/bin/env python
"""T11/smsemoa — bateria 4: (a) HV EXATO em M=3 (elimina o ruído do estimador MC)
para fechar a query-joia; (b) caça ao denominador '103/112' da ERRATA 5.
READ-ONLY."""
import json, os, glob
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado'
RES = f'{ROOT}/resultados_experimentos'
EXP = f'{ROOT}/ua-dd-saea/data/experiments'
OUT = f'{ROOT}/ua-dd-saea/f5/t11/baterias/smsemoa'


def hv2(F, ref):
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    F = F[np.argsort(F[:, 0])]
    keep, best = [], np.inf
    for r in F:
        if r[1] < best:
            keep.append(r)
            best = r[1]
    F = np.array(keep)
    v, prev = 0.0, ref[1]
    for r in F:
        v += (ref[0] - r[0]) * (prev - r[1])
        prev = r[1]
    return v


def hv3(F, ref):
    """HV exato em M=3 por fatiamento no 3o objetivo (slicing)."""
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    zs = np.unique(np.concatenate([F[:, 2], [ref[2]]]))
    zs.sort()
    v = 0.0
    for i in range(len(zs) - 1):
        z, z2 = zs[i], zs[i + 1]
        sub = F[F[:, 2] <= z][:, :2]
        if len(sub):
            v += hv2(sub, ref[:2]) * (z2 - z)
    return v


def cell(alg, p, base=RES, seed='42'):
    d = f'{base}/{alg}/{p}/{seed}'
    if not os.path.isdir(d):
        return None
    stem = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
    return (json.load(open(f'{d}/{stem}.manifest.json')),
            [json.loads(l) for l in open(f'{d}/{stem}.jsonl')],
            pd.read_parquet(f'{d}/{stem}__real.parquet'),
            pd.read_parquet(f'{d}/{stem}__pop.parquet'))


print('===== A. HV EXATO — as 6 células M=3 dos 4 pisos (sem estimador) =====')
PROBS = sorted(os.listdir(f'{RES}/smsemoa'))
lin = []
for p in PROBS:
    cs = {a: cell(a, p) for a in ['smsemoa', 'nsga2', 'nsga3', 'moead']}
    cs = {a: c for a, c in cs.items() if c}
    fc = [c for c in list(cs.values())[0][2].columns if c.startswith('f') and c[1:].isdigit()]
    M = len(fc)
    ref = np.vstack([c[2][fc].values.astype(np.float64) for c in cs.values()]).max(0)
    ref = ref + 0.01 * np.abs(ref) + 1e-9
    for a, (m, L, R, P) in cs.items():
        F = R[fc].values.astype(np.float64)
        s = []
        for g in sorted(P['geracao'].unique()):
            A = F[P[P['geracao'] == g]['solution_id'].values]
            s.append(hv2(A, ref) if M == 2 else hv3(A, ref))
        s = np.array(s)
        d = np.diff(s)
        rel = d / np.maximum(np.abs(s[:-1]), 1e-30)
        lin.append(dict(problema=p, alg=a, M=M, trans=len(d), quedas=int((d < 0).sum()),
                        q1pc=int((rel < -0.01).sum()), pior=float(rel.min()) if len(rel) else 0.0,
                        ganho=float((s[-1] - s[0]) / max(s[0], 1e-30))))
D = pd.DataFrame(lin)
D.to_csv(f'{OUT}/hv_exato_4pisos.csv', index=False)
g = D.groupby('alg').agg(trans=('trans', 'sum'), quedas=('quedas', 'sum'),
                         q1pc=('q1pc', 'sum'), pior=('pior', 'min'))
g['%'] = (100 * g.quedas / g.trans).round(2)
print(g.to_string())
print()
print('só M=3 (6 células):')
g3 = D[D.M == 3].groupby('alg').agg(trans=('trans', 'sum'), quedas=('quedas', 'sum'), pior=('pior', 'min'))
g3['%'] = (100 * g3.quedas / g3.trans).round(2)
print(g3.to_string())
print()
print('smsemoa com queda (HV exato):')
print(D[(D.alg == 'smsemoa') & (D.quedas > 0)][['problema', 'M', 'trans', 'quedas', 'pior']].to_string(index=False))
sm = D[D.alg == 'smsemoa']
print('ganho: positivo %d/%d · mediana %.1f%% · máx %.1f%% (%s) · mín %.1f%% (%s)' % (
    int((sm.ganho > 0).sum()), len(sm), 100 * sm.ganho.median(), 100 * sm.ganho.max(),
    sm.loc[sm.ganho.idxmax(), 'problema'], 100 * sm.ganho.min(), sm.loc[sm.ganho.idxmin(), 'problema']))

print()
print('===== B. ERRATA 5 — todo o universo de células de PISO em data/experiments =====')
rows = []
for mp in glob.glob(f'{EXP}/**/*.manifest.json', recursive=True):
    try:
        m = json.load(open(mp))
    except Exception:
        continue
    if m.get('alg') not in ('smsemoa', 'nsga2', 'nsga3', 'moead'):
        continue
    if '_baseline_pre_retrofit' in mp:
        cat = 'pre_retrofit'
    else:
        cat = mp.split('/experiments/')[1].split('/')[0]
    P = m.get('params') or {}
    if 'N_efetivo' not in P or m.get('n_geracoes') is None:
        rows.append(dict(alg=m['alg'], cat=cat, problema=m.get('problema'), semente=m.get('semente'),
                         D=None, N_ef=None, n_dup=None, n_ger=m.get('n_geracoes'), f=None, ok=None))
        continue
    jl = mp.replace('.manifest.json', '.jsonl')
    ndup = None
    Dd = None
    if os.path.exists(jl):
        L = [json.loads(l) for l in open(jl)]
        h = [x for x in L if x.get('rec') == 'header']
        if h:
            Dd = h[0]['D']
            nini = 11 * Dd - 1
            ndup = len([x for x in L if x.get('rec') == 'guard' and x.get('name') == 'cache_hit'
                        and x.get('fe', 0) > nini])
    if Dd is None or ndup is None:
        continue
    nef = P['N_efetivo']
    f = int(np.floor((20 * Dd + ndup) / (2 * np.floor(nef / 2))))
    rows.append(dict(alg=m['alg'], cat=cat, problema=m['problema'], semente=m['semente'],
                     D=Dd, N_ef=nef, n_dup=ndup, n_ger=m['n_geracoes'], f=f, ok=f == m['n_geracoes'],
                     off=m['n_geracoes'] - f))
E = pd.DataFrame(rows)
E.to_csv(f'{OUT}/errata5_universo_pisos.csv', index=False)
print('células de piso encontradas em data/experiments:', len(E))
print(E.groupby(['cat']).agg(n=('ok', 'size'), acertos=('ok', 'sum')).to_string())
print()
print(E.groupby(['alg']).agg(n=('ok', 'size'), acertos=('ok', 'sum')).to_string())
print()
print('erro (n_ger − fórmula):', E.off.value_counts(dropna=False).to_dict())
print('escrito em', OUT)
