#!/usr/bin/env python
"""BATERIA 9 e74/CLMEA — as identidades que a bateria 8 errou de modelo, agora GROUNDED:
 (A) f_best == min por objetivo do arquivo POS-FE (prefixo 0..arquivo-1 da ①) — todos os eventos.
 (B) n_front1 == |ND1(arquivo POS-FE)| — amostra.
 (C) A CADEIA DA s1 nos blocos NO-OP (count==0), onde a ③ contem a PROPRIA populacao P
     (100% real_solution_id): (C1) P == top-N do arquivo por NDSort+crowding sobre OBJETIVOS?
     (C2) e sobre DECISAO (hipotese do bug stock)? (C3) os rotulos pred_classe sao NAO-DECRESCENTES
     na ordem NSGA-II sobre objetivos (regra de quota 10/30/40/20 por camadas)? e sobre decisao?
 (D) n_por_nivel_pop == histograma de pred_classe do bloco da ③ (todos os eventos s1).
 (E) frac_nivel1 == fracao nivel_1 do bloco QUANDO count>0 (o bloco e' o offspring).
 (F) U11 fantasia dos infills (mu_RBF do escolhido vs f real) por celula/estrategia.
Escreve: e74_b9_identidades.csv, e74_b9_noop.csv, e74_b9_u11.csv, e74_b9.txt
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
    n = len(F); rank = np.zeros(n, int); rem = np.ones(n, bool); r = 1
    while rem.any():
        idx = np.where(rem)[0]; A = F[idx]; keep = np.ones(len(idx), bool)
        for i in range(len(idx)):
            if ((A <= A[i]).all(1) & (A < A[i]).any(1)).any():
                keep[i] = False
        if not keep.any():
            break
        rank[idx[keep]] = r; rem[idx[keep]] = False; r += 1
    return rank


def crowd(F, rank):
    cd = np.zeros(len(F))
    for r in np.unique(rank):
        idx = np.where(rank == r)[0]; A = F[idx]; c = np.zeros(len(idx))
        for j in range(A.shape[1]):
            o = np.argsort(A[:, j], kind='stable')
            c[o[0]] = np.inf; c[o[-1]] = np.inf
            rng = A[o[-1], j] - A[o[0], j]
            if rng > 0 and len(idx) > 2:
                c[o[1:-1]] += (A[o[2:], j] - A[o[:-2], j]) / rng
        cd[idx] = c
    return cd


ident, noop, u11 = [], [], []
for pr in probs:
    b = f'{ROOT}/{pr}/42/exp_main_e74_{pr}_42'
    recs = [json.loads(l) for l in open(b + '.jsonl') if l.strip()]
    hdr = [r for r in recs if r['rec'] == 'header'][0]; D, M = hdr['D'], hdr['M']
    gens = [r for r in recs if r['rec'] == 'e74_gen']
    real = pd.read_parquet(b + '__real.parquet')
    sur = pd.read_parquet(b + '__surrogate.parquet'); so = sur[sur.regime == 'online']
    fc = [f'f{i}' for i in range(M)]; xc = [f'x{i}' for i in range(D)]
    F = real[fc].to_numpy(np.float64); X = real[xc].to_numpy(np.float64)
    blocks = {g: d for g, d in so.groupby('geracao')}
    lbl2n = {f'nivel_{i}': i for i in range(1, 5)}

    # ---------- (A) f_best sobre TODOS os eventos
    fb_dif = []
    for ev in gens:
        na = ev['arquivo']
        fb_dif.append(float(np.abs(np.array(ev['f_best']) - F[:na].min(0)).max()))
    # ---------- (D)(E) identidades evento x ③
    okD = okE = nD = nE = 0
    for ev in gens:
        if ev['estrategia'] != 1:
            continue
        blk = blocks.get(ev['geracao'])
        if blk is None:
            continue
        h = blk.pred_classe.map(lbl2n).value_counts()
        vec = [int(h.get(i, 0)) for i in (1, 2, 3, 4)]
        nD += 1; okD += int(vec == list(ev['n_por_nivel_pop']))
        if ev['count'] > 0:
            nE += 1
            okE += int(abs(vec[0] / len(blk) - float(ev['frac_nivel1'])) < 1e-9)
    # ---------- (B) n_front1 (amostra 10 eventos)
    sel = gens[:: max(1, len(gens) // 10)][:10]
    nf_ok = 0
    for ev in sel:
        na = ev['arquivo']
        nf_ok += int(int((ndsort(F[:na]) == 1).sum()) == ev['n_front1'])
    ident.append(dict(problema=pr, D=D, M=M, n_ev=len(gens),
                      fbest_max=max(fb_dif), fbest_exato=int(sum(1 for x in fb_dif if x == 0.0)),
                      nf1_n=len(sel), nf1_ok=nf_ok,
                      nD=nD, okD=okD, nE=nE, okE=okE))

    # ---------- (C) cadeia da s1 nos blocos NO-OP
    for ev in [e for e in gens if e['estrategia'] == 1 and e['count'] == 0]:
        blk = blocks.get(ev['geracao'])
        if blk is None or blk.real_solution_id.isna().any():
            continue
        Pids = blk.real_solution_id.to_numpy(int)
        na = ev['arquivo'] - ev['aceito']            # arquivo que TREINOU o modelo deste slot
        N = len(blk)
        A, AX = F[:na], X[:na]
        rk = ndsort(A); cd = crowd(A, rk)
        top_obj = set(np.lexsort((-cd, rk))[:N].tolist())
        rkx = ndsort(AX); cdx = crowd(AX, rkx)
        top_dec = set(np.lexsort((-cdx, rkx))[:N].tolist())
        sP = set(Pids.tolist())
        lab = blk.pred_classe.map(lbl2n).to_numpy()
        # ordem NSGA-II RESTRITA a P
        idx = Pids
        rkP = rk[idx]; cdP = cd[idx]
        o = np.lexsort((-cdP, rkP))
        mono_obj = bool((np.diff(lab[o]) >= 0).all())
        rkPx = rkx[idx]; cdPx = cdx[idx]
        ox = np.lexsort((-cdPx, rkPx))
        mono_dec = bool((np.diff(lab[ox]) >= 0).all())
        noop.append(dict(problema=pr, geracao=ev['geracao'], N=N, arq=na,
                         inter_obj=len(sP & top_obj), inter_dec=len(sP & top_dec),
                         P_eq_obj=(sP == top_obj), P_eq_dec=(sP == top_dec),
                         mono_obj=mono_obj, mono_dec=mono_dec,
                         quota=json.dumps([int((lab == i).sum()) for i in (1, 2, 3, 4)]),
                         sig0=float(np.nanmax(np.abs(blk.sigma_0.to_numpy(float)))),
                         cand_dist=float(ev['cand_dist_dec'] or 0)))
    print(pr, 'ok', flush=True)

# ---------- (F) U11 a partir da bateria 2
J = pd.read_csv(f'{OUT}/e74_joia.csv')
A = J[(J.aceito == 1) & J.abs_err_mu.notna()].copy()
A['wape_lin'] = A.abs_err_mu / A.f_real_norm.abs().clip(lower=1e-12)
u11 = A.groupby(['problema', 'est']).agg(n=('abs_err_mu', 'size'), err_med=('abs_err_mu', 'median'),
                                         f_med=('f_real_norm', 'median'),
                                         wape_med=('wape_lin', 'median')).reset_index()
u11.to_csv(f'{OUT}/e74_b9_u11.csv', index=False)

ID = pd.DataFrame(ident); ID.to_csv(f'{OUT}/e74_b9_identidades.csv', index=False)
NO = pd.DataFrame(noop); NO.to_csv(f'{OUT}/e74_b9_noop.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

P('#'*100); P('# (A)(B)(D)(E) IDENTIDADES evento x camadas'); P('#'*100)
P(ID.to_string(index=False))
P('  (A) f_best == min por objetivo do arquivo POS-FE: exato em', int(ID.fbest_exato.sum()), '/', int(ID.n_ev.sum()),
  'eventos = %.3f%%' % (100 * ID.fbest_exato.sum() / ID.n_ev.sum()), '| max|dif| global =', ID.fbest_max.max())
P('  (B) n_front1 == |ND1(arquivo POS-FE)|:', int(ID.nf1_ok.sum()), '/', int(ID.nf1_n.sum()))
P('  (D) n_por_nivel_pop == histograma pred_classe do bloco:', int(ID.okD.sum()), '/', int(ID.nD.sum()),
  '= %.3f%%' % (100 * ID.okD.sum() / ID.nD.sum()))
P('  (E) frac_nivel1 == fracao nivel_1 do bloco (so count>0):', int(ID.okE.sum()), '/', int(ID.nE.sum()),
  '= %.3f%%' % (100 * ID.okE.sum() / max(ID.nE.sum(), 1)))

P(''); P('#'*100); P('# (C) CADEIA DA s1 nos blocos NO-OP — espaco do NDSort (D30) e regra de quota'); P('#'*100)
P('  blocos no-op analisados:', len(NO), 'em', NO.problema.nunique(), 'celulas')
P('  P == top-N do arquivo por NDSort+crowding sobre OBJETIVOS:', int(NO.P_eq_obj.sum()), '/', len(NO),
  '= %.2f%%' % (100 * NO.P_eq_obj.mean()))
P('  P == top-N por NDSort+crowding sobre DECISAO (bug stock):', int(NO.P_eq_dec.sum()), '/', len(NO),
  '= %.2f%%' % (100 * NO.P_eq_dec.mean()))
P('  intersecao media |P ∩ top-N|: objetivos %.2f de %.1f  |  decisao %.2f' % (
    NO.inter_obj.mean(), NO.N.mean(), NO.inter_dec.mean()))
P('  rotulos NAO-DECRESCENTES na ordem NSGA-II sobre OBJETIVOS:', int(NO.mono_obj.sum()), '/', len(NO),
  '= %.2f%%' % (100 * NO.mono_obj.mean()))
P('  rotulos NAO-DECRESCENTES na ordem NSGA-II sobre DECISAO  :', int(NO.mono_dec.sum()), '/', len(NO),
  '= %.2f%%' % (100 * NO.mono_dec.mean()))
P('  sigma_0 identicamente 0 nos blocos no-op: max|sigma_0| =', NO.sig0.max(),
  '| cand_dist_dec max =', NO.cand_dist.max())
P('  vetor de quotas observado (top-6):', NO.quota.value_counts().head(6).to_dict())
P(NO.groupby('problema').agg(n=('P_eq_obj', 'size'), Pobj=('P_eq_obj', 'sum'), Pdec=('P_eq_dec', 'sum'),
                             mono_obj=('mono_obj', 'sum'), mono_dec=('mono_dec', 'sum'),
                             inter_obj=('inter_obj', 'mean'), inter_dec=('inter_dec', 'mean')).round(2).to_string())

P(''); P('#'*100); P('# (F) U11 — FANTASIA dos infills (|mu_RBF - f real| do escolhido)'); P('#'*100)
P(u11.pivot(index='problema', columns='est', values='wape_med').round(3).to_string())
P('  mediana global do erro relativo por estrategia:')
P(u11.groupby('est').agg(n=('n', 'sum'), wape_med=('wape_med', 'median'), err_med=('err_med', 'median')).round(4).to_string())

open(f'{OUT}/e74_b9.txt', 'w').write('\n'.join(buf))
print('\n[ok] e74_b9_*.csv + e74_b9.txt')
