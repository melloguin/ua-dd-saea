#!/usr/bin/env python
"""BATERIA 6 e74/CLMEA — U9 (guards x manifesto x camadas), boot de extremos, quotas do
PNN, N/k_local efetivos, pred_tipo POR LINHA, cand_vazio, contabilidade de slots
e a ENTREGA DI-07b (distribuicao do n_desalinhado por ciclo/problema).
Escreve: e74_DI07b_desalinhamento.csv, e74_u9_guards.csv, e74_boot_extremos.csv,
         e74_quotas_pnn.csv, e74_slots.csv
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))
u9, bt, qt, sl, pt = [], [], [], [], []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    boot = [r for r in recs if r['rec'] == 'e74_boot'][0]
    gu = pd.Series([r['name'] for r in recs if r['rec'] == 'guard']).value_counts().to_dict()
    ftr = [r for r in recs if r['rec'] == 'footer'][0]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    so = sur[sur.regime == 'online']
    g = pd.DataFrame(gens)
    g1 = g[g.estrategia == 1]
    n_slot = int(g.slot_perdido.sum())
    n_vazio = int((g.n_cand == 0).sum())
    n_ac = int(g.aceito.sum())
    u9.append(dict(problema=pr, D=D, M=M,
                   cache_hit_guard=gu.get('cache_hit', 0), cache_hits_man=man['cache_hits'],
                   cache_ok=(gu.get('cache_hit', 0) == man['cache_hits'] == ftr['cache_hits']),
                   dedup_guard=gu.get('dedup_slot_perdido', 0), dedup_eventos=n_slot,
                   dedup_ok=(gu.get('dedup_slot_perdido', 0) == n_slot),
                   hv_range0_guard=gu.get('hv_range0', 0),
                   hv_range0_eventos=int(sum(1 for r in gens if r.get('range0') is True)),
                   cand_vazio_guard=gu.get('cand_vazio', 0), cand_vazio_eventos=n_vazio,
                   outros=json.dumps({k: v for k, v in gu.items()
                                      if k not in ('cache_hit', 'dedup_slot_perdido', 'hv_range0', 'cand_vazio')}),
                   fe_final=man['fe_final'], footer_fe=ftr['fe_final'],
                   n_ger_man=man['n_geracoes'], n_ger_footer=ftr['n_geracoes'],
                   cp_init=ftr.get('cp_init'), termino=ftr['termino'], status=ftr['status'],
                   fallback=man['fallback_ativado'], n_retries=man['n_retries']))
    bt.append(dict(problema=pr, D=D, M=M, aceitos=boot['aceitos'], rejeitados=boot['rejeitados'],
                   M_esperado=M, ok=(boot['aceitos'] + boot['rejeitados'] == M),
                   dist_ext=json.dumps([round(x, 6) for x in boot['dist_ext']]),
                   todos_gt_eps=all(x > 1e-5 for x in boot['dist_ext'][:boot['aceitos']]),
                   n_redes=boot['modelo_hp']['n_redes'], M_saidas=boot['modelo_hp']['M_saidas'],
                   n_treino=boot['n_treino'], init_esp=11 * D - 1,
                   fe_apos_boot=boot['fe'], fe_esp=11 * D - 1 + boot['aceitos']))
    # quotas do PNN 10/30/40/20 sobre N
    q = pd.DataFrame([r['n_por_nivel_pop'] for r in gens if r['estrategia'] == 1],
                     columns=['n1', 'n2', 'n3', 'n4'])
    N = q.sum(1)
    qt.append(dict(problema=pr, N_med=float(N.median()), N_min=int(N.min()), N_max=int(N.max()),
                   f1=float((q.n1 / N).mean()), f2=float((q.n2 / N).mean()),
                   f3=float((q.n3 / N).mean()), f4=float((q.n4 / N).mean()),
                   exato_10_30_40_20=int(((q.n1 == np.floor(N * .1)) & (q.n2 == np.floor(N * .3))).sum()),
                   ciclos=len(q),
                   k_local=json.dumps(sorted({r.get('k_local_efetivo') for r in gens if r['estrategia'] == 3})),
                   arq_min=int(pop.groupby('geracao').size().min())))
    sl.append(dict(problema=pr, slots_s1=int((g.estrategia == 1).sum()),
                   aceitos_s1=int(g1.aceito.sum()), dedup_s1=int(g1.slot_perdido.sum()),
                   vazio_s1=int((g1.n_cand == 0).sum()),
                   slots_s2=int((g.estrategia == 2).sum()), aceitos_s2=int(g[g.estrategia == 2].aceito.sum()),
                   slots_s3=int((g.estrategia == 3).sum()), aceitos_s3=int(g[g.estrategia == 3].aceito.sum()),
                   fe_infill=n_ac, fe_boot=boot['aceitos'], fe_init=11 * D - 1, fe_total=man['fe_final']))
    # pred_tipo POR LINHA
    x = so.groupby('modelo_flag').pred_tipo.agg(['nunique', 'first'])
    hib = so.groupby('geracao').pred_tipo.nunique()
    pt.append(dict(problema=pr, tipos=json.dumps(x['first'].to_dict()),
                   nunique_por_flag=json.dumps(x['nunique'].to_dict()),
                   blocos_hibridos=int((hib > 1).sum()), n_blocos=len(hib),
                   mu_nulo_s1=int(so[so.modelo_flag == 'PNN(s1)'].mu_0.notna().sum()),
                   classe_nao_nula_rbf=int(so[so.modelo_flag != 'PNN(s1)'].pred_classe.notna().sum()),
                   espaco_modelo=json.dumps(so.espaco_modelo.dropna().unique().tolist()),
                   transf=json.dumps(so.transf_tipo.dropna().unique().tolist())))
    print(pr, 'ok', flush=True)

pd.set_option('display.width', 300)
U = pd.DataFrame(u9); U.to_csv(f'{OUT}/e74_u9_guards.csv', index=False)
B = pd.DataFrame(bt); B.to_csv(f'{OUT}/e74_boot_extremos.csv', index=False)
Q = pd.DataFrame(qt); Q.to_csv(f'{OUT}/e74_quotas_pnn.csv', index=False)
S = pd.DataFrame(sl); S.to_csv(f'{OUT}/e74_slots.csv', index=False)
P = pd.DataFrame(pt); P.to_csv(f'{OUT}/e74_pred_tipo.csv', index=False)
print('\n=== U9 guards x manifesto x footer ===')
print(U[['problema', 'cache_hit_guard', 'cache_ok', 'dedup_guard', 'dedup_eventos', 'dedup_ok',
         'hv_range0_guard', 'hv_range0_eventos', 'cand_vazio_guard', 'cand_vazio_eventos',
         'termino', 'status', 'cp_init', 'fallback', 'n_retries', 'outros']].to_string())
print('cache_ok', int(U.cache_ok.sum()), '/25 | dedup_ok', int(U.dedup_ok.sum()), '/25 |',
      'hv_range0 guard==eventos', int((U.hv_range0_guard == U.hv_range0_eventos).sum()), '/25 |',
      'cand_vazio guard==eventos', int((U.cand_vazio_guard == U.cand_vazio_eventos).sum()), '/25')
print('termino normal:', int((U.termino == 'normal').sum()), '/25 | cp_init True:', int(U.cp_init.sum()),
      '| fallback:', int(U.fallback.sum()), '| retries:', int(U.n_retries.sum()))
print('\n=== BOOT de extremos (Alg.1 l.5-9) ===')
print(B.to_string())
print('aceitos+rejeitados == M em', int(B.ok.sum()), '/25 | total FE de extremos:', int(B.aceitos.sum()),
      '| rejeitados no dedup:', int(B.rejeitados.sum()))
print('\n=== QUOTAS do PNN (Data_Process 10/30/40/20) ===')
print(Q.to_string())
print('\n=== CONTABILIDADE DE SLOTS ===')
print(S.to_string())
print('TOTAIS: slots s1/s2/s3 =', S.slots_s1.sum(), S.slots_s2.sum(), S.slots_s3.sum(),
      '| aceitos =', S.aceitos_s1.sum(), S.aceitos_s2.sum(), S.aceitos_s3.sum(),
      '| dedup s1 =', S.dedup_s1.sum(), '| vazio s1 =', S.vazio_s1.sum())
print('fe: init', S.fe_init.sum(), '+ boot', S.fe_boot.sum(), '+ infill', S.fe_infill.sum(),
      '=', S.fe_init.sum() + S.fe_boot.sum() + S.fe_infill.sum(), 'vs total', S.fe_total.sum())
print('\n=== pred_tipo POR LINHA ===')
print(P[['problema', 'tipos', 'blocos_hibridos', 'mu_nulo_s1', 'classe_nao_nula_rbf', 'espaco_modelo', 'transf']].head(3).to_string())
print('blocos hibridos (pred_tipo misto no mesmo bloco):', P.blocos_hibridos.sum(), 'de', P.n_blocos.sum())
print('mu preenchido em linha PNN(s1):', P.mu_nulo_s1.sum(), '| pred_classe preenchida em linha RBF:', P.classe_nao_nula_rbf.sum())

# ---------- ENTREGA DI-07b ----------
d1 = pd.read_csv(f'{OUT}/e74_s1_mecanismo.csv')
d1.to_csv(f'{OUT}/e74_DI07b_desalinhamento.csv', index=False)
print('\n############ ENTREGA DI-07b — n_desalinhado por ciclo/problema ############')
t = d1.groupby('problema').agg(
    ciclos_s1=('desal', 'size'), N=('N', 'median'),
    media=('desal', 'mean'), frac_media_pct=('desal_frac', lambda s: 100 * s.mean()),
    p50=('desal', 'median'), p75=('desal', lambda s: s.quantile(.75)),
    p90=('desal', lambda s: s.quantile(.9)), p99=('desal', lambda s: s.quantile(.99)),
    maxi=('desal', 'max'), zeros=('desal', lambda s: int((s == 0).sum())),
    noop=('count', lambda s: int((s == 0).sum())),
    slots_perdidos=('slot', 'sum'), infills=('aceito', 'sum'),
    eq8_ok=('is_argmax', lambda s: int(np.nansum(s.astype(float)))))
t['noop_pct'] = (100 * t.noop / t.ciclos_s1).round(1)
t['eq8_pct'] = (100 * t.eq8_ok / t.infills).round(1)
print(t.round(2).to_string())
print('\nGLOBAL 25 celulas: ciclos s1 =', len(d1),
      '| n_desalinhado medio =', round(d1.desal.mean(), 2), f'({100*d1.desal_frac.mean():.2f}% da pop)',
      '| mediana =', d1.desal.median(), '| max =', d1.desal.max(),
      '| ciclos no-op (count==0) =', int((d1['count'] == 0).sum()),
      f'({100*(d1["count"]==0).mean():.2f}%)')
print('decis da fracao desalinhada (todos os ciclos s1):')
print((d1.desal_frac.quantile([.1, .25, .5, .75, .9, .95, .99, 1.0]) * 100).round(2).to_string())
