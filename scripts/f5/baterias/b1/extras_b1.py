"""Bateria b1 - parte 5: extras do mecanismo.
sigma do escolhido x sigma do argmin-mu (o preco da exploracao), ganho de EI,
warm-theta (custo do 1o fit), saturacao de theta, curva n_acumulado x tempo_fit,
e0_trace, dedup_treino, fe_treino_max, sonda fe_treino_max, streaks de cache.
Saida: b1_extras.csv
"""
import json, os
import numpy as np, pandas as pd
import pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])
joia = pd.read_csv(f'{OUT}/b1_joia_iter.csv')
joia['match'] = (joia.d_mu < 1e-5) & (joia.d_sg < 1e-5)

rows = []
sig_rows = []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    son = [e for e in evs if e['rec'] == 'sonda']
    guards = [e for e in evs if e['rec'] == 'guard']
    D, M = hdr['D'], hdr['M']
    tim = pd.read_parquet(base + '__timing.parquet')
    sur = pq.read_table(base + '__surrogate.parquet',
                        columns=['regime', 'geracao', 'mu_0', 'sigma_0']).to_pandas()
    on = sur[sur.regime == 'online']
    del sur
    gg = on.geracao.astype(int).values
    MU = on.mu_0.values.astype(np.float64); SG = on.sigma_0.values.astype(np.float64)
    idx = {}; start = 0
    for i in range(1, len(gg) + 1):
        if i == len(gg) or gg[i] != gg[start]:
            idx[int(gg[start])] = (start, i); start = i
    sub = joia[joia.problema == p].set_index('geracao')
    ns_ng = 0; sg_gain = []; ei_gain = []; sg_rank_sel = []; sg_rank_greedy = []
    for e in ge:
        g = e['geracao']
        if not bool(sub.loc[g, 'match']):
            continue
        a, b = idx[g]
        mu = MU[a:b]; sg = SG[a:b]
        k = int(sub.loc[g, 'k_ei']); km = int(sub.loc[g, 'k_mu'])
        if k == km:
            continue
        ns_ng += 1
        sg_gain.append(sg[k] / max(sg[km], 1e-300))
        ei_gain.append(float(sub.loc[g, 'ganho_ei']))
        sg_rank_sel.append(float((sg < sg[k]).mean()))
        sg_rank_greedy.append(float((sg < sg[km]).mean()))
    # theta
    thmin = np.array([e['theta_min'] for e in ge]); thmax = np.array([e['theta_max'] for e in ge])
    thmed = np.array([e['theta_media'] for e in ge])
    hp = [e.get('modelo_hp') for e in ge]
    n_theta_sat_hi = 0; n_theta_sat_lo = 0; n_theta_comp = 0
    for h in hp:
        if isinstance(h, dict) and 'theta' in h:
            t = np.asarray(h['theta'], float)
            n_theta_comp += t.size
            n_theta_sat_hi += int((t >= 20 - 1e-9).sum())
            n_theta_sat_lo += int((t <= 1e-5 + 1e-12).sum())
    hp0 = hp[0] if isinstance(hp[0], dict) else {}
    # warm-theta: custo do 1o fit vs mediana
    tf = tim.tempo_fit_s.values
    r1 = tf[0] / np.median(tf)
    # curva n_acumulado x tempo_fit
    na = tim.n_acumulado.values
    cap = 11 * D - 1 + 25
    p_cap = float((na == cap).mean())
    tf_pre = tf[na < cap]; tf_pos = tf[na == cap]
    drift = np.nan
    if len(tf_pos) > 5:
        x = np.arange(len(tf_pos)); c = np.polyfit(x, tf_pos, 1)
        drift = float(c[0] * len(tf_pos) / max(np.median(tf_pos), 1e-12))
    # e0
    e0len = [len(e['e0_trace']) for e in ge]
    e0mono = np.mean([bool(np.all(np.diff(e['e0_trace']) <= 1e-15)) for e in ge])
    # sonda fe_treino_max
    ftm_son = [s.get('fe_treino_max') for s in son]
    rows.append(dict(problema=p, D=D, M=M, n_iter=len(ge),
                     n_ng_match=ns_ng,
                     sg_ratio_med=float(np.median(sg_gain)) if sg_gain else np.nan,
                     sg_ratio_p90=float(np.percentile(sg_gain, 90)) if sg_gain else np.nan,
                     frac_sg_maior=float(np.mean(np.array(sg_gain) > 1)) if sg_gain else np.nan,
                     ei_gain_med=float(np.median(ei_gain)) if ei_gain else np.nan,
                     sg_rank_sel=float(np.median(sg_rank_sel)) if sg_rank_sel else np.nan,
                     sg_rank_greedy=float(np.median(sg_rank_greedy)) if sg_rank_greedy else np.nan,
                     theta_lo=float(thmin.min()), theta_hi=float(thmax.max()),
                     theta_med_1=float(thmed[0]), theta_med_last=float(thmed[-1]),
                     n_theta_comp=n_theta_comp, n_sat_hi=n_theta_sat_hi, n_sat_lo=n_theta_sat_lo,
                     hp_keys=';'.join(sorted(hp0.keys())) if hp0 else '',
                     fit1=float(tf[0]), fit_med=float(np.median(tf)), fit_ratio1=float(r1),
                     fit_last=float(tf[-1]), frac_no_cap=p_cap, drift_pos_cap=drift,
                     tempo_total=float(tim.tempo_geracao_s.sum()),
                     frac_fit=float(tim.tempo_fit_s.sum() / tim.tempo_geracao_s.sum()),
                     e0_len_min=int(min(e0len)), e0_len_max=int(max(e0len)),
                     e0_frac_monot=float(e0mono),
                     n_dedup_ev=sum(1 for g_ in guards if g_['name'] == 'dedup_treino'),
                     dedup_sum=int(sum(e['n_dedup'] for e in ge)),
                     dedup_max=int(max(e['n_dedup'] for e in ge)),
                     ftm_sonda_min=int(min(ftm_son)), ftm_sonda_max=int(max(ftm_son)),
                     n_front1_1=ge[0].get('n_front1'), n_front1_last=ge[-1].get('n_front1'),
                     ))
    print(f'{p:10s} NGmatch={ns_ng:4d} sg_ratio_med={rows[-1]["sg_ratio_med"]:.3f} '
          f'fracSGmaior={rows[-1]["frac_sg_maior"]:.3f} sgrank sel={rows[-1]["sg_rank_sel"]:.3f} '
          f'greedy={rows[-1]["sg_rank_greedy"]:.3f} fit1/med={r1:.2f} '
          f'theta[{thmin.min():.1e},{thmax.max():.3f}] satHi={n_theta_sat_hi} satLo={n_theta_sat_lo} de {n_theta_comp}')
    del on, MU, SG

df = pd.DataFrame(rows); df.to_csv(f'{OUT}/b1_extras.csv', index=False)
print()
print('theta componentes:', df.n_theta_comp.sum(), 'sat 20:', df.n_sat_hi.sum(), 'sat 1e-5:', df.n_sat_lo.sum())
print('fit1/mediana: mediana', df.fit_ratio1.median(), 'min', df.fit_ratio1.min(), 'max', df.fit_ratio1.max())
print('sigma do escolhido MAIOR que a do argmin-mu em (mediana das celulas):', df.frac_sg_maior.median())
print('razao sigma_sel/sigma_greedy mediana:', df.sg_ratio_med.median())
print('rank de sigma: escolhido', df.sg_rank_sel.median(), 'x greedy', df.sg_rank_greedy.median())
print('dedup eventos', df.n_dedup_ev.sum(), 'remocoes acumuladas', df.dedup_sum.sum())
print('e0 fracao monotonica (media)', df.e0_frac_monot.mean())
