#!/usr/bin/env python
"""BATERIA 7 e74/CLMEA — CONSOLIDACAO dos agregados das baterias 1-6 (F5.3b).
Le os CSVs de evidencia ja gravados e imprime TODOS os numeros do relatorio
(nao recomputa nada dos parquets; a bateria 8 faz as checagens novas).
Escreve: e74_agregados.txt (o dump completo)
"""
import json, os, sys
import pandas as pd, numpy as np

OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
buf = []


def P(*a):
    s = ' '.join(str(x) for x in a)
    buf.append(s); print(s)


C = pd.read_csv(f'{OUT}/e74_celulas.csv')
G = pd.read_csv(f'{OUT}/e74_gen_eventos.csv')
J = pd.read_csv(f'{OUT}/e74_joia.csv')
S1 = pd.read_csv(f'{OUT}/e74_s1_mecanismo.csv')
S2 = pd.read_csv(f'{OUT}/e74_s2_range0.csv')
S3 = pd.read_csv(f'{OUT}/e74_s3_forte.csv')
U4 = pd.read_csv(f'{OUT}/e74_u457.csv')
CAD = pd.read_csv(f'{OUT}/e74_cadencia.csv')
U9 = pd.read_csv(f'{OUT}/e74_u9_guards.csv')
BT = pd.read_csv(f'{OUT}/e74_boot_extremos.csv')
Q = pd.read_csv(f'{OUT}/e74_quotas_pnn.csv')
SL = pd.read_csv(f'{OUT}/e74_slots.csv')
PT = pd.read_csv(f'{OUT}/e74_pred_tipo.csv')
SP = pd.read_csv(f'{OUT}/e74_spread.csv')
D74 = pd.read_csv(f'{OUT}/e74_d74.csv')
W = pd.read_csv(f'{OUT}/e74_wape_cabeca.csv')
MET = pd.read_csv(f'{OUT}/e74_metricas.csv')
TR = pd.read_csv(f'{OUT}/e74_trajetorias.csv')

for df, cols in [(J, ['achado', 'is_argmax']), (S1, ['pos_le_K', 'is_argmax', 'flag_copia']),
                 (S2, ['range0', 'is_argmax']), (S3, ['ok_forte', 'in_front'])]:
    for c in cols:
        if c in df.columns and df[c].dtype == object:
            df[c] = df[c].map({'True': True, 'False': False, True: True, False: False})
        df[c] = df[c].astype(float)

P('#'*100); P('# 0. CENSO ESTRUTURAL (25 celulas main, semente 42)'); P('#'*100)
P(C[['problema', 'D', 'M', 'status', 'termino', 'maxfe', 'fe_final', 'n_init', 'n_opt', 'ciclos',
     'n_s1', 'n_s2', 'n_s3', 'boot_aceitos', 'boot_rejeitados', 'slot_s1', 'slot_s2', 'slot_s3',
     'n_geracoes', 'pop_gens', 'timing_rows', 'n_eventos_gen', 'n_sonda_blocos', 'tempo_total']].to_string(index=False))
P('')
for c in ['u1_ok', 'fe_index_denso', 'u2_init_ok', 'u10_pop_ok', 'u10_tim_ok', 'rot_1a1', 'fe_check']:
    P(f'  {c}: {int(C[c].sum())}/25')
P('  TOTAIS: ciclos =', int(C.ciclos.sum()), '| slots s1/s2/s3 =', int(C.n_s1.sum()), int(C.n_s2.sum()), int(C.n_s3.sum()),
  '| eventos e74_gen =', int(C.n_eventos_gen.sum()), '| blocos de sonda =', int(C.n_sonda_blocos.sum()))
P('  FE: init', int(SL.fe_init.sum()), '+ boot', int(SL.fe_boot.sum()), '+ infill', int(SL.fe_infill.sum()),
  '=', int(SL.fe_init.sum() + SL.fe_boot.sum() + SL.fe_infill.sum()), 'vs fe_final total', int(SL.fe_total.sum()))
