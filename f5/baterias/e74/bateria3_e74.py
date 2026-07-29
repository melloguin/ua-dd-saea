#!/usr/bin/env python
"""BATERIA 3 e74/CLMEA — MECANISMO da s1 (DI-07b) + s2 range0 + s3 identidade FORTE.
s1: testa a predicao falsificavel do bug de indexacao ClassifierSelect:48
    x_candidate = Parent(index(1)), index(1) in {1..|S|}, S={y_label==1}
    => (a) pos <= round(frac_nivel1*N)  (b) is_argmax <=> frac_nivel1==1
    + footprint de linhas-arquivo do Parent via real_solution_id (nao-nulo)
s3: reconstroi o front do NDSort([y_train; mu_off]) a partir de ①+② e testa
    chosen == argmax(Eucli | front)
Escreve: e74_s1_mecanismo.csv, e74_s3_forte.csv, e74_s2_range0.csv
"""
import json, os
import pandas as pd, numpy as np

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e74'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/e74'
probs = sorted(os.listdir(ROOT))


def nd_mask(F):
    """mascara de nao-dominados (minimizacao) — rank 1 do NDSort."""
    n = len(F)
    keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        le = (F <= F[i]).all(axis=1)
        lt = (F < F[i]).any(axis=1)
        dom = le & lt
        if dom.any():
            keep[i] = False
    return keep


def crowding(F):
    n, m = F.shape
    cd = np.zeros(n)
    for j in range(m):
        o = np.argsort(F[:, j], kind='stable')
        f = F[o, j]
        cd[o[0]] = np.inf; cd[o[-1]] = np.inf
        rng = f[-1] - f[0]
        if rng <= 0:
            continue
        cd[o[1:-1]] += (f[2:] - f[:-2]) / rng
    return cd


s1rows, s3rows, s2rows = [], [], []
for pr in probs:
    base = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]
    D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    sur = pd.read_parquet(base + '__surrogate.parquet'); sur = sur[sur.regime == 'online']
    xc = [f'x{i}' for i in range(D)]; fc = [f'f{i}' for i in range(M)]
    Xr = real[xc].to_numpy(np.float32); Fr = real[fc].to_numpy(np.float64)
    sid2row = dict(zip(real.solution_id.to_numpy(), np.arange(len(real))))
    blocks = {g: d for g, d in sur.groupby('geracao')}
    popg = {g: d.solution_id.to_numpy() for g, d in pop.groupby('geracao')}

    for ev in gens:
        g = ev['geracao']; est = ev['estrategia']
        blk = blocks.get(g)
        if blk is None or len(blk) == 0:
            continue
        Xb = blk[xc].to_numpy(np.float32)
        s0 = blk['sigma_0'].to_numpy(np.float64)
        N = len(blk)
        pos = np.nan
        if ev['aceito'] == 1:
            xi = Xr[ev['fe'] - 1]
            pos = int(np.argmin(np.abs(Xb - xi).max(axis=1)))
        if est == 1:
            K = int(round(float(ev['frac_nivel1']) * N))
            n_arq = int(blk.real_solution_id.notna().sum())
            cls = blk.pred_classe.to_numpy()
            s1rows.append(dict(problema=pr, D=D, M=M, geracao=g, N=N, K=K,
                               frac_n1=float(ev['frac_nivel1']), count=int(ev['count']),
                               desal=int(ev['n_desalinhado']), desal_frac=ev['n_desalinhado'] / N,
                               aceito=ev['aceito'], slot=ev['slot_perdido'],
                               flag_copia=bool(ev['flag_copia']),
                               cand_dist=float(ev['cand_dist_dec'] or 0),
                               pos=pos, pos_le_K=(pos <= K - 1) if pos == pos else None,
                               argmax=int(np.nanargmax(s0)),
                               is_argmax=(pos == int(np.nanargmax(s0))) if pos == pos else None,
                               n_linhas_arquivo=n_arq, frac_linhas_arquivo=n_arq / N,
                               n_nivel1_resim=int((cls == 'nivel_1').sum()),
                               sig_max=float(np.nanmax(s0)), sig_med=float(np.nanmedian(s0)),
                               quotas=json.dumps(ev.get('n_por_nivel_pop'))))
        elif est == 2:
            nval = int(np.isfinite(s0).sum())
            s2rows.append(dict(problema=pr, geracao=g, aceito=ev['aceito'],
                               range0=bool(ev.get('range0', False)),
                               n_front_ev=ev.get('n_front'), n_sigma_val=nval,
                               hv_base=ev.get('hv_base'), hv_gain=ev.get('hv_gain'),
                               score_best=(ev.get('score') or {}).get('max'),
                               pos=pos, is_argmax=(pos == int(np.nanargmax(s0))) if (pos == pos and nval) else None,
                               # identidade sigma_0 == pred_score - hv_base
                               dif_sig_score=(float(np.nanmax(np.abs(
                                   blk.pred_score.to_numpy(np.float64) - s0 - (ev.get('hv_base') or 0))))
                                   if nval else np.nan)))
        else:
            if ev['aceito'] != 1:
                continue
            sids = popg.get(g)
            if sids is None:
                continue
            idx = np.array([sid2row[s] for s in sids])
            A = Fr[idx]
            ndm = nd_mask(A)
            PF = A[ndm]
            cd = crowding(PF)
            cd[np.isinf(cd)] = 0.0
            order = np.argsort(-cd, kind='stable')
            RefObj = PF[order[0]]
            dist = np.linalg.norm(A - RefObj, axis=1)
            near = np.argsort(dist, kind='stable')[:N]
            ytr = A[near]
            mu = blk[[f'mu_{j}' for j in range(M)]].to_numpy(np.float64)
            U = np.vstack([ytr, mu])
            keep = nd_mask(U)[len(ytr):]
            nf = int(keep.sum())
            ok = False; sel = -1
            if nf > 0:
                ss = np.where(keep, s0, -np.inf)
                sel = int(np.argmax(ss))
                ok = (sel == pos)
            s3rows.append(dict(problema=pr, geracao=g, N=N, n_front_ev=ev.get('n_front'),
                               n_front_rec=nf, pos=pos, sel_rec=sel, ok_forte=ok,
                               in_front=bool(keep[pos]) if nf > 0 else None,
                               cand_eucli=ev.get('cand_eucli'), sig_pos=float(s0[pos]),
                               k_local=ev.get('k_local_efetivo')))
    print(pr, 'ok', flush=True)

