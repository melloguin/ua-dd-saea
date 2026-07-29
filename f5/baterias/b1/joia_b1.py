"""Bateria b1 - parte 4: a QUERY-JOIA em versao FORTE.
Recomputa o EI de TODAS as ~5,55 M linhas do pool final do GA interno (a (3) online),
com o gbest da propria iteracao, e verifica:
  (i)  argmax_pool EI  ==  (mu_best, sigma_best) logados no (6)  -> o infill E o argmax-EI
  (ii) EI(argmax) == -ei_best (identidade fechada, ja provada no (6))
  (iii) NAO-GREEDY exato: argmax-EI != argmin-mu (sem ruido de float32)
  (iv)  ranking: posicao do escolhido no ranking de mu (percentil)
Saidas: b1_joia_iter.csv (1 linha/iteracao) + b1_joia_celula.csv
"""
import json, os
import numpy as np, pandas as pd
import pyarrow.parquet as pq
from scipy.special import ndtr

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])

rows, cells = [], []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    sur = pq.read_table(base + '__surrogate.parquet',
                        columns=['regime', 'geracao', 'mu_0', 'sigma_0', 'real_solution_id']).to_pandas()
    on = sur[sur.regime == 'online']
    del sur
    on = on.sort_index()
    idx = {}
    gg = on.geracao.astype(int).values
    # blocos contiguos por geracao
    start = 0
    for i in range(1, len(gg) + 1):
        if i == len(gg) or gg[i] != gg[start]:
            idx[int(gg[start])] = (start, i)
            start = i
    MU = on.mu_0.values.astype(np.float64)
    SG = on.sigma_0.values.astype(np.float64)
    RS = on.real_solution_id.values
    for e in ge:
        g = e['geracao']
        a, b = idx[g]
        mu = MU[a:b]; sg = SG[a:b]
        gb = e['gbest']
        z = np.where(sg > 0, (gb - mu) / np.where(sg > 0, sg, 1.0), 0.0)
        ei = np.where(sg > 0, (gb - mu) * ndtr(z) + sg * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi),
                      np.maximum(gb - mu, 0.0))
        k = int(np.argmax(ei))
        kmu = int(np.argmin(mu))
        # o escolhido bate com o logado? (o (3) e float32; tolerancia relativa float32)
        dmu = abs(mu[k] - e['mu_best']) / max(abs(e['mu_best']), 1e-30)
        dsg = abs(sg[k] - e['sigma_best']) / max(abs(e['sigma_best']), 1e-30)
        dei = abs(ei[k] - (-e['ei_best'])) / max(abs(e['ei_best']), 1e-300)
        # percentil de mu do escolhido dentro do pool (0 = menor mu)
        perc_mu = float((mu < mu[k]).mean())
        perc_sg = float((sg < sg[k]).mean())
        rows.append(dict(problema=p, geracao=g, n_pool=b - a,
                         k_ei=k, k_mu=kmu, nao_greedy=(k != kmu),
                         d_mu=dmu, d_sg=dsg, d_ei_pool=dei,
                         mu_sel=mu[k], mu_min=mu[kmu], sg_sel=sg[k],
                         perc_mu=perc_mu, perc_sg=perc_sg,
                         ei_sel=ei[k], ei_do_argmin_mu=ei[kmu],
                         ganho_ei=float(ei[k] - ei[kmu]),
                         rsid_sel=(RS[a:b][k] == RS[a:b][k]),
                         rsid_frac=float(pd.notna(RS[a:b]).mean())))
    it = pd.DataFrame([r for r in rows if r['problema'] == p])
    cells.append(dict(problema=p, n_iter=len(it),
                      match_mu=int((it.d_mu < 1e-6).sum()), match_sg=int((it.d_sg < 1e-6).sum()),
                      match_both=int(((it.d_mu < 1e-6) & (it.d_sg < 1e-6)).sum()),
                      max_dmu=float(it.d_mu.max()), max_dsg=float(it.d_sg.max()),
                      ei_pool_ok=int((it.d_ei_pool < 1e-5).sum()), max_dei=float(it.d_ei_pool.max()),
                      n_nao_greedy=int(it.nao_greedy.sum()), frac_nao_greedy=float(it.nao_greedy.mean()),
                      perc_mu_med=float(it.perc_mu.median()), perc_sg_med=float(it.perc_sg.median()),
                      perc_mu_ng=float(it.loc[it.nao_greedy, 'perc_mu'].median()) if it.nao_greedy.any() else np.nan,
                      perc_sg_ng=float(it.loc[it.nao_greedy, 'perc_sg'].median()) if it.nao_greedy.any() else np.nan,
                      rsid_frac=float(it.rsid_frac.mean()), n_pool_med=float(it.n_pool.median())))
    print(f'{p:10s} iters={len(it):4d} match(mu,sg)={int(((it.d_mu<1e-6)&(it.d_sg<1e-6)).sum())}/{len(it)} '
          f'maxdmu={it.d_mu.max():.2e} NG={it.nao_greedy.mean():.3f} '
          f'perc_mu_med={it.perc_mu.median():.3f} perc_sg_med={it.perc_sg.median():.3f}')
    del on, MU, SG, RS

pd.DataFrame(rows).to_csv(f'{OUT}/b1_joia_iter.csv', index=False)
cd = pd.DataFrame(cells); cd.to_csv(f'{OUT}/b1_joia_celula.csv', index=False)
print()
print('argmax-EI do pool == (mu_best,sigma_best) do (6):', cd.match_both.sum(), '/', cd.n_iter.sum())
print('  max erro rel mu:', cd.max_dmu.max(), ' sigma:', cd.max_dsg.max())
print('EI(argmax pool) == -ei_best:', cd.ei_pool_ok.sum(), '/', cd.n_iter.sum(), 'max rel', cd.max_dei.max())
print('NAO-GREEDY total:', cd.n_nao_greedy.sum(), '/', cd.n_iter.sum(),
      ' por celula: min', cd.frac_nao_greedy.min(), 'mediana', cd.frac_nao_greedy.median(), 'max', cd.frac_nao_greedy.max())
print('percentil mediano de mu do escolhido:', cd.perc_mu_med.median(), ' de sigma:', cd.perc_sg_med.median())
