#!/usr/bin/env python
"""F5.4 — tentativa adversarial de REFUTAR o achado c122-A27.

Hipoteses:
  H0 (declarada): a referencia do e(z) da sonda tem tamanho FIXO n_ref = N (=MU)
      em TODOS os blocos  ==> teto aritmetico e(z) <= 2N em todo bloco.
  H1 (do analista): no bloco g=1 a referencia e a populacao NAO truncada do DoE
      (11D-1)  ==> teto e(z) <= 2*(11D-1) no bloco 1 e <= 2N nos demais.

Tres testes INDEPENDENTES entre si:
  T-A  teto aritmetico (livre de modelo)     : max e(z) por bloco vs 2N / 2*(11D-1)
  T-B  massa da distribuicao                 : fracao de pontos com e(z) > 2N
  T-C  custo computacional (ortogonal)       : tempo_pred_sonda_s(g=1) / mediana(g>=2)
                                               previsto por H1 = (11D-1)/N ; por H0 = 1
Escreve resultados em CSV no diretorio deste script. READ-ONLY nos dados.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAW = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122"
OUT = os.path.dirname(os.path.abspath(__file__))
SEED = "42"


def cells():
    for prob in sorted(os.listdir(RAW)):
        d = os.path.join(RAW, prob, SEED)
        if os.path.isdir(d):
            yield prob, d


def main():
    linhas, blocos_rows = [], []
    for prob, d in cells():
        base = f"exp_main_c122_{prob}_{SEED}"
        mf = json.load(open(os.path.join(d, base + ".manifest.json")))
        params = mf.get("params") or {}
        N = int(params["N_MU"])
        n_ref_decl = mf.get("sonda", {}).get("n_ref")
        real = pq.read_table(os.path.join(d, base + "__real.parquet")).to_pandas()
        D = len([c for c in real.columns if c.startswith("x")])
        M = len([c for c in real.columns if c.startswith("f")])
        n_init = int((real.fase == "init").sum())
        assert n_init == 11 * D - 1, (prob, n_init, D)

        sur = pq.read_table(os.path.join(d, base + "__surrogate.parquet"),
                            columns=["regime", "geracao", "pred_score",
                                     "pred_confianca"]).to_pandas()
        snd = sur[sur.regime == "sonda"]
        tim = pq.read_table(os.path.join(d, base + "__timing.parquet"),
                            columns=["geracao", "tempo_pred_sonda_s"]).to_pandas()
        tim = tim[tim.tempo_pred_sonda_s > 0]

        g_blocos = sorted(snd.geracao.unique().tolist())
        g1 = g_blocos[0]
        by = snd.groupby("geracao")
        for g, sub in by:
            v = sub.pred_score.to_numpy(np.float64)
            blocos_rows.append(dict(
                problema=prob, D=D, M=M, N=N, n_init=n_init, geracao=int(g),
                n_linhas=len(v), max_ez=float(np.nanmax(v)),
                med_ez=float(np.nanmedian(v)),
                frac_gt_2N=float(np.mean(v > 2 * N)),
                frac_gt_2ninit=float(np.mean(v > 2 * n_init)),
                frac_gt0=float(np.mean(v > 0)),
                excede_H0=bool(np.nanmax(v) > 2 * N + 1e-6),
                excede_H1=bool(np.nanmax(v) > 2 * n_init + 1e-6),
            ))
        b = pd.DataFrame([r for r in blocos_rows if r["problema"] == prob])
        b1 = b[b.geracao == g1].iloc[0]
        brest = b[b.geracao != g1]

        # T-C custo
        t1 = float(tim[tim.geracao == g1].tempo_pred_sonda_s.iloc[0]) if len(
            tim[tim.geracao == g1]) else np.nan
        trest = tim[tim.geracao != g1].tempo_pred_sonda_s.to_numpy(np.float64)
        tmed = float(np.median(trest)) if len(trest) else np.nan
        # 2o bloco isolado (para separar warm-up: o 2o tb e "cedo")
        g2 = g_blocos[1] if len(g_blocos) > 1 else None
        t2 = float(tim[tim.geracao == g2].tempo_pred_sonda_s.iloc[0]) if (
            g2 is not None and len(tim[tim.geracao == g2])) else np.nan

        linhas.append(dict(
            problema=prob, D=D, M=M, N=N, n_init=n_init, n_ref_decl=n_ref_decl,
            teto_H0=2 * N, teto_H1=2 * n_init, n_blocos=len(g_blocos),
            g1=int(g1), max_ez_g1=b1.max_ez, med_ez_g1=b1.med_ez,
            frac_gt_2N_g1=b1.frac_gt_2N,
            g1_excede_H0=bool(b1.excede_H0), g1_excede_H1=bool(b1.excede_H1),
            max_ez_grest=float(brest.max_ez.max()) if len(brest) else np.nan,
            n_blocos_rest_violam_H0=int(brest.excede_H0.sum()) if len(brest) else 0,
            n_blocos_rest=int(len(brest)),
            t_sonda_g1=t1, t_sonda_g2=t2, t_sonda_med_rest=tmed,
            razao_t_g1_med=(t1 / tmed if tmed and tmed > 0 else np.nan),
            razao_t_g1_g2=(t1 / t2 if t2 and t2 > 0 else np.nan),
            razao_prevista_H1=n_init / N,
        ))
        print(f"{prob:12s} D={D:2d} N={N:2d} n_init={n_init:3d} | "
              f"max_ez(g1)={b1.max_ez:9.3f} (2N={2*N}, 2n_init={2*n_init}) | "
              f"max_ez(g>=2)={(brest.max_ez.max() if len(brest) else float('nan')):8.3f} | "
              f"t_g1/t_med={t1/tmed if tmed else float('nan'):6.2f} "
              f"(prev H1 {n_init/N:5.2f})", flush=True)

    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(OUT, "A27_celulas.csv"), index=False)
    pd.DataFrame(blocos_rows).to_csv(os.path.join(OUT, "A27_blocos.csv"),
                                     index=False)

    print("\n=== VEREDITO DOS TESTES ===")
    print(f"celulas: {len(df)}")
    print(f"T-A  bloco-1 excede o teto H0 (2N): {int(df.g1_excede_H0.sum())}/{len(df)}")
    print(f"T-A  bloco-1 excede o teto H1 (2*(11D-1)): {int(df.g1_excede_H1.sum())}/{len(df)}"
          "   (esperado 0 sob H1)")
    print(f"T-A  blocos g>=2 que violam 2N: {int(df.n_blocos_rest_violam_H0.sum())}"
          f"/{int(df.n_blocos_rest.sum())}")
    print(f"T-C  razao t_g1/t_med  mediana={df.razao_t_g1_med.median():.2f}  "
          f"vs prevista H1 mediana={df.razao_prevista_H1.median():.2f}")
    r = df.dropna(subset=["razao_t_g1_med"])
    print(f"T-C  correlacao Pearson(razao_obs, razao_prevista) = "
          f"{np.corrcoef(r.razao_t_g1_med, r.razao_prevista_H1)[0,1]:.4f}")
    print(f"T-C  razao_obs/razao_prevista: min={(r.razao_t_g1_med/r.razao_prevista_H1).min():.3f} "
          f"med={(r.razao_t_g1_med/r.razao_prevista_H1).median():.3f} "
          f"max={(r.razao_t_g1_med/r.razao_prevista_H1).max():.3f}")
    print("\nD=2 (nao-discriminantes no teto):")
    print(df[df.D == 2][["problema", "N", "n_init", "max_ez_g1", "teto_H0",
                         "teto_H1", "razao_t_g1_med", "razao_prevista_H1"]]
          .to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
