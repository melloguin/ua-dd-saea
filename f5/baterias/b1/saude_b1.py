"""Bateria b1 - parte 6: saude em escala (Classe B).
Metricas oficiais F5.2c x pisos, trajetorias de 20 checkpoints (violacoes de
monotonicidade), rank entre os algoritmos do main, maquina real (F5.2d).
Saida: b1_saude.csv + b1_trajetorias.csv
"""
import json, os, glob
import numpy as np, pandas as pd

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/b1'
PISOS = ['nsga2', 'nsga3', 'moead', 'smsemoa']

met = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
print('colunas metricas:', list(met.columns))
main = met[met.exp == 'main'] if 'exp' in met.columns else met
tempo = pd.read_csv(f'{F5}/tempo_f52d.csv')
probs = sorted([p for p in os.listdir('/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1')
                if not p.startswith(('_', '.')) and p != 'WFG1'])

key_alg = 'alg' if 'alg' in main.columns else 'algoritmo'
key_pb = 'problema'
rows = []
for p in probs:
    sub = main[(main[key_pb] == p)]
    b1 = sub[sub[key_alg] == 'b1']
    if not len(b1):
        print('SEM METRICA', p); continue
    b1 = b1.iloc[0]
    pis = sub[sub[key_alg].isin(PISOS)]
    best_p = pis.loc[pis['igd_plus'].idxmin()] if len(pis) else None
    # rank entre TODOS os algs do main naquele problema
    r = sub.sort_values('igd_plus').reset_index(drop=True)
    rank = int(r.index[r[key_alg] == 'b1'][0]) + 1
    tm = tempo[(tempo[key_alg] == 'b1') & (tempo[key_pb] == p)] if key_alg in tempo.columns else None
    maq = tm.iloc[0]['maquina'] if tm is not None and len(tm) and 'maquina' in tm.columns else None
    rows.append(dict(problema=p, igd_plus=b1['igd_plus'], hv=b1.get('hv'), igd=b1.get('igd'),
                     gd=b1.get('gd'), spacing=b1.get('spacing'), n_nd=b1.get('n_nd'),
                     piso_best=best_p[key_alg] if best_p is not None else None,
                     piso_igd=best_p['igd_plus'] if best_p is not None else np.nan,
                     piso_hv=best_p.get('hv') if best_p is not None else np.nan,
                     razao=b1['igd_plus'] / best_p['igd_plus'] if best_p is not None else np.nan,
                     rank=rank, n_algs=len(r), maquina=maq,
                     hv_b1=b1.get('hv')))

sd = pd.DataFrame(rows)
sd.to_csv(f'{OUT}/b1_saude.csv', index=False)
print(sd.to_string())
print()
print('bate o melhor piso em', int((sd.razao < 1).sum()), '/', len(sd))
print('rank medio', sd['rank'].mean(), 'de', sd.n_algs.max())
print('maquinas:', sd.maquina.value_counts().to_dict())

# --- trajetorias ---
tr = []
for p in probs:
    f = f'{F5}/trajetorias/main_b1_{p}_42.json'
    if not os.path.exists(f):
        cand = glob.glob(f'{F5}/trajetorias/*b1_{p}_42.json')
        f = cand[0] if cand else None
    if not f:
        print('SEM TRAJ', p); continue
    j = json.load(open(f))
    ig = np.array([c['igd_plus'] for c in j], float)
    hv = np.array([c['hv'] for c in j], float)
    fes = [c['fe'] for c in j]
    d = np.diff(ig)
    dh = np.diff(hv) if len(hv) > 1 else np.array([])
    tr.append(dict(problema=p, n_ck=len(ig), viol_igd=int((d > 1e-12).sum()),
                   n_trans=len(d), ganho=float(ig[0] / max(ig[-1], 1e-30)),
                   viol_hv=int((dh < -1e-12).sum()), igd_1=float(ig[0]), igd_last=float(ig[-1]),
                   hv_1=float(hv[0]) if len(hv) else np.nan, hv_last=float(hv[-1]) if len(hv) else np.nan,
                   fe_1=fes[0], fe_last=fes[-1]))
td = pd.DataFrame(tr); td.to_csv(f'{OUT}/b1_trajetorias.csv', index=False)
print()
print(td.to_string())
print('violacoes IGD+', td.viol_igd.sum(), 'em', td.n_trans.sum(), 'transicoes; HV quedas', td.viol_hv.sum())
print('ganho mediano', td.ganho.median(), 'max', td.ganho.max())
