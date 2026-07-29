#!/usr/bin/env python
"""F5.3b c238 (EIM) — BATERIA 6: agregados finais do relatorio (le os CSVs das baterias 1-5).
Nao recomputa dado bruto exceto theta/mu da sonda (degeneracao numerica) e ruido do eim_best.
Saida: agregados.txt (dump) + theta_traj.csv
"""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

BASE = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c238"
OUT = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/c238"
buf = []


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); buf.append(s)


E = pd.read_csv(f"{OUT}/estrutura_celula.csv")
G = pd.read_csv(f"{OUT}/eim_gens.csv")
SB = pd.read_csv(f"{OUT}/sonda_blocos.csv")
SJ = pd.read_csv(f"{OUT}/sonda_join.csv")

P("== TOTAIS ==")
P("celulas:", len(E), "| iteracoes(=gens):", int(E.n_gens.sum()),
  "| infills:", int(E.n_opt.sum()), "| FE reais:", int(E.n_real.sum()))
P("linhas (3) online:", int((E.n_gens * E.c9_ga_pop_decl).sum()),
  "| blocos de sonda:", int(E.n_blocos_sonda.sum()),
  "| linhas de sonda:", int((E.n_blocos_sonda * E.sonda_S).sum()),
  "| medicoes sonda(cel x bloco x obj):", len(SB))
P("aval. de aquisicao (GA):", int((E.n_gens * E.c9_aval_aquis_iter).sum()))

P("\n== QUERY-JOIA (identidade EIM_Euclidean, Apendice A) ==")
P("gens:", len(G), "| front reconstruido EXATO:", int(G.front_exato.sum()),
  f"({G.front_exato.mean():.4%})", "| dentro do bracket [nd_std/weak, nd_strict]:",
  int(G.front_bracket.sum()))
P("rel(max recomputado, eim_best) < 1e-5:", int((G.rel_max < 1e-5).sum()),
  f"({(G.rel_max<1e-5).mean():.4%})", "| mediana:", f"{G.rel_max.median():.3e}",
  "| p99:", f"{G.rel_max.quantile(.99):.3e}")
sub = G[G.front_exato]
P("  restrito as gens com front EXATO (n=%d): rel<1e-5 = %d (%.4f%%), mediana %.3e, max %.3e" %
  (len(sub), int((sub.rel_max < 1e-5).sum()), 100 * (sub.rel_max < 1e-5).mean(),
   sub.rel_max.median(), sub.rel_max.max()))
P("  gens com front NAO-exato (n=%d): rel<1e-5 = %d; celulas: %s" %
  (int((~G.front_exato).sum()), int((G[~G.front_exato].rel_max < 1e-5).sum()),
   G[~G.front_exato].problema.value_counts().to_dict()))
P("rel(EIM do infill, eim_best) < 1e-5:", int((G.rel_infill < 1e-5).sum()),
  "| mediana:", f"{G.rel_infill.median():.3e}")
P("argmax do pool == infill (exato):", int(G.argmax_eh_infill.sum()),
  f"({G.argmax_eh_infill.mean():.2%})")
P("gap relativo (max_pool - infill)/max_pool: ==0 em", int((G.gap_argmax <= 0).sum()),
  "| <1e-9 em", int((G.gap_argmax < 1e-9).sum()),
  "| <1e-6 em", int((G.gap_argmax < 1e-6).sum()),
  "| maximo global:", f"{G.gap_argmax.max():.3e}")
P("rel(mediana do pool recomputada, eim_mediana_pool) < 1e-5:", int((G.rel_med < 1e-5).sum()),
  "| mediana:", f"{G.rel_med.median():.3e}")
P("frente ND: min", int(G.n_front.min()), "max", int(G.n_front.max()),
  "mediana", float(G.n_front.median()), "| gens com n_front==1 (crash latente stock):",
  int((G.n_front == 1).sum()))

P("\n== CLONES NO POOL (anti-clustering AUSENTE, B10.7) ==")
cl = G.groupby("problema").apply(lambda x: pd.Series(
    dict(clones=int(x.pool_clones.sum()), linhas=int(x.pool_n.sum()),
         share=float(x.pool_clones.sum() / x.pool_n.sum()),
         gens_com_clone=int((x.pool_clones > 0).sum()), n=len(x))), include_groups=False)
P(cl.sort_values("share", ascending=False).head(8).to_string())
P("total clones:", int(cl.clones.sum()), "de", int(cl.linhas.sum()), "linhas de pool",
  f"({cl.clones.sum()/cl.linhas.sum():.4%})")
P("min_dist_infill: minimo global", f"{E.c12_mindist_min.min():.3e}",
  "| gens com dist<1e-8:", int(E.c12_mindist_lt1e8.sum()),
  "| celulas com dist<1e-6:", int((E.c12_mindist_min < 1e-6).sum()))

P("\n== U11 erro de fantasia do infill (espaco do MODELO, [0,1] da iteracao) ==")
P("(recomputado abaixo)")

P("\n== SONDA ==")
P("U5 join posicional: max|dX| por celula (float32 ULP x escala dos bounds):")
P(SJ[["problema", "D", "u5_dx_max"]].sort_values("u5_dx_max", ascending=False).head(6).to_string(index=False))
P("U6 confronto com f5/sonda_f52e.csv: ver rodape do b3 (maxdif WAPE 5,0e-7; cobertura 0,0)")
P("WAPE mediano 1o->ultimo bloco (por celula):")
P(SJ[["problema", "wape_1", "wape_n", "dwape", "corr_1", "corr_n", "cob_1", "cob_n", "mu_max"]]
  .to_string(index=False))
