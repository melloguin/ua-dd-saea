#!/usr/bin/env python
"""BATERIA 3 — c154 (JES): ruido x cobertura por bloco, plateau da acqf, bounds,
posicao vs pisos/rivais, timing fino."""
import json, os
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")
PROBS = sorted([p for p in os.listdir(ROOT) if not p.startswith('.')])
PISOS = ["moead", "nsga2", "nsga3", "smsemoa"]

# ---------- A. ruido x cobertura x WAPE por bloco ----------
son = pd.read_csv(os.path.join(REPO, "f5/sonda_f52e.csv"))
s = son[(son.alg == "c154") & (son.exp == "main")].copy()
hp = pd.read_csv(os.path.join(OUT, "c154_modelo_hp.csv"))
# bloco k da sonda <-> geracao; a sonda roda DEPOIS do fit da geracao g
blocos = []
for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    sn = [r for r in L if r.get("rec") == "sonda"]
    for k, rec in enumerate(sn, start=1):
        blocos.append(dict(problema=prob, bloco=k, geracao=rec["geracao"],
                           fe=rec["fe"], fe_treino_max=rec["fe_treino_max"]))
B = pd.DataFrame(blocos)
s["bloco"] = s["bloco"].astype(int)          # no f52e, `bloco` JA E a geracao
s = s.merge(B.rename(columns={"bloco": "k_bloco"}), left_on=["problema", "bloco"],
            right_on=["problema", "geracao"], how="left", suffixes=("", "_j"))
s = s.merge(hp[["problema", "it", "obj", "noise", "ls_med", "outputscale", "mll"]],
            left_on=["problema", "bloco", "obj"],
            right_on=["problema", "it", "obj"], how="left")
s.to_csv(os.path.join(OUT, "c154_sonda_x_ruido.csv"), index=False)

print("=== A. correlacao ruido x cobertura x WAPE (por celula-objetivo)")
out = []
for (p, o), sub in s.groupby(["problema", "obj"]):
    sub = sub.sort_values("bloco").dropna(subset=["noise"])
    if len(sub) < 5:
        continue
    out.append(dict(
        problema=p, obj=o, n=len(sub),
        r_noise_cob=float(np.corrcoef(np.log(sub.noise), sub.cobertura95)[0, 1]),
        r_noise_wape=float(np.corrcoef(np.log(sub.noise), sub.wape)[0, 1]),
        noise_ini=float(sub.noise.iloc[0]), noise_fim=float(sub.noise.iloc[-1]),
        noise_max=float(sub.noise.max()),
        cob_no_noise_max=float(sub.loc[sub.noise.idxmax(), "cobertura95"]),
        wape_no_noise_max=float(sub.loc[sub.noise.idxmax(), "wape"]),
        cob_ini=float(sub.cobertura95.iloc[0]), cob_fim=float(sub.cobertura95.iloc[-1]),
        cob_min=float(sub.cobertura95.min()),
        bloco_cob_min=int(sub.loc[sub.cobertura95.idxmin(), "bloco"]),
        noise_no_cob_min=float(sub.loc[sub.cobertura95.idxmin(), "noise"])))
A = pd.DataFrame(out)
A.to_csv(os.path.join(OUT, "c154_ruido_x_cobertura.csv"), index=False)
print(A.to_string())
print("\ncorrelacao log(noise) x cobertura: mediana %.3f | negativa em %d/%d" %
      (A.r_noise_cob.median(), (A.r_noise_cob < 0).sum(), len(A)))
print("correlacao log(noise) x WAPE:      mediana %.3f | positiva em %d/%d" %
      (A.r_noise_wape.median(), (A.r_noise_wape > 0).sum(), len(A)))

# janela do achado-de-ouro: MMF1 obj1 e ZDT4 obj1
for p, o in [("MMF1", 1), ("ZDT4", 1), ("DTLZ1", 2), ("BBOB_F22", 0)]:
    sub = s[(s.problema == p) & (s.obj == o)].sort_values("bloco")
    print(f"\n--- {p} obj{o}: bloco/ger | noise | wape | cob95")
    print(sub[["bloco", "noise", "wape", "cobertura95"]]
          .head(30).to_string(index=False))

# ---------- B. plateau da acqf ----------
pl = []
for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    dec = [r for r in L if r.get("rec") == "decision"]
    sur = pq.read_table(base + "__surrogate.parquet").to_pandas()
    on = sur[sur["regime"] == "online"]
    D = [r for r in L if r.get("rec") == "header"][0]["D"]
    xc = [f"x{i}" for i in range(D)]
    n_pl = 0; n_it = 0; maxspread = []
    for d in dec:
        a = np.array(d.get("acqf_todos_restarts", []), float)
        if not len(a):
            continue
        n_it += 1
        af = np.where(np.isfinite(a), a, -np.inf)
        mx = af.max()
        tie = np.isclose(af, mx, rtol=1e-9, atol=0)
        if tie.sum() >= 2:
            blk = on[on["geracao"] == d["it"]]
            if len(blk) == len(a):
                X = blk[xc].values.astype(np.float64)
                sel = X[tie]
                dmax = float(np.abs(sel[:, None, :] - sel[None, :, :]).max())
                maxspread.append(dmax)
                if dmax > 1e-3:
                    n_pl += 1
    pl.append(dict(problema=prob, D=D, n_it=n_it, n_plateau_disjunto=n_pl,
                   pct=100.0 * n_pl / n_it,
                   spread_med=float(np.median(maxspread)) if maxspread else np.nan))
