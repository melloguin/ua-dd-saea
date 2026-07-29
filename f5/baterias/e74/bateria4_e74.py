#!/usr/bin/env python
"""BATERIA 4 e74/CLMEA — U3/U4/U5/U7/U8 + sonda por CABECA + spreads recomputados + D74.
U4: cadencia ROUND-ROBIN k=6/3/12 (DI-19.1) por cabeca + boot em g=1
U5: join posicional sonda x gabarito (max|dX|)
U3/U7: 1 fit por bloco; fit+busca <= tempo_geracao_s (violacao so com sonda)
U8: fe_treino_max por cabeca conforme o regime declarado
spr: PNN spr=max(pdist2(x_train))/sqrt(2n) recomputado nos blocos count==0 (Parent==x_train)
     RBF-global spr=max(pdist2(Arc))/(D n)^(1/D) recomputado do ①+②
D74: Ymin/Ymax == min/max do FRONT-1 do arquivo corrente
Escreve: e74_sonda_cabecas.csv, e74_u457.csv, e74_spread.csv, e74_d74.csv
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
ART = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))


def nd_mask(F):
    n = len(F); keep = np.ones(n, bool)
    for i in range(n):
        le = (F <= F[i]).all(axis=1); lt = (F < F[i]).any(axis=1)
        if (le & lt).any():
            keep[i] = False
    return keep


u457, spread, d74rows, cab = [], [], [], []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    boot = [r for r in recs if r['rec'] == 'e74_boot'][0]
    sond = [r for r in recs if r['rec'] == 'sonda']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    tim = pd.read_parquet(base + '__timing.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]
    Xr = real[xc].to_numpy(np.float32); Fr = real[fc].to_numpy(np.float64)
    sid2row = dict(zip(real.solution_id.to_numpy(), np.arange(len(real))))
    popg = {g: d.solution_id.to_numpy() for g, d in pop.groupby('geracao')}

    # ---- U4 cadencia round-robin
    sd = man['sonda']['cabecas']
    ev_g = {(r['modelo'], r['geracao']) for r in sond}
    ger_s1 = sorted(g for (m, g) in ev_g if m == 'PNN(s1)')
    ger_s2 = sorted(g for (m, g) in ev_g if m == 'RBF-global(s2)')
    ger_s3 = sorted(g for (m, g) in ev_g if m == 'RBF-local(s3)')
    gmaxg = max(r['geracao'] for r in gens)
    # esperado: s1 em geracoes de estrategia 1 a cada 3 ciclos (k=6 -> 1 a cada 6 gens de s1?)
    g1 = sorted(r['geracao'] for r in gens if r['estrategia'] == 1)
    g2 = sorted(r['geracao'] for r in gens if r['estrategia'] == 2)
    g3 = sorted(r['geracao'] for r in gens if r['estrategia'] == 3)
    # fase deslocada (DI-19.1): s2 na 1a ocorrencia, s1 na 2a, s3 na 3a; periodo 3 ciclos
    esp1 = [g for i, g in enumerate(g1) if i % 3 == 1]
    esp2 = [g for i, g in enumerate(g2) if i % 3 == 0]
    esp3 = [g for i, g in enumerate(g3) if i % 3 == 2]
    # clausula da ULTIMA geracao (finalProbe): cobre gmaxg mesmo fora da cadencia
    todas = set(esp1) | set(esp2) | set(esp3)
    extra = sorted(set(ger_s1 + ger_s2 + ger_s3) - todas)
    ultimo_coberto = (gmaxg in set(ger_s1 + ger_s2 + ger_s3))

    # ---- U5 join posicional sonda x gabarito
    gab = pd.read_parquet(f'{ART}/sonda_{pr}.parquet')
    gxc = [c for c in gab.columns if c.startswith('x')]
    Xg = gab[gxc].to_numpy(np.float32)
    ss = sur[sur.regime == 'sonda']
    dXs = []
    for (g, mf), blk in ss.groupby(['geracao', 'modelo_flag']):
        Xb = blk[xc].to_numpy(np.float32)
        S = len(Xb)
        if S <= len(Xg):
            dXs.append(float(np.abs(Xb - Xg[:S]).max()))
    # ---- U3/U7 timing
    viol = tim[(tim.tempo_fit_s + tim.tempo_busca_s) > tim.tempo_geracao_s + 1e-9]
    ger_sonda = {r['geracao'] for r in sond}
    viol_com_sonda = int(viol.geracao.isin(ger_sonda).sum())
    # ---- U8 fe_treino_max por cabeca
    ftm = ss.groupby('modelo_flag').fe_treino_max.agg(['min', 'max', 'nunique'])
    mono = {}
    for mf, b in ss.groupby('modelo_flag'):
        v = b.groupby('geracao').fe_treino_max.first().sort_index().to_numpy()
        mono[mf] = bool((np.diff(v) >= 0).all())
    u457.append(dict(problema=pr, D=D, M=M,
                     s1_blocos=len(ger_s1), s1_esp=len(esp1), s1_ok=(ger_s1 == esp1),
                     s2_blocos=len(ger_s2), s2_esp=len(esp2), s2_ok=(ger_s2 == esp2),
                     s3_blocos=len(ger_s3), s3_esp=len(esp3), s3_ok=(ger_s3 == esp3),
                     boot_g1=(1 in [r['geracao'] for r in sond if r['modelo'] == 'RBF-global(boot)']),
                     extra_final=json.dumps(extra), ultimo_coberto=ultimo_coberto, gmaxg=gmaxg,
                     n_blocos_tot=len(sond), n_falhas=sum(0 if r['ok'] else 1 for r in sond),
                     u5_dX_max=(max(dXs) if dXs else np.nan), u5_blocos=len(dXs),
                     u7_viol=len(viol), u7_viol_com_sonda=viol_com_sonda,
                     u3_fits=len(tim), u3_esp=len(gens) + 1,
                     ftm_mono=json.dumps(mono),
                     ftm_max=int(ss.fe_treino_max.max()), fe_final=man['fe_final']))
    # ---- spreads
    # PNN: nos blocos count==0, Parent == x_train => spr = max(pdist2)/sqrt(2n)
    so = sur[sur.regime == 'online']
    blocks = {g: d for g, d in so.groupby('geracao')}
    for ev in gens:
        if ev['estrategia'] == 1 and ev['count'] == 0:
            blk = blocks.get(ev['geracao'])
            if blk is None: continue
            X = blk[xc].to_numpy(np.float64)
            dm = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
            sp = dm.max() / np.sqrt(2 * len(X))
            spread.append(dict(problema=pr, geracao=ev['geracao'], tipo='PNN',
                               spr_log=ev['spr'], spr_rec=sp, rel=abs(sp - ev['spr']) / max(ev['spr'], 1e-12)))
            if len([r for r in spread if r['problema'] == pr and r['tipo'] == 'PNN']) >= 5: break
    # RBF-global (s2): spr = max(pdist2(Arc))/(D*n)^(1/D) — amostra de 5 blocos
    cnt = 0
    for ev in gens:
        if ev['estrategia'] != 2 or cnt >= 5: continue
        sids = popg.get(ev['geracao'])
        if sids is None: continue
        X = Xr[[sid2row[s] for s in sids]].astype(np.float64)
        dm = np.sqrt(np.maximum(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1), 0))
        sp = dm.max() / (D * len(X)) ** (1.0 / D)
        spread.append(dict(problema=pr, geracao=ev['geracao'], tipo='RBF-global',
                           spr_log=ev['spr'], spr_rec=sp, rel=abs(sp - ev['spr']) / max(ev['spr'], 1e-12)))
        cnt += 1
    # ---- D74: Ymin/Ymax == min/max do FRONT-1 do arquivo
    cnt = 0
    for ev in gens:
        if ev['estrategia'] != 2 or 'Ymin' not in ev or cnt >= 8: continue
        sids = popg.get(ev['geracao'])
        if sids is None: continue
        A = Fr[[sid2row[s] for s in sids]]
        m = nd_mask(A)
        ym = A[m].min(0); yM = A[m].max(0)
        d74rows.append(dict(problema=pr, geracao=ev['geracao'],
                            dYmin=float((np.abs(ym - np.array(ev['Ymin'])) / np.maximum(np.abs(np.array(ev['Ymin'])), 1e-9)).max()),
                            dYmax=float((np.abs(yM - np.array(ev['Ymax'])) / np.maximum(np.abs(np.array(ev['Ymax'])), 1e-9)).max()),
                            n_front1=int(m.sum()), n_front1_ev=ev.get('n_front1'),
                            range0=bool(ev.get('range0'))))
        cnt += 1
    # ---- sonda por cabeca: classe do PNN
    p = ss[ss.modelo_flag == 'PNN(s1)']
    if len(p):
        h = p.groupby(['geracao', 'pred_classe']).size().unstack(fill_value=0)
        h = h.div(h.sum(1), axis=0)
        for c in h.columns:
            cab.append(dict(problema=pr, cabeca='PNN(s1)', classe=c,
                            frac_1o=float(h[c].iloc[0]), frac_ult=float(h[c].iloc[-1]),
                            frac_med=float(h[c].mean())))
    print(pr, 'ok', flush=True)

pd.DataFrame(u457).to_csv(f'{OUT}/e74_u457.csv', index=False)
pd.DataFrame(spread).to_csv(f'{OUT}/e74_spread.csv', index=False)
pd.DataFrame(d74rows).to_csv(f'{OUT}/e74_d74.csv', index=False)
pd.DataFrame(cab).to_csv(f'{OUT}/e74_pnn_sonda_classes.csv', index=False)
pd.set_option('display.width', 300)
u = pd.DataFrame(u457)
print(u.to_string())
print('\ncadencia s1/s2/s3 exata:', int(u.s1_ok.sum()), int(u.s2_ok.sum()), int(u.s3_ok.sum()), '/ 25')
print('ultima geracao coberta:', int(u.ultimo_coberto.sum()), '/25 | blocos extra (finalProbe):', u.extra_final.tolist())
print('boot em g=1:', int(u.boot_g1.sum()), '| falhas de sonda:', u.n_falhas.sum(), '| blocos total:', u.n_blocos_tot.sum())
print('U5 max|dX| global:', u.u5_dX_max.max(), '| blocos casados:', u.u5_blocos.sum())
print('U7 violacoes:', u.u7_viol.sum(), 'delas com sonda:', u.u7_viol_com_sonda.sum())
print('U3 fits==eventos+1:', int((u.u3_fits == u.u3_esp).sum()), '/25')
sp = pd.DataFrame(spread)
print('\nSPREAD recomputado: max erro relativo por tipo')
print(sp.groupby('tipo').rel.describe().to_string())
dd = pd.DataFrame(d74rows)
print('\nD74 Ymin/Ymax vs front-1 do arquivo (erro RELATIVO): mediana', dd[['dYmin','dYmax']].median().to_dict(),
      '| p95', dd[['dYmin','dYmax']].quantile(.95).to_dict(), '| max', dd[['dYmin','dYmax']].max().to_dict(), '| n', len(dd))
print(dd.groupby('problema')[['dYmin','dYmax']].max().to_string())