P("celulas que MELHORAM WAPE:", int((SJ.dwape < 0).sum()), "/", len(SJ),
  "| dWAPE mediano:", f"{SJ.dwape.median():.3f}")
P("cobertura mediana 1o bloco:", f"{SJ.cob_1.median():.3f}", "-> ultimo:", f"{SJ.cob_n.median():.3f}",
  "| celulas com cob_n < 0.90:", int((SJ.cob_n < .90).sum()),
  "| >= 0.90:", int((SJ.cob_n >= .90).sum()))

# DTLZ2 por objetivo (prior 7,5 v2)
d2 = SB[(SB.problema == "DTLZ2")]
P("\nDTLZ2 por objetivo (prior 7,5 v2: 'f2 8,1%->0,9%, cobertura ->0,95'):")
for j in sorted(d2.obj.unique()):
    x = d2[d2.obj == j].sort_values("bloco")
    P(f"  obj{j}: WAPE {x.wape.iloc[0]:.4f} -> {x.wape.iloc[-1]:.4f} | "
      f"cob {x.cob.iloc[0]:.3f} -> {x.cob.iloc[-1]:.3f} | corr {x.correl.iloc[0]:.3f} -> {x.correl.iloc[-1]:.3f}")
m1 = SB[SB.problema == "MMF1"]
P("MMF1 (prior: degeneracao numerica no fim; mu ate 339):")
for j in sorted(m1.obj.unique()):
    x = m1[m1.obj == j].sort_values("bloco")
    P(f"  obj{j}: WAPE {x.wape.iloc[0]:.4f} -> {x.wape.iloc[-1]:.4f} | "
      f"|mu|max no ultimo bloco {x.mu_max.iloc[-1]:.2f} | |mu|max global {x.mu_max.max():.2f} | "
      f"cob {x.cob.iloc[0]:.3f} -> {x.cob.iloc[-1]:.3f}")

# theta: trajetoria e saturacao
P("\n== THETA (MLE fmincon sqp single-start, bounds [1e-3,1e3]) ==")
rows = []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    gens = [json.loads(l) for l in open(f"{b}.jsonl") if '"c238_gen"' in l]
    tmin = np.array([r["theta_min"] for r in gens], float)
    tmax = np.array([r["theta_max"] for r in gens], float)
    tmed = np.array([r["theta_media"] for r in gens], float)
    lnl = np.array([r["lnL"] for r in gens], float)
    rows.append(dict(problema=prob, n_gens=len(gens), M=tmin.shape[1],
                     theta_min=float(tmin.min()), theta_max=float(tmax.max()),
                     sat_lb=int((np.abs(tmin - 1e-3) < 1e-12).sum()),
                     sat_ub=int((np.abs(tmax - 1e3) < 1e-6).sum()),
                     viola=int((tmin < 1e-3 - 1e-15).sum() + (tmax > 1e3 + 1e-9).sum()),
                     theta_med_ini=float(np.median(tmed[0])), theta_med_fim=float(np.median(tmed[-1])),
                     lnL_ini=float(np.median(lnl[0])), lnL_fim=float(np.median(lnl[-1])),
                     lnL_max=float(lnl.max()), comps=int(tmin.size)))
T = pd.DataFrame(rows)
T.to_csv(f"{OUT}/theta_traj.csv", index=False)
P(T.to_string(index=False))
P("violacoes de bound:", int(T.viola.sum()), "| saturacoes no piso 1e-3:", int(T.sat_lb.sum()),
  "| no teto 1e3:", int(T.sat_ub.sum()), "| componentes-geracao:", int(T.comps.sum()))

# ruido do eim_best (DI-18) e decaimento do pool (DI-10)
P("\n== eim_best RUIDOSO (DI-18: re-escala muda por iteracao) e eim_mediana_pool (DI-10) ==")
rows = []
for prob in sorted(os.listdir(BASE)):
    b = f"{BASE}/{prob}/42/exp_main_c238_{prob}_42"
    gens = [json.loads(l) for l in open(f"{b}.jsonl") if '"c238_gen"' in l]
    eb = np.array([r["eim_best"] for r in gens])
    em = np.array([r["eim_mediana_pool"] for r in gens])
    rg = np.array([r["norm_range_efetivo"] for r in gens], float)
    drg = np.abs(np.diff(rg, axis=0)) / np.maximum(rg[:-1], 1e-300)
    subiu = np.diff(eb) > 0
    rows.append(dict(problema=prob, n=len(eb), subidas=int(subiu.sum()),
                     frac_subidas=float(subiu.mean()),
                     salto_max=float((np.diff(eb) / np.maximum(eb[:-1], 1e-300)).max()),
                     range_var_med=float(np.median(drg)), range_var_max=float(drg.max()),
                     gens_range_muda=int((drg.max(1) > 1e-12).sum()),
                     eb_ini=float(eb[0]), eb_fim=float(eb[-1]), eb_min=float(eb.min()),
                     razao_med_best_ini=float(em[0] / max(eb[0], 1e-300)),
                     razao_med_best_fim=float(em[-1] / max(eb[-1], 1e-300)),
                     decai_pool=float(em[-1] / max(em[0], 1e-300))))
R = pd.DataFrame(rows)
R.to_csv(f"{OUT}/eim_ruido.csv", index=False)
P(R.to_string(index=False))
P("gens em que o range de y MUDOU:", int(R.gens_range_muda.sum()), "de", int((R.n - 1).sum()),
  f"({R.gens_range_muda.sum()/(R.n-1).sum():.1%})")
P("subidas de eim_best (nao-monotonicidade):", int(R.subidas.sum()), "de", int((R.n - 1).sum()),
  f"({R.subidas.sum()/(R.n-1).sum():.1%})")

open(f"{OUT}/agregados.txt", "w").write("\n".join(buf))
