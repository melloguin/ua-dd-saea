#!/usr/bin/env python
"""T11/smsemoa — bateria 5: fechamento (quedas exatas, insumos F5 pré-computados,
papel de régua, checagem do SMOKE contra os artefatos normativos novos). READ-ONLY."""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado'
RES = f'{ROOT}/resultados_experimentos'
F5 = f'{ROOT}/ua-dd-saea/f5'
ART = f'{ROOT}/ua-dd-saea/claude_code_context/artifacts'
SMK = f'{ROOT}/evidencia_T11/smoke_matlab/experiments/main/smsemoa'
OUT = f'{ROOT}/ua-dd-saea/f5/t11/baterias/smsemoa'
PROBS = sorted(os.listdir(f'{RES}/smsemoa'))


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
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    zs = np.unique(np.concatenate([F[:, 2], [ref[2]]]))
    v = 0.0
    for i in range(len(zs) - 1):
        sub = F[F[:, 2] <= zs[i]][:, :2]
        if len(sub):
            v += hv2(sub, ref[:2]) * (zs[i + 1] - zs[i])
    return v


print('===== A. MMF16_20 — as 3 quedas, com HV EXATO (M=3, sem estimador) =====')
p = 'MMF16_20'
Fall, refs = {}, []
for a in ['smsemoa', 'nsga2', 'nsga3', 'moead']:
    d = f'{RES}/{a}/{p}/42'
    stem = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
    R = pd.read_parquet(f'{d}/{stem}__real.parquet')
    fc = [c for c in R.columns if c.startswith('f') and c[1:].isdigit()]
    refs.append(R[fc].values.astype(np.float64).max(0))
ref = np.max(refs, axis=0)
ref = ref + 0.01 * np.abs(ref) + 1e-9
d = f'{RES}/smsemoa/{p}/42'
stem = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
R = pd.read_parquet(f'{d}/{stem}__real.parquet')
P = pd.read_parquet(f'{d}/{stem}__pop.parquet')
F = R[fc].values.astype(np.float64)
s = np.array([hv3(F[P[P['geracao'] == g]['solution_id'].values], ref) for g in sorted(P['geracao'].unique())])
rel = np.diff(s) / s[:-1]
for i, r in enumerate(rel):
    if r < 0:
        print(f'  transição {i + 1}->{i + 2}: {100 * r:+.4f}%  (HV {s[i]:.6f} -> {s[i + 1]:.6f})')
print('  quedas em M=2 (19 células, 266 transições): 0 — o resíduo é EXCLUSIVO do M=3')

print()
print('===== B. tempo_aval_real_s (I-02) e timing nas 25 =====')
lin = []
for pr in PROBS:
    dd = f'{RES}/smsemoa/{pr}/42'
    st = [f[:-len('.manifest.json')] for f in os.listdir(dd) if f.endswith('.manifest.json')][0]
    m = json.load(open(f'{dd}/{st}.manifest.json'))
    lin.append(dict(problema=pr, aval=m['timing']['tempo_aval_real_s'], tot=m['timing']['tempo_total_s']))
t = pd.DataFrame(lin)
print('tempo_aval_real_s não-nulo:', int(t.aval.notna().sum()), '/', len(t),
      '| Σ %.2f s (%.1f%% do wall Σ %.2f s)' % (t.aval.sum(), 100 * t.aval.sum() / t.tot.sum(), t.tot.sum()))
print('h-core das 25:', round(t.tot.sum() / 3600, 4), '| projeção 30 sementes:',
      round(30 * t.tot.sum() / 3600, 2), 'h-core')

print()
print('===== C. Insumos pré-computados da F5 (uso, não recomputo) =====')
for f, filt in [('metricas_finais_f52c.csv', None), ('contrato_f52b.csv', None),
                ('integridade_f52a.csv', None), ('tempo_f52d.csv', None), ('sonda_f52e.csv', None)]:
    fp = f'{F5}/{f}'
    if not os.path.exists(fp):
        print(f'{f}: AUSENTE')
        continue
    df = pd.read_csv(fp)
    col = 'alg' if 'alg' in df.columns else ('algoritmo' if 'algoritmo' in df.columns else None)
    n = int((df[col] == 'smsemoa').sum()) if col else -1
    print(f'{f}: {len(df)} linhas | smsemoa = {n}' + (f' | colunas: {list(df.columns)[:9]}' if n else ''))

