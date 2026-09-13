#!/usr/bin/env python
"""BATERIA 5 — c154 (JES): cache_hit (D57) bit-a-bit, off-by-one dos warnings,
escada rs por degrau, fantasia absoluta x sonda absoluta."""
import json, os, re
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")
PROBS = sorted([p for p in os.listdir(ROOT) if not p.startswith('.')])

# ---------- A. cache_hit do MMF11_L: prova bit-a-bit ----------
base = f"{ROOT}/MMF11_L/42/exp_main_c154_MMF11_L_42"
L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
dec = [r for r in L if r.get("rec") == "decision"]
print("=== A. MMF11_L — as 2 iteracoes de cache_hit (D57)")
rows = []
for d in dec:
    hp = d.get("modelo_hp", {}).get("por_objetivo", [{}, {}])
    rows.append(dict(it=d["it"], caminho=d.get("caminho"), fe=d.get("fe"),
                     n_train=d.get("n_train"), cache_hit=d.get("cache_hit"),
                     sol=d.get("solution_id"),
                     dist=d.get("dist_min_arquivo"),
                     ls0=hp[0].get("lengthscale_med"), ls1=hp[1].get("lengthscale_med"),
                     noise0=hp[0].get("noise"), noise1=hp[1].get("noise"),
                     mll=d.get("modelo_hp", {}).get("mll_final"),
                     acqf=d.get("acqf_escolhido")))
Rm = pd.DataFrame(rows)
Rm.to_csv(os.path.join(OUT, "c154_MMF11L_cachehit.csv"), index=False)
print(Rm[(Rm.it >= 35) & (Rm.it <= 42)].to_string(index=False))
ch = Rm[Rm.cache_hit == True]
print("\niteracoes com cache_hit:", ch.it.tolist(), "| dist_min_arquivo:",
      ch.dist.tolist(), "| solution_id:", ch.sol.tolist())
for it in ch.it.tolist():
    a = Rm[Rm.it == it - 1].iloc[0]; b = Rm[Rm.it == it].iloc[0]
    c = Rm[Rm.it == it + 1].iloc[0]
    print(f"  it {it-1}->{it}: n_train {a.n_train}->{b.n_train} | fe {a.fe}->{b.fe} | "
          f"mll {a.mll:.12g} -> {b.mll:.12g} (igual={a.mll==b.mll}) | "
          f"ls0 igual={a.ls0==b.ls0} ls1 igual={a.ls1==b.ls1}")
    print(f"  it {it}->{it+1}: mll {b.mll:.12g} -> {c.mll:.12g} (igual={b.mll==c.mll}) | "
          f"acqf {b.acqf:.12g} -> {c.acqf:.12g} (igual={b.acqf==c.acqf})")

# ---------- B. off-by-one dos optimize_acqf_warning ----------
print("\n=== B. reconciliacao dos optimize_acqf_warning (U9)")
rr = []
for prob in PROBS:
    b = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    Ls = [json.loads(l) for l in open(b + ".jsonl") if l.strip()]
    dd = [r for r in Ls if r.get("rec") == "decision"]
    ww = [r for r in Ls if r.get("rec") == "optimize_acqf_warning"]
    n_ger = len(dd)
    rr.append(dict(problema=prob, n_recs=sum(r.get("n", 1) for r in ww),
                   n_linhas=len(ww),
                   soma_campo=sum(r.get("acqf_warnings", 0) for r in dd),
                   warn_na_hardstop=sum(1 for r in ww if r["it"] == n_ger),
                   campo_na_hardstop="acqf_warnings" in dd[-1],
                   pct_its_com_warning=100.0 * len({r["it"] for r in ww}) / n_ger))
W = pd.DataFrame(rr)
W["delta"] = W.n_linhas - W.soma_campo
W.to_csv(os.path.join(OUT, "c154_warnings.csv"), index=False)
print(W.to_string())

