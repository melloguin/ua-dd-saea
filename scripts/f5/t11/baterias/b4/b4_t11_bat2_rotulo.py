#!/usr/bin/env python
"""b4 / T11 SMOKE — bateria 2: a REGRA_DO_ROTULO declarada.
(i) fecha rr/y_treino_dist recomputando o rotulo sobre o ARQUIVO com os ref_ids REAIS;
(ii) aplica a regra na REGUA SOBOL e (SEPARADAMENTE) no BLOCO ESTRATIFICADO.
READ-ONLY."""
import json, sys, os
import numpy as np, pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src.problems import MMF1, evaluate_problem

B = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4/exp_main_b4_MMF1_42'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4/'
R = {}

man = json.load(open(B + '.manifest.json'))
L = [json.loads(l) for l in open(B + '.jsonl')]
gens = {g['geracao']: g for g in L if g['rec'] == 'b4_gen'}
df1 = pq.read_table(B + '__real.parquet').to_pandas().sort_values('fe_index').reset_index(drop=True)
df2 = pq.read_table(B + '__pop.parquet').to_pandas()
df3 = pq.read_table(B + '__surrogate.parquet').to_pandas()

F1 = df1[['f0', 'f1']].values.astype(np.float64)          # float32 promovido
sid2row = {int(s): i for i, s in enumerate(df1.solution_id.values)}

# ---------- 0. o avaliador bate com o artefato? ----------
art = pq.read_table('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet').to_pandas()
art = art.iloc[:2000].reset_index(drop=True)
Xa = art[['x0', 'x1']].values
Fa = art[['f0', 'f1']].values
Fr = evaluate_problem(MMF1(), Xa)
R['0_avaliador_max_dif_vs_artefato'] = float(np.abs(Fr - Fa).max())

# ---------- helpers ----------
def rotulo(Fpts, Rrefs, op):
    """DI-18: rotulo 1  <=>  para CADA ref j existe objetivo k com f_k <op> R_jk."""
    # Fpts (n,M), Rrefs (K,M)
    out = np.ones(len(Fpts), dtype=bool)
    for j in range(len(Rrefs)):
        if op == 'le':
            ok = (Fpts <= Rrefs[j]).any(axis=1)
        else:
            ok = (Fpts < Rrefs[j]).any(axis=1)
        out &= ok
    return out

def domina_alguma(Fpts, Rrefs):
    """regra IMPRESSA no paper (Alg.4): domina estritamente ao menos 1 referencia."""
    out = np.zeros(len(Fpts), dtype=bool)
    for j in range(len(Rrefs)):
        out |= ((Fpts <= Rrefs[j]).all(axis=1) & (Fpts < Rrefs[j]).any(axis=1))
    return out

def nao_dominado_por_nenhuma(Fpts, Rrefs):
    out = np.ones(len(Fpts), dtype=bool)
    for j in range(len(Rrefs)):
        dom = ((Rrefs[j] <= Fpts).all(axis=1) & (Rrefs[j] < Fpts).any(axis=1))
        out &= ~dom
    return out

