#!/usr/bin/env python
"""B4 CSEA - Bateria 1: estrutura, contrato, gate, rotulo (query-joia), particao.
Le TODAS as 25 celulas main/semente 42. READ-ONLY. Escreve pickles/CSVs em f5/baterias/b4/.
"""
import json, os, glob, pickle
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = REPO + '/f5/baterias/b4'
SEED = 42

probs = sorted(os.listdir(ROOT))
probs = [p for p in probs if os.path.isdir(os.path.join(ROOT, p))]

def load_cell(prob):
    base = f'{ROOT}/{prob}/{SEED}/exp_main_b4_{prob}_{SEED}'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    return base, man, recs

rows_cell = []
gen_frames = []
guard_rows = []
sonda_rows = []

for prob in probs:
    base, man, recs = load_cell(prob)
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    ftr = [r for r in recs if r['rec'] == 'footer']
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    sondas = [r for r in recs if r['rec'] == 'sonda']
    guards = [r for r in recs if r['rec'] == 'guard']

    D, M = hdr['D'], hdr['M']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet',
                          columns=['regime', 'geracao', 'real_solution_id', 'mu_0', 'sigma_0',
                                   'pred_tipo', 'pred_classe', 'pred_score', 'pred_confianca',
                                   'modelo_flag', 'espaco_modelo', 'transf_tipo', 'transf_params',
                                   'fe_treino_max'])

    xcols = [c for c in real.columns if c.startswith('x') and c[1:].isdigit()]
    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    F = real[fcols].to_numpy(dtype=np.float64)
    X = real[xcols].to_numpy(dtype=np.float64)
    sid = real['solution_id'].to_numpy()

    # ---------- U1 orcamento ----------
    maxfe_esp = 31 * D - 1
    init_esp = 11 * D - 1
    n_init = int((real['fase'] == 'init').sum())
    fe_dense = bool((real['fe_index'].to_numpy() == np.arange(len(real))).all())
    sid_dense = bool((sid == np.arange(len(real))).all())

    # ---------- U2 DoE ----------
    doe_p = f'{REPO}/data/doe/{prob}/doe_{prob}_{SEED}.parquet'
    doe_ok, doe_dmax, doe_hash_ok = None, None, None
    if os.path.exists(doe_p):
        doe = pd.read_parquet(doe_p)
        dx = [c for c in doe.columns if c.startswith('x') and c[1:].isdigit()]
        Xd = doe[dx].to_numpy(dtype=np.float64)
        n = min(len(Xd), n_init)
        doe_dmax = float(np.abs(Xd[:n] - X[:n]).max())
        doe_ok = (len(Xd) == n_init)
        dm = doe_p.replace('.parquet', '.manifest.json')
        if os.path.exists(dm):
            doe_hash_ok = (json.load(open(dm)).get('sha256') or json.load(open(dm)).get('hash')) == man['doe_hash']

    # ---------- geracoes ----------
    g = pd.DataFrame([{k: v for k, v in r.items() if k not in ('modelo_hp', 'ref_ids', 'f_best')} for r in gens])
    g['problema'] = prob
    g['D'] = D; g['M'] = M
    g['n_ref_ids'] = [len(r['ref_ids']) for r in gens]
    g['ref_ids'] = [tuple(r['ref_ids']) for r in gens]
    g['n_treino_fit'] = [r.get('modelo_hp', {}).get('n_treino_fit') for r in gens]
    g['arq_hp'] = [r.get('modelo_hp', {}).get('arquitetura') for r in gens]

    # ---------- rr / tr / particao ----------
    # |D1| implicito = round(rr*n_treino) ; checa rr racional exato
    nt = g['n_treino'].to_numpy(dtype=np.float64)
    rr = g['rr'].to_numpy(dtype=np.float64)
    n1 = np.rint(rr * nt)
    rr_exato = np.abs(rr - n1 / nt) < 1e-12
    n0 = nt - n1
    tr_pred = 0.5 * np.minimum(rr, 1 - rr)
    tr_ok = np.abs(g['tr'].to_numpy(dtype=np.float64) - tr_pred) < 1e-12
    ntrein_pred = np.rint(0.75 * n0) + np.rint(0.75 * n1)
    ntrein_ok = (g['n_acumulado'].to_numpy() == ntrein_pred)
    ntrein_pred_floor = np.floor(0.75 * n0) + np.floor(0.75 * n1)
    ntrein_ok_floor = (g['n_acumulado'].to_numpy() == ntrein_pred_floor)
    g['rr_exato'] = rr_exato; g['tr_ok'] = tr_ok
    g['n1_impl'] = n1; g['n0_impl'] = n0
    g['ntrein_ok_round'] = ntrein_ok; g['ntrein_ok_floor'] = ntrein_ok_floor

    # ---------- ramos: recomputo da regra do paper ----------
    p0 = g['p0'].to_numpy(dtype=np.float64); p1 = g['p1'].to_numpy(dtype=np.float64)
    tr = g['tr'].to_numpy(dtype=np.float64)
    # paper (Alg.6) com p0<->paper p1 (cat I) e p1<->paper p2 (cat II)
    cond_R1 = (p1 < tr) | ((p0 < tr) & (p1 < 1 - tr))
    cond_R3 = (p0 > 1 - tr) & (p1 > tr)
    g['cond_R1'] = cond_R1; g['cond_R3'] = cond_R3
    # candidatas para o 0.4 hardcoded
    g['p0_lt_04'] = p0 < 0.4; g['p1_lt_04'] = p1 < 0.4
    g['p0_gt_04'] = p0 > 0.4; g['p1_gt_04'] = p1 > 0.4

    # ---------- ③ online x lote ----------
    on = sur[sur.regime == 'online'].copy()
    on_por_gen = on.groupby('geracao').size()
    g['n_online3'] = g['geracao'].map(on_por_gen).fillna(0).astype(int)
    g['lote_eq_online3'] = (g['lote'] == g['n_online3'])

    # ---------- ② pop ----------
    pop_sz = pop.groupby('geracao')['solution_id'].size()
    g['pop_size'] = g['geracao'].map(pop_sz)
    # refs subconjunto da pop da geracao?
    popsets = {int(k): set(v.tolist()) for k, v in pop.groupby('geracao')['solution_id']}
    g['refs_in_pop'] = [set(r).issubset(popsets.get(int(gg), set())) for r, gg in zip(g['ref_ids'], g['geracao'])]
    g['refs_lt_arquivo'] = [max(r) < a for r, a in zip(g['ref_ids'], g['n_treino'])]

    # ---------- reconstrucao do ARQUIVO MATLAB (com re-adds de cache-hit) ----------
    arc_ids = list(range(n_init)) + [int(v) for v in on['real_solution_id'].to_numpy()]

    # ---------- QUERY-JOIA: recomputo do rotulo -> rr ----------
    rr_code, rr_paper, arc_used = [], [], []
    for r in gens:
        ridx = np.array(r['ref_ids'], dtype=int)
        nA = int(r['n_treino'])
        Fa = F[np.array(arc_ids[:nA], dtype=int)]
        R = F[ridx]
        # regra CODIGO: label 1 <=> para CADA ref existe ao menos 1 objetivo <= ref
        lab = np.ones(nA, dtype=bool)
        for j in range(len(R)):
            lab &= (Fa <= R[j]).any(axis=1)
        rr_code.append(lab.mean())
        # regra PAPER (Alg.4): label 1 <=> domina ao menos 1 ref
        dom = np.zeros(nA, dtype=bool)
        for j in range(len(R)):
            dom |= ((Fa <= R[j]).all(axis=1) & (Fa < R[j]).any(axis=1))
        rr_paper.append(dom.mean())
        arc_used.append(nA)
    g['rr_code'] = rr_code; g['rr_paper'] = rr_paper
    g['rr_code_ok'] = np.abs(np.array(rr_code) - rr) < 1e-9
    g['rr_paper_ok'] = np.abs(np.array(rr_paper) - rr) < 1e-9

    # ---------- U11-analogo: acerto do classificador nos infills ----------
    # para cada infill (linha online da ③), rotulo VERDADEIRO vs refs da sua geracao
    ref_by_gen = {int(r['geracao']): np.array(r['ref_ids'], dtype=int) for r in gens}
    inf = on[['geracao', 'real_solution_id', 'pred_classe', 'pred_confianca']].copy()
    tv = []
    for gg, rs in zip(inf['geracao'].to_numpy(), inf['real_solution_id'].to_numpy()):
        R = F[ref_by_gen[int(gg)]]
        fi = F[int(rs)]
        tv.append(bool(np.all([(fi <= R[j]).any() for j in range(len(R))])))
    inf['label_true'] = tv
    inf['pred_bom'] = (inf['pred_classe'] == 'bom')
    inf['problema'] = prob
    infill_acc = float((inf['label_true'] == inf['pred_bom']).mean()) if len(inf) else np.nan
    infill_tpr = float(inf.loc[inf['pred_bom'], 'label_true'].mean()) if inf['pred_bom'].any() else np.nan

    # ---------- consistencia classe<->L ----------
    cc = ((sur['pred_classe'] == 'bom') == (sur['pred_confianca'] >= 0.5))
    classe_L_ok = float(cc.mean())
    # limiar exato de corte
    Lb = sur.loc[sur.pred_classe == 'bom', 'pred_confianca']
    Lr = sur.loc[sur.pred_classe == 'ruim', 'pred_confianca']

    # ---------- gate L>0.9 ----------
    on2 = on[['geracao', 'pred_confianca']].merge(g[['geracao', 'ramo', 'lote']], on='geracao', how='left')
    gate = on2.groupby('ramo')['pred_confianca'].agg(['size', 'min', 'max', 'median'])

    # ---------- sonda ----------
    sd = pd.DataFrame(sondas)
    sd['problema'] = prob
    bl = sur[sur.regime == 'sonda'].groupby('geracao').size()
    sonda_gens = sorted(bl.index.tolist())
    S = man['sonda']['S']; k = man['sonda']['k']
    cad_esp = [1] + [x for x in range(2, len(gens) + 1) if x % 2 == 0]
    cad_ok = (sonda_gens == sorted(set(cad_esp)))
    ult_gen = len(gens)
    final_probe = [r for r in sondas if r.get('motivo') != 'cadencia']

    # ---------- U9 guards ----------
    gnames = pd.Series([r['name'] for r in guards]).value_counts().to_dict()
    for r in guards:
        guard_rows.append({'problema': prob, **{kk: r.get(kk) for kk in ('name', 'solution_id', 'fe', 'x_key')}})

    # ---------- U7 timing ----------
    t_ok1 = float(((tim['tempo_fit_s'] + tim['tempo_busca_s']) <= tim['tempo_geracao_s'] + 1e-6).mean())
    gs_sonda = set(sonda_gens)
    t_sonda_pos = tim['tempo_pred_sonda_s'] > 0
    t_ok2 = float((t_sonda_pos == tim['geracao'].isin(gs_sonda)).mean())

    # ---------- U8 fe_treino_max ----------
    ftm = g['fe_treino_max'].to_numpy()
    quedas = int((np.diff(ftm) < 0).sum())

    # ---------- U10 aritmetica ----------
    n_lote = int(g['lote'].sum())
    ch = man.get('cache_hits', 0)
    arit = (n_init + n_lote - (ch - 1), len(real))
    arc_final = int(g['arquivo'].iloc[-1])
    arc_ok = (arc_final == len(real) + ch - 1)

    rows_cell.append(dict(
        problema=prob, D=D, M=M, maxfe=man['maxfe'], maxfe_esp=maxfe_esp,
        fe_final=man['fe_final'], n_linhas1=len(real), n_init=n_init, init_esp=init_esp,
        fe_dense=fe_dense, sid_dense=sid_dense, doe_ok=doe_ok, doe_dmax=doe_dmax,
        n_geracoes=man['n_geracoes'], n_gen_events=len(gens), n_tim=len(tim),
        N=hdr['N'], K_refs=hdr['K_refs'], gmax=hdr['gmax'],
        status=man['status'], termino=(ftr[0]['termino'] if ftr else None),
        cp_init=(ftr[0]['cp_init'] if ftr else None),
        cache_hits=ch, guards=json.dumps(gnames),
        n_online3=len(on), n_lote=n_lote, arit_ok=(arit[0] == arit[1]),
        arc_final=arc_final, arc_ok=arc_ok, n_infill_unico=int(on['real_solution_id'].nunique()),
        rr_exato=int(g['rr_exato'].sum()), tr_ok=int(g['tr_ok'].sum()),
        ntrein_ok_round=int(g['ntrein_ok_round'].sum()), ntrein_ok_floor=int(g['ntrein_ok_floor'].sum()),
        rr_code_ok=int(g['rr_code_ok'].sum()), rr_paper_ok=int(g['rr_paper_ok'].sum()),
        refs6=int((g['n_ref_ids'] == 6).sum()), refs_in_pop=int(g['refs_in_pop'].sum()),
        refs_lt_arq=int(g['refs_lt_arquivo'].sum()),
        pop_size_modal=int(pd.Series(g['pop_size']).mode()[0]), pop_grupos=int(pop['geracao'].nunique()),
        lote_eq_online3=int(g['lote_eq_online3'].sum()),
        classe_L_ok=classe_L_ok, Lbom_min=float(Lb.min()) if len(Lb) else np.nan,
        Lruim_max=float(Lr.max()) if len(Lr) else np.nan,
        infill_acc=infill_acc, infill_tpr=infill_tpr,
        mu_null=float(sur['mu_0'].isna().mean()), sigma_null=float(sur['sigma_0'].isna().mean()),
        predscore_null=float(sur['pred_score'].isna().mean()),
        n_sonda_blocos=len(sondas), sonda_S=S, sonda_k=k, cad_ok=cad_ok,
        n_final_probe=len(final_probe), sonda_gens_max=max(sonda_gens), ult_gen=ult_gen,
        blocos_2000=int((bl == S).sum()), n_blocos_man=man['sonda']['n_blocos'],
        t_ok1=t_ok1, t_ok2=t_ok2, ftm_quedas=quedas, ftm_min=int(ftm.min()), ftm_max=int(ftm.max()),
        stalls=int((g['lote'] == 0).sum()),
        ramo_counts=json.dumps(g['ramo'].value_counts().to_dict()),
        guard_randperm=int(g['guard_randperm'].sum()) if 'guard_randperm' in g else -1,
        wall_s=man['timing']['tempo_total_s'],
        t_fit=man['timing']['tempo_fit_surrogate_s'], t_busca=man['timing']['tempo_busca_s'],
        t_aval=man['timing']['tempo_aval_real_s'], t_sonda=man['timing']['tempo_pred_sonda_s'],
        gate_json=gate.to_json(),
    ))
    gen_frames.append(g)
    sonda_rows.append(sd)
    inf.to_pickle(f'{OUT}/infills_{prob}.pkl')
    print('ok', prob, D, M, len(gens))

cells = pd.DataFrame(rows_cell)
G = pd.concat(gen_frames, ignore_index=True)
SD = pd.concat(sonda_rows, ignore_index=True)
cells.to_csv(f'{OUT}/b4_celulas.csv', index=False)
G.drop(columns=['ref_ids']).to_csv(f'{OUT}/b4_geracoes.csv', index=False)
G.to_pickle(f'{OUT}/b4_geracoes.pkl')
SD.to_csv(f'{OUT}/b4_sonda_eventos.csv', index=False)
pd.DataFrame(guard_rows).to_csv(f'{OUT}/b4_guards.csv', index=False)
print('\n=== CELULAS ===')
pd.set_option('display.width', 250)
print(cells.to_string())
