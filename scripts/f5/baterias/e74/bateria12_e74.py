#!/usr/bin/env python
"""BATERIA 12 e74/CLMEA — as 5 checagens de fechamento do relatorio F5.3b:
 (1) N das estrategias == min(100,|Arc|) e k_local == min(20,|Arc|) em TODOS os blocos;
 (2) particao EXATA do criterio de saida do loop da s1 (>=90% | count>50);
 (3) padrao TEMPORAL do regime no-op (tercos do run);
 (4) espaco do NDSort (D30) por CORRELACAO DE POSTOS rotulo x rank ND (objetivos x decisao);
 (5) D74: dYmin/dYmax e o residuo do DTLZ4 (float32 x alpha=100).
Escreve: e74_b12.txt
"""
import json, os, warnings
import pandas as pd, numpy as np
from scipy.stats import spearmanr

warnings.filterwarnings('ignore')
ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
buf = []


def P(*a):
    s = ' '.join(str(x) for x in a); buf.append(s); print(s, flush=True)


def ndsort(F):
    n = len(F); rank = np.zeros(n, int); rem = np.ones(n, bool); r = 1
    while rem.any():
        idx = np.where(rem)[0]; A = F[idx]; keep = np.ones(len(idx), bool)
        for i in range(len(idx)):
            if ((A <= A[i]).all(1) & (A < A[i]).any(1)).any():
                keep[i] = False
        if not keep.any():
            break
        rank[idx[keep]] = r; rem[idx[keep]] = False; r += 1
    return rank


