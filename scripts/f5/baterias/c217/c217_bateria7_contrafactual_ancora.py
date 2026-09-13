#!/usr/bin/env python
"""BATERIA 7 — (a) contrafactual D17 (fiação as-shipped x corrigida);
(b) acurácia por amostra comparável à Tab.5/7 do paper;
(c) assinatura de tempo do laço interno Gmax/wmax;
(d) célula-ÂNCORA DTLZ2_d15 semente 0 (fora das 25) — identidades + IGD cru.
Saídas: c217_contrafactual_d17.csv, c217_acuracia.csv, c217_busca_por_estado.csv, c217_ancora_d15.json
"""
import os, sys, json
import numpy as np, pandas as pd, pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = f'{REPO}/f5/baterias/c217'
sys.path.insert(0, REPO)
G = pd.read_pickle(f'{OUT}/c217_identidades.pkl')
C = pd.read_csv(f'{OUT}/c217_celulas.csv').set_index('problema')
d = 0.8

# ---------- (a) contrafactual D17 ----------
st_ship = np.where(G.p_mais < 1 - d, 1, np.where(G.p_menos < 1 - d, 2, 3))
lote_ship = np.where(st_ship == 3, 1, np.floor(G.Pbest / 2))
print('=== (a) CONTRAFACTUAL D17 ===')
print('real       :', G.estado.value_counts().to_dict())
print('as-shipped :', pd.Series(st_ship).value_counts().to_dict())
print('divergem em %d/%d (%.1f%%)' % ((st_ship != G.estado).sum(), len(G), 100 * (st_ship != G.estado).mean()))
print('Σlote real %d x as-shipped %d (%.1fx)' % (G.lote.sum(), lote_ship.sum(), lote_ship.sum() / G.lote.sum()))
rows = []
for p, t in G.assign(ls=lote_ship, ss=st_ship).groupby('problema'):
    orc = C.loc[p, 'maxfe'] - C.loc[p, 'n_init']
    cum = np.cumsum(t.sort_values('geracao').ls.to_numpy())
    rows.append(dict(problema=p, gens_reais=len(t), gens_asshipped_est=int(min(np.searchsorted(cum, orc) + 1, len(t))),
                     frac_st1_ship=float((t.ss == 1).mean()), frac_st1_real=float((t.estado == 1).mean()),
                     frac_st2_ship=float((t.ss == 2).mean()), frac_st3_ship=float((t.ss == 3).mean())))
R = pd.DataFrame(rows); R.to_csv(f'{OUT}/c217_contrafactual_d17.csv', index=False); print(R.to_string())

# ---------- (b) acurácia por amostra ----------
G['contr_frac'] = G.n_contradicoes / G.Dvalid
G['acc'] = G.p_mais + 0.5 * G.contr_frac
A = G.groupby('problema').agg(n=('acc', 'size'), acc=('acc', 'mean'), pmais=('p_mais', 'mean'),
                              pmenos=('p_menos', 'mean'), contr=('contr_frac', 'mean'),
                              st12=('estado', lambda s: int((s != 3).sum())))
A['fam'] = ['BBOB' if p.startswith('BBOB') else ('DTLZ' if p.startswith('DTLZ') else
            ('WFG' if p.startswith('WFG') else ('ZDT' if p.startswith('ZDT') else 'MMF'))) for p in A.index]
A.to_csv(f'{OUT}/c217_acuracia.csv')
print('\n=== (b) ACURÁCIA POR AMOSTRA (p+ + 0,5·contradição) — comparável à Tab.5/7 ===')
print('global média %.4f (paper Tab.7 média WFG N/4 = 0,60417)' % G.acc.mean())
print(A.groupby('fam').agg(n=('n', 'sum'), acc=('acc', 'mean'), contr=('contr', 'mean'), st12=('st12', 'sum')).to_string())

