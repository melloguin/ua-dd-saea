#!/usr/bin/env python
"""
BATERIA E — c262 qNEHVI (F5.3b, protocolo v1.1). READ-ONLY nos dados.
Escreve SOMENTE em f5/baterias/c262/.

E1  QUERY-JOIA REFINADA (a prova do elo ⑥↔③): o bloco ③ de cada geração é o
    CONJUNTO dos 10 candidatos dos restarts do optimize_acqf, REORDENADO com o
    escolhido (argmax do qLogNEHVI) na ÚLTIMA linha. Teste: a partição de
    equivalência das 10 linhas por x (candidatos que convergiram ao MESMO ótimo)
    tem de bater com a partição dos 10 valores de `acqf_todos_restarts` sob a
    permutação σ = [i≠best] + [best]. Comparo com a hipótese nula (permutação
    identidade) para mostrar que a reordenação é a explicação, não coincidência.
E2  C1 dissecado: a única iteração em que n_baseline>0 sem ponto ESTRITAMENTE
    dentro da caixa do ref (DTLZ4 it 23) — margem ao ref.
E3  ref da aquisição × tabela S.5 CONGELADA (oráculo D73): igualdade exata
    header.ideal_s5/nadir_s5 vs src.metrics.reference_bounds + álgebra do paper.
E4  aritmética do treino: fe == n_train + q; n_train == n_init + infills anteriores;
    fit_series do ⑤ ≡ decisões do ⑥ (n_acumulado e tempo_fit_s).
E5  acqf_warnings × paisagem (dist_min, cache-hit, spread).
E6  ranks (SA-only e all-algs) + pisos, do metricas_finais_f52c.csv.
E7  sonda: agregados por célula-objetivo (WAPE 1º/último, cobertura, σ-NaN).
"""
import json, glob, os, collections, sys
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
F5   = f'{REPO}/f5'
OUT  = f'{F5}/baterias/c262'
PROBS = sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))

sys.path.insert(0, REPO)
from src import metrics as _m


def partition(vals, same):
    """rotulagem canônica de uma partição induzida por `same(a,b)`."""
    lab = [-1]*len(vals)
    nxt = 0
    for i in range(len(vals)):
        if lab[i] != -1:
            continue
        lab[i] = nxt
        for j in range(i+1, len(vals)):
            if lab[j] == -1 and same(vals[i], vals[j]):
                lab[j] = nxt
        nxt += 1
    return tuple(lab)


