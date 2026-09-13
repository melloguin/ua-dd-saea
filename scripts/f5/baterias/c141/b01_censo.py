#!/usr/bin/env python
"""B01 — censo estrutural c141 (25 celulas main, semente 42).
Coleta: params, D/M, FE, geracoes, eventos ⑥, guards, camadas, niveis da cascata.
Saida: b01_censo.csv (1 linha/celula) + b01_gen.parquet (1 linha/geracao, todas as celulas).
"""
import json, os, glob
import pandas as pd, numpy as np
from collections import Counter

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c141'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c141'
probs = sorted(os.listdir(ROOT))

rows, genrows = [], []
for pb in probs:
    d = os.path.join(ROOT, pb, '42')
    stem = os.path.join(d, f'exp_main_c141_{pb}_42')
    man = json.load(open(stem + '.manifest.json'))
    ev = [json.loads(l) for l in open(stem + '.jsonl') if l.strip()]
    cnt = Counter(e.get('rec') for e in ev)
    header = [e for e in ev if e.get('rec') == 'header'][0]
    footer = [e for e in ev if e.get('rec') == 'footer']
    footer = footer[0] if footer else {}
    gens = [e for e in ev if e.get('rec') == 'c141_gen']
    sondas = [e for e in ev if e.get('rec') == 'sonda']
    guards = [e for e in ev if e.get('rec') == 'guard']
    gcnt = Counter(g.get('name') for g in guards)

    real = pd.read_parquet(stem + '__real.parquet')
    pop = pd.read_parquet(stem + '__pop.parquet')
    sur = pd.read_parquet(stem + '__surrogate.parquet')
    tim = pd.read_parquet(stem + '__timing.parquet')
    D = header['D']; M = header['M']
    on = sur[sur.regime == 'online']
    so = sur[sur.regime == 'sonda']

    def st(g, key, sub):
        v = g.get(key)
        if isinstance(v, dict):
            return v.get(sub)
        return np.nan

    for g in gens:
        npn = g.get('n_por_nivel', {})
        genrows.append(dict(
            problema=pb, D=D, M=M, geracao=g['geracao'], fe=g['fe'], arquivo=g['arquivo'],
            nivel=g['nivel'], ramo_QU=g['ramo_QU'], motivo=g['motivo'],
            n_front1=g['n_front1'], n_front2=g['n_front2'], lote=g['lote'],
            n_pool=g['n_pool'], n_sub1=g['n_sub1'], n_sub2=g['n_sub2'],
            fit1_min=st(g,'fit1','min'), fit1_med=st(g,'fit1','med'), fit1_max=st(g,'fit1','max'),
            fit2_min=st(g,'fit2','min'), fit2_med=st(g,'fit2','med'), fit2_max=st(g,'fit2','max'),
            fit3_min=st(g,'fit3','min'), fit3_med=st(g,'fit3','med'), fit3_max=st(g,'fit3','max'),
            Q_min=st(g,'Q','min'), Q_med=st(g,'Q','med'), Q_max=st(g,'Q','max'),
            U_min=st(g,'U','min'), U_med=st(g,'U','med'), U_max=st(g,'U','max'),
            U_pool_max=g['U_pool_max'],
            entrada=npn.get('entrada'), nivel1=npn.get('nivel1'), nivel2=npn.get('nivel2'),
            selecionados=npn.get('selecionados'), lote_npn=npn.get('lote'),
            hp_bf=g['modelo_hp']['bf_type'], hp_c=g['modelo_hp']['bf_c'],
            hp_poly=g['modelo_hp']['poly'], hp_n=g['modelo_hp']['n'],
            fe_treino_max=g['fe_treino_max'], tempo_fit_s=g['tempo_fit_s'],
            tempo_busca_s=g['tempo_busca_s'], tempo_geracao_s=g['tempo_geracao_s'],
            dist_min=json.dumps(g.get('dist_min_arquivo')),
            f_best=json.dumps(g.get('f_best')),
        ))

    rows.append(dict(
        problema=pb, D=D, M=M, maxfe=man['maxfe'], fe_final=man['fe_final'],
        esperado_maxfe=31 * D - 1, init_esperado=11 * D - 1,
        n_init=(real.fase == 'init').sum(), n_real=len(real),
        n_geracoes=man['n_geracoes'], n_gen_ev=len(gens), n_timing=len(tim),
        n_fit_series=len(man['fit_series']),
        N_subpop=man['params']['N_subpop'], wmax=man['params']['wmax'],
        kernel=man['params']['kernel'], ds=man['params']['ds_dsmerge'],
        N_esperado=min(100, 11 * D - 1),
        status=man['status'], termino=footer.get('termino'), footer_status=footer.get('status'),
        cache_hits_man=man.get('cache_hits'), cache_hits_footer=footer.get('cache_hits'),
        cp_init=footer.get('cp_init'), fallback=man.get('fallback_ativado'),
        guards=json.dumps(dict(gcnt)), n_guards=len(guards),
        n_sonda_ev=len(sondas), n_blocos_man=man['sonda']['n_blocos'],
        sonda_S=man['sonda']['S'], sonda_k=man['sonda']['k'],
        sonda_linhas=man['sonda']['n_linhas'], sonda_falhas=man['sonda']['n_falhas'],
        n_online=len(on), n_sonda_rows=len(so), n_pop=len(pop),
        n_pop_gen=pop.geracao.nunique(),
        sigma0_nan=float(on.sigma_0.isna().mean()), sigma1_nan=float(on.sigma_1.isna().mean()),
        sigma2_nan=float(on.sigma_2.isna().mean()) if 'sigma_2' in on else np.nan,
        rsid_notna=int(on.real_solution_id.notna().sum()),
        modelo_flag=';'.join(map(str, sur.modelo_flag.unique())),
        pred_tipo=';'.join(map(str, sur.pred_tipo.unique())),
        espaco=';'.join(map(str, sur.espaco_modelo.unique())),
        transf=';'.join(map(str, sur.transf_tipo.unique())),
        n_ev=len(ev), ev_counts=json.dumps(dict(cnt)),
        tempo_total_s=man['timing']['tempo_total_s'],
        lote_soma=sum(g['lote'] for g in gens),
        lote_min=min(g['lote'] for g in gens), lote_max=max(g['lote'] for g in gens),
        n_lote0=sum(1 for g in gens if g['lote'] == 0),
        niveis=json.dumps(dict(Counter(g['nivel'] for g in gens))),
        ramo_QU_share=float(np.mean([g['ramo_QU'] for g in gens])),
        doe_hash=man['doe_hash'], sonda_xhash=man['sonda']['x_hash'],
    ))

df = pd.DataFrame(rows)
dg = pd.DataFrame(genrows)
df.to_csv(os.path.join(OUT, 'b01_censo.csv'), index=False)
dg.to_parquet(os.path.join(OUT, 'b01_gen.parquet'))
pd.set_option('display.width', 250, 'display.max_columns', 100)
print(df[['problema', 'D', 'M', 'maxfe', 'fe_final', 'esperado_maxfe', 'n_init', 'init_esperado',
          'n_geracoes', 'n_gen_ev', 'N_subpop', 'N_esperado', 'wmax', 'lote_soma', 'lote_min',
          'lote_max', 'n_lote0', 'niveis', 'ramo_QU_share', 'cache_hits_man', 'guards']].to_string())
print()
print('TOTAL geracoes:', len(dg), ' celulas:', len(df))