def metricas(y, pclass, conf):
    y = np.asarray(y, bool); p = np.asarray(pclass, bool)
    tp = int((y & p).sum()); fp = int((~y & p).sum())
    fn = int((y & ~p).sum()); tn = int((~y & ~p).sum())
    acc = (tp + tn) / len(y)
    prec = tp / (tp + fp) if (tp + fp) else np.nan
    rec = tp / (tp + fn) if (tp + fn) else np.nan
    # AUC de Mann-Whitney
    if y.all() or (~y).all():
        auc = np.nan
    else:
        r = pd.Series(conf).rank().values
        n1 = y.sum(); n0 = (~y).sum()
        auc = (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return dict(n=len(y), prev=float(y.mean()), acc=float(acc), prec=float(prec),
                rec=float(rec), auc=float(auc), tp=tp, fp=fp, fn=fn, tn=tn)

# ---------- 1. fechar rr / y_treino_dist com os ref_ids REAIS ----------
rows = []
arq = {int(g): df2[df2.geracao == g].solution_id.values for g in df2.geracao.unique()}
for g, ev in sorted(gens.items()):
    sids = arq[g]                       # arquivo no INICIO da geracao g (② )
    Farq = F1[[sid2row[int(s)] for s in sids]]
    ridx = np.array(ev['ref_ids'])
    # interpretacao A: ref_ids sao POSICOES no arquivo ②
    Ra = Farq[ridx]
    # interpretacao B: ref_ids sao solution_id
    Rb = F1[[sid2row[int(s)] for s in ridx]]
    for nome, Rref in (('posicional②', Ra), ('solution_id', Rb)):
        hi = rotulo(Farq, Rref, 'le').sum()
        lo = rotulo(Farq, Rref, 'lt').sum()
        rows.append(dict(geracao=g, interp=nome, n1_hi=int(hi), n1_lo=int(lo),
                         n1_log=ev['y_treino_dist']['classe_1'],
                         n_arq=len(sids), n_log=ev['y_treino_dist']['n'],
                         dom_alguma=int(domina_alguma(Farq, Rref).sum()),
                         nao_dom=int(nao_dominado_por_nenhuma(Farq, Rref).sum())))
T = pd.DataFrame(rows)
T['exato'] = T.n1_hi == T.n1_log
T['sanduiche'] = (T.n1_lo <= T.n1_log) & (T.n1_log <= T.n1_hi)
T['decidida'] = T.n1_lo == T.n1_hi
T.to_csv(OUT + 'b4_t11_rotulo_arquivo.csv', index=False)
for nome in ('posicional②', 'solution_id'):
    s = T[T.interp == nome]
    R['1_' + nome] = dict(exato=int(s.exato.sum()), sanduiche=int(s.sanduiche.sum()),
                          decididas=int(s.decidida.sum()),
                          exato_entre_decididas=int((s.exato & s.decidida).sum()),
                          n=len(s),
                          regra_paper_match=int((s.dom_alguma == s.n1_log).sum()),
                          nao_dom_match=int((s.nao_dom == s.n1_log).sum()))
R['1_n_arq_eq_n_log'] = int((T[T.interp == 'posicional②'].n_arq == T[T.interp == 'posicional②'].n_log).sum()), len(gens)

# ---------- 2. REGUA SOBOL (regime='sonda') ----------
S = df3[df3.regime == 'sonda'].copy()
blocos = sorted(S.geracao.unique())
res = []
for g in blocos:
    blk = S[S.geracao == g]
    assert len(blk) == 2000, (g, len(blk))
    dX = np.abs(blk[['x0', 'x1']].values.astype(np.float32) - Xa.astype(np.float32)).max()
    ev = gens[int(g)]
    sids = arq[int(g)]
    Farq = F1[[sid2row[int(s)] for s in sids]]
    Rref = Farq[np.array(ev['ref_ids'])]
    y_hi = rotulo(Fa, Rref, 'le'); y_lo = rotulo(Fa, Rref, 'lt')
    p = (blk.pred_classe.values == 'bom'); conf = blk.pred_confianca.values.astype(float)
    m = metricas(y_hi, p, conf)
    m.update(geracao=int(g), maxdX=float(dX), ambiguos=int((y_hi != y_lo).sum()),
             prev_lo=float(y_lo.mean()),
             prev_paper=float(domina_alguma(Fa, Rref).mean()),
             prev_naodom=float(nao_dominado_por_nenhuma(Fa, Rref).mean()),
             L_med=float(np.median(conf)), pred_pos=float(p.mean()))
    res.append(m)
Sr = pd.DataFrame(res); Sr.to_csv(OUT + 'b4_t11_sonda_sobol.csv', index=False)
R['2_sobol'] = dict(n_blocos=len(Sr), maxdX=float(Sr.maxdX.max()),
                    prev_media=float(Sr.prev.mean()), prev_min=float(Sr.prev.min()), prev_max=float(Sr.prev.max()),
                    auc_media=float(Sr.auc.mean()), auc_mediana=float(Sr.auc.median()),
                    auc_min=float(Sr.auc.min()), auc_max=float(Sr.auc.max()),
                    auc_gt05=int((Sr.auc > 0.5).sum()), auc_gt07=int((Sr.auc > 0.7).sum()),
                    acc_media=float(Sr.acc.mean()), prec_media=float(Sr.prec.mean()),
                    rec_media=float(Sr.rec.mean()),
                    prev_paper_media=float(Sr.prev_paper.mean()),
                    prev_naodom_media=float(Sr.prev_naodom.mean()),
                    ambiguos_total=int(Sr.ambiguos.sum()),
                    L_med_primeiro=float(Sr.L_med.iloc[0]), L_med_ultimo=float(Sr.L_med.iloc[-1]),
                    auc_1o_terco=float(Sr.auc.iloc[:8].mean()), auc_3o_terco=float(Sr.auc.iloc[-8:].mean()))

# ---------- 3. BLOCO ESTRATIFICADO (regime='sonda_estratificada') — SEPARADO (regra 12) ----------
E = df3[df3.regime == 'sonda_estratificada'].copy()
blocosE = sorted(E.geracao.unique())
resE = []
for g in blocosE:
    blk = E[E.geracao == g]
    Xe = blk[['x0', 'x1']].values.astype(np.float64)
    Fe = evaluate_problem(MMF1(), Xe)
    ev = gens[int(g)]
    sids = arq[int(g)]
    Farq = F1[[sid2row[int(s)] for s in sids]]
    Rref = Farq[np.array(ev['ref_ids'])]
    y_hi = rotulo(Fe, Rref, 'le'); y_lo = rotulo(Fe, Rref, 'lt')
    p = (blk.pred_classe.values == 'bom'); conf = blk.pred_confianca.values.astype(float)
    m = metricas(y_hi, p, conf)
    m.update(geracao=int(g), n_pontos=len(blk), ambiguos=int((y_hi != y_lo).sum()),
             prev_lo=float(y_lo.mean()),
             prev_paper=float(domina_alguma(Fe, Rref).mean()),
             L_med=float(np.median(conf)), pred_pos=float(p.mean()),
             dist_min=float(np.sqrt(((Xe[:, None, :] - df1[['x0', 'x1']].values[None, :len(sids), :]) ** 2).sum(-1)).min()))
    resE.append(m)
Er = pd.DataFrame(resE); Er.to_csv(OUT + 'b4_t11_sonda_estratificada.csv', index=False)
R['3_estratificada'] = dict(n_blocos=len(Er), n_pontos=int(Er.n_pontos.sum()),
                            prev_media=float(Er.prev.mean()), prev_min=float(Er.prev.min()), prev_max=float(Er.prev.max()),
                            auc_media=float(Er.auc.mean()), auc_mediana=float(Er.auc.median()),
                            auc_min=float(Er.auc.min()), auc_max=float(Er.auc.max()),
                            auc_gt05=int((Er.auc > 0.5).sum()), auc_gt07=int((Er.auc > 0.7).sum()),
                            acc_media=float(Er.acc.mean()), prec_media=float(Er.prec.mean()),
                            rec_media=float(Er.rec.mean()),
                            ambiguos_total=int(Er.ambiguos.sum()),
                            auc_1o_terco=float(Er.auc.iloc[:8].mean()), auc_3o_terco=float(Er.auc.iloc[-8:].mean()),
                            L_med_primeiro=float(Er.L_med.iloc[0]), L_med_ultimo=float(Er.L_med.iloc[-1]))
R['3_razao_prevalencia_estrat_sobre_sobol'] = float(Er.prev.mean() / Sr.prev.mean())

print(json.dumps(R, indent=1, default=str))
