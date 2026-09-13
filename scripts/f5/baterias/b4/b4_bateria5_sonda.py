#!/usr/bin/env python
"""B4 - Bateria 5: sonda. Cadencia + join posicional bit-a-bit + curva de APRENDIZADO
(AUC/acuracia por bloco contra o rotulo POR CONSTRUCAO, refs da propria geracao).
Substitui o WAPE (N/A por desenho: mu/sigma NULL num classificador puro).
"""
import json, os
import numpy as np
import pandas as pd

ROOT = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b4'
REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
OUT = REPO + '/f5/baterias/b4'
probs = sorted([p for p in os.listdir(ROOT) if os.path.isdir(f'{ROOT}/{p}')])

def auc(y, s):
    y = np.asarray(y, bool)
    if y.all() or (~y).any() == False or y.sum() == 0:
        return np.nan
    r = pd.Series(s).rank().to_numpy()
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

blocos, cells = [], []
for prob in probs:
    base = f'{ROOT}/{prob}/42/exp_main_b4_{prob}_42'
    recs = [json.loads(l) for l in open(base + '.jsonl') if l.strip()]
    gens = {int(r['geracao']): r for r in recs if r['rec'] == 'b4_gen'}
    sondas = [r for r in recs if r['rec'] == 'sonda']
    man = json.load(open(base + '.manifest.json'))
    real = pd.read_parquet(base + '__real.parquet')
    fc = [c for c in real.columns if c.startswith('f') and c[1:].isdigit()]
    F = real[fc].to_numpy(np.float64)
    art = pd.read_parquet(f'{REPO}/data/sonda/sonda_{prob}.parquet')
    axc = [c for c in art.columns if c.startswith('x') and c[1:].isdigit()]
    afc = [c for c in art.columns if c.startswith('f') and c[1:].isdigit()]
    S = int(man['sonda']['S'])
    Xa = art[axc].to_numpy(np.float64)[:S]
    Fa_s = art[afc].to_numpy(np.float64)[:S]

    xcols_s = [f'x{i}' for i in range(len(axc))]
    sur = pd.read_parquet(base + '__surrogate.parquet',
                          columns=['regime', 'geracao', 'pred_classe', 'pred_confianca', 'fe_treino_max'] + xcols_s)
    sd = sur[sur.regime == 'sonda']
    dmax_glob = 0.0
    gs = sorted(sd.geracao.unique().tolist())
    for i, gg in enumerate(gs):
        b = sd[sd.geracao == gg]
        d = float(np.abs(b[xcols_s].to_numpy(np.float64) - Xa).max()) if len(b) == S else np.nan
        dmax_glob = max(dmax_glob, d if d == d else 0.0)
        L = b['pred_confianca'].to_numpy(np.float64)
        cls = (b['pred_classe'].to_numpy() == 'bom')
        r = gens.get(int(gg))
        if r is None:
            lab = None
        else:
            R = F[np.array(r['ref_ids'], int)]
            lab = np.ones(S, bool)
            for j in range(len(R)):
                lab &= (Fa_s <= R[j]).any(axis=1)
        blocos.append(dict(problema=prob, bloco=i + 1, geracao=int(gg), n=len(b), dmaxX=d,
                           fe_treino_max=int(b['fe_treino_max'].iloc[0]),
                           frac_bom_pred=float(cls.mean()), L_med=float(np.median(L)),
                           L_min=float(L.min()), L_max=float(L.max()),
                           base_rate=(float(lab.mean()) if lab is not None else np.nan),
                           auc=(auc(lab, L) if lab is not None else np.nan),
                           acc=(float((lab == cls).mean()) if lab is not None else np.nan),
                           ghost=(r is None)))
    print('ok', prob, 'blocos', len(gs), 'dmaxX', dmax_glob)
    cells.append(dict(problema=prob, n_blocos=len(gs), dmaxX=dmax_glob))

B = pd.DataFrame(blocos)
B.to_csv(f'{OUT}/b4_sonda_blocos.csv', index=False)
print('\n=== JOIN POSICIONAL ===')
print('blocos:', len(B), ' max|dX| global:', B.dmaxX.max(), ' blocos com dX==0:', int((B.dmaxX == 0).sum()))
print('\n=== APRENDIZADO (AUC por bloco) ===')
ok = B[B.auc.notna()]
print(f'blocos com AUC computavel: {len(ok)}/{len(B)}   mediana {ok.auc.median():.4f}   >0.5 em '
      f'{100*(ok.auc>0.5).mean():.1f}%   >0.7 em {100*(ok.auc>0.7).mean():.1f}%')
res = B.groupby('problema').apply(lambda d: pd.Series({
    'blocos': len(d), 'auc_calc': int(d.auc.notna().sum()),
    'auc_1o': float(d.dropna(subset=['auc']).auc.iloc[0]) if d.auc.notna().any() else np.nan,
    'auc_ult': float(d.dropna(subset=['auc']).auc.iloc[-1]) if d.auc.notna().any() else np.nan,
    'auc_med': float(d.auc.median()), 'auc_q1': float(d.auc.quantile(.25)), 'auc_q3': float(d.auc.quantile(.75)),
    'frac_auc_gt05': float((d.auc > 0.5).mean()),
    'acc_med': float(d.acc.median()), 'base_med': float(d.base_rate.median()),
    'fracbom_1o': float(d.frac_bom_pred.iloc[0]), 'fracbom_ult': float(d.frac_bom_pred.iloc[-1]),
    'L_med_1o': float(d.L_med.iloc[0]), 'L_med_ult': float(d.L_med.iloc[-1]),
}), include_groups=False)
# tendencia 1o quartil vs 4o quartil de blocos
tend = []
for p, d in B.groupby('problema'):
    d = d.dropna(subset=['auc'])
    if len(d) < 4:
        tend.append((p, np.nan, np.nan)); continue
    q = len(d) // 4
    tend.append((p, float(d.auc.iloc[:q].mean()), float(d.auc.iloc[-q:].mean())))
T = pd.DataFrame(tend, columns=['problema', 'auc_q1blocos', 'auc_q4blocos']).set_index('problema')
res = res.join(T)
res['delta_auc'] = res.auc_q4blocos - res.auc_q1blocos
res.to_csv(f'{OUT}/b4_sonda_resumo.csv')
pd.set_option('display.width', 250)
print(res.round(4).to_string())
