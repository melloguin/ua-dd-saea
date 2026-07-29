#!/usr/bin/env python
"""BATERIA 2 — c154 (JES): empates da query-joia, ruido inferido, sonda, tempo, metricas."""
import json, os, glob
import numpy as np, pandas as pd

ROOT = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c154"
REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
OUT = os.path.join(REPO, "f5/baterias/c154")
import pyarrow.parquet as pq
PROBS = sorted([p for p in os.listdir(ROOT) if not p.startswith('.')])

# ---------- 1. query-joia com tratamento de EMPATE ----------
res = []
for prob in PROBS:
    base = f"{ROOT}/{prob}/42/exp_main_c154_{prob}_42"
    L = [json.loads(l) for l in open(base + ".jsonl") if l.strip()]
    dec = [r for r in L if r.get("rec") == "decision"]
    sur = pq.read_table(base + "__surrogate.parquet").to_pandas()
    on = sur[sur["regime"] == "online"]
    D = [r for r in L if r.get("rec") == "header"][0]["D"]
    exato = tie = mism = 0
    ties_n = []
    for d in dec:
        a = np.array(d.get("acqf_todos_restarts", []), float)
        if not len(a):
            continue
        g = d["it"]; blk = on[on["geracao"] == g]
        if len(blk) != len(a) or not blk["real_solution_id"].notna().any():
            continue
        pos = int(np.flatnonzero(blk["real_solution_id"].notna().values)[0])
        af = np.where(np.isfinite(a), a, -np.inf)
        mx = af.max()
        if pos == int(np.argmax(af)):
            exato += 1
        elif np.isclose(af[pos], mx, rtol=1e-9, atol=1e-12):
            tie += 1
        else:
            mism += 1
        ties_n.append(int(np.isclose(af, mx, rtol=1e-9, atol=1e-12).sum()))
    res.append(dict(problema=prob, D=D, pos_exata=exato, pos_empate=tie,
                    pos_mismatch=mism,
                    n_empates_med=float(np.median(ties_n)) if ties_n else np.nan,
                    n_empates_max=int(np.max(ties_n)) if ties_n else 0))
qj = pd.DataFrame(res)
qj.to_csv(os.path.join(OUT, "c154_queryjoia_posicao.csv"), index=False)
print("=== QUERY-JOIA posicao (com empates)")
print(qj.to_string())
print("TOTAIS: exata=%d empate=%d mismatch=%d" %
      (qj.pos_exata.sum(), qj.pos_empate.sum(), qj.pos_mismatch.sum()))

# ---------- 2. ruido inferido (PRIOR 6.0 v2) ----------
hp = pd.read_csv(os.path.join(OUT, "c154_modelo_hp.csv"))
g = hp.groupby(["problema", "obj"])["noise"]
rz = g.agg(["min", "max", "median", "first", "last"]).reset_index()
rz["razao_max_min"] = rz["max"] / rz["min"]
rz["n_no_piso"] = hp[hp.noise <= 1.0001e-4].groupby(["problema", "obj"]).size().reindex(
    pd.MultiIndex.from_frame(rz[["problema", "obj"]])).fillna(0).values
# maior salto entre iteracoes consecutivas
sal = []
for (p, o), sub in hp.sort_values("it").groupby(["problema", "obj"]):
    v = sub["noise"].values
    it = sub["it"].values
    ratio = v[1:] / np.maximum(v[:-1], 1e-300)
    k = int(np.argmax(ratio))
    sal.append(dict(problema=p, obj=o, salto_max=float(ratio[k]),
                    salto_it=int(it[k + 1]),
                    noise_antes=float(v[k]), noise_depois=float(v[k + 1]),
                    janela_max_it=int(it[int(np.argmax(v))]),
                    noise_pico=float(v.max())))
rz = rz.merge(pd.DataFrame(sal), on=["problema", "obj"])
rz.to_csv(os.path.join(OUT, "c154_ruido_inferido.csv"), index=False)
print("\n=== RUIDO INFERIDO por celula-objetivo")
print(rz.to_string())

