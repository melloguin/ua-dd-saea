#!/usr/bin/env python
"""
BATERIA F — c262 qNEHVI: a QUERY-JOIA em forma robusta + fechamentos. READ-ONLY.

F1 (query-joia, forma 1 — a identidade dura): acqf_escolhido == max(acqf_todos_restarts)
   BIT-A-BIT, em TODAS as decisões (infill + hard_stop). |Δ| máximo global.
F2 (query-joia, forma 2 — o elo ⑥→③→①): a linha marcada com real_solution_id no bloco
   ③ da geração é SEMPRE a ÚLTIMA das 10 e o seu x é BIT-IDÊNTICO ao x que consumiu o FE
   na ①.
F3 (query-joia, forma 3 — o elo ③↔restarts, teste de REFINAMENTO): sob a permutação
   σ = [i≠argmax] + [argmax] (hipótese "o escolhido é reescrito por último"), duas linhas
   do bloco ③ com x quase-idêntico TÊM de ter acqf quase-idêntico. Conto pares e
   violações; comparo com a permutação IDENTIDADE (hipótese nula) e com uma permutação
   ALEATÓRIA (controle). σ tem de dominar.
F4 fe × n_train nos cache-hits (fe == n_train, sem +q) e nos infills normais.
F5 σ do posterior nos candidatos: monotonicidade do decaimento + faixa; erro-fantasia.
F6 ② (pop) = dataset acumulado: |②(g)| == n_init + infills até g.
"""
import json, glob, os, collections
import numpy as np, pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c262'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c262'
PROBS = sorted(os.path.basename(p) for p in glob.glob(f'{ROOT}/*') if os.path.isdir(p))
rng = np.random.default_rng(20260729)

