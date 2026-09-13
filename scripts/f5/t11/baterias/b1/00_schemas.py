#!/usr/bin/env python
"""Censo de schemas das 5 camadas do smoke T11 main/b1/MMF1 + comparacao com a rodada-42."""
import pandas as pd, pyarrow.parquet as pq, json, sys

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42'
OLD = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42'

for tag, base in [('T11', B), ('R42', OLD)]:
    print('=' * 30, tag)
    for lay in ['real', 'pop', 'surrogate', 'timing']:
        p = f'{base}__{lay}.parquet'
        s = pq.read_schema(p)
        n = pq.ParquetFile(p).metadata.num_rows
        print(f'  {lay:10s} rows={n:8d}  cols={len(s.names)}')
        print('     ', list(zip(s.names, [str(t) for t in s.types])))
