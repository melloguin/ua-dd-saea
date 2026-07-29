"""B01 — censo estrutural das 54 células: constantes esperadas x observadas."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

rows = []
decs_all = []
for label, d, pref in celulas():
    man, evs, dfs = carrega(d, pref)
    mt = meta(label, man)
    real, sur, tim, fin, pop = dfs['real'], dfs['surrogate'], dfs['timing'], dfs['final'], dfs['pop']
    X = xcols(real); F = fcols(real)
    D = len(X); M = len(F); N = len(real)
    bu = busca(sur); so = sonda(sur)
    recs = {}
    for e in evs:
        recs[e.get('rec')] = recs.get(e.get('rec'), 0) + 1
    dec = [e for e in evs if e.get('rec') == 'decision']
    son = [e for e in evs if e.get('rec') == 'sonda']
    foot = [e for e in evs if e.get('rec') == 'footer']
    guards = [e for e in evs if e.get('rec') == 'guard']
    hdr = [e for e in evs if e.get('rec') == 'header']
    I_eff = len(dec)
    I_max = math.ceil(N / (10 * D))
    g = gera_int(bu)
    ngen_obs = int(g.max()) if len(g) else 0
    esperado_ngen = 51 * I_eff + 1000
    build = bu[bu['modelo_flag'] == 'treedGP_build']
    final_f = bu[bu['modelo_flag'] == 'treedGP_final']
    gb = gera_int(build); gf = gera_int(final_f)
    # footer do runner
    fr = None
    for f in foot:
        if 'n_final' in f:
            fr = f
    rows.append(dict(
        **mt, D=D, M=M, N=N,
        n_real=len(real), n_pop=(0 if pop is None else len(pop)),
        n_sur=len(sur), n_busca=len(bu), n_sonda=len(so), n_tim=len(tim),
        n_final=len(fin),
        status=man['status'], maxfe=man['maxfe'], fe_final=man['fe_final'],
        n_geracoes=man['n_geracoes'], cache_hits=man.get('cache_hits'),
        n_retries=man.get('n_retries'), fallback=man.get('fallback_ativado'),
        min_samples_leaf=man['sigma_dict'] and man['params']['min_samples_leaf'],
        max_depth=man['params']['max_depth'],
        kernel=man['params']['kernel'], selection=man['params']['selection_type'],
        alpha=man['params']['alpha'], G_max=man['params']['G_max_build'],
        n_gen_total_final=man['params']['n_gen_total_final'],
        sonda_S=man['sonda']['S'], sonda_nblocos=man['sonda']['n_blocos'],
        I_eff=I_eff, I_max=I_max,
        n_decision=len(dec), n_sonda_ev=len(son), n_footer=len(foot),
        n_guard=len(guards), n_header=len(hdr), n_ev=len(evs),
        rec_tipos=';'.join(sorted(recs)),
        ngen_obs=ngen_obs, ngen_esperado=esperado_ngen,
        ok_ngen=(ngen_obs == esperado_ngen == man['n_geracoes']),
        build_min=int(gb.min()) if len(gb) else -1, build_max=int(gb.max()) if len(gb) else -1,
        final_min=int(gf.min()) if len(gf) else -1, final_max=int(gf.max()) if len(gf) else -1,
        ok_fases=(len(gb) > 0 and len(gf) > 0 and int(gb.min()) == 1
                  and int(gb.max()) == 51 * I_eff and int(gf.min()) == 51 * I_eff + 1
                  and int(gf.max()) == 51 * I_eff + 1000),
        sem_furos=(set(range(1, ngen_obs + 1)) == set(g.unique().tolist())),
        tempo_aval_real_s=man['timing']['tempo_aval_real_s'],
        tempo_fit_s=man['timing']['tempo_fit_surrogate_s'],
        tempo_busca_s=man['timing']['tempo_busca_s'],
        tempo_pred_sonda_s=man['timing']['tempo_pred_sonda_s'],
        tempo_total_s=man['timing']['tempo_total_s'],
        n_fit_series=len(man['fit_series']),
        footer_runner=(fr is not None),
        footer_motivo=(fr or {}).get('motivo'),
        footer_nfinal=(fr or {}).get('n_final'),
        footer_ndpos=(fr or {}).get('n_nd_pos_real'),
        footer_cpinit=(fr or {}).get('cp_init'),
        upload_status=man.get('upload_status'),
        guard_nomes=';'.join(sorted({(g_.get('nome') or g_.get('guard') or g_.get('tipo') or 'NA') for g_ in guards})),
        guard_msgs=' | '.join([str(g_)[:220] for g_ in guards])[:600],
    ))
    for k, e in enumerate(dec):
        decs_all.append(dict(label=label, tier=mt['tier'], dist=mt['dist'], problema=mt['problema'],
                             D=D, M=M, N=N, I_eff=I_eff, I_max=I_max,
                             iteracao=e.get('iteracao'), geracao=e.get('geracao'),
                             caminho=e.get('caminho'), motivo=e.get('motivo'),
                             n_gps=json.dumps(e.get('n_gps')), n_folhas=json.dumps(e.get('n_folhas')),
                             profundidade=json.dumps(e.get('profundidade')),
                             tppm=json.dumps(e.get('total_points_per_model')),
                             delta_total_point=e.get('delta_total_point'),
                             early_stop=e.get('early_stop'), fe=e.get('fe'),
                             n_acumulado=e.get('n_acumulado'),
                             f_best=json.dumps(e.get('f_best')), n_front1=e.get('n_front1'),
                             tempo_fit_s=e.get('tempo_fit_s'), tempo_busca_s=e.get('tempo_busca_s'),
                             chaves=';'.join(sorted(e.keys()))))

c = pd.DataFrame(rows); salva(c, 'b01_censo.csv')
dd = pd.DataFrame(decs_all); salva(dd, 'b01_decisoes.csv')
print('celulas', len(c), 'decisoes', len(dd))
for col in ['ok_ngen','ok_fases','sem_furos','footer_runner']:
    print(col, c[col].sum(), '/', len(c))
print(c.groupby('tier')[['N','I_eff','I_max','D']].describe().T.to_string())
