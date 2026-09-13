"""t05 — saude do surrogate no smoke: regua Sobol (regime='sonda'), WAPE/spearman/MAE_ref
por bloco e por objetivo. Regra 12 do CONTRATO respeitada (nao ha bloco estratificado no c141).
Compara com a MESMA celula da rodada-42 (main/c141/MMF1/42).
READ-ONLY."""
import json, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr

D, M = 2, 2
GAB = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
SRC = {
 'T11': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/c141/exp_main_c141_MMF1_42',
 'R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141/MMF1/42/exp_main_c141_MMF1_42',
}
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

gab = pd.read_parquet(GAB)
Gf = gab[[f'f{i}' for i in range(M)]].values[:2000].astype(np.float64)
rows = []
for tag, stem in SRC.items():
    sur = pd.read_parquet(stem + '__surrogate.parquet')
    man = json.load(open(stem + '.manifest.json'))
    sd = sur[sur.regime == 'sonda']
    P(f'== {tag} == blocos {sd.geracao.nunique()} linhas {len(sd)} regimes {sur.regime.unique().tolist()}')
    for g, blk in sd.groupby('geracao'):
        mu = blk[[f'mu_{i}' for i in range(M)]].values.astype(np.float64)
        for j in range(M):
            f = Gf[:, j]; m = mu[:, j]
            wape = np.abs(m - f).sum() / np.abs(f).sum()
            mae = np.abs(m - f).mean()
            mae_ref = np.abs(f - f.mean()).mean()
            sp = spearmanr(m, f).statistic
            rows.append(dict(fonte=tag, bloco=int(g), obj=j, WAPE=wape, spearman=sp,
                             MAE=mae, MAE_ref=mae_ref, razao=mae/mae_ref,
                             mu_min=m.min(), mu_max=m.max(), f_min=f.min(), f_max=f.max()))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't05_saude.csv'), index=False)
P('')
P(df.to_string(index=False, float_format=lambda v: f'{v:.4g}'))
P('')
for tag in SRC:
    d = df[df.fonte == tag]
    P(f'--- {tag} resumo ---')
    for j in range(M):
        dj = d[d.obj == j].sort_values('bloco')
        P(f'  obj{j}: WAPE 1o={dj.WAPE.iloc[0]:.4g} -> ult={dj.WAPE.iloc[-1]:.4g}  (D={100*(dj.WAPE.iloc[-1]/dj.WAPE.iloc[0]-1):+.1f}%)'
          f' | spearman {dj.spearman.iloc[0]:.3f} -> {dj.spearman.iloc[-1]:.3f}'
          f' | MAE/MAE_ref ult={dj.razao.iloc[-1]:.3f} max={dj.razao.max():.3f}'
          f' | mu in [{dj.mu_min.min():.4g},{dj.mu_max.max():.4g}] f in [{dj.f_min.iloc[0]:.4g},{dj.f_max.iloc[0]:.4g}]')
    dm = d.groupby('bloco').WAPE.mean()
    P(f'  WAPE medio 1o bloco {dm.iloc[0]:.4g} -> ultimo {dm.iloc[-1]:.4g}  DWAPE = {100*(dm.iloc[-1]/dm.iloc[0]-1):+.1f}%')

# --- fantasia + metricas finais da (1) ---
P('')
P('--- front final da (1) e indicadores brutos (1 semente, sem regua comum) ---')
def front1(F):
    n = len(F); dom = np.zeros(n, bool)
    for i in range(n):
        le = (F <= F[i]).all(1); lt = (F < F[i]).any(1)
        if (le & lt).any(): dom[i] = True
    return np.where(~dom)[0]
for tag, stem in SRC.items():
    real = pd.read_parquet(stem + '__real.parquet')
    F = real[[f'f{i}' for i in range(M)]].values.astype(np.float64)
    nd = front1(F)
    P(f'  {tag}: |(1)|={len(F)}  |ND|={len(nd)}  f0 in [{F[:,0].min():.4g},{F[:,0].max():.4g}]'
      f'  f1 in [{F[:,1].min():.4g},{F[:,1].max():.4g}]')
    # IGD+ contra o gabarito da sonda como proxy grosseiro (mesma referencia p/ os dois)
    R = Gf[front1(Gf)]
    Fn = F[nd]
    d = np.sqrt((np.maximum(Fn[None, :, :] - R[:, None, :], 0)**2).sum(-1))
    P(f'     IGD+ (ref = front do gabarito Sobol 2000 pts, MESMA ref nos dois) = {d.min(1).mean():.5f}')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't05_saude.txt'), 'w').write('\n'.join(out))
