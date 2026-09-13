#!/usr/bin/env python3
"""T11/F5-bis — RE-MEDIÇÃO do mecanismo do e103 na rodada-42 (45 células).

READ-ONLY absoluto: só abre parquet/jsonl/manifest de
`resultados_experimentos/e103/{label}/42/`. Nada é escrito fora de
`ua-dd-saea/f5/t11/baterias/e103/`.

Re-mede, do zero, as identidades-chave da F5 (não confia nos CSVs antigos):
  I1  regime offline / FE / ① == dataset
  I2  99 gerações densas + orçamento 9.900
  I3  ④ com 1 linha (treino único) + fe_treino_max único
  I4  pop inicial = dataset INTEIRO (n_julgados g1 == n_ds+100; g>=2 == 200)
  I5  matriz N² completa (n_pares_total == n_julgados²)
  I6  QUERY-JOIA: KFlag==1  <=>  #obj com R_m=1 em TODOS os pares >= M-1
  I7  KFlag STATELESS: nº de trocas
  I8  centros == ceil(sqrt(n_dataset))  (D93)
  I9  θ do DACE congelado em θ0=10 (alta dimensão)
  I10 σ: NULL 100% no RBFN, 0% no Kriging; MSE<0
  I11 ⑦: cardinalidade, recomputo do ND, link posicional bit-a-bit  <-- A25
  I12 censo do ⑥ + término
"""
from __future__ import annotations
import os, sys, json, math, hashlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e103'
DS   = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets'
OUT  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/e103'


