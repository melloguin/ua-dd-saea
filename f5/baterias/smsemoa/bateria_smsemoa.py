#!/usr/bin/env python
"""Bateria de fidelidade — config smsemoa (SMS-EMOA piso online) — F5.3b.
Executa TODAS as queries em TODAS as 25 celulas main/semente 42. READ-ONLY nos dados.
Saidas: CSVs + pickle em f5/baterias/smsemoa/.
"""
import json, glob, os, pickle
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/smsemoa'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/smsemoa'
os.makedirs(OUT, exist_ok=True)


# ---------------- utilitarios de selecao (replica NSGA-II/PlatEMO) ----------------
def nd_sort(F):
    """Fast non-dominated sorting -> vetor de frentes (1-based)."""
    n = F.shape[0]
    front = np.zeros(n, dtype=int)
    dom_count = np.zeros(n, dtype=int)
    dominated = [[] for _ in range(n)]
    for i in range(n):
        di = F[i]
        le = np.all(F >= di, axis=1)
        lt = np.any(F > di, axis=1)
        dom_i = le & lt          # i domina esses
        dom_i[i] = False
        ge = np.all(F <= di, axis=1)
        gt = np.any(F < di, axis=1)
        dominates_i = ge & gt    # esses dominam i
        dominates_i[i] = False
        dominated[i] = np.where(dom_i)[0]
        dom_count[i] = dominates_i.sum()
    cur = np.where(dom_count == 0)[0]
    f = 1
    while len(cur):
        front[cur] = f
        nxt = []
        for i in cur:
            for j in dominated[i]:
                dom_count[j] -= 1
                if dom_count[j] == 0:
                    nxt.append(j)
        cur = np.array(sorted(set(nxt)), dtype=int)
        f += 1
    return front


def crowding(F):
    n, m = F.shape
    cd = np.zeros(n)
    if n <= 2:
        return np.full(n, np.inf)
    for j in range(m):
        o = np.argsort(F[:, j], kind='stable')
        fj = F[o, j]
        cd[o[0]] = np.inf
        cd[o[-1]] = np.inf
        rng = fj[-1] - fj[0]
        if rng == 0:
            continue
        cd[o[1:-1]] += (fj[2:] - fj[:-2]) / rng
    return cd


def seed_pick(F, N):
    """Melhores N por NDSort + CrowdingDistance, desempate final por indice (D88)."""
    fr = nd_sort(F)
    chosen = []
    f = 1
    while len(chosen) < N:
        idx = np.where(fr == f)[0]
        if len(chosen) + len(idx) <= N:
            chosen.extend(sorted(idx.tolist()))
        else:
            cd = crowding(F[idx])
            order = sorted(range(len(idx)), key=lambda k: (-cd[k], idx[k]))
            need = N - len(chosen)
            chosen.extend(sorted(idx[order[:need]].tolist()))
        f += 1
    return np.array(sorted(chosen))


def hv(F, ref):
    from pymoo.indicators.hv import HV
    return HV(ref_point=ref)(F)


# ---------------- carga por celula ----------------
def load_cell(prob):
    base = f'{ROOT}/{prob}/42/exp_main_smsemoa_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = []
    for line in open(base + '.jsonl'):
        line = line.strip()
        if line:
            recs.append(json.loads(line))
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    return man, recs, real, pop, sur, tim


