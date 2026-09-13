#!/usr/bin/env python
"""B02 — bateria universal U1-U11 do protocolo v1.1, nas 25 celulas main do c141."""
import json, os, sys, hashlib
import numpy as np
import pandas as pd
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_c141 import load, ROOT

OUT = os.path.dirname(os.path.abspath(__file__))
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SND = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
EPS32 = np.finfo(np.float32).eps

rows = []
for pb in sorted(os.listdir(ROOT)):
    man, ev, real, pop, sur, tim = load(pb)
    hdr = [e for e in ev if e.get('rec') == 'header'][0]
    ftr = [e for e in ev if e.get('rec') == 'footer']
    ftr = ftr[0] if ftr else {}
    D, M = hdr['D'], hdr['M']
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    mc = [f'mu_{i}' for i in range(M)]
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    sondas = [e for e in ev if e.get('rec') == 'sonda']
    guards = [e for e in ev if e.get('rec') == 'guard']
    gcnt = Counter(g['name'] for g in guards)
    on = sur[sur.regime == 'online']
    so = sur[sur.regime == 'sonda']
    r = dict(problema=pb, D=D, M=M)

    # ---- U1: FE = 31D-1, fe_index denso 0-based ----
    r['U1_maxfe_ok'] = (man['maxfe'] == 31 * D - 1) and (man['fe_final'] == 31 * D - 1) and (len(real) == 31 * D - 1)
    r['U1_denso'] = bool((real.fe_index.values == np.arange(len(real))).all())
    r['U1_sid_denso'] = bool((real.solution_id.values == np.arange(len(real))).all())
    r['U1_fases'] = ';'.join(f'{k}={v}' for k, v in Counter(real.fase).items())

    # ---- U2: init 11D-1 + DoE bit-a-bit contra o artefato ----
    ini = real[real.fase == 'init']
    r['U2_n_init'] = len(ini)
    r['U2_init_ok'] = len(ini) == 11 * D - 1
    doe = pd.read_parquet(os.path.join(DOE, pb, f'doe_{pb}_42.parquet'))
    dman = json.load(open(os.path.join(DOE, pb, f'doe_{pb}_42.manifest.json')))
    dcols = [c for c in doe.columns if c.startswith('x')]
    A = ini[xc].values.astype(np.float64)
    B = doe[dcols].values.astype(np.float64)
    r['U2_shape_ok'] = A.shape == B.shape
    r['U2_dX_max'] = float(np.abs(A - B).max()) if A.shape == B.shape else np.nan
    r['U2_bitexato'] = bool((ini[xc].values.astype(np.float32) == doe[dcols].values.astype(np.float32)).all()) if A.shape == B.shape else False
    r['U2_hash_manifesto'] = man['doe_hash']
    r['U2_hash_sidecar'] = dman.get('doe_hash')
    r['U2_hash_ok'] = r['U2_hash_manifesto'] == r['U2_hash_sidecar']
    r['U2_cp_init'] = ftr.get('cp_init')

    # ---- U3: 1 fit por retreino no ④ ----
    r['U3_n_timing'] = len(tim)
    r['U3_n_gen_ev'] = len(gens)
    r['U3_ok'] = len(tim) == len(gens) == len(man['fit_series'])
    r['U3_fit_notna'] = int(tim.tempo_fit_s.notna().sum())
    r['U3_ger_seq'] = bool((tim.geracao.values == np.arange(1, len(tim) + 1)).all())

    # ---- U4: cadencia da sonda ----
    gsond = sorted(s['geracao'] for s in sondas)
    ngmax = man['n_geracoes']
    esperado = [g for g in range(1, ngmax + 1) if g == 1 or g % 2 == 0]
    if ngmax % 2 == 1 and ngmax not in esperado:
        esperado.append(ngmax)
    r['U4_gens_sonda'] = len(gsond)
    r['U4_cadencia_ok'] = gsond == sorted(esperado)
    r['U4_ultima_coberta'] = ngmax in gsond
    r['U4_n_blocos_man'] = man['sonda']['n_blocos']
    r['U4_blocos_ok'] = man['sonda']['n_blocos'] == len(gsond) == so.geracao.nunique()
    r['U4_linhas_ok'] = len(so) == 2000 * len(gsond) == man['sonda']['n_linhas']
    r['U4_por_bloco_2000'] = bool((so.groupby('geracao').size() == 2000).all())
    r['U4_motivos'] = ';'.join(sorted(set(s.get('motivo', '?') for s in sondas)))
    r['U4_falhas'] = man['sonda']['n_falhas']

    # ---- U5: join posicional sonda x gabarito ----
    gab = pd.read_parquet(os.path.join(SND, f'sonda_{pb}.parquet'))
    gxc = [c for c in gab.columns if c.startswith('x') and c[1:].isdigit()]
    gfc = [c for c in gab.columns if c.startswith('f') and c[1:].isdigit()]
    G = gab[gxc].values.astype(np.float64)[:2000]
    dmax = 0.0
    for gnum, blk in so.groupby('geracao'):
        dmax = max(dmax, float(np.abs(blk[xc].values.astype(np.float64) - G).max()))
    r['U5_dX_max'] = dmax
    r['U5_ok'] = dmax <= EPS32
    sman = json.load(open(os.path.join(SND, f'sonda_{pb}.manifest.json')))
    r['U5_xhash_ok'] = all(s.get('x_hash') == man['sonda']['x_hash'] for s in sondas) and \
        man['sonda']['x_hash'] == sman['x_hash_online']
    r['U5_S_online'] = sman['S_online']

    # ---- U6: WAPE por bloco (espaco cru; transf_tipo NULL => sem transformacao) ----
    Fg = gab[gfc].values.astype(np.float64)[:2000]
    wl = []
    for gnum, blk in so.groupby('geracao'):
        mu = blk[mc].values.astype(np.float64)
        w = np.abs(mu - Fg).sum(0) / np.abs(Fg).sum(0)
        cr = [float(np.corrcoef(mu[:, j], Fg[:, j])[0, 1]) for j in range(M)]
        wl.append((gnum, w, cr))
    r['U6_wape_1o'] = float(np.mean(wl[0][1]))
    r['U6_wape_ult'] = float(np.mean(wl[-1][1]))
    r['U6_dwape_pct'] = 100 * (r['U6_wape_ult'] / r['U6_wape_1o'] - 1)
    r['U6_corr_1o'] = float(np.mean(wl[0][2]))
    r['U6_corr_ult'] = float(np.mean(wl[-1][2]))
    r['U6_wape_min'] = float(min(np.mean(w) for _, w, _ in wl))
    r['U6_wape_max'] = float(max(np.mean(w) for _, w, _ in wl))
    r['U6_transf'] = ';'.join(map(str, so.transf_tipo.unique()))
    r['U6_cobertura'] = 'N/A (sigma_0/sigma_1 = incerteza de ensemble, nao desvio-padrao preditivo por objetivo)'

    # ---- U7: fit + busca <= tempo_geracao_s ----
    v = tim.tempo_fit_s + tim.tempo_busca_s - tim.tempo_geracao_s
    r['U7_viol'] = int((v > 1e-6).sum())
    r['U7_n'] = len(tim)
    vi = set(tim.geracao[v > 1e-6])
    r['U7_viol_em_sonda'] = len(vi & set(gsond))
    r['U7_folga_med'] = float((-v).median())
    # sonda contabilizada a parte
    v2 = tim.tempo_fit_s + tim.tempo_busca_s + tim.tempo_pred_sonda_s - tim.tempo_geracao_s
    r['U7_viol_com_sonda'] = int((v2 > 1e-6).sum())

    # ---- U8: fe_treino_max ----
    fem = np.array([g['fe_treino_max'] for g in gens])
    r['U8_monotonico'] = bool((np.diff(fem) >= 0).all())
    r['U8_igual_n_menos1'] = int(sum(g['fe_treino_max'] == g['modelo_hp']['n'] - 1 for g in gens))
    r['U8_max'] = int(fem.max())
    r['U8_sonda_bate'] = int(sum(1 for s in sondas if s['fe_treino_max'] in set(fem.tolist())))

    # ---- U9: guards do ⑥ ≡ manifesto/⑤ ----
    r['U9_guards'] = json.dumps(dict(gcnt))
    r['U9_cache_ok'] = gcnt.get('cache_hit', 0) == man.get('cache_hits') == ftr.get('cache_hits')
    r['U9_cache_n'] = gcnt.get('cache_hit', 0)
    r['U9_hardstop'] = gcnt.get('hard_stop', 0)
    r['U9_eps_sde'] = gcnt.get('sde_eps', 0) + gcnt.get('nan_sde', 0) + gcnt.get('sde_nan', 0)
    r['U9_batch_vazio'] = gcnt.get('batch_vazio', 0)
    r['U9_outros'] = json.dumps({k: v for k, v in gcnt.items() if k not in ('cache_hit', 'hard_stop')})

    # ---- U10: aritmetica entre camadas ----
    lot = sum(g['lote'] for g in gens)
    r['U10_init_mais_lotes'] = 11 * D - 1 + lot
    r['U10_fe_final'] = man['fe_final']
    r['U10_resto'] = man['fe_final'] - (11 * D - 1 + lot)
    r['U10_fe_ultimo_gen'] = gens[-1]['fe']
    r['U10_n_pop'] = len(pop)
    r['U10_pop_gens'] = pop.geracao.nunique()
    r['U10_pop_por_gen_ok'] = bool((pop.groupby('geracao').size().values[:-1] > 0).all())
    r['U10_online_ok'] = len(on) == 200 * len(gens) if min(100, 11 * D - 1) == 100 else len(on) == 2 * min(100, 11 * D - 1) * len(gens)
    r['U10_pool_unico'] = ';'.join(map(str, sorted(on.groupby('geracao').size().unique())))
    # ② = uniao acumulada? tamanho por geracao
    sz = pop.groupby('geracao').size()
    r['U10_pop_sz_min'] = int(sz.min()); r['U10_pop_sz_max'] = int(sz.max())
    r['U10_pop_g1'] = int(sz.iloc[0]); r['U10_pop_glast'] = int(sz.iloc[-1])

    # ---- U11: erro de fantasia dos infills (real_solution_id -> ①) ----
    inf = on[on.real_solution_id.notna()]
    if len(inf):
        sid = inf.real_solution_id.values.astype(int)
        freal = real.set_index('solution_id').loc[sid, fc].values.astype(np.float64)
        mu = inf[mc].values.astype(np.float64)
        err = mu - freal
        r['U11_n'] = len(inf)
        r['U11_mae_med'] = float(np.median(np.abs(err)))
        r['U11_mae_max'] = float(np.abs(err).max())
        r['U11_otimista'] = float((err < 0).mean())
        r['U11_wape'] = float(np.abs(err).sum() / np.abs(freal).sum())
        # ΔX do join (deve ser 0: mesma solucao)
        xr = real.set_index('solution_id').loc[sid, xc].values.astype(np.float64)
        r['U11_dX_max'] = float(np.abs(inf[xc].values.astype(np.float64) - xr).max())
    else:
        r['U11_n'] = 0
    rows.append(r)
    print('ok', pb, flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'b02_universal.csv'), index=False)
pd.set_option('display.width', 300, 'display.max_columns', 200)
cols = [c for c in df.columns if c.startswith(('U1_', 'U2_', 'U3_', 'U4_'))]
print(df[['problema'] + cols].to_string())
print()
cols = [c for c in df.columns if c.startswith(('U5_', 'U6_', 'U7_', 'U8_'))]
print(df[['problema'] + cols].to_string())
print()
cols = [c for c in df.columns if c.startswith(('U9_', 'U10_', 'U11_'))]
print(df[['problema'] + cols].to_string())
