#!/usr/bin/env python
"""T11/e7 — as invariantes centrais valem no CORPUS NOVO (smoke T11)? READ-ONLY."""
import json, re
import numpy as np, pandas as pd

EV = '/Users/gmello/Documents/python_repos/mestrado/evidencia_T11'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'
alvos = {
    'smoke_matlab/MMF11_L': f'{EV}/smoke_matlab/experiments/main/e7/exp_main_e7_MMF11_L_42',
    'g6_com/MMF1': f'{EV}/g6_com/experiments/main/e7/exp_main_e7_MMF1_42',
    'g6_sem/MMF1(sonda OFF)': f'{EV}/g6_sem/experiments/main/e7/exp_main_e7_MMF1_42',
}
res = {}
for nome, base in alvos.items():
    ev = [json.loads(x) for x in open(base + '.jsonl')]
    gens = [e for e in ev if e.get('rec') == 'e7_gen']
    sond = [e for e in ev if e.get('rec') == 'sonda']
    gu = [e for e in ev if e.get('rec') == 'guard']
    man = json.load(open(base + '.manifest.json'))
    hdr = [e for e in ev if e.get('rec') == 'header'][0]
    D, M = hdr['D'], hdr['M']; n0 = 11 * D - 1; C = len(gens)
    r1 = pd.read_parquet(base + '__real.parquet'); r3 = pd.read_parquet(base + '__surrogate.parquet')
    r4 = pd.read_parquet(base + '__timing.parquet'); r2 = pd.read_parquet(base + '__pop.parquet')
    on = r3[r3.regime == 'online']
    muc = [c for c in r3.columns if re.fullmatch(r'mu_\d+', c)]
    sgc = [c for c in r3.columns if re.fullmatch(r'sigma_\d+', c)]
    x3c = [c for c in r3.columns if re.fullmatch(r'x\d+', c)]
    xc = [c for c in r1.columns if re.fullmatch(r'x\d+', c)]
    X1 = r1[xc].to_numpy(np.float32); onX = on[x3c].to_numpy(np.float32)
    onMU = on[muc].to_numpy(float); onSG = on[sgc].to_numpy(float)
    cn = cd = iv = idn = 0
    for c, g in enumerate(gens, 1):
        s = (c - 1) * 1900
        blkX = onX[s + 1800:s + 1900]; blkMU = onMU[s + 1800:s + 1900]; blkSG = onSG[s + 1800:s + 1900]
        if blkX.shape[0] != 100:
            continue
        keys = [blkX[i].tobytes() for i in range(100)]
        alvo = {X1[i].tobytes() for i in range(n0 + 3 * (c - 1), min(n0 + 3 * c, len(X1)))}
        idx = [i for i, k in enumerate(keys) if k in alvo]
        if g['ramo'] == 'convergencia':
            cd += 1
            cn += int(np.argmin(np.linalg.norm(blkMU, axis=1)) in idx)
        else:
            idn += 1
            iv += int(np.argmax(blkSG.mean(axis=1)) in idx)
    Gs = C + (1 if any(x.get('name') == 'hard_stop' for x in gu) else 0)
    esp = sorted({1} | {g for g in range(2, Gs + 1) if g % 2 == 0} | {Gs})
    R = {
        'D': D, 'M': M, 'C': C, 'C_esperado': (20 * D) // 3,
        'FE': len(r1), 'FE_esperado': 31 * D - 1,
        'init': int((r1.fase == 'init').sum()), 'init_esperado': n0,
        'opt': int((r1.fase == 'opt').sum()), 'opt_esperado': 20 * D,
        'gatilho_ok': sum(1 for g in gens if ((g['RatioOld'] - g['Ratio']) < g['delta']) == (g['ramo'] == 'convergencia')),
        'joia_conv': f'{cn}/{cd}', 'joia_inc': f'{iv}/{idn}',
        'online_linhas': len(on), 'online_esperado': 1900 * C,
        'pop_por_w_ok': sum(1 for g in gens if len(g['pop_por_w']) == 19 and set(g['pop_por_w']) == {100}),
        'n_treino_ok': sum(1 for g in gens if g['n_treino'] == n0),
        'fetm_ok': sum(1 for c, g in enumerate(gens, 1) if g['fe_treino_max'] == n0 + 3 * (c - 1) - 1),
        'ymin_maxerr': float(max([0.0] + [np.abs(np.array(gens[c + 1]['ymin'], float) - np.array(gens[c]['f_best'], float)).max() for c in range(C - 1)])),
        'n_std_neg': sum(g['n_std_neg'] for g in gens), 'n_dup_infill': sum(g['n_dup_infill'] for g in gens),
        'stall_ciclos': sum(g['stall_ciclos'] for g in gens),
        'sigma_min': float(np.nanmin(r3[sgc].to_numpy(float))), 'sigma_zero': int((r3[sgc].to_numpy(float) == 0).sum()),
        'sigma_nan': int(np.isnan(r3[sgc].to_numpy(float)).sum()),
        'dropP': gens[0]['modelo_hp']['dropP'], 'T': gens[0]['modelo_hp']['T'],
        'batchsize': gens[0]['modelo_hp']['batchsize'], 'loss_treino': gens[0]['modelo_hp']['loss_treino'],
        'razao_fit_80k_8k': round(gens[0]['tempo_fit_inicial_s'] / gens[0]['tempo_fit_s'], 2),
        'blocos_sonda': len(sond), 'cadencia_esperada': esp,
        'cadencia_obs': sorted(int(s['geracao']) for s in sond),
        'sonda_manifesto': man['sonda'].get('geracoes'), 'sonda_desligada': man['sonda'].get('desligada'),
        'l4_linhas': len(r4), 'l4_esperado': C + 1, 'l2_gers': int(r2.geracao.nunique()),
        'termino': [e for e in ev if e.get('rec') == 'footer'][0]['termino'],
        'cache_hits': man['cache_hits'], 'campanha_id': man.get('campanha_id'),
        'schema_version': man.get('schema_version'), 'transf_tipo': list(pd.unique(r3.transf_tipo.dropna())),
        'rsid_conj_ok': sum(1 for c in range(1, C + 1) if set(int(v) for v in on['real_solution_id'].to_numpy()[(c - 1) * 1900:c * 1900] if not pd.isna(v)) == set(range(n0 + 3 * (c - 1), n0 + 3 * c))),
    }
    res[nome] = R
    print(f'\n=== {nome}'); print(json.dumps(R, indent=1, default=str))
json.dump(res, open(f'{OUT}/smoke_estrutural_e7.json', 'w'), indent=1, default=str)
