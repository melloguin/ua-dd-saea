#!/usr/bin/env python3
"""T11/F5-bis — endpoint (⑦), ②/decay, elitismo e a NOVA identidade
`origem_solution_id` da ⑦ ≡ `n_ds_membros` da última geração do ⑥.

READ-ONLY. Usa `src/metrics.py` oficial (gate D92 antes de qualquer número).
Saídas em f5/t11/baterias/e103/.
"""
from __future__ import annotations
import os, sys, json, glob
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = '/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea'
RES = '/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos'
OUT = os.path.join(REPO, 'f5', 't11', 'baterias', 'e103')
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import metrics  # noqa: E402

v = metrics.hv_smoke_bbob_f1()
assert abs(v - 1.04333) < 5e-6, 'GATE D92 FALHOU: %r' % v
print('gate D92 OK: %.5f' % v, flush=True)


def load_jsonl(p):
    out = []
    for line in open(p, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


rows = []
root = os.path.join(RES, 'e103')
for lab in sorted(os.listdir(root)):
    d = os.path.join(root, lab, '42')
    if not os.path.isdir(d):
        continue
    base = [f for f in os.listdir(d) if f.endswith('.manifest.json')
            and not f.endswith('__final.manifest.json')][0][:-len('.manifest.json')]
    P = os.path.join(d, base)
    man = json.load(open(P + '.manifest.json'))
    prob = man['problema']
    evs = load_jsonl(P + '.jsonl')
    gens = sorted([e for e in evs if e['rec'] == 'e103_gen'], key=lambda e: e['geracao'])
    R = metrics.reference_set(prob)
    r = dict(label=lab, problema=prob, tier=man['dataset']['tier'],
             dist=man['dataset']['dist'], n_dataset=man['dataset']['n'],
             kflag_lider=gens[0].get('modelo_lider'))

    # ---- ⑦ ----
    fin = pq.read_table(P + '__final.parquet').to_pandas()
    fc = sorted([c for c in fin if c.startswith('f') and c[1:].isdigit()],
                key=lambda s: int(s[1:]))
    nd = fin['nd_pos_real'].to_numpy(bool)
    m_all = metrics.metrics_of_set(fin[fc].to_numpy(float), prob, ref_norm=R)
    m_nd = metrics.metrics_of_set(fin[fc].to_numpy(float)[nd], prob, ref_norm=R)
    r.update(n_final=len(fin), n_nd=int(nd.sum()), fantasia=float(nd.mean()),
             igd_plus_7=m_all['igd_plus'], hv_7=m_all['hv'],
             igd_plus_7_nd=m_nd['igd_plus'], hv_7_nd=m_nd['hv'])

    # ---- dataset como baseline (a ①) ----
    t1 = pq.read_table(P + '__real.parquet').to_pandas()
    f1c = sorted([c for c in t1 if c.startswith('f') and c[1:].isdigit()],
                 key=lambda s: int(s[1:]))
    m_ds = metrics.metrics_of_set(t1[f1c].to_numpy(float), prob, ref_norm=R)
    r['igd_plus_dataset'] = m_ds['igd_plus']
    r['ganho_rel'] = (m_ds['igd_plus'] - m_all['igd_plus']) / m_ds['igd_plus']

    # ---- ② / decay / identidade nova ----
    t2 = pq.read_table(P + '__pop.parquet').to_pandas()
    ndsm = [g.get('n_ds_membros') for g in gens]
    r['pop_linhas'] = len(t2)
    r['soma_n_ds_membros'] = int(sum(x or 0 for x in ndsm))
    r['pop_eq_soma'] = (len(t2) == r['soma_n_ds_membros'])
    r['ndsm_g1'] = ndsm[0]
    r['ndsm_g99'] = ndsm[-1]
    r['ndsm_zera_em'] = next((g['geracao'] for g in gens if (g.get('n_ds_membros') or 0) == 0), None)
    r['orig_sid_naonulo'] = int(fin['origem_solution_id'].notna().sum())
    r['IDENT_sid_eq_ndsm99'] = (r['orig_sid_naonulo'] == (ndsm[-1] or 0))

    # ---- elitismo / n_front1 ----
    r['nfront1_g1'] = gens[0].get('n_front1')
    r['nfront1_g99'] = gens[-1].get('n_front1')
    rows.append(r)
    print('.', end='', flush=True)

print()
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 't11_e103_endpoint.csv'), index=False)
print('IDENT_sid_eq_ndsm99:', df.IDENT_sid_eq_ndsm99.value_counts().to_dict())
print('pop_eq_soma       :', df.pop_eq_soma.value_counts().to_dict())
print('n_final           :', df.n_final.value_counts().to_dict())
print()
print(df[['label', 'kflag_lider', 'n_nd', 'fantasia', 'igd_plus_7',
          'igd_plus_dataset', 'ganho_rel', 'ndsm_g99', 'orig_sid_naonulo',
          'IDENT_sid_eq_ndsm99']].round(5).to_string())
