"""T05 — a RÉGUA SOBOL do c311 re-medida, com a coluna que o `sonda_f52e.csv` não tem:
`n_sigma_valido` (o item I-11 que a T11 respondeu com AVISO no ⑤, sem produzir o número).
WAPE/corr no espaço CRU (transf_tipo NULL em 54/54) · cobertura ±1,96σ SÓ sobre σ finito.
Os 2 blocos são bit-idênticos (F1) ⇒ mede-se o bloco 0.
Regra 12 do CONTRATO: c311 não tem `sonda_estratificada` — nada a separar.
READ-ONLY. Escreve só nesta pasta."""
import sys, os, json
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311')
import numpy as np, pandas as pd
import lib_c311 as L

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'
SONDA = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'

rows = []
for label, d, pref in L.celulas():
    man, evs, dfs = L.carrega(d, pref, camadas=('surrogate',))
    mt = L.meta(label, man)
    sur = dfs['surrogate']; so = L.sonda(sur)
    b0 = so[so['modelo_flag'] == 'treedGP_build'].reset_index(drop=True)
    mu = L.mucols(b0); sg = L.sigcols(b0)
    gab = pd.read_parquet(os.path.join(SONDA, f"sonda_{mt['problema']}.parquet"))
    fc = L.fcols(gab)
    assert (b0['espaco_modelo'] == 'cru').all() and b0['transf_tipo'].isna().all()
    for j in range(len(mu)):
        m = b0[mu[j]].values.astype(np.float64)
        s = b0[sg[j]].values.astype(np.float64)
        f = gab[fc[j]].values[:20000].astype(np.float64)
        wape = float(np.abs(m - f).sum() / np.abs(f).sum())
        corr = float(np.corrcoef(m, f)[0, 1])
        ok = np.isfinite(s)
        cob = float((np.abs(m[ok] - f[ok]) <= 1.96 * s[ok]).mean()) if ok.any() else np.nan
        rows.append(dict(**mt, obj=j, wape=wape, corr=corr, cobertura95=cob,
                         n_validas_mu=int(np.isfinite(m).sum()), n_nan_mu=int((~np.isfinite(m)).sum()),
                         n_sigma_valido=int(ok.sum()), sigma_nan_share=float(1 - ok.mean())))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 't05_sonda_regua.csv'), index=False)

ofc = pd.read_csv('/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/sonda_f52e.csv')
ofc = ofc[ofc.alg == 'c311'] if 'alg' in ofc.columns else ofc
print('pares (célula, objetivo):', len(df), '| linhas c311 no sonda_f52e.csv:', len(ofc))
print('\n== n_sigma_valido — a coluna que o CSV oficial NÃO tem ==')
print('mediana: %d de 20.000 | mínimo: %d | pares com <1.000: %d | com 20.000: %d'
      % (df.n_sigma_valido.median(), df.n_sigma_valido.min(),
         (df.n_sigma_valido < 1000).sum(), (df.n_sigma_valido == 20000).sum()))
print('\npior caso (o citado no AVISO do ⑤):')
print(df.nsmallest(5, 'n_sigma_valido')[['label', 'obj', 'cobertura95', 'n_sigma_valido',
                                         'sigma_nan_share', 'n_validas_mu']].to_string(index=False))
print('\ncobertura95 (só σ finito): mediana %.4f  q1 %.4f  q3 %.4f  (n=%d pares com σ)'
      % (df.cobertura95.median(), df.cobertura95.quantile(.25),
         df.cobertura95.quantile(.75), df.cobertura95.notna().sum()))
print('σ-NaN share por tier (mediana):')
print(df.groupby('tier').agg(nsig_med=('n_sigma_valido', 'median'),
                             nan_med=('sigma_nan_share', 'median'),
                             wape_med=('wape', 'median'),
                             cob_med=('cobertura95', 'median')).to_string())
print('\nWAPE do tier small (off) por problema:')
sm = df[df.exp == 'off'].pivot_table(index='problema', columns='obj', values='wape')
co = df[df.exp == 'off'].pivot_table(index='problema', columns='obj', values='corr')
print(pd.concat([sm.add_prefix('wape_'), co.add_prefix('corr_')], axis=1).round(3).to_string())
