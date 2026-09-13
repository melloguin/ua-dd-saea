#!/usr/bin/env python
"""bateria7_e81 — consolidacao: (1) inventario COMPLETO de registros do 6o layer por
celula (incl. os `guard` que a v1.0 nao viu e a anomalia de header/footer repetidos);
(2) reconciliacao U9 dos guards DI-25; (3) exemplares numericos citados no relatorio.

READ-ONLY. Saidas: e81_guards.csv · e81_anomalia_jsonl.csv · e81_inventario_rec.csv ·
e81_exemplares.txt
"""
import json, os
from collections import Counter
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/e81"
OUT = os.path.join(REPO, "f5", "baterias", "e81")


def cells():
    out = []
    for lab in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, lab, "42")
        if not os.path.isdir(d):
            continue
        exp = "batch" if lab.startswith("q10_") else "main"
        prob = lab[4:] if lab.startswith("q10_") else lab
        out.append((exp, prob, lab, d))
    return out


rows_inv, rows_gd, rows_an = [], [], []
for exp, prob, lab, d in cells():
    base = os.path.join(d, f"exp_{exp}_e81_{prob}_42")
    man = json.load(open(base + ".manifest.json"))
    objs = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    c = Counter(o.get("rec") for o in objs)
    hd = [o for o in objs if o.get("rec") == "header"]
    fo = [o for o in objs if o.get("rec") == "footer"]
    fo_run = [o for o in fo if "fe_final" in o]
    fo_desp = [o for o in fo if "fe_final" not in o]
    gu = [o for o in objs if o.get("rec") == "guard"]
    rows_inv.append(dict(label=lab, exp=exp, problema=prob, n_linhas=len(objs),
                         **{f"rec_{k}": v for k, v in c.items()},
                         n_header=len(hd), n_footer=len(fo), n_footer_runner=len(fo_run),
                         n_footer_desp=len(fo_desp), n_guard=len(gu),
                         guard_names=",".join(sorted({g.get("name", "?") for g in gu})),
                         header_extras=len(hd) - 1,
                         ts_primeiro=objs[0]["ts"], ts_ultimo=objs[-1]["ts"],
                         man_created=man.get("created_at"), man_updated=man.get("updated_at"),
                         anomalia=bool(len(hd) != 1 or len(fo) != 2)))
    for g in gu:
        rows_gd.append(dict(label=lab, **{k: v for k, v in g.items() if k != "rec"}))
    if len(hd) != 1 or len(fo) != 2:
        for h, f in zip(hd[1:], fo_desp):
            rows_an.append(dict(label=lab, header_ts=h["ts"], footer_ts=f["ts"],
                                run_id=h.get("run_id"), exp_hdr=h.get("exp"),
                                problema_hdr=h.get("problema"), modo_rapido=h.get("modo_rapido"),
                                D=h.get("D"), maxfe=h.get("maxfe"), n_init=h.get("n_init"),
                                versao=h.get("versao"), tempo_total_s=f.get("tempo_total_s"),
                                n_retries=f.get("n_retries"), status=f.get("status")))

pd.DataFrame(rows_inv).to_csv(f"{OUT}/e81_inventario_rec.csv", index=False)
pd.DataFrame(rows_gd).to_csv(f"{OUT}/e81_guards.csv", index=False)
pd.DataFrame(rows_an).to_csv(f"{OUT}/e81_anomalia_jsonl.csv", index=False)

inv = pd.DataFrame(rows_inv)
print("== INVENTARIO DO 6o LAYER ==")
print("celulas com header!=1 ou footer!=2:", int(inv["anomalia"].sum()),
      "->", inv.loc[inv["anomalia"], "label"].tolist())
print("celulas com guard:", int((inv["n_guard"] > 0).sum()), "-> total de guards:", int(inv["n_guard"].sum()))
print(inv[["label", "n_linhas", "n_header", "n_footer", "n_footer_runner", "n_footer_desp",
           "n_guard", "guard_names"]].to_string())

# ── exemplares numericos ──────────────────────────────────────────────────
txt = []
def P(s):
    txt.append(s); print(s)