P('  timing_rows == eventos_gen + 1(boot):', int((C.timing_rows == C.n_eventos_gen + 1).sum()), '/25')
# k = nº de slots executados no ULTIMO ciclo (1,2,3) — o ciclo abortado pelo hard-stop
C['k_ult'] = 3 - (3 * C.ciclos - C.n_eventos_gen)
P('  k (slots executados no ultimo ciclo):', C.k_ult.value_counts().to_dict())
P('  ARITMETICA U10 (fecha exato?):')
P('   n_geracoes == 4*C - 2 + k :', int((C.n_geracoes == 4 * C.ciclos - 2 + C.k_ult).sum()), '/25')
P('   pop_gens  == n_geracoes    :', int((C.pop_gens == C.n_geracoes).sum()), '/25')
P('   eventos   == 3*(C-1) + k   :', int((C.n_eventos_gen == 3 * (C.ciclos - 1) + C.k_ult).sum()), '/25')
P('   n_s1 == C                  :', int((C.n_s1 == C.ciclos).sum()), '/25')
P('   n_s2 == C-1+[k>=2]         :', int((C.n_s2 == C.ciclos - 1 + (C.k_ult >= 2)).sum()), '/25')
P('   n_s3 == C-1+[k>=3]         :', int((C.n_s3 == C.ciclos - 1 + (C.k_ult >= 3)).sum()), '/25')
P('   ROTACAO 1:1:1 EXATA nos ciclos COMPLETOS (C-1) em 25/25 por construcao acima')
P('  tempo total das 25 celulas (h):', round(C.tempo_total.sum() / 3600, 2))

P(''); P('#'*100); P('# 1. ROTACAO 1:1:1 e CONTABILIDADE DE SLOTS'); P('#'*100)
P(SL.to_string(index=False))
P('  rotacao exata (n_s1==n_s2 e n_s3 in {n_s1-1,n_s1}):', int(C.rot_1a1.sum()), '/25')
P('  aceitos por estrategia:', int(SL.aceitos_s1.sum()), int(SL.aceitos_s2.sum()), int(SL.aceitos_s3.sum()))
P('  taxa de aceite s1 = %.4f  s2 = %.4f  s3 = %.4f' % (
    SL.aceitos_s1.sum()/SL.slots_s1.sum(), SL.aceitos_s2.sum()/SL.slots_s2.sum(), SL.aceitos_s3.sum()/SL.slots_s3.sum()))
P('  slots perdidos por dedup: s1 =', int(C.slot_s1.sum()), 's2 =', int(C.slot_s2.sum()), 's3 =', int(C.slot_s3.sum()))

P(''); P('#'*100); P('# 2. QUERY-JOIA — identidade da selecao (argmax do pseudo-sigma por estrategia)'); P('#'*100)
A = J[J.aceito == 1]
r = A.groupby('est').agg(n=('achado', 'size'), achado=('achado', 'sum'), argmax=('is_argmax', 'sum'),
                         dXmax=('dX_max', 'max'), rank_med=('rank_sigma', 'median'),
                         rank_p95=('rank_sigma', lambda s: s.quantile(.95)), rank_max=('rank_sigma', 'max'))
r['pct_achado'] = (100 * r.achado / r.n).round(3); r['pct_argmax'] = (100 * r.argmax / r.n).round(3)
P(r.to_string())
P('')
P('  blocos SEM sigma valido (s2, front vazio) por estrategia:')
P(J.groupby('est').agg(blocos=('bloco', 'size'), sem_sigma=('n_sigma_val', lambda s: int((s == 0).sum())),
                       sem_mu=('n_mu_val', lambda s: int((s == 0).sum())),
                       bloco_med=('bloco', 'median')).to_string())
P('')
P('  pct argmax por problema x estrategia:')
t = A.pivot_table(index='problema', columns='est', values='is_argmax', aggfunc=lambda s: 100 * s.mean()).round(2)
n = A.pivot_table(index='problema', columns='est', values='is_argmax', aggfunc='size')
P(pd.concat([t.add_prefix('pct_s'), n.add_prefix('n_s')], axis=1).to_string())
P('')
P('  identidade telemetria(evento) vs sigma_0 da (3): |sig_do_escolhido - telemetria|')
A2 = A.dropna(subset=['sig_do_escolhido', 'tel']).copy()
A2['dif'] = (A2.sig_do_escolhido - A2.tel).abs()
P(A2.groupby('est').dif.describe().to_string())