P = pd.DataFrame(pl)
P.to_csv(os.path.join(OUT, "c154_plateau_acqf.csv"), index=False)
print("\n=== B. PLATEAU da acqf (>=2 restarts empatados a 1e-9 rel em x distantes)")
print(P.to_string())

# ---------- C. bounds nativos ----------
bd = []
for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    real = pq.read_table(base + "__real.parquet").to_pandas()
    sur = pq.read_table(base + "__surrogate.parquet").to_pandas()
    xc = [c for c in real.columns if c.startswith("x")]
    lo = real[xc].min().values; hi = real[xc].max().values
    slo = sur[xc].min().values; shi = sur[xc].max().values
    bd.append(dict(problema=prob, x_min_1=float(lo.min()), x_max_1=float(hi.max()),
                   x_min_3=float(slo.min()), x_max_3=float(shi.max()),
                   fora_1=int(0), lb_por_dim=";".join("%.3g" % v for v in lo[:4]),
                   ub_por_dim=";".join("%.3g" % v for v in hi[:4])))
Bd = pd.DataFrame(bd)
Bd.to_csv(os.path.join(OUT, "c154_bounds.csv"), index=False)
print("\n=== C. BOUNDS (min/max de x na ① e na ③)")
print(Bd.to_string())

# ---------- D. posicao vs pisos e rivais (11 problemas) ----------
met = pd.read_csv(os.path.join(REPO, "f5/metricas_finais_f52c.csv"))
mm = met[met.exp == "main"]
rank = []
for prob in PROBS:
    sub = mm[mm.problema == prob].set_index("alg")
    if "c154" not in sub.index:
        continue
    ig = sub["igd_plus"]
    piso = ig[[a for a in PISOS if a in ig.index]]
    sa = ig[[a for a in ig.index if a not in PISOS]]
    r = dict(problema=prob, igd_c154=float(ig["c154"]),
             melhor_piso=float(piso.min()), piso_arg=piso.idxmin(),
             delta_vs_piso_pct=100 * (ig["c154"] - piso.min()) / piso.min(),
             bate_piso=bool(ig["c154"] < piso.min()),
             rank_sa=int(sa.rank().loc["c154"]), n_sa=len(sa),
             melhor_sa=sa.idxmin(), igd_melhor_sa=float(sa.min()),
             igd_c262=float(ig.get("c262", np.nan)),
             igd_e81=float(ig.get("e81", np.nan)),
             hv_c154=float(sub.loc["c154", "hv"]),
             nd_c154=int(sub.loc["c154", "n_nd"]))
    rank.append(r)
R = pd.DataFrame(rank)
R.to_csv(os.path.join(OUT, "c154_posicao_vs_rivais.csv"), index=False)
print("\n=== D. POSICAO vs pisos e rivais (IGD+)")
print(R.to_string())
print("\nbate o melhor piso em %d/%d | rank medio SA %.2f de %d | vence c262 em %d/%d | vence e81 em %d/%d"
      % (R.bate_piso.sum(), len(R), R.rank_sa.mean(), R.n_sa.max(),
         (R.igd_c154 < R.igd_c262).sum(), R.igd_c262.notna().sum(),
         (R.igd_c154 < R.igd_e81).sum(), R.igd_e81.notna().sum()))

# ---------- E. timing fino ----------
tm = []
for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    man = json.load(open(base + ".manifest.json"))
    t = pq.read_table(base + "__timing.parquet").to_pandas()
    L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    dec = [r for r in L if r.get("rec") == "decision"]
    sn = {r["geracao"] for r in L if r.get("rec") == "sonda"}
    tp = np.array([d.get("t_paths_s", np.nan) for d in dec], float)
    v1 = ((t.tempo_fit_s + t.tempo_busca_s) <= t.tempo_geracao_s + 1e-9)
    exc = t[(t.tempo_fit_s + t.tempo_busca_s + t.tempo_pred_sonda_s)
            > t.tempo_geracao_s + 1e-9].geracao.tolist()
    tm.append(dict(problema=prob, wall_h=man["timing"]["tempo_total_s"] / 3600,
                   t_fit=man["timing"]["tempo_fit_surrogate_s"],
                   t_busca=man["timing"]["tempo_busca_s"],
                   t_paths=man["timing"]["tempo_paths_s"],
                   paths_pct_busca=100 * man["timing"]["tempo_paths_s"] /
                   man["timing"]["tempo_busca_s"],
                   t_sonda=man["timing"]["tempo_pred_sonda_s"],
                   t_aval_real=man["timing"]["tempo_aval_real_s"],
                   inv1_viol=int((~v1).sum()), n_ger=len(t),
                   exc_total=len(exc), exc_sao_sonda=set(exc).issubset(sn),
                   sonda_sem_exc=len(sn - set(exc)), n_sonda=len(sn),
                   busca_por_it_s=man["timing"]["tempo_busca_s"] / len(t)))
T = pd.DataFrame(tm)
T.to_csv(os.path.join(OUT, "c154_timing_fino.csv"), index=False)
print("\n=== E. TIMING fino")
print(T.to_string())
