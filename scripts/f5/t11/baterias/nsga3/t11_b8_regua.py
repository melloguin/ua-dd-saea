"""T11/nsga3 — bateria 8: o PAPEL DE REGUA, a partir dos insumos PRE-COMPUTADOS da F5.2
(nao recomputa metrica: le metricas_finais_f52c.csv / tempo_f52d.csv / integridade_f52a.csv).
READ-ONLY. Saida: regua_t11.csv
"""
import os
import numpy as np
import pandas as pd

F5 = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/nsga3"
PISOS = ["nsga2", "nsga3", "moead", "smsemoa"]
M3 = ["DTLZ1", "DTLZ2", "DTLZ3", "DTLZ4", "DTLZ7", "MMF16_20"]

m = pd.read_csv(os.path.join(F5, "metricas_finais_f52c.csv"))
m = m[m.exp == "main"]
t = pd.read_csv(os.path.join(F5, "tempo_f52d.csv"))
i = pd.read_csv(os.path.join(F5, "integridade_f52a.csv"))

# ranking entre os 4 pisos, por problema (IGD+ menor = melhor)
p = m[m.alg.isin(PISOS)].pivot(index="problema", columns="alg", values="igd_plus")
rk = p.rank(axis=1)
print("=== IGD+ entre os 4 pisos (%d problemas) ===" % len(p))
print("rank medio:", rk.mean().round(3).to_dict())
print("nsga3 melhor piso em %d/%d · pior em %d/%d"
      % (int((rk.nsga3 == 1).sum()), len(rk), int((rk.nsga3 == rk.max(axis=1)).sum()), len(rk)))
print("nsga3 bate moead em %d/%d" % (int((p.nsga3 < p.moead).sum()), len(p)))
print("rank medio nsga3 em M=3: %.2f · em M=2: %.2f"
      % (rk.loc[rk.index.isin(M3), "nsga3"].mean(), rk.loc[~rk.index.isin(M3), "nsga3"].mean()))

# spacing
sp = m[m.alg.isin(PISOS)].pivot(index="problema", columns="alg", values="spacing")
rs = sp.rank(axis=1)
print("\n=== spacing (uniformidade) ===")
print("rank medio:", rs.mean().round(3).to_dict())
print("nsga3 M=3 %.2f · M=2 %.2f" % (rs.loc[rs.index.isin(M3), "nsga3"].mean(),
                                     rs.loc[~rs.index.isin(M3), "nsga3"].mean()))

# nsga3 vs os SA (todos os configs main que nao sao piso nem sobol)
alg_all = sorted(m.alg.unique())
sa = [a for a in alg_all if a not in PISOS + ["sobol_batch"]]
print("\n=== nsga3 x SA-MOEA (%d configs SA) ===" % len(sa))
tot, win = 0, 0
por_prob = []
for prob, g in m.groupby("problema"):
    v = g.set_index("alg").igd_plus
    if "nsga3" not in v:
        continue
    base = v["nsga3"]
    pres = [a for a in sa if a in v.index and np.isfinite(v[a])]
    b = sum(1 for a in pres if v[a] < base)
    tot += len(pres); win += b
    por_prob.append(dict(problema=prob, n_sa=len(pres), sa_batem=b, igd_nsga3=base))
pp = pd.DataFrame(por_prob)
print("SA batem o nsga3 em %d/%d comparacoes = %.1f%%" % (win, tot, 100 * win / tot))
print(pp.sort_values("sa_batem").to_string(index=False))

# rank geral do nsga3 entre todos os configs main
rg = m.pivot(index="problema", columns="alg", values="igd_plus").rank(axis=1)
print("\nrank geral medio do nsga3 entre %d configs: %.2f (min %s, max %s)"
      % (rg.shape[1], rg.nsga3.mean(), rg.nsga3.min(), rg.nsga3.max()))

# e7 (o casamento)
if "e7" in m.alg.unique():
    pe = m[m.alg.isin(["nsga3", "e7"])].pivot(index="problema", columns="alg", values="igd_plus")
    pe = pe.dropna()
    print("e7 melhor que nsga3 em %d/%d (%.0f%%)" % (int((pe.e7 < pe.nsga3).sum()), len(pe),
                                                     100 * (pe.e7 < pe.nsga3).mean()))

# tempo / maquina
tn = t[t.alg == "nsga3"]
print("\n=== custo/maquina ===")
print("maquinas:", dict(tn.maquina.value_counts()))
print("wall total %.1f s (%.4f h-core) · mediana %.2f s" %
      (tn.wall_s.sum(), tn.wall_s.sum() / 3600, tn.wall_s.median()))
tp = t[t.alg.isin(PISOS)]
print("4 pisos: %.1f s = %.4f h-core" % (tp.wall_s.sum(), tp.wall_s.sum() / 3600))
tsa = t[t.alg.isin(sa)]
print("SA (%d configs): %.1f h-core" % (len(sa), tsa.wall_s.sum() / 3600))

# integridade
inn = i[i.alg == "nsga3"]
print("\n=== integridade F5.2a (nsga3) ===")
print(dict(inn.veredito.value_counts()), "· camadas:", dict(inn.camada.value_counts()))

pd.DataFrame({"rank_igd": rk.nsga3, "rank_spacing": rs.nsga3}).to_csv(
    os.path.join(OUT, "regua_t11.csv"))
