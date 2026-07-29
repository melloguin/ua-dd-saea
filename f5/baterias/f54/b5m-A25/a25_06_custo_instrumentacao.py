#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / passo 3b — o criterio DI-12.1 e COMPORTAMENTO (custo), nao pureza.
Quanto custaria capturar `p_wrong_stats` dentro de ProbMOEAD_select.do?
Locus: ProbMOEAD_select.py:82-88 — `probabilities` (20 floats) e `selection`.
Chamadas por run = 1 por FE-surrogate = 40.000 (pop 50) / 39.900 (pop 105).
Duas rotas medidas:
  (A) reduzir NA HORA (min/med/max do vetor de 20) e acumular 3 floats
  (B) so acumular o vetor (append) e reduzir 1x por geracao
Comparo com o wall real do b5m (④ tempo_busca_s dos 45 runs).
"""
import os, time, numpy as np, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
N_CALLS = 40000
rng = np.random.RandomState(0)
vet = [rng.rand(20) for _ in range(1000)]

t0 = time.time()
acc = []
for i in range(N_CALLS):
    p = vet[i % 1000]
    acc.append((float(p.min()), float(np.median(p)), float(p.max())))
tA = time.time() - t0

t0 = time.time()
acc2 = []
for i in range(N_CALLS):
    acc2.append(vet[i % 1000])
    if (i + 1) % 50 == 0:
        a = np.concatenate(acc2[-50:])
        _ = (a.min(), np.median(a), a.max())
tB = time.time() - t0

t0 = time.time()
acc3 = []
for i in range(N_CALLS):
    p = vet[i % 1000]
    acc3.append(int((p > 0.5).sum()))          # n_substituicoes = len(selection)
tC = time.time() - t0

walls = []
for lab in sorted(d for d in os.listdir(ROOT) if not d.startswith(".")):
    d = os.path.join(ROOT, lab, "42")
    f = [x for x in os.listdir(d) if x.endswith("__timing.parquet")] \
        if os.path.isdir(d) else []
    if not f:
        continue
    t = pq.read_table(os.path.join(d, f[0]))
    if "tempo_busca_s" in t.column_names:
        v = [x for x in np.asarray(t.column("tempo_busca_s")) if x is not None]
        if v:
            walls.append(float(v[0]))

w_med = float(np.median(walls))
print("rota (A) reduzir na hora  : %.3f s / run  (%d chamadas)" % (tA, N_CALLS))
print("rota (B) acumular+reduzir : %.3f s / run" % tB)
print("rota (C) n_substituicoes  : %.3f s / run" % tC)
print("tempo_busca_s do b5m (45 celulas): mediana %.1f s  min %.1f  max %.1f"
      % (w_med, min(walls), max(walls)))
print("sobrecarga relativa: (A) %.4f%%   (B) %.4f%%   (C) %.4f%%"
      % (100 * tA / w_med, 100 * tB / w_med, 100 * tC / w_med))
print("volume do log: 1 registro/geracao x 3 floats = %d floats/run (pop 50)"
      % (3 * 800))
print("P_wrong POR COMPARACAO (A12) seria: 40.000 chamadas x 20 vizinhos = "
      "%d valores/run  -> %.1f M/celula, %.2f G nas 45x30" %
      (40000 * 20, 40000 * 20 / 1e6, 40000 * 20 * 45 * 30 / 1e9))
