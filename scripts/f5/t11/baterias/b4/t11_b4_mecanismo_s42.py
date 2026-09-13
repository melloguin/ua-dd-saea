"""T11/b4 — bateria 4: RE-MEDE no corpus PRINCIPAL (s42, 25 celulas) as
identidades do mecanismo, direto do ⑥ bruto (nao do CSV da F5), para conferir
que o veredito da F5 se sustenta e que a declaracao NOVA do sigma_dict
(p0 = MAE da categoria II) e a que os dados exibem.
READ-ONLY.
"""
import json, os
import numpy as np
import pandas as pd

S42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4'

rows = []
for p in sorted(os.listdir(S42)):
    jl = f'{S42}/{p}/42/exp_main_b4_{p}_42.jsonl'
    for r in map(json.loads, open(jl)):
        if r.get('rec') != 'b4_gen':
            continue
        rows.append(dict(problema=p, g=r['geracao'], p0=r['p0'], p1=r['p1'], rr=r['rr'],
                         tr=r['tr'], ramo=r['ramo'], lote=r['lote'], fe=r['fe'],
                         arquivo=r['arquivo'], n_treino=r['n_treino'],
                         n_acumulado=r['n_acumulado'], ftm=r.get('fe_treino_max'),
                         n_refs=r['n_refs'], guard_rp=r.get('guard_randperm'),
                         nL=len(r['L_sel']) if isinstance(r['L_sel'], list) else 1,
                         Lmin=(min(r['L_sel']) if isinstance(r['L_sel'], list) and r['L_sel']
                               else (r['L_sel'] if not isinstance(r['L_sel'], list) else np.nan))))
d = pd.DataFrame(rows)
d['p0'] = pd.to_numeric(d.p0, errors='coerce'); d['p1'] = pd.to_numeric(d.p1, errors='coerce')
d.to_csv(f'{OUT}/t11_b4_geracoes_s42.csv', index=False)
N = len(d)
print(f'=== s42: {d.problema.nunique()} celulas · {N} geracoes ===\n')

# A13 — o gate SAS.m:27  p0<0.4 || (p1<a && p0<b)
a, b = d.tr, 1 - d.tr
gate_cod = (d.p0 < 0.4) | ((d.p1 < a) & (d.p0 < b))
gate_pap = (d.p0 < a) | ((d.p1 < a) & (d.p0 < b))
r1 = d.ramo == 1
print(f'A13 gate CODIGO  `p0<0.4 | (p1<tr & p0<1-tr)` == (ramo==1): {int((gate_cod == r1).sum())}/{N}'
      f'  ({(gate_cod == r1).mean() * 100:.3f}%)')
print(f'A13 gate PAPER   `p0<tr  | (p1<tr & p0<1-tr)` == (ramo==1): {int((gate_pap == r1).sum())}/{N}'
      f'  ({(gate_pap == r1).mean() * 100:.2f}%)  — falha em {int((gate_pap != r1).sum())} geracoes')
print(f'    ramo: ' + str(dict(d.ramo.value_counts().sort_index())))
print(f'    ramo1 sob a regra do PAPER seria {int(gate_pap.sum())} (vs {int(r1.sum())} reais) = '
      f'{r1.sum() / max(gate_pap.sum(), 1):.2f}x')
fe1 = d.loc[d.ramo == 1, 'lote'].sum(); fe4 = d.loc[d.ramo == 4, 'lote'].sum()
print(f'    FEs: ramo1={int(fe1)} · ramo4={int(fe4)} · total={int(d.lote.sum())}'
      f' · fracao gateada={fe1 / d.lote.sum() * 100:.1f}%')
print(f'    tr max={d.tr.max():.6f} (teto 0,25 => 0,4 e ESTRUTURALMENTE mais permissivo)')

# A8 — tr
print(f'\nA8  tr == 0,5*min(rr,1-rr): {int((np.abs(d.tr - 0.5 * np.minimum(d.rr, 1 - d.rr)) < 1e-12).sum())}/{N}')
# A7 — rr racional exato n1/|Arc|
n1 = np.round(d.rr * d.n_treino)
print(f'A7  rr == n1/n_treino (racional exato): '
      f'{int((np.abs(d.rr - n1 / d.n_treino) < 1e-12).sum())}/{N}')
# A9 — particao
D1 = n1.astype(int); D0 = (d.n_treino - D1).astype(int)
ceil34 = np.ceil(0.75 * D0).astype(int) + np.ceil(0.75 * D1).astype(int)
floor34 = np.floor(0.75 * D0).astype(int) + np.floor(0.75 * D1).astype(int)
print(f'A9  n_acumulado == ceil(3/4|D0|)+ceil(3/4|D1|)  (DataProcess.m:19-20): '
      f'{int((ceil34 == d.n_acumulado).sum())}/{N}')
print(f'    (pseudo-codigo do paper, floor): {int((floor34 == d.n_acumulado).sum())}/{N}')

# A12 -> declaracao NOVA do sigma_dict: p0 = MAE da categoria II (rotulo 1)
teste1 = np.floor(D1 / 4).astype(int)   # |teste| da classe 1
teste0 = np.floor(D0 / 4).astype(int)
nan0 = d.p0.isna()
print(f'\nA12/T11 sigma_dict declara "p0 = MAE da categoria II (rotulo 1, CSEA.m:78)".')
print(f'    p0 NaN em {int(nan0.sum())} geracoes; p1 NaN em {int(d.p1.isna().sum())}')
print(f'    p0_NaN <=> floor(|D1|/4)==0 (teste SEM categoria II): '
      f'{int((nan0 == (teste1 == 0)).sum())}/{N}')
print(f'    p0_NaN <=> floor(|D0|/4)==0 (teste SEM categoria I) : '
      f'{int((nan0 == (teste0 == 0)).sum())}/{N}  [antecedente ocorre em {int((teste0 == 0).sum())}]')
print(f'    magnitude: p0 media {d.p0.mean():.4f} · p1 media {d.p1.mean():.4f} · rr mediano {d.rr.median():.4f}')

# A23 — fe_treino_max nao-monotonico
q = 0; cel = 0
for p, s in d.groupby('problema'):
    dd = pd.to_numeric(s.sort_values('g').ftm, errors='coerce').diff()
    k = int((dd < 0).sum()); q += k; cel += (k > 0)
print(f'\nA23 fe_treino_max nao-monotonico: quedas em {cel}/25 celulas, Sigma={q}')
print(f'    n_acumulado < n_treino: {int((d.n_acumulado < d.n_treino).sum())}/{N}')
print(f'A4  n_refs==6: {int((d.n_refs == 6).sum())}/{N}')
print(f'A29 guard_randperm True: {int(d.guard_rp.sum())}/{N}')
print(f'A16 ramo 4 com lote==1: {int(((d.ramo == 4) & (d.lote == 1)).sum())}/{int((d.ramo == 4).sum())}')
print(f'A18 ramo 1 com lote<=12: {int(((d.ramo == 1) & (d.lote <= 12)).sum())}/{int((d.ramo == 1).sum())}')
print(f'A17 stalls (lote==0): {int((d.lote == 0).sum())} — todos em ramo 1: '
      f'{int(((d.lote == 0) & (d.ramo == 1)).sum())}')
print(f'A14 min(L) nos infills de ramo 1: {d.loc[d.ramo == 1, "Lmin"].min():.7f} (gate L>0,9)')
cel8 = [p for p, s in d.groupby('problema') if (s.ramo == 1).sum() == 0]
print(f'    celulas SEM nenhum ramo 1: {len(cel8)} -> {cel8}')
