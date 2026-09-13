#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead.py — F5.3b · analista de fidelidade do config `moead` (MOEA/D piso online).
Executa TODAS as checagens em TODAS as 25 células main da semente 42. READ-ONLY sobre dados.
Saída: CSVs/pickles de evidência em f5/baterias/moead/.
"""
import json, os, sys, hashlib, collections
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
DOE = os.path.join(REPO, 'data', 'doe')
os.makedirs(OUT, exist_ok=True)

PROBS = sorted(os.listdir(RAIZ))
PROBS = [p for p in PROBS if not p.startswith('.')]


def carrega(prob):
    d = os.path.join(RAIZ, prob, '42')
    base = os.path.join(d, 'exp_main_moead_%s_42' % prob)
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    return man, evs, real, pop, sur, tim


def por_rec(evs, rec):
    return [e for e in evs if e.get('rec') == rec]


linhas = []
gen_rows = []
guard_rows = []
pop_rows = []

for prob in PROBS:
    man, evs, real, pop, sur, tim = carrega(prob)
    hdr = por_rec(evs, 'header')[0]
    dec = por_rec(evs, 'decomposicao')[0]
    seed_ev = por_rec(evs, 'seeding')[0]
    foot = por_rec(evs, 'footer')
    foot = foot[0] if foot else {}
    gens = por_rec(evs, 'moead_gen')
    guards = por_rec(evs, 'guard')

    D, M = hdr['D'], hdr['M']
    maxfe = man['maxfe']
    n_doe = 11 * D - 1
    N_nom = man['params']['N_nominal']
    N_ef = man['params']['N_efetivo']
    N_lat = dec['N_lattice']
    n_ger = man['n_geracoes']

    # ---------- U1 orçamento / término ----------
    u1_len = len(real) == 31 * D - 1
    fe_idx = real['fe_index'].to_numpy()
    u1_denso = bool((fe_idx == np.arange(len(real))).all())
    u1_fefinal = man['fe_final'] == maxfe == 31 * D - 1
    termino = foot.get('termino')
    status = man['status']

    # ---------- U2 DoE ----------
    n_init = int((real['fase'] == 'init').sum())
    doe_pq = os.path.join(DOE, prob, 'doe_%s_42.parquet' % prob)
    doe_mf = os.path.join(DOE, prob, 'doe_%s_42.manifest.json' % prob)
    dsc = json.load(open(doe_mf)) if os.path.exists(doe_mf) else {}
    hash_ok = (dsc.get('hash') or dsc.get('doe_hash') or dsc.get('sha256')) == man['doe_hash']
    xcols = ['x%d' % i for i in range(D)]
    if os.path.exists(doe_pq):
        Xd = pd.read_parquet(doe_pq)
        xdc = [c for c in Xd.columns if c.startswith('x')]
        Xa = Xd[xdc].to_numpy(dtype=np.float64)
        Xr = real.loc[real['fase'] == 'init', xcols].to_numpy(dtype=np.float64)
        dX = float(np.abs(Xa[:len(Xr)].astype(np.float32).astype(np.float64) - Xr).max()) if len(Xr) else np.nan
    else:
        dX = np.nan
    # duplicatas de X no DoE e na ① inteira
    def nkey(A):
        return [a.tobytes() for a in np.ascontiguousarray(A.astype(np.float32))]
    keys_all = nkey(real[xcols].to_numpy())
    dupX_total = len(keys_all) - len(set(keys_all))
    keys_init = keys_all[:n_init]
    dupX_doe = len(keys_init) - len(set(keys_init))

    # ---------- U3/U4/U6/U8/U11: sem surrogate ----------
    sur_vazia = len(sur) == 0
    fit_series_vazia = (man.get('fit_series') == [])
    sonda = man.get('sonda', {})
    tim_fit_null = bool(tim['tempo_fit_s'].isna().all())
    tim_busca_null = bool(tim['tempo_busca_s'].isna().all())
    tim_sonda_null = bool(tim['tempo_pred_sonda_s'].isna().all())
    tnull = man['timing']
    # n_acumulado no ④
    nacc = tim['n_acumulado'].to_numpy()

    # ---------- U7 timing ----------
    tim_rows_ok = len(tim) == n_ger
    tg_ev = np.array([g['tempo_geracao_s'] for g in gens], dtype=float)
    tg_pq = tim['tempo_geracao_s'].to_numpy(dtype=float)
    dt_max = float(np.abs(tg_ev - tg_pq).max()) if len(tg_ev) == len(tg_pq) else np.nan
    soma_ger = float(tg_pq.sum())
    ttotal = man['timing']['tempo_total_s']
    t_aval = man['timing']['tempo_aval_real_s']

    # ---------- U9 guards ----------
    gcount = collections.Counter(g['name'] for g in guards)
    ch_jsonl = gcount.get('cache_hit', 0)
    hs_jsonl = gcount.get('hard_stop', 0)
    ch_man = man['cache_hits']
    ch_foot = foot.get('cache_hits')

    # cache-hits do seeding (fe == n_doe, antes/na primeira geração)
    ch_fe = np.array([g['fe'] for g in guards if g['name'] == 'cache_hit'], dtype=int)
    ch_sid = np.array([g['solution_id'] for g in guards if g['name'] == 'cache_hit'], dtype=int)
    ch_seed = int((ch_fe == n_doe).sum())          # inclui seeding + offspring da ger.1
    # os PRIMEIROS N_ef cache-hits são o seeding (ordem de log)
    seed_hits = ch_sid[:N_ef]
    seed_hits_sao_doe = bool((seed_hits < n_doe).all()) if len(seed_hits) else False
    # cache-hits de offspring
    ch_off = ch_jsonl - N_ef
    # alvos: quantos apontam para pontos do DoE vs de infill
    alvo_doe = int((ch_sid[N_ef:] < n_doe).sum())
    alvo_infill = int((ch_sid[N_ef:] >= n_doe).sum())
    # re-hits: mesmo solution_id atingido mais de uma vez
    cnt_sid = collections.Counter(ch_sid[N_ef:].tolist())
    sid_repetidos = sum(1 for v in cnt_sid.values() if v > 1)
    max_hits_mesmo_sid = max(cnt_sid.values()) if cnt_sid else 0

    # ---------- U10 aritmética entre camadas ----------
    tentativas = n_ger * N_ef
    novos = (31 * D - 1) - n_doe          # == 20D
    ledger = tentativas - ch_off - hs_jsonl - novos    # deve fechar em 0
    pop_rows_ok = len(pop) == n_ger * N_ef

    # ---------- ② diversidade da população ----------
    g_un = pop.groupby('geracao')['solution_id'].nunique()
    g_n = pop.groupby('geracao')['solution_id'].size()
    uniq_frac = (g_un / g_n)
    uniq_g1 = float(uniq_frac.iloc[0]); uniq_gf = float(uniq_frac.iloc[-1])
    uniq_med = float(uniq_frac.median()); uniq_min = float(uniq_frac.min())
    # multiplicidade máxima (quantas cópias do indivíduo mais repetido)
    maxmult = int(pop.groupby(['geracao', 'solution_id']).size().max())
    # fração de indivíduos da pop final que ainda são do DoE
    ultg = pop['geracao'].max()
    pf = pop[pop['geracao'] == ultg]['solution_id']
    frac_doe_final = float((pf < n_doe).mean())

    # ---------- ideal point ----------
    ideal = np.array([g['ideal'] for g in gens], dtype=float)
    viol_ideal = int((np.diff(ideal, axis=0) > 1e-12).sum())
    npop_ok = all(g['n_pop'] == N_ef for g in gens)
    nf1 = np.array([g['n_front1'] for g in gens], dtype=int)
    fe_ev = np.array([g['fe'] for g in gens], dtype=int)
    d_fe = np.diff(fe_ev)
    # incrementos de FE por geração
    dfe_min = int(d_fe.min()) if len(d_fe) else -1
    dfe_max = int(d_fe.max()) if len(d_fe) else -1
    dfe_med = float(np.median(d_fe)) if len(d_fe) else np.nan
    fe_g1 = int(fe_ev[0])

    # ---------- seeding ----------
    seed_n_doe = seed_ev['n_doe']
    seed_f1 = seed_ev['n_frente1']
    seed_exc = seed_ev['frente1_excede_pop']
    seed_nfr = seed_ev['n_frentes']

    # ---------- lattice ----------
    vet = np.array(dec['vetores'], dtype=float)
    lat_soma = float(np.abs(vet.sum(axis=1) - 1.0).max())
    lat_n = len(vet)

    linhas.append(dict(
        problema=prob, D=D, M=M, maxfe=maxfe, n_doe=n_doe, n_ger=n_ger,
        N_nom=N_nom, N_ef=N_ef, N_lat=N_lat, lat_n=lat_n, lat_soma_err=lat_soma,
        u1_len=u1_len, u1_denso=u1_denso, u1_fefinal=u1_fefinal, termino=termino,
        status=status, n_init=n_init, n_init_ok=(n_init == n_doe),
        doe_hash_ok=hash_ok, dX_max=dX, dupX_total=dupX_total, dupX_doe=dupX_doe,
        sur_vazia=sur_vazia, sur_cols=len(sur.columns), fit_series_vazia=fit_series_vazia,
        sonda_status=sonda.get('status'), sonda_blocos=sonda.get('n_blocos'),
        tim_rows_ok=tim_rows_ok, tim_fit_null=tim_fit_null, tim_busca_null=tim_busca_null,
        tim_sonda_null=tim_sonda_null, dt_ev_pq=dt_max, soma_tger=soma_ger,
        t_total=ttotal, t_aval=t_aval, frac_tger=soma_ger / ttotal,
        nacc_unicos=int(pd.Series(nacc).nunique()), nacc_min=float(np.nanmin(nacc)),
        nacc_max=float(np.nanmax(nacc)),
        ch_jsonl=ch_jsonl, ch_man=ch_man, ch_foot=ch_foot, hs_jsonl=hs_jsonl,
        ch_seed_bloco=ch_seed, seed_hits_doe=seed_hits_sao_doe, ch_off=ch_off,
        alvo_doe=alvo_doe, alvo_infill=alvo_infill, sid_repetidos=sid_repetidos,
        max_hits_sid=max_hits_mesmo_sid,
        tentativas=tentativas, novos=novos, ledger=ledger, pop_rows_ok=pop_rows_ok,
        taxa_clone=ch_off / tentativas,
        uniq_g1=uniq_g1, uniq_med=uniq_med, uniq_min=uniq_min, uniq_gf=uniq_gf,
        maxmult=maxmult, frac_doe_final=frac_doe_final,
        viol_ideal=viol_ideal, npop_ok=npop_ok, nf1_g1=int(nf1[0]), nf1_fim=int(nf1[-1]),
        nf1_max=int(nf1.max()), fe_g1=fe_g1, dfe_min=dfe_min, dfe_max=dfe_max, dfe_med=dfe_med,
        seed_n_doe=seed_n_doe, seed_f1=seed_f1, seed_exc=seed_exc, seed_nfr=seed_nfr,
        cp_init=foot.get('cp_init'), algo_version=man['algo_version'],
        n_evs=len(evs), n_guards=len(guards),
    ))

    for g in gens:
        gen_rows.append(dict(problema=prob, **{k: v for k, v in g.items() if k not in ('rec', 'ts', 'f_best', 'ideal', 'nadir_pop', 'nadir_front1')}))
    for i, s in enumerate(ch_sid):
        guard_rows.append(dict(problema=prob, ordem=i, solution_id=int(s), fe=int(ch_fe[i]),
                               seeding=(i < N_ef)))
    for gg, sub in pop.groupby('geracao'):
        pop_rows.append(dict(problema=prob, geracao=int(gg), n=len(sub),
                             n_unicos=int(sub['solution_id'].nunique()),
                             n_doe=int((sub['solution_id'] < n_doe).sum())))

df = pd.DataFrame(linhas)
df.to_csv(os.path.join(OUT, 'moead_aspectos.csv'), index=False)
pd.DataFrame(gen_rows).to_csv(os.path.join(OUT, 'moead_geracoes.csv'), index=False)
pd.DataFrame(guard_rows).to_csv(os.path.join(OUT, 'moead_cachehits.csv'), index=False)
pd.DataFrame(pop_rows).to_csv(os.path.join(OUT, 'moead_pop_diversidade.csv'), index=False)

pd.set_option('display.width', 300); pd.set_option('display.max_columns', 200)
print(df.to_string())
print('\n=== RESUMO ===')
for c in ['u1_len', 'u1_denso', 'u1_fefinal', 'n_init_ok', 'doe_hash_ok', 'sur_vazia',
          'fit_series_vazia', 'tim_rows_ok', 'tim_fit_null', 'tim_busca_null',
          'tim_sonda_null', 'pop_rows_ok', 'npop_ok', 'seed_hits_doe', 'seed_exc']:
    print('%-18s' % c, df[c].sum(), '/', len(df))
print('ledger != 0 :', (df.ledger != 0).sum(), ' valores:', sorted(df.ledger.unique()))
print('dX_max global:', df.dX_max.max())
print('viol_ideal total:', df.viol_ideal.sum())
print('termino:', df.termino.value_counts().to_dict())
print('status:', df.status.value_counts().to_dict())
print('taxa_clone: min %.4f med %.4f max %.4f' % (df.taxa_clone.min(), df.taxa_clone.median(), df.taxa_clone.max()))