def load_jsonl(p):
    evs, bad = [], 0
    with open(p, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                evs.append(json.loads(line))
            except Exception:
                bad += 1
    return evs, bad


def nd_mask(F):
    n = F.shape[0]
    m = np.ones(n, bool)
    for i in range(n):
        if not m[i]:
            continue
        d = (F <= F[i]).all(1) & (F < F[i]).any(1)
        if d.any():
            m[i] = False
    return m


rows = []
gate_rows = []
for lab in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, lab, '42')
    if not os.path.isdir(d):
        continue
    base = [f for f in os.listdir(d) if f.endswith('.manifest.json')
            and not f.endswith('__final.manifest.json')][0][:-len('.manifest.json')]
    P = os.path.join(d, base)
    man = json.load(open(P + '.manifest.json'))
    evs, bad = load_jsonl(P + '.jsonl')
    r = {'label': lab, 'problema': man['problema'], 'n_orfas': bad}
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ftr = [e for e in evs if e['rec'] == 'footer']
    setup = [e for e in evs if e['rec'] == 'e103_setup'][0]
    gens = sorted([e for e in evs if e['rec'] == 'e103_gen'], key=lambda e: e['geracao'])
    D, M = int(hdr['D']), int(hdr['M'])
    nds = int(hdr['n_dataset'])
    r.update(D=D, M=M, n_dataset=nds, n_gen_ev=len(gens),
             tier=man['dataset']['tier'], dist=man['dataset']['dist'])

    # ---------- I1 regime offline ----------
    t1 = pq.read_table(P + '__real.parquet').to_pandas()
    r['I1_n_real'] = len(t1)
    r['I1_fase_init_pct'] = float((t1['fase'] == 'init').mean()) if 'fase' in t1 else np.nan
    r['I1_fe_final_eq_maxfe_eq_nds'] = (man['fe_final'] == man['maxfe'] == nds)
    r['I1_dup_x'] = int(len(t1) - len(t1[[c for c in t1 if c.startswith('x') and c[1:].isdigit()]].drop_duplicates()))
    dsp = os.path.join(DS, man['problema'], f"ds_{man['problema']}_42.parquet")
    if man['dataset']['tier'] != 'small' or man['dataset']['dist'] != 'lhs':
        dsp = os.path.join(DS, man['problema'],
                           f"ds_{man['problema']}_42_{man['dataset']['tier']}_{man['dataset']['dist']}.parquet")
    r['I1_ds_artefato'] = os.path.exists(dsp)
    if r['I1_ds_artefato']:
        td = pq.read_table(dsp).to_pandas()
        xc = [c for c in t1 if c.startswith('x') and c[1:].isdigit()]
        fc = [c for c in t1 if c.startswith('f') and c[1:].isdigit()]
        xcd = [c for c in td if c.startswith('x') and c[1:].isdigit()]
        fcd = [c for c in td if c.startswith('f') and c[1:].isdigit()]
        if len(td) == len(t1):
            r['I1_dX'] = float(np.abs(t1[xc].to_numpy(float) - td[xcd].to_numpy(float)).max())
            r['I1_dF'] = float(np.abs(t1[fc].to_numpy(float) - td[fcd].to_numpy(float)).max())
    r['I1_t_aval_real_s'] = man['timing'].get('tempo_aval_real_s')

    # ---------- ③ ----------
    t3 = pq.read_table(P + '__surrogate.parquet').to_pandas()
    opt = t3[t3.regime != 'sonda']
    son = t3[t3.regime == 'sonda']
    r['I2_opt_linhas'] = len(opt)
    r['I2_opt_esperado'] = 2 * 100 * len(gens)
    r['I2_ger_densa'] = sorted(set(int(g) for g in opt.geracao.dropna())) == list(range(1, len(gens) + 1))
    r['I2_orcamento_surrogate'] = 100 * len(gens)
    r['I2_regimes'] = json.dumps(sorted(t3.regime.unique().tolist()))
    r['I2_sonda_linhas'] = len(son)

    # ---------- I3 ④ ----------
    t4 = pq.read_table(P + '__timing.parquet').to_pandas()
    r['I3_tim_linhas'] = len(t4)
    r['I3_tim_ger0'] = bool((t4['geracao'].fillna(-1) == 0).all())
    r['I3_fit_series_len'] = len(man.get('fit_series', []))
    r['I3_fe_treino_uniq'] = json.dumps(sorted(pd.unique(opt.fe_treino_max.dropna()).tolist()))
    r['I3_fe_treino_ok'] = (list(pd.unique(opt.fe_treino_max.dropna())) == [nds - 1])

    # ---------- I4/I5/I6/I7 do ⑥ ----------
    njg = [g['n_julgados'] for g in gens]
    r['I4_njulg_g1'] = njg[0] if njg else None
    r['I4_g1_eq_nds_mais_100'] = (njg[0] == nds + 100) if njg else None
    r['I4_g2p_todos_200'] = all(v == 200 for v in njg[1:]) if len(njg) > 1 else None
    r['I4_nsel_100'] = all(g['n_sel'] == 100 for g in gens)

    n_par_ok, kfl, ufcons, obj_full = 0, [], 0, []
    for g in gens:
        ms = g.get('margem_3sigma_stats') or {}
        npt = ms.get('n_pares_total'); nok = ms.get('n_pares_ok')
        po = ms.get('n_pares_ok_por_objetivo')
        if npt == g['n_julgados'] ** 2:
            n_par_ok += 1
        kf = int(g['kflag'])
        kfl.append(kf)
        nfull = sum(1 for v in (po or []) if v == npt)
        obj_full.append(nfull)
        if (nfull >= M - 1) == (kf == 1):
            ufcons += 1
        gate_rows.append(dict(label=lab, geracao=g['geracao'], M=M, kflag=kf,
                              n_pares_total=npt, n_pares_ok=nok,
                              n_obj_full=nfull, frac_ok=(nok / npt) if npt else np.nan,
                              modelo_lider=g.get('modelo_lider')))
    r['I5_npares_eq_n2'] = n_par_ok
    r['I6_identidade_ok'] = ufcons
    r['I6_total_ger'] = len(gens)
    r['I7_kflag_trocas'] = int(sum(1 for a, b in zip(kfl, kfl[1:]) if a != b))
    r['I7_kflag_lider'] = gens[0].get('modelo_lider') if gens else None
    r['I7_kflag_1'] = int(sum(kfl))

    # contrafactual estrito (UF = M)
    r['I6_estrito_kriging'] = int(sum(1 for n in obj_full if n >= M))

    # ---------- I8/I9 setup ----------
    r['I8_center_num'] = setup['center_num']
    r['I8_center_esperado'] = int(math.ceil(math.sqrt(nds)))
    r['I8_center_stock_11D'] = int(math.ceil(math.sqrt(11 * D - 1)))
    r['I8_ok'] = (setup['center_num'] == r['I8_center_esperado'])
    r['I8_spread'] = setup['rbfn_spread']
    tmin = np.asarray(setup['krig_theta_min'], float)
    tmax = np.asarray(setup['krig_theta_max'], float)
    r['I9_theta_min'] = float(tmin.min()); r['I9_theta_max'] = float(tmax.max())
    r['I9_dentro_bounds'] = bool(tmin.min() >= 1e-3 - 1e-12 and tmax.max() <= 1e3 + 1e-9)
    r['I9_theta_congelado_10'] = bool(np.allclose(tmin, 10.0) and np.allclose(tmax, 10.0))
    r['I9_warn_setup'] = setup.get('warn_setup')

    # ---------- I10 σ ----------
    K = opt[opt.modelo_flag.str.contains('Kriging', na=False)]
    R = opt[opt.modelo_flag.str.contains('RBFN', na=False)]
    sc = [c for c in opt if c.startswith('sigma_')]
    r['I10_K_linhas'] = len(K); r['I10_R_linhas'] = len(R)
    r['I10_sigmaK_null_pct'] = float(K[sc].isna().to_numpy().mean() * 100) if len(K) else np.nan
    r['I10_sigmaR_null_pct'] = float(R[sc].isna().to_numpy().mean() * 100) if len(R) else np.nan
    r['I10_sigmaK_neg'] = int((K[sc].to_numpy(float) < 0).sum()) if len(K) else 0
    r['I10_n_mse_neg'] = int(sum(g.get('n_mse_neg', 0) or 0 for g in gens))

    # ---------- I11 ⑦ ----------
    fp = P + '__final.parquet'
    if os.path.exists(fp):
        t7 = pq.read_table(fp).to_pandas()
        fm = json.load(open(P + '__final.manifest.json'))
        r['I11_n_final'] = len(t7)
        r['I11_mtime'] = pd.Timestamp(os.path.getmtime(fp), unit='s', tz='UTC').tz_convert(
            'America/Sao_Paulo').strftime('%Y-%m-%d %H:%M:%S')
        fc7 = [c for c in t7 if c.startswith('f') and c[1:].isdigit()]
        rec = nd_mask(t7[fc7].to_numpy(float))
        r['I11_nd_recomputo_ok'] = bool((rec == t7['nd_pos_real'].to_numpy(bool)).all())
        r['I11_nd'] = int(t7['nd_pos_real'].sum())
        r['I11_fantasia'] = float(t7['nd_pos_real'].mean())
        r['I11_ger_uniq'] = json.dumps(sorted(pd.unique(t7['origem_geracao']).tolist()))
        r['I11_linha_densa'] = (t7['origem_linha'].tolist() == list(range(len(t7))))
        r['I11_rsid_null'] = bool(t7['origem_solution_id'].isna().all())
        # link posicional: última geração, PRIMEIRO modelo_flag da ordem da ③
        gf = int(opt.geracao.max())
        ult = opt[opt.geracao == gf]
        prim = list(dict.fromkeys(ult.modelo_flag.tolist()))[0]
        ultf = ult[ult.modelo_flag == prim]
        xc7 = [c for c in t7 if c.startswith('x') and c[1:].isdigit()]
        xc3 = [c for c in ultf if c.startswith('x') and c[1:].isdigit()]
        if len(ultf) == len(t7):
            dd = np.abs(t7[xc7].to_numpy(float) - ultf[xc3].to_numpy(float))
            r['I11_link_dX_max'] = float(dd.max())
            r['I11_link_bit'] = bool(dd.max() == 0.0)
        r['I11_modelo_primeiro'] = prim
        r['I11_n_final_man'] = fm.get('n_final')

    # ---------- I12 censo ----------
    import collections
    cen = collections.Counter(e['rec'] for e in evs)
    r['I12_censo'] = json.dumps(dict(sorted(cen.items())))
    r['I12_n_recs'] = sum(cen.values())
    r['I12_termino'] = ftr[0].get('termino') if ftr else None
    r['I12_status_man'] = man['status']
    r['I12_guards'] = cen.get('guard', 0)
    r['I12_params'] = 'params' in man and bool(man['params'])
    r['I12_sigma_dict'] = 'sigma_dict' in man and bool(man['sigma_dict'])
    r['I12_schema_version'] = man.get('schema_version')
    r['I12_campanha_id'] = man.get('campanha_id')
    r['I12_repo_hash'] = man.get('repo_hash')
    r['I12_sonda_desligada_presente'] = 'desligada' in (man.get('sonda') or {})
    # ERRATA 7 / 14
    r['E7_margem_3sigma_stats'] = int(sum(1 for g in gens if g.get('margem_3sigma_stats')))
    r['E7_margem_3sigma_plano'] = int(sum(1 for g in gens if 'margem_3sigma' in g))
    r['E14_gen_com_tempo_busca'] = int(sum(1 for g in gens if 'tempo_busca_s' in g))
    r['E14_gen_com_tempo_fit'] = int(sum(1 for g in gens if 'tempo_fit_s' in g))
    ebus = [e for e in evs if e['rec'] == 'e103_busca']
    r['E14_busca_ev'] = len(ebus)
    r['E14_busca_campos'] = json.dumps(sorted(ebus[0].keys())) if ebus else None
    r['E14_busca_tem_tempo_geracao_s'] = ('tempo_geracao_s' in ebus[0]) if ebus else None
    rows.append(r)
    print('.', end='', flush=True)