def analyse(prob):
    man, recs, real, pop, sur, tim = load_cell(prob)
    r = {'problema': prob}
    hdr = [x for x in recs if x.get('rec') == 'header']
    ftr = [x for x in recs if x.get('rec') == 'footer']
    seedev = [x for x in recs if x.get('rec') == 'seeding']
    guards = [x for x in recs if x.get('rec') == 'guard']
    gens = [x for x in recs if x.get('rec') == 'smsemoa_gen']
    other = sorted(set(x.get('rec') for x in recs) - {'header', 'footer', 'seeding', 'guard', 'smsemoa_gen'})
    r['recs_outros'] = ';'.join(other)
    r['n_recs'] = len(recs)
    r['n_header'] = len(hdr)
    r['n_footer'] = len(ftr)
    h = hdr[0]
    D, M = h['D'], h['M']
    r['D'], r['M'] = D, M
    N = h['N_nominal']
    r['N_nominal'] = N
    r['N_efetivo_man'] = man['params']['N_efetivo']
    r['N_efetivo_footer'] = ftr[0].get('N_efetivo') if ftr else None
    maxfe, init = 31 * D - 1, 11 * D - 1
    r['maxfe_esp'] = maxfe
    r['init_esp'] = init

    # --- U1 orcamento ---
    r['n_real'] = len(real)
    r['U1_len_ok'] = len(real) == maxfe
    r['U1_maxfe_man'] = man['maxfe'] == maxfe
    r['U1_fefinal_ok'] = man['fe_final'] == maxfe
    r['U1_feindex_denso'] = bool((real.fe_index.values == np.arange(len(real))).all())
    r['U1_sid_denso'] = bool((real.solution_id.values == np.arange(len(real))).all())

    # --- U2 DoE ---
    fases = real.fase.value_counts().to_dict()
    r['fases'] = ';'.join(f'{k}={v}' for k, v in sorted(fases.items()))
    r['U2_init_ok'] = int(fases.get('init', 0)) == init
    r['U2_cp_init'] = ftr[0].get('cp_init') if ftr else None
    xcols = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    xcols = sorted(xcols, key=lambda c: int(c[1:]))
    r['n_xcols'] = len(xcols)
    doep = f'{DOE}/{prob}/doe_{prob}_42.npy'
    if os.path.exists(doep):
        Xd = np.load(doep)
        r['doe_shape'] = str(Xd.shape)
        Xi = real.loc[real.fase == 'init', xcols].values
        n = min(len(Xd), len(Xi))
        r['U2_dX_max'] = float(np.abs(Xd[:n].astype(np.float32) - Xi[:n]).max())
    else:
        r['doe_shape'] = 'AUSENTE'
        r['U2_dX_max'] = np.nan
    r['doe_hash_man'] = man['doe_hash'][:12]
    r['U2_hash_hdr_eq'] = man['doe_hash'] == h['doe_hash']

    # --- geracoes / FE por geracao ---
    gser = pd.DataFrame([{'g': g['geracao'], 'fe': g['fe'], 'n_pop': g['n_pop'],
                          'n_front1': g['n_front1'], 't': g['tempo_geracao_s'],
                          'f_best': g['f_best'], 'ideal': g['ideal'],
                          'nadir_pop': g['nadir_pop'], 'nadir_front1': g['nadir_front1']}
                         for g in gens])
    r['n_gens_log'] = len(gser)
    r['n_ger_man'] = man['n_geracoes']
    r['A5_gens_esp'] = D + 1                      # 20D/N + 1(seeding)
    r['A5_gens_ok'] = len(gser) == D + 1 == man['n_geracoes']
    r['A5_g_denso'] = bool((gser.g.values == np.arange(1, len(gser) + 1)).all())
    r['A5_fe_g1'] = int(gser.fe.iloc[0])
    r['A5_fe_g1_eq_init'] = int(gser.fe.iloc[0]) == init
    d = np.diff(gser.fe.values)
    r['A5_dfe_unicos'] = ';'.join(map(str, sorted(set(d.tolist()))))
    r['A5_dfe_todos_N'] = bool((d == N).all())
    r['A5_fe_last'] = int(gser.fe.iloc[-1])
    r['A5_npop_sempre_N'] = bool((gser.n_pop == N).all())

    # --- (2) camada pop ---
    r['n_pop_rows'] = len(pop)
    grp = pop.groupby('geracao').solution_id
    sizes = grp.size()
    r['A7_grupos'] = len(sizes)
    r['A7_todos_N'] = bool((sizes == N).all())
    r['A7_total_ok'] = len(pop) == N * len(gser)
    r['A7_dup_intra'] = int(sum(pop.groupby('geracao').solution_id.apply(lambda s: len(s) - s.nunique())))
    popmap = {int(g): np.array(v.tolist()) for g, v in pop.groupby('geracao')['solution_id']}

    # --- seeding D88 (recomputo) ---
    se = seedev[0] if seedev else {}
    r['S_n_doe'] = se.get('n_doe')
    r['S_n_frentes'] = se.get('n_frentes')
    r['S_n_frente1'] = se.get('n_frente1')
    r['S_f1_excede'] = se.get('frente1_excede_pop')
    r['S_criterio'] = se.get('criterio', '')[:40]
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    fcols = sorted(fcols, key=lambda c: int(c[1:]))
    Fall = real[fcols].values.astype(np.float64)
    Fdoe = Fall[:init]
    fr_doe = nd_sort(Fdoe)
    r['S_n_frentes_calc'] = int(fr_doe.max())
    r['S_n_frente1_calc'] = int((fr_doe == 1).sum())
    r['S_frentes_ok'] = (r['S_n_frentes_calc'] == se.get('n_frentes')) and (r['S_n_frente1_calc'] == se.get('n_frente1'))
    pick = seed_pick(Fdoe, N)
    obs1 = np.sort(popmap[1])
    r['S_pick_igual'] = bool(np.array_equal(pick, obs1))
    r['S_pick_inter'] = int(len(set(pick.tolist()) & set(obs1.tolist())))
    r['S_todos_do_doe'] = bool((obs1 < init).all())
    # frente-1 completa contida?
    f1 = set(np.where(fr_doe == 1)[0].tolist())
    r['S_f1_contida'] = bool(f1 <= set(obs1.tolist())) if len(f1) <= N else None

    # --- guards / cache_hit ---
    gnames = {}
    for g in guards:
        gnames[g.get('name')] = gnames.get(g.get('name'), 0) + 1
    r['G_guards'] = ';'.join(f'{k}={v}' for k, v in sorted(gnames.items()))
    r['G_n_guards'] = len(guards)
    r['G_cache_hits_man'] = man['cache_hits']
    r['G_cache_hits_ftr'] = ftr[0].get('cache_hits') if ftr else None
    r['G_recon'] = len(guards) == man['cache_hits'] == (ftr[0].get('cache_hits') if ftr else -1)
    gsid = [g.get('solution_id') for g in guards]
    r['G_uniq_sid'] = len(set(gsid))
    r['G_dups'] = len(gsid) - len(set(gsid))
    gfe = [g.get('fe') for g in guards]
    r['G_fe_no_init'] = int(sum(1 for x in gfe if x == init))
    r['G_fe_pos_init'] = int(sum(1 for x in gfe if x > init))
    r['G_sids_sao_pop1'] = bool(set(x for x in gsid) == set(obs1.tolist()))
    r['G_ordem_igual'] = bool(list(dict.fromkeys(gsid)) == popmap[1].tolist())

    # --- elitismo (mu+1): pop(g+1) subset pop(g) U novos ---
    viol_sub, entrantes, saidas = 0, [], []
    for i in range(1, len(gser)):
        g = int(gser.g.iloc[i])
        fe_prev = int(gser.fe.iloc[i - 1])
        fe_cur = int(gser.fe.iloc[i])
        novos = set(range(fe_prev, fe_cur))
        prev = set(popmap[g - 1].tolist())
        cur = set(popmap[g].tolist())
        if not cur <= (prev | novos):
            viol_sub += 1
        entrantes.append(len(cur - prev))
        saidas.append(len(prev - cur))
    r['E_viol_subset'] = viol_sub
    r['E_entrantes_med'] = float(np.mean(entrantes)) if entrantes else np.nan
    r['E_entrantes_max'] = int(np.max(entrantes)) if entrantes else 0
    r['E_entrantes_soma'] = int(np.sum(entrantes)) if entrantes else 0
    r['E_taxa_aceite'] = float(np.sum(entrantes) / (N * (len(gser) - 1))) if len(gser) > 1 else np.nan
    r['E_ent_le_N'] = bool(max(entrantes) <= N) if entrantes else True

    # --- n_front1 / ideal / nadir recomputados ---
    bad_f1 = bad_ideal = bad_np = bad_nf1 = 0
    fbest_eq_ideal = 0
    for i in range(len(gser)):
        g = int(gser.g.iloc[i])
        ids = popmap[g]
        Fp = Fall[ids]
        fr = nd_sort(Fp)
        if int((fr == 1).sum()) != int(gser.n_front1.iloc[i]):
            bad_f1 += 1
        ide = Fp.min(axis=0)
        nap = Fp.max(axis=0)
        naf1 = Fp[fr == 1].max(axis=0)
        if not np.allclose(ide, np.array(gser.ideal.iloc[i], dtype=float), rtol=1e-6, atol=1e-9):
            bad_ideal += 1
        if not np.allclose(nap, np.array(gser.nadir_pop.iloc[i], dtype=float), rtol=1e-6, atol=1e-9):
            bad_np += 1
        if not np.allclose(naf1, np.array(gser.nadir_front1.iloc[i], dtype=float), rtol=1e-6, atol=1e-9):
            bad_nf1 += 1
        if np.allclose(np.array(gser.f_best.iloc[i], dtype=float), np.array(gser.ideal.iloc[i], dtype=float)):
            fbest_eq_ideal += 1
    r['R_bad_front1'] = bad_f1
    r['R_bad_ideal'] = bad_ideal
    r['R_bad_nadirpop'] = bad_np
    r['R_bad_nadirf1'] = bad_nf1
    r['R_fbest_eq_ideal'] = fbest_eq_ideal
    r['R_ngen'] = len(gser)
    r['R_front1_lt_N'] = int((gser.n_front1 < N).sum())
    r['R_front1_frac_media'] = float((gser.n_front1 / N).mean())

    # --- HV da populacao (assinatura da selecao S-metric) ---
    ref = Fall.max(axis=0) * 1.0
    ref = ref + 0.01 * np.abs(ref) + 1e-9
    hvs = []
    for i in range(len(gser)):
        ids = popmap[int(gser.g.iloc[i])]
        hvs.append(hv(Fall[ids], ref))
    hvs = np.array(hvs)
    dh = np.diff(hvs)
    rel = dh / np.maximum(np.abs(hvs[:-1]), 1e-12)
    r['HV_n_trans'] = len(dh)
    r['HV_viol'] = int((rel < -1e-9).sum())
    r['HV_viol_1pct'] = int((rel < -0.01).sum())
    r['HV_pior_rel'] = float(rel.min()) if len(rel) else np.nan
    r['HV_ganho_total'] = float((hvs[-1] - hvs[0]) / max(abs(hvs[0]), 1e-12)) if hvs[0] != 0 else np.nan
    r['HV_g1'] = float(hvs[0])
    r['HV_gN'] = float(hvs[-1])

    # --- (3) surrogate vazia / sonda / sigma_dict ---
    r['SUR_linhas'] = len(sur)
    r['SUR_cols'] = len(sur.columns)
    r['SIG_sigma_dict'] = 'sigma_dict' in man
    r['SIG_fit_series'] = len(man.get('fit_series', []))
    r['SONDA_status'] = man.get('sonda', {}).get('status')
    r['SONDA_blocos'] = man.get('sonda', {}).get('n_blocos')
    r['SONDA_linhas'] = man.get('sonda', {}).get('n_linhas')
    r['HDR_surrogate_flag'] = h.get('surrogate')
    r['HDR_piso_flag'] = h.get('piso')

    # --- timing ---
    r['T_rows'] = len(tim)
    r['T_rows_ok'] = len(tim) == len(gser)
    r['T_fit_null'] = bool(tim.tempo_fit_s.isna().all())
    r['T_busca_null'] = bool(tim.tempo_busca_s.isna().all())
    r['T_sonda_null'] = bool(tim.tempo_pred_sonda_s.isna().all())
    r['T_nacum_null'] = bool(tim.n_acumulado.isna().all())
    r['T_soma_ger'] = float(tim.tempo_geracao_s.sum())
    r['T_total_man'] = man['timing']['tempo_total_s']
    r['T_soma_le_total'] = float(tim.tempo_geracao_s.sum()) <= man['timing']['tempo_total_s']
    r['T_aval_real'] = man['timing']['tempo_aval_real_s']
    r['T_fit_man'] = man['timing']['tempo_fit_surrogate_s']
    r['T_busca_man'] = man['timing']['tempo_busca_s']
    r['T_sonda_man'] = man['timing']['tempo_pred_sonda_s']
    r['T_ger_gt0'] = bool((tim.tempo_geracao_s > 0).all())
    # coerencia ⑥ x ④
    tj = gser.t.values.astype(float)
    r['T_jsonl_eq_parquet'] = bool(np.allclose(tj, tim.tempo_geracao_s.values.astype(float), rtol=1e-5, atol=1e-7))

    # --- manifesto/termino ---
    r['MAN_status'] = man['status']
    r['MAN_retries'] = man['n_retries']
    r['FTR_termino'] = ftr[0].get('termino') if ftr else None
    r['FTR_status'] = ftr[0].get('status') if ftr else None
    r['MAN_motivo_parada'] = man.get('motivo_parada', 'AUSENTE')
    r['MAN_fallback'] = man.get('fallback_ativado')
    r['MAN_algo_version'] = man.get('algo_version')
    r['MAN_repo_hash'] = man.get('repo_hash')
    r['HDR_operadores'] = h.get('operadores', '')
    r['HDR_principio'] = h.get('principio', '')
    r['PAR_patches'] = man['params'].get('patches')
    r['PAR_surrogate'] = man['params'].get('surrogate')
    r['PAR_parameter'] = man['params'].get('parameter')
    r['MAN_params_keys'] = len(man.get('params', {}))
    r['MAN_env'] = json.dumps(man.get('env', {}), ensure_ascii=False)

    # --- dedup / X duplicados na (1) ---
    Xall = real[xcols].values
    uq = np.unique(Xall, axis=0)
    r['DED_x_unicos'] = int(len(uq))
    r['DED_x_dups'] = int(len(Xall) - len(uq))

    aux = {'gser': gser, 'popmap': popmap, 'hvs': hvs, 'Fall': Fall, 'front1': gser.n_front1.values,
           'entrantes': entrantes, 'guards': guards, 'seed': se}
    return r, aux


if __name__ == '__main__':
    probs = sorted(os.path.basename(p) for p in glob.glob(ROOT + '/*') if os.path.isdir(p))
    rows, auxall = [], {}
    for p in probs:
        try:
            rr, aa = analyse(p)
            rows.append(rr)
            auxall[p] = aa
            print('ok', p, flush=True)
        except Exception as e:
            print('ERRO', p, repr(e), flush=True)
            raise
    df = pd.DataFrame(rows)
    df.to_csv(OUT + '/aspectos_smsemoa.csv', index=False)
    with open(OUT + '/evidencia_smsemoa.pkl', 'wb') as f:
        pickle.dump({'aux': auxall}, f)
    print(df.shape)
