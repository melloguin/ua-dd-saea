#!/usr/bin/env python
"""BATERIA 4 — saúde: cadência/finalProbe, AUC refinada, tendência do Error1,
comparação PAREADA gated x aleatório, guards, aritmética do Arc, timing.
"""
import os, json
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c217'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c217'
G = pd.read_pickle(f'{OUT}/c217_identidades.pkl')
I = pd.read_csv(f'{OUT}/c217_infills.csv')
B = pd.read_csv(f'{OUT}/c217_sonda_blocos.csv')
C = pd.read_csv(f'{OUT}/c217_celulas.csv')
SE = pd.read_csv(f'{OUT}/c217_sonda_eventos.csv')
GU = pd.read_csv(f'{OUT}/c217_guards.csv')

print('=== 1. CADÊNCIA DA SONDA / finalProbe ===')
rows = []
for _, c in C.iterrows():
    p = c.problema; ng = c.n_geracoes; ge = c.n_gen_events
    obs = sorted(SE[SE.problema == p].geracao.unique())
    esp = [1] + [g for g in range(2, ge + 1) if g % 2 == 0]
    falt = sorted(set(esp) - set(obs)); extra = sorted(set(obs) - set(esp))
    mot = SE[SE.problema == p].motivo.value_counts().to_dict()
    rows.append(dict(problema=p, n_blocos=len(obs), n_esperado=len(esp), faltando=len(falt),
                     extra=json.dumps([int(x) for x in extra]), motivos=json.dumps({str(k): int(v) for k, v in mot.items()}),
                     ult_gen_completa=ge, fantasma=ng, ult_par=(ge % 2 == 0),
                     ok_flag=int(SE[SE.problema == p].ok.all()),
                     n_pontos_ok=int((SE[SE.problema == p].n_pontos == 2000).all())))
CAD = pd.DataFrame(rows); CAD.to_csv(f'{OUT}/c217_cadencia.csv', index=False)
print(CAD.to_string())
print('blocos faltando (total):', CAD.faltando.sum(), '| células com extra:', int((CAD.extra != '[]').sum()))
print('eventos motivo=final:', int((SE.motivo == 'final').sum()), SE[SE.motivo == 'final'][['problema', 'geracao']].to_dict('records'))
print('x_hash sonda == artefato:', int((C.sonda_x_hash.nunique() >= 1)), '| n_blocos ⑥ == manifesto:',
      int((CAD.set_index('problema').n_blocos == C.set_index('problema').n_blocos_manif).sum()), '/25')

print()
print('=== 2. AUC (só blocos INFORMATIVOS: score com >=2 valores) ===')
B['inform'] = B.score_uniq != '[0.0]'
Bi = B[B.inform]
print('blocos informativos:', len(Bi), '/', len(B), '| células:', Bi.problema.nunique())
print('AUC_good  mediana %.4f  >0.5 em %.1f%%' % (Bi.auc_good.median(), 100 * (Bi.auc_good > 0.5).mean()))
print('AUC_nd    mediana %.4f  >0.5 em %.1f%%' % (Bi.auc_nd.median(), 100 * (Bi.auc_nd > 0.5).mean()))
r = Bi.groupby('problema').agg(nb=('n', 'size'), auc=('auc_good', 'median'), aucnd=('auc_nd', 'median'),
                               frac0=('frac_0', 'median'), conf=('conf', 'median'))
