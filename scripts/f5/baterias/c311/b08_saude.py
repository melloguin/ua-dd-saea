"""B08 — saúde em escala: trajetórias (20 checkpoints), empate-por-desenho das métricas
oficiais entre os 5 algs offline, endpoint ⑦, régua da sonda, sweep tier x dist."""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from lib_c311 import *

F5 = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5'
met = pd.read_csv(f'{F5}/metricas_finais_f52c.csv')
tmp = pd.read_csv(f'{F5}/tempo_f52d.csv')
snd = pd.read_csv(f'{F5}/sonda_f52e.csv')
c7 = pd.read_csv(f'{F5}/transversal_offline_camada7.csv')
u = pd.read_csv(os.path.join(OUT, 'b02_universal.csv'))
cel = pd.read_csv(os.path.join(OUT, 'b03_celulas.csv'))

# ---------- 1. trajetórias ----------
tr = []
for f in sorted(glob.glob(f'{F5}/trajetorias/*_c311_*_42.json')):
    base = os.path.basename(f)[:-5]
    exp, _, rest = base.partition('_c311_')
    prob = rest[:-3]
    j = json.load(open(f))
    ig = np.array([p['igd_plus'] for p in j]); hv = np.array([p['hv'] for p in j])
    tr.append(dict(exp=exp, problema=prob, n_cp=len(j),
                   viol_igd=int((np.diff(ig) > 1e-12).sum()),
                   viol_hv=int((np.diff(hv) < -1e-12).sum()),
                   igd_ini=float(ig[0]), igd_fim=float(ig[-1]),
                   ganho=float(ig[0] / ig[-1]) if ig[-1] > 0 else np.nan,
                   nd_ini=j[0]['n_nd'], nd_fim=j[-1]['n_nd']))
T = pd.DataFrame(tr); salva(T, 'b08_trajetorias.csv')
print('trajetórias:', len(T), 'transições:', int((T.n_cp - 1).sum()),
      'viol IGD+:', int(T.viol_igd.sum()), 'viol HV:', int(T.viol_hv.sum()))

# ---------- 2. empate por desenho entre os 5 offline ----------
OFF = ['c311', 'b5r', 'b5m', 'e103', 'moead_media', 'treed_media']
sub = met[met.alg.isin(OFF)]
emp = []
for (e, p), g in sub.groupby(['exp', 'problema']):
    if len(g) < 2:
        continue
    emp.append(dict(exp=e, problema=p, n_alg=len(g), algs=';'.join(sorted(g.alg)),
                    igd_nunique=g.igd_plus.round(12).nunique(),
                    hv_nunique=g.hv.round(12).nunique(),
                    nd_nunique=g.n_nd.nunique(),
                    igd=float(g.igd_plus.iloc[0])))
E = pd.DataFrame(emp); salva(E, 'b08_empate_offline.csv')
print('grupos (exp,problema) com >=2 offline:', len(E),
      '| IGD+ idêntico:', int((E.igd_nunique == 1).sum()),
      '| HV idêntico:', int((E.hv_nunique == 1).sum()),
      '| |ND| idêntico:', int((E.nd_nunique == 1).sum()))

# ---------- 3. régua c311 x pisos no main ----------
PISOS = ['nsga2', 'nsga3', 'smsemoa', 'moead']
mm = met[met.exp == 'main']
oo = met[(met.exp == 'off') & (met.alg == 'c311')]
reg = []
for _, row in oo.iterrows():
    p = row.problema
    g = mm[(mm.problema == p) & (mm.alg.isin(PISOS))]
    if not len(g):
        continue
    b = g.loc[g.igd_plus.idxmin()]
    reg.append(dict(problema=p, igd_c311=row.igd_plus, hv_c311=row.hv, nd_c311=row.n_nd,
                    melhor_piso=b.alg, igd_piso=b.igd_plus, razao=row.igd_plus / b.igd_plus,
                    bate=bool(row.igd_plus < b.igd_plus)))
R = pd.DataFrame(reg); salva(R, 'b08_regua_pisos.csv')
print('c311 bate o melhor piso (métrica oficial ①):', int(R.bate.sum()), '/', len(R))

# ---------- 4. endpoint ⑦ ----------
c7c = c7[c7.alg == 'c311'].copy()
c7o = c7[c7.alg.isin(['c311', 'b5r', 'b5m', 'e103', 'moead_media'])]
piv = c7o.pivot_table(index='problema', columns='alg', values='igd_plus_c7')
piv['vencedor'] = piv.idxmin(axis=1)
piv['c311_rank'] = piv[['b5m', 'b5r', 'c311', 'e103', 'moead_media']].rank(axis=1)['c311']
salva(piv.reset_index(), 'b08_endpoint_c7.csv')
print('\n⑦ (endpoint oficial do offline) — c311 x demais offline no main/off:')
print('c311 vence em', int((piv.vencedor == 'c311').sum()), '/', len(piv),
      '| rank médio', float(piv.c311_rank.mean()))

# ---------- 5. régua da sonda (do f5/sonda_f52e.csv) ----------
sc = snd[snd.alg == 'c311'].copy()
sc['nan_share'] = 1 - sc.n_validas / (sc.n_validas + sc.n_nan)
salva(sc, 'b08_sonda_f52e_c311.csv')
print('\nsonda_f52e c311:', sc.shape, '| blocos por célula:', sc.groupby(['exp', 'problema']).bloco.nunique().unique())

# ---------- 6. sweep tier x dist ----------
sw = met[(met.alg == 'c311') & (met.exp.str.startswith('sweep'))].copy()
sw['tier'] = sw.exp.str.split('-').str[1]; sw['dist'] = sw.exp.str.split('-').str[2]
pv = sw.pivot_table(index=['problema', 'dist'], columns='tier', values='igd_plus')
salva(pv.reset_index(), 'b08_sweep_igd.csv')
print('\nsweep IGD+ (métrica oficial da ①) por tier:')
print(pv.to_string())

# ---------- 7. mecanismo x tier ----------
mec = cel.merge(u[['label', 'F2_nan_sonda_b0', 'F2_nan_build', 'F2_nan_final',
                   'U12_razao_fantasia', 'U12_n_final', 'U12_n_nd']], on='label')
salva(mec[['label', 'tier', 'dist', 'problema', 'D', 'M', 'N', 'I_eff', 'I_max', 'I_frac',
           'cobertura_frac', 'prof_max', 'max_folhas', 'teto_folhas', 'pop_max', 'pop_ultima',
           'F2_nan_sonda_b0', 'F2_nan_build', 'F2_nan_final', 'U12_razao_fantasia',
           'fit_total', 'busca_total', 'tempo_total_s']], 'b08_mecanismo_tier.csv')
print('\nmecanismo por tier (mediana):')
print(mec.groupby('tier')[['I_eff', 'I_max', 'I_frac', 'cobertura_frac', 'F2_nan_sonda_b0',
                           'U12_razao_fantasia', 'fit_total', 'tempo_total_s']].median().to_string())
print('\ntempo: máquina =', tmp[tmp.alg == 'c311'].maquina.value_counts().to_dict())
print('wall por tier:')
tt = tmp[tmp.alg == 'c311'].copy()
tt['tier'] = np.where(tt.exp == 'off', 'small', tt.exp.str.split('-').str[1])
print(tt.groupby('tier').wall_s.describe().to_string())
