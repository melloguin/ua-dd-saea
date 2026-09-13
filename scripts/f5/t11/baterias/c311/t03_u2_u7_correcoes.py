"""T03 — correções de duas medições do T02 (o caminho do artefato de dataset do
tier small-MVNS e o nome do sidecar) + o teste de timing com tolerância ULP-relativa.
READ-ONLY. Escreve só nesta pasta."""
import sys, os, json
sys.path.insert(0, '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c311')
import numpy as np, pandas as pd
import lib_c311 as L

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/c311'
DS = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets'
EPS32 = np.finfo(np.float32).eps            # 1,19e-7

rows = []
for label, d, pref in L.celulas():
    man, evs, dfs = L.carrega(d, pref, camadas=('real', 'timing'))
    mt = L.meta(label, man)
    real, tim = dfs['real'], dfs['timing']
    Xc, Fc = L.xcols(real), L.fcols(real)
    # o token do artefato: `off` (small-LHS canônico) NÃO tem sufixo; o sweep tem
    tag = '' if mt['exp'] == 'off' else f"_{mt['tier']}_{mt['dist']}"
    p = os.path.join(DS, mt['problema'], f"ds_{mt['problema']}_42{tag}.parquet")
    alt = os.path.join(DS, mt['problema'], f"ds_{mt['problema']}_42.parquet")
    usado = p if os.path.exists(p) else alt
    art = pd.read_parquet(usado)
    sc = json.load(open(usado.replace('.parquet', '.manifest.json')))
    dx = int((real[Xc].values.astype(np.float32) == art[Xc].values.astype(np.float32)).all())
    df_ = int((real[Fc].values.astype(np.float32) == art[Fc].values.astype(np.float32)).all())
    hx = int(man['cp_init_offline']['x_hash'] == sc.get('x_hash'))
    hf = int(man['cp_init_offline']['f_hash'] == sc.get('f_hash'))
    # U7 com tolerância ULP-relativa float32
    s = tim['tempo_fit_s'].values + tim['tempo_busca_s'].values
    tg = tim['tempo_geracao_s'].values
    viol_ulp = int((s - tg > EPS32 * np.maximum(np.abs(tg), 1e-12)).sum())
    viol_1e6 = int((s - tg > 1e-6).sum())
    exato = int((np.abs(s - tg) <= 1e-12).sum())
    rows.append(dict(**mt, artefato=os.path.basename(usado), u2_dx=dx, u2_df=df_,
                     u2_hx=hx, u2_hf=hf, n4=len(tim),
                     u7_viol_ulp=viol_ulp, u7_viol_1e6=viol_1e6, u7_exato=exato,
                     u7_dmax=float(np.abs(s - tg).max())))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 't03_u2_u7.csv'), index=False)
n = len(df)
print('células:', n)
print('U2 ΔX bit-exato   : %d/%d' % (df.u2_dx.sum(), n))
print('U2 ΔF bit-exato   : %d/%d' % (df.u2_df.sum(), n))
print('U2 x_hash ≡ sidecar: %d/%d' % (df.u2_hx.sum(), n))
print('U2 f_hash ≡ sidecar: %d/%d' % (df.u2_hf.sum(), n))
print('artefatos distintos:', df.artefato.nunique())
print('U7 violações (ULP-relativa float32): %d de %d linhas ④' % (df.u7_viol_ulp.sum(), df.n4.sum()))
print('U7 violações (tolerância fixa 1e-6): %d de %d  -> %s'
      % (df.u7_viol_1e6.sum(), df.n4.sum(),
         df[df.u7_viol_1e6 > 0][['label', 'u7_viol_1e6', 'u7_dmax']].to_dict('records')))
print('U7 igualdade exata (|Δ|<=1e-12): %d de %d' % (df.u7_exato.sum(), df.n4.sum()))