# ---------- 3. sonda oficial (f52e) do c154 ----------
son = pd.read_csv(os.path.join(REPO, "f5/sonda_f52e.csv"))
s = son[(son.alg == "c154") & (son.exp == "main")].copy()
s.to_csv(os.path.join(OUT, "c154_sonda_f52e_recorte.csv"), index=False)
agg = []
for (p, o), sub in s.groupby(["problema", "obj"]):
    sub = sub.sort_values("bloco")
    w0, w1 = sub.wape.iloc[0], sub.wape.iloc[-1]
    c0, c1 = sub.cobertura95.iloc[0], sub.cobertura95.iloc[-1]
    agg.append(dict(problema=p, obj=o, n_blocos=len(sub), wape_1=w0, wape_N=w1,
                    dwape_pct=100 * (w1 - w0) / w0 if w0 else np.nan,
                    wape_max=sub.wape.max(), cob_1=c0, cob_N=c1,
                    cob_min=sub.cobertura95.min(), cob_med=sub.cobertura95.median(),
                    corr_N=sub["corr"].iloc[-1],
                    nan_total=sub.n_nan.sum()))
A = pd.DataFrame(agg)
A.to_csv(os.path.join(OUT, "c154_sonda_resumo.csv"), index=False)
print("\n=== SONDA (f52e) resumo por celula-objetivo")
print(A.to_string())
print("\nDELTA WAPE mediano (%%): %.1f | melhoram: %d/%d" %
      (A.dwape_pct.median(), (A.dwape_pct < 0).sum(), len(A)))
print("Cobertura final: mediana %.3f | min %.3f | <0.90: %d/%d" %
      (A.cob_N.median(), A.cob_N.min(), (A.cob_N < 0.90).sum(), len(A)))

# ---------- 4. metricas + trajetorias ----------
met = pd.read_csv(os.path.join(REPO, "f5/metricas_finais_f52c.csv"))
mc = met[(met.alg == "c154") & (met.exp == "main")]
print("\n=== METRICAS c154 main")
print(mc.to_string())
tr = []
for p in PROBS:
    t = json.load(open(f"{REPO}/f5/trajetorias/main_c154_{p}_42.json"))
    ig = np.array([x["igd_plus"] for x in t])
    hv = np.array([x["hv"] for x in t])
    nd = np.array([x["n_nd"] for x in t])
    tr.append(dict(problema=p, n_ckpt=len(t), igd0=ig[0], igdN=ig[-1],
                   viol_igd=int((np.diff(ig) > 1e-12).sum()),
                   viol_igd_max=float(np.diff(ig).max()),
                   viol_hv=int((np.diff(hv) < -1e-12).sum()),
                   nd0=int(nd[0]), ndN=int(nd[-1]),
                   ganho_pct=100 * (ig[-1] - ig[0]) / ig[0]))
T = pd.DataFrame(tr)
T.to_csv(os.path.join(OUT, "c154_trajetorias.csv"), index=False)
print("\n=== TRAJETORIAS (20 checkpoints)")
print(T.to_string())

# ---------- 5. tempo ----------
tp = pd.read_csv(os.path.join(REPO, "f5/tempo_f52d.csv"))
tc = tp[(tp.alg == "c154")]
tc.to_csv(os.path.join(OUT, "c154_tempo.csv"), index=False)
print("\n=== TEMPO c154")
print(tc.to_string())
print("total h-core: %.2f | maquinas: %s" %
      (tc.wall_s.sum() / 3600, tc.maquina.value_counts().to_dict()))

# ---------- 6. contrato / integridade ----------
co = pd.read_csv(os.path.join(REPO, "f5/contrato_f52b.csv"))
ic = pd.read_csv(os.path.join(REPO, "f5/integridade_f52a.csv"))
print("\n=== CONTRATO c154:", len(co[co.alg == "c154"]), "linhas")
print(co[co.alg == "c154"].to_string())
print("\n=== INTEGRIDADE c154:", len(ic[ic.alg == "c154"]), "linhas")
print(ic[ic.alg == "c154"].to_string())