tot = ok = 0; kl_ok = kl_n = 0
rho_o, rho_d = [], []
for pr in sorted(os.listdir(ROOT)):
    b = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    hd = [r for r in recs if r['rec'] == 'header'][0]; D, M = hd['D'], hd['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(b + '__real.parquet')
    sur = pd.read_parquet(b + '__surrogate.parquet'); so = sur[sur.regime == 'online']
    sz = so.groupby('geracao').size().to_dict()
    F = real[[f'f{i}' for i in range(M)]].to_numpy(float)
    X = real[[f'x{i}' for i in range(D)]].to_numpy(float)
    lbl = {f'nivel_{i}': i for i in range(1, 5)}
    for ev in gens:
        n = sz.get(ev['geracao'])
        if n is None:
            continue
        arq = ev['arquivo'] - ev['aceito']
        tot += 1; ok += int(n == min(100, arq))
        if ev['estrategia'] == 3:
            kl_n += 1; kl_ok += int(ev.get('k_local_efetivo') == min(20, arq))
    noop = [e for e in gens if e['estrategia'] == 1 and e['count'] == 0]
    for ev in noop[:: max(1, len(noop) // 6)][:6]:
        blk = so[so.geracao == ev['geracao']]
        if blk.real_solution_id.isna().any():
            continue
        ids = blk.real_solution_id.to_numpy(int); lab = blk.pred_classe.map(lbl).to_numpy()
        if len(set(lab)) < 2:
            continue
        na = ev['arquivo']
        rho_o.append(spearmanr(lab, ndsort(F[:na])[ids]).statistic)
        rho_d.append(spearmanr(lab, ndsort(X[:na])[ids]).statistic)
    print(pr, 'ok', flush=True)

P('#'*100); P('# (1) N e k_local efetivos'); P('#'*100)
P('  bloco da ③ == min(100,|Arc|):', ok, '/', tot, '= %.3f%%' % (100 * ok / tot))
P('  k_local_efetivo == min(20,|Arc|):', kl_ok, '/', kl_n, '= %.3f%%' % (100 * kl_ok / kl_n))

S1 = pd.read_csv(f'{OUT}/e74_s1_mecanismo.csv')
P(''); P('#'*100); P('# (2) PARTICAO DO CRITERIO DE SAIDA DO LOOP DA s1'); P('#'*100)
prod = S1[S1['count'] > 0]
a = int((prod.frac_n1 >= .9).sum()); bg = int((prod['count'] == 51).sum())
both = int(((prod.frac_n1 >= .9) & (prod['count'] == 51)).sum())
P('  ciclos produtivos (count>0):', len(prod))
P('  saida A (frac_nivel1 >= 0,9 — regra do PAPER):', a)
P('  saida B (count == 51, i.e. count>50 — guarda do CODIGO):', bg, '| interseccao:', both)
P('  A + B - AB =', a + bg - both, '=> cobre', '%.2f%%' % (100 * (a + bg - both) / len(prod)), 'dos produtivos')
P('  count: min', int(prod['count'].min()), 'mediana', float(prod['count'].median()), 'max', int(prod['count'].max()))

P(''); P('#'*100); P('# (3) PADRAO TEMPORAL DO REGIME NO-OP'); P('#'*100)
R = pd.read_csv(f'{OUT}/e74_b10_di07b.csv')
R['idx'] = R.groupby('problema').cumcount(); R['n'] = R.groupby('problema').problema.transform('size')
R['pos'] = R.idx / (R.n - 1)
cut = pd.cut(R.pos, [0, 1 / 3, 2 / 3, 1.01], labels=['1o terco', '2o terco', '3o terco'], include_lowest=True)
t = pd.crosstab(cut, R.regime)
t['taxa_noop_%'] = (100 * t['no-op'] / (t['no-op'] + t['produtivo'])).round(2)
P(t.to_string())
P('  posicao relativa dos no-op: mediana %.3f | quartis %.3f / %.3f' % (
    R[R.regime == 'no-op'].pos.median(), R[R.regime == 'no-op'].pos.quantile(.25), R[R.regime == 'no-op'].pos.quantile(.75)))

P(''); P('#'*100); P('# (4) ESPACO DO NDSort (D30) — correlacao de postos rotulo x rank ND'); P('#'*100)
P('  blocos no-op com rotulo NAO-constante testados:', len(rho_o))
ro = np.array(rho_o, float); rd = np.array(rho_d, float)
P('  OBJETIVOS: mediana %.4f | media %.4f | min %.4f | max %.4f | NaN %d' % (
    np.nanmedian(ro), np.nanmean(ro), np.nanmin(ro), np.nanmax(ro), int(np.isnan(ro).sum())))
P('  DECISAO  : mediana %.4f | media %.4f | min %.4f | max %.4f | NaN %d (rank ND CONSTANTE=1 em decisao)' % (
    np.nanmedian(rd), np.nanmean(rd), np.nanmin(rd), np.nanmax(rd), int(np.isnan(rd).sum())))
m = ~np.isnan(rd)
P('  entre os blocos com rho_dec DEFINIDO: rho_obj > rho_dec em', int((ro[m] > rd[m]).sum()), '/', int(m.sum()))

P(''); P('#'*100); P('# (5) D74 — Ymin/Ymax vs front-1 recomputado'); P('#'*100)
d = pd.read_csv(f'{OUT}/e74_d74.csv')
P('  amostras:', len(d), '| dYmin <= 1e-6:', int((d.dYmin <= 1e-6).sum()), '| dYmax <= 1e-6:', int((d.dYmax <= 1e-6).sum()))
P('  dYmin max: %.3e | dYmax max (excl. DTLZ4): %.3e' % (d.dYmin.max(), d[d.problema != 'DTLZ4'].dYmax.max()))
P('  residuo: celulas com dYmax>1e-6 =', d[d.dYmax > 1e-6].problema.value_counts().to_dict())
P('  DTLZ4: |ND1| recomputado (①, float32) x n_front1 do evento (float64 do PlatEMO):')
P(d[d.dYmax > 1e-6][['geracao', 'n_front1', 'n_front1_ev']].to_string(index=False))

open(f'{OUT}/e74_b12.txt', 'w').write('\n'.join(buf))
print('\n[ok] e74_b12.txt')