# (i) query-joia: uma geracao concreta do MMF1
base = f"{ROOT}/MMF1/42/exp_main_e81_MMF1_42"
man = json.load(open(base + ".manifest.json"))
dec = [json.loads(l) for l in open(base + ".jsonl") if '"rec": "decision"' in l]
real = pd.read_parquet(base + "__real.parquet"); sur = pd.read_parquet(base + "__surrogate.parquet")
dm = json.load(open(f"{REPO}/data/doe/MMF1/doe_MMF1_42.manifest.json"))
xl = np.array(dm["bounds"]["xl"], float); xu = np.array(dm["bounds"]["xu"], float); rg = xu - xl
o = dec[9]
blk = sur[(sur.regime == "online") & (sur.geracao == o["geracao"])]
c01 = (blk[["x0", "x1"]].values.astype(float) - xl) / rg
X01 = (real[["x0", "x1"]].values.astype(float) - xl) / rg
dmin = cdist(c01, X01[:o["n_train"]]).min(1)
P("\n=== EXEMPLAR 1 — query-joia (MMF1, geracao %d) ===" % o["geracao"])
P("  bounds nativos MMF1: xl=%s xu=%s (NAO [0,1]^2)" % (xl.tolist(), xu.tolist()))
P("  n_front_acq=%d  n_train=%d  idx_escolhidos=%s" % (o["n_front_acq"], o["n_train"], o["idx_escolhidos"]))
P("  maximin_escolhido (log)      = %.17g" % o["maximin_escolhido"][0])
P("  maximin RECOMPUTADO em [0,1] = %.17g   |delta| = %.3e" %
  (dmin[o["idx_escolhidos"][0]], abs(dmin[o["idx_escolhidos"][0]] - o["maximin_escolhido"][0])))
P("  argmax do recomputo = %d (== idx_escolhido)  | 2o colocado = %.6f" %
  (int(np.argmax(dmin)), float(np.sort(dmin)[-2])))
dnat_full = cdist(blk[["x0", "x1"]].values.astype(float), real[["x0", "x1"]].values.astype(float)[:o["n_train"]]).min(1)
P("  mesmo recomputo em espaco NATIVO -> argmax = %d (dist=%.6f); dist_min_arquivo=%.6f" %
  (int(np.argmax(dnat_full)), float(dnat_full.max()), o["dist_min_arquivo"]))
P("  x do escolhido (nativo) = %s ; x da 1a linha da ③ = %s" %
  (np.round(blk[["x0", "x1"]].values[o["idx_escolhidos"][0]], 6).tolist(),
   np.round(blk[["x0", "x1"]].values[0], 6).tolist()))
P("  linha marcada na ③ (posicao) = %s" % np.where(blk["real_solution_id"].notna().values)[0].tolist())

# (ii) contrafactual B17.5 concreto
base = f"{ROOT}/q10_DTLZ2/42/exp_batch_e81_DTLZ2_42"
dec = [json.loads(l) for l in open(base + ".jsonl") if '"rec": "decision"' in l]
real = pd.read_parquet(base + "__real.parquet"); sur = pd.read_parquet(base + "__surrogate.parquet")
xc = [f"x{i}" for i in range(12)]
o = dec[2]
blk = sur[(sur.regime == "online") & (sur.geracao == o["geracao"])]
c01 = blk[xc].values.astype(float); X01 = real[xc].values.astype(float)
dmin = cdist(c01, X01[:o["n_train"]]).min(1)
topq = np.argsort(dmin, kind="stable")[-10:]
sel, cur = [], dmin.copy()
for _ in range(10):
    i = int(np.argmax(cur)); sel.append(i)
    cur = np.minimum(cur, cdist(c01, c01[i:i + 1]).ravel()); cur[i] = -np.inf
iu = np.triu_indices(10, 1)
P("\n=== EXEMPLAR 2 — B17.5 top-q x Eq.6-greedy (q10_DTLZ2, geracao %d) ===" % o["geracao"])
P("  front=%d  top-q (log)=%s" % (o["n_front_acq"], sorted(o["idx_escolhidos"])))
P("  top-q recomputado          =%s" % sorted(topq.tolist()))
P("  Eq.6-greedy (contrafactual)=%s" % sorted(sel))
P("  soma dos maximin: top-q=%.6f  greedy=%.6f (top-q maximiza a SOMA)" %
  (dmin[topq].sum(), dmin[sel].sum()))
P("  separacao mutua MINIMA do lote: top-q=%.6f  greedy=%.6f (greedy %.2fx mais disperso)" %
  (cdist(c01[topq], c01[topq])[iu].min(), cdist(c01[sel], c01[sel])[iu].min(),
   cdist(c01[sel], c01[sel])[iu].min() / cdist(c01[topq], c01[topq])[iu].min()))

# (iii) maior salto de aprendizado
e = pd.read_csv(f"{OUT}/e81_elo_causal.csv")
r = e.nsmallest(1, "maior_queda_wape").iloc[0]
P("\n=== EXEMPLAR 3 — maior salto de aprendizado (%s obj%d) ===" % (r["label"], r["obj"]))
P("  WAPE cai x%.1f num unico passo de bloco; lengthscale x%.2f; outputscale x%.3f" %
  (np.exp(-r["maior_queda_wape"]), np.exp(r["ls_no_maior_salto"]), np.exp(r["osc_no_maior_salto"])))
P("  ponta a ponta: lengthscale x%.2f, outputscale x%.3f" % (r["ls_razao"], r["osc_razao"]))

open(f"{OUT}/e81_exemplares.txt", "w").write("\n".join(txt))
print("\nescrito em", OUT)