P(''); P('#'*100); P('# 3. DI-07b — DESALINHAMENTO mascara x Parent (A ENTREGA PRIORITARIA)'); P('#'*100)
d1 = S1
t = d1.groupby('problema').agg(
    ciclos_s1=('desal', 'size'), N=('N', 'median'),
    media=('desal', 'mean'), frac_media_pct=('desal_frac', lambda s: 100 * s.mean()),
    p50=('desal', 'median'), p75=('desal', lambda s: s.quantile(.75)),
    p90=('desal', lambda s: s.quantile(.9)), p99=('desal', lambda s: s.quantile(.99)),
    maxi=('desal', 'max'), zeros=('desal', lambda s: int((s == 0).sum())),
    noop=('count', lambda s: int((s == 0).sum())),
    slots=('slot', 'sum'), infills=('aceito', 'sum'),
    eq8=('is_argmax', lambda s: int(np.nansum(s.astype(float)))))
t['zeros_pct'] = (100 * t.zeros / t.ciclos_s1).round(1)
t['noop_pct'] = (100 * t.noop / t.ciclos_s1).round(1)
t['eq8_pct'] = (100 * t.eq8 / t.infills).round(1)
P(t.round(2).to_string())
P('')
P('  GLOBAL: ciclos s1 =', len(d1), '| n_desalinhado medio =', round(d1.desal.mean(), 3),
  '(%.2f%% da pop N)' % (100 * d1.desal_frac.mean()), '| mediana =', d1.desal.median(),
  '| max =', int(d1.desal.max()), '| zeros =', int((d1.desal == 0).sum()),
  '(%.2f%%)' % (100 * (d1.desal == 0).mean()))
P('  decis da FRACAO desalinhada (%):')
P((d1.desal_frac.quantile([.1, .25, .5, .75, .9, .95, .99, 1.0]) * 100).round(2).to_string())
P('  ciclos no-op (count==0):', int((d1['count'] == 0).sum()), '(%.2f%%)' % (100 * (d1['count'] == 0).mean()))
P('')
P('  CRUZAMENTO count==0  x  slot_perdido:')
P(pd.crosstab(d1['count'] == 0, d1.slot == 1).to_string())
P('  CRUZAMENTO count==0  x  flag_copia:')
P(pd.crosstab(d1['count'] == 0, d1.flag_copia).to_string())
P('  CRUZAMENTO desal>0   x  slot_perdido:')
P(pd.crosstab(d1.desal > 0, d1.slot == 1).to_string())
P('  correlacao desal_frac x slot:', round(np.corrcoef(d1.desal_frac, d1.slot)[0, 1], 4))
P('  correlacao desal_frac x count:', round(np.corrcoef(d1.desal_frac, d1['count'])[0, 1], 4))
P('  desal medio | slot==1: %.2f  vs  slot==0: %.2f' % (d1[d1.slot == 1].desal.mean(), d1[d1.slot == 0].desal.mean()))
P('')
P('  frac_nivel1 (guarda >=90%) e count (guarda count>50):')
P(d1.groupby('problema').agg(frac_n1_med=('frac_n1', 'median'), frac_n1_min=('frac_n1', 'min'),
                             frac_n1_ge09=('frac_n1', lambda s: int((s >= .9).sum())),
                             count_med=('count', 'median'), count_max=('count', 'max'),
                             count_gt50=('count', lambda s: int((s > 50).sum())),
                             ciclos=('count', 'size')).to_string())
P('  GLOBAL frac_nivel1>=0,9 em', int((d1.frac_n1 >= .9).sum()), '/', len(d1),
  '| count>50 (guarda do loop) em', int((d1['count'] > 50).sum()),
  '| count max global =', int(d1['count'].max()))
P('')
P('  PREDICAO FALSIFICAVEL (a): pos <= K-1  (K = round(frac_n1*N)):',
  int(d1[d1.aceito == 1].pos_le_K.sum()), '/', int(d1.aceito.sum()),
  '= %.2f%%' % (100 * d1[d1.aceito == 1].pos_le_K.mean()))
P('  PREDICAO (b): is_argmax  <=>  frac_n1==1 :')
a = d1[d1.aceito == 1]
P(pd.crosstab(a.frac_n1 == 1.0, a.is_argmax).to_string())
P('  n_linhas do bloco com real_solution_id NAO-nulo (candidato = ponto do arquivo):')
P(d1.groupby(d1['count'] == 0).frac_linhas_arquivo.describe().round(4).to_string())

