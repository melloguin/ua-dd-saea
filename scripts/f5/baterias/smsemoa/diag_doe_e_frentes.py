#!/usr/bin/env python
"""Diagnosticos dirigidos: (a) DoE bit-a-bit + hash; (b) dissecacao do desvio de n_front1
(hipotese float32 x float64 / empates); (c) hard_stop e geracao fantasma nas 3 celulas D=2;
(d) identidade de seeding entre os 4 pisos. Saidas em CSV."""
import json, os, glob, hashlib, pickle
import numpy as np, pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bateria_smsemoa import nd_sort, crowding, seed_pick, load_cell

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
DOE = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe'
OUT = os.path.dirname(os.path.abspath(__file__))
PROBS = sorted(os.path.basename(p) for p in glob.glob(ROOT + '/smsemoa/*') if os.path.isdir(p))


def doe_check():
    rows = []
    for p in PROBS:
        man, recs, real, pop, sur, tim = load_cell(p)
        D = 11 * 0
        dp = f'{DOE}/{p}/doe_{p}_42.parquet'
        dm = json.load(open(f'{DOE}/{p}/doe_{p}_42.manifest.json'))
        Xd = pd.read_parquet(dp)
        xcols = sorted([c for c in real.columns if c.startswith('x') and c[1:].isdigit()], key=lambda c: int(c[1:]))
        Xi = real.loc[real.fase == 'init', xcols].values
        n = len(Xd)
        d32 = np.abs(Xd.values.astype(np.float32) - Xi).max()
        d64 = np.abs(Xd.values - Xi.astype(np.float64)).max()
        # hash do artefato conforme sidecar
        h_side = dm.get('sha256') or dm.get('hash') or dm.get('doe_hash')
        h_file = hashlib.sha256(open(dp, 'rb').read()).hexdigest()
        rows.append(dict(problema=p, n_doe=n, n_init_real=len(Xi), iguais=n == len(Xi),
                         dX_max_f32=float(d32), dX_max_f64=float(d64),
                         hash_manifesto_run=man['doe_hash'], hash_sidecar=h_side,
                         hash_arquivo=h_file, hash_bate=(h_side == man['doe_hash']),
                         hash_arq_bate=(h_file == man['doe_hash']),
                         ordem_preservada=bool(np.abs(Xd.values.astype(np.float32) - Xi).max() == 0)))
    return pd.DataFrame(rows)


def frentes_diag():
    """Para cada celula: por geracao, n_front1 logado x recomputado em float32;
    conta empates exatos e quase-empates no espaco de objetivos."""
    rows = []
    for p in PROBS:
        man, recs, real, pop, sur, tim = load_cell(p)
        gens = [x for x in recs if x.get('rec') == 'smsemoa_gen']
        fcols = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))
        F32 = real[fcols].values.astype(np.float64)   # float32 promovido (sem perda)
        popmap = {int(g): np.array(v.tolist()) for g, v in pop.groupby('geracao')['solution_id']}
        for g in gens:
            ids = popmap[g['geracao']]
            Fp = F32[ids]
            fr = nd_sort(Fp)
            calc = int((fr == 1).sum())
            log = int(g['n_front1'])
            # empates: linhas duplicadas em f
            uq = len(np.unique(Fp, axis=0))
            # quase-empates: pares com dif relativa < 1e-6 em TODOS os objetivos
            nq = 0
            for i in range(len(Fp)):
                for j in range(i + 1, len(Fp)):
                    den = np.maximum(np.abs(Fp[i]), np.abs(Fp[j]))
                    den[den == 0] = 1
                    if np.all(np.abs(Fp[i] - Fp[j]) / den < 1e-6):
                        nq += 1
            rows.append(dict(problema=p, geracao=g['geracao'], n_front1_log=log,
                             n_front1_calc=calc, delta=calc - log, n_pop=g['n_pop'],
                             n_f_unicos=uq, n_quase_empates=nq))
    return pd.DataFrame(rows)


def dtlz4_zoom():
    man, recs, real, pop, sur, tim = load_cell('DTLZ4')
    fcols = ['f0', 'f1', 'f2']
    F = real[fcols].values.astype(np.float64)
    init = 131
    Fd = F[:init]
    fr = nd_sort(Fd)
    out = {}
    out['n_unicos_f'] = int(len(np.unique(Fd, axis=0)))
    out['n_f0_zero'] = int((Fd[:, 0] == 0).sum())
    out['n_f1_zero'] = int((Fd[:, 1] == 0).sum())
    out['n_f0f1_zero'] = int(((Fd[:, 0] == 0) & (Fd[:, 1] == 0)).sum())
    out['front_sizes'] = np.bincount(fr)[1:].tolist()
    out['n_frentes_calc'] = int(fr.max())
    out['n_front1_calc'] = int((fr == 1).sum())
    # min de f0/f1 nao-nulos
    out['min_f0_nonzero'] = float(Fd[Fd[:, 0] > 0, 0].min()) if (Fd[:, 0] > 0).any() else None
    out['f0_lt_1e-7'] = int((Fd[:, 0] < 1e-7).sum())
    out['f1_lt_1e-7'] = int((Fd[:, 1] < 1e-7).sum())
    return out


