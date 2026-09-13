#!/usr/bin/env python
"""B6 — saude do smoke: IGD+/HV/trajetoria com a regua oficial src/metrics.py, contra a
celula homologa da rodada-42 e contra os pisos da rodada-42 no mesmo problema (MMF1)."""
import sys, json
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
sys.path.insert(0, ROOT)
from src import metrics as MT

CASES = {
    'T11_smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c238/exp_main_c238_MMF1_42__real.parquet',
    'R42_c238': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238/MMF1/42/exp_main_c238_MMF1_42__real.parquet',
}
PISOS = ['nsga2', 'nsga3', 'moead', 'smsemoa']
for p in PISOS:
    CASES[f'R42_{p}'] = f'/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/{p}/MMF1/42/exp_main_{p}_MMF1_42__real.parquet'

R = MT.reference_set('MMF1')
rows = []
for tag, p in CASES.items():
    try:
        t = pq.read_table(p).to_pandas()
    except Exception as e:
        print(f'{tag}: INDISPONIVEL ({e.__class__.__name__})'); continue
    fcols = sorted([c for c in t.columns if len(c) > 1 and c[0] == 'f' and c[1:].isdigit()], key=lambda z: int(z[1:]))
    F = t[fcols].to_numpy(np.float64)
    fe = t['fe_index'].to_numpy()
    m = MT.metrics_of_set(F, 'MMF1', ref_norm=R)
    traj = MT.trajectory(F, fe, 'MMF1', n_checkpoints=20, ref_norm=R)
    ip = [c['igd_plus'] for c in traj]
    viol = int(sum(1 for a, b in zip(ip, ip[1:]) if b > a + 1e-12))
    rows.append(dict(fonte=tag, n=len(F), **{k: v for k, v in m.items() if not isinstance(v, (list, dict))},
                     cp0=ip[0], cpN=ip[-1], ganho=ip[0] / max(ip[-1], 1e-30), viol_monot=viol, n_cp=len(ip)))
D = pd.DataFrame(rows)
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 40)
print(D.to_string(index=False))
D.to_csv(f'{ROOT}/f5/t11/baterias/c238/saude_t11.csv', index=False)

print('\nreferencia F5 (saude_celula.csv, MMF1): igd_plus=0.041409 hv=0.785507 rank 5/17 melhor_piso=nsga3 0.057013 razao 0.726 viol=0 ganho=67.89')
