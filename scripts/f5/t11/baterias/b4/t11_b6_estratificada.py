"""T11/b4 — bateria 6: o bloco ESTRATIFICADO faz o que promete?
 (a) e mesmo "perto do arquivo"? (distancia ao arquivo x a regua Sobol)
 (b) `prevalencia_nd_no_bloco` sai NaN por desenho (MATLAB) — a analise consegue
     RECOMPOR do X da ③, como b4_sonda.m:82-89 promete?
 (c) o bloco responde algo que a regua nao responde?
Regra 12: os dois blocos NUNCA entram na mesma analise — aqui sao contrastados
como DUAS reguas distintas, cada uma com o seu proprio numero. READ-ONLY.
"""
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SM = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b4'
ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b4'


def mmf1(X):
    x1, x2 = X[:, 0].astype(float), X[:, 1].astype(float)
    f1 = np.abs(x1 - 2.0)
    f2 = 1.0 - np.sqrt(f1) + 2.0 * (x2 - np.sin(6.0 * np.pi * np.abs(x1 - 2.0) + np.pi)) ** 2
    return np.column_stack([f1, f2])


art = pq.read_table(ART).to_pandas()
Xa = art[['x0', 'x1']].values[:2000]
real = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__real.parquet').to_pandas()
sur = pq.read_table(f'{SM}/exp_main_b4_MMF1_42__surrogate.parquet').to_pandas()
recs = [json.loads(l) for l in open(f'{SM}/exp_main_b4_MMF1_42.jsonl')]
gens = {r['geracao']: r for r in recs if r.get('rec') == 'b4_gen'}
sev = {r['geracao']: r for r in recs if r.get('rec') == 'sonda_estratificada'}

# arquivo por geracao: |Arc| no INICIO da geracao == n_treino  (A24 da F5)
LO = np.array([1.0, -1.0]); HI = np.array([3.0, 1.0])
rows = []
for g, sub in sur[sur.regime == 'sonda_estratificada'].groupby('geracao'):
    gi = gens[int(g)]; ev = sev[int(g)]
    nA = int(gi['n_treino'])                        # |Arc| que a sonda viu
    A = real[real.solution_id < nA]
    XA = A[['x0', 'x1']].values.astype(float)
    FA = A[['f0', 'f1']].values.astype(float)
    Xb = sub[['x0', 'x1']].values.astype(float)
    Fb = mmf1(Xb)
    # (a) distancia normalizada ao arquivo
    def dmin(X):
        Z = (X - LO) / (HI - LO); ZA = (XA - LO) / (HI - LO)
        return np.sqrt(((Z[:, None, :] - ZA[None, :, :]) ** 2).sum(-1)).min(1)
    d_est = dmin(Xb); d_reg = dmin(Xa)
    # (b) prevalencia_nd_no_bloco RECOMPOSTA: fracao do bloco nao-dominada pelo arquivo
    def nd_frac(F):
        nd = np.ones(len(F), bool)
        for k in range(len(FA)):
            nd &= ~(((FA[k] <= F).all(1)) & ((FA[k] < F).any(1)))
        return nd.mean()
    rows.append(dict(geracao=int(g), n=len(sub), n_arquivo_ev=ev['n_arquivo'], n_treino=nA,
                     sigma_rel=ev['sigma_rel'], prev_nd_logada=ev['prevalencia_nd_no_bloco'],
                     prev_nd_recomposta=nd_frac(Fb), prev_nd_regua=nd_frac(mmf1(Xa)),
                     dmin_est_mediana=np.median(d_est), dmin_regua_mediana=np.median(d_reg),
                     dmin_est_p95=np.percentile(d_est, 95), semente_bloco=ev['semente_bloco']))
d = pd.DataFrame(rows)
d.to_csv(f'{OUT}/t11_b4_estratificada.csv', index=False)
pd.set_option('display.width', 220, 'display.max_columns', 30)
print(d.to_string(index=False))
print()
print(f'(a) distancia ao arquivo (X normalizado em [0,1]^2), mediana por bloco:')
print(f'    estratificado {d.dmin_est_mediana.mean():.4f}  x  regua Sobol {d.dmin_regua_mediana.mean():.4f}'
      f'   -> o bloco esta {d.dmin_regua_mediana.mean() / d.dmin_est_mediana.mean():.1f}x MAIS PERTO')
print(f'    sigma_rel declarado = {d.sigma_rel.unique()} ; n_arquivo do evento == n_treino do b4_gen: '
      f'{int((d.n_arquivo_ev == d.n_treino).sum())}/{len(d)}')
print(f'(b) prevalencia_nd_no_bloco LOGADA: nula em {int(d.prev_nd_logada.isna().sum())}/{len(d)} (NaN por desenho, MATLAB)')
print(f'    RECOMPOSTA do X da ③: media {d.prev_nd_recomposta.mean():.4f} '
      f'(faixa {d.prev_nd_recomposta.min():.4f}–{d.prev_nd_recomposta.max():.4f})')
print(f'    a MESMA quantidade na regua Sobol: media {d.prev_nd_regua.mean():.4f}')
print(f'    razao estratificado/regua = {(d.prev_nd_recomposta / d.prev_nd_regua).mean():.3f}')
print(f'(c) semente_bloco distinta por bloco: {d.semente_bloco.nunique()}/{len(d)}')
