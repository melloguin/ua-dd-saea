#!/usr/bin/env python
"""Parte 2 da bateria T11 do `moead`.

(1) M15 com tolerancia FLOAT32 correta (regra 11 do CONTRATO).
(2) M6 clonagem: previsao POR GERACAO agregada (estimador melhor que a mediana).
(3) M16 / n_front1: o bracket [ND_f32 corrigido, ND_certo] do veredito F5.4.
(4) A formula `geracoes_derivadas` da T11 nos 4 PISOS (checagem do "103/112").
READ-ONLY.
"""
import json, os, math, glob
import numpy as np
import pandas as pd

RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/moead'
EPS32 = np.finfo(np.float32).eps


def le(alg, prob):
    base = f'{RES}/{alg}/{prob}/42/exp_main_{alg}_{prob}_42'
    man = json.load(open(base + '.manifest.json'))
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    return man, recs, real, pop


def nd_f32(O):
    """ND padrao (dominancia fraca) sobre a matriz float32."""
    n = len(O)
    dom = np.zeros(n, bool)
    for i in range(n):
        le_ = np.all(O <= O[i], axis=1)
        lt_ = np.any(O < O[i], axis=1)
        if np.any(le_ & lt_):
            dom[i] = True
    return int((~dom).sum())


def nd_certo(O):
    """So dominancia CERTA (estrito em TODOS os objetivos) -> limite superior."""
    n = len(O)
    dom = np.zeros(n, bool)
    for i in range(n):
        if np.any(np.all(O < O[i], axis=1)):
            dom[i] = True
    return int((~dom).sum())


def colisoes_linha(O, sids):
    """Nº de sids em grupos de linha de objetivos bit-identica (>1 sid)."""
    _, inv, cnt = np.unique(O, axis=0, return_inverse=True, return_counts=True)
    return int(sum(c - 1 for c in cnt if c > 1))


# ---------------------------------------------------------------- (1)(2)(3)
rows = []
gap = []
probs = sorted(os.listdir(f'{RES}/moead'))
for prob in probs:
    man, recs, real, pop = le('moead', prob)
    head = [x for x in recs if x['rec'] == 'header'][0]
    dec = [x for x in recs if x['rec'] == 'decomposicao'][0]
    ger = [x for x in recs if x['rec'] == 'moead_gen']
    guards = [x for x in recs if x['rec'] == 'guard']
    D, M = int(head['D']), int(head['M'])
    Nef = int(man['params']['N_efetivo'])
    W = np.array(dec['vetores'], float)
    T = math.ceil(len(W) / 10)
    d = np.sqrt(((W[:, None, :] - W[None, :, :]) ** 2).sum(-1))
    B = np.argsort(d, axis=1, kind='stable')[:, :T]
    nn = B[:, 1]

    fcols = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    objs = real.set_index('solution_id')[fcols]
    sid_by_gen = {int(g): grp['solution_id'].values for g, grp in pop.groupby('geracao')}

    ok_id = ok_nd = 0
    quebras = 0
    prev = None
    exp_clones = 0.0
    nf_ok = nf_bracket = nf_fora = 0
    for g in ger:
        gg = int(g['geracao'])
        sids = sid_by_gen[gg]
        O64 = objs.loc[sids].values.astype(np.float64)
        O32 = objs.loc[sids].values.astype(np.float32)
        lo = np.array(g['ideal'], float)
        # tolerancia float32 relativa (regra 11): |a-b| <= eps32*max(1,|a|)
        tol = EPS32 * np.maximum(1.0, np.abs(lo)) * 4
        ok_id += int(np.all(np.abs(lo - O64.min(0)) <= tol))
        hi = np.array(g['nadir_pop'], float)
        tol2 = EPS32 * np.maximum(1.0, np.abs(hi)) * 4
        ok_nd += int(np.all(np.abs(hi - O64.max(0)) <= tol2))
        if prev is not None:
            tp = EPS32 * np.maximum(1.0, np.abs(prev)) * 4
            if np.any(lo > prev + tp):
                quebras += 1
        prev = lo
        # previsao de clones desta geracao: p = f_pares * (1-1/D)^D  (+ ramo 2^-D)
        f = float(np.mean(sids == sids[nn]))
        p = (f + (1 - f) * 2.0 ** (-D)) * (1 - 1.0 / D) ** D
        exp_clones += p * Nef
        # n_front1: bracket
        logv = int(g['n_front1'])
        v_lo = nd_f32(O32)
        v_hi = nd_certo(O32)
        v_lo_corr = v_lo - colisoes_linha(O32, sids)
        if logv == v_lo:
            nf_ok += 1
        elif v_lo_corr <= logv <= v_hi:
            nf_bracket += 1
        else:
            nf_fora += 1
            gap.append(dict(problema=prob, geracao=gg, log=logv, lo=v_lo,
                            lo_corr=v_lo_corr, hi=v_hi))
    ch = [x for x in guards if x['name'] == 'cache_hit']
    c0 = len([x for x in ch if x['fe'] <= 11 * D - 1])
    clones = len(ch) - c0
    rows.append(dict(problema=prob, D=D, M=M, N_ef=Nef, n_ger=len(ger),
                     M15_ideal=ok_id, M15_nadir=ok_nd, M15_quebras=quebras,
                     clones=clones, clones_prev=exp_clones,
                     razao=clones / exp_clones if exp_clones else np.nan,
                     nf_exato=nf_ok, nf_bracket=nf_bracket, nf_fora=nf_fora))

