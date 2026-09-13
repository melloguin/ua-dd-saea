#!/usr/bin/env python3
"""T11/F5-bis — o corpus da INSTRUMENTAÇÃO NOVA do e103.

READ-ONLY. Cobre, com números medidos:
  S1  ⑤: schema_version/campanha_id/repo_hash/sonda.desligada  (s42 × smoke)
  S2  ⑤: `params` e `sigma_dict` BIT-IDÊNTICOS entre s42 e smoke (o mecanismo
      declarado NÃO mudou na T11)
  S3  ⑥: censo de eventos e esquema por evento  (s42 × smoke) → o delta da T11
  S4  ④: `tempo_geracao_s`  — I-7/A5: NaN na s42, = fit+busca no smoke
  S5  G-6 (não-perturbação): a prova FORTE — as 19.800 linhas de BUSCA da ③
      bit-idênticas COM e SEM sonda (a ① do e103 é o dataset injetado e não
      pode mudar; o hash da ① NÃO prova nada sobre a busca)
  S6  cross-arquitetura: s42 (vm3) × smoke (Mac arm64) — onde a busca diverge
      e quanto o ENDPOINT se move
  S7  sonda: WAPE/corr/cobertura por MODELO, s42 × smoke × g6_com
  S8  ERRATA 7 e ERRATA 14 re-medidas
"""
from __future__ import annotations
import json, hashlib, os
import numpy as np
import pyarrow.parquet as pq

S42 = ('/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/'
       'e103/MMF1/42/exp_off_e103_MMF1_42')
SMK = ('/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/'
       'experiments/off/e103/exp_off_e103_MMF1_42')
COM = ('/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/'
       'experiments/off/e103/exp_off_e103_MMF1_42')
SEM = ('/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/'
       'experiments/off/e103/exp_off_e103_MMF1_42')
GAB = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'


def evs(p):
    out = []
    for line in open(p + '.jsonl', encoding='utf-8', errors='replace'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def busca(p):
    t = pq.read_table(p + '__surrogate.parquet').to_pandas()
    return t[t.regime != 'sonda'].reset_index(drop=True)


def h(df, cols):
    return hashlib.sha256(np.ascontiguousarray(
        df[cols].to_numpy(np.float64)).tobytes()).hexdigest()[:16]


COLS = ['x0', 'x1', 'mu_0', 'mu_1']
print('== S1/S2 ⑤')
a, b = (json.load(open(S42 + '.manifest.json')),
        json.load(open(SMK + '.manifest.json')))
for k in ('schema_version', 'campanha_id', 'repo_hash'):
    print(f'   {k:16s} s42={a.get(k)!r:12} smoke={b.get(k)!r}')
print('   sonda.desligada  s42=%s smoke=%s' %
      ('desligada' in a['sonda'], 'desligada' in b['sonda']))
print('   params BIT-IDÊNTICOS      :', a['params'] == b['params'])
print('   sigma_dict BIT-IDÊNTICOS  :', a['sigma_dict'] == b['sigma_dict'])

print('== S3/S8 ⑥')
import collections
for tag, p in (('s42', S42), ('smoke', SMK)):
    E = evs(p)
    g = [x for x in E if x['rec'] == 'e103_gen']
    bu = [x for x in E if x['rec'] == 'e103_busca']
    print(f'   {tag}: censo={dict(sorted(collections.Counter(x["rec"] for x in E).items()))}')
    print(f'        e103_gen com margem_3sigma_stats={sum(1 for x in g if x.get("margem_3sigma_stats"))}/{len(g)}'
          f' · com margem_3sigma(plano)={sum(1 for x in g if "margem_3sigma" in x)}'
          f' · com tempo_busca_s={sum(1 for x in g if "tempo_busca_s" in x)}'
          f' · com tempo_fit_s={sum(1 for x in g if "tempo_fit_s" in x)}')
    print(f'        e103_busca campos={sorted(bu[0])}')

print('== S4 ④ tempo_geracao_s')
for tag, p in (('s42', S42), ('smoke', SMK), ('g6com', COM), ('g6sem', SEM)):
    t = pq.read_table(p + '__timing.parquet').to_pandas().iloc[0]
    soma = t.tempo_fit_s + t.tempo_busca_s
    print(f'   {tag:6s} fit={t.tempo_fit_s:.6f} busca={t.tempo_busca_s:.6f} '
          f'sonda={t.tempo_pred_sonda_s:.6f} geracao={t.tempo_geracao_s} '
          f'| fit+busca={soma:.6f} igual={np.isclose(t.tempo_geracao_s, soma)}')

print('== S5 G-6 (não-perturbação sobre a BUSCA)')
bc, bs = busca(COM), busca(SEM)
print('   linhas de busca com/sem :', len(bc), len(bs))
print('   sha256(X+μ) com         :', h(bc, COLS))
print('   sha256(X+μ) sem         :', h(bs, COLS))
print('   BIT-IDÊNTICAS           :', h(bc, COLS) == h(bs, COLS))
print('   σ nan-safe iguais       :', all(np.array_equal(bc[c].to_numpy(float),
                                                         bs[c].to_numpy(float), equal_nan=True)
                                          for c in ('sigma_0', 'sigma_1')))
print('   modelo_flag idêntico    :', bool((bc.modelo_flag.values == bs.modelo_flag.values).all()))
print('   sha256 dos BYTES da ①   :',
      hashlib.sha256(open(COM + '__real.parquet', 'rb').read()).hexdigest()[:16], '/',
      hashlib.sha256(open(SEM + '__real.parquet', 'rb').read()).hexdigest()[:16])

print('== S6 cross-arquitetura (vm3 × Mac)')
b42, bsm = busca(S42), busca(SMK)
d = np.abs(b42[['x0', 'x1']].to_numpy(float) - bsm[['x0', 'x1']].to_numpy(float))
dif = (d > 0).any(1)
b42 = b42.assign(dif=dif)
per = b42.groupby('geracao')['dif'].sum()
print('   linhas de busca com X diferente : %d/%d' % (dif.sum(), len(b42)))
print('   PRIMEIRA geração divergente     :', int(per[per > 0].index.min()))
g1 = [x for x in evs(S42) if x['rec'] == 'e103_gen']
g2 = [x for x in evs(SMK) if x['rec'] == 'e103_gen']
print('   kflag idêntico nas 99 gerações  :',
      [x['kflag'] for x in g1] == [x['kflag'] for x in g2])
print('   n_ds_membros idêntico           :',
      [x['n_ds_membros'] for x in g1] == [x['n_ds_membros'] for x in g2])

print('== S7 sonda por modelo (join POSICIONAL, espaço cru)')
g = pq.read_table(GAB).to_pandas()
for tag, p in (('s42', S42), ('smoke', SMK), ('g6com', COM)):
    t = pq.read_table(p + '__surrogate.parquet').to_pandas()
    s = t[t.regime == 'sonda']
    for mdl, blk in s.groupby('modelo_flag', sort=False):
        blk = blk.reset_index(drop=True)
        dX = np.abs(blk[['x0', 'x1']].to_numpy(np.float32) -
                    g[['x0', 'x1']].to_numpy(np.float32)).max()
        w = [float(np.abs(blk[f'mu_{j}'] - g[f'f{j}']).sum() / np.abs(g[f'f{j}']).sum())
             for j in (0, 1)]
        print(f'   {tag:6s} {mdl:13s} dX_max={dX} WAPE={[round(x,6) for x in w]}')
