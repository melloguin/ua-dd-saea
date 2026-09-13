# -*- coding: utf-8 -*-
"""T11/c217 — BATERIA 4: sonda (regua Sobol s42, bloco ESTRATIFICADO smoke — SEPARADOS,
regra 12), saude e contrato. READ-ONLY."""
import json, glob, os
from collections import Counter
import pandas as pd, numpy as np

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = os.path.join(RAIZ, 'ua-dd-saea/f5/t11/baterias/c217')
SONDA = os.path.join(RAIZ, 'ua-dd-saea/data/sonda')

# ---------------- BLOCO A — REGUA SOBOL (s42; comparavel entre configs) -------------
print('== BLOCO A · regua Sobol (regime=="sonda") — s42, 25 celulas ==')
tot_b = ok_dx = tot_l = 0
frac0, cel_rows = [], []
for cel in sorted(glob.glob(os.path.join(RAIZ, 'resultados_experimentos/c217/*/42'))):
    prob = cel.split('/')[-2]
    sur = pd.read_parquet(glob.glob(os.path.join(cel, '*__surrogate.parquet'))[0])
    snd = sur[sur.regime == 'sonda']
    art = pd.read_parquet(os.path.join(SONDA, 'sonda_%s.parquet' % prob))
    xc_a = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
    xc_s = [c for c in snd.columns if c.startswith('x') and c[1:].isdigit()]
    Xa = art[xc_a].to_numpy(np.float32)
    nb = 0; dxmax = 0.0; f0 = []
    for g, blk in snd.groupby('geracao'):
        nb += 1; tot_l += len(blk)
        Xb = blk[xc_s].to_numpy(np.float32)
        d = np.abs(Xb - Xa[:len(Xb)]).max()
        dxmax = max(dxmax, float(d)); ok_dx += (d == 0.0)
        f0.append(float((blk.pred_score == 0).mean()))
    tot_b += nb
    cel_rows.append(dict(problema=prob, n_blocos=nb, linhas=len(snd), dxmax=dxmax,
                         frac_pred0_med=float(np.median(f0)),
                         blocos_degenerados=int(sum(1 for v in f0 if v == 1.0)),
                         mu_null=float(snd.filter(like='mu_').isna().mean().mean()) if len(snd.filter(like='mu_').columns) else np.nan))
    frac0 += f0
S = pd.DataFrame(cel_rows); S.to_csv(os.path.join(OUT, 't11_c217_regua_sobol.csv'), index=False)
print('  blocos=%d  linhas=%d  linhas/bloco distintas=%s' % (tot_b, tot_l, sorted(set(S.linhas//S.n_blocos))))
print('  join POSICIONAL bit-a-bit (max|dX| float32 == 0): %d/%d blocos' % (ok_dx, tot_b))
print('  blocos 100%% degenerados (pred_score==0 em todas as 2000 linhas): %d/%d (%.1f%%)'
      % (int(S.blocos_degenerados.sum()), tot_b, 100*S.blocos_degenerados.sum()/tot_b))
print('  celulas com TODOS os blocos degenerados: %s'
      % list(S[S.blocos_degenerados == S.n_blocos].problema))

# ---------------- BLOCO B — ESTRATIFICADO (smoke; NUNCA junto com A) ----------------
print('\n== BLOCO B · sonda_estratificada (smoke T11) — SEPARADO (regra 12) ==')
SM = os.path.join(RAIZ, 'evidencia_T11/smoke_matlab/experiments/main/c217')
sur = pd.read_parquet(glob.glob(os.path.join(SM, '*__surrogate.parquet'))[0])
real = pd.read_parquet(glob.glob(os.path.join(SM, '*__real.parquet'))[0])
art = pd.read_parquet(os.path.join(SONDA, 'sonda_MMF1.parquet'))
E = sur[sur.regime == 'sonda_estratificada']
xc = [c for c in E.columns if c.startswith('x') and c[1:].isdigit()]
xr = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
xa = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
XE = E[xc].to_numpy(np.float32); XR = real[xr].to_numpy(np.float32); XA = art[xa].to_numpy(np.float32)
setR = {tuple(r) for r in XR}; setA = {tuple(r) for r in XA}
inR = sum(1 for r in XE if tuple(r) in setR); inA = sum(1 for r in XE if tuple(r) in setA)
print('  %d linhas em %d blocos; blocos por geracao: %s' % (len(E), E.geracao.nunique(),
      sorted(Counter(E.geracao).values())[:3]))
print('  X do bloco presente na ① (avaliado de verdade): %d/%d (%.2f%%)' % (inR, len(XE), 100*inR/len(XE)))
print('  X do bloco presente no artefato da sonda (f verdadeiro tabelado): %d/%d' % (inA, len(XE)))
print('  colunas com valor: pred_score nao-nulo %d/%d ; mu/sigma nao-nulos %d'
      % (int(E.pred_score.notna().sum()), len(E),
         int(E.filter(regex=r'^(mu|sigma)_').notna().sum().sum())))
print('  distribuicao pred_score no bloco estratificado: %s' % dict(Counter(E.pred_score)))
regua = sur[sur.regime == 'sonda']
print('  COMPARACAO INTRA-CONFIG (permitida): frac(score==0) estratificado %.4f x regua %.4f'
      % (float((E.pred_score == 0).mean()), float((regua.pred_score == 0).mean())))

# ---------------- BLOCO C — contrato/saude ----------------
print('\n== BLOCO C · contrato e saude ==')
con = pd.read_csv(os.path.join(RAIZ, 'ua-dd-saea/f5/contrato_f52b.csv'))
c = con[con.astype(str).apply(lambda r: r.str.contains('c217').any(), axis=1)]
print('  contrato_f52b linhas c217: %d ; achados: %s' % (len(c), sorted(set(c.iloc[:, -1].astype(str)))[:4]))
integ = pd.read_csv(os.path.join(RAIZ, 'ua-dd-saea/f5/integridade_f52a.csv'))
print('  integridade_f52a linhas c217: %d'
      % len(integ[integ.astype(str).apply(lambda r: r.str.contains('c217').any(), axis=1)]))
sonda52 = pd.read_csv(os.path.join(RAIZ, 'ua-dd-saea/f5/sonda_f52e.csv'), nrows=200000)
print('  sonda_f52e linhas c217: %d (esperado 0 — sem cabeca de valor)'
      % len(sonda52[sonda52.astype(str).apply(lambda r: r.str.contains('c217').any(), axis=1)]))
met = pd.read_csv(os.path.join(RAIZ, 'ua-dd-saea/f5/metricas_finais_f52c.csv'))
mc = met[met.get('alg', pd.Series(dtype=str)).astype(str) == 'c217'] if 'alg' in met.columns else pd.DataFrame()
print('  metricas_finais_f52c linhas c217: %d ; colunas: %s' % (len(mc), list(met.columns)[:12]))