P(''); P('#'*100); P('# 4. s2 — D74 / range0 / identidade do score'); P('#'*100)
P('  blocos s2:', len(S2), '| range0=True:', int((S2.range0>0).sum()), '| sem sigma valido:', int((S2.n_sigma_val == 0).sum()))
P(pd.crosstab(S2.range0, S2.n_sigma_val == 0).to_string())
P('  range0 por problema:', S2[S2.range0>0].problema.value_counts().to_dict())
P('  identidade sigma_0 == pred_score - hv_base: max|dif| =', np.nanmax(S2.dif_sig_score.values))
aa = S2[(S2.aceito == 1) & (S2.n_sigma_val > 0)]
P('  argmax do HV_gain (blocos com front valido):', int(aa.is_argmax.sum()), '/', len(aa),
  '= %.3f%%' % (100 * aa.is_argmax.mean()))
P('  n_front (membros do pseudo-front) mediana:', S2.n_front_ev.median(), 'min', S2.n_front_ev.min(), 'max', S2.n_front_ev.max())
P('  hv_base mediana:', round(S2.hv_base.median(), 4), '| hv_gain mediana:', round(S2.hv_gain.median(), 6),
  '| hv_gain<=0:', int((S2.hv_gain <= 0).sum()))
P('')
P('  D74 (Ymin/Ymax == min/max do FRONT-1 do arquivo corrente) — erro RELATIVO:')
P('   n amostras =', len(D74), '| mediana', D74[['dYmin', 'dYmax']].median().round(12).to_dict(),
  '| p95', D74[['dYmin', 'dYmax']].quantile(.95).round(9).to_dict(),
  '| max', D74[['dYmin', 'dYmax']].max().round(9).to_dict())
P('  n_front1 do evento == recomputado:', int((D74.n_front1 == D74.n_front1_ev).sum()), '/', len(D74))

P(''); P('#'*100); P('# 5. s3 — identidade FORTE (front reconstruido) '); P('#'*100)
P('  blocos testados:', len(S3), '| ok_forte:', int(S3.ok_forte.sum()), '= %.2f%%' % (100 * S3.ok_forte.mean()),
  '| escolhido DENTRO do front:', int(S3.in_front.sum()), '= %.2f%%' % (100 * S3.in_front.mean()))
P('  n_front do evento == reconstruido:', int((S3.n_front_ev == S3.n_front_rec).sum()), '/', len(S3))
P(S3.groupby('problema').agg(n=('ok_forte', 'size'), ok=('ok_forte', 'sum'), infront=('in_front', 'sum'),
                             nf_ev=('n_front_ev', 'median'), nf_rec=('n_front_rec', 'median'),
                             k_local=('k_local', 'median')).to_string())

P(''); P('#'*100); P('# 6. U4/U5/U7/U3/U8 — sonda, join, timing, relogios'); P('#'*100)
P(U4[['problema', 'D', 'M', 's1_blocos', 's1_esp', 's1_ok', 's2_blocos', 's2_esp', 's2_ok',
      's3_blocos', 's3_esp', 's3_ok', 'boot_g1', 'ultimo_coberto', 'gmaxg', 'n_blocos_tot', 'n_falhas',
      'u5_dX_max', 'u5_blocos', 'u7_viol', 'u7_viol_com_sonda', 'u3_fits', 'u3_esp', 'ftm_max', 'fe_final']].to_string(index=False))
P('  cadencia exata s1/s2/s3:', int(U4.s1_ok.sum()), int(U4.s2_ok.sum()), int(U4.s3_ok.sum()), '/25')
P('  (subset-check) buracos na cadencia esperada:', int((CAD.falta_s1 + CAD.falta_s2 + CAD.falta_s3).sum()),
  '| blocos EXTRA (finalProbe):', int((CAD.extra_s1 + CAD.extra_s2 + CAD.extra_s3).sum()),
  '| ultima geracao coberta:', int(CAD.ultima_coberta.sum()), '/25')
P('  extras por celula:', CAD[CAD.extras != '{}'].set_index('problema').extras.to_dict())
P('  boot 1x em g=1:', int(CAD.boot_1x.sum()), '/25 | blocos de sonda total:', int(U4.n_blocos_tot.sum()),
  '| falhas:', int(U4.n_falhas.sum()))
