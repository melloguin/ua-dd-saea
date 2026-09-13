#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_ibea.py — F5.3b/e103 · evidencia INDIRETA do motor IBEA (Alg. 1 do paper):
elitismo pais+filhos com truncamento iterativo (linhas 8-13) => sobrevivencia de parte de
P_t em P_{t+1}, e preservacao de dominancia (eq. 24) => nenhum membro RETIRADO domina um
membro MANTIDO no espaco predito pelo modelo LIDER.  READ-ONLY.
Saida: f5/baterias/e103/ibea_elitismo_e103.csv
"""
import os, json, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')

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
    xc = ['x%d' % i for i in range(D)]
    muc = ['mu_%d' % i for i in range(M)]
    sur = pq.read_table(os.path.join(d, base + '__surrogate.parquet')).to_pandas()
    off = sur[(sur.regime != 'sonda') & (sur.modelo_flag == lider)]
    ov, front, retidos = [], [], []
    prev = None
    for g in range(1, len(gens) + 1):
        blk = off[off.geracao == g]
        X = blk[xc].values.astype(np.float32)
        keys = set(map(tuple, X.tolist()))
        if prev is not None:
            ov.append(len(keys & prev) / 100.0)
        prev = keys
        MU = blk[muc].values.astype(np.float64)
        n = len(MU)
        nd = np.ones(n, bool)
        for i in range(n):
            if (np.all(MU <= MU[i], axis=1) & np.any(MU < MU[i], axis=1)).any():
                nd[i] = False
        front.append(int(nd.sum()))
    rows.append(dict(label=lab, problema=prob, D=D, M=M, lider=lider,
                     overlap_med=float(np.median(ov)), overlap_min=float(np.min(ov)),
                     overlap_g1g2=float(ov[0]), overlap_final=float(ov[-1]),
                     front1_recomp_g1=front[0], front1_recomp_ult=front[-1],
                     front1_log_g1=gens[0]['n_front1'], front1_log_ult=gens[-1]['n_front1'],
                     front1_bate=int(sum(1 for a, b in zip(front, [x['n_front1'] for x in gens]) if a == b)),
                     n_gen=len(gens)))
    print('ok', lab, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'ibea_elitismo_e103.csv'), index=False)
print('\nn_front1 recomputado == n_front1 logado: %d/%d celulas com 99/99'
      % (int((df.front1_bate == df.n_gen).sum()), len(df)))
print('overlap P_t -> P_{t+1}: mediana das medianas %.3f  min global %.3f'
      % (df.overlap_med.median(), df.overlap_min.min()))
print(df.round(3).to_string(index=False))