print()
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 't11_e103_celulas.csv'), index=False)
pd.DataFrame(gate_rows).to_csv(os.path.join(OUT, 't11_e103_gate3sigma.csv'), index=False)
print('células:', len(df))
pd.set_option('display.width', 250)
for c in ['I1_fase_init_pct', 'I1_fe_final_eq_maxfe_eq_nds', 'I1_dup_x', 'I1_dX', 'I1_dF',
          'I2_opt_linhas', 'I2_ger_densa', 'I3_tim_linhas', 'I3_fit_series_len', 'I3_fe_treino_ok',
          'I4_g1_eq_nds_mais_100', 'I4_g2p_todos_200', 'I4_nsel_100',
          'I5_npares_eq_n2', 'I6_identidade_ok', 'I6_total_ger', 'I6_estrito_kriging',
          'I7_kflag_trocas', 'I8_ok', 'I9_dentro_bounds', 'I9_theta_congelado_10',
          'I10_sigmaK_null_pct', 'I10_sigmaR_null_pct', 'I10_sigmaK_neg', 'I10_n_mse_neg',
          'I11_n_final', 'I11_nd_recomputo_ok', 'I11_link_bit', 'I11_linha_densa', 'I11_rsid_null',
          'I12_n_recs', 'I12_termino', 'I12_params', 'I12_schema_version',
          'E7_margem_3sigma_stats', 'E7_margem_3sigma_plano',
          'E14_gen_com_tempo_busca', 'E14_gen_com_tempo_fit', 'E14_busca_tem_tempo_geracao_s']:
    if c in df:
        v = df[c]
        try:
            print(f'{c:32s} -> {dict(v.value_counts(dropna=False))}')
        except Exception:
            print(f'{c:32s} -> min={v.min()} max={v.max()}')
