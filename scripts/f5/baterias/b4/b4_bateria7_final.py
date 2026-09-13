#!/usr/bin/env python
"""B4 - Bateria 7: join float32 bit-a-bit, L_sel x ③, lote/div, header-echo,
DTLZ2_d15 (ancora J), fronteira final ZDT1, AUC x prior, dist_min_arquivo.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = REPO + '/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])
pd.set_option('display.width', 260)

# ---------- join float32 bit-a-bit + L_sel + dist_min ----------
rows = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    art = pd.read_parquet(f'{REPO}/data/sonda/sonda_{prob}.parquet')
    axc = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
    Xa32 = art[axc].to_numpy(np.float32)[:2000]
    sur = pd.read_parquet(base + '__surrogate.parquet',
                          columns=['regime', 'geracao', 'pred_confianca'] + axc)
    sd = sur[sur.regime == 'sonda']
    dmax = 0.0; nb = 0; nb0 = 0
    for gg, b in sd.groupby('geracao'):
        d = float(np.abs(b[axc].to_numpy(np.float32) - Xa32).max()); nb += 1
        dmax = max(dmax, d); nb0 += (d == 0.0)
    on = sur[sur.regime == 'online']
    # L_sel do ⑥ == max(L) dos escolhidos na ③ ? (b4_gen loga 1 valor: o do escolhido/1o)
    grp = {int(k): v['pred_confianca'].to_numpy(np.float64) for k, v in on.groupby('geracao')}
    n_ls = 0; ok_set = 0; ok_len = 0; tipos = set()
    for r in gens:
        if r.get('lote', 0) <= 0:
            continue
        v = r.get('L_sel'); n_ls += 1
        tipos.add(type(v).__name__)
        vv = np.atleast_1d(np.array(v, dtype=np.float64))
        arr = grp.get(int(r['geracao']), np.array([]))
        ok_len += (len(vv) == len(arr))
        if len(vv) == len(arr) and len(arr):
            ok_set += bool(np.allclose(np.sort(vv), np.sort(arr), rtol=1e-6, atol=1e-9))
    rows.append(dict(problema=prob, blocos=nb, dmax_f32=dmax, blocos_iguais=nb0,
                     n_lsel=n_ls, lsel_len_ok=ok_len, lsel_set_ok=ok_set, lsel_tipos=str(sorted(tipos))))
    print('ok', prob, dmax)
J = pd.DataFrame(rows)
J.to_csv(f'{OUT}/b4_join_f32.csv', index=False)
print('\n=== U5 JOIN POSICIONAL (cast float32) ===')
print(J.to_string())
print('blocos totais', J.blocos.sum(), ' bit-a-bit iguais', J.blocos_iguais.sum(), ' max|dX|', J.dmax_f32.max())
print('L_sel: tamanho == lote em', J.lsel_len_ok.sum(), '/', J.n_lsel.sum(),
      ' | conjunto identico ao da ③ em', J.lsel_set_ok.sum(), '/', J.n_lsel.sum(), '| tipos', set(J.lsel_tipos))

# ---------- header/params echo ----------
print('\n=== ECHO DE PARAMETROS (declarativo) ===')
ech = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    hdr = [json.loads(l) for l in open(base + '.jsonl') if '"header"' in l][0]
    p = man['params']
    ech.append(dict(problema=prob, N=hdr['N'], K=hdr['K_refs'], gmax=hdr['gmax'],
                    op=hdr['operadores'], treino=hdr['treino'], env=hdr['exec_env'],
                    rede=p['rede'], treinador=p['treinador'][:40], gate=p['gate'],
                    sigma_keys=tuple(sorted(man['sigma_dict'].keys())),
                    params_keys=tuple(sorted(p.keys()))))
E = pd.DataFrame(ech)
for c in ['N', 'K', 'gmax', 'op', 'treino', 'env', 'rede', 'treinador', 'gate', 'sigma_keys', 'params_keys']:
    u = E[c].astype(str).unique()
    print(f'  {c:12s}: {len(u)} valor(es) distintos em 25 celulas -> {u[0][:150]}')

# ---------- lote / div=3 / cap de orcamento ----------
G = pd.read_pickle(f'{OUT}/b4_geracoes_enriq.pkl')
print('\n=== LOTE (ramo 1) ===')
r1 = G[G.ramo == 1]
print(r1.lote.value_counts().sort_index().to_string())
print('lote>0 mediana', r1[r1.lote > 0].lote.median(), ' max', r1.lote.max())
print('saldo de orcamento na ultima geracao de cada celula:')
last = G.sort_values(['problema', 'geracao']).groupby('problema').tail(1)
print(last[['problema', 'geracao', 'fe', 'arquivo', 'lote', 'ramo']].to_string())

# ---------- ancora J: DTLZ2_d15 ----------
M = pd.read_csv(f'{REPO}/f5/metricas_finais_f52c.csv')
print('\n=== DTLZ2_d15 (ancora J) ===')
print(M[M.problema == 'DTLZ2_d15'].to_string())
print('\n=== IGD (nao-normalizado?) das celulas DTLZ do b4 ===')
print(M[(M.alg == 'b4') & (M.problema.str.startswith('DTLZ'))][['problema', 'igd_plus', 'igd', 'hv', 'n_nd']].to_string())

# ---------- ordem intra-familia DTLZ: nosso x paper ----------
paper = {'DTLZ1': 4.36e+1, 'DTLZ2': 1.89e-1, 'DTLZ3': 1.09e+2, 'DTLZ4': 3.89e-1, 'DTLZ7': 1.39e+0}
nos = M[(M.alg == 'b4') & (M.problema.isin(paper))].set_index('problema').igd_plus
cmp = pd.DataFrame({'paper_IGD_d10_M3_300FE': pd.Series(paper), 'nosso_IGDplus': nos})
cmp['rank_paper'] = cmp.paper_IGD_d10_M3_300FE.rank()
cmp['rank_nosso'] = cmp.nosso_IGDplus.rank()
print('\n=== ORDEM INTRA-FAMILIA DTLZ ===')
print(cmp.to_string())
print('posicoes coincidentes:', int((cmp.rank_paper == cmp.rank_nosso).sum()), '/', len(cmp))
cmp.to_csv(f'{OUT}/b4_canonica_dtlz.csv')

# ---------- fronteira final ZDT1 (D=30, 929 FE ~ paper 900 FE d=30) ----------
real = pd.read_parquet(f'{ROOT}/ZDT1/42/exp_main_b4_ZDT1_42__real.parquet')
F = real[['f0', 'f1']].to_numpy(float)
nd = np.ones(len(F), bool)
for i in range(len(F)):
    if nd[i]:
        dom = ((F <= F[i]).all(1) & (F < F[i]).any(1))
        if dom.any():
            nd[i] = False
print('\n=== ZDT1 D=30 (nosso 929 FE x paper 900 FE) ===')
print('|ND| final:', int(nd.sum()), ' f1 range', np.round(F[nd, 0].min(), 4), np.round(F[nd, 0].max(), 4),
      ' f2 min', np.round(F[nd, 1].min(), 4), ' f2 no f1~0', np.round(F[nd][F[nd, 0].argmin(), 1], 4))