rows = []
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
    pop = pd.read_parquet(f'{b}/{s}__pop.parquet')
    sur = pd.read_parquet(f'{b}/{s}__surrogate.parquet')
    on = sur[sur.regime == 'online'].reset_index(drop=True)
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{j}' for j in range(M)]
    r = {'problema': prob, 'D': D, 'M': M, 'n_ger': ng, 'n_init': n_init}

    # ---------- F1 ----------
    d1 = [abs(max(d['acqf_todos_restarts']) - d['acqf_escolhido']) for d in dec]
    r['F1_n'] = len(dec); r['F1_ok_bit'] = int(sum(1 for v in d1 if v == 0.0))
    r['F1_delta_max'] = float(max(d1))
    r['F1_len10'] = int(sum(1 for d in dec if len(d['acqf_todos_restarts']) == 10 and d['n_restarts'] == 10))

    # ---------- F2 ----------
    dec_by_it = {d['it']: d for d in dec}
    pos_last = pos_tot = pos_none = 0
    xmax = 0.0; n_x = 0
    for g, sub in on.groupby('geracao', sort=True):
        idx = np.where(sub['real_solution_id'].notna().values)[0]
        if len(idx) == 0:
            pos_none += 1; continue
        pos_tot += 1
        if int(idx[0]) == len(sub) - 1: pos_last += 1
        sid = int(sub['real_solution_id'].dropna().iloc[0])
        x3 = sub[xc].values[idx[0]]
        x1 = real.loc[real.solution_id == sid, xc].values[0]
        xmax = max(xmax, float(np.max(np.abs(x3 - x1)))); n_x += 1
    r['F2_pos_last'] = pos_last; r['F2_pos_tot'] = pos_tot; r['F2_sem_marca'] = pos_none
    r['F2_x_maxabs'] = xmax; r['F2_n'] = n_x

    # ---------- F3 ----------
    par_tot = 0; viol_sig = viol_id = viol_rnd = 0; ger = 0
    for g, sub in on.groupby('geracao', sort=True):
        d = dec_by_it.get(int(g))
        if d is None or len(sub) != 10: continue
        a = np.array(d['acqf_todos_restarts'], float)
        if len(a) != 10: continue
        X = sub[xc].values.astype(np.float64)
        scx = max(1.0, float(np.abs(X).max())); sca = max(1.0, float(np.abs(a).max()))
        best = int(np.argmax(a))
        sig = np.array([i for i in range(10) if i != best] + [best])
        idp = np.arange(10)
        rp = rng.permutation(10)
        ger += 1
        for i in range(10):
            for j in range(i+1, 10):
                if np.max(np.abs(X[i]-X[j])) <= 1e-6*scx:      # MESMO ótimo local
                    par_tot += 1
                    if abs(a[sig[i]]-a[sig[j]]) > 1e-6*sca: viol_sig += 1
                    if abs(a[idp[i]]-a[idp[j]]) > 1e-6*sca: viol_id += 1
                    if abs(a[rp[i]]-a[rp[j]]) > 1e-6*sca: viol_rnd += 1
    r['F3_ger'] = ger; r['F3_pares'] = par_tot
    r['F3_viol_sigma'] = viol_sig; r['F3_viol_id'] = viol_id; r['F3_viol_rnd'] = viol_rnd

    # ---------- F4 ----------
    inf = [d for d in dec if d['caminho'] == 'infill']
    ch = [d for d in inf if d.get('cache_hit')]
    nch = [d for d in inf if not d.get('cache_hit')]
    r['F4_nch'] = len(nch); r['F4_nch_ok'] = int(sum(1 for d in nch if d['fe'] == d['n_train'] + d['q']))
    r['F4_ch'] = len(ch); r['F4_ch_ok'] = int(sum(1 for d in ch if d['fe'] == d['n_train']))
    r['F4_ch_dist0'] = int(sum(1 for d in ch if d['dist_min_arquivo'] == 0.0))
    r['F4_fe_final'] = man['fe_final']
    r['F4_fe_cresc'] = int(all(np.diff([d['fe'] for d in inf]) >= 0))

    # ---------- F5 ----------
    sel = on[on.real_solution_id.notna()]
    sg = sel[[f'sigma_{j}' for j in range(M)]].values.astype(np.float64)
    mu = sel[[f'mu_{j}' for j in range(M)]].values.astype(np.float64)
    sid = sel.real_solution_id.astype(int).values
    fr = real.set_index('solution_id').loc[sid, fc].values.astype(np.float64)
    err = np.abs(mu - fr)
    r['F5_sigma_min'] = float(sg.min()); r['F5_sigma_med'] = float(np.median(sg))
    r['F5_sigma_zero'] = int((sg <= 0).sum())
    half = len(sg)//2
    r['F5_sigma_1ametade'] = float(np.median(sg[:half])); r['F5_sigma_2ametade'] = float(np.median(sg[half:]))
    r['F5_cob_infill'] = float((err <= 1.96*sg).mean())
    r['F5_err_med'] = float(np.median(err))
    r['F5_err_rel_med'] = float(np.median(err / np.maximum(np.abs(fr).mean(axis=0), 1e-12)))

    # ---------- F6 ----------
    # ②(0) = DoE inicial; ②(g) = n_train da geração g (estado NO INÍCIO da geração g)
    # ⇒ ②(0) ≡ ②(1) = n_init (o off-by-one documentado do config); ②(ng) = fe_final.
    gs = pop.groupby('geracao').size()
    esp = [n_init] + [(d.get('n_train') or man['fe_final']) for d in dec]
    esp = np.array(esp)
    r['F6_ok'] = int((gs.values == esp).sum()) if len(esp) == len(gs) else -1
    r['F6_n'] = len(gs); r['F6_esp_n'] = len(esp)
    r['F6_g0'] = int(gs.iloc[0]); r['F6_g1'] = int(gs.iloc[1]); r['F6_glast'] = int(gs.iloc[-1])
    r['F6_off1'] = bool(gs.iloc[0] == gs.iloc[1] == n_init)

    # ---------- F3b: sensibilidade da tolerância de x (só onde houve violação) ----------
    if r['F3_viol_sigma'] > 0:
        for tol in (1e-7, 1e-9, 1e-12):
            v = 0; p = 0
            for g, sub in on.groupby('geracao', sort=True):
                d = dec_by_it.get(int(g))
                if d is None or len(sub) != 10: continue
                a = np.array(d['acqf_todos_restarts'], float)
                X = sub[xc].values.astype(np.float64)
                scx = max(1.0, float(np.abs(X).max())); sca = max(1.0, float(np.abs(a).max()))
                best = int(np.argmax(a))
                sig = np.array([i for i in range(10) if i != best] + [best])
                for i in range(10):
                    for j in range(i+1, 10):
                        if np.max(np.abs(X[i]-X[j])) <= tol*scx:
                            p += 1
                            if abs(a[sig[i]]-a[sig[j]]) > 1e-6*sca: v += 1
            r[f'F3b_pares_{tol:g}'] = p; r[f'F3b_viol_{tol:g}'] = v
    else:
        for tol in (1e-7, 1e-9, 1e-12):
            r[f'F3b_pares_{tol:g}'] = -1; r[f'F3b_viol_{tol:g}'] = -1
    rows.append(r); print('[ok]', prob, flush=True)