# ---------- (c) assinatura de tempo do laço interno ----------
rows = []
for p, t in G.groupby('problema'):
    a = t[t.estado.isin([1, 2])]; b = t[t.estado == 3]
    if len(a):
        rows.append(dict(problema=p, n12=len(a), lnum=int(a.n_Pmid.median()), wmax_pred=int(3000 // a.n_Pmid.median()),
                         busca12=a.tempo_busca_s.median(), busca3=b.tempo_busca_s.median(),
                         razao=a.tempo_busca_s.median() / b.tempo_busca_s.median()))
W = pd.DataFrame(rows); W.to_csv(f'{OUT}/c217_busca_por_estado.csv', index=False)
print('\n=== (c) tempo_busca_s por estado (evidência indireta do laço wmax=⌊3000/lnum⌋) ===')
print(W.to_string())
g12 = G[G.estado.isin([1, 2])]; g3 = G[G.estado == 3]
print('mediana st1/2 %.4f s x st3 %.4f s = %.1fx | 55 gerações (0,81%%) = %.1f%% de todo o tempo de busca'
      % (g12.tempo_busca_s.median(), g3.tempo_busca_s.median(), g12.tempo_busca_s.median() / g3.tempo_busca_s.median(),
         100 * g12.tempo_busca_s.sum() / G.tempo_busca_s.sum()))

# ---------- (d) célula-âncora DTLZ2_d15 (semente 0) ----------
b = f'{REPO}/data/experiments/main/c217/exp_main_c217_DTLZ2_d15_0'
man = json.load(open(b + '.manifest.json'))
gg = []; hdr = None
for line in open(b + '.jsonl'):
    x = json.loads(line)
    if x['rec'] == 'header':
        hdr = x
    elif x['rec'] == 'c217_gen':
        y = {k: v for k, v in x.items() if k not in ('rec', 'ts', 'f_best', 'modelo_hp')}
        y['spread'] = x['modelo_hp']['spread']; gg.append(y)
gg = pd.DataFrame(gg)
pop = pq.read_table(b + '__pop.parquet').to_pandas(); gg['pop_n'] = gg.geracao.map(pop.groupby('geracao').size())
P = np.where(gg.geracao == 1, gg.pop_n, np.minimum(50, gg.pop_n)).astype(float)
Pb = np.ceil(P / 4); Pw = np.ceil(P / 2) - Pb; Dv = (Pb - gg.n_best) + (Pw - gg.n_worst)
anc = dict(run=man['run_id'], D=hdr['D'], M=hdr['M'], maxfe=man['maxfe'], n_gen=len(gg),
           estados=gg.estado.value_counts().to_dict(),
           nbest_ok=int((np.ceil(3 * Pb / 4) == gg.n_best).sum()), nworst_ok=int((np.ceil(3 * Pw / 4) == gg.n_worst).sum()),
           npares_ok=int((gg.n_treino * (gg.n_treino - 1) == gg.n_pares_treino).sum()),
           npmid_ok=int((2 * np.floor(P / 8) + 1 == gg.n_Pmid).sum()),
           soma_ok=int(np.isclose(gg.p_mais * Dv + gg.p_menos * Dv + gg.n_contradicoes, Dv, atol=1e-6).sum()),
           regra_ok=int((np.where(gg.p_mais > .8, 1, np.where(gg.p_menos > .8, 2, 3)) == gg.estado).sum()),
           acc=float((gg.p_mais + 0.5 * gg.n_contradicoes / Dv).mean()))
from src import metrics
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.problems import get_problem
F = pq.read_table(b + '__real.parquet').to_pandas()[['f0', 'f1', 'f2']].to_numpy().astype(float)
nd = metrics.nondominated_front(F)
pf = get_problem('dtlz2', n_var=15, n_obj=3).pareto_front(get_reference_directions('das-dennis', 3, n_partitions=99))
anc.update(n_nd=int(len(nd)), n_ref=int(len(pf)), igd_cru=float(metrics.igd(nd, pf)), igdp_cru=float(metrics.igd_plus(nd, pf)),
           paper_igd=6.9212e-2, paper_3sigma=[4.586e-2, 9.256e-2])
json.dump(anc, open(f'{OUT}/c217_ancora_d15.json', 'w'), indent=1)
print('\n=== (d) ÂNCORA DTLZ2_d15 semente 0 ===')
print(json.dumps(anc, indent=1))
