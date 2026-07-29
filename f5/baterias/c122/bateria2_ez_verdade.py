#!/usr/bin/env python
"""BATERIA 2 — c122: o e(z) do EDN contra a DOMINANCIA REAL (contrafactual).

Para cada geracao de cada celula: pega o TOP-100 exportado na ③ (regime=online),
avalia a funcao VERDADEIRA nos X exportados e compara o ranking do e(z)
(dominancia PREVISTA ponderada pela confianca) com a dominancia REAL dentro do
mesmo conjunto. Mede: rho de Spearman, taxa de acerto do argmax (top-1),
percentil do escolhido, e a fracao de conjuntos degenerados ("satura por
vitoria": o escolhido domina todos / ninguem domina ninguem).

Tambem fecha a identidade ③.X -> ①.f do escolhido (prova de que a linha
exportada e a solucao que virou FE).

READ-ONLY sobre os dados. Escreve so em f5/baterias/c122/.
"""
import os, sys, json, pickle
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea')
from src.experiment import _instantiate_problem
from src.problems import evaluate_problem

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c122'
PROBS = sorted([p for p in os.listdir(RAIZ) if not p.startswith('.')])


def dom_count(F):
    """n_i = #{j != i : F_i domina F_j} (Pareto, minimizacao)."""
    n = len(F)
    le = (F[:, None, :] <= F[None, :, :]).all(axis=2)
    lt = (F[:, None, :] < F[None, :, :]).any(axis=2)
    d = le & lt
    np.fill_diagonal(d, False)
    return d.sum(axis=1)


def cell(prob):
    b = f'{RAIZ}/{prob}/42/exp_main_c122_{prob}_42'
    mf = json.load(open(b + '.manifest.json'))
    D, M = None, None
    hdr = json.loads(open(b + '.jsonl').readline())
    D, M = hdr['D'], hdr['M']
    xs = [f'x{i}' for i in range(D)]
    sg = pd.read_parquet(b + '__surrogate.parquet',
                         columns=['regime', 'geracao', 'real_solution_id',
                                  'pred_score', 'pred_confianca'] + xs)
    on = sg[sg.regime == 'online'].copy()
    del sg
    real = pd.read_parquet(b + '__real.parquet',
                           columns=['solution_id'] + [f'f{j}' for j in range(M)] + xs)
    P = _instantiate_problem(prob)

    X = on[xs].to_numpy(np.float64)
    F = evaluate_problem(P, X)
    on['_ix'] = np.arange(len(on))

    rhos, top1, perc, ndeg, nsets, nzero, ntot_c = [], [], [], 0, 0, 0, 0
    conf_hit, conf_miss = [], []
    ez_all, dn_all = [], []
    for g, sub in on.groupby('geracao'):
        idx = sub._ix.to_numpy()
        if len(idx) < 3:
            continue
        Fg = F[idx]
        ez = sub.pred_score.to_numpy(np.float64)
        if np.isnan(ez).any():
            continue
        dn = dom_count(Fg)
        nsets += 1
        ntot_c += len(idx)
        if dn.max() == 0:
            nzero += 1
        if np.unique(ez).size < 2 or np.unique(dn).size < 2:
            ndeg += 1
        else:
            rhos.append(spearmanr(ez, dn).statistic)
        k = int(np.argmax(ez))
        # top-1: o argmax de e(z) e tambem um argmax da dominancia REAL?
        hit = bool(dn[k] == dn.max())
        top1.append(hit)
        perc.append(float((dn <= dn[k]).mean()))
        cf = sub.pred_confianca.to_numpy(np.float64)[k]
        (conf_hit if hit else conf_miss).append(cf)
        ez_all.append(ez); dn_all.append(dn)

    # identidade ③.X (escolhido) -> ①.f
    ch = on[on.real_solution_id.notna()]
    sid = ch.real_solution_id.astype(int).to_numpy()
    Fch = F[ch._ix.to_numpy()]
    Freal = real.set_index('solution_id').loc[sid][[f'f{j}' for j in range(M)]].to_numpy(np.float64)
    dfmax = float(np.abs(Fch - Freal).max())
    Xreal = real.set_index('solution_id').loc[sid][xs].to_numpy(np.float64)
    dxmax = float(np.abs(ch[xs].to_numpy(np.float64) - Xreal).max())

    ez_all = np.concatenate(ez_all) if ez_all else np.array([])
    dn_all = np.concatenate(dn_all) if dn_all else np.array([])
    rho_pool = float(spearmanr(ez_all, dn_all).statistic) if len(ez_all) > 10 else np.nan
    return {
        'problema': prob, 'D': D, 'M': M,
        'n_sets': nsets, 'n_cands_tot': ntot_c,
        'rho_med': float(np.median(rhos)) if rhos else np.nan,
        'rho_p25': float(np.percentile(rhos, 25)) if rhos else np.nan,
        'rho_p75': float(np.percentile(rhos, 75)) if rhos else np.nan,
        'rho_frac_pos': float(np.mean(np.array(rhos) > 0)) if rhos else np.nan,
        'rho_pool': rho_pool,
        'n_rho': len(rhos), 'n_degenerado': ndeg,
        'frac_set_sem_dominancia': nzero / nsets if nsets else np.nan,
        'top1_frac': float(np.mean(top1)) if top1 else np.nan,
        'percentil_med': float(np.median(perc)) if perc else np.nan,
        'conf_hit_med': float(np.median(conf_hit)) if conf_hit else np.nan,
        'conf_miss_med': float(np.median(conf_miss)) if conf_miss else np.nan,
        'dX_escolhido_vs_real': dxmax, 'dF_escolhido_vs_real': dfmax,
    }


def main():
    rows = []
    for p in PROBS:
        try:
            r = cell(p); rows.append(r); print('OK', p, round(r['rho_med'], 3),
                                               round(r['top1_frac'], 3), flush=True)
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERR', p, e)
    df = pd.DataFrame(rows)
    df.to_csv(f'{OUT}/c122_ez_verdade.csv', index=False)
    print(df.to_string())


if __name__ == '__main__':
    main()
