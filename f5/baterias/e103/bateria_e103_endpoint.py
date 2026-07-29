#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_e103_endpoint.py — F5.3b/e103 · o ENDPOINT do regime offline (⑦, DI-08) e o
mecanismo (KFlag, decay do dataset na pop, theta do DACE, divergencia Kriging×RBFN).
Usa src/metrics.py (metrica OFICIAL, nunca reimplementada) com o gate D92 antes.
READ-ONLY.  Saidas em f5/baterias/e103/.
"""
import os, sys, json, glob, math
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
OUT = os.path.join(REPO, 'f5', 'baterias', 'e103')
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics  # noqa: E402

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)


def cells():
    out = []
    for lab in sorted(os.listdir(RES)):
        d = os.path.join(RES, lab, '42')
        if not os.path.isdir(d):
            continue
        mf = [f for f in glob.glob(os.path.join(d, 'exp_*_e103_*_42.manifest.json'))
              if '__final' not in f]
        base = os.path.basename(mf[0])[:-len('.manifest.json')]
        exp = base.split('_e103_')[0][len('exp_'):]
        prob = base.split('_e103_')[1][:-len('_42')]
        out.append((lab, exp, prob, d, base))
    return out


rows, kf_rows = [], []
for lab, exp, prob, d, base in cells():
    r = {'label': lab, 'exp': exp, 'problema': prob}
    man = json.load(open(os.path.join(d, base + '.manifest.json')))
    recs = []
    for line in open(os.path.join(d, base + '.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
    gens = sorted([x for x in recs if x.get('rec') == 'e103_gen'], key=lambda x: x['geracao'])
    setup = [x for x in recs if x.get('rec') == 'e103_setup'][0]
    D, M, n_ds = man['params'].get('N') and 0 or 0, None, man['dataset']['n']
    hdr = [x for x in recs if x.get('rec') == 'header'][0]
    D, M = hdr['D'], hdr['M']
    r.update(D=D, M=M, n_dataset=n_ds, tier=man['dataset']['tier'], dist=man['dataset']['dist'])

    real = pq.read_table(os.path.join(d, base + '__real.parquet')).to_pandas()
    fin = pq.read_table(os.path.join(d, base + '__final.parquet')).to_pandas()
    fc = ['f%d' % i for i in range(M)]
    R = metrics.reference_set(prob)

    m_ds = metrics.metrics_of_set(real[fc].values, prob, ref_norm=R)
    m_fin = metrics.metrics_of_set(fin[fc].values, prob, ref_norm=R)
    m_nd = metrics.metrics_of_set(fin[fin['nd_pos_real']][fc].values, prob, ref_norm=R)
    r['igd_dataset'] = m_ds['igd_plus']
    r['hv_dataset'] = m_ds['hv']
    r['nnd_dataset'] = m_ds['n_nd']
    r['igd_final'] = m_fin['igd_plus']
    r['hv_final'] = m_fin['hv']
    r['nnd_final'] = m_fin['n_nd']
    r['igd_final_ndonly'] = m_nd['igd_plus']
    r['ganho_igd'] = 1.0 - (m_fin['igd_plus'] / m_ds['igd_plus']) if m_ds['igd_plus'] else np.nan
    r['bate_dataset'] = bool(m_fin['igd_plus'] < m_ds['igd_plus'])
    r['n_final'] = len(fin)
    r['nd_pos_real'] = int(fin['nd_pos_real'].sum())
    r['fantasia'] = float(fin['nd_pos_real'].mean())

    # --- KFlag / gate ---
    kf = np.array([x['kflag'] for x in gens])
    r['kflag_1'] = int((kf == 1).sum())
    r['kflag_0'] = int((kf == 0).sum())
    r['modelo'] = 'Kriging' if kf[0] == 1 else 'RBFN'
    r['trocas'] = int((kf[1:] != kf[:-1]).sum())
    tot = np.array([(x.get('margem_3sigma_stats') or {}).get('n_pares_total', np.nan) for x in gens], float)
    ok = np.array([(x.get('margem_3sigma_stats') or {}).get('n_pares_ok', np.nan) for x in gens], float)
    po = np.array([[(x.get('margem_3sigma_stats') or {}).get('n_pares_ok_por_objetivo', [np.nan] * M)[j]
                    for j in range(M)] for x in gens], float)
    r['frac_pares_ok_med'] = float(np.nanmedian(ok / tot))
    r['frac_pares_ok_min'] = float(np.nanmin(ok / tot))
    r['frac_obj_med'] = json.dumps([round(float(np.nanmedian(po[:, j] / tot)), 6) for j in range(M)])
    r['obj_100pct'] = int(sum((po[:, j] == tot).all() for j in range(M)))
    r['obj_melhor_med'] = float(np.nanmedian(po.max(axis=1) / tot))
    # contrafactual da relaxacao M-1: quantas geracoes SERIAM Kriging sob criterio ESTRITO
    # (estrito exige R=1 em TODOS os objetivos p/ TODOS os pares -> so se ok==tot)
    r['gen_kriging_estrito'] = int((ok == tot).sum())
    r['sqrtmse_max_med'] = float(np.nanmedian([x.get('sqrtmse_surr_max', np.nan) for x in gens]))
    r['sqrtmse_med_med'] = float(np.nanmedian([x.get('sqrtmse_surr_med', np.nan) for x in gens]))
    r['div_modelos_med'] = float(np.nanmedian([x.get('divergencia_modelos', np.nan) for x in gens]))
    r['div_modelos_g1'] = gens[0].get('divergencia_modelos')
    r['div_modelos_g99'] = gens[-1].get('divergencia_modelos')

    # --- decay dos membros do dataset na populacao (② / n_ds_membros) ---
    nds = np.array([x['n_ds_membros'] for x in gens], float)
    r['ndsm_g1'] = int(nds[0])
    r['ndsm_g5'] = int(nds[4]) if len(nds) > 4 else None
    r['ndsm_g10'] = int(nds[9]) if len(nds) > 9 else None
    r['ndsm_g50'] = int(nds[49]) if len(nds) > 49 else None
    r['ndsm_g99'] = int(nds[-1])
    z = np.where(nds == 0)[0]
    r['ger_zera'] = int(z[0] + 1) if len(z) else None   # 1-based
    r['meia_vida'] = int(np.argmax(nds <= nds[0] / 2) + 1)
    r['fuga_total'] = bool(nds[-1] == 0)

    # --- theta do DACE ---
    tmin = setup.get('krig_theta_min') or []
    tmax = setup.get('krig_theta_max') or []
    tmed = setup.get('krig_theta_media') or []
    r['theta_min'] = json.dumps(tmin)
    r['theta_max'] = json.dumps(tmax)
    r['theta_parado_em_10'] = bool(all(abs(a - 10) < 1e-9 and abs(b - 10) < 1e-9
                                       for a, b in zip(tmin, tmax)))
    r['theta_no_piso'] = int(sum(1 for a in tmin if a <= 1e-3 * (1 + 1e-9)))
    r['theta_no_teto'] = int(sum(1 for b in tmax if b >= 1e3 * (1 - 1e-9)))
    r['sigma2'] = json.dumps(setup.get('krig_sigma2'))
    r['sigma2_min'] = float(np.min(setup.get('krig_sigma2') or [np.nan]))
    r['center_num'] = setup.get('center_num')
    r['center_esperado'] = int(math.ceil(math.sqrt(n_ds)))
    r['center_stock'] = int(math.ceil(math.sqrt(11 * D - 1)))
    r['spread'] = setup.get('rbfn_spread')
    r['t_fit_krig'] = setup.get('tempo_fit_kriging_s')
    r['t_fit_rbfn'] = setup.get('tempo_fit_rbfn_s')
    r['razao_fit'] = (setup.get('tempo_fit_kriging_s') or np.nan) / max(setup.get('tempo_fit_rbfn_s') or np.nan, 1e-12)

    rows.append(r)
    for x in gens:
        ms = x.get('margem_3sigma_stats') or {}
        kf_rows.append({'label': lab, 'problema': prob, 'M': M, 'geracao': x['geracao'],
                        'kflag': x['kflag'], 'modelo_lider': x['modelo_lider'],
                        'n_julgados': x['n_julgados'], 'n_ds_membros': x['n_ds_membros'],
                        'n_front1': x.get('n_front1'),
                        'pares_ok': ms.get('n_pares_ok'), 'pares_total': ms.get('n_pares_total'),
                        'pares_ok_obj': json.dumps(ms.get('n_pares_ok_por_objetivo')),
                        'sqrtmse_surr_max': x.get('sqrtmse_surr_max'),
                        'divergencia': x.get('divergencia_modelos')})
    print('ok', lab, flush=True)

pd.DataFrame(rows).to_csv(os.path.join(OUT, 'endpoint_e103.csv'), index=False)
pd.DataFrame(kf_rows).to_csv(os.path.join(OUT, 'geracoes_e103.csv'), index=False)
print(len(rows), len(kf_rows))
