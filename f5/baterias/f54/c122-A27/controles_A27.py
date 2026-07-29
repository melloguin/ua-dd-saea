#!/usr/bin/env python
"""F5.4 c122-A27 — controles positivos/negativos + testes complementares.

C1  massa da distribuicao no bloco-1 (nao e outlier?)                [T-B]
C2  overhead absoluto do 1o bloco: t_g1 - (n_init/N)*t_med           [T-C fino]
C3  a ② do g=1 tem N linhas (a referencia do bloco-1 NAO e a ② exportada)
C4  o DoE (① fase=init) e recuperavel bit-a-bit => correcao pos-hoc possivel
C5  CONTROLE TRANSVERSAL: outros configs declaram sonda.n_ref? e ele bate?
"""
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos"
RAW = os.path.join(ROOT, "c122")
OUT = os.path.dirname(os.path.abspath(__file__))
SEED = "42"

rows = []
for prob in sorted(os.listdir(RAW)):
    d = os.path.join(RAW, prob, SEED)
    if not os.path.isdir(d):
        continue
    base = f"exp_main_c122_{prob}_{SEED}"
    mf = json.load(open(os.path.join(d, base + ".manifest.json")))
    N = int(mf["params"]["N_MU"])
    real = pq.read_table(os.path.join(d, base + "__real.parquet")).to_pandas()
    D = len([c for c in real.columns if c.startswith("x")])
    n_init = int((real.fase == "init").sum())
    sur = pq.read_table(os.path.join(d, base + "__surrogate.parquet"),
                        columns=["regime", "geracao", "pred_score",
                                 "pred_confianca"]).to_pandas()
    snd = sur[sur.regime == "sonda"]
    gs = sorted(snd.geracao.unique().tolist())
    v1 = snd[snd.geracao == gs[0]].pred_score.to_numpy(np.float64)
    v2 = snd[snd.geracao == gs[1]].pred_score.to_numpy(np.float64)
    c1 = snd[snd.geracao == gs[0]].pred_confianca.to_numpy(np.float64)
    pop = pq.read_table(os.path.join(d, base + "__pop.parquet")).to_pandas()
    n_pop_g1 = int((pop.geracao == gs[0]).sum())
    tim = pq.read_table(os.path.join(d, base + "__timing.parquet")).to_pandas()
    tim = tim[tim.tempo_pred_sonda_s > 0]
    t1 = float(tim[tim.geracao == gs[0]].tempo_pred_sonda_s.iloc[0])
    tmed = float(np.median(tim[tim.geracao != gs[0]].tempo_pred_sonda_s))
    # quantizacao: e(z) e soma de p_hat<=1 sobre a referencia; com conf~1 os
    # valores ficam quase inteiros. quanto "cabe" na referencia declarada?
    near_int = float(np.mean(np.abs(v1 - np.round(v1)) < 1e-3))
    rows.append(dict(
        problema=prob, D=D, N=N, n_init=n_init,
        # C1
        frac_gt_2N_b1=float(np.mean(v1 > 2 * N)),
        med_b1=float(np.median(v1)), p90_b1=float(np.percentile(v1, 90)),
        p99_b1=float(np.percentile(v1, 99)), max_b1=float(v1.max()),
        frac_gt0_b1=float(np.mean(v1 > 0)), frac_gt0_b2=float(np.mean(v2 > 0)),
        max_b2=float(v2.max()), razao_max_b1_b2=float(v1.max() / max(v2.max(), 1e-12)),
        med_b1_por_2N=float(np.median(v1) / (2 * N)),
        near_int_b1=near_int, conf_med_b1=float(np.nanmedian(c1)),
        # C2
        t_g1=t1, t_med=tmed, t_prev_H1=(n_init / N) * tmed,
        overhead_abs_s=t1 - (n_init / N) * tmed,
        t_por_ref_g1=t1 / n_init, t_por_ref_rest=tmed / N,
        # C3
        n_pop_g1=n_pop_g1, n_pop_g1_eq_N=bool(n_pop_g1 == N),
    ))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "A27_controles.csv"), index=False)
pd.set_option("display.width", 250)
print("=== C1 massa da distribuicao do bloco-1 ===")
print(df[["problema", "N", "n_init", "frac_gt_2N_b1", "med_b1", "p90_b1",
          "p99_b1", "max_b1", "max_b2", "razao_max_b1_b2", "frac_gt0_b1",
          "frac_gt0_b2"]].to_string(index=False))
print("\nmediana da frac>2N no bloco-1 (22 celulas discriminantes): "
      f"{df[df.max_b1 > 2*df.N].frac_gt_2N_b1.median():.3f}")
print("\n=== C2 custo por referencia (s / ponto-de-referencia / bloco de 2000) ===")
print(df[["problema", "D", "N", "n_init", "t_g1", "t_med", "t_prev_H1",
          "overhead_abs_s", "t_por_ref_g1", "t_por_ref_rest"]].to_string(index=False))
r = df.t_por_ref_g1 / df.t_por_ref_rest
print(f"\nt_por_ref(g1)/t_por_ref(g>=2): med={r.median():.3f} "
      f"min={r.min():.3f} max={r.max():.3f}   (1.0 = mesmo custo unitario "
      "=> a diferenca de tempo e SO o tamanho da referencia)")
print(f"overhead absoluto (s): med={df.overhead_abs_s.median():.3f} "
      f"min={df.overhead_abs_s.min():.3f} max={df.overhead_abs_s.max():.3f}")
print("\n=== C3 ② do g=1 ===")
print(f"celulas com |②(g1)| == N: {int(df.n_pop_g1_eq_N.sum())}/{len(df)}")
print("\n=== C4/C5 ver saida do bloco seguinte ===")

# C5 controle transversal: quais configs declaram sonda.n_ref?
print("\n=== C5 CONTROLE TRANSVERSAL (sonda.n_ref por config) ===")
achados = []
for cfg in sorted(os.listdir(ROOT)):
    dcfg = os.path.join(ROOT, cfg)
    if not os.path.isdir(dcfg):
        continue
    probs = sorted(os.listdir(dcfg))
    got = None
    for p in probs:
        dd = os.path.join(dcfg, p, SEED)
        if not os.path.isdir(dd):
            continue
        mans = [f for f in os.listdir(dd) if f.endswith(".manifest.json")]
        if not mans:
            continue
        m = json.load(open(os.path.join(dd, mans[0])))
        snd = m.get("sonda") or {}
        got = dict(config=cfg, exemplo=p,
                   n_ref=snd.get("n_ref"),
                   referencia=str(snd.get("referencia"))[:70],
                   chaves=",".join(sorted(snd.keys())))
        break
    if got:
        achados.append(got)
print(pd.DataFrame(achados).to_string(index=False))
