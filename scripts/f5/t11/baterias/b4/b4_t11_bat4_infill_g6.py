#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 4: infills por ramo, cadencia da sonda, contra-hipoteses
p0/p1, e NAO-PERTURBACAO (g6_com x g6_sem). READ-ONLY."""
import json, sys, hashlib
import numpy as np, pandas as pd
import pyarrow.parquet as pq
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
CO = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_com/experiments/main/b4/exp_main_b4_MMF1_42'
SE = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/g6_sem/experiments/main/b4/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}

L = [json.loads(l) for l in open(SM + '.jsonl')]
gens = {g['geracao']: g for g in L if g['rec'] == 'b4_gen'}
G = pd.DataFrame([{k: v for k, v in g.items() if not isinstance(v, (dict, list))} for g in gens.values()])
df1 = pq.read_table(SM + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
df2 = pq.read_table(SM + '__pop.parquet').to_pandas()
df3 = pq.read_table(SM + '__surrogate.parquet').to_pandas()
F1 = df1[['f0', 'f1']].values.astype(np.float64)
sid2row = {int(s): i for i, s in enumerate(df1.solution_id.values)}
arq = {int(g): df2[df2.geracao == g].solution_id.values.astype(int) for g in df2.geracao.unique()}

# ---------- contra-hipoteses p0/p1 no gate ----------
p0, p1, tr, ramo = G.p0.values, G.p1.values, G.tr.values, G.ramo.values
alt = {
    'H1 p0=catII (declarado): p0<0.4 | (p1<tr & p0<1-tr)': (p0 < 0.4) | ((p1 < tr) & (p0 < 1 - tr)),
    'H2 invertido:            p1<0.4 | (p0<tr & p1<1-tr)': (p1 < 0.4) | ((p0 < tr) & (p1 < 1 - tr)),
}
R['gate_contra_hipoteses'] = {k: (int(((v).astype(int) == (ramo == 1).astype(int)).sum()), len(G)) for k, v in alt.items()}
R['p0_media'] = float(np.mean(p0)); R['p1_media'] = float(np.mean(p1))
R['rr_mediana'] = float(np.median(G.rr))
R['margem_do_0.4'] = dict(max_p0_ramo1=float(p0[ramo == 1].max()), min_p0_ramo4=float(p0[ramo == 4].min()),
                          tr_max=float(tr.max()))
R['gens_ramo1'] = G.geracao[ramo == 1].tolist()
R['lote_ramo1'] = G.lote[ramo == 1].tolist()

# ---------- infills: rotulo verdadeiro x predicao ----------
on = df3[df3.regime == 'online'].copy()
R['n_online'] = len(on)
rows = []
for _, r in on.iterrows():
    g = int(r.geracao); sid = int(r.real_solution_id)
    ev = gens[g]; Rref = F1[[sid2row[int(s)] for s in ev['ref_ids']]]
    f = F1[sid2row[sid]]
    ytrue = all((f <= Rref[j]).any() for j in range(6))
    rows.append(dict(geracao=g, sid=sid, ramo=ev['ramo'], L=float(r.pred_confianca),
                     pred=(r.pred_classe == 'bom'), ytrue=bool(ytrue)))
I = pd.DataFrame(rows); I.to_csv(OUT + 'b4_t11_infills.csv', index=False)
for rm in sorted(I.ramo.unique()):
    s = I[I.ramo == rm]
    R['infill_ramo%d' % rm] = dict(n=len(s), frac_catII_verdadeira=float(s.ytrue.mean()),
                                   acuracia=float((s.ytrue == s.pred).mean()),
                                   L_min=float(s.L.min()), L_max=float(s.L.max()))
R['infill_global'] = dict(n=len(I), frac_catII=float(I.ytrue.mean()), acc=float((I.ytrue == I.pred).mean()))
R['A14_L_gt_09_no_ramo1'] = int((I.L[I.ramo == 1] > 0.9).sum()), int((I.ramo == 1).sum())

# ---------- cadencia da sonda ----------
sd = sorted(int(x['geracao']) for x in L if x['rec'] == 'sonda')
se = sorted(int(x['geracao']) for x in L if x['rec'] == 'sonda_estratificada')
ng = max(gens)
esperado = [1] + [g for g in range(2, ng + 1) if g % 2 == 0]
R['cadencia'] = dict(sonda=sd, esperado_pares=esperado,
                     faltando=[g for g in esperado if g not in sd],
                     extra=[g for g in sd if g not in esperado],
                     motivos={m: sum(1 for x in L if x['rec'] == 'sonda' and x['motivo'] == m)
                              for m in set(x['motivo'] for x in L if x['rec'] == 'sonda')})
R['cadencia_estratificada'] = dict(n=len(se), gens=se, faltando_vs_sonda=[g for g in sd if g not in se])

# ---------- NAO-PERTURBACAO g6_com x g6_sem ----------
def h(df, cols):
    return hashlib.sha256(np.ascontiguousarray(df[cols].values).tobytes()).hexdigest()
a1 = pq.read_table(CO + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
b1 = pq.read_table(SE + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
cols = ['solution_id', 'x0', 'x1', 'f0', 'f1', 'fe_index']
R['g6'] = dict(n_com=len(a1), n_sem=len(b1),
               hash_com=h(a1, cols)[:16], hash_sem=h(b1, cols)[:16],
               identicas=bool(a1[cols].equals(b1[cols])),
               maxdX=float(np.abs(a1[['x0', 'x1']].values - b1[['x0', 'x1']].values).max()),
               maxdF=float(np.abs(a1[['f0', 'f1']].values - b1[['f0', 'f1']].values).max()))
mc = json.load(open(CO + '.manifest.json')); ms = json.load(open(SE + '.manifest.json'))
R['g6_manifesto'] = dict(sonda_desligada_com=mc['sonda']['desligada'], sonda_desligada_sem=ms['sonda']['desligada'],
                         n_blocos_com=mc['sonda']['n_blocos'], n_blocos_sem=ms['sonda']['n_blocos'],
                         fe_final_com=mc['fe_final'], fe_final_sem=ms['fe_final'],
                         n_ger_com=mc['n_geracoes'], n_ger_sem=ms['n_geracoes'],
                         cache_com=mc['cache_hits'], cache_sem=ms['cache_hits'])
c3 = pq.read_table(CO + '__surrogate.parquet').to_pandas(); s3 = pq.read_table(SE + '__surrogate.parquet').to_pandas()
R['g6_terceira'] = dict(regimes_com=c3.regime.value_counts().to_dict(), regimes_sem=s3.regime.value_counts().to_dict())
# o smoke e a mesma celula que o g6_com?
R['smoke_eq_g6com'] = bool(df1[cols].equals(a1[cols]))
# sigma_dict identico nos tres?
sm = json.load(open(SM + '.manifest.json'))
R['sigma_dict_igual_nos_3'] = bool(sm['sigma_dict'] == mc['sigma_dict'] == ms['sigma_dict'])
R['params_igual_nos_3'] = bool(sm['params'] == mc['params'] == ms['params'])

print(json.dumps(R, indent=1, default=str))
