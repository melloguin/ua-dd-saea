#!/usr/bin/env python
"""Bateria T11 do config `moead` (piso online MOEA/D, PlatEMO 4.15).

READ-ONLY. Corpus principal = s42 organizada (25 celulas main).
Reproduz e RE-MEDE o nucleo da F5 + testa as correcoes da campanha T11.
Saida: t11_moead_celulas.csv (1 linha por celula) + resumo no stdout.
"""
import json, glob, os, math, sys
import numpy as np
import pandas as pd

RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/moead'


def carrega(prob):
    base = f'{RAIZ}/{prob}/42/exp_main_moead_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    return man, recs, real, pop, sur, tim


def vizinhanca(W, T):
    """Replica sort(pdist2(W,W),2) do MATLAB com argsort estavel."""
    d = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    return np.argsort(d, axis=1, kind='stable')[:, :T]


linhas = []
probs = sorted(os.listdir(RAIZ))
for prob in probs:
    man, recs, real, pop, sur, tim = carrega(prob)
    r = {'problema': prob}
    ger = [x for x in recs if x.get('rec') == 'moead_gen']
    guards = [x for x in recs if x.get('rec') == 'guard']
    foot = [x for x in recs if x.get('rec') == 'footer'][0]
    head = [x for x in recs if x.get('rec') == 'header'][0]
    dec = [x for x in recs if x.get('rec') == 'decomposicao'][0]
    seed = [x for x in recs if x.get('rec') == 'seeding'][0]

    D = int(head['D']); M = int(head['M'])
    r['D'] = D; r['M'] = M
    Nn = int(man['params']['N_nominal']); Nef = int(man['params']['N_efetivo'])
    r['N_nom'] = Nn; r['N_ef'] = Nef
    r['N_lattice'] = int(dec['N_lattice'])
    r['n_ger'] = len(ger); r['n_ger_man'] = man['n_geracoes']

    # ---- U1 orcamento
    r['maxfe'] = man['maxfe']; r['maxfe_ok'] = (man['maxfe'] == 31 * D - 1)
    r['n_real'] = len(real); r['U1_len_real'] = (len(real) == 31 * D - 1)
    r['U1_fe_index'] = bool((real['fe_index'].values == np.arange(len(real))).all())
    r['U1_fe_final'] = (man['fe_final'] == man['maxfe'])
    r['termino'] = foot.get('termino'); r['status'] = man['status']
    r['n_retries'] = man['n_retries']; r['fallback'] = man['fallback_ativado']
    r['cp_init'] = foot.get('cp_init')

    # ---- U2 DoE
    init = real[real['fase'] == 'init']
    r['n_init'] = len(init); r['U2_init'] = (len(init) == 11 * D - 1)
    dpath = f'{DOE}/{prob}/doe_{prob}_42.parquet'
    r['U2_dX'] = np.nan
    if os.path.exists(dpath):
        d = pd.read_parquet(dpath)
        xc = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
        xd = [c for c in d.columns if c.startswith('x') and c[1:].isdigit()]
        if len(xd) == len(xc) and len(d) == len(init):
            r['U2_dX'] = float(np.max(np.abs(
                init[xc].values.astype(np.float64) -
                d[xd].values.astype(np.float32).astype(np.float64))))
    sc = dpath.replace('.parquet', '.sha256')
    r['U2_doe_hash_side'] = None
    for cand in (sc, dpath + '.sha256', f'{DOE}/{prob}/doe_{prob}_42.meta.json'):
        if os.path.exists(cand):
            t = open(cand).read().strip()
            r['U2_doe_hash_side'] = (man['doe_hash'] in t)
            break

    # ---- U3 sem surrogate
    r['U3_sur_linhas'] = len(sur); r['U3_sur_cols'] = sur.shape[1]
    r['U3_fit_series'] = (man['fit_series'] == [])
    r['U3_tfit_nan'] = bool(tim['tempo_fit_s'].isna().all()) if 'tempo_fit_s' in tim else None
    r['U3_tbusca_nan'] = bool(tim['tempo_busca_s'].isna().all()) if 'tempo_busca_s' in tim else None
    r['U3_sem_sigma_dict_s42'] = ('sigma_dict' not in man)

    # ---- U4 sonda
    r['U4_sonda'] = man['sonda']['status']; r['U4_blocos'] = man['sonda']['n_blocos']

    # ---- U5 timing
    r['U5_len_tim'] = len(tim); r['U5_tim_ok'] = (len(tim) == len(ger))
    tg_t = tim['tempo_geracao_s'].values.astype(float)
    tg_j = np.array([g['tempo_geracao_s'] for g in ger], dtype=float)
    r['U5_dt_max'] = float(np.max(np.abs(tg_t - tg_j))) if len(tg_t) == len(tg_j) else np.nan
    r['U5_sum_tger'] = float(np.nansum(tg_t)); r['tempo_total'] = man['timing']['tempo_total_s']
    r['U5_frac'] = r['U5_sum_tger'] / r['tempo_total']
    r['t_aval_real'] = man['timing'].get('tempo_aval_real_s')

    # ---- U6 guards
    ch = [g for g in guards if g['name'] == 'cache_hit']
    hs = [g for g in guards if g['name'] == 'hard_stop']
    r['n_cache'] = len(ch); r['n_hardstop'] = len(hs)
    r['U6_ch_man'] = (len(ch) == man['cache_hits'] == foot['cache_hits'])
    r['guard_vocab'] = ','.join(sorted({g['name'] for g in guards}))

    # ---- M14 c0 = N+1
    fe1 = ger[0]['fe'] if ger else None
    pre = [g for g in ch if g['fe'] <= (11 * D - 1)]
    r['c0'] = len(pre); r['M14_c0_eq_N1'] = (len(pre) == Nef + 1)
    sids_pre = [g['solution_id'] for g in pre]
    r['M14_dup_primeiro'] = (len(sids_pre) > 1 and sids_pre[0] == sids_pre[1])
    r['M14_unicos'] = len(set(sids_pre))

    # ---- U7 ledger: qual denominador fecha?
    clones = len(ch) - r['c0']
    r['clones'] = clones
    r['tentativas'] = 20 * D + clones + 1          # 20D novos + clones + o abortado
    for nome, den in (('Nef', Nef), ('par', 2 * (Nef // 2))):
        k = r['tentativas'] - (len(ger) - 1) * den
        r[f'k_{nome}'] = k
        r[f'ledger_{nome}_ok'] = bool(1 <= k <= den)
    # ---- M11/A6: a formula NOVA do params.geracoes_derivadas (T11)
    den_par = 2 * (Nef // 2)
    r['T11_formula_par'] = math.floor((20 * D + clones) / den_par)
    r['T11_formula_par_ok'] = (r['T11_formula_par'] == len(ger))
    r['T11_formula_Nef'] = math.floor((20 * D + clones) / Nef)
    r['T11_formula_Nef_ok'] = (r['T11_formula_Nef'] == len(ger))
    r['T11_formula_Nef_p1'] = math.floor((20 * D + clones) / Nef) + 1
    r['T11_formula_Nef_p1_ok'] = (r['T11_formula_Nef_p1'] == len(ger))
    r['antiga_20D_N'] = 20 * D // Nef
    r['antiga_ok'] = (r['antiga_20D_N'] == len(ger))

    # ---- ② estrutura
    r['len_pop'] = len(pop); r['M13_len_ok'] = (len(pop) == len(ger) * Nef)
    g1 = pop[pop['geracao'] == 1]
    r['M13_g1_doe'] = bool((g1['solution_id'].values < 11 * D - 1).all())
    r['M13_g1_unicos'] = int(g1['solution_id'].nunique())

    # ---- M5 vizinhanca T
    W = np.array(dec['vetores'], dtype=float)
    r['M3_nvec'] = W.shape[0]; r['M3_soma1'] = float(np.max(np.abs(W.sum(1) - 1)))
    T = math.ceil(W.shape[0] / 10)
    r['M5_T'] = T
    B = vizinhanca(W, T)

    # ---- M6/M7 pares identicos por geracao (fracao media)
    sid_by_gen = {int(g): grp['solution_id'].values
                  for g, grp in pop.groupby('geracao')}
    fr = []
    for g, sids in sid_by_gen.items():
        if len(sids) != W.shape[0]:
            continue
        nn = B[:, 1] if B.shape[1] > 1 else B[:, 0]
        fr.append(float(np.mean(sids == sids[nn])))
    r['M7_frac_pares_med'] = float(np.median(fr)) if fr else np.nan
    r['M6_taxa_clone'] = clones / (r['tentativas'] - 1) if r['tentativas'] > 1 else np.nan
    f = r['M7_frac_pares_med']
    r['M6_prev'] = ((f + (1 - f) * 2.0 ** (-D)) * (1 - 1.0 / D) ** D) if not np.isnan(f) else np.nan
    # IC95 binomial (Wilson) da taxa medida
    n = r['tentativas'] - 1; p = r['M6_taxa_clone']; z = 1.96
    den_w = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den_w
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den_w
    r['M6_ic_lo'], r['M6_ic_hi'] = cen - hw, cen + hw
    r['M6_ic_contem'] = bool(r['M6_ic_lo'] <= r['M6_prev'] <= r['M6_ic_hi'])

    # ---- ultima pop: diversidade
    gmax = int(pop['geracao'].max())
    r['M7_unicos_final'] = int(pop[pop['geracao'] == gmax]['solution_id'].nunique())

    # ---- M15 ideal/nadir/f_best  (contra ② + ①)
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    objs = real.set_index('solution_id')[fcols]
    ok_id = ok_nd = ok_fb = 0
    quebras = 0
    prev = None
    for g in ger:
        gg = int(g['geracao'])
        sids = sid_by_gen.get(gg)
        if sids is None:
            continue
        O = objs.loc[sids].values.astype(np.float64)
        ok_id += int(np.allclose(np.array(g['ideal'], float), O.min(0), rtol=0, atol=1e-6))
        ok_nd += int(np.allclose(np.array(g['nadir_pop'], float), O.max(0), rtol=0, atol=1e-6))
        ok_fb += int(np.array_equal(np.array(g['f_best'], float), np.array(g['ideal'], float)))
        cur = np.array(g['ideal'], float)
        if prev is not None and np.any(cur > prev + 1e-12):
            quebras += 1
        prev = cur
    r['M15_ideal_ok'] = ok_id; r['M15_nadir_ok'] = ok_nd; r['M15_fbest_eq'] = ok_fb
    r['M15_quebras_monot'] = quebras
    r['n_ger_check'] = len(ger)
    linhas.append(r)

df = pd.DataFrame(linhas)
df.to_csv(f'{OUT}/t11_moead_celulas.csv', index=False)
pd.set_option('display.width', 250)
print(df[['problema', 'D', 'M', 'N_ef', 'n_ger', 'clones', 'k_Nef', 'ledger_Nef_ok',
          'k_par', 'ledger_par_ok', 'T11_formula_par_ok', 'T11_formula_Nef_p1_ok',
          'M5_T', 'M6_taxa_clone', 'M6_ic_contem']].to_string(index=False))
print()
tot = len(df)
def s(c):
    return f'{int(df[c].sum())}/{tot}'
print('U1 len(1)=31D-1:', s('U1_len_real'), '| fe_index denso:', s('U1_fe_index'),
      '| fe_final==maxfe:', s('U1_fe_final'), '| termino normal:',
      f"{(df.termino=='normal').sum()}/{tot}")
print('U2 init=11D-1:', s('U2_init'), '| max|dX| global:', df['U2_dX'].max())
print('U3 sur linhas:', df.U3_sur_linhas.sum(), '| fit_series []:', s('U3_fit_series'),
      '| tfit NaN:', s('U3_tfit_nan'), '| tbusca NaN:', s('U3_tbusca_nan'),
      '| sem sigma_dict (s42):', s('U3_sem_sigma_dict_s42'))
print('U4 sonda:', df.U4_sonda.unique(), '| blocos', df.U4_blocos.unique())
print('U5 |dt|max:', df.U5_dt_max.max(), '| frac tger/total mediana:', df.U5_frac.median(),
      '| t_aval_real nao-nulo:', int(df.t_aval_real.notna().sum()), '/', tot)
print('U6 reconciliacao:', s('U6_ch_man'), '| hard_stop==1:',
      f"{(df.n_hardstop==1).sum()}/{tot}", '| vocab:', df.guard_vocab.unique())
print('M14 c0=N+1:', s('M14_c0_eq_N1'), '| primeiro duplicado:', s('M14_dup_primeiro'))
print('LEDGER Nef:', s('ledger_Nef_ok'), '| LEDGER par(2*floor(N/2)):', s('ledger_par_ok'))
print('T11 formula floor((20D+dup)/par):', s('T11_formula_par_ok'),
      '| floor(/Nef):', s('T11_formula_Nef_ok'),
      '| floor(/Nef)+1:', s('T11_formula_Nef_p1_ok'),
      '| antiga 20D/Nef:', s('antiga_ok'))
print('M13 len(2)=nger*Nef:', s('M13_len_ok'), '| g1 so DoE:', s('M13_g1_doe'))
print('M5 T=2:', f"{(df.M5_T==2).sum()}/{tot}")
print('M6 clones tot:', df.clones.sum(), '/ tentativas', df.tentativas.sum(),
      '=', df.clones.sum() / df.tentativas.sum(), '| IC contem previsao:', s('M6_ic_contem'))
print('M15 ideal ok:', df.M15_ideal_ok.sum(), '/', df.n_ger_check.sum(),
      '| nadir ok:', df.M15_nadir_ok.sum(), '| f_best==ideal:', df.M15_fbest_eq.sum(),
      '| quebras monotonia:', df.M15_quebras_monot.sum())
print('M7 unicos pop final mediana:', df.M7_unicos_final.median(),
      '| frac pares mediana:', df.M7_frac_pares_med.median())
print('TOTAIS: geracoes', df.n_ger.sum(), '| linhas 1', df.n_real.sum(),
      '| init', df.n_init.sum(), '| 2', df.len_pop.sum(), '| cache', df.n_cache.sum())
