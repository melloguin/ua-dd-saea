#!/usr/bin/env python
"""BATERIA 1 — estrutura, gerações, guards, sonda-eventos, timing (25 células c217, semente 42).
Escreve: c217_celulas.csv, c217_geracoes.pkl/.csv, c217_guards.csv, c217_sonda_eventos.csv
READ-ONLY sobre resultados_experimentos.
"""
import json, os, math, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c217'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c217'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
SONDA = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'

problemas = sorted(os.listdir(ROOT))
cel, gens, guards, sondas = [], [], [], []

for prob in problemas:
    base = f'{ROOT}/{prob}/42/exp_main_c217_{prob}_42'
    m = json.load(open(base + '.manifest.json'))
    hdr = ftr = None
    grows, srows, growds = [], [], []
    for line in open(base + '.jsonl'):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        r = d.get('rec')
        if r == 'header':
            hdr = d
        elif r == 'footer':
            ftr = d
        elif r == 'guard':
            guards.append(dict(problema=prob, **{k: v for k, v in d.items() if k != 'rec'}))
        elif r == 'sonda':
            sondas.append(dict(problema=prob, **{k: v for k, v in d.items() if k != 'rec'}))
        elif r == 'c217_gen':
            g = {k: v for k, v in d.items() if k not in ('rec', 'ts', 'f_best', 'modelo_hp')}
            g['spread'] = d.get('modelo_hp', {}).get('spread')
            g['f_best'] = json.dumps(d.get('f_best'))
            g['problema'] = prob
            grows.append(g)
    gdf = pd.DataFrame(grows)
    gens.append(gdf)

    real = pq.read_table(base + '__real.parquet').to_pandas()
    pop = pq.read_table(base + '__pop.parquet').to_pandas()
    tim = pq.read_table(base + '__timing.parquet').to_pandas()
    sur_md = pq.ParquetFile(base + '__surrogate.parquet').metadata

    D = hdr['D']; M = hdr['M']
    xc = [f'x{i}' for i in range(D)]

    # U2: DoE bit-a-bit vs artefato
    doe_p = f'{DOE}/{prob}/doe_{prob}_42.parquet'
    dmax = np.nan; doe_hash_art = None
    if os.path.exists(doe_p):
        X0 = pq.read_table(doe_p).to_pandas()[xc].to_numpy()
        doe_hash_art = json.load(open(doe_p.replace('.parquet', '.manifest.json')))['doe_hash']
        Xi = real[real.fase == 'init'][xc].to_numpy()
        if X0.shape == Xi.shape:
            dmax = float(np.max(np.abs(X0.astype(np.float32) - Xi.astype(np.float32))))
    # ② tamanhos por geração
    psz = pop.groupby('geracao').size()
    dup = pop.groupby('geracao').apply(lambda t: int(t.solution_id.duplicated().sum()), include_groups=False)

    cel.append(dict(
        problema=prob, D=D, M=M, maxfe=m['maxfe'], fe_final=m['fe_final'],
        n_geracoes=m['n_geracoes'], status=m['status'], termino=ftr['termino'] if ftr else None,
        cp_init=ftr['cp_init'] if ftr else None, cache_hits=m['cache_hits'],
        fallback=m['fallback_ativado'], doe_hash=m['doe_hash'], algo_version=m['algo_version'],
        N=hdr['N'], delta=hdr['delta'], gmax=hdr['gmax'],
        n_real=len(real), n_init=int((real.fase == 'init').sum()),
        fe_index_denso=bool((np.sort(real.fe_index.to_numpy()) == np.arange(len(real))).all()),
        sid_denso=bool((np.sort(real.solution_id.to_numpy()) == np.arange(len(real))).all()),
        doe_dmax=dmax, doe_hash_art=doe_hash_art,
        n_pop_rows=len(pop), n_pop_grupos=int(psz.shape[0]), pop_g1=int(psz.iloc[0]),
        pop_last=int(psz.iloc[-1]), pop_dup_total=int(dup.sum()), pop_dup_gens=int((dup > 0).sum()),
        n_timing=len(tim), n_gen_events=len(gdf), n_sur_rows=sur_md.num_rows,
        n_blocos_manif=m['sonda']['n_blocos'], sonda_S=m['sonda']['S'], sonda_k=m['sonda']['k'],
        sonda_x_hash=m['sonda']['x_hash'], sonda_falhas=m['sonda']['n_falhas'],
        t_total=m['timing']['tempo_total_s'], t_fit=m['timing']['tempo_fit_surrogate_s'],
        t_busca=m['timing']['tempo_busca_s'], t_aval=m['timing']['tempo_aval_real_s'],
        t_sonda=m['timing']['tempo_pred_sonda_s'],
        fit_series_len=len(m['fit_series']),
        sigma_dict=json.dumps(m['sigma_dict'], sort_keys=True),
        env=json.dumps(m['env'], sort_keys=True),
        # timing invariantes
        t_inv1=int((tim.tempo_fit_s + tim.tempo_busca_s <= tim.tempo_geracao_s + 1e-9).sum()),
        t_rows=len(tim),
        fit_pos=int((tim.tempo_fit_s > 0).sum()),
    ))
    print(prob, 'ok', len(gdf), 'gens')

pd.DataFrame(cel).to_csv(f'{OUT}/c217_celulas.csv', index=False)
G = pd.concat(gens, ignore_index=True)
G.to_pickle(f'{OUT}/c217_geracoes.pkl')
G.to_csv(f'{OUT}/c217_geracoes.csv', index=False)
pd.DataFrame(guards).to_csv(f'{OUT}/c217_guards.csv', index=False)
pd.DataFrame(sondas).to_csv(f'{OUT}/c217_sonda_eventos.csv', index=False)
print('TOTAL gerações', len(G), '| células', len(cel))
