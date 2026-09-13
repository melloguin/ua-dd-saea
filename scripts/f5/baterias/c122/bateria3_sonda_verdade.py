#!/usr/bin/env python
"""BATERIA 3 — c122: a SONDA contra a verdade (analise propria da familia).

A sonda grava e(z) = EDN dos 2.000 pontos do gabarito CONTRA a populacao
selecionada corrente (n_ref = N). Aqui reconstruimos a MESMA grandeza com a
VERDADE: quantos membros da populacao cada ponto do gabarito realmente domina
(Pareto, f reais). Comparamos:
  (a) rho de Spearman e(z) x dominancia real, bloco a bloco;
  (b) o teste de ALINHAMENTO da referencia — ②(g-1) [pos-truncamento da geracao
      anterior] vs ②(g) — para provar QUAL populacao a sonda usou;
  (c) a saturacao "POR VITORIA": fracao de blocos em que NINGUEM domina ninguem
      na verdade (e nao so no modelo).

READ-ONLY sobre os dados. Escreve so em f5/baterias/c122/.
"""
import os, sys, json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122'
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c122'
PROBS = sorted([p for p in os.listdir(RAIZ) if not p.startswith('.')])


def dom_inter(Fz, Fp):
    """n_i = #{j : Fz_i domina Fp_j} (minimizacao)."""
    le = (Fz[:, None, :] <= Fp[None, :, :]).all(axis=2)
    lt = (Fz[:, None, :] < Fp[None, :, :]).any(axis=2)
    return (le & lt).sum(axis=1)


def cell(prob):
    b = f'{RAIZ}/{prob}/42/exp_main_c122_{prob}_42'
    hdr = json.loads(open(b + '.jsonl').readline())
    D, M = hdr['D'], hdr['M']
    mf = json.load(open(b + '.manifest.json'))
    N = mf['params']['N_MU']
    sx = pd.read_parquet(f'{SND}/sonda_{prob}.parquet')
    fc = [c for c in sx.columns if c.startswith('f')][:M]
    Fz = sx[fc].to_numpy(np.float64)[:2000]

    sg = pd.read_parquet(b + '__surrogate.parquet',
                         columns=['regime', 'geracao', 'pred_score', 'pred_confianca'])
    so = sg[sg.regime == 'sonda']
    del sg
    pop = pd.read_parquet(b + '__pop.parquet')
    real = pd.read_parquet(b + '__real.parquet',
                           columns=['solution_id', 'fase'] + [f'f{j}' for j in range(M)])
    Fall = real[[f'f{j}' for j in range(M)]].to_numpy(np.float64)
    ini = real.fase.eq('init').sum()
    pg = {int(g): v.solution_id.to_numpy() for g, v in pop.groupby('geracao')}

    rows = []
    for g, sub in so.groupby('geracao'):
        g = int(g)
        ez = sub.pred_score.to_numpy(np.float64)
        ref_prev = pg.get(g - 1) if g > 1 else np.arange(ini)
        ref_cur = pg.get(g)
        out = {'problema': prob, 'geracao': g, 'N': N,
               'n_ref_prev': (len(ref_prev) if ref_prev is not None else 0),
               'ez_max': float(np.nanmax(ez)), 'ez_frac_pos': float((ez > 0).mean()),
               'conf_med': float(np.nanmedian(sub.pred_confianca.to_numpy(np.float64)))}
        for tag, ref in (('prev', ref_prev), ('cur', ref_cur)):
            if ref is None or len(ref) == 0:
                out[f'rho_{tag}'] = np.nan; out[f'dnmax_{tag}'] = np.nan
                out[f'viol_{tag}'] = np.nan; out[f'fracpos_{tag}'] = np.nan
                continue
            dn = dom_inter(Fz, Fall[ref])
            out[f'dnmax_{tag}'] = int(dn.max())
            out[f'fracpos_{tag}'] = float((dn > 0).mean())
            # violacao de teto: e(z) so pode chegar a 2*len(ref)
            out[f'viol_{tag}'] = float((ez > 2 * len(ref) + 1e-6).mean())
            if np.unique(ez).size > 1 and np.unique(dn).size > 1:
                out[f'rho_{tag}'] = float(spearmanr(ez, dn).statistic)
            else:
                out[f'rho_{tag}'] = np.nan
        rows.append(out)
    return pd.DataFrame(rows)


def main():
    todos = []
    for p in PROBS:
        try:
            d = cell(p); todos.append(d)
            print('OK', p, len(d), 'rho_prev med=%.3f' % d.rho_prev.median(),
                  'rho_cur med=%.3f' % d.rho_cur.median(), flush=True)
        except Exception as e:
            import traceback; traceback.print_exc(); print('ERR', p, e)
    D = pd.concat(todos, ignore_index=True)
    D.to_csv(f'{OUT}/c122_sonda_verdade.csv', index=False)
    g = D[D.geracao > 1].groupby('problema').agg(
        n_blocos=('geracao', 'size'),
        rho_prev_med=('rho_prev', 'median'), rho_cur_med=('rho_cur', 'median'),
        viol_prev=('viol_prev', 'mean'), viol_cur=('viol_cur', 'mean'),
        ez_fracpos_med=('ez_frac_pos', 'median'),
        true_fracpos_med=('fracpos_prev', 'median'),
        blocos_ez_zero=('ez_frac_pos', lambda x: float((x == 0).mean())),
        blocos_true_zero=('fracpos_prev', lambda x: float((x == 0).mean())),
        conf_med=('conf_med', 'median'))
    g.to_csv(f'{OUT}/c122_sonda_verdade_resumo.csv')
    print(g.to_string())


if __name__ == '__main__':
    main()
