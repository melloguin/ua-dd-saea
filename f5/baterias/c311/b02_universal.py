"""B02 — bateria universal U1-U12 + módulo de família offline/treed, nas 54 células."""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

DSDIR = os.path.join(REPO, 'data', 'datasets')
SODIR = os.path.join(REPO, 'data', 'sonda')

def ds_path(prob, tier, dist):
    if tier == 'small' and dist == 'lhs':
        return os.path.join(DSDIR, prob, f'ds_{prob}_42.parquet')
    return os.path.join(DSDIR, prob, f'ds_{prob}_42_{tier}_{dist}.parquet')

rows = []
blocos = []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref)
    mt = meta(label, man)
    real, sur, tim, fin, pop = dfs['real'], dfs['surrogate'], dfs['timing'], dfs['final'], dfs['pop']
    Xc = xcols(real); Fc = fcols(real); D = len(Xc); M = len(Fc); N = len(real)
    bu = busca(sur); so = sonda(sur)
    dec = [e for e in evs if e.get('rec') == 'decision']
    son = [e for e in evs if e.get('rec') == 'sonda']
    I_eff = len(dec)
    r = dict(**mt, D=D, M=M, N=N, I_eff=I_eff)

    # ---------- U1 : orçamento = dataset, zero FE na busca ----------
    r['U1_n_real'] = N
    r['U1_fe_ok'] = bool(man['fe_final'] == man['maxfe'] == N)
    r['U1_fase_init'] = float((real['fase'] == 'init').mean())
    r['U1_feindex_denso'] = bool((real['fe_index'].values == np.arange(N)).all())
    r['U1_solid_unico'] = bool(real['solution_id'].nunique() == N)
    r['U1_tempo_aval_real'] = man['timing']['tempo_aval_real_s']
    r['U1_N_esperado'] = {'small': 31 * D - 1, 'medium': 2000, 'big': 50000}[mt['tier']]
    r['U1_N_ok'] = bool(N == r['U1_N_esperado'])

    # ---------- U2 : proveniência do dataset (hash + ΔX bit-a-bit) ----------
    p = ds_path(mt['problema'], mt['tier'], mt['dist'])
    r['U2_ds_existe'] = os.path.exists(p)
    if os.path.exists(p):
        ds = pd.read_parquet(p)
        dsX = [c for c in ds.columns if c in Xc]
        A = ds[Xc].values.astype(np.float32) if set(Xc) <= set(ds.columns) else None
        if A is not None and len(A) == N:
            B = real[Xc].values.astype(np.float32)
            r['U2_dX_bitexato'] = bool((A == B).all())
            r['U2_dX_max'] = float(np.abs(A.astype(np.float64) - B.astype(np.float64)).max())
            AF = ds[Fc].values.astype(np.float32); BF = real[Fc].values.astype(np.float32)
            r['U2_dF_bitexato'] = bool((AF == BF).all())
        dm = json.load(open(p.replace('.parquet', '.manifest.json')))
        r['U2_hash_x_sidecar'] = dm.get('x_hash')
        r['U2_hash_x_manifesto'] = man['cp_init_offline']['x_hash']
        r['U2_hash_x_ok'] = (dm.get('x_hash') == man['cp_init_offline']['x_hash'])
        r['U2_hash_f_ok'] = (dm.get('f_hash') == man['cp_init_offline']['f_hash'])
        r['U2_doe_hash_eq_x'] = (man.get('doe_hash') == man['cp_init_offline']['x_hash'])

    # ---------- U3 : 1 fit por retreino (④ == I_eff == fit_series) ----------
    r['U3_n_timing'] = len(tim)
    r['U3_ok'] = bool(len(tim) == I_eff == len(man['fit_series']))
    r['U3_ger_timing'] = ';'.join(str(int(x)) for x in tim['geracao'].values[:6])
    r['U3_ger_51i'] = bool((tim['geracao'].values == np.arange(1, I_eff + 1) * 51).all())

    # ---------- U4 : sonda offline = 2 blocos de 20.000 ----------
    r['U4_n_ev_sonda'] = len(son)
    r['U4_n_pontos'] = ';'.join(str(e.get('n_pontos')) for e in son)
    r['U4_flags'] = ';'.join(str(e.get('modelo_flag')) for e in son)
    r['U4_hash_ok'] = all(str(e.get('hash_check', '')).startswith('ok') for e in son)
    r['U4_ger_null'] = bool(so['geracao'].isna().all())
    r['U4_len'] = len(so)
    r['U4_ok'] = bool(len(son) == 2 and len(so) == 40000 and r['U4_hash_ok']
                      and [e.get('modelo_flag') for e in son] == ['treedGP_build', 'treedGP_final'])
    r['U4_tempo_pred'] = sum(float(e.get('tempo_pred_sonda_s') or 0) for e in son)

    # ---------- U5 : join posicional sonda x gabarito ----------
    gp = os.path.join(SODIR, f'sonda_{mt["problema"]}.parquet')
    gm = json.load(open(gp.replace('.parquet', '.manifest.json')))
    gab = pd.read_parquet(gp)
    G = gab[Xc].values.astype(np.float64)
    S1 = so[Xc].values[:20000].astype(np.float64)
    S2 = so[Xc].values[20000:].astype(np.float64)
    r['U5_dX_blk0'] = float(np.abs(G - S1).max())
    r['U5_dX_blk1'] = float(np.abs(G - S2).max())
    r['U5_dX_ulp_ok'] = bool(r['U5_dX_blk0'] <= np.abs(G).max() * 1.2e-7 + 1e-9)
    r['U5_hash_gab'] = gm['x_hash']
    r['U5_hash_ev'] = son[0].get('sonda_x_hash') if son else None
    r['U5_hash_eq'] = (gm['x_hash'] == man['sonda']['x_hash'])
    # ---------- U6 : WAPE + cobertura por bloco (espaço CRU) ----------
    GF = gab[Fc].values.astype(np.float64)
    mus = mucols(so); sgs = sigcols(so)
    r['U6_espaco'] = str(so['espaco_modelo'].iloc[0]); r['U6_transf'] = str(so['transf_tipo'].iloc[0])
    for b, (lo, hi) in enumerate([(0, 20000), (20000, 40000)]):
        sub = so.iloc[lo:hi]
        for j in range(M):
            mu = sub[mus[j]].values.astype(np.float64); f = GF[:, j]
            sg = sub[sgs[j]].values.astype(np.float64) if j < len(sgs) else np.full(len(sub), np.nan)
            den = np.abs(f).sum()
            wape = float(np.abs(mu - f).sum() / den) if den > 0 else np.nan
            val = ~np.isnan(sg)
            cov = float((np.abs(mu[val] - f[val]) <= 1.96 * sg[val]).mean()) if val.sum() else np.nan
            ok = ~np.isnan(mu)
            corr = float(np.corrcoef(mu[ok], f[ok])[0, 1]) if ok.sum() > 2 and np.std(mu[ok]) > 0 else np.nan
            blocos.append(dict(**mt, bloco=b, obj=j, D=D, M=M, N=N, I_eff=I_eff,
                               wape=wape, corr=corr, cobertura95=cov,
                               n_sigma_valido=int(val.sum()), nan_share=float(np.isnan(sg).mean()),
                               mu_min=float(np.nanmin(mu)), mu_max=float(np.nanmax(mu)),
                               f_min=float(f.min()), f_max=float(f.max()),
                               mae=float(np.abs(mu - f).mean()),
                               mae_ref=float(np.abs(f - f.mean()).mean())))

    # ---------- F1 : bit-identidade dos 2 blocos (modelo CONGELADO) ----------
    cols = Xc + mus + sgs
    A = so.iloc[:20000][cols].values; B = so.iloc[20000:][cols].values
    eq = (A == B) | (np.isnan(A.astype(np.float64)) & np.isnan(B.astype(np.float64)))
    r['F1_bit_identico'] = bool(eq.all())
    r['F1_n_diff'] = int((~eq).sum())

    # ---------- F2 : σ NaN-share por fase / regime ----------
    gg = bu['geracao'].astype(float)
    pre = bu[gg <= 50]; bld = bu[bu['modelo_flag'] == 'treedGP_build']; fnl = bu[bu['modelo_flag'] == 'treedGP_final']
    def nsh(df):
        s = sigcols(df)
        return float(df[s].isna().values.mean()) if len(df) and s else np.nan
    r['F2_nan_pre50'] = nsh(pre); r['F2_nan_build'] = nsh(bld); r['F2_nan_final'] = nsh(fnl)
    r['F2_nan_sonda_b0'] = float(so.iloc[:20000][sgs].isna().values.mean())
    r['F2_nan_sonda_b1'] = float(so.iloc[20000:][sgs].isna().values.mean())
    r['F2_nan_busca'] = nsh(bu)

    # ---------- U7 : invariante dupla do timing ----------
    fb = tim['tempo_fit_s'].values + tim['tempo_busca_s'].values
    tg = tim['tempo_geracao_s'].values
    ps = tim['tempo_pred_sonda_s'].values if 'tempo_pred_sonda_s' in tim.columns else np.zeros(len(tim))
    r['U7_viol'] = int((fb - tg > 1e-6).sum())
    r['U7_viol_com_sonda'] = int((fb + ps - tg > 1e-6).sum())
    r['U7_linhas_com_sonda'] = int((ps > 0).sum())
    r['U7_idx_viol_sonda'] = ';'.join(str(i) for i in np.where(fb + ps - tg > 1e-6)[0])
    r['U7_ok'] = bool(r['U7_viol'] == 0 and r['U7_viol_com_sonda'] == r['U7_linhas_com_sonda'])
    r['U7_folga_med'] = float(np.median(tg - fb))
    r['U7_fit_total'] = float(tim['tempo_fit_s'].sum())
    r['U7_busca_total'] = float(tim['tempo_busca_s'].sum())

    # ---------- U8 : fe_treino_max ----------
    u = bu['fe_treino_max'].dropna().unique()
    r['U8_valores'] = ';'.join(str(int(x)) for x in u[:4])
    r['U8_ok'] = bool(len(u) == 1 and int(u[0]) == N - 1)

    # ---------- U9 : guards / cache ----------
    gu = [e for e in evs if e.get('rec') == 'guard']
    r['U9_n_guard'] = len(gu)
    r['U9_cache_manifest'] = man.get('cache_hits')
    fr = [e for e in evs if e.get('rec') == 'footer' and 'n_final' in e]
    r['U9_cache_footer'] = fr[0].get('cache_hits') if fr else None
    r['U9_ok'] = bool((man.get('cache_hits') or 0) == 0 and (not fr or (fr[0].get('cache_hits') or 0) == 0))

    # ---------- U10 : aritmética entre camadas ----------
    r['U10_ngen'] = man['n_geracoes']
    r['U10_esperado'] = 51 * I_eff + 1000
    r['U10_ok'] = bool(man['n_geracoes'] == 51 * I_eff + 1000)
    r['U10_ok_footer'] = bool((not fr) or fr[0].get('n_geracoes') == man['n_geracoes'])

    # ---------- U11 / família : ② vazia, real_solution_id NULL ----------
    r['U11_pop_linhas'] = 0 if pop is None else len(pop)
    r['U11_rsid_naonulo'] = int(sur['real_solution_id'].notna().sum())
    r['U11_ok'] = bool(r['U11_pop_linhas'] == 0 and r['U11_rsid_naonulo'] == 0)

    # ---------- U12 : ⑦ recomputo do Pareto + link posicional ----------
    Ff = fin[Fc].values.astype(np.float64)
    keep = nd_mask(Ff)
    ndp = fin['nd_pos_real'].values.astype(bool)
    r['U12_nd_ok'] = bool((keep == ndp).all())
    r['U12_n_final'] = len(fin); r['U12_n_nd'] = int(ndp.sum())
    r['U12_razao_fantasia'] = float(ndp.mean())
    og = fin['origem_geracao'].values
    r['U12_origem_unica'] = bool(len(set(og.tolist())) == 1)
    r['U12_origem_ger'] = int(og[0]); r['U12_origem_eq_ultima'] = bool(int(og[0]) == man['n_geracoes'])
    ult = bu[bu['geracao'] == man['n_geracoes']]
    r['U12_pop_ultima'] = len(ult)
    r['U12_nfinal_eq_pop'] = bool(len(ult) == len(fin))
    if len(ult) == len(fin):
        XA = ult[Xc].values.astype(np.float32)
        ol = fin['origem_linha'].values.astype(int)
        XB = fin[Xc].values.astype(np.float32)
        r['U12_link_bit'] = bool((XA[ol] == XB).all())
        r['U12_link_dmax'] = float(np.abs(XA[ol].astype(np.float64) - XB.astype(np.float64)).max())
    r['U12_footer_nfinal_ok'] = bool((not fr) or (fr[0].get('n_final') == len(fin)
                                                  and fr[0].get('n_nd_pos_real') == int(ndp.sum())))
    r['U12_osid_null'] = int(fin['origem_solution_id'].notna().sum()) if 'origem_solution_id' in fin.columns else -1
    rows.append(r)
    print(label, 'ok')

u = pd.DataFrame(rows); salva(u, 'b02_universal.csv')
b = pd.DataFrame(blocos); salva(b, 'b02_sonda_blocos.csv')
for c_ in [c for c in u.columns if c.endswith('_ok') or c.endswith('_bit') or c.endswith('_identico')]:
    try:
        print(c_, int(u[c_].sum()), '/', len(u))
    except Exception:
        pass
