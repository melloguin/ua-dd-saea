#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 1: estrutura, camadas, guards, identidades do gate.
READ-ONLY. Escreve só nesta pasta."""
import json, hashlib, sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}

man = json.load(open(B + '.manifest.json'))
L = [json.loads(l) for l in open(B + '.jsonl')]
hdr = [l for l in L if l['rec'] == 'header'][0]
ftr = [l for l in L if l['rec'] == 'footer'][0]
gens = [l for l in L if l['rec'] == 'b4_gen']
sondas = [l for l in L if l['rec'] == 'sonda']
sestr = [l for l in L if l['rec'] == 'sonda_estratificada']
guards = [l for l in L if l['rec'] == 'guard']

D, M, maxfe = hdr['D'], hdr['M'], hdr['maxfe']
R['D'] = D; R['M'] = M
R['maxfe_esperado_31D-1'] = 31 * D - 1
R['maxfe_manifesto'] = man['maxfe']; R['fe_final'] = man['fe_final']
R['init_esperado_11D-1'] = 11 * D - 1

df1 = pq.read_table(B + '__real.parquet').to_pandas()
df2 = pq.read_table(B + '__pop.parquet').to_pandas()
df3 = pq.read_table(B + '__surrogate.parquet').to_pandas()
df4 = pq.read_table(B + '__timing.parquet').to_pandas()

# ---------- U1 orçamento ----------
R['U1_len1'] = len(df1)
R['U1_fe_index_denso'] = bool((np.sort(df1.fe_index.values) == np.arange(len(df1))).all())
R['U1_solution_id_denso'] = bool((np.sort(df1.solution_id.values) == np.arange(len(df1))).all())
R['U1_fe_final_eq_maxfe'] = bool(man['fe_final'] == man['maxfe'] == 31 * D - 1)

# ---------- U2 DoE ----------
n_init = int((df1.fase == 'init').sum())
R['U2_n_init'] = n_init
R['U2_n_init_ok'] = bool(n_init == 11 * D - 1)
doe_f = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/MMF1/doe_MMF1_42.parquet'
import os
if os.path.exists(doe_f):
    doe = pq.read_table(doe_f).to_pandas()
    xc = [c for c in doe.columns if c.startswith('x')]
    Xa = doe[xc].values[:n_init].astype(np.float32)
    Xb = df1.sort_values('fe_index')[['x%d' % i for i in range(D)]].values[:n_init].astype(np.float32)
    R['U2_maxdX_artefato'] = float(np.abs(Xa - Xb).max())
    sc = doe_f.replace('.parquet', '.manifest.json')
    if os.path.exists(sc):
        R['U2_doe_hash_sidecar'] = json.load(open(sc)).get('doe_hash')
    R['U2_doe_hash_manifesto'] = man['doe_hash']
else:
    R['U2_doe_arquivo'] = 'AUSENTE:' + doe_f
R['U2_cp_init'] = ftr.get('cp_init')

# ---------- ⑥ estrutura ----------
R['n_gen_events'] = len(gens)
R['n_geracoes_manifesto'] = man['n_geracoes']
R['fantasma'] = bool(man['n_geracoes'] == len(gens) + 1)
R['n_sonda_eventos'] = len(sondas)
R['n_sonda_estrat_eventos'] = len(sestr)
R['guards'] = pd.Series([g['name'] for g in guards]).value_counts().to_dict()
R['cache_hits_manifesto'] = man['cache_hits']
R['guard_cache_hit_fe1_sid0'] = bool(any(g['name'] == 'cache_hit' and g.get('fe') == 1 and g.get('solution_id') == 0 for g in guards))

G = pd.DataFrame([{k: v for k, v in g.items() if not isinstance(v, (dict, list))} for g in gens])
G['ref_ids'] = [g['ref_ids'] for g in gens]
G['n_refs'] = [g['n_refs'] for g in gens]
G['y_n'] = [g['y_treino_dist']['n'] for g in gens]
G['y_c1'] = [g['y_treino_dist']['classe_1'] for g in gens]
G['y_c0'] = [g['y_treino_dist']['classe_0'] for g in gens]
G['y_prev'] = [g['y_treino_dist']['prevalencia_classe_1'] for g in gens]
G['n_treino_fit'] = [g['modelo_hp']['n_treino_fit'] for g in gens]

# ---------- A4: K=6 e ref_ids REAIS ----------
R['A4_n_refs_eq6'] = int((G.n_refs == 6).sum()), len(G)
R['A4_len_ref_ids_eq6'] = int(sum(len(r) == 6 for r in G.ref_ids)), len(G)
R['A4_ref_ids_sentinela'] = int(sum(all(x == -1 for x in r) for r in G.ref_ids))
R['A4_ref_ids_negativos'] = int(sum(any(x < 0 for x in r) for r in G.ref_ids))
R['A4_ref_ids_dentro_arquivo'] = int(sum(max(r) < n for r, n in zip(G.ref_ids, G.n_treino))), len(G)
R['A4_ref_ids_distintos'] = int(sum(len(set(r)) == 6 for r in G.ref_ids)), len(G)
R['A4_n_conjuntos_distintos'] = len(set(tuple(r) for r in G.ref_ids))

# ---------- A7/A8: rr e tr ----------
G['rr_calc_ytreino'] = G.y_c1 / G.y_n
R['A7_rr_eq_y_prev'] = int((np.abs(G.rr - G.y_prev) < 1e-12).sum()), len(G)
R['A7_rr_eq_c1_sobre_ntreino'] = int((np.abs(G.rr - G.rr_calc_ytreino) < 1e-12).sum()), len(G)
R['A7_y_n_eq_n_treino'] = int((G.y_n == G.n_treino).sum()), len(G)
R['A8_tr'] = int((np.abs(G.tr - 0.5 * np.minimum(G.rr, 1 - G.rr)) < 1e-15).sum()), len(G)
R['A7_rr_mediana'] = float(G.rr.median()); R['A8_tr_max'] = float(G.tr.max())

# ---------- A9: DataPartition ----------
D1 = G.y_c1.values; D0 = G.y_c0.values
cand = {
    'ceil34_estrat': np.ceil(0.75 * D0) + np.ceil(0.75 * D1),
    'floor34_estrat': np.floor(0.75 * D0) + np.floor(0.75 * D1),
    'round34_total': np.round(0.75 * (D0 + D1)),
    'ceil34_total': np.ceil(0.75 * (D0 + D1)),
}
R['A9'] = {k: (int((v == G.n_acumulado.values).sum()), len(G)) for k, v in cand.items()}
R['A9_n_acum_eq_n_treino_fit'] = int((G.n_acumulado == G.n_treino_fit).sum()), len(G)

# ---------- A13: o gate ----------
p0, p1, tr, ramo = G.p0.values, G.p1.values, G.tr.values, G.ramo.values
forms = {
    'paper_puro(p0<tr | (p1<tr & p0<1-tr))': (p0 < tr) | ((p1 < tr) & (p0 < 1 - tr)),
    'com_0.4(p0<0.4 | (p1<tr & p0<1-tr))': (p0 < 0.4) | ((p1 < tr) & (p0 < 1 - tr)),
    'minima(p0<0.4 | p1<tr)': (p0 < 0.4) | (p1 < tr),
}
R['A13'] = {k: (int(((v).astype(int) == (ramo == 1).astype(int)).sum()), len(G)) for k, v in forms.items()}
R['A13_ramos'] = pd.Series(ramo).value_counts().to_dict()
R['A13_p0_min_ramo4'] = float(p0[ramo == 4].min()) if (ramo == 4).any() else None
R['A13_p0_max_ramo1'] = float(p0[ramo == 1].max()) if (ramo == 1).any() else None
R['A13_p1_max'] = float(p1.max()); R['A13_1mtr_min'] = float((1 - tr).min())
R['A13_p0_nan'] = int(np.isnan(p0).sum()); R['A13_p1_nan'] = int(np.isnan(p1).sum())

# ---------- A16/A17: lote por ramo, stalls ----------
R['A16_lote1_em_ramo4'] = int((G.lote[G.ramo == 4] == 1).sum()), int((G.ramo == 4).sum())
R['A16_lote_ramo1_dist'] = G.lote[G.ramo == 1].value_counts().sort_index().to_dict()
R['A17_stalls_lote0'] = int((G.lote == 0).sum())
R['A17_stalls_guard'] = sum(1 for g in guards if g['name'] == 'stall_0fe')
R['A17_stalls_ramo1'] = int(((G.lote == 0) & (G.ramo == 1)).sum())
R['A18_lote_max_ramo1'] = int(G.lote[G.ramo == 1].max()) if (G.ramo == 1).any() else None
R['soma_lote'] = int(G.lote.sum())

# ---------- A24: ② arquivo ----------
g2 = df2.groupby('geracao').size()
R['A24_n_grupos_pop'] = int(len(g2))
R['A24_pop_eq_ntreino'] = int((g2.reindex(G.geracao).values == G.n_treino.values).sum()), len(G)
dd = np.diff(g2.values); ll = G.lote.values[:len(dd)]
R['A24_delta_pop_eq_lote'] = int((dd == ll).sum()), len(dd)
R['A24_pop_g1'] = int(g2.iloc[0]); R['A24_pop_fim'] = int(g2.iloc[-1])
R['A24_dup_intra'] = int(df2.groupby('geracao').solution_id.apply(lambda s: s.duplicated().sum()).sum())

# ---------- A23: fe_treino_max não-monotônico ----------
d = np.diff(G.fe_treino_max.values)
R['A23_quedas'] = int((d < 0).sum()); R['A23_soma_quedas'] = int(-d[d < 0].sum()) if (d < 0).any() else 0
R['A23_n_acum_lt_n_treino'] = int((G.n_acumulado < G.n_treino).sum()), len(G)

# ---------- A26: timing ----------
R['A26_fit_busca_le_ger'] = int((G.tempo_fit_s + G.tempo_busca_s <= G.tempo_geracao_s).sum()), len(G)
R['A26_fit_series_eq_4'] = int((np.abs(np.array([f['tempo_fit_s'] for f in man['fit_series']]) - df4.tempo_fit_s.values) < 1e-6).sum()), len(df4)
R['A26_perfil'] = {k: float(man['timing'][k] / man['timing']['tempo_total_s']) for k in
                   ['tempo_fit_surrogate_s', 'tempo_busca_s', 'tempo_aval_real_s', 'tempo_pred_sonda_s']}
R['I3_tempo_aval_real_s'] = float(man['timing']['tempo_aval_real_s'])

# ---------- A21: sem cabeça de valor ----------
R['A21_mu_null'] = int(df3.mu_0.isna().sum()), len(df3)
R['A21_sigma_null'] = int(df3.sigma_0.isna().sum()), len(df3)
R['A21_pred_score_null'] = int(df3.pred_score.isna().sum()), len(df3)
R['A21_pred_tipo'] = df3.pred_tipo.value_counts().to_dict()
R['A21_modelo_flag'] = df3.modelo_flag.value_counts().to_dict()
cons = ((df3.pred_classe == 'bom') == (df3.pred_confianca >= 0.5))
R['A21_classe_eq_L05'] = int(cons.sum()), len(df3)
R['A21_min_L_bom'] = float(df3.pred_confianca[df3.pred_classe == 'bom'].min())
R['A21_max_L_ruim'] = float(df3.pred_confianca[df3.pred_classe != 'bom'].max())

# ---------- regimes da ③ ----------
R['regimes3'] = df3.regime.value_counts().to_dict()

# ---------- U10 aritmética ----------
n_online = int((df3.regime == 'online').sum())
R['n_linhas_online_3'] = n_online
R['aritm_1'] = dict(len1=len(df1), init=n_init, soma_lote=int(G.lote.sum()),
                    cache_hits=man['cache_hits'],
                    check=int(n_init + G.lote.sum() - (man['cache_hits'] - 1)))

G.drop(columns=['ref_ids']).to_csv(OUT + 'b4_t11_geracoes.csv', index=False)
pd.DataFrame({'geracao': G.geracao, 'ref_ids': [json.dumps(r) for r in G.ref_ids]}).to_csv(OUT + 'b4_t11_refids.csv', index=False)

print(json.dumps(R, indent=1, default=str))
