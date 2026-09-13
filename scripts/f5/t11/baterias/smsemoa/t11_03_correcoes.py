#!/usr/bin/env python
"""T11/smsemoa — bateria 3: correções finas + query-joia + ERRATA 5 nos 4 pisos.
READ-ONLY.
"""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado'
RES = f'{ROOT}/resultados_experimentos'
DOE = f'{ROOT}/ua-dd-saea/data/doe'
OUT = f'{ROOT}/ua-dd-saea/f5/t11/baterias/smsemoa'
PROBS = sorted(os.listdir(f'{RES}/smsemoa'))


def cell(alg, p):
    d = f'{RES}/{alg}/{p}/42'
    if not os.path.isdir(d):
        return None
    stem = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
    m = json.load(open(f'{d}/{stem}.manifest.json'))
    L = [json.loads(l) for l in open(f'{d}/{stem}.jsonl')]
    R = pd.read_parquet(f'{d}/{stem}__real.parquet')
    P = pd.read_parquet(f'{d}/{stem}__pop.parquet')
    return m, L, R, P


print('===== 1. DoE hash ≡ sidecar (chave correta `doe_hash`) =====')
ok = 0
for p in PROBS:
    m, L, R, P = cell('smsemoa', p)
    dm = json.load(open(f'{DOE}/{p}/doe_{p}_42.manifest.json'))
    ok += int(m['doe_hash'] == dm['doe_hash'])
print(f'doe_hash ⑤ ≡ sidecar: {ok}/{len(PROBS)}')

print()
print('===== 2. ideal / nadir recomputados — tolerância float32 (①=f32, log=f64) =====')
tot = ok_i = ok_np = ok_nf = 0
maxrel_i = maxrel_n = 0.0
for p in PROBS:
    m, L, R, P = cell('smsemoa', p)
    gens = [g for g in L if g['rec'] == 'smsemoa_gen']
    fc = [c for c in R.columns if c.startswith('f') and c[1:].isdigit()]
    F = R[fc].values.astype(np.float64)
    for g in gens:
        tot += 1
        sid = P[P['geracao'] == g['geracao']]['solution_id'].values
        A = F[sid]
        for nome, rec, key in (('i', A.min(0), 'ideal'), ('n', A.max(0), 'nadir_pop')):
            log = np.array(g[key], float)
            rel = np.abs(rec - log) / np.maximum(np.abs(log), 1e-30)
            if nome == 'i':
                ok_i += int(np.allclose(rec, log, rtol=1e-6, atol=1e-30))
                maxrel_i = max(maxrel_i, float(rel.max()))
            else:
                ok_np += int(np.allclose(rec, log, rtol=1e-6, atol=1e-30))
                maxrel_n = max(maxrel_n, float(rel.max()))
        if g.get('nadir_front1'):
            # front1 recomputado (dominância padrão) — usa o mesmo caveat float32
            n = len(A)
            dom = (A[:, None, :] <= A[None, :, :]).all(2) & (A[:, None, :] < A[None, :, :]).any(2)
            f1 = ~dom.any(0)
            ok_nf += int(np.allclose(A[f1].max(0), np.array(g['nadir_front1'], float), rtol=1e-6, atol=1e-30))
print(f'ideal      {ok_i}/{tot}  (desvio relativo máx {maxrel_i:.3g})')
print(f'nadir_pop  {ok_np}/{tot}  (desvio relativo máx {maxrel_n:.3g})')
print(f'nadir_f1   {ok_nf}/{tot}  (recomputo float32 da frente-1)')

print()
print('===== 3. Fechamento aritmético por ORDEM no fluxo do ⑥ (armadilha ⑤) =====')
lin = []
for p in PROBS:
    m, L, R, P = cell('smsemoa', p)
    gens = [i for i, x in enumerate(L) if x['rec'] == 'smsemoa_gen']
    fim = gens[-1]
    ch_pre = [x for i, x in enumerate(L)
              if x['rec'] == 'guard' and x['name'] == 'cache_hit' and i < fim and x['fe'] > (11 * L[0]['D'] - 1)]
    ch_pos = [x for i, x in enumerate(L)
              if x['rec'] == 'guard' and x['name'] == 'cache_hit' and i > fim]
    fes = [x['fe'] for x in L if x['rec'] == 'smsemoa_gen']
    esq = 20 * (len(fes) - 1)
    dir_ = int(np.diff(fes).sum()) + len(ch_pre)
    lin.append(dict(problema=p, esq=esq, dir=dir_, ok=esq == dir_, ch_pre=len(ch_pre), ch_pos=len(ch_pos)))
d3 = pd.DataFrame(lin)
print('fechamento N·(n_ger−1) == Σ Δfe + cache-hits ANTES do último evento de geração:',
      f'{int(d3.ok.sum())}/{len(d3)}')
print(d3[d3.ch_pre + d3.ch_pos > 0].to_string(index=False))

