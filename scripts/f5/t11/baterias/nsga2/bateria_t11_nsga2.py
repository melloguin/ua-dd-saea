#!/usr/bin/env python
"""Bateria T11 do config nsga2 — RE-MEDICAO INTEGRAL sobre as 25 celulas da s42.
READ-ONLY. Nao toca data/experiments, nao invoca experiments.py.
Saida: aspectos_t11_nsga2.csv + prints agregados.
"""
import json, glob, os, hashlib, math
import numpy as np, pandas as pd
import pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga2'
DOE  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT  = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga2'

def jl(p):
    out = []
    for l in open(p):
        l = l.strip()
        if l:
            out.append(json.loads(l))
    return out

def ndsort(F):
    """Non-dominated sort classico. Retorna vetor de fronteiras 1-based."""
    n = len(F)
    fr = np.zeros(n, dtype=int)
    rest = np.arange(n)
    k = 1
    while len(rest):
        Fr = F[rest]
        dom = np.zeros(len(rest), dtype=bool)
        for i in range(len(rest)):
            le = np.all(Fr <= Fr[i], axis=1)
            lt = np.any(Fr < Fr[i], axis=1)
            if np.any(le & lt):
                dom[i] = True
        fr[rest[~dom]] = k
        rest = rest[dom]
        k += 1
    return fr

def crowding(F):
    n, M = F.shape
    cd = np.zeros(n)
    if n <= 2:
        return np.full(n, np.inf)
    for j in range(M):
        o = np.argsort(F[:, j], kind='stable')
        cd[o[0]] = cd[o[-1]] = np.inf
        rng = F[o[-1], j] - F[o[0], j]
        if rng == 0:
            continue
        cd[o[1:-1]] += (F[o[2:], j] - F[o[:-2], j]) / rng
    return cd

def selec_d88(F, N):
    """NDSort + crowding + desempate por indice -> indices escolhidos."""
    fr = ndsort(F)
    esc = []
    k = 1
    while len(esc) < N:
        idx = np.where(fr == k)[0]
        if len(esc) + len(idx) <= N:
            esc.extend(idx.tolist())
        else:
            cd = crowding(F[idx])
            ordem = np.lexsort((idx, -cd))
            esc.extend(idx[ordem][:N - len(esc)].tolist())
        k += 1
    return sorted(esc), fr

