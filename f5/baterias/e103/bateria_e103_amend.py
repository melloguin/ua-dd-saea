#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_amend.py — F5.3b/e103 · a 2a query-joia: PROVAR por dado que os membros do
dataset mantem o F REAL tambem no ramo RBFN (AmendRBFCal), coisa que a ③ nao mostra
(a linha RBFN e' a RE-PREDICAO INCONDICIONAL — sigma_dict/C4).
Metodo: recomputar n_front1 da populacao selecionada com os mu do modelo LIDER e
comparar com o n_front1 logado no ⑥, em 3 variantes:
  (i)  mu cru do lider (③ como esta)
  (ii) mu do lider com os membros do dataset SUBSTITUIDOS pelo f REAL da ①  (= amend)
  (iii) idem (ii) em float64 exato
READ-ONLY.  Saida: f5/baterias/e103/amend_front1_e103.csv
"""
import os, json, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')


def nfront(F):
    n = len(F)
    k = np.ones(n, bool)
    for i in range(n):
        if (np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)).any():
            k[i] = False
    return int(k.sum())


rows = []
for lab in sorted(os.listdir(RES)):
    d = os.path.join(RES, lab, '42')
    if not os.path.isdir(d):
        continue
    mf = [f for f in glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json')) if '__final' not in f]
    base = os.path.basename(mf[0])[:-len('.manifest.json')]
    prob = base.split('_e103_')[1][:-len('_42')]
    recs = []
    for line in open(os.path.join(d, base + '.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    hdr = [x for x in recs if x.get('rec') == 'header'][0]
    gens = sorted([x for x in recs if x.get('rec') == 'e103_gen'], key=lambda x: x['geracao'])
    D, M = hdr['D'], hdr['M']
    lider = 'Kriging-DACE' if gens[0]['modelo_lider'] == 'Kriging' else 'RBFN'
    muc = ['mu_%d' % i for i in range(M)]
    fc = ['f%d' % i for i in range(M)]
    real = pq.read_table(os.path.join(d, base + '__real.parquet')).to_pandas()
    RF = real.set_index('solution_id')[fc]
    sur = pq.read_table(os.path.join(d, base + '__surrogate.parquet')).to_pandas()
    off = sur[(sur.regime != 'sonda') & (sur.modelo_flag == lider)]
    ok_cru = ok_amend = 0
    for g in gens:
        blk = off[off.geracao == g['geracao']]
        MU = blk[muc].values.astype(np.float64)
        n1 = nfront(MU)
        rs = blk['real_solution_id'].values
        m = ~pd.isna(rs)
        MU2 = MU.copy()
        if m.any():
            MU2[m] = RF.loc[rs[m].astype(int)].values.astype(np.float64)
        n2 = nfront(MU2)
        ok_cru += int(n1 == g['n_front1'])
        ok_amend += int(n2 == g['n_front1'])
    rows.append(dict(label=lab, problema=prob, D=D, M=M, lider=lider, n_gen=len(gens),
                     front1_cru_bate=ok_cru, front1_amend_bate=ok_amend,
                     ndsm_g1=gens[0]['n_ds_membros'], ndsm_ult=gens[-1]['n_ds_membros']))
    print('ok', lab, rows[-1]['front1_cru_bate'], rows[-1]['front1_amend_bate'], flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'amend_front1_e103.csv'), index=False)
print('\nTOTAL geracoes: %d' % df.n_gen.sum())
print('n_front1 bate com mu CRU do lider          : %d (%.1f%%)'
      % (df.front1_cru_bate.sum(), 100 * df.front1_cru_bate.sum() / df.n_gen.sum()))
print('n_front1 bate com mu AMENDADO (f real nos membros do dataset): %d (%.1f%%)'
      % (df.front1_amend_bate.sum(), 100 * df.front1_amend_bate.sum() / df.n_gen.sum()))
print('celulas com 99/99 no amendado: %d/45' % int((df.front1_amend_bate == df.n_gen).sum()))
print(df.to_string(index=False))
