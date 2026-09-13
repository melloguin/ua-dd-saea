#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 3: sanduiche float32 RIGOROSO (auto-comparacao exata)
sobre o ARQUIVO, para fechar y_treino_dist/rr com os ref_ids REAIS; + varredura de
leituras alternativas na regua Sobol (para auditar os numeros do sigma_dict). READ-ONLY."""
import json, sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src.problems import MMF1, evaluate_problem

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}
L = [json.loads(l) for l in open(B + '.jsonl')]
gens = {g['geracao']: g for g in L if g['rec'] == 'b4_gen'}
df1 = pq.read_table(B + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
df2 = pq.read_table(B + '__pop.parquet').to_pandas()
df3 = pq.read_table(B + '__surrogate.parquet').to_pandas()
F1 = df1[['f0', 'f1']].values.astype(np.float64)
sid2row = {int(s): i for i, s in enumerate(df1.solution_id.values)}
arq = {int(g): df2[df2.geracao == g].solution_id.values for g in df2.geracao.unique()}

# a ② e ordenada por solution_id crescente? posicional == solution_id?
same = [(g, bool((s == np.arange(len(s))).all())) for g, s in sorted(arq.items())]
R['0_pop_pos_eq_sid'] = int(sum(v for _, v in same)), len(same)
R['0_gen_primeira_divergencia'] = next((g for g, v in same if not v), None)

def sandwich(Fpts, sid_pts, Rrefs, sid_refs):
    """hi: <= em tudo. lo: < em tudo, EXCETO a auto-comparacao (mesmo solution_id),
    que e exata em qualquer precisao."""
    n = len(Fpts)
    hi = np.ones(n, bool); lo = np.ones(n, bool)
    for j in range(len(Rrefs)):
        hi &= (Fpts <= Rrefs[j]).any(axis=1)
        strict = (Fpts < Rrefs[j]).any(axis=1)
        selfrow = (sid_pts == sid_refs[j])
        lo &= (strict | selfrow)
    return hi, lo

rows = []
for g, ev in sorted(gens.items()):
    sids = arq[g].astype(int)
    Farq = F1[[sid2row[s] for s in sids]]
    ridx = np.array(ev['ref_ids'])
    for nome, sid_refs in (('posicional②', sids[ridx]), ('solution_id', ridx)):
        Rref = F1[[sid2row[int(s)] for s in sid_refs]]
        hi, lo = sandwich(Farq, sids, Rref, np.array(sid_refs, int))
        rows.append(dict(geracao=g, interp=nome, n1_hi=int(hi.sum()), n1_lo=int(lo.sum()),
                         n1_log=ev['y_treino_dist']['classe_1'], n=len(sids)))
T = pd.DataFrame(rows)
T['sanduiche'] = (T.n1_lo <= T.n1_log) & (T.n1_log <= T.n1_hi)
T['decidida'] = T.n1_lo == T.n1_hi
T['exato'] = T.n1_hi == T.n1_log
T.to_csv(OUT + 'b4_t11_rotulo_sanduiche.csv', index=False)
for nome in ('posicional②', 'solution_id'):
    s = T[T.interp == nome]
    R['1_' + nome] = dict(n=len(s), sanduiche=int(s.sanduiche.sum()),
                          decididas=int(s.decidida.sum()),
                          exato_nas_decididas=int((s.exato & s.decidida).sum()),
                          exato_total=int(s.exato.sum()),
                          largura_media=float((s.n1_hi - s.n1_lo).mean()))

# ---------- varredura de leituras na REGUA SOBOL (auditoria do sigma_dict) ----------
art = pq.read_table('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet').to_pandas().iloc[:2000]
Fa = art[['f0', 'f1']].values
S = df3[df3.regime == 'sonda']
def auc(y, c):
    y = np.asarray(y, bool)
    if y.all() or (~y).all(): return np.nan
    r = pd.Series(c).rank().values
    return (r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum())
leituras = {}
for g in sorted(S.geracao.unique()):
    blk = S[S.geracao == g]; conf = blk.pred_confianca.values.astype(float)
    p = blk.pred_classe.values == 'bom'
    ev = gens[int(g)]; sids = arq[int(g)].astype(int)
    Farq = F1[[sid2row[s] for s in sids]]
    Rref = F1[[sid2row[int(s)] for s in np.array(ev['ref_ids'])]]
    cands = {
        'A_DI18 (∀j ∃k: f_k<=R_jk)': np.array([all((Fa[i] <= Rref[j]).any() for j in range(6)) for i in range(len(Fa))]),
        'B_domina>=1ref (paper Alg.4)': np.array([any(((Fa[i] <= Rref[j]).all() and (Fa[i] < Rref[j]).any()) for j in range(6)) for i in range(len(Fa))]),
        'C_nao-dominado pelas 6 refs': np.array([all(not ((Rref[j] <= Fa[i]).all() and (Rref[j] < Fa[i]).any()) for j in range(6)) for i in range(len(Fa))]),
        'D_∃j ∃k: f_k<=R_jk': np.array([any((Fa[i] <= Rref[j]).any() for j in range(6)) for i in range(len(Fa))]),
        'E_∀j ∀k: f_k<=R_jk (domina todas)': np.array([all((Fa[i] <= Rref[j]).all() for j in range(6)) for i in range(len(Fa))]),
        'F_nao-dominado pelo ARQUIVO': np.array([not any(((Farq[j] <= Fa[i]).all() and (Farq[j] < Fa[i]).any()) for j in range(len(Farq))) for i in range(len(Fa))]),
        'G_∀a∈Arc ∃k: f_k<=a_k': np.array([all((Fa[i] <= Farq[j]).any() for j in range(len(Farq))) for i in range(len(Fa))]),
    }
    for k, y in cands.items():
        leituras.setdefault(k, []).append(dict(geracao=int(g), prev=float(y.mean()),
                                               acc=float((y == p).mean()), auc=auc(y, conf)))
R['2_leituras_sobol'] = {k: dict(prev=float(pd.DataFrame(v).prev.mean()),
                                 acc=float(pd.DataFrame(v).acc.mean()),
                                 auc=float(pd.DataFrame(v).auc.mean())) for k, v in leituras.items()}
pd.concat([pd.DataFrame(v).assign(leitura=k) for k, v in leituras.items()]).to_csv(OUT + 'b4_t11_leituras_sobol.csv', index=False)
print(json.dumps(R, indent=1, default=str))
