#!/usr/bin/env python
"""BATERIA 3 — a camada ③ (busca + sonda) em TODAS as 25 células.
Saídas: c217_infills.csv (todos os infills, com qualidade real), c217_sonda_blocos.csv (3410 blocos),
        c217_sonda_resumo.csv
"""
import os, json
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c217'
SOND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c217'
G = pd.read_pickle(f'{OUT}/c217_identidades.pkl')

def dom_counts(F):
    """nº de pontos que dominam cada linha de F (minimização, dominância de Pareto)."""
    n = F.shape[0]
    out = np.zeros(n, dtype=np.int32)
    step = 500
    for i in range(0, n, step):
        A = F[i:i + step][:, None, :]           # (b,1,M)
        B = F[None, :, :]                        # (1,n,M)
        le = (B <= A).all(axis=2)
        lt = (B < A).any(axis=2)
        out[i:i + step] = (le & lt).sum(axis=1)
    return out

def auc_ties(score, y):
    """AUC de Mann-Whitney com empates; y bool."""
    if y.sum() == 0 or (~y).sum() == 0:
        return np.nan
    r = pd.Series(score).rank().to_numpy()
    n1 = y.sum(); n0 = (~y).sum()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

inf_rows, blk_rows = [], []
for prob in sorted(os.listdir(ROOT)):
    base = f'{ROOT}/{prob}/42/exp_main_c217_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    D = man['sonda']['S'] and None
    real = pq.read_table(base + '__real.parquet').to_pandas()
    import re as _re
    Dn = len([c for c in real.columns if _re.fullmatch(r'x\d+', c)])
    M = len([c for c in real.columns if _re.fullmatch(r'f\d+', c)])
    xc = [f'x{i}' for i in range(Dn)]; fc = [f'f{i}' for i in range(M)]
    sur = pq.read_table(base + '__surrogate.parquet').to_pandas()
    gsub = G[G.problema == prob].set_index('geracao')

    # ---------- lado BUSCA (infills) ----------
    on = sur[sur.regime == 'online'].copy()
    real_ix = real.set_index('solution_id')
    sid = on.real_solution_id.to_numpy()
    okid = ~np.isnan(sid)
    Xr = real_ix.loc[sid[okid].astype(int), xc].to_numpy().astype(np.float32)
    Xs = on.loc[okid, xc].to_numpy().astype(np.float32)
    dX = float(np.max(np.abs(Xr - Xs))) if len(Xr) else np.nan

    F = real[fc].to_numpy().astype(np.float64)
    fe = real.fe_index.to_numpy()
    order = np.argsort(fe)
    Fo = F[order]; sid_o = real.solution_id.to_numpy()[order]
    pos_of_sid = {s: i for i, s in enumerate(sid_o)}
    for _, r in on.iterrows():
        s = r.real_solution_id
        rec = dict(problema=prob, geracao=int(r.geracao), solution_id=(int(s) if not np.isnan(s) else -1),
                   pred_score=r.pred_score, pred_confianca=r.pred_confianca,
                   estado=int(gsub.loc[int(r.geracao), 'estado']),
                   lote=int(gsub.loc[int(r.geracao), 'lote']))
        if not np.isnan(s):
            i = pos_of_sid[int(s)]
            prev = Fo[:i]
            f = Fo[i]
            if len(prev):
                dom_by = ((prev <= f).all(1) & (prev < f).any(1)).sum()
                dominates = ((f <= prev).all(1) & (f < prev).any(1)).sum()
                rec['nd_vs_arq'] = bool(dom_by == 0)
                rec['n_domina'] = int(dominates)
                rec['n_dominado_por'] = int(dom_by)
                rec['frac_domina'] = dominates / len(prev)
            rec['pos'] = i
        inf_rows.append(rec)

    # ---------- lado SONDA ----------
    art = pq.read_table(f'{SOND}/sonda_{prob}.parquet').to_pandas()
    Xa = art[xc].to_numpy()[:2000].astype(np.float32)
    Fa = art[fc].to_numpy()[:2000].astype(np.float64)
    dc = dom_counts(Fa)
    good = dc <= np.median(dc)          # gabarito: metade melhor pela contagem de dominadores
    nd_art = dc == 0                     # gabarito estrito: não-dominado no bloco Sobol
    sd = sur[sur.regime == 'sonda']
    for g, blk in sd.groupby('geracao'):
        Xb = blk[xc].to_numpy().astype(np.float32)
        sc = blk.pred_score.to_numpy()
        n = len(blk)
        row = dict(problema=prob, geracao=int(g), n=n,
                   dX=float(np.max(np.abs(Xb - Xa))) if n == 2000 else np.nan,
                   conf_nuniq=int(blk.pred_confianca.nunique(dropna=False)),
                   conf=float(blk.pred_confianca.iloc[0]),
                   p_mais=float(gsub.loc[int(g), 'p_mais']) if int(g) in gsub.index else np.nan,
                   estado=int(gsub.loc[int(g), 'estado']) if int(g) in gsub.index else -1,
                   ftm=int(blk.fe_treino_max.iloc[0]),
                   frac_m1=float((sc == -1).mean()), frac_0=float((sc == 0).mean()), frac_p1=float((sc == 1).mean()),
                   mean_score=float(sc.mean()),
                   auc_good=auc_ties(sc, good) if n == 2000 else np.nan,
                   auc_nd=auc_ties(sc, nd_art) if n == 2000 else np.nan,
                   score_uniq=json.dumps(sorted(set(sc.tolist()))))
        blk_rows.append(row)
    print(prob, 'infills', len(on), 'blocos', sd.geracao.nunique(), 'dX_busca', dX)

I = pd.DataFrame(inf_rows); I.to_csv(f'{OUT}/c217_infills.csv', index=False)
B = pd.DataFrame(blk_rows); B.to_csv(f'{OUT}/c217_sonda_blocos.csv', index=False)
print('infills', len(I), '| blocos', len(B))
