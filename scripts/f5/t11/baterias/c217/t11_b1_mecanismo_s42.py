# -*- coding: utf-8 -*-
"""T11/c217 — BATERIA 1: o MECANISMO na rodada-42 (25 celulas, TODAS as geracoes).
Re-medicao independente das identidades fechadas da F5 (A4/A5/A6/A7/A9/A10/A12/A17/A19/A20).
READ-ONLY. Escreve so em f5/t11/baterias/c217/.
"""
import json, glob, os, math
from collections import Counter
import pandas as pd, numpy as np

RAIZ = '/Users/gmello/Documents/python_repos/mestrado'
OUT = os.path.join(RAIZ, 'ua-dd-saea/f5/t11/baterias/c217')
CEL = sorted(glob.glob(os.path.join(RAIZ, 'resultados_experimentos/c217/*/42')))

def ler(cel):
    prob = cel.split('/')[-2]
    j = glob.glob(os.path.join(cel, '*.jsonl'))[0]
    man = json.load(open(glob.glob(os.path.join(cel, '*.manifest.json'))[0]))
    gens, sondas, guards, header, footer = [], [], [], None, None
    for line in open(j, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        d = json.loads(line); r = d.get('rec')
        if r == 'c217_gen': gens.append(d)
        elif r == 'sonda': sondas.append(d)
        elif r == 'guard': guards.append(d)
        elif r == 'header': header = d
        elif r == 'footer': footer = d
    return prob, man, gens, sondas, guards, header, footer

rows, gall = [], []
for cel in CEL:
    prob, man, gens, sondas, guards, header, footer = ler(cel)
    base = glob.glob(os.path.join(cel, '*__pop.parquet'))[0]
    pop = pd.read_parquet(base)
    real = pd.read_parquet(base.replace('__pop', '__real'))
    sur = pd.read_parquet(base.replace('__pop', '__surrogate'))
    D = header['D']
    # |P| por geracao: g=1 -> |Arc|=init; g>=2 -> min(50,|②(g)|)
    tam2 = pop.groupby('geracao').size()
    for g in gens:
        gg = g['geracao']
        a2 = int(tam2.get(gg, np.nan)) if gg in tam2.index else np.nan
        P = a2 if gg == 1 else min(50, a2)
        gall.append(dict(problema=prob, D=D, g=gg, P=P, a2=a2, arc_size=g['arc_size'],
                         n_best=g['n_best'], n_worst=g['n_worst'], n_treino=g['n_treino'],
                         n_pares=g['n_pares_treino'], n_Pmid=g['n_Pmid'],
                         p_mais=g['p_mais'], p_menos=g['p_menos'], nc=g['n_contradicoes'],
                         estado=g['estado'], lote=g['lote'], score=g['score'],
                         delta=g['delta'], fe=g['fe'], ftm=g['fe_treino_max'],
                         spread=g['modelo_hp']['spread'], motivo=g['motivo'],
                         t_fit=g['tempo_fit_s'], t_busca=g['tempo_busca_s'],
                         t_ger=g['tempo_geracao_s'],
                         pmid_ids=('pmid_ids' in g), y_dist=('y_treino_dist' in g)))
    surb = sur[sur.regime == 'busca'] if 'regime' in sur.columns else sur
    rows.append(dict(problema=prob, D=D, M=header['M'], maxfe=header['maxfe'],
                     n_real=len(real), n_gen=len(gens), n_ger_man=man['n_geracoes'],
                     n_sonda=len(sondas), n_guard=len(guards), cache=man['cache_hits'],
                     fe_final=man['fe_final'], status=man['status'],
                     termino=footer['termino'], cp_init=footer['cp_init'],
                     n_sur=len(sur), n_busca=len(surb),
                     tem_params='params' in man,
                     tem_regra='REGRA_DO_ROTULO' in man.get('sigma_dict', {}),
                     tem_campanha='campanha_id' in man))

C = pd.DataFrame(rows); G = pd.DataFrame(gall)
C.to_csv(os.path.join(OUT, 't11_c217_s42_celulas.csv'), index=False)
G.to_pickle(os.path.join(OUT, 't11_c217_s42_geracoes.pkl'))

def ceil(x): return int(math.ceil(x - 1e-12))
n = len(G)
print('== ESCALA: %d celulas, %d geracoes, %d infills(soma lote)' % (len(C), n, int(G.lote.sum())))
print('== FE: 31D-1 exato em %d/%d ; fe_final==maxfe %d/%d' %
      ((C.maxfe == 31*C.D-1).sum(), len(C), (C.fe_final == C.maxfe).sum(), len(C)))
print('== n_real == maxfe: %d/%d' % ((C.n_real == C.maxfe).sum(), len(C)))
print('== n_geracoes == n_gen_events+1: %d/%d' % ((C.n_ger_man == C.n_gen+1).sum(), len(C)))

ok = G.P.notna()
Gv = G[ok].copy()
Gv['Pb'] = Gv.P.map(lambda p: ceil(p/4))
Gv['Pw'] = Gv.P.map(lambda p: ceil(p/2) - ceil(p/4))
id_best = (Gv.n_best == Gv.Pb.map(lambda x: ceil(0.75*x))).sum()
id_worst = (Gv.n_worst == Gv.Pw.map(lambda x: ceil(0.75*x))).sum()
id_tre = (Gv.n_treino == Gv.n_best + Gv.n_worst).sum()
id_par = (Gv.n_pares == Gv.n_treino*(Gv.n_treino-1)).sum()
id_pmid = (Gv.n_Pmid == Gv.P.map(lambda p: 2*int(p//8)+1)).sum()
print('== A4 n_best=ceil(3/4*ceil(|P|/4)) : %d/%d' % (id_best, len(Gv)))
print('== A4 n_worst=ceil(3/4*(ceil(|P|/2)-ceil(|P|/4))) : %d/%d' % (id_worst, len(Gv)))
print('== A4 n_treino=n_best+n_worst : %d/%d' % (id_tre, n))
print('== A5 n_pares=n_tr(n_tr-1) : %d/%d ; razao vs 2*nb*nw = %.3f' %
      (id_par, n, (G.n_pares.sum()/(2*(G.n_best*G.n_worst)).sum())))
print('== A17 n_Pmid=2*floor(|P|/8)+1 : %d/%d' % (id_pmid, len(Gv)))

Gv['Dv'] = (Gv.Pb - Gv.n_best) + (Gv.Pw - Gv.n_worst)
tri = (np.abs(Gv.p_mais.fillna(-9)*Gv.Dv + Gv.p_menos.fillna(-9)*Gv.Dv + Gv.nc - Gv.Dv) < 1e-6).sum()
kint = (np.abs(Gv.p_mais.fillna(0)*Gv.Dv - np.round(Gv.p_mais.fillna(0)*Gv.Dv)) < 1e-6).sum()
print('== A6 p+*|Dv| + p-*|Dv| + contrad == |Dv| : %d/%d' % (tri, len(Gv)))
print('== A6 k+ inteiro : %d/%d ; |Dv| distrib: %s' % (kint, len(Gv), dict(Counter(Gv.Dv))))

def est(r):
    pm, pn, d = r.p_mais, r.p_menos, r.delta
    if pm is None or (isinstance(pm, float) and np.isnan(pm)): return 3
    if pm > d: return 1
    if pn > d: return 2
    return 3
rec = G.apply(est, axis=1)
print('== A9 estado recomputado == logado : %d/%d' % ((rec == G.estado).sum(), n))
print('== A9 distribuicao estado: %s' % dict(Counter(G.estado)))
cf = G.apply(lambda r: 1 if (r.p_mais is not None and not (isinstance(r.p_mais,float) and np.isnan(r.p_mais)) and r.p_mais < 1-r.delta) else (2 if (r.p_menos is not None and not (isinstance(r.p_menos,float) and np.isnan(r.p_menos)) and r.p_menos < 1-r.delta) else 3), axis=1)
print('== A9 contrafactual as-shipped: %s ; divergem %d/%d (%.1f%%)' %
      (dict(Counter(cf)), (cf != G.estado).sum(), n, 100*(cf != G.estado).sum()/n))

st3 = G[G.estado == 3]; st12 = Gv[Gv.estado != 3]
print('== A10 lote==1 no estado3: %d/%d' % ((st3.lote == 1).sum(), len(st3)))
print('== A10 lote==floor(ceil(|P|/4)/2) nos st1/2: %d/%d' % ((st12.lote == (st12.Pb//2)).sum(), len(st12)))
print('== A12 score==+1|-1|0 conforme estado: %d/%d' %
      (((G.estado == 1) & (G.score == 1) | (G.estado == 2) & (G.score == -1) | (G.estado == 3) & (G.score == 0)).sum(), n))
print('== A8 delta==0.8 em %d/%d ; A14 spread==0.1925 em %d/%d' %
      ((G.delta == 0.8).sum(), n, (G.spread == 0.1925).sum(), n))
print('== A16 busca mediana st1/2=%.4fs  st3=%.4fs  razao=%.1fx' %
      (st12.t_busca.median(), st3.t_busca.median(), st12.t_busca.median()/st3.t_busca.median()))
print('== A23 fe_treino_max quedas (soma): %d ; celulas com queda: %d/%d' %
      (int(sum((G[G.problema == p].ftm.astype(float).diff() < 0).sum() for p in C.problema)),
       sum(1 for p in C.problema if (G[G.problema == p].ftm.astype(float).diff() < 0).any()), len(C)))
print('== A28 regime-NaN no motivo: %d/%d' % (G.motivo.str.contains('NaN', case=False).sum(), n))
print('== NOVOS T11 no s42: pmid_ids em %d/%d ger ; y_treino_dist em %d/%d ger' %
      (G.pmid_ids.sum(), n, G.y_dist.sum(), n))
print('== CONTRATO s42: params em %d/25 ; REGRA_DO_ROTULO em %d/25 ; campanha_id em %d/25' %
      (C.tem_params.sum(), C.tem_regra.sum(), C.tem_campanha.sum()))
print('== termino normal %d/25 ; status ok %d/25 ; cp_init %d/25' %
      ((C.termino == 'normal').sum(), (C.status == 'ok').sum(), C.cp_init.sum()))
C.to_csv(os.path.join(OUT, 't11_c217_s42_celulas.csv'), index=False)
