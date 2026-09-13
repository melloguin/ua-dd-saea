#!/usr/bin/env python
"""B4 - Bateria 6: camada ② (arquivo append-only), timing ④, fe_treino_max,
infills (U11-analogo), trajetorias 20-checkpoints, posicao vs pisos, join float32.
"""
import json, os, glob
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = REPO + '/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])
pd.set_option('display.width', 260)

rows = []
inf_all = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    man = json.load(open(base + '.manifest.json'))
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    g = pd.DataFrame([{k: v for k, v in r.items() if k not in ('modelo_hp', 'ref_ids', 'f_best')} for r in gens])

    # ② == arquivo no INICIO da geracao?
    sz = pop.groupby('geracao').size()
    a2 = g['geracao'].map(sz)
    b2_eq_ntreino = int((a2 == g['n_treino']).sum())
    # incremento de ② == lote(g-1)?
    dsz = sz.diff().dropna()
    lote_prev = g.set_index('geracao')['lote'].reindex(dsz.index - 1).to_numpy()
    inc_ok = int((dsz.to_numpy() == lote_prev).sum())
    dup2 = int(pop.duplicated(['geracao', 'solution_id']).sum())

    # ④ timing: 1 fit por geracao, ordem, invariantes
    t1 = int(((tim.tempo_fit_s + tim.tempo_busca_s) <= tim.tempo_geracao_s + 1e-6).sum())
    fit_pos = int((tim.tempo_fit_s > 0).sum())
    t_sum = float(tim.tempo_geracao_s.sum())
    t5 = float(man['timing']['tempo_total_s'])

    # fit_series do manifesto == ④
    fs = pd.DataFrame(man['fit_series'])
    fs_ok = int((fs.n_acumulado.to_numpy() == tim.n_acumulado.to_numpy()).sum()) if len(fs) == len(tim) else -1

    # fe_treino_max
    ftm = g.fe_treino_max.to_numpy()
    nt = g.n_treino.to_numpy(); nac = g.n_acumulado.to_numpy()
    ftm_lt_nt = int((ftm < nt).sum())
    ftm_ge_nac = int((ftm >= nac).sum())

    # infills: acerto do classificador
    inf = pd.read_pickle(f'{OUT}/infills_{prob}.pkl')
    inf_all.append(inf)

    rows.append(dict(problema=prob, n_gen=len(g), b2_eq_ntreino=b2_eq_ntreino, inc_ok=inc_ok,
                     n_grupos2=int(pop.geracao.nunique()), dup2=dup2,
                     t1=t1, fit_pos=fit_pos, t4_sum=round(t_sum, 2), t5=round(t5, 2),
                     razao_t4_t5=round(t_sum / t5, 4), fs_ok=fs_ok,
                     ftm_lt_nt=ftm_lt_nt, ftm_ge_nac=ftm_ge_nac,
                     ftm_eq_nt_menos1=int((ftm == nt - 1).sum())))
    print('ok', prob)

C = pd.DataFrame(rows)
C.to_csv(f'{OUT}/b4_saude_camadas.csv', index=False)
print('\n=== CAMADAS ② ④ ===')
print(C.to_string())

I = pd.concat(inf_all, ignore_index=True)
I.to_csv(f'{OUT}/b4_infills.csv', index=False)
print('\n=== INFILLS (U11-analogo: rotulo verdadeiro do escolhido vs pred) ===')
print('total infills:', len(I))
print('acuracia global:', round(float((I.label_true == I.pred_bom).mean()), 4))
print('base rate (label_true) global:', round(float(I.label_true.mean()), 4))
print('precisao quando pred=bom:', round(float(I.loc[I.pred_bom, 'label_true'].mean()), 4),
      f'(n={int(I.pred_bom.sum())})')
print('base rate quando pred=ruim:', round(float(I.loc[~I.pred_bom, 'label_true'].mean()), 4),
      f'(n={int((~I.pred_bom).sum())})')
G = pd.read_pickle(f'{OUT}/b4_geracoes_enriq.pkl')
I2 = I.merge(G[['problema', 'geracao', 'ramo']], on=['problema', 'geracao'], how='left')
print('\npor ramo:')
print(I2.groupby('ramo').apply(lambda d: pd.Series({
    'n': len(d), 'frac_label_true': float(d.label_true.mean()),
    'frac_pred_bom': float(d.pred_bom.mean()), 'acc': float((d.label_true == d.pred_bom).mean()),
    'L_med': float(d.pred_confianca.median())}), include_groups=False).to_string())
print('\npor problema:')
print(I2.groupby('problema').apply(lambda d: pd.Series({
    'n': len(d), 'label_true': float(d.label_true.mean()), 'pred_bom': float(d.pred_bom.mean()),
    'acc': float((d.label_true == d.pred_bom).mean())}), include_groups=False).round(4).to_string())

# ---------- trajetorias ----------
print('\n=== TRAJETORIAS (20 checkpoints) ===')
tr_rows = []
for prob in probs:
    j = json.load(open(f'{REPO}/f5/trajetorias/main_b4_{prob}_42.json'))
    if isinstance(j, dict):
        ks = list(j.keys())
        serie = j.get('igd_plus') or j.get('trajetoria') or j
    else:
        serie = j
    if isinstance(serie, list) and serie and isinstance(serie[0], dict):
        df = pd.DataFrame(serie)
        col = 'igd_plus' if 'igd_plus' in df.columns else df.columns[-1]
        v = df[col].to_numpy(float)
    else:
        v = np.array(serie, float)
    d = np.diff(v)
    tr_rows.append(dict(problema=prob, n=len(v), viol=int((d > 1e-12).sum()),
                        primeiro=float(v[0]), ultimo=float(v[-1]), razao=float(v[-1] / v[0])))
T = pd.DataFrame(tr_rows)
T.to_csv(f'{OUT}/b4_trajetorias.csv', index=False)
print(T.to_string())
print('TOTAL violacoes:', int(T.viol.sum()), 'de', int((T.n - 1).sum()), 'transicoes')

# ---------- posicao vs pisos ----------
M = pd.read_csv(f'{REPO}/f5/metricas_finais_f52c.csv')
M = M[M.exp == 'main']
piso = M[M.alg.isin(['moead', 'nsga2', 'nsga3', 'smsemoa'])].groupby('problema').igd_plus.min()
b4 = M[M.alg == 'b4'].set_index('problema').igd_plus
sa = M.pivot_table(index='problema', columns='alg', values='igd_plus')
rank = sa.rank(axis=1)['b4']
cmp = pd.DataFrame({'b4': b4, 'melhor_piso': piso, 'razao': b4 / piso, 'rank_b4': rank})
cmp['bate_piso'] = cmp.razao < 1
cmp['dentro_ruido'] = (~cmp.bate_piso) & (cmp.razao <= 1.5898)
cmp.to_csv(f'{OUT}/b4_vs_pisos.csv')
print('\n=== IGD+ vs melhor piso ===')
print(cmp.round(4).to_string())
print('bate o melhor piso:', int(cmp.bate_piso.sum()), '/25   dentro do piso de ruido O-18 (<=1,5898x):',
      int(cmp.dentro_ruido.sum()), '   claramente abaixo:', int((~cmp.bate_piso & ~cmp.dentro_ruido).sum()))
print('rank medio b4 (17 algs main):', round(float(rank.mean()), 2))