# ---------- C. escada rs por degrau ----------
print("\n=== C. escada rs_runtimeerror_fallback por degrau (DI-11 §3)")
al = []
for prob in PROBS:
    b = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    Ls = [json.loads(l) for l in open(b + ".jsonl") if l.strip()]
    for r in Ls:
        if r.get("rec") == "rs_runtimeerror_fallback":
            r = dict(r); r["problema"] = prob; al.append(r)
F = pd.DataFrame(al)
if len(F):
    F.to_csv(os.path.join(OUT, "c154_escada_rs.csv"), index=False)
    print(F.groupby(["problema", "degrau_falho", "pop_size", "max_tries"]).size()
          .rename("n").reset_index().to_string())
    print("\nits distintas com >=1 falha, por celula:")
    print(F.groupby("problema")["it"].nunique().to_string())
    print("\nfaltantes declarados no erro (K de 'Only found K instead of 10'):")
    F["K"] = F.erro.str.extract(r"found (\d+)").astype(int)
    print(F.groupby("K").size().to_string())
    print("\namostra s que falha (1..10):")
    print(F.groupby("amostra").size().to_string())
    print("\ndegrau 2 (4096,40) alcancado?  n falhas com pop_size=4096:",
          int((F.pop_size == 4096).sum()))
    # quantas its escalaram ao degrau 1
    esc = F[F.degrau_falho == 1].groupby("problema").size()
    print("\nits que escalaram ao degrau 1 (falha em 2048,20):")
    print(esc.to_string() if len(esc) else "nenhuma")

# ---------- D. fantasia ABSOLUTA x erro absoluto da sonda ----------
print("\n=== D. |mu-f| mediano: infills (JES escolhe) x sonda (espaco todo)")
out = []
for prob in PROBS:
    b = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    real = pq.read_table(b + "__real.parquet").to_pandas()
    sur = pq.read_table(b + "__surrogate.parquet").to_pandas()
    gab = pq.read_table(f"{REPO}/data/sonda/sonda_{prob}.parquet").to_pandas().iloc[:2000]
    M = sum(1 for c in real.columns if re.fullmatch(r"f\d+", c))
    on = sur[sur.regime == "online"].dropna(subset=["real_solution_id"]).copy()
    on["real_solution_id"] = on["real_solution_id"].astype(int)
    j = on.merge(real[["solution_id"] + [f"f{m}" for m in range(M)]],
                 left_on="real_solution_id", right_on="solution_id")
    sd = sur[sur.regime == "sonda"]
    ult = sd.geracao.max()
    blk = sd[sd.geracao == ult]
    for m in range(M):
        ei = np.abs(j[f"mu_{m}"].values - j[f"f{m}"].values)
        es = np.abs(blk[f"mu_{m}"].values - gab[f"f{m}"].values)
        si = j[f"sigma_{m}"].values
        ss = blk[f"sigma_{m}"].values
        out.append(dict(problema=prob, obj=m,
                        err_infill_med=float(np.median(ei)),
                        err_sonda_med=float(np.median(es)),
                        razao_err=float(np.median(ei) / np.median(es)),
                        sigma_infill_med=float(np.median(si)),
                        sigma_sonda_med=float(np.median(ss)),
                        razao_sigma=float(np.median(si) / np.median(ss)),
                        z_infill=float(np.median(ei / si)),
                        cob_infill=float(np.mean(ei <= 1.96 * si))))
Dz = pd.DataFrame(out)
Dz.to_csv(os.path.join(OUT, "c154_fantasia_absoluta.csv"), index=False)
print(Dz.to_string())
print("\nrazao |erro| infill/sonda: mediana %.2f | >1 em %d/%d" %
      (Dz.razao_err.median(), (Dz.razao_err > 1).sum(), len(Dz)))
print("razao sigma infill/sonda:  mediana %.2f | >1 em %d/%d" %
      (Dz.razao_sigma.median(), (Dz.razao_sigma > 1).sum(), len(Dz)))
print("cobertura +-1.96s NOS INFILLS: mediana %.3f | min %.3f" %
      (Dz.cob_infill.median(), Dz.cob_infill.min()))