F = pd.DataFrame(rows); F.to_csv(f'{OUT}/c262_bateriaF.csv', index=False)
pd.set_option('display.width', 300)
print('\n== F1 identidade do argmax ==')
print(F[['problema', 'F1_n', 'F1_ok_bit', 'F1_delta_max', 'F1_len10']].to_string())
print('TOTAL F1: %d/%d bit-a-bit | Δmáx global %.3g | 10 restarts em %d'
      % (F.F1_ok_bit.sum(), F.F1_n.sum(), F.F1_delta_max.max(), F.F1_len10.sum()))
print('\n== F2 elo ③→① ==')
print(F[['problema', 'F2_pos_last', 'F2_pos_tot', 'F2_sem_marca', 'F2_x_maxabs', 'F2_n']].to_string())
print('TOTAL F2: última linha %d/%d | |Δx| máx %.3g em %d infills'
      % (F.F2_pos_last.sum(), F.F2_pos_tot.sum(), F.F2_x_maxabs.max(), F.F2_n.sum()))
print('\n== F3 refinamento (σ × identidade × aleatória) ==')
print(F[['problema', 'F3_ger', 'F3_pares', 'F3_viol_sigma', 'F3_viol_id', 'F3_viol_rnd']].to_string())
tp = F.F3_pares.sum()
print('TOTAL F3: pares de x-duplicatas %d | violações σ %d (%.2f%%) | identidade %d (%.2f%%) | aleatória %d (%.2f%%)'
      % (tp, F.F3_viol_sigma.sum(), 100*F.F3_viol_sigma.sum()/max(tp, 1),
         F.F3_viol_id.sum(), 100*F.F3_viol_id.sum()/max(tp, 1),
         F.F3_viol_rnd.sum(), 100*F.F3_viol_rnd.sum()/max(tp, 1)))
print('\n== F4 aritmética do FE ==')
print(F[['problema', 'F4_nch', 'F4_nch_ok', 'F4_ch', 'F4_ch_ok', 'F4_ch_dist0', 'F4_fe_final', 'F4_fe_cresc']].to_string())
print('\n== F5 σ e erro-fantasia ==')
print(F[['problema', 'F5_sigma_min', 'F5_sigma_zero', 'F5_sigma_1ametade', 'F5_sigma_2ametade', 'F5_cob_infill', 'F5_err_med', 'F5_err_rel_med']].to_string())
print('\n== F6 ② = dataset acumulado ==')
print(F[['problema', 'F6_ok', 'F6_n', 'F6_esp_n', 'F6_g0', 'F6_g1', 'F6_glast', 'F6_off1']].to_string())
print('TOTAL F6: %d/%d blocos de ② com |②(g)| == n_train(g)' % (F.F6_ok.sum(), F.F6_n.sum()))
print('\n== F3b sensibilidade da tolerância de x ==')
print(F[[c for c in F.columns if c.startswith('F3b') or c == 'problema']].to_string())
