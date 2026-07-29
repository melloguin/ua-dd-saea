#!/usr/bin/env python
"""BATERIA 8 e74/CLMEA — checagens NOVAS da F5.3b (o que faltava as baterias 1-6):
 (A) IDENTIDADE ndsort-obj + quotas: reconstroi P = top-N do arquivo por NDSort+crowding
     sobre OBJETIVOS e o vetor de classes por camadas ND com quotas 10/30/40/20
     -> compara com n_por_nivel_pop do evento. Contrasta com a hipotese DECISAO (bug stock).
 (B) frac_nivel1 do evento == fracao de pred_classe=='nivel_1' no bloco da (3).
 (C) f_best == min por objetivo do arquivo; n_front1 == |ND1(arquivo)|.
 (D) reparticao REAL do orcamento por estrategia (FE share) por celula.
 (E) cadencia round-robin medida no INDICE DE SLOT de cada cabeca (deltas).
 (F) os 10 blocos range0 (front degenerado) dissecados.
 (G) U11 fantasia dos infills + s3 outlier de telemetria.
 (H) dedup: cand_dist_dec nos slots perdidos; sigma/cobertura da sonda (todas NaN?).
Escreve: e74_b8_ndsort.csv, e74_b8_share.csv, e74_b8_cadencia_slot.csv, e74_b8_range0.csv,
         e74_b8_misc.txt
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))
buf = []


def P(*a):
    s = ' '.join(str(x) for x in a); buf.append(s); print(s, flush=True)


def ndsort(F):
    """rank de nao-dominancia completo (1-based), minimizacao."""
    n = len(F); rank = np.zeros(n, int); remaining = np.ones(n, bool); r = 1
    while remaining.any():
        idx = np.where(remaining)[0]
        A = F[idx]
        keep = np.ones(len(idx), bool)
        for i in range(len(idx)):
            le = (A <= A[i]).all(axis=1); lt = (A < A[i]).any(axis=1)
            if (le & lt).any():
                keep[i] = False
        rank[idx[keep]] = r; remaining[idx[keep]] = False; r += 1
    return rank


def crowding(F, rank):
    cd = np.zeros(len(F))
    for r in np.unique(rank):
        idx = np.where(rank == r)[0]
        A = F[idx]
        c = np.zeros(len(idx))
        for j in range(A.shape[1]):
            o = np.argsort(A[:, j], kind='stable')
            c[o[0]] = np.inf; c[o[-1]] = np.inf
            rng = A[o[-1], j] - A[o[0], j]
            if rng > 0 and len(idx) > 2:
                c[o[1:-1]] += (A[o[2:], j] - A[o[:-2], j]) / rng
        cd[idx] = c
    return cd


def classes_por_camada(rank_P, quotas=(.1, .3, .4, .2)):
    """rotula por CAMADAS ND acumuladas ate a quota (nao parte camada)."""
    n = len(rank_P)
    lim = np.cumsum(np.array(quotas) * n)
    lab = np.zeros(n, int); acc = 0; cls = 0
    for r in np.unique(rank_P):
        idx = np.where(rank_P == r)[0]
        lab[idx] = cls + 1
        acc += len(idx)
        while cls < 3 and acc >= lim[cls]:
            cls += 1
    return np.bincount(lab, minlength=5)[1:5]


nd_rows, share_rows, cad_rows, r0_rows = [], [], [], []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    sond = [r for r in recs if r['rec'] == 'sonda']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet')
    so = sur[sur.regime == 'online']
    ss = sur[sur.regime == 'sonda']
    fc = [f'f{i}' for i in range(M)]; xc = [f'x{i}' for i in range(D)]
    Fr = real[fc].to_numpy(np.float64); Xr = real[xc].to_numpy(np.float64)
    sid2row = dict(zip(real.solution_id.to_numpy(), np.arange(len(real))))
    popg = {g: d.solution_id.to_numpy() for g, d in pop.groupby('geracao')}
    blocks = {g: d for g, d in so.groupby('geracao')}

    # ---------- (D) share do orcamento
    g = pd.DataFrame(gens)
    ac = g.groupby('estrategia').aceito.sum()
    tot = int(g.aceito.sum())
    share_rows.append(dict(problema=pr, D=D, M=M, fe_infill=tot,
                           s1=int(ac.get(1, 0)), s2=int(ac.get(2, 0)), s3=int(ac.get(3, 0)),
                           sh1=100 * ac.get(1, 0) / tot, sh2=100 * ac.get(2, 0) / tot,
                           sh3=100 * ac.get(3, 0) / tot,
                           desvio_max_pp=max(abs(100 * ac.get(e, 0) / tot - 100 / 3) for e in (1, 2, 3))))

    # ---------- (E) cadencia por indice de slot da cabeca
    for est, mod, k in [(1, 'PNN(s1)', 6), (2, 'RBF-global(s2)', 3), (3, 'RBF-local(s3)', 12)]:
        gl = sorted(r['geracao'] for r in gens if r['estrategia'] == est)
        pos = {gg: i for i, gg in enumerate(gl)}
        obs = sorted({r['geracao'] for r in sond if r['modelo'] == mod})
        idx = [pos[o] for o in obs if o in pos]
        d = np.diff(idx) if len(idx) > 1 else np.array([])
        cad_rows.append(dict(problema=pr, est=est, cabeca=mod, k_declarado=k, n_blocos=len(obs),
                             n_slots=len(gl), idx0=(idx[0] if idx else None),
                             deltas=json.dumps(pd.Series(d).value_counts().to_dict()),
                             delta3=int((d == 3).sum()), delta_outro=int((d != 3).sum()),
                             ultimo_slot_coberto=(len(gl) - 1 in idx),
                             ultima_ger_run=(max(pos) if pos else None)))

    # ---------- (F) range0
    for ev in gens:
        if ev.get('range0') is True:
            blk = blocks.get(ev['geracao'])
            r0_rows.append(dict(problema=pr, geracao=ev['geracao'], n_front=ev.get('n_front'),
                                n_front1=ev.get('n_front1'), Ymin=json.dumps(ev.get('Ymin')),
                                Ymax=json.dumps(ev.get('Ymax')), hv_base=ev.get('hv_base'),
                                hv_gain=ev.get('hv_gain'), aceito=ev['aceito'],
                                sig_todos_nan=(bool(blk.sigma_0.isna().all()) if blk is not None else None),
                                mu_ok=(int(blk.mu_0.notna().sum()) if blk is not None else None)))

    # ---------- (A)(B)(C) identidade ndsort-obj/quotas/f_best/n_front1
    ev1 = [e for e in gens if e['estrategia'] == 1]
    sel = ev1[:: max(1, len(ev1) // 12)][:12]
    for ev in sel:
        gg = ev['geracao']
        sids = popg.get(gg)
        blk = blocks.get(gg)
        if sids is None or blk is None:
            continue
        rows = np.array([sid2row[s] for s in sids])
        A = Fr[rows]; AX = Xr[rows]
        N = len(blk)
        # ---- C: n_front1 e f_best sobre o ARQUIVO
        rk = ndsort(A)
        n_f1 = int((rk == 1).sum())
        fb = A.min(0)
        # ---- P = top-N por NDSort + crowding (OBJETIVOS)
        cd = crowding(A, rk)
        order = np.lexsort((-cd, rk))
        Pidx = order[:N]
        rkP = ndsort(A[Pidx])
        cls_obj = classes_por_camada(rkP)
        # ---- hipotese STOCK (bug): NDSort sobre DECISAO
        rkX = ndsort(AX[Pidx])
        cls_dec = classes_por_camada(rkX)
        obs = np.array(ev['n_por_nivel_pop'], int)
        # ---- B: frac_nivel1 vs pred_classe do bloco
        cls_blk = blk.pred_classe.astype(str)
        frac_blk = float((cls_blk == 'nivel_1').mean())
        nd_rows.append(dict(problema=pr, D=D, M=M, geracao=gg, N=N, arq=len(A),
                            n_front1_ev=ev.get('n_front1'), n_front1_rec=n_f1,
                            nf1_ok=(ev.get('n_front1') == n_f1),
                            fbest_dif=float(np.abs(np.array(ev['f_best']) - fb).max()),
                            obs=json.dumps(obs.tolist()), obj=json.dumps(cls_obj.tolist()),
                            dec=json.dumps(cls_dec.tolist()),
                            ok_obj=bool((cls_obj == obs).all()), ok_dec=bool((cls_dec == obs).all()),
                            ok_obj_n1=bool(cls_obj[0] == obs[0]), ok_dec_n1=bool(cls_dec[0] == obs[0]),
                            frac_n1_ev=float(ev['frac_nivel1']), frac_n1_blk=frac_blk,
                            frac_ok=(abs(float(ev['frac_nivel1']) - frac_blk) < 1e-9)))
    print(pr, 'ok', flush=True)

ND = pd.DataFrame(nd_rows); ND.to_csv(f'{OUT}/e74_b8_ndsort.csv', index=False)
SH = pd.DataFrame(share_rows); SH.to_csv(f'{OUT}/e74_b8_share.csv', index=False)
CD = pd.DataFrame(cad_rows); CD.to_csv(f'{OUT}/e74_b8_cadencia_slot.csv', index=False)
R0 = pd.DataFrame(r0_rows); R0.to_csv(f'{OUT}/e74_b8_range0.csv', index=False)
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 40)

P('#'*100); P('# (A) IDENTIDADE ndsort-obj + quotas 10/30/40/20 (amostra por celula)'); P('#'*100)
P('  eventos testados:', len(ND), 'em', ND.problema.nunique(), 'celulas')
P('  n_por_nivel_pop == classes por camadas ND sobre OBJETIVOS :', int(ND.ok_obj.sum()), '/', len(ND),
  '= %.2f%%' % (100 * ND.ok_obj.mean()))
P('  n_por_nivel_pop == classes por camadas ND sobre DECISAO   :', int(ND.ok_dec.sum()), '/', len(ND),
  '= %.2f%%' % (100 * ND.ok_dec.mean()))
P('  (so a 1a classe) OBJETIVOS:', int(ND.ok_obj_n1.sum()), '| DECISAO:', int(ND.ok_dec_n1.sum()))
P(ND.groupby('problema').agg(n=('ok_obj', 'size'), obj=('ok_obj', 'sum'), dec=('ok_dec', 'sum'),
                             obj_n1=('ok_obj_n1', 'sum'), dec_n1=('ok_dec_n1', 'sum')).to_string())
P('  exemplos (obs | obj | dec):')
P(ND[['problema', 'geracao', 'N', 'obs', 'obj', 'dec', 'ok_obj', 'ok_dec']].head(20).to_string(index=False))

P(''); P('#'*100); P('# (B)(C) frac_nivel1 / n_front1 / f_best'); P('#'*100)
P('  frac_nivel1(evento) == fracao pred_classe==nivel_1 no bloco:', int(ND.frac_ok.sum()), '/', len(ND))
P('  |dif| max:', float((ND.frac_n1_ev - ND.frac_n1_blk).abs().max()))
P('  n_front1(evento) == |ND1(arquivo)| recomputado:', int(ND.nf1_ok.sum()), '/', len(ND),
  '= %.2f%%' % (100 * ND.nf1_ok.mean()))
P('  f_best == min por objetivo do arquivo: max|dif| =', float(ND.fbest_dif.max()),
  '| exato (<1e-12):', int((ND.fbest_dif < 1e-12).sum()), '/', len(ND))

P(''); P('#'*100); P('# (D) REPARTICAO REAL DO ORCAMENTO POR ESTRATEGIA'); P('#'*100)
P(SH.round(2).to_string(index=False))
P('  GLOBAL: s1 %d (%.2f%%)  s2 %d (%.2f%%)  s3 %d (%.2f%%)  de %d infills' % (
    SH.s1.sum(), 100 * SH.s1.sum() / SH.fe_infill.sum(), SH.s2.sum(), 100 * SH.s2.sum() / SH.fe_infill.sum(),
    SH.s3.sum(), 100 * SH.s3.sum() / SH.fe_infill.sum(), SH.fe_infill.sum()))
P('  celulas com desvio >5 pp do 1/3:', int((SH.desvio_max_pp > 5).sum()), '| >10 pp:', int((SH.desvio_max_pp > 10).sum()))
P('  pior celula:', SH.loc[SH.desvio_max_pp.idxmax(), ['problema', 'sh1', 'sh2', 'sh3']].to_dict())

P(''); P('#'*100); P('# (E) CADENCIA por INDICE DE SLOT da cabeca'); P('#'*100)
P(CD[['problema', 'cabeca', 'k_declarado', 'n_slots', 'n_blocos', 'idx0', 'delta3', 'delta_outro',
      'ultimo_slot_coberto', 'deltas']].to_string(index=False))
P('  delta==3 (1 sonda a cada 3 ciclos) em', int(CD.delta3.sum()), 'de', int(CD.delta3.sum() + CD.delta_outro.sum()),
  'transicoes = %.2f%%' % (100 * CD.delta3.sum() / (CD.delta3.sum() + CD.delta_outro.sum())))
P('  fase inicial (idx0) por cabeca:', CD.groupby('cabeca').idx0.agg(lambda s: sorted(set(s))).to_dict())
P('  ultimo slot da cabeca coberto:', int(CD.ultimo_slot_coberto.sum()), '/', len(CD))

P(''); P('#'*100); P('# (F) BLOCOS range0 (front degenerado — hazard CalHV do bundle)'); P('#'*100)
P(R0.to_string(index=False) if len(R0) else '  (nenhum)')

open(f'{OUT}/e74_b8_misc.txt', 'w').write('\n'.join(buf))
print('\n[ok] e74_b8_*.csv + e74_b8_misc.txt')