df = pd.DataFrame(rows)
df.to_csv(f'{OUT}/t11_moead_parte2.csv', index=False)
pd.DataFrame(gap).to_csv(f'{OUT}/t11_moead_nfront1_fora.csv', index=False)
print(df.to_string(index=False))
n = df.n_ger.sum()
print(f'\nM15 (tol float32): ideal {df.M15_ideal.sum()}/{n} · nadir {df.M15_nadir.sum()}/{n}'
      f' · quebras de monotonia {df.M15_quebras.sum()} em '
      f'{(df.M15_quebras>0).sum()}/25 celulas')
print(f'M6 clones medidos {df.clones.sum()} · previstos {df.clones_prev.sum():.1f}'
      f' · razao global {df.clones.sum()/df.clones_prev.sum():.3f}'
      f' · razao por celula [{df.razao.min():.3f}, {df.razao.max():.3f}] mediana {df.razao.median():.3f}')
print(f'M16 n_front1: exato {df.nf_exato.sum()}/{n} · dentro do bracket '
      f'{df.nf_bracket.sum()} · FORA {df.nf_fora.sum()}')

# ---------------------------------------------------------------- (4) 4 pisos
print('\n=== A formula T11 `geracoes_derivadas` nos 4 pisos (s42 main) ===')
tab = []
for alg in ['moead', 'nsga2', 'nsga3', 'smsemoa']:
    for prob in sorted(os.listdir(f'{RES}/{alg}')):
        try:
            man, recs, real, pop = le(alg, prob)
        except Exception:
            continue
        head = [x for x in recs if x['rec'] == 'header'][0]
        D = int(head['D'])
        Nef = int(man['params']['N_efetivo'])
        guards = [x for x in recs if x['rec'] == 'guard']
        ch = [x for x in guards if x['name'] == 'cache_hit']
        c0 = len([x for x in ch if x['fe'] <= 11 * D - 1])
        dup = len(ch) - c0
        ng = man['n_geracoes']
        par = 2 * (Nef // 2)
        tab.append(dict(alg=alg, problema=prob, D=D, N_ef=Nef, n_ger=ng, dup=dup,
                        f_T11=math.floor((20 * D + dup) / par),
                        f_Nef=math.floor((20 * D + dup) / Nef),
                        f_Nef_p1=math.floor((20 * D + dup) / Nef) + 1,
                        f_antiga=(20 * D) // Nef))
t = pd.DataFrame(tab)
t['T11_ok'] = t.f_T11 == t.n_ger
t['Nef_ok'] = t.f_Nef == t.n_ger
t['Nef_p1_ok'] = t.f_Nef_p1 == t.n_ger
t['antiga_ok'] = t.f_antiga == t.n_ger
t.to_csv(f'{OUT}/t11_formula_4pisos.csv', index=False)
g = t.groupby('alg').agg(n=('n_ger', 'size'), T11=('T11_ok', 'sum'),
                         Nef=('Nef_ok', 'sum'), Nef_p1=('Nef_p1_ok', 'sum'),
                         antiga=('antiga_ok', 'sum'))
print(g.to_string())
print('TOTAL', len(t), '| formula T11 acerta', int(t.T11_ok.sum()),
      '| floor(/Nef)+1 acerta', int(t.Nef_p1_ok.sum()),
      '| antiga acerta', int(t.antiga_ok.sum()))
