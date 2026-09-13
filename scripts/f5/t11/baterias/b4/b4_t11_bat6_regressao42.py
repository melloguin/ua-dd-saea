#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 6: regressao contra a MESMA celula da rodada-42
(main/b4/MMF1/42) + front1 sob a lossiness float32 (R4#11). READ-ONLY."""
import json, sys, hashlib
import numpy as np, pandas as pd
import pyarrow.parquet as pq

T11 = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
R42 = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4/MMF1/42/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}

def load(P):
    man = json.load(open(P + '.manifest.json'))
    L = [json.loads(l) for l in open(P + '.jsonl')]
    d1 = pq.read_table(P + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
    d2 = pq.read_table(P + '__pop.parquet').to_pandas()
    d3 = pq.read_table(P + '__surrogate.parquet').to_pandas()
    return man, L, d1, d2, d3

ma, La, a1, a2, a3 = load(T11)
mb, Lb, b1, b2, b3 = load(R42)
cols = ['solution_id', 'x0', 'x1', 'f0', 'f1', 'fe_index']
R['1_identica'] = bool(a1[cols].equals(b1[cols]))
R['1_maxdX'] = float(np.abs(a1[['x0', 'x1']].values - b1[['x0', 'x1']].values).max()) if len(a1) == len(b1) else None
R['1_maxdF'] = float(np.abs(a1[['f0', 'f1']].values - b1[['f0', 'f1']].values).max()) if len(a1) == len(b1) else None
R['1_n'] = (len(a1), len(b1))
R['manifest'] = dict(
    n_ger=(ma['n_geracoes'], mb['n_geracoes']), fe=(ma['fe_final'], mb['fe_final']),
    cache=(ma['cache_hits'], mb['cache_hits']), doe=(ma['doe_hash'] == mb['doe_hash']),
    repo=(ma.get('repo_hash'), mb.get('repo_hash')),
    algo=(ma['algo_version'], mb['algo_version']),
    matlab=(ma['env'].get('matlab'), mb['env'].get('matlab')),
    campanha=(ma.get('campanha_id'), mb.get('campanha_id')))
ga = pd.DataFrame([{k: v for k, v in g.items() if not isinstance(v, (dict, list))} for g in La if g['rec'] == 'b4_gen'])
gb = pd.DataFrame([{k: v for k, v in g.items() if not isinstance(v, (dict, list))} for g in Lb if g['rec'] == 'b4_gen'])
R['gen_events'] = (len(ga), len(gb))
comuns = [c for c in ('geracao', 'fe', 'arquivo', 'p0', 'p1', 'rr', 'tr', 'ramo', 'lote', 'n_treino',
                      'n_acumulado', 'fe_treino_max', 'L_sel') if c in ga.columns and c in gb.columns]
R['gen_colunas_comparadas'] = comuns
if len(ga) == len(gb):
    R['gen_iguais'] = {c: int((ga[c].values == gb[c].values).sum()) for c in comuns}
    R['gen_n'] = len(ga)
    for c in ('p0', 'p1', 'rr', 'tr'):
        R['gen_maxdiff_' + c] = float(np.abs(ga[c].values - gb[c].values).max())
R['campos_novos_no_T11'] = sorted(set().union(*[set(g) for g in La if g['rec'] == 'b4_gen']) -
                                  set().union(*[set(g) for g in Lb if g['rec'] == 'b4_gen']))
R['campos_perdidos'] = sorted(set().union(*[set(g) for g in Lb if g['rec'] == 'b4_gen']) -
                              set().union(*[set(g) for g in La if g['rec'] == 'b4_gen']))
R['sigma_dict_chaves_T11'] = sorted(ma.get('sigma_dict', {}).keys())
R['sigma_dict_chaves_42'] = sorted(mb.get('sigma_dict', {}).keys())
R['regimes3_T11'] = a3.regime.value_counts().to_dict()
R['regimes3_42'] = b3.regime.value_counts().to_dict()
R['recs_T11'] = pd.Series([x['rec'] for x in La]).value_counts().to_dict()
R['recs_42'] = pd.Series([x['rec'] for x in Lb]).value_counts().to_dict()

# ---------- front1 sob lossiness float32 (R4#11) ----------
F1 = a1[['f0', 'f1']].values.astype(np.float64)
sid2row = {int(s): i for i, s in enumerate(a1.solution_id.values)}
arq = {int(g): a2[a2.geracao == g].solution_id.values.astype(int) for g in a2.geracao.unique()}
gens = {g['geracao']: g for g in La if g['rec'] == 'b4_gen'}
def nd_count(F, modo):
    n = len(F); nd = np.ones(n, bool)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            if modo == 'lo':   # domina se <= em tudo (empate conta como dominacao) -> menos ND
                dom = (F[j] <= F[i]).all()
            elif modo == 'std':
                dom = (F[j] <= F[i]).all() and (F[j] < F[i]).any()
            else:              # 'hi': domina so se < em tudo -> mais ND
                dom = (F[j] < F[i]).all()
            if dom: nd[i] = False; break
    return int(nd.sum())
rows = []
for g, ev in sorted(gens.items()):
    F = F1[[sid2row[s] for s in arq[g]]]
    rows.append(dict(geracao=g, lo=nd_count(F, 'lo'), std=nd_count(F, 'std'),
                     hi=nd_count(F, 'hi'), log=ev['n_front1']))
Nf = pd.DataFrame(rows); Nf.to_csv(OUT + 'b4_t11_front1_sanduiche.csv', index=False)
R['front1_sanduiche'] = int(((Nf.lo <= Nf.log) & (Nf.log <= Nf.hi)).sum()), len(Nf)
R['front1_std_exato'] = int((Nf['std'] == Nf.log).sum()), len(Nf)
R['front1_largura_media'] = float((Nf.hi - Nf.lo).mean())
print(json.dumps(R, indent=1, default=str))