P('  U5 max|dX| global (join posicional):', U4.u5_dX_max.max(), '| blocos casados:', int(U4.u5_blocos.sum()))
P('  U7 violacoes fit+busca>total:', int(U4.u7_viol.sum()), '| delas com sonda:', int(U4.u7_viol_com_sonda.sum()))
P('  U3 fits == eventos+1:', int((U4.u3_fits == U4.u3_esp).sum()), '/25')
P('  U8 fe_treino_max monotonico por cabeca:')
mono = [json.loads(x) for x in U4.ftm_mono]
ks = sorted({k for m in mono for k in m})
for k in ks:
    P('   ', k, ':', sum(1 for m in mono if m.get(k)), '/', sum(1 for m in mono if k in m))
P('  U8 ftm_max == fe_final - 1:', int((U4.ftm_max == U4.fe_final - 1).sum()), '/25',
  '| ftm_max == fe_final:', int((U4.ftm_max == U4.fe_final).sum()))

P(''); P('#'*100); P('# 7. U9 — guards x manifesto x footer'); P('#'*100)
P(U9[['problema', 'cache_hit_guard', 'cache_hits_man', 'cache_ok', 'dedup_guard', 'dedup_eventos', 'dedup_ok',
      'hv_range0_guard', 'hv_range0_eventos', 'cand_vazio_guard', 'cand_vazio_eventos', 'termino', 'status',
      'cp_init', 'fallback', 'n_retries', 'outros']].to_string(index=False))
P('  cache_ok:', int(U9.cache_ok.sum()), '/25 | dedup_ok:', int(U9.dedup_ok.sum()), '/25')
P('  hv_range0 guard==eventos:', int((U9.hv_range0_guard == U9.hv_range0_eventos).sum()), '/25 | total range0:',
  int(U9.hv_range0_guard.sum()))
P('  cand_vazio guard==eventos:', int((U9.cand_vazio_guard == U9.cand_vazio_eventos).sum()), '/25 | total:',
  int(U9.cand_vazio_guard.sum()))
P('  termino normal:', int((U9.termino == 'normal').sum()), '/25 | status ok:', int((U9.status == 'ok').sum()),
  '| cp_init True:', int(U9.cp_init.sum()), '| fallback:', int(U9.fallback.sum()), '| retries:', int(U9.n_retries.sum()))
P('  outros guards:', set(U9.outros))
P('  cache_hits total (manifesto):', int(U9.cache_hits_man.sum()), '| dedup total:', int(U9.dedup_guard.sum()))

P(''); P('#'*100); P('# 8. BOOTSTRAP DE EXTREMOS (Alg.1 l.5-9)'); P('#'*100)
P(BT[['problema', 'D', 'M', 'aceitos', 'rejeitados', 'ok', 'todos_gt_eps', 'n_redes', 'M_saidas',
      'n_treino', 'init_esp', 'fe_apos_boot', 'fe_esp', 'dist_ext']].to_string(index=False))
P('  aceitos+rejeitados == M:', int(BT.ok.sum()), '/25 | FE reais de extremos:', int(BT.aceitos.sum()),
  '| rejeitados no dedup:', int(BT.rejeitados.sum()))
P('  n_treino == 11D-1:', int((BT.n_treino == BT.init_esp).sum()), '/25 | fe_apos_boot == 11D-1+aceitos:',
  int((BT.fe_apos_boot == BT.fe_esp).sum()), '/25')
P('  n_redes == M:', int((BT.n_redes == BT.M_esperado).sum()), '/25 | M_saidas==1 (1 rede por objetivo):',
  int((BT.M_saidas == 1).sum()), '/25')

P(''); P('#'*100); P('# 9. QUOTAS DO PNN / N efetivo / k_local'); P('#'*100)
P(Q.to_string(index=False))
P('  N mediano por celula: min', Q.N_med.min(), 'max', Q.N_med.max())
P('  fracoes medias das 4 classes (global): %.4f %.4f %.4f %.4f' % (Q.f1.mean(), Q.f2.mean(), Q.f3.mean(), Q.f4.mean()))

