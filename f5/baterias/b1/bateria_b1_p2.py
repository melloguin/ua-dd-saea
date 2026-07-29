"""Bateria b1 - parte 2: cache-hit por iteracao, best_sid, duplicatas float32 da (1),
janela de violacao do timing, streaks de cache, dist_min_arquivo.
Saida: b1_p2.csv
"""
import json, os
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b1'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b1'
probs = sorted([p for p in os.listdir(ROOT) if not p.startswith(('_', '.')) and p != 'WFG1'])
rows = []
for p in probs:
    base = f'{ROOT}/{p}/42/exp_main_b1_{p}_42'
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl')]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    ge = [e for e in evs if e['rec'] == 'b1_gen']
    guards = [e for e in evs if e['rec'] == 'guard']
    D, M = hdr['D'], hdr['M']
    real = pd.read_parquet(base + '__real.parquet').sort_values('fe_index').reset_index(drop=True)
    tim = pd.read_parquet(base + '__timing.parquet')
    xc = [f'x{i}' for i in range(D)]
    fc = [f'f{i}' for i in range(M)]
    X = np.ascontiguousarray(real[xc].values.astype(np.float32))
    F = real[fc].values.astype(np.float64)
    SID = real['solution_id'].values

    # --- duplicatas float32 na (1) ---
    keys = list(map(bytes, X))
    ser = pd.Series(keys)
    dupmask = ser.duplicated(keep=False)
    n_dupX = int(ser.duplicated().sum())
    dmaxf = 0.0
    if n_dupX:
        for k, idx in ser[dupmask].groupby(ser[dupmask]).groups.items():
            idx = np.asarray(list(idx))
            dmaxf = max(dmaxf, float(np.abs(F[idx] - F[idx[0]]).max()))

    # --- cache-hit por iteracao (do guard, casando o fe) ---
    ch_fes = [g['fe'] for g in guards if g['name'] == 'cache_hit']
    from collections import defaultdict
    ch_sids = defaultdict(list)
    for g in guards:
        if g['name'] == 'cache_hit':
            ch_sids[g['fe']].append(g['solution_id'])
    from collections import Counter
    chc = Counter(ch_fes)
    n_c0 = chc.get(1, 0)
    it_rows = []
    for e in ge:
        fe = e['fe']
        it_rows.append(dict(geracao=e['geracao'], fe=fe, best_sid=e['best_sid'],
                            dist_min=e.get('dist_min_arquivo'),
                            sid_prev=SID[fe - 1] if fe - 1 < len(SID) else -1))
    itd = pd.DataFrame(it_rows)
    # uma iteracao e cache-hit sse dist_min_arquivo == 0 (o infill ja esta no arquivo)
    itd['cache'] = itd.dist_min == 0
    n_cache_it = int(itd.cache.sum())
    # best_sid pertence ao (1)?
    sidset = set(SID.tolist())
    in_real = int(itd.best_sid.isin(sidset).sum())
    # best_sid == solution_id da linha aberta pelo infill (so nas nao-cache)
    nc = itd[~itd.cache]
    sid_ok_nc = int((nc.best_sid == nc.sid_prev).sum())
    # nas cache-hit: best_sid == solution_id logado no guard
    ch = itd[itd.cache]
    ok_ch = int(sum(1 for _, r in ch.iterrows() if r.best_sid in ch_sids.get(r.fe, [])))

    # --- streaks de cache ---
    arr = itd.cache.values.astype(int)
    streak, best_streak, cur = 0, 0, 0
    for v in arr:
        cur = cur + 1 if v else 0
        best_streak = max(best_streak, cur)

    # --- timing: quais geracoes de sonda NAO violam ---
    gsonda = set(man['sonda']['geracoes'])
    tim = tim.copy()
    tim['viol'] = (tim.tempo_fit_s + tim.tempo_busca_s + tim.tempo_pred_sonda_s.fillna(0)) > tim.tempo_geracao_s
    tsp_last = float(tim.loc[tim.geracao == len(ge), 'tempo_pred_sonda_s'].fillna(0).iloc[0]) if len(tim) else np.nan
    gv = set(tim.loc[tim.viol, 'geracao'].astype(int))
    falta = sorted(gsonda - gv)
    sobra = sorted(gv - gsonda)
    # (4) tem tempo_pred_sonda_s preenchido exatamente nas gens de sonda?
    gsp = set(tim.loc[tim.tempo_pred_sonda_s.fillna(0) > 0, 'geracao'].astype(int))

    rows.append(dict(problema=p, D=D, M=M, n_iter=len(ge),
                     n_dupX_f32=n_dupX, dupX_maxdF=dmaxf,
                     cache_manifest=man['cache_hits'], c0=n_c0,
                     cache_iter=n_cache_it, cache_iter_ok=(n_cache_it == man['cache_hits'] - n_c0),
                     best_sid_in_real=in_real, sid_ok_nc=sid_ok_nc, n_nc=len(nc),
                     sid_ok_ch=ok_ch, n_ch=len(ch), streak_max=best_streak,
                     sonda_gens=len(gsonda), viol_gens=len(gv),
                     falta=str(falta), sobra=str(sobra),
                     pred_sonda_eq_sonda=(gsp == gsonda), n_pred_sonda=len(gsp), tsp_last=tsp_last))
    print(p, 'dupX32', n_dupX, 'maxdF', f'{dmaxf:.3g}', 'cacheIt', n_cache_it, '/', man['cache_hits'] - n_c0,
          'sid_nc', sid_ok_nc, '/', len(nc), 'sid_ch', ok_ch, '/', len(ch), 'streak', best_streak,
          'falta', falta[:4], 'sobra', sobra[:4])

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/b1_p2.csv', index=False)
print()
print('TOTAL dupX float32:', df.n_dupX_f32.sum(), 'max |dF| entre duplicatas:', df.dupX_maxdF.max())
print('cache por iteracao:', df.cache_iter.sum(), 'ok em', df.cache_iter_ok.sum(), '/23')
print('best_sid in (1):', df.best_sid_in_real.sum(), '/', df.n_iter.sum())
print('best_sid == infill (nao-cache):', df.sid_ok_nc.sum(), '/', df.n_nc.sum())
print('best_sid == guard sid (cache):', df.sid_ok_ch.sum(), '/', df.n_ch.sum())
print('pred_sonda == sonda gens:', df.pred_sonda_eq_sonda.sum(), '/23')
