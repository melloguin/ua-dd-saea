#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T11/treed_media — 02: PRE-T11 (s42) x POS-T11 (smoke) na MESMA celula.
A celula sweep-big-mvns/ZDT4/42 existe nos dois corpora. READ-ONLY."""
import json, os, glob
import numpy as np, pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/treed_media/swap_big-mvns_ZDT4/42"
SMK = "/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/sweep-big-mvns/treed_media"
B = "exp_sweep-big-mvns_treed_media_ZDT4_42"
OUT = os.path.dirname(os.path.abspath(__file__))

def rd(root, suf):
    return pd.read_parquet(os.path.join(root, B + suf))

out = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)

for suf, nome in [("__real.parquet", "① real"), ("__surrogate.parquet", "③ surrogate"),
                  ("__timing.parquet", "④ timing"), ("__final.parquet", "⑦ final"),
                  ("__pop.parquet", "② pop")]:
    a = rd(S42, suf); b = rd(SMK, suf)
    same_cols = list(a.columns) == list(b.columns)
    same_shape = a.shape == b.shape
    P("\n--- %s ---  s42=%s  smoke=%s  colunas_iguais=%s" % (nome, a.shape, b.shape, same_cols))
    if not (same_shape and same_cols):
        P("   DIFERENTE em shape/colunas — colunas s42-only=%s smoke-only=%s" %
          (sorted(set(a.columns) - set(b.columns)), sorted(set(b.columns) - set(a.columns))))
        continue
    difs = []
    for c in a.columns:
        va, vb = a[c].to_numpy(), b[c].to_numpy()
        if va.dtype.kind in "fc":
            eq = np.array_equal(va, vb) or (np.isnan(va).all() and np.isnan(vb).all())
            if not eq:
                m = ~(np.isnan(va) & np.isnan(vb))
                d = np.nanmax(np.abs(va[m].astype(float) - vb[m].astype(float))) if m.any() else 0.0
                nd = int((va[m] != vb[m]).sum())
                difs.append("%s(ndif=%d,maxabs=%.3g)" % (c, nd, d))
        else:
            eq = a[c].equals(b[c])
            if not eq:
                difs.append("%s(ndif=%d)" % (c, int((a[c].astype(str) != b[c].astype(str)).sum())))
    P("   BIT-IDENTICO" if not difs else "   DIVERGE: " + " ".join(difs))

# manifesto / jsonl
m42 = json.load(open(os.path.join(S42, B + ".manifest.json")))
msk = json.load(open(os.path.join(SMK, B + ".manifest.json")))
P("\n--- ⑤ manifesto: chaves com VALOR diferente ---")
for k in sorted(set(m42) | set(msk)):
    a, b = m42.get(k, "<AUSENTE>"), msk.get(k, "<AUSENTE>")
    if k in ("created_at", "updated_at", "paths", "timing", "fit_series", "upload_status"):
        continue
    if json.dumps(a, sort_keys=True, default=str) != json.dumps(b, sort_keys=True, default=str):
        P("   %-18s s42=%s" % (k, json.dumps(a, ensure_ascii=False)[:110]))
        P("   %-18s smk=%s" % ("", json.dumps(b, ensure_ascii=False)[:110]))
P("   timing s42 = %s" % m42["timing"])
P("   timing smk = %s" % msk["timing"])
f42 = json.load(open(os.path.join(S42, B + "__final.manifest.json")))
fsk = json.load(open(os.path.join(SMK, B + "__final.manifest.json")))
P("   ⑦manif s42: n_final=%s n_nd=%s | smk: n_final=%s n_nd=%s" %
  (f42["n_final"], f42["n_nd_pos_real"], fsk["n_final"], fsk["n_nd_pos_real"]))

e42 = [json.loads(x) for x in open(os.path.join(S42, B + ".jsonl")) if x.strip()]
esk = [json.loads(x) for x in open(os.path.join(SMK, B + ".jsonl")) if x.strip()]
P("\n--- ⑥ eventos --- s42: %d %s | smoke: %d %s" %
  (len(e42), [e["rec"] for e in e42], len(esk), [e["rec"] for e in esk]))
ck = [e for e in esk if e["rec"] == "checkpoint"]
P("   checkpoints: n=%d  iteracoes=%s" % (len(ck), [e["iteracao"] for e in ck]))
P("   custo checkpoint: soma=%.4f s  (por ckpt %.4f–%.4f)  = %.1f%% do wall(%.3f s)" %
  (sum(e["tempo_checkpoint_s"] for e in ck), min(e["tempo_checkpoint_s"] for e in ck),
   max(e["tempo_checkpoint_s"] for e in ck),
   100 * sum(e["tempo_checkpoint_s"] for e in ck) / msk["timing"]["tempo_total_s"],
   msk["timing"]["tempo_total_s"]))
P("   n_linhas_terceira por ckpt = %s" % [e["n_linhas_terceira"] for e in ck])
# a serie de linhas por checkpoint recomposta da ③ (prova de que iteracao == geracao)
r3 = rd(SMK, "__surrogate.parquet"); bs = r3[r3.regime != "sonda"]
cum = bs.groupby("geracao").size().cumsum()
S = 20000
P("   ③ cumulativo(busca) em g=100,200,...,1000 (+%d sonda) = %s" %
  (S, [int(cum.loc[g]) + S for g in range(100, 1001, 100)]))
P("   CASA com n_linhas_terceira? %s" %
  all(int(cum.loc[g]) + S == e["n_linhas_terceira"] for g, e in zip(range(100, 1001, 100), ck)))
# footers
P("   footer s42: %s" % json.dumps({k: v for k, v in e42[-1].items() if k != "ts"}, ensure_ascii=False))
P("   footer smk: %s" % json.dumps({k: v for k, v in esk[-1].items() if k != "ts"}, ensure_ascii=False))

open(os.path.join(OUT, "tm11_prepos.txt"), "w").write("\n".join(out))
