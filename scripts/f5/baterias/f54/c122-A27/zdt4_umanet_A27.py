#!/usr/bin/env python
"""F5.4 c122-A27 — o teste MAIS APERTADO: ZDT4 tem UMA rede so.

Em ZDT4 a theta-Net nunca nasce (s_net=None em 201/201). Logo, no
`_sonda_predict`, o laco `for net in (p_net, s_net)` soma UMA parcela apenas:
    e(z) = sum_j I(label=1)*p_hat  <=  1 * |referencia|
O teto deixa de ser 2*n_ref e passa a ser n_ref EXATO — um limite MUITO apertado.
    H0 (n_ref=N=11)      => max e(z) <= 11
    H1 (n_ref=11D-1=109) => max e(z) <= 109
"""
import json
import os

import numpy as np
import pyarrow.parquet as pq

D = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122/ZDT4/42"
B = "exp_main_c122_ZDT4_42"

pnet_g1 = snet_g1 = None
n_dec = n_s_null = 0
for line in open(os.path.join(D, B + ".jsonl")):
    d = json.loads(line)
    if d.get("rec") == "fit_inicial":
        pnet_g1, snet_g1 = d.get("p_net"), d.get("s_net")
    if d.get("rec") == "decisao" or d.get("caminho", "").startswith("c122_gen"):
        n_dec += 1
        if d.get("accs_s") is None:
            n_s_null += 1
print(f"fit_inicial: p_net={pnet_g1}  s_net={snet_g1}")
print(f"decisoes={n_dec}  com accs_s NULL (theta-Net inexistente)={n_s_null}")

sur = pq.read_table(os.path.join(D, B + "__surrogate.parquet"),
                    columns=["regime", "geracao", "pred_score",
                             "pred_confianca"]).to_pandas()
snd = sur[sur.regime == "sonda"]
gs = sorted(snd.geracao.unique())
v1 = snd[snd.geracao == gs[0]].pred_score.to_numpy(np.float64)
c1 = snd[snd.geracao == gs[0]].pred_confianca.to_numpy(np.float64)
rest = snd[snd.geracao != gs[0]].pred_score.to_numpy(np.float64)
n_init, N = 109, 11
print(f"\nbloco g={gs[0]}: max e(z) = {v1.max():.6f}")
print(f"   teto H0 (1 rede x N=11)        = {N}      -> excede em "
      f"{v1.max()/N:.2f}x   [{np.mean(v1 > N)*100:.1f}% dos 2000 pontos "
      "acima do teto H0]")
print(f"   teto H1 (1 rede x 11D-1=109)   = {n_init}     -> folga = "
      f"{n_init - v1.max():.6f}  ({100*v1.max()/n_init:.3f}% do teto)")
print(f"   conf mediana no bloco 1 = {np.nanmedian(c1):.6f}; "
      f"e(z)/conf no maximo = {v1.max()/np.nanmedian(c1):.3f}")
print(f"\nblocos g>=2: max e(z) = {rest.max():.6f}  (teto H0/H1 = N = {N}) -> "
      f"violacoes: {int((rest > N + 1e-9).sum())}/{len(rest)}")
# quantizacao: quantos niveis inteiros distintos aparecem no bloco 1?
niveis = np.unique(np.round(v1))
print(f"\nniveis inteiros distintos no bloco 1: {len(niveis)} "
      f"(min {niveis.min():.0f}, max {niveis.max():.0f})")
print("um unico ponto da sonda 'domina' ate "
      f"{v1.max()/np.nanmedian(c1):.1f} referencias — impossivel com 11.")