rows, e2, e5 = [], [], []
for prob in PROBS:
    b = f'{ROOT}/{prob}/42'; s = f'exp_main_c262_{prob}_42'
    man = json.load(open(f'{b}/{s}.manifest.json'))
    recs = [json.loads(l) for l in open(f'{b}/{s}.jsonl') if l.strip()]
    by = collections.defaultdict(list)
    for x in recs: by[x.get('rec')].append(x)
    hdr = by['header'][0]; dec = by['decision']
    D, M, ng = hdr['D'], hdr['M'], man['n_geracoes']
    n_init = 11*D - 1
    real = pd.read_parquet(f'{b}/{s}__real.parquet')
    sur = pd.read_parquet(f'{b}/{s}__surrogate.parquet')
    on = sur[sur.regime == 'online'].reset_index(drop=True)
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{j}' for j in range(M)]
    r = {'problema': prob, 'D': D, 'M': M, 'n_ger': ng}

    # ---------------- E1 ----------------
    dec_by_it = {d['it']: d for d in dec}
    ok_perm = ok_id = tot = 0
    ok_last_is_argmax_cluster = 0
    n_clusters = []
    falhas = []
    for g, sub in on.groupby('geracao', sort=True):
        d = dec_by_it.get(int(g))
        if d is None or len(sub) != 10:
            continue
        a = np.array(d['acqf_todos_restarts'], float)
        if len(a) != 10:
            continue
        X = sub[xc].values.astype(np.float64)
        # escala do bloco p/ tolerância relativa
        sc = max(1.0, float(np.abs(X).max()))
        px = partition(list(X), lambda u, v: np.max(np.abs(u-v)) <= 1e-5*sc)
        best = int(np.argmax(a))
        sig = [i for i in range(10) if i != best] + [best]
        aa = a[sig]
        sca = max(1.0, float(np.abs(a).max()))
        pa = partition(list(aa), lambda u, v: abs(u-v) <= 1e-8*sca)
        pid = partition(list(a), lambda u, v: abs(u-v) <= 1e-8*sca)
        tot += 1
        n_clusters.append(len(set(px)))
        if px == pa: ok_perm += 1
        else: falhas.append((int(g), px, pa))
        if px == pid: ok_id += 1
        # a última linha (o escolhido) pertence ao cluster do argmax?
        if px[9] == pa[9]: ok_last_is_argmax_cluster += 1
    r['E1_tot'] = tot; r['E1_perm_ok'] = ok_perm; r['E1_id_ok'] = ok_id
    r['E1_clusters_med'] = float(np.median(n_clusters)) if n_clusters else np.nan
    r['E1_clusters_1'] = int(sum(1 for c in n_clusters if c == 1))
    r['E1_falhas'] = json.dumps([f[0] for f in falhas][:12])

    # ---------------- E2 ----------------
    ref = np.array(hdr['acqf_ref_f'], float)
    F = real.sort_values('fe_index')[fc].values.astype(np.float64)
    dentro = (F < ref).all(axis=1)
    cum = np.cumsum(dentro)
    for d in dec:
        nt = d.get('n_train') or man['fe_final']
        nd = int(cum[nt-1])
        if (nd > 0) != (d['n_baseline'] > 0):
            sub = F[:nt]
            marg = (ref - sub).min(axis=1)     # >0 ⇒ dentro em todas as dims
            k = int(np.argmax(marg))
            e2.append(dict(problema=prob, it=d['it'], n_baseline=d['n_baseline'],
                           n_dentro_estrito=nd, n_train=nt,
                           melhor_margem=float(marg[k]),
                           f_do_melhor=json.dumps([float(v) for v in sub[k]]),
                           ref=json.dumps([float(v) for v in ref]),
                           n_com_margem_ge_0=int((marg >= 0).sum()),
                           n_com_margem_gt_m1e3=int((marg > -1e-3*np.abs(ref).max()).sum())))

    # ---------------- E3 ----------------
    ideal, nadir = _m.reference_bounds(prob)
    r['E3_ideal_bate'] = float(np.max(np.abs(np.array(hdr['ideal_s5'], float) - ideal)))
    r['E3_nadir_bate'] = float(np.max(np.abs(np.array(hdr['nadir_s5'], float) - nadir)))
    ref_paper = nadir + 0.1*(nadir - ideal)     # ≡ nadir − β(ideal − nadir), β=0,1
    r['E3_ref_algebra'] = float(np.max(np.abs(ref_paper - ref)))
    r['E3_ref_man_bate'] = float(np.max(np.abs(np.array(man['acqf_ref_f'], float) - ref)))
    r['E3_ref_max_espelha'] = float(np.max(np.abs(np.array(hdr['acqf_ref_max'], float) + ref)))
    # o ref é ORÁCULO? nenhum FE do run poderia conhecê-lo na it 1
    r['E3_ref_fonte'] = hdr['ref_fonte']

    # ---------------- E4 ----------------
    inf = [d for d in dec if d['caminho'] == 'infill']
    fe_ok = sum(1 for d in inf if d['fe'] == d['n_train'] + d['q'])
    q_ok = sum(1 for d in inf if d['q'] == 1 and len(d['lote_solution_ids']) == 1)
    # n_train esperado: n_init + (nº de FE consumidos antes)
    ntr = np.array([d['n_train'] for d in inf], float)
    ch = np.array([bool(d.get('cache_hit')) for d in inf])
    esp = n_init + np.arange(len(inf)) - np.concatenate([[0], np.cumsum(ch[:-1])])
    r['E4_fe_eq_ntrain_q'] = fe_ok; r['E4_inf'] = len(inf); r['E4_q1'] = q_ok
    r['E4_ntrain_ok'] = int((ntr == esp).sum())
    fs = man['fit_series']
    r['E4_fitseries_len'] = len(fs)
    r['E4_fs_nacum_ok'] = int(sum(1 for a2, d in zip(fs, dec)
                                  if a2['n_acumulado'] == (d.get('n_train') or man['fe_final'])))
    r['E4_fs_tempo_ok'] = int(sum(1 for a2, d in zip(fs, dec)
                                  if abs(round(a2['tempo_fit_s'], 4) - d['tempo_fit_s']) <= 1e-4))
    r['E4_sol_id_eq_lote'] = int(sum(1 for d in inf if d['lote_solution_ids'] == [d['solution_id']]))
    # o escolhido é sempre um FE NOVO (fe_index == solution_id) exceto cache-hit
    sid = np.array([d['solution_id'] for d in inf])
    r['E4_sid_novo'] = int(sum(1 for d in inf if not d.get('cache_hit')))
    r['E4_sid_unicos'] = int(len(set(sid.tolist())))

    # ---------------- E5 ----------------
    for d in dec:
        e5.append(dict(problema=prob, it=d['it'], caminho=d['caminho'],
                       warn=d.get('acqf_warnings', np.nan),
                       cache_hit=bool(d.get('cache_hit', False)),
                       dist_min=d['dist_min_arquivo'],
                       spread=float(np.ptp(d['acqf_todos_restarts'])),
                       n_baseline=d['n_baseline'], n_front1=d['n_front1'],
                       acqf=d['acqf_escolhido'],
                       t_fit=d['tempo_fit_s'], t_busca=d['tempo_busca_s'],
                       n_train=d.get('n_train')))
    rows.append(r); print('[ok]', prob, flush=True)

E = pd.DataFrame(rows); E.to_csv(f'{OUT}/c262_bateriaE.csv', index=False)
pd.DataFrame(e2).to_csv(f'{OUT}/c262_E2_prune_mismatch.csv', index=False)
d5 = pd.DataFrame(e5); d5.to_parquet(f'{OUT}/c262_E5_decisoes.parquet')

