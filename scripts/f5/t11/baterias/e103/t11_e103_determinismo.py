#!/usr/bin/env python3
"""T11/F5-bis — DETERMINISMO do e103 (o que a F5 declarou como teto T1).

Descoberta: o canto `small`+`lhs` do sweep (D51) É a configuração do `off`
(31D−1, LHS) — logo as 5 células `swap_small-lhs_*` são RE-EXECUÇÕES
INDEPENDENTES das 5 células `off` homônimas. Este script mostra que os dois
runs são BYTE-A-BYTE idênticos apesar de terem run_id, exp, timestamps e wall
diferentes — o "re-run bit-idêntico" que o teto T1 pedia.

READ-ONLY.
"""
from __future__ import annotations
import hashlib, json, os

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
PARES = ['ZDT1', 'ZDT4', 'DTLZ2', 'WFG9', 'MMF16_20']
CAM = ['__surrogate.parquet', '__real.parquet', '__pop.parquet',
       '__timing.parquet', '__final.parquet']


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


for p in PARES:
    A = os.path.join(RES, p, '42', f'exp_off_e103_{p}_42')
    B = os.path.join(RES, f'swap_small-lhs_{p}', '42',
                     f'exp_sweep-small-lhs_e103_{p}_42')
    ma, mb = json.load(open(A + '.manifest.json')), json.load(open(B + '.manifest.json'))
    iguais = [c for c in CAM if md5(A + c) == md5(B + c)]
    print(f'{p:10s} camadas byte-idênticas: {len(iguais)}/{len(CAM)} {iguais}')
    print(f'           run_id  {ma["run_id"]:34s} × {mb["run_id"]}')
    print(f'           created {ma["created_at"]} × {mb["created_at"]}'
          f'  wall {ma["timing"]["tempo_total_s"]:.3f}s × {mb["timing"]["tempo_total_s"]:.3f}s')
