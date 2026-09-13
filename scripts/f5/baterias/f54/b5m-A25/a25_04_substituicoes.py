#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A25 / passo 2b — a sub-alegacao do analista: "a rejeicao do DI-10
(contagem de substituicoes do MOEA/D) esta empiricamente REFUTADA porque
reconstrui 356.137 grupos post-hoc da ③".

Testo se o que a ③ permite reconstruir E a contagem de substituicoes.
Fato do codigo (ProbMOEAD._next_gen): por geracao sao gerados EXATAMENTE
`population_size` offspring (1 por i); cada um chama do() e escreve em
len(selection) slots do vizinhado. A ③ guarda so a populacao PO'S-geracao.
Logo, da ③ so se ve o EFEITO LIQUIDO: slots cujo X final mudou.
Metricas por celula:
  pop, n_ger, offspring_gerados = pop*(n_ger-1)
  slots_mudados (soma sobre geracoes), grupos (X distintos novos)
  offspring_INVISIVEIS = offspring_gerados - grupos  (nao-distinguiveis entre
  "nao substituiu" e "substituiu e foi sobrescrito")
Saida: a25_substituicoes.csv
"""
import os, csv, numpy as np, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/b5m"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/b5m-A25"

rows, tot_grupos, tot_slots, tot_off = [], 0, 0, 0
labels = sorted(d for d in os.listdir(ROOT) if not d.startswith("."))
for lab in labels:
    d = os.path.join(ROOT, lab, "42")
    if not os.path.isdir(d):
        continue
    p = [f for f in os.listdir(d) if f.endswith("__surrogate.parquet")]
    if not p:
        continue
    t = pq.read_table(os.path.join(d, p[0]))
    cols = t.column_names
    xs = [c for c in cols if c.startswith("x") and c[1:].isdigit()]
    g = np.asarray(t.column("geracao"))
    reg = np.asarray(t.column("regime")) if "regime" in cols else None
    X = np.column_stack([np.asarray(t.column(c)) for c in xs])
    # so a BUSCA (a sonda tem geracao NULL -> vira nan/None)
    mask = np.array([gv is not None and gv == gv for gv in g])
    g = np.array([int(v) for v in g[mask]])
    X = X[mask]
    gers = np.unique(g)
    pops = {gg: X[g == gg] for gg in gers}
    pop = pops[gers[0]].shape[0]
    n_ger = len(gers)
    slots_mud, grupos, gmulti = 0, 0, 0
    tam_grupo = []
    for a, b in zip(gers[:-1], gers[1:]):
        A, B = pops[a], pops[b]
        if A.shape != B.shape:
            continue
        dif = np.any(A != B, axis=1)
        nd = int(dif.sum())
        slots_mud += nd
        if nd:
            novos = B[dif]
            _, inv, cnt = np.unique(novos, axis=0, return_inverse=True,
                                    return_counts=True)
            grupos += len(cnt)
            gmulti += int((cnt > 1).sum())
            tam_grupo += list(cnt)
    off_ger = pop * (n_ger - 1)          # 1 offspring por individuo por geracao
    rows.append(dict(
        celula=lab, pop=pop, n_ger=n_ger, offspring_gerados=off_ger,
        slots_mudados=slots_mud, grupos=grupos, grupos_multi_slot=gmulti,
        frac_multi=round(gmulti / grupos, 6) if grupos else None,
        tam_medio_grupo=round(float(np.mean(tam_grupo)), 4) if tam_grupo else None,
        offspring_invisiveis=off_ger - grupos,
        frac_invisivel=round(1 - grupos / off_ger, 6) if off_ger else None,
        turnover_medio=round(slots_mud / (pop * (n_ger - 1)), 6)))
    tot_grupos += grupos
    tot_slots += slots_mud
    tot_off += off_ger

with open(os.path.join(OUT, "a25_substituicoes.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    [w.writerow(r) for r in rows]

print("celulas: %d" % len(rows))
print("GRUPOS reconstruidos (soma 45 celulas): %d   [relatorio: 356.137]" % tot_grupos)
print("slots mudados (soma): %d" % tot_slots)
print("offspring GERADOS pelo motor (soma, = pop*(n_ger-1)): %d" % tot_off)
print("offspring INVISIVEIS na ③ (soma): %d  (%.2f%%)"
      % (tot_off - tot_grupos, 100 * (1 - tot_grupos / tot_off)))
mm = [r for r in rows if r["frac_multi"] is not None]
print("frac multi-slot (mediana): %.4f" %
      float(np.median([r["frac_multi"] for r in mm])))
print("\ntop-5 celulas por fracao invisivel:")
for r in sorted(rows, key=lambda r: -(r["frac_invisivel"] or 0))[:5]:
    print("  %-24s pop=%3d n_ger=%4d off=%6d grupos=%6d invis=%.3f turnover=%.3f"
          % (r["celula"], r["pop"], r["n_ger"], r["offspring_gerados"],
             r["grupos"], r["frac_invisivel"], r["turnover_medio"]))
print("\nbottom-5 (mais visiveis):")
for r in sorted(rows, key=lambda r: (r["frac_invisivel"] or 0))[:5]:
    print("  %-24s pop=%3d n_ger=%4d off=%6d grupos=%6d invis=%.3f turnover=%.3f"
          % (r["celula"], r["pop"], r["n_ger"], r["offspring_gerados"],
             r["grupos"], r["frac_invisivel"], r["turnover_medio"]))
print("\nOK ->", os.path.join(OUT, "a25_substituicoes.csv"))
