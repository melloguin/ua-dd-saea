#!/usr/bin/env python
"""T11/e7 — ajustes finos: (a) tempo_fit_inicial_s so no ciclo 1? (b) U11 na definicao F5
(1 linha por infill, janela da pop final); (c) contrafactual delta ESTRITO do paper;
(d) bounds nativos; (e) CV(sigma) intra-pop; (f) A11 magnitude dos mu. READ-ONLY."""
import json, os, re
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e7'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e7'
BOX = {  # box nativo por problema (lb, ub) escalar ou por-coord
    'MMF1': None, 'MMF4': None, 'MMF11_L': None,
}
res = {'celulas': {}}
gl = {'fit_ini_extra': 0, 'contraf_estrito': 0, 'contraf_ge': 0, 'ciclos': 0,
      'u11_num': 0.0, 'u11_den': 0.0, 'bounds_fora': 0, 'bounds_n': 0, 'bounds_no_limite': 0,
      'cv_sigma': [], 'mu_fora_pm1': 0, 'mu_n': 0}
for p in sorted(d for d in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{d}')):
    base = f'{ROOT}/{p}/42/exp_main_e7_{p}_42'
    ev = [json.loads(x) for x in open(base + '.jsonl')]
    gens = [e for e in ev if e.get('rec') == 'e7_gen']
    hdr = [e for e in ev if e.get('rec') == 'header'][0]
    D = hdr['D']; n0 = 11 * D - 1; C = len(gens)
    r1 = pd.read_parquet(base + '__real.parquet')
    r3 = pd.read_parquet(base + '__surrogate.parquet')
    on = r3[r3.regime == 'online']
    xc = [c for c in r1.columns if re.fullmatch(r'x\d+', c)]
    fc = [c for c in r1.columns if re.fullmatch(r'f\d+', c)]
    muc = [c for c in r3.columns if re.fullmatch(r'mu_\d+', c)]
    sgc = [c for c in r3.columns if re.fullmatch(r'sigma_\d+', c)]
    x3c = [c for c in r3.columns if re.fullmatch(r'x\d+', c)]
    L = {}
    # (a)
    extra = sum(1 for g in gens[1:] if 'tempo_fit_inicial_s' in g)
    L['fit_ini_em_gens_1plus'] = extra
    L['fit_ini_vals_g2plus'] = sorted({g.get('tempo_fit_inicial_s') for g in gens[1:]})[:3]
    gl['fit_ini_extra'] += extra
    # (c) contrafactual
    est = sum(1 for g in gens if (g['RatioOld'] - g['Ratio']) > 0.08)
    ge = sum(1 for g in gens if (g['RatioOld'] - g['Ratio']) >= 0.08)
    L['contraf_estrito'] = est; L['contraf_ge'] = ge
    gl['contraf_estrito'] += est; gl['contraf_ge'] += ge; gl['ciclos'] += C
    # margem do limiar
    L['n_perto_1e9'] = sum(1 for g in gens if abs((g['RatioOld'] - g['Ratio']) - g['delta']) < 1e-9)
    # (b) U11 na janela da pop final, 1 linha por infill
    X1 = r1[xc].to_numpy(np.float32); F1 = r1[fc].to_numpy(float)
    onX = on[x3c].to_numpy(np.float32); onMU = on[muc].to_numpy(float); onSG = on[sgc].to_numpy(float)
    num = den = 0.0; nin = 0
    cvs = []
    for c, g in enumerate(gens, 1):
        s = (c - 1) * 1900
        ym = np.array(g['ymin'], float)
        blkX = onX[s + 1800:s + 1900]; blkMU = onMU[s + 1800:s + 1900]; blkSG = onSG[s + 1800:s + 1900]
        if blkX.shape[0] != 100:
            continue
        sb = blkSG.mean(axis=1)
        cvs.append(float(sb.std() / sb.mean()))
        keys = [blkX[i].tobytes() for i in range(100)]
        for sid in range(n0 + 3 * (c - 1), n0 + 3 * c):
            if sid >= len(X1):
                continue
            k = X1[sid].tobytes()
            idx = [i for i, kk in enumerate(keys) if kk == k]
            if not idx:
                continue
            mu = blkMU[idx].mean(axis=0) + ym
            num += float(np.abs(mu - F1[sid]).sum()); den += float(np.abs(F1[sid]).sum()); nin += 1
    L['u11_wape'] = num / den if den else None; L['u11_n'] = nin
    L['cv_sigma_mediana'] = float(np.median(cvs)) if cvs else None
    gl['u11_num'] += num; gl['u11_den'] += den; gl['cv_sigma'].append(L['cv_sigma_mediana'])
    # (d) bounds — do proprio artefato de sonda (cobre o box nativo por desenho)
    son = pd.read_parquet(f'/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_{p}.parquet')
    sxc = [c for c in son.columns if re.fullmatch(r'x\d+', c)]
    lb = son[sxc].to_numpy(float).min(axis=0); ub = son[sxc].to_numpy(float).max(axis=0)
    XX = onX.astype(float)
    tol = 1e-6 * np.maximum(1.0, ub - lb)
    fora = int(((XX < lb - tol) | (XX > ub + tol)).sum())
    nolim = int((np.isclose(XX, lb, atol=1e-7) | np.isclose(XX, ub, atol=1e-7)).sum())
    L['bounds_fora'] = fora; L['bounds_n'] = int(XX.size); L['bounds_no_limite'] = nolim
    L['box'] = [float(lb.min()), float(ub.max())]
    gl['bounds_fora'] += fora; gl['bounds_n'] += XX.size; gl['bounds_no_limite'] += nolim
    # (f) magnitude dos mu (A11)
    MU = r3[muc].to_numpy(float)
    L['mu_min'] = float(np.nanmin(MU)); L['mu_max'] = float(np.nanmax(MU))
    L['frac_mu_fora_pm1'] = float(((MU < -1) | (MU > 1)).sum() / MU.size)
    gl['mu_fora_pm1'] += int(((MU < -1) | (MU > 1)).sum()); gl['mu_n'] += MU.size
    res['celulas'][p] = L
    print(p, json.dumps({k: v for k, v in L.items() if k != 'box'}, default=str), flush=True)

gl['u11_wape_global'] = gl['u11_num'] / gl['u11_den']
gl['cv_sigma_mediana_25'] = float(np.median(gl['cv_sigma']))
gl['frac_mu_fora_pm1'] = gl['mu_fora_pm1'] / gl['mu_n']
res['global'] = gl
json.dump(res, open(f'{OUT}/ajustes_e7.json', 'w'), indent=1, default=str)
print('== GLOBAL ==', json.dumps({k: v for k, v in gl.items() if k != 'cv_sigma'}, indent=1, default=str))