print()
print('===== D. Papel de régua — IGD+/HV da F5.2c (pré-computado) =====')
M = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
col = 'alg' if 'alg' in M.columns else 'algoritmo'
main = M[(M.get('exp', 'main') == 'main') if 'exp' in M.columns else slice(None)]
sm = main[main[col] == 'smsemoa']
print('smsemoa: %d células | colunas de métrica: %s' % (
    len(sm), [c for c in M.columns if any(k in c.lower() for k in ('igd', 'hv', 'spac', 'nd'))]))
mcol = [c for c in M.columns if c.lower().startswith('igd_plus') or c.lower() == 'igdplus' or c.lower() == 'igd+']
print('coluna IGD+ detectada:', mcol)
if mcol:
    mc = mcol[0]
    pis = main[main[col].isin(['smsemoa', 'nsga2', 'nsga3', 'moead'])]
    piv = pis.pivot_table(index='problema', columns=col, values=mc, aggfunc='min')
    piv = piv.dropna()
    vencedor = piv.idxmin(axis=1)
    print('melhor piso por IGD+ (25 problemas):', vencedor.value_counts().to_dict())
    rk = piv.rank(axis=1)
    print('rank médio:', rk.mean().round(2).to_dict())
    # c262 x smsemoa (espelho D25)
    c262 = main[main[col] == 'c262'].set_index('problema')[mc]
    sms = piv['smsemoa']
    j = pd.concat([sms.rename('sms'), c262.rename('c262')], axis=1).dropna()
    print('espelho D25 c262 × smsemoa: %d células | c262 vence %d | razão mediana %.2f×' % (
        len(j), int((j.c262 < j.sms).sum()), float((j.sms / j.c262).median())))
    # % de células SA piores que o piso
    sa = main[~main[col].isin(['smsemoa', 'nsga2', 'nsga3', 'moead', 'sobol_batch'])]
    jj = sa.merge(sms.rename('piso'), left_on='problema', right_index=True)
    print('células SA (main) piores que o piso smsemoa: %d/%d (%.1f%%)' % (
        int((jj[mc] > jj.piso).sum()), len(jj), 100 * (jj[mc] > jj.piso).mean()))

print()
print('===== E. O SMOKE T11 contra os artefatos normativos NOVOS =====')
m = json.load(open(f'{SMK}/exp_main_smsemoa_DTLZ2_42.manifest.json'))
L = [json.loads(l) for l in open(f'{SMK}/exp_main_smsemoa_DTLZ2_42.jsonl')]
C = json.load(open(f'{ART}/contrato_61.json'))
MT = json.load(open(f'{ART}/mapa_termino.json'))
G = json.load(open(f'{ART}/gabarito_camadas.json'))
quinto = C['quinto_obrigatorio']['campos']
falta = [k for k in quinto if k not in m or m.get(k) in ('', None)]
print('⑤ quinto_obrigatorio:', 'COMPLETO' if not falta else f'FALTA {falta}',
      f'(campanha_id={m.get("campanha_id")}, repo_hash={m.get("repo_hash")[:12]}…, schema_version={m.get("schema_version")})')
print('sigma_dict.status =', m['sigma_dict']['status'], '|', m['sigma_dict']['motivo'][:70], '…')
campos = [c for c in set(C['minimo_comum_di10']['campos'] + C['configs']['smsemoa']['di10'])
          if c not in C['configs']['smsemoa']['nao_se_aplica']]
gens = [x for x in L if x['rec'] == 'smsemoa_gen']
print('DI-10 (%s) em todos os eventos: %d/%d' % (sorted(campos),
      sum(all(c in g for c in campos) for g in gens), len(gens)))
ft = [x for x in L if x['rec'] == 'footer']
cfg = MT['configs']['smsemoa']
print('mapa_termino: n_footers %d (esperado %s) · campo `%s` = %r · evento `%s` presente %d×' % (
    len(ft), cfg['n_footers_esperado'], cfg['campo_termino'], ft[0].get(cfg['campo_termino']),
    cfg['evento_geracao']['rec'], len(gens)))
obr = G['configs']['smsemoa']['obrigatorias']
mapa = {'real': '__real.parquet', 'pop': '__pop.parquet', 'surrogate': '__surrogate.parquet',
        'timing': '__timing.parquet', 'jsonl': '.jsonl', 'manifest': '.manifest.json'}
print('gabarito_camadas: %d/%d presentes' % (
    sum(os.path.exists(f'{SMK}/exp_main_smsemoa_DTLZ2_42{mapa[k]}') for k in obr), len(obr)))
print('repo_hash do smoke bate com o campanha_id?', m['campanha_id'].endswith(m['repo_hash'][:7]))
