#!/usr/bin/env python
"""BATERIA 6 — fechamento: μ/σ NULL, campos declarativos da ③, regime-NaN, score do ⑥ x ③,
dist_min_arquivo / n_front1 (diversidade), canônica WFG corrigida, granularidade do Error."""
import os, json, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c217'
F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
OUT = f'{F5}/baterias/c217'
G = pd.read_pickle(f'{OUT}/c217_identidades.pkl')
I = pd.read_csv(f'{OUT}/c217_infills.csv')

print('=== 1. ③ — campos declarativos, μ/σ NULL, regimes ===')
rows = []
for p in sorted(os.listdir(ROOT)):
    d = pq.read_table(f'{ROOT}/{p}/42/exp_main_c217_{p}_42__surrogate.parquet').to_pandas()
    mu = [c for c in d.columns if c.startswith('mu_')]; sg = [c for c in d.columns if c.startswith('sigma_')]
    rows.append(dict(problema=p, n=len(d),
                     mu_null=float(d[mu].isna().all(axis=1).mean()), sg_null=float(d[sg].isna().all(axis=1).mean()),
                     pred_tipo=json.dumps(sorted(d.pred_tipo.dropna().unique().tolist())),
                     pred_classe_null=float(d.pred_classe.isna().mean()),
                     modelo_flag=json.dumps(sorted(d.modelo_flag.dropna().unique().tolist())),
                     espaco=json.dumps(sorted(d.espaco_modelo.dropna().unique().tolist())),
                     transf=json.dumps(sorted(d.transf_tipo.dropna().unique().tolist())),
                     score_uniq=json.dumps(sorted(d.pred_score.dropna().unique().tolist())),
                     rsid_null_sonda=float(d[d.regime == 'sonda'].real_solution_id.isna().mean()),
                     rsid_null_online=float(d[d.regime == 'online'].real_solution_id.isna().mean()),
                     regimes=json.dumps(sorted(d.regime.unique().tolist()))))
S = pd.DataFrame(rows); S.to_csv(f'{OUT}/c217_camada3_campos.csv', index=False)
print(S.to_string())
print('μ 100% NULL em', int((S.mu_null == 1).sum()), '/25 ; σ 100% NULL em', int((S.sg_null == 1).sum()), '/25')
print('pred_classe 100% NULL em', int((S.pred_classe_null == 1).sum()), '/25')
print('valores distintos de pred_score no conjunto:', set(sum([json.loads(x) for x in S.score_uniq], [])))

print()
print('=== 2. regime-NaN (DEF-L6) e vocabulário de motivos ===')
print('motivos com "NaN":', int(G.motivo.str.contains('NaN', case=False).sum()), '/', len(G))
print('motivos com "contradic":', int(G.motivo.str.contains('contradic').sum()))
print('n_contradicoes==Dvalid (contradição total):', int((G.n_contradicoes == G.Dvalid).sum()), '/', len(G))
print('  por célula:', G[G.n_contradicoes == G.Dvalid].problema.value_counts().to_dict())

print()
print('=== 3. score do ⑥ x pred_score da ③ ===')
sc = I.groupby(['problema', 'geracao']).pred_score.agg(['min', 'max', 'nunique']).reset_index()
mm = sc.merge(G[['problema', 'geracao', 'score', 'estado', 'lote']], on=['problema', 'geracao'])
print('⑥.score == pred_score único da geração:', int(((mm['min'] == mm.score) & (mm['max'] == mm.score)).sum()), '/', len(mm))
print('nunique==1 em', int((mm['nunique'] == 1).sum()), '/', len(mm))

print()
print('=== 4. DIVERSIDADE: dist_min_arquivo e n_front1 ===')
def q14(t, col):
    t = t.sort_values('geracao'); k = max(1, len(t) // 4)
    return t[col].iloc[:k].mean(), t[col].iloc[-k:].mean()
G['dmin'] = G.dist_min_arquivo.map(lambda v: float(np.mean(v)) if isinstance(v, (list, np.ndarray)) else float(v))
G['dmin_is_list'] = G.dist_min_arquivo.map(lambda v: isinstance(v, (list, np.ndarray)))
print('dist_min_arquivo é LISTA em', int(G.dmin_is_list.sum()), 'gerações (=lote>1); escalar nas demais')
print('  lista <-> estado 1/2:', int((G.dmin_is_list == G.estado.isin([1,2])).sum()), '/', len(G))
rows = []
for p, t in G.groupby('problema'):
    d1, d4 = q14(t, 'dmin'); f1, f4 = q14(t, 'n_front1')
    rows.append(dict(problema=p, dmin_q1=d1, dmin_q4=d4, dmin_med=t.dmin.median(),
                     front1_q1=f1, front1_q4=f4, front1_max=t.n_front1.max()))
DV = pd.DataFrame(rows); DV.to_csv(f'{OUT}/c217_diversidade.csv', index=False)
print(DV.to_string())
print('dist_min cai (q4<q1) em', int((DV.dmin_q4 < DV.dmin_q1).sum()), '/25')
print('n_front1 cresce em', int((DV.front1_q4 > DV.front1_q1).sum()), '/25')
# gated x aleatório na distância
Gg = G[G.estado.isin([1, 2])]; Gr = G[G.estado == 3]
print('dist_min_arquivo mediana: gated %.4f (n=%d) x aleatório %.4f (n=%d)' %
      (Gg.dmin.median(), len(Gg), Gr.dmin.median(), len(Gr)))

print()
print('=== 5. GRANULARIDADE do Error (p+ * |Dvalid| inteiro) por regime ===')
st = G[G.Dvalid == 6]
print('gerações |Dvalid|=6:', len(st), '| p_mais em múltiplos de 1/6:',
      int(np.isclose(st.p_mais * 6, np.round(st.p_mais * 6)).sum()))
print('valores de p_mais observados quando |Dvalid|=6:', sorted(st.p_mais.round(6).unique()))
print('gerações |Dvalid|=2 (D=2 ramp):', int((G.Dvalid == 2).sum()), 'valores:', sorted(G[G.Dvalid == 2].p_mais.unique()))
print('gerações |Dvalid| != 6:', int((G.Dvalid != 6).sum()), '(gen 1 + ramp)')
print('p_mais>delta possível só com k>=%.0f de 6 ->' % np.ceil(0.8 * 6), 'k=5 (0.8333) ou 6 (1.0)')

print()
print('=== 6. CANÔNICA WFG com o valor de WFG5 CORRIGIDO (1.1186e-1) ===')
M = pd.read_csv(f'{F5}/metricas_finais_f52c.csv'); main = M[M.exp == 'main']
ours = {k: float(main[(main.alg == 'c217') & (main.problema == k)].igd_plus.iloc[0])
        for k in ['WFG1', 'WFG2', 'WFG4', 'WFG5', 'WFG9']}
for nome, w5 in [('literal e-2', 1.1186e-2), ('corrigido e-1', 1.1186e-1)]:
    paper = {'WFG1': 1.1225, 'WFG2': 1.9643e-1, 'WFG4': 8.9525e-2, 'WFG5': w5, 'WFG9': 1.3327e-1}
    pp = sorted(paper, key=paper.get); oo = sorted(ours, key=ours.get)
    from scipy.stats import spearmanr
    print(f'  {nome}: paper {pp} | nosso {oo} | idênticas {sum(1 for i,k in enumerate(pp) if oo[i]==k)}/5 | rho={spearmanr([paper[k] for k in paper],[ours[k] for k in paper]).statistic:.3f}')
print('  nossos IGD+:', {k: round(v, 4) for k, v in ours.items()})
