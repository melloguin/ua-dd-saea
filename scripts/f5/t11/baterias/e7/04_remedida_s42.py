#!/usr/bin/env python
"""T11/e7 — RE-MEDIDA das invariantes centrais na s42 (25 celulas). READ-ONLY.
Confirma (ou refuta) os numeros do relatorio F5. Saida: remedida_e7.json + remedida_e7.csv"""
import json, glob, os, re, sys
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SON = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'

linhas = []
G = {'joia_conv_ok': 0, 'joia_conv_n': 0, 'joia_inc_ok': 0, 'joia_inc_n': 0,
     'joia_popmin_ok': 0, 'joia_cru_ok': 0, 'infills_localizados': 0, 'infills_esperados': 0,
     'gatilho_ok': 0, 'ciclos': 0, 'ciclos_Xdup': 0, 'motivo_ok': 0,
     'ratio_quant_maxerr': 0.0, 'sigma_min_global': np.inf, 'sigma_nulos': 0, 'sigma_nan': 0,
     'n_std_neg': 0, 'n_dup_infill': 0, 'linhas3': 0, 'linhas3_online': 0, 'linhas3_sonda': 0,
     'linhas1': 0, 'linhas2': 0, 'linhas4': 0, 'blocos_sonda': 0,
     'ymin_maxerr': 0.0, 'ymin_n': 0, 'transf_maxerr': 0.0, 'transf_n': 0,
     'blocos_espaco_ok': 0, 'blocos_espaco_n': 0, 'blocos_fetm_ok': 0,
     'u7_viol': 0, 'u7_n': 0, 'u7_viol_sonda': 0, 'u7_blocos_com_4': 0,
     'u11_num': 0.0, 'u11_den': 0.0, 'rsid_conj_ok': 0, 'rsid_linhas': 0, 'rsid_distintos': 0,
     'contraf_inc_008': 0, 'ea_melhora': 0, 'ea_n': 0, 'bounds_fora': 0, 'bounds_n': 0,
     'nf1_h2_ok': 0, 'nf1_n': 0, 'pop_por_w_ok': 0, 'blocos1900_ok': 0}