rows = []
probs = sorted(os.listdir(RAIZ))
for prob in probs:
    base = f'{RAIZ}/{prob}/42/exp_main_nsga2_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    ev = jl(base + '.jsonl')
    hdr = [e for e in ev if e['rec'] == 'header'][0]
    ftr = [e for e in ev if e['rec'] == 'footer']
    seed_rec = [e for e in ev if e['rec'] == 'seeding'][0]
    gens = [e for e in ev if e['rec'] == 'nsga2_gen']
    guards = [e for e in ev if e['rec'] == 'guard']
    real = pq.read_table(base + '__real.parquet').to_pandas()
    pop = pq.read_table(base + '__pop.parquet').to_pandas()
    sur = pq.read_table(base + '__surrogate.parquet')
    tim = pq.read_table(base + '__timing.parquet').to_pandas()
    D, M = hdr['D'], hdr['M']
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    r = dict(problema=prob, D=D, M=M)

    # ---------- U1 orcamento
    r['u1_len1'] = len(real); r['u1_maxfe'] = man['maxfe']; r['u1_31Dm1'] = 31 * D - 1
    r['u1_ok_fe'] = (len(real) == 31 * D - 1 == man['maxfe'] == man['fe_final'])
    r['u1_feidx_denso'] = bool((np.sort(real.fe_index.values) == np.arange(len(real))).all())
    r['u1_sid_unicos'] = int(real.solution_id.nunique()) == len(real)
    r['u1_termino'] = ftr[0]['termino'] if ftr else None
    r['u1_nfooter'] = len(ftr)
    r['u1_hardstop'] = sum(1 for g in guards if g['name'] == 'hard_stop')
    r['u1_status'] = man['status']; r['u1_retries'] = man['n_retries']
    r['u1_fallback'] = man['fallback_ativado']

    # ---------- U2 DoE
    n_init = 11 * D - 1
    ini = real[real.fase == 'init']
    r['u2_ninit'] = len(ini); r['u2_esperado'] = n_init
    r['u2_prefixo'] = bool((ini.fe_index.values == np.arange(n_init)).all()) if len(ini) == n_init else False
    doe = pq.read_table(f'{DOE}/{prob}/doe_{prob}_42.parquet').to_pandas()
    dx = doe[[c for c in doe.columns if c.startswith('x')][:D]].to_numpy(np.float64)[:n_init]
    r['u2_dX'] = float(np.abs(dx.astype(np.float32).astype(np.float64) -
                              ini[xc].to_numpy(np.float64)).max())
    dm = json.load(open(f'{DOE}/{prob}/doe_{prob}_42.manifest.json'))
    r['u2_hash_ok'] = (dm.get('sha256') or dm.get('doe_hash') or dm.get('hash')) == man['doe_hash']
    r['u2_cpinit'] = ftr[0].get('cp_init') if ftr else None
    r['u2_fases'] = ','.join(sorted(real.fase.unique()))

    # ---------- U3 sem surrogate
    r['u3_n3'] = sur.num_rows; r['u3_cols3'] = len(sur.schema.names)
    r['u3_tempo_nulos'] = int(tim[['tempo_fit_s', 'tempo_busca_s', 'tempo_pred_sonda_s']].isna().all(axis=1).sum())
    r['u3_n4'] = len(tim)
    r['u3_nacum_nan'] = int(tim.n_acumulado.isna().sum())
    r['u3_fitseries'] = len(man['fit_series'])
    r['u3_sigma_dict_presente'] = 'sigma_dict' in man
    r['u3_timing5_nulos'] = all(man['timing'][k] is None for k in
                                ('tempo_fit_surrogate_s', 'tempo_busca_s', 'tempo_pred_sonda_s'))
    r['u3_tempo_aval_real'] = man['timing']['tempo_aval_real_s']

    # ---------- U4 sonda
    s = man.get('sonda', {})
    r['u4_sonda_status'] = s.get('status'); r['u4_sonda_blocos'] = s.get('n_blocos')
    r['u4_sonda_linhas'] = s.get('n_linhas')
    r['u4_rec_sonda'] = sum(1 for e in ev if e['rec'] == 'sonda')

    # ---------- T11: instrumentacao nova presente na s42?
    r['t11_campanha_id'] = 'campanha_id' in man
    r['t11_repo_hash'] = man.get('repo_hash')
    r['t11_schema_version'] = man.get('schema_version')
    r['t11_regra_rotulo'] = 'REGRA_DO_ROTULO' in json.dumps(man)
    r['t11_sonda_estrat'] = 'sonda_estratificada' in json.dumps(man)
    r['t11_ger_deriv'] = man['params']['geracoes_derivadas'][:40]

    # ---------- U7 timing
    tg6 = np.array([g['tempo_geracao_s'] for g in gens], float)
    tg4 = tim.tempo_geracao_s.to_numpy(np.float64)
    r['u7_n_gen6'] = len(gens); r['u7_n_ger4'] = len(tim)
    r['u7_dmax'] = float(np.abs(tg6 - tg4).max()) if len(tg6) == len(tg4) else np.nan
    r['u7_ger_seq'] = bool((tim.geracao.values == np.arange(1, len(tim) + 1)).all())
    r['u7_soma_le_total'] = float(tg4.sum()) <= man['timing']['tempo_total_s']
    r['u7_soma_ger'] = float(tg4.sum()); r['u7_total'] = man['timing']['tempo_total_s']
    r['u7_aval_le_ger'] = man['timing']['tempo_aval_real_s'] <= float(tg4.sum())

    # ---------- U9 guards
    ch = [g for g in guards if g['name'] == 'cache_hit']
    r['u9_ch6'] = len(ch); r['u9_ch5'] = man['cache_hits']
    r['u9_chfooter'] = ftr[0]['cache_hits'] if ftr else None
    r['u9_ok'] = (len(ch) == man['cache_hits'] == (ftr[0]['cache_hits'] if ftr else -1))
    sids = set(real.solution_id.tolist())
    r['u9_sid_no1'] = all(g['solution_id'] in sids for g in ch)
    seedblk = [g for g in ch if g['fe'] == n_init]
    r['u9_seedblk'] = len(seedblk)
    r['u9_seedblk_sids'] = len({g['solution_id'] for g in seedblk})
    r['u9_seedblk_todos_doe'] = all(g['solution_id'] < n_init for g in seedblk) if seedblk else None
    r['u9_dup_arranque'] = (len(seedblk) == 21 and len({g['solution_id'] for g in seedblk}) == 20)
    r['u9_ch_prole'] = len(ch) - len(seedblk)

    # ---------- U10 aritmetica
    gsz = pop.groupby('geracao').size()
    r['u10_pop_20'] = bool((gsz == 20).all()); r['u10_n2'] = len(pop)
    r['u10_nger_man'] = man['n_geracoes']; r['u10_nger6'] = len(gens); r['u10_nger4'] = len(tim)
    r['u10_nger_eq'] = (man['n_geracoes'] == len(gens) == len(tim) == len(gsz))
    r['u10_D_mais_1'] = (man['n_geracoes'] == D + 1)
    r['u10_subset'] = set(pop.solution_id) <= sids

    # ---------- T11 formula geracoes_derivadas (2*floor(Nef/2))
    Nef = ftr[0]['N_efetivo'] if ftr else 20
    passo = 2 * (Nef // 2)
    r['t11_form_nova'] = math.floor((20 * D + man['cache_hits']) / passo)
    r['t11_form_nova_ok'] = (r['t11_form_nova'] == man['n_geracoes'])
    r['t11_form_nova_prole'] = math.floor((20 * D + r['u9_ch_prole']) / passo)
    r['t11_form_antiga'] = math.floor(20 * D / Nef)
    r['t11_form_ceil_f5'] = math.ceil(20 * D / Nef)

    # ---------- P1 seeding D88
    Fdoe = doe[[c for c in doe.columns if c.startswith('f')][:M]].to_numpy(np.float64)[:n_init]
    esc, fr = selec_d88(Fdoe, 20)
    g1 = sorted(pop[pop.geracao == 1].solution_id.tolist())
    r['p1_bate'] = (esc == g1)
    r['p1_inter'] = len(set(esc) & set(g1))
    r['p1_nfrentes_rec'] = seed_rec['n_frentes']; r['p1_nfrentes_calc'] = int(fr.max())
    r['p1_nf1_rec'] = seed_rec['n_frente1']; r['p1_nf1_calc'] = int((fr == 1).sum())
    r['p1_ndoe_rec'] = seed_rec['n_doe']
    r['p1_excede_rec'] = seed_rec['frente1_excede_pop']
    r['p1_excede_calc'] = bool(int((fr == 1).sum()) > 20)

    # ---------- P2 N=20
    r['p2_Nnom'] = man['params']['N_nominal']; r['p2_Nef'] = man['params']['N_efetivo']
    r['p2_npop_gen'] = sorted({g['n_pop'] for g in gens})
    r['p2_hdr_N'] = hdr['N_nominal']

    # ---------- P3 infill
    r['p3_infill'] = man['maxfe'] - n_init
    r['p3_20D'] = (r['p3_infill'] == 20 * D)

    # ---------- P4 elitismo / turnover
    viol = 0; turn = []
    fe_por_ger = {g['geracao']: g['fe'] for g in gens}
    for gg in range(1, man['n_geracoes']):
        a = pop[pop.geracao == gg].solution_id.tolist()
        b = pop[pop.geracao == gg + 1].solution_id.tolist()
        jan = set(real[(real.fe_index >= fe_por_ger[gg]) & (real.fe_index < fe_por_ger.get(gg + 1, 10 ** 9))].solution_id)
        permitido = set(a) | jan
        if not set(b) <= permitido:
            viol += 1
        from collections import Counter
        ca, cb = Counter(a), Counter(b)
        turn.append(sum((cb - ca).values()))
    r['p4_transicoes'] = man['n_geracoes'] - 1
    r['p4_violacoes'] = viol
    r['p4_turn_min'] = min(turn) if turn else None
    r['p4_turn_max'] = max(turn) if turn else None
    r['p4_turn_med'] = float(np.mean(turn)) if turn else None
    ult = set(pop[pop.geracao == man['n_geracoes']].solution_id)
    r['p4_doe_sobrevive'] = len([s for s in ult if s < n_init])

    # ---------- P5 monotonia ideal / f_best
    ide = np.array([g['ideal'] for g in gens], float)
    fb = np.array([g['f_best'] for g in gens], float)
    r['p5_fbest_eq_ideal'] = bool(np.array_equal(ide, fb))
    d = np.diff(ide, axis=0)
    r['p5_comp'] = int(d.size)
    r['p5_viol'] = int((d > 0).sum())
    r['p5_melhora'] = int((d < 0).sum())
    r['p5_estag'] = int((d == 0).sum())
    nf1 = np.array([g['nadir_front1'] for g in gens], float)
    npo = np.array([g['nadir_pop'] for g in gens], float)
    r['p5_nadirf1_le_pop'] = bool((nf1 <= npo + 1e-12).all())

    # ---------- P6 n_front1
    n1 = np.array([g['n_front1'] for g in gens])
    r['p6_le_N'] = bool((n1 <= 20).all()); r['p6_max'] = int(n1.max())
    r['p6_satura'] = bool((n1 == 20).any())
    r['p6_satura_g1'] = bool(n1[0] == 20)

    # ---------- P7 ledger clone-hazard
    ult_fe = gens[-1]['fe']
    r['p7_resto'] = man['maxfe'] - ult_fe
    r['p7_ch_prole'] = r['u9_ch_prole']
    r['p7_ledger_ok'] = (r['p7_resto'] == r['u9_ch_prole'])
    r['p7_slots'] = 20 * D
    r['p7_taxa'] = r['u9_ch_prole'] / (20 * D)
    dupg = pop.groupby('geracao').solution_id.apply(lambda s: len(s) - s.nunique())
    r['p7_clones2'] = int(dupg.sum()); r['p7_gens_com_clone'] = int((dupg > 0).sum())
    r['p7_clone_max'] = int(dupg.max())

    # ---------- P8 recomputo ideal/nadir
    mp = real.set_index('solution_id')[fc]
    errs = []
    n1rec_ok = 0
    for g in gens:
        ids = pop[pop.geracao == g['geracao']].solution_id.tolist()
        Fg = mp.loc[ids].to_numpy(np.float64)
        idr = Fg.min(axis=0); ndr = Fg.max(axis=0)
        errs.append(np.max(np.abs(idr - np.array(g['ideal'])) / np.maximum(np.abs(g['ideal']), 1e-30)))
        errs.append(np.max(np.abs(ndr - np.array(g['nadir_pop'])) / np.maximum(np.abs(g['nadir_pop']), 1e-30)))
        if int((ndsort(Fg) == 1).sum()) == g['n_front1']:
            n1rec_ok += 1
    r['p8_err_rel'] = float(max(errs))
    r['p8_n1_ok'] = n1rec_ok; r['p8_n1_tot'] = len(gens)

    # ---------- N3/N4 sanidade
    r['n4_nan'] = int(real[xc + fc].isna().sum().sum())
    r['n4_xmin'] = float(real[xc].to_numpy().min()); r['n4_xmax'] = float(real[xc].to_numpy().max())
    xk = real[xc].to_numpy(np.float32)
    _, cnt = np.unique(xk, axis=0, return_counts=True)
    r['n3_x_dup'] = int((cnt > 1).sum())
    r['n1_patches'] = man['params']['patches'][:20]
    r['n1_piso'] = hdr['piso']; r['n1_surrog'] = hdr['surrogate']
    r['n5_campos6'] = all(all(k in g for k in ('n_front1', 'f_best', 'ideal', 'nadir_pop')) for g in gens)
    r['n5_nadirf1'] = all('nadir_front1' in g for g in gens)
    r['n6_hdr_runid'] = 'run_id' in hdr
    r['n6_hdr_ambiente'] = 'ambiente' in hdr
    r['n6_hdr_sigma'] = 'sigma_dict' in hdr
    r['n6_hdr_campanha'] = 'campanha_id' in hdr
    r['n6_algo_version'] = man['algo_version']
    r['n6_matlab'] = man['env']['matlab']
    rows.append(r)
    print('.', end='', flush=True)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/aspectos_t11_nsga2.csv', index=False)
print('\n\n== AGREGADOS (25 celulas) ==')
print('U1  fe exato', df.u1_ok_fe.sum(), '| feidx denso', df.u1_feidx_denso.sum(),
      '| sid unicos', df.u1_sid_unicos.sum(), '| termino normal',
      (df.u1_termino == 'normal').sum(), '| hard_stop>0', (df.u1_hardstop > 0).sum(),
      '| footers', sorted(df.u1_nfooter.unique()), '| total FE', df.u1_len1.sum())
print('U2  dX max', df.u2_dX.max(), '| hash ok', df.u2_hash_ok.sum(), '| prefixo',
      df.u2_prefixo.sum(), '| cp_init', df.u2_cpinit.sum(), '| fases', df.u2_fases.unique())
print('U3  n3=0', (df.u3_n3 == 0).sum(), '| tempo nulos', (df.u3_tempo_nulos == df.u3_n4).sum(),
      '| n_acum NaN', (df.u3_nacum_nan == df.u3_n4).sum(), '| fit_series 0',
      (df.u3_fitseries == 0).sum(), '| sigma_dict presente', df.u3_sigma_dict_presente.sum(),
      '| tempo_aval_real nao-nulo', df.u3_tempo_aval_real.notna().sum())
print('U4  sonda nao_se_aplica', (df.u4_sonda_status == 'nao_se_aplica').sum(),
      '| rec sonda', df.u4_rec_sonda.sum())
print('T11 campanha_id', df.t11_campanha_id.sum(), '| repo_hash vazio',
      (df.t11_repo_hash == '').sum(), '| schema_version', sorted(df.t11_schema_version.unique()),
      '| REGRA_DO_ROTULO', df.t11_regra_rotulo.sum(), '| sonda_estratificada', df.t11_sonda_estrat.sum())
print('T11 formula nova acerta', df.t11_form_nova_ok.sum(), '/25 |',
      'antiga(20D/Nef)', (df.t11_form_antiga == df.u10_nger_man).sum(),
      '| ceil-F5', (df.t11_form_ceil_f5 == df.u10_nger_man).sum(),
      '| D+1', df.u10_D_mais_1.sum())
print('U7  gen6=ger4', (df.u7_n_gen6 == df.u7_n_ger4).sum(), '| dmax', df.u7_dmax.max(),
      '| seq', df.u7_ger_seq.sum(), '| soma<=total', df.u7_soma_le_total.sum(),
      '| aval<=ger', df.u7_aval_le_ger.sum(), '| Sigma tempo_ger', round(df.u7_soma_ger.sum(), 2),
      '| wall total', round(df.u7_total.sum(), 2))
print('U9  ch ok', df.u9_ok.sum(), '| sid na (1)', df.u9_sid_no1.sum(), '| seedblk=21',
      (df.u9_seedblk == 21).sum(), '| sids distintos=20', (df.u9_seedblk_sids == 20).sum(),
      '| dup arranque', df.u9_dup_arranque.sum(), '| ch total', df.u9_ch6.sum(),
      '| ch prole', df.u9_ch_prole.sum())
print('U10 pop=20', df.u10_pop_20.sum(), '| nger consistente', df.u10_nger_eq.sum(),
      '| n_ger=D+1', df.u10_D_mais_1.sum(), '| subset', df.u10_subset.sum(),
      '| linhas (2)', df.u10_n2.sum())
print('P1  D88 bate', df.p1_bate.sum(), '| nfrentes ok', (df.p1_nfrentes_rec == df.p1_nfrentes_calc).sum(),
      '| nf1 ok', (df.p1_nf1_rec == df.p1_nf1_calc).sum(),
      '| excede ok', (df.p1_excede_rec == df.p1_excede_calc).sum(),
      '| excede True', df.p1_excede_rec.sum())
print('P2  N nominal', sorted(df.p2_Nnom.unique()), '| N efetivo', sorted(df.p2_Nef.unique()),
      '| n_pop', set(map(tuple, df.p2_npop_gen)))
print('P3  infill=20D', df.p3_20D.sum())
print('P4  violacoes', df.p4_violacoes.sum(), '| transicoes', df.p4_transicoes.sum(),
      '| turn min', df.p4_turn_min.min(), 'max', df.p4_turn_max.max(),
      'media', round(float((df.p4_turn_med * df.p4_transicoes).sum() / df.p4_transicoes.sum()), 3),
      '| turn==0 em alguma celula', (df.p4_turn_min == 0).sum())
print('P5  comparacoes', df.p5_comp.sum(), '| violacoes', df.p5_viol.sum(), '| melhoras',
      df.p5_melhora.sum(), '| estag', df.p5_estag.sum(), '| fbest==ideal', df.p5_fbest_eq_ideal.sum(),
      '| nadirf1<=pop', df.p5_nadirf1_le_pop.sum())
print('P6  n1<=N', df.p6_le_N.sum(), '| satura', df.p6_satura.sum(), '| satura g1', df.p6_satura_g1.sum())
print('P7  ledger ok', df.p7_ledger_ok.sum(), '| ch prole', df.p7_ch_prole.sum(), '/', df.p7_slots.sum(),
      '=', round(100 * df.p7_ch_prole.sum() / df.p7_slots.sum(), 3), '% | clones (2)',
      df.p7_clones2.sum(), 'em', df.p7_gens_com_clone.sum(), 'gens (max', df.p7_clone_max.max(), ')')
print('P8  err rel max', df.p8_err_rel.max(), '| n1 recomp ok', df.p8_n1_ok.sum(), '/', df.p8_n1_tot.sum())
print('N3  celulas com X duplicado', (df.n3_x_dup > 0).sum(), '| pares', df.n3_x_dup.sum())
print('N4  NaN', df.n4_nan.sum())
print('N5  campos (6)', df.n5_campos6.sum(), '| nadir_front1', df.n5_nadirf1.sum())
print('N6  hdr run_id', df.n6_hdr_runid.sum(), '| ambiente', df.n6_hdr_ambiente.sum(),
      '| sigma_dict', df.n6_hdr_sigma.sum(), '| campanha_id', df.n6_hdr_campanha.sum(),
      '| algo_version', df.n6_algo_version.unique(), '| matlab', df.n6_matlab.unique())
print('\nCelulas onde a formula NOVA erra:',
      df.loc[~df.t11_form_nova_ok, ['problema', 'D', 'u10_nger_man', 't11_form_nova', 'u9_ch6']].to_dict('records'))
