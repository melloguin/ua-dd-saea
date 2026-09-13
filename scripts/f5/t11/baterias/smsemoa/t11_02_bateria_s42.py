#!/usr/bin/env python
"""T11/smsemoa — bateria 2: RE-MEDIÇÃO das 25 células da s42 (corpus do MECANISMO).
READ-ONLY. Nada roda célula; nada toca data/experiments.
Saída: aspectos_t11_smsemoa.csv em f5/t11/baterias/smsemoa/.
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado'
S42 = f'{ROOT}/resultados_experimentos/smsemoa'
DOE = f'{ROOT}/ua-dd-saea/data/doe'
OUT = f'{ROOT}/ua-dd-saea/f5/t11/baterias/smsemoa'
PROBS = sorted(os.listdir(S42))

CONTRATO61 = json.load(open(f'{ROOT}/ua-dd-saea/claude_code_context/artifacts/contrato_61.json'))
MAPATERM = json.load(open(f'{ROOT}/ua-dd-saea/claude_code_context/artifacts/mapa_termino.json'))
DI10 = CONTRATO61['configs']['smsemoa']['di10']
MINIMO = CONTRATO61['minimo_comum_di10']['campos']
QUINTO = CONTRATO61['quinto_obrigatorio']['campos']
NAOAPL = set(CONTRATO61['configs']['smsemoa']['nao_se_aplica'])


def cell(p):
    d = f'{S42}/{p}/42'
    stem = [f[:-len('.manifest.json')] for f in os.listdir(d) if f.endswith('.manifest.json')][0]
    m = json.load(open(f'{d}/{stem}.manifest.json'))
    L = [json.loads(l) for l in open(f'{d}/{stem}.jsonl')]
    dfs = {k: pd.read_parquet(f'{d}/{stem}__{k}.parquet') for k in ['real', 'pop', 'surrogate', 'timing']}
    return m, L, dfs


def ndsort(F):
    n = len(F)
    fr = np.zeros(n, int)
    rem = np.arange(n)
    k = 1
    while len(rem):
        A = F[rem]
        dom = (A[:, None, :] <= A[None, :, :]).all(2) & (A[:, None, :] < A[None, :, :]).any(2)
        nd = ~dom.any(0)
        fr[rem[nd]] = k
        rem = rem[~nd]
        k += 1
    return fr


def ndsort_estrito(F):
    """dominância que exige DESIGUALDADE em todas as coords (empate => incomparável)."""
    n = len(F)
    fr = np.zeros(n, int)
    rem = np.arange(n)
    k = 1
    while len(rem):
        A = F[rem]
        dom = (A[:, None, :] < A[None, :, :]).all(2)
        nd = ~dom.any(0)
        fr[rem[nd]] = k
        rem = rem[~nd]
        k += 1
    return fr


def crowding(F, fr):
    cd = np.zeros(len(F))
    for f in np.unique(fr):
        idx = np.where(fr == f)[0]
        sub = F[idx]
        c = np.zeros(len(idx))
        for j in range(F.shape[1]):
            o = np.argsort(sub[:, j], kind='stable')
            c[o[0]] = c[o[-1]] = np.inf
            rng = sub[o[-1], j] - sub[o[0], j]
            if rng > 0 and len(idx) > 2:
                c[o[1:-1]] += (sub[o[2:], j] - sub[o[:-2], j]) / rng
        cd[idx] = c
    return cd


rows = []
for p in PROBS:
    m, L, dfs = cell(p)
    r = {'problema': p}
    R, P, S, T = dfs['real'], dfs['pop'], dfs['surrogate'], dfs['timing']
    hdr = [x for x in L if x['rec'] == 'header'][0]
    ftr = [x for x in L if x['rec'] == 'footer']
    seed_ev = [x for x in L if x['rec'] == 'seeding'][0]
    gens = [x for x in L if x['rec'] == 'smsemoa_gen']
    guards = [x for x in L if x['rec'] == 'guard']
    D, M = hdr['D'], hdr['M']
    r['D'], r['M'] = D, M
    n_init, maxfe = 11 * D - 1, 31 * D - 1

    # ---- U1 orçamento
    r['U1_fe_exato'] = (len(R) == maxfe) and (m['fe_final'] == maxfe) and (m['maxfe'] == maxfe)
    r['U1_fe_index_denso'] = bool((R['fe_index'].values == np.arange(len(R))).all())
    r['U1_sid_denso'] = bool((R['solution_id'].values == np.arange(len(R))).all())
    r['U1_init'] = int((R['fase'] == 'init').sum())
    r['U1_opt'] = int((R['fase'] == 'opt').sum())
    r['U1_init_ok'] = r['U1_init'] == n_init
    r['U1_opt_ok'] = r['U1_opt'] == 20 * D

    # ---- U2 DoE bit-a-bit
    doe = pd.read_parquet(f'{DOE}/{p}/doe_{p}_42.parquet')
    dm = json.load(open(f'{DOE}/{p}/doe_{p}_42.manifest.json'))
    xc = [c for c in R.columns if c.startswith('x') and c[1:].isdigit()]
    dxc = [c for c in doe.columns if c.startswith('x') and c[1:].isdigit()]
    Xr = R.loc[R['fase'] == 'init', xc].values[:, :D]
    Xd = doe[sorted(dxc, key=lambda s: int(s[1:]))].values[:, :D]
    r['U2_ndoe'] = len(doe)
    r['U2_dX_f32'] = float(np.abs(Xr.astype(np.float32) - Xd.astype(np.float32)).max())
    r['U2_dX_f64'] = float(np.abs(Xr - Xd).max())
    r['U2_hash_ok'] = (m['doe_hash'] == dm.get('hash', dm.get('x_hash')))

    # ---- N=20 em todas as gerações
    r['n_ger_manifesto'] = m['n_geracoes']
    r['n_ger_jsonl'] = len(gens)
    r['n_ger_pop'] = int(P['geracao'].nunique())
    r['n_ger_timing'] = len(T)
    r['npop_sempre20'] = all(g['n_pop'] == 20 for g in gens)
    r['pop_20_por_ger'] = bool((P.groupby('geracao').size() == 20).all())
    r['pop_dup_intra'] = int(P.groupby('geracao')['solution_id'].apply(lambda s: s.duplicated().sum()).sum())
    r['N_nom'], r['N_ef'] = m['params']['N_nominal'], m['params']['N_efetivo']

    # ---- Δfe / cache-hits / fechamento
    fes = [g['fe'] for g in gens]
    dfe = np.diff(fes)
    r['dfe_igual20'] = int((dfe == 20).sum())
    r['dfe_total'] = len(dfe)
    r['dfe_valores'] = str(sorted(set(dfe.tolist()))) if len(dfe) else ''
    ch = [g for g in guards if g['name'] == 'cache_hit']
    hs = [g for g in guards if g['name'] != 'cache_hit']
    r['n_guards'] = len(guards)
    r['n_cache_hit'] = len(ch)
    r['guards_outros'] = str(sorted(set(g['name'] for g in hs)))
    ch_seed = [g for g in ch if g['fe'] == n_init]
    r['ch_seeding'] = len(ch_seed)
    r['ch_seeding_sid_unicos'] = len(set(g['solution_id'] for g in ch_seed))
    r['ch_evolucao'] = len(ch) - len(ch_seed)
    r['cache_hits_manifesto'] = m['cache_hits']
    r['cache_hits_bate'] = m['cache_hits'] == len(ch)
    # fechamento: N*(n_ger-1) = soma dfe + cache-hits de evolução atribuídos por ORDEM
    r['fechamento'] = 20 * (len(gens) - 1) == int(dfe.sum()) + (len(ch) - len(ch_seed)) if len(gens) > 1 else None
    # o sid repetido do seeding é a posição 0 de ②(g=1)?
    from collections import Counter
    cnt = Counter(g['solution_id'] for g in ch_seed)
    rep = [k for k, v in cnt.items() if v > 1]
    g1 = P[P['geracao'] == P['geracao'].min()]['solution_id'].values
    r['ch_seed_repetido'] = rep[0] if rep else None
    r['ch_seed_rep_eh_pos0'] = (len(rep) == 1 and rep[0] == g1[0])

    # ---- ERRATA 5 / I-13: geracoes_derivadas EMERGENTE
    nef = m['params']['N_efetivo']
    ndup = len(ch) - len(ch_seed)
    r['ger_formula_T11'] = int(np.floor((20 * D + ndup) / (2 * np.floor(nef / 2))))
    r['ger_formula_T11_ok'] = r['ger_formula_T11'] == m['n_geracoes']
    r['ger_formula_antiga'] = int(20 * D / nef)
    r['ger_formula_antiga_ok'] = r['ger_formula_antiga'] == m['n_geracoes']
    r['ger_formula_ceil_F5'] = int(np.ceil(20 * D / nef))
    r['ger_formula_ceil_ok'] = r['ger_formula_ceil_F5'] == m['n_geracoes']
    r['ger_T11_mais1'] = (r['ger_formula_T11'] + 1) == m['n_geracoes']

    # ---- ③ vazia / sonda / sigma_dict
    r['tres_linhas'] = len(S)
    r['tres_cols'] = S.shape[1]
    r['fit_series_vazio'] = (m['fit_series'] == [])
    r['sonda_status'] = m['sonda']['status']
    r['sonda_nblocos'] = m['sonda']['n_blocos']
    r['sigma_dict_presente'] = 'sigma_dict' in m
    r['campanha_id_presente'] = 'campanha_id' in m
    r['repo_hash'] = m.get('repo_hash', '<AUSENTE>')
    r['schema_version'] = m.get('schema_version')
    r['quinto_faltando'] = str(sorted([k for k in QUINTO if k not in m or m.get(k) in ('', None)]))
    r['params_nkeys'] = len(m['params'])
    r['params_ger_deriv_novo'] = m['params']['geracoes_derivadas'].startswith('EMERGENTE')

    # ---- término (mapa_termino I-08)
    r['n_footer'] = len(ftr)
    r['footer_termino'] = ftr[0].get('termino') if ftr else None
    r['motivo_parada_no_5'] = 'motivo_parada' in m
    r['campo_termino_mapa'] = MAPATERM['configs']['smsemoa']['campo_termino']
    r['mapa_termino_confere'] = (ftr[0].get(MAPATERM['configs']['smsemoa']['campo_termino']) is not None
                                 and len(ftr) in MAPATERM['configs']['smsemoa']['n_footers_esperado'])
    r['evento_ger_mapa_ok'] = MAPATERM['configs']['smsemoa']['evento_geracao']['rec'] == 'smsemoa_gen'
    r['status'] = m['status']

    # ---- contrato_61 (G-7): campos DI-10 em TODOS os eventos de geração
    campos = [c for c in set(MINIMO + DI10) if c not in NAOAPL]
    r['di10_campos_exigidos'] = str(sorted(campos))
    r['di10_completo_em'] = sum(all(c in g for c in campos) for g in gens)
    r['di10_de'] = len(gens)

    # ---- timing (④/⑤)
    r['T_rows_ok'] = len(T) == m['n_geracoes']
    for c in ['tempo_fit_s', 'tempo_busca_s', 'tempo_pred_sonda_s']:
        r[f'T_{c}_nan'] = float(T[c].isna().mean()) if c in T.columns else None
    r['T_tger_pos'] = int((T['tempo_geracao_s'] > 0).sum()) if 'tempo_geracao_s' in T.columns else None
    r['tempo_total_s'] = m['timing']['tempo_total_s']
    r['tempo_aval_real_s'] = m['timing']['tempo_aval_real_s']
    r['soma_tger'] = float(T['tempo_geracao_s'].sum()) if 'tempo_geracao_s' in T.columns else None
    r['tger_le_total'] = r['soma_tger'] <= r['tempo_total_s']
    tg6 = np.array([g['tempo_geracao_s'] for g in gens])
    r['tger_4_eq_6'] = bool(np.allclose(np.sort(tg6), np.sort(T['tempo_geracao_s'].values), rtol=1e-5))

    # ---- elitismo (μ+1) + recomputo ideal/nadir/n_front1
    fc = [c for c in R.columns if c.startswith('f') and c[1:].isdigit()]
    Fall = R[fc].values.astype(np.float64)
    gl = sorted(P['geracao'].unique())
    viol = 0
    entrantes = []
    for a, b in zip(gl[:-1], gl[1:]):
        sa = set(P[P['geracao'] == a]['solution_id'])
        sb = set(P[P['geracao'] == b]['solution_id'])
        fa = [g['fe'] for g in gens if g['geracao'] == a][0]
        fb = [g['fe'] for g in gens if g['geracao'] == b][0]
        novos = set(range(fa, fb))
        if not sb <= (sa | novos):
            viol += 1
        entrantes.append(len(sb - sa))
    r['transicoes'] = len(gl) - 1
    r['elitismo_viol'] = viol
    r['entrantes_med'] = float(np.mean(entrantes)) if entrantes else None
    r['entrantes_max'] = int(np.max(entrantes)) if entrantes else None

    okI = okNp = okNf1 = okNf = 0
    fr32_div = 0
    dentro_env = 0
    empates_div, empates_conc = [], []
    for g in gens:
        gg = g['geracao']
        sid = P[P['geracao'] == gg]['solution_id'].values
        F = Fall[sid]
        okI += int(np.allclose(F.min(0), np.array(g['ideal'], float), rtol=0, atol=1e-12))
        okNp += int(np.allclose(F.max(0), np.array(g['nadir_pop'], float), rtol=0, atol=1e-12))
        fr = ndsort(F)
        n1 = int((fr == 1).sum())
        okNf1 += int(n1 == g['n_front1'])
        if n1 != g['n_front1']:
            fr32_div += 1
        fre = ndsort_estrito(F)
        n1e = int((fre == 1).sum())
        lo, hi = min(n1, n1e), max(n1, n1e)
        dentro_env += int(lo <= g['n_front1'] <= hi)
        # empates de coordenada
        emp = sum(len(F[:, j]) - len(np.unique(F[:, j])) for j in range(F.shape[1]))
        (empates_div if n1 != g['n_front1'] else empates_conc).append(emp)
        if g.get('nadir_front1'):
            okNf += int(np.allclose(F[fr == 1].max(0), np.array(g['nadir_front1'], float), rtol=0, atol=1e-12))
    r['rec_ideal_ok'] = okI
    r['rec_nadir_pop_ok'] = okNp
    r['rec_n_front1_ok'] = okNf1
    r['rec_nadir_f1_ok'] = okNf
    r['f32_divergentes'] = fr32_div
    r['f32_dentro_envelope'] = dentro_env
    r['empates_med_div'] = float(np.mean(empates_div)) if empates_div else None
    r['empates_med_conc'] = float(np.mean(empates_conc)) if empates_conc else None
    r['f_best_eq_ideal'] = sum(int(g['f_best'] == g['ideal']) for g in gens)

    # ---- seeding D88 recomputado
    F0 = Fall[:n_init]
    fr0 = ndsort(F0)
    cd0 = crowding(F0, fr0)
    ordem = np.lexsort((np.arange(n_init), -cd0, fr0))
    sel = set(ordem[:20].tolist())
    r['seed_nfrentes_log'] = seed_ev['n_frentes']
    r['seed_nf1_log'] = seed_ev['n_frente1']
    r['seed_nfrentes_rec'] = int(fr0.max())
    r['seed_nf1_rec'] = int((fr0 == 1).sum())
    r['seed_conjunto_ok'] = sel == set(g1.tolist())
    r['seed_f1_excede'] = seed_ev['frente1_excede_pop']

    # ---- declarativos
    r['patches'] = m['params']['patches'][:12]
    r['parameter_nenhum'] = m['params']['parameter'].startswith('nenhum')
    r['operadores_hdr'] = hdr['operadores'][:30]
    r['algo_version'] = m['algo_version']
    r['hdr_run_id'] = 'run_id' in hdr
    r['hdr_ambiente'] = 'ambiente' in hdr
    r['hdr_sigma_dict'] = 'sigma_dict' in hdr
    rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/aspectos_t11_smsemoa.csv', index=False)
pd.set_option('display.width', 250, 'display.max_columns', 200)

print('==== 25 CÉLULAS · RESUMO (n=%d) ====' % len(df))


def agg(col, how='all'):
    s = df[col]
    if how == 'all':
        return f'{int(s.sum())}/{len(s)}'
    return s


for c in ['U1_fe_exato', 'U1_fe_index_denso', 'U1_sid_denso', 'U1_init_ok', 'U1_opt_ok',
          'U2_hash_ok', 'npop_sempre20', 'pop_20_por_ger', 'cache_hits_bate',
          'ch_seed_rep_eh_pos0', 'fit_series_vazio', 'sigma_dict_presente',
          'campanha_id_presente', 'motivo_parada_no_5', 'mapa_termino_confere',
          'evento_ger_mapa_ok', 'T_rows_ok', 'tger_le_total', 'tger_4_eq_6',
          'params_ger_deriv_novo', 'ger_formula_T11_ok', 'ger_formula_antiga_ok',
          'ger_formula_ceil_ok', 'ger_T11_mais1', 'seed_conjunto_ok', 'parameter_nenhum',
          'hdr_run_id', 'hdr_ambiente', 'hdr_sigma_dict']:
    print(f'{c:26s} {agg(c)}')

print()
print('dX f32 max  =', df['U2_dX_f32'].max(), ' | dX f64 max =', df['U2_dX_f64'].max())
print('n_ger: manif==jsonl==pop==timing:',
      int(((df.n_ger_manifesto == df.n_ger_jsonl) & (df.n_ger_manifesto == df.n_ger_pop) &
           (df.n_ger_manifesto == df.n_ger_timing)).sum()), '/', len(df))
print('n_ger == D+1:', int((df.n_ger_manifesto == df.D + 1).sum()), '/', len(df))
print('Δfe==20:', int(df.dfe_igual20.sum()), '/', int(df.dfe_total.sum()),
      '| células com exceção:', df.loc[df.dfe_igual20 != df.dfe_total, ['problema', 'dfe_valores']].to_dict('records'))
print('guards:', int(df.n_guards.sum()), '| cache_hit:', int(df.n_cache_hit.sum()),
      '| seeding:', int(df.ch_seeding.sum()), '| evolução:', int(df.ch_evolucao.sum()),
      '| outros:', df.guards_outros.value_counts().to_dict())
print('fechamento aritmético:', int(df.fechamento.fillna(False).sum()), '/', len(df))
print('③ linhas:', df.tres_linhas.unique(), '| colunas:', sorted(df.tres_cols.unique()))
print('sonda status:', df.sonda_status.unique(), '| n_blocos:', df.sonda_nblocos.unique())
print('repo_hash valores:', df.repo_hash.unique(), '| schema_version:', df.schema_version.unique())
print('quinto faltando (⑤):', df.quinto_faltando.value_counts().to_dict())
print('footers:', df.n_footer.value_counts().to_dict(), '| termino:', df.footer_termino.value_counts().to_dict())
print('DI-10 (contrato_61) completo:', int(df.di10_completo_em.sum()), '/', int(df.di10_de.sum()),
      '| campos:', df.di10_campos_exigidos.iloc[0])
print('elitismo violações:', int(df.elitismo_viol.sum()), 'em', int(df.transicoes.sum()), 'transições',
      '| entrantes médios:', round(float((df.entrantes_med * df.transicoes).sum() / df.transicoes.sum()), 2),
      '| máx:', int(df.entrantes_max.max()))
tot = int(df.n_ger_jsonl.sum())
print(f'recomputo (de {tot} gerações): ideal {int(df.rec_ideal_ok.sum())} · nadir_pop {int(df.rec_nadir_pop_ok.sum())}'
      f' · n_front1 {int(df.rec_n_front1_ok.sum())} · nadir_front1 {int(df.rec_nadir_f1_ok.sum())}'
      f' · f_best==ideal {int(df.f_best_eq_ideal.sum())}')
print('float32: divergentes', int(df.f32_divergentes.sum()), '| dentro do envelope [fraco,estrito]',
      int(df.f32_dentro_envelope.sum()), '/', tot)
print('empates médios: divergentes %.2f × concordantes %.2f' % (
    float(np.nansum(df.empates_med_div * df.f32_divergentes) / max(df.f32_divergentes.sum(), 1)),
    float(np.nansum(df.empates_med_conc * (df.n_ger_jsonl - df.f32_divergentes)) /
          max((df.n_ger_jsonl - df.f32_divergentes).sum(), 1))))
print('seeding: n_frentes log==rec', int((df.seed_nfrentes_log == df.seed_nfrentes_rec).sum()), '/', len(df),
      '| n_f1 log==rec', int((df.seed_nf1_log == df.seed_nf1_rec).sum()), '/', len(df),
      '| conjunto ②(1) recomputado ok', int(df.seed_conjunto_ok.sum()), '/', len(df),
      '| f1>N em', int(df.seed_f1_excede.sum()))
print('tempo: Σ total %.2f s | Σ tger %.2f s | Σ aval_real %.2f s | mediana %.2f | max %.2f (%s)' % (
    df.tempo_total_s.sum(), df.soma_tger.sum(), df.tempo_aval_real_s.sum(),
    df.tempo_total_s.median(), df.tempo_total_s.max(), df.loc[df.tempo_total_s.idxmax(), 'problema']))
print('T NULL: fit %.0f%% busca %.0f%% pred_sonda %.0f%%' % (
    100 * df.T_tempo_fit_s_nan.mean(), 100 * df.T_tempo_busca_s_nan.mean(), 100 * df.T_tempo_pred_sonda_s_nan.mean()))
print()
print('--- ERRATA 5 / I-13 · fórmula de gerações, célula a célula (só as que a fórmula T11 erra) ---')
bad = df[~df.ger_formula_T11_ok][['problema', 'D', 'n_ger_manifesto', 'ger_formula_T11',
                                  'ch_evolucao', 'ger_formula_antiga', 'ger_formula_ceil_F5']]
print(bad.to_string(index=False) if len(bad) else 'nenhuma')
print()
print('--- hard-stop / geração fantasma ---')
print(df[df.n_cache_hit > 21][['problema', 'D', 'n_ger_manifesto', 'n_cache_hit', 'ch_evolucao',
                               'guards_outros', 'U1_opt', 'dfe_valores']].to_string(index=False))
print('escrito:', f'{OUT}/aspectos_t11_smsemoa.csv')
