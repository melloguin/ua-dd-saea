#!/usr/bin/env python
"""B4 - Bateria 3: gate de 4 ramos, particao 75/25 (MATLAB round), lote, stalls,
RefSelect (1a ref = argmin Con), projecao radial M=2, e o corte-limpo da regra de rotulo.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
OUT = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])

def mround(x):  # MATLAB round: half away from zero
    return np.floor(np.abs(x) + 0.5) * np.sign(x)

G = pd.read_pickle(f'{OUT}/b4_geracoes.pkl')
RR = pd.read_csv(f'{OUT}/b4_regra_rotulo.csv')
G = G.merge(RR, on=['problema', 'geracao'], how='left')

# ---------- corte limpo da regra de rotulo: so geracoes sem empate alem das 6 refs ----------
lim = G[G.n_empate == 6]
print('=== REGRA DE ROTULO — corte limpo (n_empate==6, i.e. so as auto-comparacoes das K=6 refs) ===')
print(f'geracoes limpas: {len(lim)}/{len(G)}  match regra <=: {int((lim.n1_le==lim.n1log).sum())}/{len(lim)}'
      f'  ({100*(lim.n1_le==lim.n1log).mean():.3f}%)')
print('celulas com >=1 geracao limpa:', lim.problema.nunique())
print(lim.groupby('problema').apply(lambda d: pd.Series({'lim': len(d), 'ok': int((d.n1_le == d.n1log).sum())}),
                                    include_groups=False).to_string())

# ---------- particao 75/25 (Alg.5) ----------
nt = G.n_treino.to_numpy(float); n1 = G.n1log.to_numpy(float); n0 = nt - n1
pred_r = mround(0.75 * n0) + mround(0.75 * n1)
pred_f = np.floor(0.75 * n0) + np.floor(0.75 * n1)
pred_c = np.ceil(0.75 * n0) + np.ceil(0.75 * n1)
pred_tot = mround(0.75 * nt)
G['part_round'] = (G.n_acumulado.to_numpy() == pred_r)
G['part_floor'] = (G.n_acumulado.to_numpy() == pred_f)
G['part_ceil'] = (G.n_acumulado.to_numpy() == pred_c)
G['part_tot'] = (G.n_acumulado.to_numpy() == pred_tot)
print('\n=== PARTICAO 75/25 (n_acumulado = |Dtrain|) ===')
for c in ['part_round', 'part_floor', 'part_ceil', 'part_tot']:
    print(f'  {c:11s}: {int(G[c].sum())}/{len(G)} ({100*G[c].mean():.2f}%)')
print('  n_acumulado == n_treino_fit (modelo_hp):', int((G.n_acumulado == G.n_treino_fit).sum()), '/', len(G))
print('  n_acumulado < n_treino (subamostra) :', int((G.n_acumulado < G.n_treino).sum()), '/', len(G))
print('  razao n_acumulado/n_treino: med', round(float((G.n_acumulado/G.n_treino).median()), 5),
      'min', round(float((G.n_acumulado/G.n_treino).min()), 5), 'max', round(float((G.n_acumulado/G.n_treino).max()), 5))

# ---------- gate de ramos ----------
print('\n=== GATE DE 4 RAMOS ===')
print(G.ramo.value_counts().to_string())
p0 = G.p0.to_numpy(float); p1 = G.p1.to_numpy(float); tr = G.tr.to_numpy(float)
condR1 = (p1 < tr) | ((p0 < tr) & (p1 < 1 - tr))
condR3 = (p0 > 1 - tr) & (p1 > tr)
G['condR1_paper'] = condR1; G['condR3_paper'] = condR3
print('\nramo x condicao R1 do paper (p2<tr OR (p1<tr AND p2<1-tr)):')
print(pd.crosstab(G.ramo, condR1).to_string())
print('\nramo x condicao R3 do paper (p1>1-tr AND p2>tr):')
print(pd.crosstab(G.ramo, condR3).to_string())
# candidatas ao 0.4 hardcoded
for nome, cond in [('p0<0.4', p0 < 0.4), ('p1<0.4', p1 < 0.4), ('p0>0.4', p0 > 0.4), ('p1>0.4', p1 > 0.4),
                   ('p1<0.4 & p0<0.4', (p1 < 0.4) & (p0 < 0.4)),
                   ('p1<0.4 | R1', (p1 < 0.4) | condR1)]:
    ct = pd.crosstab(G.ramo, cond)
    ok = (G.ramo == 1) == cond
    print(f'  cond {nome:18s} -> concorda com (ramo==1) em {100*ok.mean():6.2f}%')
print('\nestatistica p0/p1/tr por ramo:')
print(G.groupby('ramo')[['p0', 'p1', 'tr', 'rr', 'lote']].describe().T.to_string())

# ---------- lote / stalls ----------
print('\n=== LOTE por ramo ===')
print(pd.crosstab(G.ramo, G.lote).to_string())
print('\nramo 4 com lote != 1:', int(((G.ramo == 4) & (G.lote != 1)).sum()))
print('ramo 1 com lote > 12:', int(((G.ramo == 1) & (G.lote > 12)).sum()))
print('stalls (lote==0) por ramo:', G[G.lote == 0].ramo.value_counts().to_dict())

# ---------- motivos textuais ----------
G['motivo_tpl'] = G.motivo.str.replace(r'[-+0-9.]+', '#', regex=True)
print('\n=== TEMPLATES DE MOTIVO ===')
print(G.groupby(['ramo', 'motivo_tpl']).size().to_string())

G.to_pickle(f'{OUT}/b4_geracoes_enriq.pkl')
G.drop(columns=['ref_ids']).to_csv(f'{OUT}/b4_geracoes_enriq.csv', index=False)

# ---------- RefSelect: 1a ref = argmin Con(P) ----------
print('\n=== REFSELECT (Alg.1 L3-4: 1a ref = argmin ||(f-fmin)/(fmax-fmin)||) ===')
res = []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = [r for r in recs if r['rec'] == 'b4_gen']
    real = pd.read_parquet(base + '__real.parquet')
    pop = pd.read_parquet(base + '__pop.parquet')
    fc = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    F = real[fc].to_numpy(np.float64)
    popsets = {int(k): v.to_numpy() for k, v in pop.groupby('geracao')['solution_id']}
    ok_arg = 0; ok_sub = 0; n = 0; tam = []
    for r in gens:
        ids = popsets.get(int(r['geracao']))
        if ids is None:
            continue
        n += 1; tam.append(len(ids))
        Fp = F[ids]
        lo, hi = Fp.min(0), Fp.max(0)
        rg = np.where(hi - lo > 1e-6, hi - lo, 1.0)
        con = np.linalg.norm((Fp - lo) / rg, axis=1)
        if ids[int(np.argmin(con))] == r['ref_ids'][0]:
            ok_arg += 1
        if set(r['ref_ids']).issubset(set(ids.tolist())):
            ok_sub += 1
    res.append(dict(problema=prob, n=n, ref1_argmin_Con=ok_arg, refs_subset_camada2=ok_sub,
                    tam2_med=float(np.median(tam))))
rs = pd.DataFrame(res)
rs.to_csv(f'{OUT}/b4_refselect.csv', index=False)
print(rs.to_string())
print('TOTAL: ref1==argmin(Con) em', rs.ref1_argmin_Con.sum(), '/', rs.n.sum(),
      f'({100*rs.ref1_argmin_Con.sum()/rs.n.sum():.1f}%)')
