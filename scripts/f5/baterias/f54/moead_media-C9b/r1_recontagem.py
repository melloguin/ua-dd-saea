#!/usr/bin/env python3
# r1_recontagem.py — F5.4 / ataque adversarial ao achado moead_media-C9b.
# Passo 2 do roteiro: a evidencia do analista e reproduzivel? sobrevive a outra
# formulacao (dedup do re-run, criterio invariante a deslocamento, teste que
# respeita a estrutura de dependencia)?
# READ-ONLY. Saida: r1_recontagem.json + r1_pares.csv
import json
import numpy as np
import pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = F5 + '/baterias/f54/moead_media-C9b'
CFGS = ['moead_media', 'b5m', 'b5r']

d = pd.read_csv(F5 + '/sonda_f52e.csv')
t = d[d.alg.isin(CFGS)].copy()
t['cel'] = t.exp + '/' + t.problema
t['par'] = t.cel + '#o' + t.obj.astype(str)

res = {}

# ── (A) criterios de colapso ────────────────────────────────────────────────
def flags(s):
    w1 = (s.wape - 1.0).abs() <= 1e-4                 # criterio do relatorio (mu=0)
    cs = (s['corr'].abs() <= 0.015) | s['corr'].isna()  # invariante a shift/escala
    return pd.DataFrame({'w1': w1, 'cs': cs, 'and': w1 & cs, 'or': w1 | cs}, index=s.index)

t = t.join(flags(t))
res['A_contagens_por_criterio'] = {
    a: {k: int(s[k].sum()) for k in ['w1', 'cs', 'and', 'or']} | {'n': len(s)}
    for a, s in t.groupby('alg')}

# ── (B) o re-run: off/{p} == sweep-small-lhs/{p} (armadilha 26 do proprio rel.)
DUP = ['DTLZ2', 'MMF16_20', 'WFG9', 'ZDT1', 'ZDT4']
dupchk = []
for a in CFGS:
    for p in DUP:
        A = t[(t.alg == a) & (t.exp == 'off') & (t.problema == p)].sort_values('obj')
        B = t[(t.alg == a) & (t.exp == 'sweep-small-lhs') & (t.problema == p)].sort_values('obj')
        if len(A) and len(A) == len(B):
            dupchk.append({'alg': a, 'prob': p, 'M': len(A),
                           'max_dwape': float(np.abs(A.wape.values - B.wape.values).max()),
                           'igual_flag_w1': bool((A.w1.values == B.w1.values).all())})
res['B_rerun_duplicado'] = {
    'pares_checados': len(dupchk),
    'max_dwape_global': float(max(r['max_dwape'] for r in dupchk)),
    'flags_identicas': int(sum(r['igual_flag_w1'] for r in dupchk)),
    'detalhe': dupchk}

# unidade dedup: colapsa 'sweep-small-lhs' em 'off' (mesmo fit, mesmo dataset)
t['dup'] = (t.exp == 'sweep-small-lhs') & (t.problema.isin(DUP))
u = t[~t.dup].copy()          # 104 - 12 = 92 pares independentes de fit
res['C_dedup'] = {a: {'n_pares': int(len(s)), 'colapsos_w1': int(s.w1.sum()),
                      'taxa': round(float(s.w1.mean()), 4)}
                  for a, s in u.groupby('alg')}

# ── (D) nivel CELULA (1 evento de fit por celula, nao 2-3 por objetivo) ─────
cel = t.groupby(['alg', 'cel']).agg(qq=('w1', 'any'), nobj=('w1', 'size'),
                                    ncol=('w1', 'sum')).reset_index()
res['D_nivel_celula'] = {a: {'celulas': int(len(s)), 'com_colapso': int(s.qq.sum()),
                             'taxa': round(float(s.qq.mean()), 4)}
                         for a, s in cel.groupby('alg')}
celu = cel[~cel.cel.isin(['sweep-small-lhs/' + p for p in DUP])]
res['D2_celula_dedup'] = {a: {'celulas': int(len(s)), 'com_colapso': int(s.qq.sum()),
                              'taxa': round(float(s.qq.mean()), 4)}
                          for a, s in celu.groupby('alg')}

# ── (E) o chi2 do analista, e o mesmo teste com as unidades corretas ────────
def chi2_3(counts, ns):
    counts = np.asarray(counts, float); ns = np.asarray(ns, float)
    p = counts.sum() / ns.sum()
    e1 = ns * p; e0 = ns * (1 - p)
    x = ((counts - e1) ** 2 / e1 + ((ns - counts) - e0) ** 2 / e0).sum()
    return float(x)