# tendência: 1º quartil de blocos -> 4º quartil
def tend(t, col):
    t = t.sort_values('geracao'); k = max(1, len(t) // 4)
    return t[col].iloc[:k].mean(), t[col].iloc[-k:].mean()
tr = Bi.groupby('problema').apply(lambda t: pd.Series(dict(zip(['auc_q1', 'auc_q4'], tend(t, 'auc_good')))), include_groups=False)
tr2 = Bi.groupby('problema').apply(lambda t: pd.Series(dict(zip(['ndc_q1', 'ndc_q4'], tend(t, 'auc_nd')))), include_groups=False)
r = r.join(tr).join(tr2); r['d_auc'] = r.auc_q4 - r.auc_q1; r['d_nd'] = r.ndc_q4 - r.ndc_q1
print(r.to_string())
r.to_csv(f'{OUT}/c217_sonda_resumo.csv')

print()
print('=== 3. TENDÊNCIA do Error1 (p+) por quartil de gerações ===')
def q14(t):
    t = t.sort_values('geracao'); k = max(1, len(t) // 4)
    return pd.Series(dict(q1=t.p_mais.iloc[:k].mean(), q4=t.p_mais.iloc[-k:].mean(),
                          med=t.p_mais.median(), mx=t.p_mais.max(), zero=float((t.p_mais == 0).mean())))
E = G.groupby('problema').apply(q14, include_groups=False); E['delta'] = E.q4 - E.q1
print(E.to_string())
print('sobe (q4>q1) em', int((E.delta > 0).sum()), '/25 ; cai em', int((E.delta < 0).sum()))
E.to_csv(f'{OUT}/c217_error1_tendencia.csv')

print()
print('=== 4. COMPARAÇÃO PAREADA gated x aleatório (janela ±25 gerações, mesma célula) ===')
I['gated'] = I.estado.isin([1, 2])
pares = []
for (p), t in I.groupby('problema'):
    gt = t[t.gated]; rd = t[~t.gated]
    for _, r in gt.iterrows():
        w = rd[(rd.geracao >= r.geracao - 25) & (rd.geracao <= r.geracao + 25)]
        if len(w) >= 5:
            pares.append(dict(problema=p, geracao=r.geracao, estado=r.estado,
                              fd_gated=r.frac_domina, fd_rand=w.frac_domina.mean(),
                              nd_gated=r.nd_vs_arq, nd_rand=w.nd_vs_arq.mean(), nviz=len(w)))
PA = pd.DataFrame(pares); PA.to_csv(f'{OUT}/c217_pareado.csv', index=False)
print('pares formados:', len(PA), 'de', int(I.gated.sum()), 'infills gated')
print('frac_domina  gated %.4f  vs  vizinhança aleatória %.4f   (razão %.2fx)' %
      (PA.fd_gated.mean(), PA.fd_rand.mean(), PA.fd_gated.mean() / PA.fd_rand.mean()))
print('gated > vizinhança em', int((PA.fd_gated > PA.fd_rand).sum()), '/', len(PA))
print('nd_vs_arq    gated %.4f  vs  %.4f' % (PA.nd_gated.mean(), PA.nd_rand.mean()))
for e in [1, 2]:
    s = PA[PA.estado == e]
    if len(s):
        print('  estado %d: n=%d  fd_gated %.4f  fd_rand %.4f  (%.2fx)  gated>viz %d/%d' %
              (e, len(s), s.fd_gated.mean(), s.fd_rand.mean(), s.fd_gated.mean() / s.fd_rand.mean(),
               int((s.fd_gated > s.fd_rand).sum()), len(s)))
from scipy.stats import wilcoxon
try:
    print('Wilcoxon pareado (fd_gated vs fd_rand): p =', wilcoxon(PA.fd_gated, PA.fd_rand).pvalue)
except Exception as e:
    print('wilcoxon:', e)

print()
print('=== 5. GUARDS e ARITMÉTICA DO ARQUIVO ===')
print(GU.groupby(['problema', 'name']).size().to_string())
print('guards por nome:', GU.name.value_counts().to_dict())
gc = GU.groupby('problema').size().rename('n_guards')
cc = C.set_index('problema')
print('guards ≡ manifest.cache_hits:', int((gc.reindex(cc.index).fillna(0) == cc.cache_hits).sum()), '/25')
arr = GU[GU.name == 'cache_hit']
print('cache_hit com fe==1 e solution_id==0:', int(((arr.fe == 1) & (arr.solution_id == 0)).sum()), 'em',
      arr[(arr.fe == 1) & (arr.solution_id == 0)].problema.nunique(), 'células')
sl = G.groupby('problema').lote.sum().rename('soma_lote')
ar = pd.DataFrame({'soma_lote': sl, 'init': cc.n_init, 'nreal': cc.n_real, 'ch': cc.cache_hits})
ar['pred'] = ar.init + ar.soma_lote - (ar.ch - 1)
ar['fantasma'] = ar.nreal - ar.pred
print(ar.to_string())
print('fantasma==1 em', int((ar.fantasma == 1).sum()), '/25 ; distribuição', ar.fantasma.value_counts().to_dict())

print()
print('=== 6. ② duplicatas == re-add de cache-hit ===')
dupinfo = []
for _, c in C.iterrows():
    dupinfo.append(dict(problema=c.problema, pop_dup_total=c.pop_dup_total, pop_dup_gens=c.pop_dup_gens,
                        cache_hits=c.cache_hits, pop_last=c.pop_last, maxfe=c.maxfe))
DP = pd.DataFrame(dupinfo)
DP['excesso'] = DP.pop_last - DP.maxfe
print(DP.to_string())
print('pop_last - maxfe == cache_hits-1:', int((DP.excesso == DP.cache_hits - 1).sum()), '/25')

print()
print('=== 7. TIMING: sonda no ④ x ⑤ ===')
rows = []
for _, c in C.iterrows():
    p = c.problema
    t = pq.read_table(f'{ROOT}/{p}/42/exp_main_c217_{p}_42__timing.parquet').to_pandas()
    gsonda = set(SE[SE.problema == p].geracao)
    t['tem_bloco'] = t.geracao.isin(gsonda)
    ok2 = ((t.tempo_pred_sonda_s > 0) == t.tem_bloco).mean()
    rows.append(dict(problema=p, t_ok2=ok2, soma_sonda4=t.tempo_pred_sonda_s.sum(), sonda5=c.t_sonda,
                     gap=c.t_sonda - t.tempo_pred_sonda_s.sum(),
                     soma_fit4=t.tempo_fit_s.sum(), fit5=c.t_fit,
                     soma_ger=t.tempo_geracao_s.sum(), total5=c.t_total,
                     frac_fit=c.t_fit / c.t_total, frac_sonda=c.t_sonda / c.t_total,
                     frac_busca=c.t_busca / c.t_total, frac_aval=c.t_aval / c.t_total))
T = pd.DataFrame(rows); T.to_csv(f'{OUT}/c217_timing.csv', index=False)
print(T.to_string())
print('t_ok2 == 1.0 em', int((T.t_ok2 == 1).sum()), '/25')
print('perfil mediano: fit %.2f%% sonda %.2f%% busca %.2f%% aval %.4f%%' %
      (100 * T.frac_fit.median(), 100 * T.frac_sonda.median(), 100 * T.frac_busca.median(), 100 * T.frac_aval.median()))
