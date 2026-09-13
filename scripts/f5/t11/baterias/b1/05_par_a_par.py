#!/usr/bin/env python
"""Parte 5: MESMAS medidas nas DUAS execucoes da MESMA celula (main/b1/MMF1/s42):
T11-smoke (Mac) x rodada-42 (vm3). Comparacao like-for-like — o smoke tem 54
iteracoes e a R42 tem 48, entao qualquer numero AGREGADO das 23 celulas da F5
NAO e comparavel com o smoke; esta tabela e."""
import json, numpy as np, pandas as pd
from collections import Counter
from scipy.special import ndtr

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b1'
SON = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet'
BASES = {
    'T11_smoke': '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_matlab/experiments/main/b1/exp_main_b1_MMF1_42',
    'R42': '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1/MMF1/42/exp_main_b1_MMF1_42',
}
INIT, MAXFE, CAP, RHO = 21, 61, 46, 0.05
son = pd.read_parquet(SON).iloc[:2000]
fg = son[['f0', 'f1']].to_numpy(np.float64)
xg = son[['x0', 'x1']].to_numpy(np.float64)

res = {}
for tag, base in BASES.items():
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gen = [r for r in recs if r['rec'] == 'b1_gen']
    gu = [r for r in recs if r['rec'] == 'guard']
    man = json.load(open(base + '.manifest.json'))
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    G = len(gen); F = real[['f0', 'f1']].to_numpy(np.float64)
    d = {}
    d['n_iter'] = G
    d['cache_hits'] = man['cache_hits']
    d['n_blocos_sonda'] = man['sonda']['n_blocos']
    d['linhas_6'] = len(recs)
    d['malformadas_6'] = sum(1 for l in open(base + '.jsonl') if l.strip() and not l.strip().endswith('}'))
    d['footers'] = sum(1 for r in recs if r['rec'] == 'footer')
    d['schema_version'] = man.get('schema_version', 1)
    d['campanha_id'] = man.get('campanha_id', 'AUSENTE')
    d['repo_hash'] = man.get('repo_hash') or 'VAZIO'
    d['tempo_aval_real_s'] = man['timing'].get('tempo_aval_real_s')
    # U1
    d['U1_fe'] = f"{len(real)}=={MAXFE}"
    d['U1_termino'] = [r for r in recs if r['rec'] == 'footer'][0]['termino']
    # U2
    d['U2_init'] = int((real.fase == 'init').sum())
    # U9 ledger
    ch = [g for g in gu if g['name'] == 'cache_hit']
    d['U9_ledger'] = f"{G}=={MAXFE-INIT}+{len(ch)}-1={MAXFE-INIT+len(ch)-1}"
    d['N1_c0'] = sum(1 for g in ch if g['fe'] == 1)
    d['U9_dedup_ev'] = sum(1 for g in gu if g['name'] == 'dedup_treino')
    d['U9_dedup_rem'] = sum(g['n'] for g in gu if g['name'] == 'dedup_treino')
    # U8
    ftm = np.array([g['fe_treino_max'] for g in gen])
    d['U8_quedas'] = int((np.diff(ftm) < 0).sum())
    # U10
    d['U10_ger_pop'] = pop.geracao.nunique()
    ult = pop[pop.geracao == pop.geracao.max()]
    d['U10_dup_ultima'] = len(ult) - ult.solution_id.nunique()
    # F1
    mu = np.array([g['mu_best'] for g in gen]); sg = np.array([g['sigma_best'] for g in gen])
    gb = np.array([g['gbest'] for g in gen]); ei = np.array([g['ei_best'] for g in gen])
    z = (gb - mu) / sg
    EI = (gb - mu) * ndtr(z) + sg * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    rel = np.abs(EI + ei) / np.maximum(np.abs(ei), 1e-300)
    d['F1_EI_ok'] = f"{int((rel<1e-6).sum())}/{G}"
    d['F1_EI_max_rel'] = f"{rel.max():.2e}"
    # F2
    sid_por_fe = dict(zip(real.fe_index.values, real.solution_id.values))
    chfe = {}
    for g in ch: chfe.setdefault(g['fe'], set()).add(g['solution_id'])
    okn = okc = nn = nc = 0
    for i, g in enumerate(gen):
        fe = g['fe']; prev = gen[i - 1]['fe'] if i else INIT
        if fe > prev: nn += 1; okn += sid_por_fe.get(fe - 1) == g['best_sid']
        else: nc += 1; okc += g['best_sid'] in chfe.get(fe, set())
    d['F2_novo'] = f'{okn}/{nn}'; d['F2_cache'] = f'{okc}/{nc}'
    # F3/F4
    on = sur[sur.regime == 'online']
    match = ng = tot = 0; raz = []; psel = []; pgre = []
    for g in gen:
        blk = on[on.geracao == g['geracao']]
        m0 = blk.mu_0.to_numpy(np.float64); s0 = blk.sigma_0.to_numpy(np.float64)
        with np.errstate(divide='ignore', invalid='ignore'):
            zz = (g['gbest'] - m0) / s0
        e = (g['gbest'] - m0) * ndtr(zz) + s0 * np.exp(-0.5 * zz * zz) / np.sqrt(2 * np.pi)
        ia = int(np.argmax(e)); ig = int(np.argmin(m0))
        ok = abs(m0[ia] - g['mu_best']) <= 1e-6 * max(1, abs(g['mu_best'])) and abs(s0[ia] - g['sigma_best']) <= 1e-6 * max(1, abs(g['sigma_best']))
        match += ok
        if ok:
            tot += 1
            if ia != ig:
                ng += 1; raz.append(s0[ia] / s0[ig]); psel.append((s0 < s0[ia]).mean()); pgre.append((s0 < s0[ig]).mean())
    d['F3_match'] = f'{match}/{G}'
    d['F3_naogreedy'] = f'{ng}/{tot}'
    d['F3_sigma_maior'] = f'{sum(1 for r in raz if r>1)}/{len(raz)}'
    d['F3_razao_med'] = f'{np.median(raz):.3f}' if raz else 'n/a'
    d['F3_pct_sel_x_gre'] = f'{np.mean(psel):.3f} x {np.mean(pgre):.3f}' if psel else 'n/a'
    le = np.array([abs(g['e0_trace'][-1] - g['ei_best']) < 1e-12 for g in gen])
    d['F4_last_eq'] = f'{int(le.sum())}/{G}'
    d['F4_min_e0'] = f"{int(sum(abs(min(g['e0_trace'])-g['ei_best'])<1e-12 for g in gen))}/{G}"
    cst = np.array([len(set(g['e0_trace'])) == 1 for g in gen])
    d['ERRATA16_e0_const'] = f'{int(cst.sum())}/{G} = {cst.mean():.1%}'
    v1 = np.array([abs(g['e0_trace'][0] - g['ei_best']) < 1e-15 for g in gen])
    d['K3_venceu_1a_ger'] = f'{int(v1.sum())}/{G} = {v1.mean():.1%}'
    na = np.array([g['n_arquivo'] for g in gen]); nt = np.array([g['n_treino'] for g in gen])
    vivo = nt < na
    d['K3_bug_vivo'] = f'{int(vivo.sum())}/{G} = {vivo.mean():.1%}'
    d['K3_venceu1_e_vivo_naodeg'] = f'{int((v1&vivo&~cst).sum())}/{G} = {(v1&vivo&~cst).mean():.1%}'
    gp = np.array([g['ga_pop'] for g in gen]); gi = np.array([g['ga_iters'] for g in gen])
    d['K3_frac_candidatos_bugados'] = f'{(gp[vivo]/2).sum()/(gp*gi).sum():.2%}'
    # B1
    lam = np.array([g['lambda'] for g in gen])
    d['B1_grid_desvio'] = f'{np.abs(lam*99-np.round(lam*99)).max():.1e}'
    d['B1_distintos'] = len(set(map(tuple, np.round(lam * 99).astype(int))))
    d['B1_max_rep'] = max(Counter(map(tuple, np.round(lam * 99).astype(int))).values())
    # B2/B3
    okg = oknm = 0; eg = []
    for i, g in enumerate(gen):
        fe = g['fe']
        for w in (fe - 1, fe):
            Fa = F[:w]
            if np.allclose(Fa.min(0), g['norm_min'], rtol=1e-4, atol=1e-9) and np.allclose(Fa.max(0), g['norm_max'], rtol=1e-4, atol=1e-9):
                oknm += 1; break
        Fa = F[:w]; lm = np.array(g['lambda']); nmin = np.array(g['norm_min']); nmax = np.array(g['norm_max'])
        rg = np.where(nmax - nmin == 0, 1.0, nmax - nmin)
        pc = (((Fa - nmin) / rg) * lm).max(1) + RHO * (((Fa - nmin) / rg) * lm).sum(1)
        e = abs(pc.min() - g['gbest']); eg.append(e); okg += e < 1e-6
    d['B3_norm'] = f'{oknm}/{G}'; d['B2_gbest'] = f'{okg}/{G}'; d['B2_max_abs'] = f'{max(eg):.1e}'
    # B5/B7/B8
    ns = np.array([g['n_subset'] for g in gen]); nd = np.array([g['n_dedup'] for g in gen])
    d['B5_ident'] = f"{int((nt==ns-nd).sum())}/{G} e {int((ns==np.minimum(na,CAP)).sum())}/{G}"
    d['B5_satura_cap'] = f'{int((ns==CAP).sum())}/{G}'
    d['B7_ga'] = f"{int((gi==np.ceil(10000/gp)).sum())}/{G} · gap-2na={sorted(set((gp-2*na).tolist()))}"
    th = np.concatenate([np.array(g['modelo_hp']['theta']) for g in gen])
    d['B8_theta'] = f'{len(th)} comp · viol={int(((th<1e-5)|(th>20)).sum())} · sat20={int((th==20).sum())} · sat1e-5={int((th==1e-5).sum())}'
    # B6
    d['B6_guards'] = f"sig<0={int((sur.sigma_0<0).sum())} · NaN={int(sur.sigma_0.isna().sum())} · min={sur.sigma_0.min():.2e}"
    # B11/B12/B13
    dm = np.array([g['dist_min_arquivo'] for g in gen])
    isch = np.array([gen[i]['fe'] == (gen[i - 1]['fe'] if i else INIT) for i in range(G)])
    d['B11_dist0_iff_cache'] = f"{bool(((dm==0)==isch).all())} ({int(isch.sum())} iters)"
    st = mx = 0
    for v in isch: st = st + 1 if v else 0; mx = max(mx, st)
    d['B11_streak'] = mx
    d['B12_n_arquivo'] = f"{int((na==INIT+np.arange(G)).sum())}/{G}"
    kb = [r.tobytes() for r in real[['x0', 'x1']].to_numpy()]
    d['B13_dupX_f32'] = sum(v - 1 for v in Counter(kb).values() if v > 1)
    # B4
    d['B4_mu1_null'] = f"{int(sur.mu_1.isna().sum())}/{len(sur)}"
    d['B4_transf_params_ok'] = int(sur.transf_params.notna().sum()) == len(sur)
    # U11
    sid2f = dict(zip(real.solution_id.values, F))
    err = []; ot = []; dt = []; mel = 0
    for g in gen:
        f = sid2f[g['best_sid']]; lm = np.array(g['lambda'])
        nmin = np.array(g['norm_min']); nmax = np.array(g['norm_max'])
        rg = np.where(nmax - nmin == 0, 1.0, nmax - nmin); fn = (f - nmin) / rg
        pc = (fn * lm).max() + RHO * (fn * lm).sum()
        err.append(g['mu_best'] - pc); ot.append(g['mu_best'] < pc)
        dt.append(abs(g['mu_best'] - pc) <= 1.96 * g['sigma_best']); mel += pc < g['gbest']
    d['U11_err_med'] = f'{np.median(np.abs(err)):.4f}'
    d['U11_otimista'] = f'{np.mean(ot):.3f}'
    d['U11_in_2sigma'] = f'{np.mean(dt):.3f}'
    d['U11_melhora_incumbente'] = f'{mel}/{G} = {mel/G:.3f}'
    # sonda escalar
    sb = sur[sur.regime == 'sonda']
    L = []
    for gg, blk in sb.groupby('geracao'):
        blk = blk.reset_index(drop=True)
        tp = json.loads(blk.transf_params.iloc[0])
        lm = np.array(tp['lambda']); nmin = np.array(tp['min']); nmax = np.array(tp['max'])
        rg = np.where(nmax - nmin == 0, 1.0, nmax - nmin)
        pc = (((fg - nmin) / rg) * lm).max(1) + RHO * (((fg - nmin) / rg) * lm).sum(1)
        m0 = blk.mu_0.to_numpy(np.float64); s0 = blk.sigma_0.to_numpy(np.float64)
        L.append((int(gg), float(np.abs(blk[['x0','x1']].to_numpy()-xg.astype(np.float32)).max()),
                  float(np.abs(m0 - pc).sum() / np.abs(pc).sum()),
                  float((np.abs(m0 - pc) <= 1.96 * s0).mean()),
                  float(np.corrcoef(m0, pc)[0, 1]), float(np.median(s0))))
    S = pd.DataFrame(L, columns=['g', 'maxdX', 'wape', 'cob', 'corr', 'sig']).sort_values('g')
    S.to_csv(f'{OUT}/b1_sonda_{tag}.csv', index=False)
    d['U5j_maxdX_sonda'] = f'{S.maxdX.max():.1e}'
    d['U6_WAPE_1o_ult'] = f'{S.wape.iloc[0]:.4f} -> {S.wape.iloc[-1]:.4f} ({(S.wape.iloc[-1]/S.wape.iloc[0]-1)*100:+.1f}%)'
    d['F5_cob_1o_ult'] = f'{S.cob.iloc[0]:.4f} -> {S.cob.iloc[-1]:.4f}'
    d['F5_cob_min'] = f'{S.cob.min():.4f}'
    d['SONDA_corr_1o_ult'] = f'{float(S["corr"].iloc[0]):.4f} -> {float(S["corr"].iloc[-1]):.4f}'
    d['SONDA_sig_1o_ult'] = f'{S.sig.iloc[0]:.4f} -> {S.sig.iloc[-1]:.4f}'
    d['SONDA_estratificada'] = 'sonda_estratificada' in set(sur.regime)
    # real_solution_id no pool online (evidencia circunstancial K.3)
    d['pool_real_sid_frac'] = f"{on.real_solution_id.notna().mean():.4%}"
    d['F6_1o_fit_x_mediana'] = f"{tim.tempo_fit_s.values[0]/np.median(tim.tempo_fit_s.values):.1f}x"
    d['F6_frac_tempo_fit'] = f"{tim.tempo_fit_s.sum()/tim.tempo_geracao_s.sum():.3f}"
    d['tempo_total_s'] = f"{man['timing']['tempo_total_s']:.2f}"
    res[tag] = d

T = pd.DataFrame(res)
T.index.name = 'medida'
pd.set_option('display.max_colwidth', 60)
print(T.to_string())
T.to_csv(f'{OUT}/b1_par_a_par.csv')
print('\nSALVO', f'{OUT}/b1_par_a_par.csv')
