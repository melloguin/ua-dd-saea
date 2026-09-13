"""T11/nsga3 — bateria 9: a taxa de duplicata PREVISTA pelo codigo-fonte x a MEDIDA.
Modelo (lido de NSGAIII.m:29 + TournamentSelection.m:26-29 + OperatorGA.m:56-58,88-95):
  · o mating pool e' `randi(N,2,N)` com aptidao TODA ZERO (cons=0 nos 25 problemas)
    => selecao de pais UNIFORME COM REPOSICAO (NSGA-III stock nao usa torneio de crowding);
  · o pareamento e' posicional: Parent(1:floor(N/2)) x Parent(floor(N/2)+1:2*floor(N/2));
  · pais IDENTICOS => SBX devolve os dois filhos == pai;
  · PM muta cada variavel com prob proM/D = 1/D => o filho continua == pai com prob (1-1/D)^D.
  E[dup/geracao] = 2*floor(N/2) * (1/N) * (1-1/D)^D
READ-ONLY. Saida: dedup_modelo.csv
"""
import json, os, glob
import numpy as np
import pandas as pd

S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/nsga3"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"

rows = []
for prob in sorted(os.listdir(S42)):
    d = os.path.join(S42, prob, "42")
    if not os.path.isdir(d):
        continue
    base = glob.glob(os.path.join(d, "*.manifest.json"))[0][:-len(".manifest.json")]
    man = json.load(open(base + ".manifest.json"))
    recs = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    hdr = [r for r in recs if r.get("rec") == "header"][0]
    gens = [r for r in recs if r.get("rec") == "nsga3_gen"]
    ch = [r for r in recs if r.get("rec") == "guard" and r["name"] == "cache_hit"]
    D, M = hdr["D"], hdr["M"]
    init = 11 * D - 1
    Nef = man["params"]["N_efetivo"]
    n_off = 2 * (Nef // 2)
    fe_last = gens[-1]["fe"]
    dup = len([g for g in ch if init < g["fe"] <= fe_last])
    off = (len(gens) - 1) * n_off
    p_pai_igual = 1.0 / Nef
    p_sem_mutacao = (1 - 1.0 / D) ** D
    prev = off * p_pai_igual * p_sem_mutacao
    rows.append(dict(prob=prob, D=D, M=M, Nef=Nef, n_off=n_off, n_ger=len(gens),
                     off=off, dup=dup, taxa=100 * dup / off,
                     prev=prev, taxa_prev=100 * p_pai_igual * p_sem_mutacao))

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "dedup_modelo.csv"), index=False)
print(df.to_string(index=False))
print()
print("AGREGADO: dup medido = %d de %d descendentes (%.2f%%) · previsto = %.1f (%.2f%%)"
      % (df.dup.sum(), df.off.sum(), 100 * df.dup.sum() / df.off.sum(),
         df.prev.sum(), 100 * df.prev.sum() / df.off.sum()))
for m in (2, 3):
    g = df[df.M == m]
    print("  M=%d: medido %.2f%% (%d/%d) · previsto %.2f%%"
          % (m, 100 * g.dup.sum() / g.off.sum(), g.dup.sum(), g.off.sum(),
             100 * g.prev.sum() / g.off.sum()))
print("  correlacao previsto x medido (por celula): r = %.3f"
      % np.corrcoef(df.prev, df.dup)[0, 1])
