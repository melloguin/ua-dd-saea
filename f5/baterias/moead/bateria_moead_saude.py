#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bateria_moead_saude.py — Classe B (saúde/papel de controle) + fechamento do D88 em float64.
  S1  seeding D88 recomputado no espaço FLOAT64 (src/problems.py) ≡ ②(ger.1), ordem inclusive
  S2  ① f ≡ float32(src/problems.py(X_float64)) bit-a-bit
  S3  trajetórias de 20 checkpoints: violações de monotonia do IGD+
  S4  regressão vs DoE: IGD+/HV do subconjunto `init` × do conjunto final (métrica OFICIAL)
  S5  posição vs os 4 pisos e vs as 17 configs SA (metricas_finais_f52c.csv)
"""
import json, os, sys
import numpy as np
import pandas as pd

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RAIZ = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/moead'
OUT = os.path.join(REPO, 'f5', 'baterias', 'moead')
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics, problems                      # noqa: E402
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.operators.survival.rank_and_crowding.metrics import get_crowding_function
_cdf = get_crowding_function('cd')

# GATE D92 antes de qualquer conta com métrica
v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)

PROBS = sorted(p for p in os.listdir(RAIZ) if not p.startswith('.'))
PROBCLS = {'BBOB_F1': 'BBOB_F1_Sphere_Sphere', 'BBOB_F5': 'BBOB_F5_Sphere_SharpRidge',
           'BBOB_F17': 'BBOB_F17_EllipsoidSeparable_SchafferF7',
           'BBOB_F22': 'BBOB_F22_AttractiveSector_SharpRidge',
           'BBOB_F37': 'BBOB_F37_SharpRidge_Rastrigin',
           'BBOB_F49': 'BBOB_F49_Rastrigin_Gallagher101',
           'BBOB_F55': 'BBOB_F55_Gallagher101_Gallagher101'}


def crowd(F):
    F = np.asarray(F, float)
    if len(F) <= 2:
        return np.full(len(F), np.inf)
    return np.asarray(_cdf.do(F)).ravel()


rows = []
for prob in PROBS:
    base = os.path.join(RAIZ, prob, '42', 'exp_main_moead_%s_42' % prob)
    man = json.load(open(base + '.manifest.json'))
    evs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    hdr = [e for e in evs if e['rec'] == 'header'][0]
    se = [e for e in evs if e['rec'] == 'seeding'][0]
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    D, M = hdr['D'], hdr['M']
    n_doe = 11 * D - 1
    N = man['params']['N_efetivo']
    xc = sorted([c for c in real.columns if c.startswith('x') and c[1:].isdigit()], key=lambda c: int(c[1:]))
    fc = sorted([c for c in real.columns if c.startswith('f') and c[1:].isdigit()], key=lambda c: int(c[1:]))

    # --- S1/S2: reavaliação em float64 do DoE do artefato ---
    doe = pd.read_parquet(os.path.join(REPO, 'data', 'doe', prob, 'doe_%s_42.parquet' % prob))
    Xd = doe[[c for c in doe.columns if c.startswith('x')]].to_numpy(np.float64)
    cls = getattr(problems, PROBCLS.get(prob, prob))
    F64 = np.asarray(cls().evaluate(Xd), dtype=np.float64)
    F32 = F64.astype(np.float32).astype(np.float64)
    Fitem = real[fc].to_numpy(np.float64)[:n_doe]
    s2_max = float(np.abs(F32 - Fitem).max())

    fr64 = NonDominatedSorting().do(F64)
    ordem = []
    for f in fr64:
        f = np.asarray(f)
        c = crowd(F64[f])
        ordem.extend(f[np.lexsort((f, -c))].tolist())
    g1 = pop[pop['geracao'] == pop['geracao'].min()]['solution_id'].to_numpy().tolist()
    s1_conj = set(ordem[:N]) == set(g1)
    s1_ord = ordem[:N] == g1
    fr32 = NonDominatedSorting().do(F32)

    # --- S3 trajetória ---
    traj = json.load(open(os.path.join(REPO, 'f5', 'trajetorias', 'main_moead_%s_42.json' % prob)))
    ig = np.array([t['igd_plus'] for t in traj], float)
    hvt = np.array([t['hv'] for t in traj], float)
    viol = int((np.diff(ig) > 1e-12).sum())
    ganho = float(ig[0] - ig[-1])

    # --- S4 DoE × final (métrica oficial) ---
    Fdoe = real.loc[real['fase'] == 'init', fc].to_numpy(np.float64)
    Ffin = real[fc].to_numpy(np.float64)
    RN = metrics.reference_set(prob)          # 1× por problema (reuso — D69)
    m_doe = metrics.metrics_of_set(Fdoe, prob, ref_norm=RN)
    m_fin = metrics.metrics_of_set(Ffin, prob, ref_norm=RN)
    # o ganho da fase de otimização só sobre os 20D infills
    Fopt = real.loc[real['fase'] != 'init', fc].to_numpy(np.float64)
    m_opt = metrics.metrics_of_set(Fopt, prob, ref_norm=RN) if len(Fopt) else None
    print('  %s ok' % prob, flush=True)

    rows.append(dict(problema=prob, D=D, M=M, N=N,
                     s1_conjunto=s1_conj, s1_ordem=s1_ord,
                     log_nfr=se['n_frentes'], f64_nfr=len(fr64), f32_nfr=len(fr32),
                     log_f1=se['n_frente1'], f64_f1=len(fr64[0]), f32_f1=len(fr32[0]),
                     s2_max_dif=s2_max,
                     traj_viol=viol, igd0=float(ig[0]), igdF=float(ig[-1]), ganho_traj=ganho,
                     igd_doe=m_doe['igd_plus'], igd_fin=m_fin['igd_plus'],
                     igd_opt=(m_opt['igd_plus'] if m_opt else np.nan),
                     hv_doe=m_doe['hv'], hv_fin=m_fin['hv'],
                     nd_doe=m_doe['n_nd'], nd_fin=m_fin['n_nd'],
                     razao_doe=m_fin['igd_plus'] / m_doe['igd_plus'],
                     regride=(m_fin['igd_plus'] > m_doe['igd_plus'] * (1 + 1e-12))))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'moead_saude.csv'), index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40)
print(df.to_string())
print('\nS1 conjunto:', df.s1_conjunto.sum(), '/25  | ordem:', df.s1_ordem.sum(), '/25')
print('S2 max dif ①×float32(problems):', df.s2_max_dif.max())
print('log_nfr==f64_nfr:', int((df.log_nfr == df.f64_nfr).sum()), '| log_f1==f64_f1:', int((df.log_f1 == df.f64_f1).sum()))
print('log==f32:', int(((df.log_nfr == df.f32_nfr) & (df.log_f1 == df.f32_f1)).sum()))
print('S3 violações de monotonia IGD+:', df.traj_viol.sum())
print('S4 células que REGRIDEM vs DoE:', df.regride.sum(), list(df.loc[df.regride, 'problema']))
print('S4 razão final/DoE: min %.4f med %.4f max %.4f' % (df.razao_doe.min(), df.razao_doe.median(), df.razao_doe.max()))
print('HV final == 0 em:', int((df.hv_fin == 0).sum()), list(df.loc[df.hv_fin == 0, 'problema']))
print('HV DoE  == 0 em:', int((df.hv_doe == 0).sum()))

# ---------- S5 posição ----------
M = pd.read_csv(os.path.join(REPO, 'f5', 'metricas_finais_f52c.csv'))
M = M[M.exp == 'main']
PISOS = ['moead', 'nsga2', 'nsga3', 'smsemoa']
piv = M.pivot_table(index='problema', columns='alg', values='igd_plus')
piv.to_csv(os.path.join(OUT, 'moead_igd_matriz_main.csv'))
sa = [c for c in piv.columns if c not in PISOS]
res = []
for p in piv.index:
    r = piv.loc[p]
    pisos = r[PISOS].dropna()
    rank_piso = int((pisos < pisos['moead']).sum()) + 1
    melhor_piso = pisos.idxmin()
    sav = r[sa].dropna()
    rank_geral = int((r.dropna() < r['moead']).sum()) + 1
    res.append(dict(problema=p, moead=r['moead'], nsga2=r.get('nsga2'), nsga3=r.get('nsga3'),
                    smsemoa=r.get('smsemoa'), rank_entre_pisos=rank_piso, melhor_piso=melhor_piso,
                    igd_melhor_piso=float(pisos.min()), n_algs=int(r.dropna().shape[0]),
                    rank_geral=rank_geral, n_sa_piores=int((sav > r['moead']).sum()), n_sa=int(sav.shape[0]),
                    banda_min=float(pisos.min()), banda_max=float(pisos.max()),
                    sa_dentro_banda=int(((sav >= pisos.min()) & (sav <= pisos.max())).sum())))
R = pd.DataFrame(res)
R.to_csv(os.path.join(OUT, 'moead_posicao.csv'), index=False)
print('\n', R.to_string())
print('\nrank entre os 4 pisos:', R.rank_entre_pisos.value_counts().sort_index().to_dict())
print('rank geral médio (de %s algs): %.2f' % (R.n_algs.max(), R.rank_geral.mean()))
print('mediana rank geral:', R.rank_geral.median())
print('melhor piso por problema:', R.melhor_piso.value_counts().to_dict())
print('média de SA abaixo (piores que) o moead: %.2f de %d' % (R.n_sa_piores.mean(), R.n_sa.max()))
