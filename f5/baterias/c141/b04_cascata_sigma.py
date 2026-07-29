#!/usr/bin/env python
"""B04 — aspectos especificos do bundle c141: cascata, papel de U, sigma D45, RBF mal-condicionado,
batch variavel, hard-stop/overshoot, dsmerge, telemetria (Q,U), semantica dos sinais [-Fit1,Fit2,-Fit3].
Roda em TODAS as 25 celulas / 1967 ciclos.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT, sde, ranks_asc, QU

OUT = os.path.dirname(os.path.abspath(__file__))


def pd2(A, B):
    return np.maximum((A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T, 0.0)


def f1i(F):
    le = (F[:, None, :] <= F[None, :, :]).all(-1)
    lt = (F[:, None, :] < F[None, :, :]).any(-1)
    return np.where(~(le & lt).any(0))[0]


cel, ger = [], []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    h = [e for e in ev if e.get('rec') == 'header'][0]
    ftr = [e for e in ev if e.get('rec') == 'footer'][0]
    D, M = h['D'], h['M']
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    mc = [f'mu_{i}' for i in range(M)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    guards = [e for e in ev if e.get('rec') == 'guard']
    on = sur[sur.regime == 'online']
    og = {g: d for g, d in on.groupby('geracao')}
    N = man['params']['N_subpop']

    for g in gens:
        P = og[g['geracao']]
        mu = P[mc].values.astype(np.float64)
        s0 = P.sigma_0.values.astype(np.float64)
        s1 = P.sigma_1.values.astype(np.float64)
        F = real.loc[real.fe_index <= g['fe_treino_max'], fc].values.astype(np.float64)
        X = real.loc[real.fe_index <= g['fe_treino_max'], xc].values.astype(np.float64)
        Phi = np.sqrt(pd2(X, X) + 1.0)
        rc = 1.0 / np.linalg.cond(Phi)
        # 3 modos reconstruidos (para semantica dos sinais)
        FitA = sde(F)
        try:
            W = np.linalg.solve(Phi, np.column_stack([FitA]))
            fitpred = (np.sqrt(pd2(mu[:, :0].reshape(len(mu), 0).shape[0] and X[:0] or X[:0], X[:0]) + 1.0) if False else None)
        except Exception:
            pass
        d = dict(problema=pb, D=D, M=M, geracao=g['geracao'], N=N,
                 lote=g['lote'], nivel=g['nivel'], ramo_QU=g['ramo_QU'],
                 n_front1=g['n_front1'], n_front2=g['n_front2'],
                 entrada=g['n_por_nivel']['entrada'], sel=g['n_por_nivel']['selecionados'],
                 n_sub1=g['n_sub1'], n_sub2=g['n_sub2'], n_pool=g['n_pool'],
                 rcond=rc, n_treino=len(X), hp_n=g['modelo_hp']['n'],
                 hp_c=g['modelo_hp']['bf_c'], hp_poly=g['modelo_hp']['poly'], hp_bf=g['modelo_hp']['bf_type'],
                 s0_min=np.nanmin(s0), s0_max=np.nanmax(s0), s0_med=np.nanmedian(s0),
                 s0_int=float((s0 == np.round(s0)).mean()), s0_teto=2 * (len(mu) - 1),
                 s1_min=np.nanmin(s1), s1_max=np.nanmax(s1), s1_med=np.nanmedian(s1),
                 s0_nan=float(np.isnan(s0).mean()), s1_nan=float(np.isnan(s1).mean()),
                 mu_min=float(mu.min()), mu_max=float(mu.max()),
                 dist_min=json.dumps(g.get('dist_min_arquivo')),
                 dist_min_med=float(np.median(g['dist_min_arquivo'])) if g.get('dist_min_arquivo') else np.nan,
                 dist_min_max=float(np.max(g['dist_min_arquivo'])) if g.get('dist_min_arquivo') else np.nan,
                 U_max=(g['U']['max'] if isinstance(g.get('U'), dict) else np.nan),
                 U_min=(g['U']['min'] if isinstance(g.get('U'), dict) else np.nan),
                 Q_med=(g['Q']['med'] if isinstance(g.get('Q'), dict) else np.nan),
                 U_pool_max=g['U_pool_max'],
                 fit1_med=(g['fit1']['med'] if isinstance(g.get('fit1'), dict) else np.nan),
                 fit2_med=(g['fit2']['med'] if isinstance(g.get('fit2'), dict) else np.nan),
                 fit3_med=(g['fit3']['med'] if isinstance(g.get('fit3'), dict) else np.nan),
                 fit2_min=(g['fit2']['min'] if isinstance(g.get('fit2'), dict) else np.nan),
                 fit2_max=(g['fit2']['max'] if isinstance(g.get('fit2'), dict) else np.nan),
                 fit3_max=(g['fit3']['max'] if isinstance(g.get('fit3'), dict) else np.nan),
                 fit1_max=(g['fit1']['max'] if isinstance(g.get('fit1'), dict) else np.nan),
                 )
        ger.append(d)

    dg = pd.DataFrame([x for x in ger if x['problema'] == pb])
    lotes = dg.lote.values
    cel.append(dict(
        problema=pb, D=D, M=M, N=N, n_ciclos=len(dg),
        lote_min=int(lotes.min()), lote_max=int(lotes.max()), lote_med=float(np.median(lotes)),
        lote_zero=int((lotes == 0).sum()), lote_gt2N=int((lotes > 2 * N).sum()),
        soma_lotes=int(lotes.sum()),
        niv1=int((dg.nivel == 1).sum()), niv2=int((dg.nivel == 2).sum()), niv3=int((dg.nivel == 3).sum()),
        ramoQU=int(dg.ramo_QU.sum()), ramoQU_pct=float(dg.ramo_QU.mean() * 100),
        nfront2_le1=int((dg.n_front2 <= 1).sum()),
        pool_sempre_2N=bool((dg.n_pool == 2 * N).all()),
        sub_sempre_N=bool((dg.n_sub1 == N).all() and (dg.n_sub2 == N).all()),
        entrada_2N=bool((dg.entrada == 2 * N).all()),
        sel_eq_lote=int((dg.sel == dg.lote).sum()),
        hp_const=bool((dg.hp_bf == 'MQ').all() and (dg.hp_c == 1).all() and (dg.hp_poly == 0).all()),
        hp_n_eq_treino=int((dg.hp_n == dg.n_treino).sum()),
        rcond_min=float(dg.rcond.min()), rcond_med=float(dg.rcond.median()),
        rcond_lt_1e12=int((dg.rcond < 1e-12).sum()), rcond_lt_1e15=int((dg.rcond < 1e-15).sum()),
        rcond_zero=int((dg.rcond == 0).sum()),
        s0_int_pct=float(dg.s0_int.mean() * 100), s0_max=float(dg.s0_max.max()), s0_teto=int(dg.s0_teto.iloc[0]),
        s0_nan=float(dg.s0_nan.mean()), s1_nan=float(dg.s1_nan.mean()),
        s1_med=float(dg.s1_med.median()), s1_max=float(dg.s1_max.max()),
        mu_min=float(dg.mu_min.min()), mu_max=float(dg.mu_max.max()),
        f_min=float(real[fc].values.min()), f_max=float(real[fc].values.max()),
        dist_min_med=float(dg.dist_min_med.median()), dist_min_max=float(dg.dist_min_max.max()),
        fit2_int_like=float(np.mean(np.abs(dg.fit2_med.values - np.round(dg.fit2_med.values)) < 0.15)),
        corr_fit1_fit3=float(np.corrcoef(dg.fit1_med.dropna(), dg.fit3_med.dropna())[0, 1]) if dg.fit1_med.notna().sum() > 3 else np.nan,
        corr_fit1_fit2=float(np.corrcoef(dg.fit1_med.dropna(), dg.fit2_med.dropna())[0, 1]) if dg.fit1_med.notna().sum() > 3 else np.nan,
        escala_fit1=float(dg.fit1_med.median()), escala_fit2=float(dg.fit2_med.median()), escala_fit3=float(dg.fit3_med.median()),
        guards=json.dumps({k:int(v) for k,v in pd.Series([x['name'] for x in guards]).value_counts().items()}),
        termino=ftr.get('termino'), fe_final=man['fe_final'], maxfe=man['maxfe'],
        ultimo_lote=int(man['fe_final'] - (11 * D - 1) - int(lotes.sum()) + man.get('cache_hits', 0)),
    ))
    print('ok', pb, flush=True)

pd.DataFrame(ger).to_csv(os.path.join(OUT, 'b04_ciclos.csv'), index=False)
dc = pd.DataFrame(cel)
dc.to_csv(os.path.join(OUT, 'b04_celulas.csv'), index=False)
pd.set_option('display.width', 320, 'display.max_columns', 200)
print(dc[['problema', 'D', 'M', 'N', 'n_ciclos', 'lote_min', 'lote_max', 'lote_med', 'lote_zero', 'lote_gt2N',
          'niv1', 'niv2', 'niv3', 'ramoQU_pct', 'pool_sempre_2N', 'sub_sempre_N', 'sel_eq_lote', 'hp_const',
          'hp_n_eq_treino']].to_string())
print()
print(dc[['problema', 'rcond_min', 'rcond_med', 'rcond_lt_1e12', 'rcond_lt_1e15', 'rcond_zero', 's0_int_pct',
          's0_max', 's0_teto', 's0_nan', 's1_nan', 's1_med', 's1_max', 'mu_min', 'mu_max', 'f_min', 'f_max',
          'dist_min_med', 'dist_min_max']].to_string())
print()
print(dc[['problema', 'escala_fit1', 'escala_fit2', 'escala_fit3', 'corr_fit1_fit3', 'corr_fit1_fit2',
          'fit2_int_like', 'termino', 'ultimo_lote', 'guards']].to_string())