def hardstop_diag():
    rows = []
    for p in PROBS:
        man, recs, real, pop, sur, tim = load_cell(p)
        gens = [x for x in recs if x.get('rec') == 'smsemoa_gen']
        guards = [x for x in recs if x.get('rec') == 'guard']
        init = int(11 * (len([c for c in real.columns if c.startswith('x') and c[1:].isdigit()])) - 1)
        fe_last_gen = gens[-1]['fe']
        n_fantasma = len(real) - fe_last_gen
        ch_init = [g for g in guards if g.get('name') == 'cache_hit' and g.get('fe') == init]
        ch_evo = [g for g in guards if g.get('name') == 'cache_hit' and g.get('fe') != init]
        hs = [g for g in guards if g.get('name') == 'hard_stop']
        sids_init = [g['solution_id'] for g in ch_init]
        # qual sid repetido no seeding?
        from collections import Counter
        c = Counter(sids_init)
        rep = [k for k, v in c.items() if v > 1]
        popmap = {int(g): np.array(v.tolist()) for g, v in pop.groupby('geracao')['solution_id']}
        pos_rep = [int(np.where(popmap[1] == r)[0][0]) for r in rep] if rep else []
        rows.append(dict(problema=p, D=int(len([c2 for c2 in real.columns if c2.startswith('x') and c2[1:].isdigit()])),
                         init=init, maxfe=len(real), fe_ultima_ger=fe_last_gen,
                         linhas_fantasma=n_fantasma, n_gen_log=len(gens),
                         ch_seeding=len(ch_init), ch_evolucao=len(ch_evo), hard_stop=len(hs),
                         sid_repetido=';'.join(map(str, rep)), pos_no_pop1=';'.join(map(str, pos_rep)),
                         hs_detalhe=json.dumps(hs[0], ensure_ascii=False) if hs else ''))
    return pd.DataFrame(rows)


def pisos_seeding():
    """Identidade do seeding D88 entre os 4 pisos (mesmo DoE, mesma regra)."""
    rows = []
    for p in PROBS:
        rec = dict(problema=p)
        base = {}
        for alg in ['smsemoa', 'nsga2', 'nsga3', 'moead']:
            f = f'{ROOT}/{alg}/{p}/42/exp_main_{alg}_{p}_42__pop.parquet'
            if not os.path.exists(f):
                rec[alg] = 'AUSENTE'
                continue
            dpop = pd.read_parquet(f)
            g1 = np.sort(dpop.loc[dpop.geracao == dpop.geracao.min(), 'solution_id'].values)
            base[alg] = g1
            rec[alg + '_N'] = len(g1)
        s = base.get('smsemoa')
        for alg in ['nsga2', 'nsga3', 'moead']:
            if alg in base:
                o = base[alg]
                rec[alg + '_igual'] = bool(len(o) == len(s) and np.array_equal(o, s))
                rec[alg + '_inter'] = int(len(set(o.tolist()) & set(s.tolist())))
                rec[alg + '_prefixo'] = bool(set(o.tolist()) <= set(s.tolist())) if len(o) < len(s) else None
        rows.append(rec)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    a = doe_check(); a.to_csv(OUT + '/diag_doe.csv', index=False)
    print('== DOE ==\n', a[['problema', 'n_doe', 'dX_max_f32', 'dX_max_f64', 'hash_bate', 'hash_arq_bate', 'ordem_preservada']].to_string(index=False))
    b = frentes_diag(); b.to_csv(OUT + '/diag_frentes.csv', index=False)
    print('\n== FRENTES: geracoes com delta != 0 ==')
    print(b[b.delta != 0].to_string(index=False))
    print('total geracoes', len(b), 'divergentes', int((b.delta != 0).sum()))
    print('\n== DTLZ4 zoom ==\n', json.dumps(dtlz4_zoom(), indent=1))
    c = hardstop_diag(); c.to_csv(OUT + '/diag_hardstop.csv', index=False)
    print('\n== HARD-STOP / FANTASMA / CACHE ==\n', c.to_string(index=False))
    d = pisos_seeding(); d.to_csv(OUT + '/diag_pisos_seeding.csv', index=False)
    print('\n== SEEDING ENTRE PISOS ==\n', d.to_string(index=False))