from scipy import stats
c_par = [res['A_contagens_por_criterio'][a]['w1'] for a in CFGS]
res['E_chi2'] = {}
res['E_chi2']['analista_104pares'] = {
    'counts': c_par, 'chi2': round(chi2_3(c_par, [104] * 3), 3),
    'p': float(stats.chi2.sf(chi2_3(c_par, [104] * 3), 2))}
c_ded = [res['C_dedup'][a]['colapsos_w1'] for a in CFGS]
n_ded = [res['C_dedup'][a]['n_pares'] for a in CFGS]
res['E_chi2']['dedup_92pares'] = {
    'counts': c_ded, 'chi2': round(chi2_3(c_ded, n_ded), 3),
    'p': float(stats.chi2.sf(chi2_3(c_ded, n_ded), 2))}
c_cel = [res['D2_celula_dedup'][a]['com_colapso'] for a in CFGS]
n_cel = [res['D2_celula_dedup'][a]['celulas'] for a in CFGS]
res['E_chi2']['celula_dedup'] = {
    'counts': c_cel, 'chi2': round(chi2_3(c_cel, n_cel), 3),
    'p': float(stats.chi2.sf(chi2_3(c_cel, n_cel), 2))}

# ── (F) teste de permutacao com CLUSTER = problema (25 clusters) ────────────
#    H0: o rotulo do config e permutavel dentro do problema (o fit e a mesma
#    experiencia aleatoria, so muda a semente). Estatistica: contagem do piso.
piv = t.pivot_table(index=['exp', 'problema', 'obj'], columns='alg',
                    values='w1', aggfunc='first')
piv = piv.dropna().astype(bool)
rng = np.random.default_rng(20260729)
obs = int(piv['moead_media'].sum())
probs = piv.index.get_level_values('problema').values
NPERM = 20000


def perm_stat(mat, probs, rng):
    # permuta o rotulo do config DENTRO de cada problema (todas as celulas/obj
    # daquele problema recebem a MESMA permutacao -> respeita o cluster)
    out = np.zeros(len(mat), bool)
    for p in np.unique(probs):
        m = probs == p
        j = rng.integers(0, mat.shape[1])
        out[m] = mat[m, j]
    return int(out.sum())


mat = piv[CFGS].to_numpy(bool)
null = np.array([perm_stat(mat, probs, rng) for _ in range(NPERM)])
res['F_permutacao_cluster_problema'] = {
    'obs_piso': obs, 'null_media': round(float(null.mean()), 2),
    'null_p95': int(np.percentile(null, 95)), 'null_max': int(null.max()),
    'p_uni': round(float((null >= obs).mean()), 5), 'nperm': NPERM,
    'clusters': int(len(np.unique(probs)))}

# ── (G) McNemar pareado piso x b5m (par = mesmo dataset, so a semente muda) ─
a_ = piv['moead_media'].to_numpy(); b_ = piv['b5m'].to_numpy()
b01 = int((a_ & ~b_).sum()); b10 = int((~a_ & b_).sum())
res['G_mcnemar_piso_x_b5m'] = {
    'piso_so': b01, 'b5m_so': b10, 'ambos': int((a_ & b_).sum()),
    'nenhum': int((~a_ & ~b_).sum()),
    'p_binomial_exato': float(stats.binomtest(b01, b01 + b10, 0.5).pvalue)}
# dedup + nivel celula
pc = celu.pivot_table(index='cel', columns='alg', values='qq', aggfunc='first').astype(bool)
a2 = pc['moead_media'].to_numpy(); b2 = pc['b5m'].to_numpy()
n01 = int((a2 & ~b2).sum()); n10 = int((~a2 & b2).sum())
res['G2_mcnemar_celula_dedup'] = {
    'piso_so': n01, 'b5m_so': n10, 'ambos': int((a2 & b2).sum()),
    'nenhum': int((~a2 & ~b2).sum()),
    'p_binomial_exato': float(stats.binomtest(n01, max(n01 + n10, 1), 0.5).pvalue)}

# ── (H) onde: mapa por problema ────────────────────────────────────────────
mapa = piv.reset_index()
mapa['cel'] = mapa.exp + '/' + mapa.problema
mapa.to_csv(OUT + '/r1_pares.csv', index=False)
res['H_por_problema'] = (mapa.groupby('problema')[CFGS].sum().astype(int)
                         .to_dict('index'))

with open(OUT + '/r1_recontagem.json', 'w') as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