print()
print('===== 4. ERRATA 5 / I-13 · a fórmula NOVA de `geracoes_derivadas` nos 4 PISOS =====')
rows = []
for alg in ['smsemoa', 'nsga2', 'nsga3', 'moead']:
    for p in sorted(os.listdir(f'{RES}/{alg}')):
        c = cell(alg, p)
        if c is None:
            continue
        m, L, R, P = c
        D = [x for x in L if x['rec'] == 'header'][0]['D']
        nini = 11 * D - 1
        gname = f'{alg}_gen'
        ch = [x for x in L if x['rec'] == 'guard' and x['name'] == 'cache_hit']
        ndup = len([x for x in ch if x['fe'] > nini])
        nef = m['params']['N_efetivo']
        f_t11 = int(np.floor((20 * D + ndup) / (2 * np.floor(nef / 2))))
        rows.append(dict(alg=alg, problema=p, D=D, N_ef=nef, n_dup=ndup,
                         n_ger=m['n_geracoes'], f_t11=f_t11,
                         ok=f_t11 == m['n_geracoes'], off=m['n_geracoes'] - f_t11))
d4 = pd.DataFrame(rows)
d4.to_csv(f'{OUT}/errata5_geracoes_4pisos.csv', index=False)
print(d4.groupby('alg').agg(celulas=('ok', 'size'), acertos=('ok', 'sum'),
                            off_min=('off', 'min'), off_max=('off', 'max')).to_string())
print('TOTAL 4 pisos: %d/%d' % (int(d4.ok.sum()), len(d4)))
print('distribuição do erro (n_ger − fórmula):', d4.off.value_counts().to_dict())
print('\nO piso que a fórmula ACERTA, por quê — n_ger vs D:')
print(d4.groupby('alg').apply(lambda g: (g.n_ger - g.D).value_counts().to_dict(), include_groups=False).to_string())

print()
print('===== 5. QUERY-JOIA · monotonicidade do HV populacional (4 pisos, ref FIXO por problema) =====')


def hv2(F, ref):
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    o = np.argsort(F[:, 0])
    F = F[o]
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


def hv_mc(F, ref, n=200000, seed=7):
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    lo = F.min(0)
    rs = np.random.default_rng(seed)
    Q = rs.uniform(lo, ref, size=(n, len(ref)))
    dom = np.zeros(n, bool)
    for r in F:
        dom |= np.all(Q >= r, axis=1)
    return dom.mean() * np.prod(ref - lo)


res = []
for p in PROBS:
    cells = {a: cell(a, p) for a in ['smsemoa', 'nsga2', 'nsga3', 'moead']}
    cells = {a: c for a, c in cells.items() if c}
    fc = None
    allF = []
    for a, (m, L, R, P) in cells.items():
        fc = [c for c in R.columns if c.startswith('f') and c[1:].isdigit()]
        allF.append(R[fc].values.astype(np.float64))
    ref = np.vstack(allF).max(0) * 1.0
    ref = ref + 0.01 * np.abs(ref) + 1e-9
    M = len(fc)
    for a, (m, L, R, P) in cells.items():
        F = R[fc].values.astype(np.float64)
        gl = sorted(P['geracao'].unique())
        serie = []
        for g in gl:
            sid = P[P['geracao'] == g]['solution_id'].values
            A = F[sid]
            serie.append(hv2(A, ref) if M == 2 else hv_mc(A, ref))
        s = np.array(serie)
        d = np.diff(s)
        rel = d / np.maximum(np.abs(s[:-1]), 1e-30)
        res.append(dict(problema=p, alg=a, M=M, trans=len(d), quedas=int((d < 0).sum()),
                        quedas_1pc=int((rel < -0.01).sum()),
                        pior_rel=float(rel.min()) if len(rel) else 0.0,
                        ganho=float((s[-1] - s[0]) / max(s[0], 1e-30))))
d5 = pd.DataFrame(res)
d5.to_csv(f'{OUT}/hv_monotonicidade_4pisos.csv', index=False)
g = d5.groupby('alg').agg(trans=('trans', 'sum'), quedas=('quedas', 'sum'),
                          quedas_1pc=('quedas_1pc', 'sum'), pior=('pior_rel', 'min'))
g['pct_quedas'] = (100 * g.quedas / g.trans).round(2)
print(g.to_string())
print('\nsmsemoa — células com queda:')
print(d5[(d5.alg == 'smsemoa') & (d5.quedas > 0)][['problema', 'M', 'trans', 'quedas', 'pior_rel']].to_string(index=False))
sm = d5[d5.alg == 'smsemoa']
print('ganho HV início→fim: positivo em %d/%d · mediana %.1f%% · máx %.1f%% (%s) · mín %.1f%% (%s)' % (
    int((sm.ganho > 0).sum()), len(sm), 100 * sm.ganho.median(),
    100 * sm.ganho.max(), sm.loc[sm.ganho.idxmax(), 'problema'],
    100 * sm.ganho.min(), sm.loc[sm.ganho.idxmin(), 'problema']))
print('escrito em', OUT)