probs = sorted(d for d in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{d}'))
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_e7_{p}_42'
    man = json.load(open(base + '.manifest.json'))
    ev = [json.loads(x) for x in open(base + '.jsonl')]
    gens = [e for e in ev if e.get('rec') == 'e7_gen']
    sond = [e for e in ev if e.get('rec') == 'sonda']
    guards = [e for e in ev if e.get('rec') == 'guard']
    foot = [e for e in ev if e.get('rec') == 'footer']
    hdr = [e for e in ev if e.get('rec') == 'header'][0]
    D, M = hdr['D'], hdr['M']
    r1 = pd.read_parquet(base + '__real.parquet')
    r2 = pd.read_parquet(base + '__pop.parquet')
    r4 = pd.read_parquet(base + '__timing.parquet')
    r3 = pd.read_parquet(base + '__surrogate.parquet')
    xc = [c for c in r1.columns if re.fullmatch(r'x\d+', c)]
    fc = [c for c in r1.columns if re.fullmatch(r'f\d+', c)]
    muc = [c for c in r3.columns if re.fullmatch(r'mu_\d+', c)]
    sgc = [c for c in r3.columns if re.fullmatch(r'sigma_\d+', c)]
    x3c = [c for c in r3.columns if re.fullmatch(r'x\d+', c)]
    n0, C = 11 * D - 1, len(gens)
    L = {'problema': p, 'D': D, 'M': M, 'C': C}

    # --- A01 orcamento
    L['fe_ok'] = (len(r1) == 31 * D - 1) and (man['maxfe'] == 31 * D - 1) and (man['fe_final'] == 31 * D - 1)
    L['fe'] = len(r1)
    L['fe_index_denso'] = bool((r1['fe_index'].to_numpy() == np.arange(len(r1))).all())
    L['sid_denso'] = bool((r1['solution_id'].to_numpy() == np.arange(len(r1))).all())
    L['n_init'] = int((r1['fase'] == 'init').sum()); L['n_opt'] = int((r1['fase'] == 'opt').sum())
    L['init_ok'] = L['n_init'] == n0 and L['n_opt'] == 20 * D
    # --- A02 DoE bit-a-bit
    doe = pd.read_parquet(f'{DOE}/{p}/doe_{p}_42.parquet')
    dxc = [c for c in doe.columns if re.fullmatch(r'x\d+', c)]
    L['doe_maxdX'] = float(np.abs(doe[dxc].to_numpy(float)[:n0] - r1[xc].to_numpy(float)[:n0]).max())
    L['doe_hash_ok'] = man['doe_hash'] == hdr['doe_hash']
    # --- A03/A16
    L['C_esperado'] = (20 * D) // 3
    L['C_ok'] = C == L['C_esperado']
    L['lote3'] = int(sum(1 for g in gens if g.get('lote') == 3 and g.get('fe_ciclo') == 3))
    L['hard_stop'] = any(g.get('name') == 'hard_stop' for g in guards)
    L['overshoot_esp'] = (3 - (20 * D) % 3) % 3
    L['hard_stop_ok'] = L['hard_stop'] == (L['overshoot_esp'] != 0)
    L['cache_hits'] = man['cache_hits']
    L['cache_hit_fe1'] = any(g.get('name') == 'cache_hit' and g.get('fe') == 1 and g.get('solution_id') == 0 for g in guards)
    # --- A04 gatilho
    ok = 0; mv = 0; quant = 0.0
    for g in gens:
        d = g['RatioOld'] - g['Ratio']
        if (d < g['delta']) == (g['ramo'] == 'convergencia'):
            ok += 1
        if ('< delta' in g['motivo']) == (g['ramo'] == 'convergencia'):
            mv += 1
        quant = max(quant, abs(g['Ratio'] * g['NW'] - round(g['Ratio'] * g['NW'])))
        if (g['RatioOld'] - g['Ratio']) >= 0.08:
            G['contraf_inc_008'] += 1
    L['gatilho_ok'] = ok; L['motivo_ok'] = mv; L['ratio_quant_maxerr'] = quant
    L['NW'] = gens[0]['NW']; L['NW_ok'] = all(g['NW'] == L['NW'] for g in gens)
    L['ramo_conv'] = sum(1 for g in gens if g['ramo'] == 'convergencia')
    L['ramo_inc'] = C - L['ramo_conv']
    G['gatilho_ok'] += ok; G['motivo_ok'] += mv; G['ciclos'] += C
    G['ratio_quant_maxerr'] = max(G['ratio_quant_maxerr'], quant)
    # --- A06 pop_por_w
    L['pop_por_w_ok'] = int(sum(1 for g in gens if len(g['pop_por_w']) == 19 and set(g['pop_por_w']) == {100}))
    G['pop_por_w_ok'] += L['pop_por_w_ok']
    # --- A14/A24/A20/A15
    L['n_treino_ok'] = int(sum(1 for g in gens if g['n_treino'] == n0))
    L['fetm_ok'] = int(sum(1 for c, g in enumerate(gens, 1) if g['fe_treino_max'] == n0 + 3 * (c - 1) - 1))
    L['fe_ciclo_ok'] = int(sum(1 for c, g in enumerate(gens, 1) if g['fe'] == n0 + 3 * c))
    L['n_std_neg'] = int(sum(g['n_std_neg'] for g in gens))
    L['n_dup_infill'] = int(sum(g['n_dup_infill'] for g in gens))
    L['dist_min_pos'] = int(sum(1 for g in gens for v in g['dist_min_arquivo'] if v > 0))
    L['dist_min_glob'] = float(min(v for g in gens for v in g['dist_min_arquivo']))
    G['n_std_neg'] += L['n_std_neg']; G['n_dup_infill'] += L['n_dup_infill']
    # --- A13 cadeia ymin
    err = 0.0; n = 0
    for c in range(len(gens) - 1):
        a = np.array(gens[c + 1]['ymin'], float); b = np.array(gens[c]['f_best'], float)
        err = max(err, float(np.abs(a - b).max())); n += 1
    L['ymin_maxerr'] = err; L['ymin_n'] = n
    G['ymin_maxerr'] = max(G['ymin_maxerr'], err); G['ymin_n'] += n
    L['ymin_c1_zero'] = bool(np.all(np.array(gens[0]['ymin'], float) == 0))
    # --- A10/A08/A07 echo
    hp = [g['modelo_hp'] for g in gens]
    L['neuronN_ok'] = all(h['neuronN'] == 40 for h in hp)
    L['dropP_ok'] = all(h['dropP'] == [0.1, 0.1] for h in hp)
    L['T_ok'] = all(h['T'] == 100 for h in hp)
    L['batch_ok'] = all(h['batchsize'] == D for h in hp)
    L['passos_ok'] = all(h['passos_init'] == 80000 and h['passos_update'] == 8000 for h in hp)
    L['lr_wd_ok'] = all(h['learnR'] == 0.01 and h['decay_efetivo'] == 1e-5 for h in hp)
    L['loss_treino_val'] = hp[0].get('loss_treino')
    # --- A09 razao 80k/8k
    g1 = gens[0]
    L['razao_fit'] = float(g1['tempo_fit_inicial_s'] / g1['tempo_fit_s'])
    L['fit_ini_so_g1'] = not any('tempo_fit_inicial_s' in g for g in gens[1:])
    # --- camada 3
    G['linhas3'] += len(r3)
    r3['_g'] = r3['geracao'].astype('float64')
    on = r3[r3.regime == 'online']; so = r3[r3.regime == 'sonda']
    G['linhas3_online'] += len(on); G['linhas3_sonda'] += len(so)
    G['linhas1'] += len(r1); G['linhas2'] += len(r2); G['linhas4'] += len(r4)
    L['l3_online'] = len(on); L['l3_sonda'] = len(so)
    L['online_1900xC'] = len(on) == 1900 * C
    sg = r3[sgc].to_numpy(float)
    L['sigma_min'] = float(np.nanmin(sg)); L['sigma_nulos'] = int((sg == 0).sum()); L['sigma_nan'] = int(np.isnan(sg).sum())
    G['sigma_min_global'] = min(G['sigma_min_global'], L['sigma_min'])
    G['sigma_nulos'] += L['sigma_nulos']; G['sigma_nan'] += L['sigma_nan']
    L['transf_tipo_unico'] = list(pd.unique(r3['transf_tipo'].dropna()))
    L['modelo_flag_unico'] = list(pd.unique(r3['modelo_flag'].dropna()))
    L['pred_nulos'] = bool(r3['pred_classe'].isna().all() and r3['pred_score'].isna().all())
    # espaco_modelo por bloco
    bl = r3.groupby(['regime', '_g'], dropna=True)
    nb = 0; okb = 0; okf = 0
    for (rg, gg), sub in bl:
        nb += 1
        esp = set(sub['espaco_modelo'].dropna().unique())
        alvo = {'cru'} if gg == 1 else {'transformado'}
        if esp == alvo:
            okb += 1
        if sub['fe_treino_max'].nunique(dropna=True) <= 1:
            okf += 1
    L['blocos_espaco_n'] = nb; L['blocos_espaco_ok'] = okb; L['blocos_fetm_ok'] = okf
    G['blocos_espaco_n'] += nb; G['blocos_espaco_ok'] += okb; G['blocos_fetm_ok'] += okf
    # transf_params (3) x ymin (6)
    er = 0.0; nn = 0
    for (rg, gg), sub in bl:
        tp = sub['transf_params'].dropna()
        if not len(tp) or pd.isna(gg):
            continue
        c = int(gg)
        if c > len(gens):
            continue
        try:
            ym = np.array(json.loads(tp.iloc[0])['ymin'], float)
        except Exception:
            continue
        er = max(er, float(np.abs(ym - np.array(gens[c - 1]['ymin'], float)).max())); nn += 1
    L['transf_maxerr'] = er; L['transf_n'] = nn
    G['transf_maxerr'] = max(G['transf_maxerr'], er); G['transf_n'] += nn
    # --- bounds
    lo = np.array([man['params'].get('lb', [])], float) if False else None
    xs = on[x3c].to_numpy(float)
    G['bounds_n'] += xs.size
    # --- A17 cadencia
    Gs = C + (1 if L['hard_stop'] else 0)
    esperado = sorted({1} | {g for g in range(2, Gs + 1) if g % 2 == 0} | {Gs})
    obs = sorted(int(s['geracao']) for s in sond)
    L['cadencia_ok'] = obs == esperado
    L['n_blocos_sonda'] = len(sond); L['Gstart'] = Gs
    L['finalProbe'] = Gs % 2 == 1
    L['sonda_2000'] = all(s['n_pontos'] == 2000 for s in sond) and all(s['ok'] for s in sond)
    G['blocos_sonda'] += len(sond)
    # join posicional sonda x gabarito
    sonart = pd.read_parquet(f'{SON}/sonda_{p}.parquet')
    sxc = [c for c in sonart.columns if re.fullmatch(r'x\d+', c)]
    gab = sonart[sxc].to_numpy(float)[:2000]
    mx = 0.0; nbl = 0
    for gg, sub in so.groupby('_g', dropna=False):
        A = sub[x3c].to_numpy(float)
        if A.shape[0] == 2000:
            mx = max(mx, float(np.abs(A - gab).max())); nbl += 1
    L['sonda_join_maxdX'] = mx; L['sonda_blocos_2000'] = nbl
    # --- U7 timing
    t = r4.dropna(subset=['tempo_geracao_s'])
    v1 = int(((t['tempo_fit_s'].fillna(0) + t['tempo_busca_s'].fillna(0)) > t['tempo_geracao_s']).sum())
    v2 = int(((t['tempo_fit_s'].fillna(0) + t['tempo_busca_s'].fillna(0) + t['tempo_pred_sonda_s'].fillna(0)) > t['tempo_geracao_s']).sum())
    L['u7_viol'] = v1; L['u7_viol_sonda'] = v2; L['u7_n'] = len(t)
    G['u7_viol'] += v1; G['u7_viol_sonda'] += v2; G['u7_n'] += len(t)
    L['l4_dup_g1'] = int((r4['geracao'] == 1).sum())
    L['l4_eq_C1'] = len(r4) == C + 1
    L['n_ger_man'] = man['n_geracoes']
    # --- A22 camada 2
    g2 = r2.groupby('geracao').size()
    L['l2_ger'] = len(g2)
    L['l2_formula_ok'] = bool(all(g2.get(g, -1) == n0 + 3 * (g - 1) for g in g2.index))
    # --- A19 QUERY-JOIA (casamento por CONJUNTO de X, versao definitiva)
    X1 = r1[xc].to_numpy(np.float32)
    onX = on[x3c].to_numpy(np.float32)
    onMU = on[muc].to_numpy(float); onSG = on[sgc].to_numpy(float)
    ymins = [np.array(g['ymin'], float) for g in gens]
    cnv_ok = inc_ok = cnv_n = inc_n = 0; pm_ok = cru_ok = 0; loc = 0; esp = 0; xdup = 0
    for c, g in enumerate(gens, 1):
        i0 = n0 + 3 * (c - 1)
        ids = list(range(i0, i0 + 3))
        if ids[-1] >= len(r1):
            continue
        esp += 3
        # pop final = ultimas 100 linhas do bloco de 1900 do ciclo c
        s = (c - 1) * 1900
        blkX = onX[s + 1800: s + 1900]; blkMU = onMU[s + 1800: s + 1900]; blkSG = onSG[s + 1800: s + 1900]
        if blkX.shape[0] != 100:
            continue
        keys = [blkX[i].tobytes() for i in range(100)]
        if len(set(keys)) < 100:
            xdup += 1
        alvo = {X1[i].tobytes() for i in ids}
        idx = [i for i, k in enumerate(keys) if k in alvo]
        loc += len({k for k in keys if k in alvo} & alvo) and len(alvo & set(keys))
        norm = np.linalg.norm(blkMU, axis=1)
        sbar = blkSG.mean(axis=1)
        if g['ramo'] == 'convergencia':
            cnv_n += 1
            if int(np.argmin(norm)) in idx:
                cnv_ok += 1
            # refutadores
            pm = blkMU - blkMU.min(axis=0)
            if int(np.argmin(np.linalg.norm(pm, axis=1))) in idx:
                pm_ok += 1
            cr = blkMU + ymins[c - 1]
            if int(np.argmin(np.linalg.norm(cr, axis=1))) in idx:
                cru_ok += 1
        else:
            inc_n += 1
            if int(np.argmax(sbar)) in idx:
                inc_ok += 1
    L['joia_conv'] = f'{cnv_ok}/{cnv_n}'; L['joia_inc'] = f'{inc_ok}/{inc_n}'
    L['joia_popmin'] = f'{pm_ok}/{cnv_n}'; L['joia_cru'] = f'{cru_ok}/{cnv_n}'
    L['ciclos_Xdup'] = xdup
    G['joia_conv_ok'] += cnv_ok; G['joia_conv_n'] += cnv_n
    G['joia_inc_ok'] += inc_ok; G['joia_inc_n'] += inc_n
    G['joia_popmin_ok'] += pm_ok; G['joia_cru_ok'] += cru_ok
    G['infills_localizados'] += loc; G['infills_esperados'] += esp; G['ciclos_Xdup'] += xdup
    # --- A27 real_solution_id
    rs = on['real_solution_id'].dropna().astype(np.int64)
    L['rsid_linhas'] = int(len(rs)); L['rsid_distintos'] = int(rs.nunique())
    L['rsid_sonda'] = int(so['real_solution_id'].notna().sum())
    conj_ok = 0
    for c in range(1, C + 1):
        s = (c - 1) * 1900
        sub = on['real_solution_id'].to_numpy()[s:s + 1900]
        obsv = set(int(v) for v in sub[~pd.isna(sub)])
        if obsv == set(range(n0 + 3 * (c - 1), n0 + 3 * c)):
            conj_ok += 1
    L['rsid_conj_ok'] = conj_ok
    G['rsid_conj_ok'] += conj_ok; G['rsid_linhas'] += L['rsid_linhas']; G['rsid_distintos'] += L['rsid_distintos']
    # --- U11 fantasia
    fs = r1[fc].to_numpy(float)
    num = den = 0.0
    onr = on['real_solution_id'].to_numpy()
    for c in range(1, C + 1):
        s = (c - 1) * 1900
        sub = onr[s:s + 1900]
        for j in np.where(~pd.isna(sub))[0]:
            sid = int(sub[j])
            mu = onMU[s + j] + ymins[c - 1]
            num += float(np.abs(mu - fs[sid]).sum()); den += float(np.abs(fs[sid]).sum())
    L['u11_wape'] = num / den if den else None
    G['u11_num'] += num; G['u11_den'] += den
    # --- 6.3 EA interno evolui
    mel = 0
    for c in range(1, C + 1):
        s = (c - 1) * 1900
        a = np.linalg.norm(onMU[s:s + 100], axis=1).mean()
        b = np.linalg.norm(onMU[s + 1800:s + 1900], axis=1).mean()
        if b < a:
            mel += 1
    L['ea_melhora'] = mel; G['ea_melhora'] += mel; G['ea_n'] += C
    # --- A21 sem warm-start
    inter = 0
    for c in range(2, C + 1):
        s = (c - 1) * 1900
        novo = {onX[s + i].tobytes() for i in range(100)}
        ant = {onX[s - 1900 + i].tobytes() for i in range(1900)}
        inter += len(novo & ant)
    L['warm_inter'] = inter
    # --- A26 n_front1 (H2)
    def nd(Y):
        n = len(Y); m = np.ones(n, bool)
        for i in range(n):
            if not m[i]:
                continue
            d = np.all(Y <= Y[i], 1) & np.any(Y < Y[i], 1)
            if d.any():
                m[i] = False
        return int(m.sum())
    h2 = 0
    for c, g in enumerate(gens, 1):
        k = n0 + 3 * c
        if k <= len(fs) and nd(fs[:k]) == g['n_front1']:
            h2 += 1
    L['nf1_h2'] = h2; G['nf1_h2_ok'] += h2; G['nf1_n'] += C
    L['termino'] = foot[0]['termino'] if foot else None
    L['status'] = man['status']; L['n_retries'] = man['n_retries']
    L['rss_max'] = float(max(g['rss_mb'] for g in gens))
    L['wall_s'] = man['timing']['tempo_total_s']
    L['t_busca'] = man['timing']['tempo_busca_s']; L['t_fit'] = man['timing']['tempo_fit_surrogate_s']
    L['t_sonda'] = man['timing']['tempo_pred_sonda_s']; L['t_aval'] = man['timing']['tempo_aval_real_s']
    L['tempo_por_ciclo'] = L['wall_s'] / C
    linhas.append(L)
    print(f"[{p}] D={D} M={M} C={C} joia={L['joia_conv']}|{L['joia_inc']} gat={ok}/{C} fe={L['fe']}", flush=True)

df = pd.DataFrame(linhas)
df.to_csv(f'{OUT}/remedida_e7.csv', index=False)
G['sigma_min_global'] = float(G['sigma_min_global'])
G['u11_wape_global'] = G['u11_num'] / G['u11_den']
json.dump({'global': G, 'celulas': len(df)}, open(f'{OUT}/remedida_e7.json', 'w'), indent=1, default=str)
print(json.dumps(G, indent=1, default=str))
