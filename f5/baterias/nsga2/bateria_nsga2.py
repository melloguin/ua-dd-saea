#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BATERIA DE FIDELIDADE — config `nsga2` (NSGA-II piso online, PlatEMO 4.15)
F5.3b · protocolo v1.1 · semente 42 · 25 células main · dados READ-ONLY.

Executa TODAS as queries dos aspectos U* (universais aplicáveis), P* (módulo de família
"piso online / MOEA puro") e N* (específicos do bundle alg_pisos_online.md).
Escreve evidência em CSV/pickle nesta mesma pasta (único local de escrita permitido).
"""
import json, os, sys, hashlib, pickle
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
DADOS = f'{RAIZ}/resultados_experimentos/nsga2'
DOE = f'{RAIZ}/ua-dd-saea/data/doe'
F5 = f'{RAIZ}/ua-dd-saea/f5'
OUT = f'{F5}/baterias/nsga2'
os.makedirs(OUT, exist_ok=True)

CARACT = pd.read_csv(f'{RAIZ}/ua-dd-saea/claude_code_context/artifacts/characteristics.csv').set_index('problema')
PROBS = sorted(os.listdir(DADOS))
PROBS = [p for p in PROBS if not p.startswith('.')]


def carrega(prob):
    b = f'{DADOS}/{prob}/42/exp_main_nsga2_{prob}_42'
    man = json.load(open(b + '.manifest.json'))
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    real = pq.read_table(b + '__real.parquet').to_pandas()
    pop = pq.read_table(b + '__pop.parquet').to_pandas()
    sur = pq.read_table(b + '__surrogate.parquet').to_pandas()
    tim = pq.read_table(b + '__timing.parquet').to_pandas()
    return man, recs, real, pop, sur, tim


# ---------------------------------------------------------------- NDSort + Crowding (PlatEMO)
def nd_sort(F):
    """Fronteiras de não-dominância (1-based), semântica PlatEMO/ENS."""
    n = len(F)
    front = np.zeros(n, dtype=int)
    resto = np.arange(n)
    k = 1
    while len(resto):
        Fr = F[resto]
        dominado = np.zeros(len(resto), dtype=bool)
        for i in range(len(resto)):
            le = np.all(Fr <= Fr[i], axis=1)
            lt = np.any(Fr < Fr[i], axis=1)
            if np.any(le & lt):
                dominado[i] = True
        atual = resto[~dominado]
        front[atual] = k
        resto = resto[dominado]
        k += 1
    return front


def crowding(F, front):
    """CrowdingDistance do PlatEMO (por fronteira, normalizada por (fmax-fmin))."""
    n, M = F.shape
    cd = np.zeros(n)
    for f in np.unique(front):
        idx = np.where(front == f)[0]
        Fi = F[idx]
        d = np.zeros(len(idx))
        for j in range(M):
            ordem = np.argsort(Fi[:, j], kind='stable')
            fmin, fmax = Fi[ordem[0], j], Fi[ordem[-1], j]
            d[ordem[0]] = np.inf
            d[ordem[-1]] = np.inf
            if fmax - fmin > 0 and len(idx) > 2:
                d[ordem[1:-1]] += (Fi[ordem[2:], j] - Fi[ordem[:-2], j]) / (fmax - fmin)
        cd[idx] = d
    return cd


def selecao_d88(F, N):
    """Seleção D88: melhores N por NDSort + CrowdingDistance, desempate por índice."""
    front = nd_sort(F)
    cd = crowding(F, front)
    ordem = np.lexsort((np.arange(len(F)), -cd, front))  # front asc, cd desc, idx asc
    return np.sort(ordem[:N]), front, cd


# ---------------------------------------------------------------- bateria por célula
linhas = []
evid = {}
for prob in PROBS:
    man, recs, real, pop, sur, tim = carrega(prob)
    D = int(CARACT.loc[prob, 'D']); M = int(CARACT.loc[prob, 'M'])
    r = {'problema': prob, 'D': D, 'M': M}
    header = [x for x in recs if x['rec'] == 'header'][0]
    seed_rec = [x for x in recs if x['rec'] == 'seeding']
    gens = [x for x in recs if x['rec'] == 'nsga2_gen']
    guards = [x for x in recs if x['rec'] == 'guard']
    footers = [x for x in recs if x['rec'] == 'footer']
    import re
    xcols = [c for c in real.columns if re.fullmatch(r'x\d+', c)]
    fcols = [c for c in real.columns if re.fullmatch(r'f\d+', c)]
    assert len(xcols) == D and len(fcols) == M, (prob, len(xcols), len(fcols))

    # ---- U1 orçamento / término
    r['maxfe'] = man['maxfe']; r['maxfe_esperado'] = 31 * D - 1
    r['u1_maxfe_ok'] = (man['maxfe'] == 31 * D - 1)
    r['u1_len_real'] = len(real)
    r['u1_len_ok'] = (len(real) == 31 * D - 1)
    r['u1_fe_final_ok'] = (man['fe_final'] == man['maxfe'])
    r['u1_feindex_denso'] = bool((real['fe_index'].values == np.arange(len(real))).all())
    r['u1_sid_unicos'] = int(real['solution_id'].nunique())
    xb = np.ascontiguousarray(real[xcols].values.astype(np.float32)).tobytes()
    arr = np.frombuffer(xb, dtype=np.float32).reshape(len(real), len(xcols))
    r['u1_dupX'] = int(len(real) - len(np.unique(arr, axis=0)))
    r['u1_status'] = man['status']; r['u1_nretries'] = man['n_retries']
    r['u1_termino'] = footers[0].get('termino') if footers else None
    r['u1_n_footers'] = len(footers)
    r['u1_fallback'] = man['fallback_ativado']
    r['u1_hardstop_guards'] = sum(1 for g in guards if g['name'] == 'hard_stop')

    # ---- U2 DoE
    r['u2_n_init'] = int((real['fase'] == 'init').sum())
    r['u2_init_ok'] = (r['u2_n_init'] == 11 * D - 1)
    doe_p = f'{DOE}/{prob}/doe_{prob}_42.parquet'
    doe = pq.read_table(doe_p).to_pandas()
    doe_man = json.load(open(f'{DOE}/{prob}/doe_{prob}_42.manifest.json'))
    dxc = [c for c in doe.columns if re.fullmatch(r"x\d+", c)]
    Xdoe = doe[dxc].values.astype(np.float32)
    Xini = real.loc[real['fase'] == 'init', xcols].values.astype(np.float32)
    r['u2_dX_max'] = float(np.abs(Xdoe[:len(Xini)] - Xini).max()) if len(Xini) == len(Xdoe) else np.nan
    hsc = doe_man.get('hash') or doe_man.get('doe_hash') or doe_man.get('sha256')
    r['u2_hash_ok'] = (man['doe_hash'] == hsc)
    r['u2_cp_init'] = footers[0].get('cp_init') if footers else None
    r['u2_init_prefixo'] = bool((real['fase'].values[:r['u2_n_init']] == 'init').all()
                                and (real['fase'].values[r['u2_n_init']:] != 'init').all())
    r['u2_fases'] = '|'.join(sorted(real['fase'].unique()))

    # ---- U3/U6/U8/U11 sem surrogate
    r['u3_sur_linhas'] = len(sur)
    r['u3_tempo_fit_null'] = bool(tim['tempo_fit_s'].isna().all())
    r['u3_tempo_busca_null'] = bool(tim['tempo_busca_s'].isna().all())
    r['u3_tempo_sonda_null'] = bool(tim['tempo_pred_sonda_s'].isna().all())
    r['u3_sigma_dict'] = 'sigma_dict' in man
    r['u3_sonda_status'] = man['sonda']['status']
    r['u3_sonda_nblocos'] = man['sonda']['n_blocos']
    r['u3_fit_series_vazia'] = (len(man['fit_series']) == 0)
    r['u3_timing_fit_null_man'] = (man['timing']['tempo_fit_surrogate_s'] is None)
    r['u3_timing_busca_null_man'] = (man['timing']['tempo_busca_s'] is None)
    r['u3_timing_sonda_null_man'] = (man['timing']['tempo_pred_sonda_s'] is None)

    # ---- U7 timing
    r['u7_n_tim'] = len(tim)
    r['u7_len_ok'] = (len(tim) == len(gens))
    r['u7_ger_seq'] = bool((tim['geracao'].values == np.arange(1, len(tim) + 1)).all())
    tg_jsonl = np.array([g['tempo_geracao_s'] for g in gens])
    r['u7_dt_max'] = float(np.abs(tim['tempo_geracao_s'].values - tg_jsonl).max()) if len(tim) == len(gens) else np.nan
    r['u7_soma_ger'] = float(tim['tempo_geracao_s'].sum())
    r['u7_total'] = man['timing']['tempo_total_s']
    r['u7_soma_le_total'] = bool(r['u7_soma_ger'] <= r['u7_total'] + 1e-9)
    r['u7_aval_real'] = man['timing']['tempo_aval_real_s']
    r['u7_nacum'] = '|'.join(str(v) for v in sorted(tim['n_acumulado'].unique())[:3])
    r['u7_nacum_eq_fe'] = bool((tim['n_acumulado'].values == np.array([g['fe'] for g in gens])).all()) if len(tim) == len(gens) else None

    # ---- U9 guards x manifesto x footer
    ch = sum(1 for g in guards if g['name'] == 'cache_hit')
    r['u9_cache_guards'] = ch
    r['u9_cache_man'] = man['cache_hits']
    r['u9_cache_footer'] = footers[0].get('cache_hits') if footers else None
    r['u9_recon_ok'] = (ch == man['cache_hits'] == (footers[0].get('cache_hits') if footers else -1))
    r['u9_guard_nomes'] = '|'.join(sorted(set(g['name'] for g in guards)))
    # c0: cache-hit no arranque (fe == n_init, solution_id do doe)
    ch_g = [g for g in guards if g['name'] == 'cache_hit']
    r['u9_ch_fe_min'] = min((g['fe'] for g in ch_g), default=None)
    r['u9_ch_no_init'] = sum(1 for g in ch_g if g['fe'] <= r['u2_n_init'])
    # cache-hit aponta para solution_id existente?
    sids = set(real['solution_id'].tolist())
    r['u9_ch_sid_valido'] = all(g['solution_id'] in sids for g in ch_g)

    # ---- U10 aritmética entre camadas (② e o ledger de FE)
    r['u10_n_gen_man'] = man['n_geracoes']
    r['u10_n_gen_jsonl'] = len(gens)
    r['u10_gen_ok'] = (man['n_geracoes'] == len(gens))
    gsz = pop.groupby('geracao').size()
    r['u10_pop_ngrupos'] = int(len(gsz))
    r['u10_pop_N_const'] = bool((gsz.values == gsz.values[0]).all())
    r['u10_pop_N'] = int(gsz.values[0])
    r['u10_pop_linhas'] = len(pop)
    r['u10_pop_linhas_ok'] = (len(pop) == r['u10_pop_ngrupos'] * r['u10_pop_N'])
    r['u10_pop_gers'] = '%d..%d' % (pop['geracao'].min(), pop['geracao'].max())
    # ledger: fe(g+1) - fe(g) == N - cache_hits ocorridos na janela
    fes = np.array([g['fe'] for g in gens])
    dfe = np.diff(fes)
    ch_fes = np.array(sorted(g['fe'] for g in ch_g))
    viol = 0; det = []
    for i in range(len(dfe)):
        lo, hi = fes[i], fes[i + 1]
        nch = int(((ch_fes > lo) & (ch_fes <= hi)).sum())
        if dfe[i] + nch != r['u10_pop_N']:
            viol += 1; det.append((i + 1, int(dfe[i]), nch))
    r['u10_ledger_viol'] = viol
    r['u10_ledger_det'] = str(det[:3])
    # última geração + resto até o maxfe
    r['u10_resto_final'] = int(man['maxfe'] - fes[-1])
    r['u10_sids_pop_validos'] = bool(set(pop['solution_id']).issubset(sids))

    # ---- P1 seeding D88 (query-joia do piso)
    if seed_rec:
        sr = seed_rec[0]
        r['p1_n_doe'] = sr['n_doe']; r['p1_n_frentes'] = sr['n_frentes']
        r['p1_n_frente1'] = sr['n_frente1']; r['p1_excede'] = sr['frente1_excede_pop']
        r['p1_n_doe_ok'] = (sr['n_doe'] == 11 * D - 1)
    Fdoe = real.loc[real['fase'] == 'init', fcols].values.astype(np.float64)
    N = r['u10_pop_N']
    sel, front, cd = selecao_d88(Fdoe, N)
    sid_init = real.loc[real['fase'] == 'init', 'solution_id'].values
    sel_sids = set(sid_init[sel].tolist())
    pop_g1 = set(pop.loc[pop['geracao'] == pop['geracao'].min(), 'solution_id'].tolist())
    r['p1_sel_bitexata'] = (sel_sids == pop_g1)
    r['p1_sel_inter'] = len(sel_sids & pop_g1)
    r['p1_nfrentes_recomp'] = int(front.max())
    r['p1_nfrente1_recomp'] = int((front == 1).sum())
    r['p1_nfrentes_ok'] = (seed_rec and front.max() == seed_rec[0]['n_frentes'])
    r['p1_nfrente1_ok'] = (seed_rec and (front == 1).sum() == seed_rec[0]['n_frente1'])
    r['p1_pop_g1_todos_init'] = bool(pop_g1.issubset(set(sid_init.tolist())))

    # ---- P2 N efetivo
    r['p2_N_nominal'] = man['params']['N_nominal']
    r['p2_N_efetivo'] = man['params']['N_efetivo']
    r['p2_N_eq'] = (man['params']['N_nominal'] == man['params']['N_efetivo'] == 20)
    r['p2_npop_gens'] = '|'.join(str(v) for v in sorted(set(g['n_pop'] for g in gens)))
    r['p2_npop_const20'] = all(g['n_pop'] == 20 for g in gens)
    r['p2_footer_Nef'] = footers[0].get('N_efetivo') if footers else None

    # ---- P3 gerações derivadas
    orc_infill = man['maxfe'] - (11 * D - 1)
    r['p3_orc_infill'] = orc_infill
    r['p3_ger_prevista'] = int(np.ceil(orc_infill / 20))
    r['p3_ger_obs'] = len(gens)
    r['p3_ger_teorica_20D'] = 20 * D / 20

    # ---- P4 elitismo (P ∪ Q → N): ②(g+1) ⊆ ②(g) ∪ novos avaliados
    viol_el = 0; turn = []
    gpop = {g: set(v['solution_id'].tolist()) for g, v in pop.groupby('geracao')}
    gkeys = sorted(gpop)
    for i in range(len(gkeys) - 1):
        g, gn = gkeys[i], gkeys[i + 1]
        lo, hi = fes[i], fes[i + 1]
        novos = set(real.loc[(real['fe_index'] >= lo) & (real['fe_index'] < hi), 'solution_id'].tolist())
        if not gpop[gn].issubset(gpop[g] | novos):
            viol_el += 1
        turn.append(len(gpop[gn] - gpop[g]))
    r['p4_elit_viol'] = viol_el
    r['p4_elit_pares'] = len(gkeys) - 1
    r['p4_turnover_med'] = float(np.mean(turn)) if turn else np.nan
    r['p4_turnover_max'] = int(np.max(turn)) if turn else -1
    r['p4_turnover_min'] = int(np.min(turn)) if turn else -1
    r['p4_turnover_zero'] = int(sum(1 for t in turn if t == 0))
    # sobrevivência do DoE até o fim
    r['p4_sobrev_doe_final'] = len(gpop[gkeys[-1]] & set(sid_init.tolist()))

    # ---- P5 monotonia do ideal / f_best (elitismo ⇒ não-piora por objetivo)
    ideal = np.array([g['ideal'] for g in gens], dtype=float)
    fbest = np.array([g['f_best'] for g in gens], dtype=float)
    dif = np.diff(ideal, axis=0)
    r['p5_ideal_viol'] = int((dif > 1e-12).sum())
    r['p5_ideal_viol_max'] = float(dif.max()) if dif.size else 0.0
    r['p5_fbest_eq_ideal'] = bool(np.allclose(ideal, fbest))
    r['p5_ideal_ganho'] = '|'.join('%.4g' % v for v in (ideal[0] - ideal[-1]))
    # nadir da frente 1 (não é monotônico por desenho — medir)
    nad1 = np.array([g['nadir_front1'] for g in gens], dtype=float)
    nadp = np.array([g['nadir_pop'] for g in gens], dtype=float)
    r['p5_nadir1_subidas'] = int((np.diff(nad1, axis=0) > 1e-12).sum())
    r['p5_nadirpop_subidas'] = int((np.diff(nadp, axis=0) > 1e-12).sum())
    r['p5_nadir1_le_pop'] = bool((nad1 <= nadp + 1e-9).all())

    # ---- P6 n_front1 (convergência da população à frente 1)
    nf1 = np.array([g['n_front1'] for g in gens])
    r['p6_nf1_ini'] = int(nf1[0]); r['p6_nf1_fim'] = int(nf1[-1])
    r['p6_nf1_med'] = float(nf1.mean()); r['p6_nf1_max'] = int(nf1.max())
    r['p6_nf1_satura'] = int((nf1 == r['u10_pop_N']).sum())
    r['p6_nf1_le_N'] = bool((nf1 <= r['u10_pop_N']).all())
    r['p6_nf1_ger_sat1'] = int(np.argmax(nf1 == r['u10_pop_N']) + 1) if (nf1 == r['u10_pop_N']).any() else -1

    # ---- P7 duplicatas / clone-hazard
    r['p7_ch_taxa'] = ch / max(1, (len(gens) - 1) * r['u10_pop_N'])
    r['p7_offspring_slots'] = (len(gens) - 1) * r['u10_pop_N']

    # ---- P8 ②(g) ≡ população reportada no ⑥ ; f do ② reconstruível da ①
    r['p8_pop_npop_ok'] = all(len(gpop[g]) == gg['n_pop'] for g, gg in zip(gkeys, gens))
    # recomputa n_front1 a partir do ② + ①
    fmap = real.set_index('solution_id')[fcols]
    nf1_rec = []
    for g, gg in zip(gkeys, gens):
        Fg = fmap.loc[sorted(gpop[g])].values.astype(np.float64)
        fr = nd_sort(Fg)
        nf1_rec.append(int((fr == 1).sum()))
    r['p8_nf1_recomp_ok'] = int(sum(1 for a, b in zip(nf1_rec, nf1) if a == b))
    r['p8_nf1_recomp_n'] = len(nf1_rec)
    # ideal recomputado
    ideal_rec = np.array([fmap.loc[sorted(gpop[g])].values.astype(np.float64).min(axis=0) for g in gkeys])
    r['p8_ideal_dmax'] = float(np.abs(ideal_rec - ideal).max())
    nad1_rec = []
    for g in gkeys:
        Fg = fmap.loc[sorted(gpop[g])].values.astype(np.float64)
        fr = nd_sort(Fg)
        nad1_rec.append(Fg[fr == 1].max(axis=0))
    r['p8_nadir1_dmax'] = float(np.abs(np.array(nad1_rec) - nad1).max())
    r['p8_nadirpop_dmax'] = float(np.abs(np.array([fmap.loc[sorted(gpop[g])].values.astype(np.float64).max(axis=0) for g in gkeys]) - nadp).max())

    # ---- N1 declarações do bundle no header/params
    p = man['params']
    r['n1_patches'] = p['patches']
    r['n1_surrogate'] = p['surrogate']
    r['n1_operadores'] = p['operadores']
    r['n1_parameter'] = p['parameter']
    r['n1_principio'] = p['principio']
    r['n1_algo_version'] = man['algo_version']
    r['n1_piso_flag'] = header.get('piso'); r['n1_surr_flag'] = header.get('surrogate')
    r['n1_env_matlab'] = man['env']['matlab']
    r['n1_repo_hash'] = man['repo_hash']

    # ---- limites/bounds
    r['n2_x_min'] = float(real[xcols].values.min()); r['n2_x_max'] = float(real[xcols].values.max())
    r['n2_f_nan'] = int(real[fcols].isna().sum().sum())
    r['n2_x_nan'] = int(real[xcols].isna().sum().sum())

    linhas.append(r)
    evid[prob] = dict(fes=fes, ideal=ideal, nf1=nf1, nad1=nad1, nadp=nadp,
                      turn=turn, ch_fes=ch_fes, front_doe=front, cd_doe=cd,
                      sel_sids=sorted(sel_sids), pop_g1=sorted(pop_g1), nf1_rec=nf1_rec)

df = pd.DataFrame(linhas)
df.to_csv(f'{OUT}/aspectos_nsga2.csv', index=False)
pickle.dump(evid, open(f'{OUT}/evidencia_nsga2.pkl', 'wb'))
pd.set_option('display.width', 250, 'display.max_columns', 400)
print(df.to_string())
