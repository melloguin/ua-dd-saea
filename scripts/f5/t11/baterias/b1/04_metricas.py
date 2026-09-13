#!/usr/bin/env python
"""Parte 4: metricas oficiais (IGD+ D70, HV, spacing) do smoke b1/MMF1 T11
contra a MESMA celula da rodada-42 e contra o b3 do mesmo smoke. READ-ONLY."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/src')
import metrics as MT

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b1'
CEL = {
    'b1_T11smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42__real.parquet',
    'b1_R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42__real.parquet',
    'b3_T11smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b3/exp_main_b3_MMF1_42__real.parquet',
    'b3_R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b3/MMF1/42/exp_main_b3_MMF1_42__real.parquet',
}
ref = MT.reference_set('MMF1')
lin = []
for k, p in CEL.items():
    try:
        df = pd.read_parquet(p)
    except Exception as e:
        print(k, 'AUSENTE', e); continue
    F = df[['f0', 'f1']].to_numpy(np.float64)
    m = MT.metrics_of_set(F, 'MMF1', ref_norm=ref)
    m['celula'] = k; m['n'] = len(F)
    lin.append(m)
T = pd.DataFrame(lin).set_index('celula')
print(T.to_string())
T.to_csv(f'{OUT}/b1_metricas.csv')

# trajetoria (o smoke tem orcamento minusculo -> so 6 checkpoints)
df = pd.read_parquet(CEL['b1_T11smoke'])
F = df[['f0', 'f1']].to_numpy(np.float64)
tr = MT.trajectory(F, df.fe_index.to_numpy(), 'MMF1', ref_norm=ref)
tr = pd.DataFrame(tr) if not isinstance(tr, pd.DataFrame) else tr
print('\nTRAJETORIA T11:'); print(tr.to_string())
tr.to_csv(f'{OUT}/b1_trajetoria_T11.csv', index=False)
d = tr['igd_plus'].to_numpy()
print('IGD+ monotonico (nao-cresc)?', bool(np.all(np.diff(d) <= 1e-12)), 'violacoes=', int((np.diff(d) > 1e-12).sum()))
h = tr['hv'].to_numpy()
print('HV nunca cai?', bool(np.all(np.diff(h) >= -1e-12)), 'quedas=', int((np.diff(h) < -1e-12).sum()))
print('ganho IGD+ 1o->ultimo:', f'{d[0]/d[-1]:.2f}x')