pd.set_option('display.width', 300)
print('\n== E1 query-joia (permutação σ) ==')
print(E[['problema', 'E1_tot', 'E1_perm_ok', 'E1_id_ok', 'E1_clusters_med', 'E1_clusters_1', 'E1_falhas']].to_string())
print('TOTAIS E1: gerações', E.E1_tot.sum(), '| perm OK', E.E1_perm_ok.sum(),
      '| identidade OK', E.E1_id_ok.sum())
print('\n== E3 ref oráculo ==')
print(E[['problema', 'E3_ideal_bate', 'E3_nadir_bate', 'E3_ref_algebra', 'E3_ref_man_bate', 'E3_ref_max_espelha']].to_string())
print('\n== E4 aritmética ==')
print(E[['problema', 'E4_inf', 'E4_fe_eq_ntrain_q', 'E4_q1', 'E4_ntrain_ok', 'E4_fitseries_len',
         'E4_fs_nacum_ok', 'E4_fs_tempo_ok', 'E4_sol_id_eq_lote', 'E4_sid_novo', 'E4_sid_unicos']].to_string())
print('\n== E2 mismatch do prune ==')
print(pd.DataFrame(e2).to_string() if e2 else 'nenhum')

# ---------------- E5 síntese ----------------
d5o = d5[d5.caminho == 'infill']
print('\n== E5 warnings × paisagem ==')
w = d5o[d5o.warn > 0]
print('iterações com acqf_warning>0:', len(w), '/', len(d5o),
      '| dist_min mediana c/ warn %.4g' % w.dist_min.median(),
      '| sem warn %.4g' % d5o[d5o.warn == 0].dist_min.median())
print('cache-hits:', int(d5o.cache_hit.sum()), '| warn nos cache-hits:', int(w.cache_hit.sum()))
print(d5o.groupby('problema').agg(n=('it', 'size'), warn=('warn', 'sum'),
                                  ch=('cache_hit', 'sum'),
                                  dmin_med=('dist_min', 'median')).to_string())

# ---------------- E6 ranks ----------------
m = pd.read_csv(f'{F5}/metricas_finais_f52c.csv'); m = m[m.exp == 'main']
PIS = ['moead', 'nsga2', 'nsga3', 'smsemoa']
out = []
for p in PROBS:
    sub = m[m.problema == p]
    me = sub[sub.alg == 'c262']
    if me.empty: continue
    ig = float(me.igd_plus.iloc[0]); hv = float(me.hv.iloc[0])
    sas = sub[~sub.alg.isin(PIS)]
    todos = sub
    out.append(dict(problema=p, igd=ig, hv=hv,
                    rank_SA=int((sas.igd_plus.values < ig).sum())+1, n_SA=len(sas),
                    rank_all=int((todos.igd_plus.values < ig).sum())+1, n_all=len(todos),
                    rank_hv_SA=int((sas.hv.values > hv).sum())+1))
R = pd.DataFrame(out); R.to_csv(f'{OUT}/c262_E6_ranks.csv', index=False)
print('\n== E6 ranks ==')
print(R.to_string())
print('rank médio SA: %.2f (n=%d) | rank médio ALL: %.2f | 1º lugar SA em %d/%d | top-3 em %d/%d'
      % (R.rank_SA.mean(), len(R), R.rank_all.mean(), (R.rank_SA == 1).sum(), len(R),
         (R.rank_SA <= 3).sum(), len(R)))

# ---------------- E7 sonda ----------------
sn = pd.read_csv(f'{F5}/sonda_f52e.csv'); sn = sn[(sn.alg == 'c262') & (sn.exp == 'main')]
print('\n== E7 sonda: colunas ==', list(sn.columns))
g = []
for (p, o), sub in sn.groupby(['problema', 'obj']):
    sub = sub.sort_values('bloco')
    w0, w1 = sub.wape.iloc[0], sub.wape.iloc[-1]
    g.append(dict(problema=p, obj=o, n_blocos=len(sub), wape_ini=w0, wape_fim=w1,
                  dwape=(w1-w0)/w0 if w0 > 0 else np.nan, wape_min=sub.wape.min(),
                  cob_ini=sub.cobertura95.iloc[0], cob_fim=sub.cobertura95.iloc[-1],
                  cob_med=sub.cobertura95.median(), corr_fim=sub['corr'].iloc[-1],
                  n_nan=int(sub.n_nan.sum()) if 'n_nan' in sub else 0,
                  n_validas_min=int(sub.n_validas.min()) if 'n_validas' in sub else -1))
G = pd.DataFrame(g); G.to_csv(f'{OUT}/c262_E7_sonda.csv', index=False)
print(G.to_string())
print('\nΔWAPE mediano (célula-obj): %.4f | melhoram: %d/%d | cobertura final mediana %.4f | <0,90: %d'
      % (G.dwape.median(), (G.dwape < 0).sum(), len(G), G.cob_fim.median(), (G.cob_fim < 0.90).sum()))
print('blocos totais:', G.n_blocos.sum()//G.groupby("problema").obj.nunique().mean(),
      '| σ-NaN total:', G.n_nan.sum())