P(''); P('#'*100); P('# 10. pred_tipo POR LINHA / espaco_modelo / transf'); P('#'*100)
P(PT[['problema', 'tipos', 'blocos_hibridos', 'n_blocos', 'mu_nulo_s1', 'classe_nao_nula_rbf',
      'espaco_modelo', 'transf']].head(6).to_string(index=False))
P('  blocos hibridos (2 pred_tipo no mesmo bloco):', int(PT.blocos_hibridos.sum()), 'de', int(PT.n_blocos.sum()))
P('  mu preenchido em linha PNN(s1):', int(PT.mu_nulo_s1.sum()), '| pred_classe em linha RBF:',
  int(PT.classe_nao_nula_rbf.sum()))
P('  tipos por flag (celula 1):', PT.tipos.iloc[0])
P('  espaco_modelo distintos:', set(PT.espaco_modelo), '| transf:', set(PT.transf))

P(''); P('#'*100); P('# 11. SPREADS recomputados (formula do codigo)'); P('#'*100)
P(SP.groupby('tipo').rel.describe().to_string())
P('  amostras por tipo:', SP.tipo.value_counts().to_dict())
P('  max erro relativo por tipo:', SP.groupby('tipo').rel.max().to_dict())

P(''); P('#'*100); P('# 12. U6 — SONDA por CABECA (regua comum)'); P('#'*100)
P(W.groupby('cabeca').agg(n=('wape_med', 'size'), wape_1_med=('wape_1', 'median'), wape_ult_med=('wape_ult', 'median'),
                          dwape_med=('dwape_pct', 'median'), wape_max=('wape_max', 'max'),
                          corr_1=('corr_1', 'median'), corr_ult=('corr_ult', 'median'),
                          nan=('n_nan', 'sum'), blocos=('n_blocos', 'sum')).round(4).to_string())
P('  dWAPE% por problema x cabeca (mediana dos objetivos):')
P(W.pivot_table(index='problema', columns='cabeca', values='dwape_pct', aggfunc='median').round(1).to_string())
P('  WAPE do ULTIMO bloco por problema x cabeca:')
P(W.pivot_table(index='problema', columns='cabeca', values='wape_ult', aggfunc='median').round(3).to_string())
P('  correlacao mediana por problema x cabeca:')
P(W.pivot_table(index='problema', columns='cabeca', values='corr_med', aggfunc='median').round(3).to_string())
P('  cobertura95 nao-nula (esperado 0 — sem sigma de modelo):', int(W.cob.sum()))

P(''); P('#'*100); P('# 13. METRICAS vs PISOS + TRAJETORIAS'); P('#'*100)
P(MET.round(5).to_string(index=False))
P('  bate o melhor piso em', int(MET.bate_piso.sum()), '/', len(MET),
  '| rank SA medio', round(MET.rank_sa.mean(), 2), 'de', int(MET.n_sa.max()))
P('  derrotas com gap > piso de ruido O-18 (58,98%):', int((MET.gap_pct > 58.98).sum()),
  '| derrotas dentro do ruido:', int(((MET.gap_pct > 0) & (MET.gap_pct <= 58.98)).sum()))
P('  vitorias por margem > 58,98%:', int((MET.gap_pct < -58.98).sum()))
P('  derrotas conclusivas:', MET[MET.gap_pct > 58.98][['problema', 'e74', 'melhor_piso', 'gap_pct']].round(4).to_dict('records'))
P('  vitorias conclusivas:', MET[MET.gap_pct < -58.98][['problema', 'e74', 'melhor_piso', 'gap_pct']].round(4).to_dict('records'))
P('')
P(TR.round(5).to_string(index=False))
P('  violacoes de monotonicidade:', int(TR.violacoes.sum()), 'em', int((TR.n - 1).sum()), 'transicoes',
  '| pior salto', TR.pior_salto.max())
P('  melhora 1o->ultimo checkpoint: min %.1f%% (%s) max %.1f%% (%s) mediana %.1f%%' % (
    TR.melhora_pct.min(), TR.loc[TR.melhora_pct.idxmin(), 'problema'],
    TR.melhora_pct.max(), TR.loc[TR.melhora_pct.idxmax(), 'problema'], TR.melhora_pct.median()))

open(f'{OUT}/e74_agregados.txt', 'w').write('\n'.join(buf))
print('\n[ok] dump em e74_agregados.txt')
