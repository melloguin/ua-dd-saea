"""Bateria b1 - parte 7: consolidacao final.
n_treino minimo, (2) gen1 == DoE, n_front1, fe_treino_max da sonda, dWAPE/corr por
celula, cabeca-a-cabeca com b3 e com o nsga2 (a contraparte do paper), cobertura de
lambda, chaves do modelo_hp.
Saida: b1_final.csv + b1_vs.csv
"""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])
blk = pd.read_csv(f'{OUT}/b1_sonda_blocos.csv')
it = pd.read_csv(f'{OUT}/b1_iters.csv')

rows = []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    son = [e for e in evs if e['rec'] == 'sonda']
    D, M = hdr['D'], hdr['M']
    real = pd.read_parquet(base + '__real.parquet').sort_values('fe_index')
    pop = pd.read_parquet(base + '__pop.parquet')
    g1 = pop[pop.geracao == pop.geracao.min()]
    doe_ids = set(real[real.fase == 'init'].solution_id.tolist())
    gen1_eq_doe = set(g1.solution_id.tolist()) == doe_ids
    nf1 = [e.get('n_front1') for e in ge]
    hp = [e.get('modelo_hp') for e in ge if isinstance(e.get('modelo_hp'), dict)]
    b = blk[blk.problema == p].sort_values('bloco')
    rows.append(dict(problema=p, D=D, M=M,
                     n_treino_min=int(it[it.problema == p].n_treino.min()),
                     n_treino_max=int(it[it.problema == p].n_treino.max()),
                     cap=int(it[it.problema == p].cap.iloc[0]),
                     gen1_eq_doe=gen1_eq_doe, pop_g1=len(g1),
                     nf1_1=nf1[0], nf1_last=nf1[-1], nf1_max=max(nf1),
                     ftm_son_min=min(s['fe_treino_max'] for s in son),
                     ftm_son_max=max(s['fe_treino_max'] for s in son),
                     hp_keys=';'.join(sorted(hp[0].keys())) if hp else '',
                     hp_n=len(hp),
                     wape_1=float(b.wape.iloc[0]), wape_last=float(b.wape.iloc[-1]),
                     dwape=float((b.wape.iloc[-1] - b.wape.iloc[0]) / max(b.wape.iloc[0], 1e-30)),
                     corr_1=float(b['corr'].iloc[0]), corr_last=float(b['corr'].iloc[-1]),
                     cob_1=float(b.cobertura.iloc[0]), cob_last=float(b.cobertura.iloc[-1]),
                     cob_min=float(b.cobertura.min()), n_blocos=len(b),
                     sig_med_1=float(b.sigma_med.iloc[0]), sig_med_last=float(b.sigma_med.iloc[-1]),
                     ))
fd = pd.DataFrame(rows)
fd.to_csv(f'{OUT}/b1_final.csv', index=False)
print(fd.to_string())
print()
print('n_treino satura no cap em', int((fd.n_treino_max == fd.cap).sum()), '/23 (excecao: DTLZ1)')
print('gen1 == DoE em', int(fd.gen1_eq_doe.sum()), '/23')
print('dWAPE mediano', round(float(fd.dwape.median()), 4), 'piora em', int((fd.dwape > 0).sum()), '/23')
print('cobertura 1o', fd.cob_1.median(), '-> ultimo', fd.cob_last.median(),
      '| <0,95 no ultimo em', int((fd.cob_last < 0.95).sum()), '/23')
print('modelo_hp keys:', fd.hp_keys.unique())

# --- cabeca-a-cabeca ---
met = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
main = met[met.exp == 'main']
vs = []
for p in probs:
    s = main[main.problema == p]
    d = {'problema': p}
    for a in ['b1', 'b3', 'nsga2', 'nsga3', 'moead', 'smsemoa', 'c262', 'e7']:
        r = s[s.alg == a]
        d[a] = float(r.igd_plus.iloc[0]) if len(r) else np.nan
        d[a + '_hv'] = float(r.hv.iloc[0]) if len(r) else np.nan
    vs.append(d)
vd = pd.DataFrame(vs)
vd['b1_vs_b3'] = vd.b1 / vd.b3
vd['b1_vs_nsga2'] = vd.b1 / vd.nsga2
vd.to_csv(f'{OUT}/b1_vs.csv', index=False)
print()
print(vd[['problema', 'b1', 'b3', 'b1_vs_b3', 'nsga2', 'b1_vs_nsga2']].to_string())
print('b1 vence b3 em', int((vd.b1_vs_b3 < 1).sum()), '/', int(vd.b1_vs_b3.notna().sum()),
      'razao mediana', round(float(vd.b1_vs_b3.median()), 3))
print('b1 vence nsga2 em', int((vd.b1_vs_nsga2 < 1).sum()), '/', int(vd.b1_vs_nsga2.notna().sum()))