d1 = pd.DataFrame(s1rows); d1.to_csv(f'{OUT}/e74_s1_mecanismo.csv', index=False)
d2 = pd.DataFrame(s2rows); d2.to_csv(f'{OUT}/e74_s2_range0.csv', index=False)
d3 = pd.DataFrame(s3rows); d3.to_csv(f'{OUT}/e74_s3_forte.csv', index=False)

print('\n########## s1 — MECANISMO (ClassifierSelect:39/46/48) ##########')
a = d1[d1.aceito == 1]
print('blocos s1:', len(d1), '| com infill aceito:', len(a))
print('PREDICAO (a) pos <= K-1 :', int(a.pos_le_K.sum()), '/', len(a),
      f'= {100*a.pos_le_K.mean():.2f}%')
print('PREDICAO (b) is_argmax <=> frac_n1==1 :')
print(pd.crosstab(a.frac_n1 == 1.0, a.is_argmax))
print('\ncount==0  <=>  slot_perdido :')
print(pd.crosstab(d1['count'] == 0, d1.slot == 1))
print('\ncount==0 -> frac linhas do Parent que sao PONTOS DO ARQUIVO:')
print(d1.groupby(d1['count'] == 0).frac_linhas_arquivo.describe().to_string())
print('\ncount==0 -> flag_copia / cand_dist==0:')
print(pd.crosstab(d1['count'] == 0, d1.flag_copia))
print('\n--- DESALINHAMENTO por problema (n_desalinhado / N) ---')
t = d1.groupby('problema').agg(ciclos=('desal', 'size'), N=('N', 'median'),
                               media=('desal', 'mean'), frac_media=('desal_frac', 'mean'),
                               mediana=('desal', 'median'), p90=('desal', lambda s: s.quantile(.9)),
                               maxi=('desal', 'max'), zero=('desal', lambda s: int((s == 0).sum())),
                               slots=('slot', 'sum'), count0=('count', lambda s: int((s == 0).sum())),
                               argmax_pct=('is_argmax', lambda s: 100 * np.nanmean(s.astype(float))))
print(t.round(3).to_string())
print('\nGLOBAL: ciclos s1 =', len(d1), '| desal medio =', round(d1.desal.mean(), 2),
      '| frac media =', round(d1.desal_frac.mean(), 4),
      '| max =', d1.desal.max(), '| slots perdidos =', int(d1.slot.sum()),
      '| count==0 =', int((d1['count'] == 0).sum()))

print('\n########## s2 — range0 / D74 ##########')
print('blocos:', len(d2), 'range0:', int(d2.range0.sum()), 'sem sigma valido:', int((d2.n_sigma_val == 0).sum()))
print(pd.crosstab(d2.range0, d2.n_sigma_val == 0))
print('range0 por problema:', d2[d2.range0].problema.value_counts().to_dict())
print('identidade sigma_0 == pred_score - hv_base: max |dif| =', np.nanmax(d2.dif_sig_score.values))
aa = d2[(d2.aceito == 1) & (d2.n_sigma_val > 0)]
print('argmax (blocos com front valido):', int(aa.is_argmax.sum()), '/', len(aa))

print('\n########## s3 — IDENTIDADE FORTE (front reconstruido) ##########')
print('blocos testados:', len(d3), '| ok_forte:', int(d3.ok_forte.sum()),
      f'= {100*d3.ok_forte.mean():.2f}%', '| chosen dentro do front:', int(d3.in_front.sum(skipna=True)))
print('n_front evento vs reconstruido: iguais em', int((d3.n_front_ev == d3.n_front_rec).sum()), '/', len(d3))
print(d3.groupby('problema').agg(n=('ok_forte', 'size'), ok=('ok_forte', 'sum'),
                                 infront=('in_front', 'sum'),
                                 nf_ev=('n_front_ev', 'median'), nf_rec=('n_front_rec', 'median')).to_string())
