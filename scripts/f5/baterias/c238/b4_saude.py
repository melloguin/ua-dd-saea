#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 4: saude em escala.
(a) trajetorias de 20 checkpoints: violacoes de monotonicidade do IGD+;
(b) posicao vs os 4 pisos online e vs os 17 algs do main (rank);
(c) tempo/maquina.
Saidas: saude_celula.csv + rank_main.csv.
"""
import glob, json, os
import numpy as np, pandas as pd

F5 = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5"
OUT = f"{F5}/baterias/c238"
PISOS = ["nsga2", "nsga3", "moead", "smsemoa"]

met = pd.read_csv(f"{F5}/metricas_finais_f52c.csv")
main = met[met.exp == "main"]
tmp = pd.read_csv(f"{F5}/tempo_f52d.csv")

rows = []
for p in sorted(main[main.alg == "c238"].problema.unique()):
    m = main[(main.alg == "c238") & (main.problema == p)].iloc[0]
    sub = main[main.problema == p].sort_values("igd_plus")
    rank = int((sub.igd_plus.values < m.igd_plus).sum()) + 1
    pis = main[(main.problema == p) & (main.alg.isin(PISOS))]
    best_p = pis.loc[pis.igd_plus.idxmin()] if len(pis) else None
    traj = json.load(open(f"{F5}/trajetorias/main_c238_{p}_42.json"))
    v = np.array([c["igd_plus"] for c in traj], float)
    fe_cp = np.array([c["fe"] for c in traj], float)
    viol = int((np.diff(v) > 1e-12).sum())
    t = tmp[(tmp.alg == "c238") & (tmp.problema == p) & (tmp.exp == "main")]
    rows.append(dict(problema=p, igd_plus=m.igd_plus, hv=m.hv, igd=m.igd, gd=m.gd,
                     spacing=m.spacing, n_nd=m.n_nd,
                     rank_main=rank, n_algs=len(sub),
                     melhor_piso=best_p.alg if best_p is not None else None,
                     piso_igd=best_p.igd_plus if best_p is not None else np.nan,
                     razao=m.igd_plus / best_p.igd_plus if best_p is not None else np.nan,
                     bate_piso=bool(m.igd_plus < best_p.igd_plus) if best_p is not None else None,
                     n_cp=len(v), viol_monot=viol, fe_cp0=fe_cp[0], fe_cpN=fe_cp[-1], cp0=v[0], cpN=v[-1],
                     ganho=float(v[0] / max(v[-1], 1e-300)),
                     maquina=t.maquina.iloc[0] if len(t) else None,
                     wall_s=t.wall_s.iloc[0] if len(t) else np.nan))
S = pd.DataFrame(rows)
S.to_csv(f"{OUT}/saude_celula.csv", index=False)
print(S.to_string(index=False))
print("\nbate melhor piso:", int(S.bate_piso.sum()), "/", len(S),
      "| rank medio:", round(S.rank_main.mean(), 2), "de", S.n_algs.iloc[0],
      "| violacoes monot totais:", int(S.viol_monot.sum()),
      "| transicoes:", int((S.n_cp - 1).sum()))

# rank medio de todos os algs do main (contexto)
r = (main.assign(rk=main.groupby("problema").igd_plus.rank())
        .groupby("alg").rk.mean().sort_values())
r.to_csv(f"{OUT}/rank_main.csv")
print("\nrank medio IGD+ (main, 25 problemas):")
print(r.round(2).to_string())
