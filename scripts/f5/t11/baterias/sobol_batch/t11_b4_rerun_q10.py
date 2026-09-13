"""T11 · sobol_batch · BATERIA 4 — o smoke que a campanha NAO fez: q=10.

O smoke T11 preservado rodou com `q=1` (o default `Q_PRINCIPAL`), regime que
NAO existe no grid (runs_matrix: 150/150 linhas com q=10). Aqui rodo o runner
de HOJE (HEAD 9ad0138) no ajuste REAL do grid, em TEMPDIR (nunca `data/`), e
comparo com a s42 (PRE-T11) celula a celula.

Escritas: SO no tempdir + f5/t11/baterias/sobol_batch/. Nada em data/.
"""
import json, os, shutil, sys, tempfile, time
import numpy as np
import pandas as pd

REPO = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea"
S42 = "/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/sobol_batch"
OUT = os.path.join(REPO, "f5/t11/baterias/sobol_batch")
sys.path.insert(0, REPO)
os.chdir(REPO)
from src import problems as _problems            # noqa: E402
from src.sobol_batch import run_sobol_batch      # noqa: E402

PROBS = ["DTLZ2", "MMF16_20", "WFG9", "ZDT1", "ZDT4"]
td = tempfile.mkdtemp(prefix="f5t11_sobol_q10_")
os.symlink(os.path.join(REPO, "data", "doe"), os.path.join(td, "doe"))
print("tempdir:", td)
assert not os.path.exists(os.path.join(td, "experiments"))

rows = []
for p in PROBS:
    t0 = time.time()
    out = run_sobol_batch("batch", "sobol_batch", p, 42, data_root=td, q=10)
    wall = time.time() - t0
    pre = os.path.join(td, "experiments", "batch", "sobol_batch",
                       f"exp_batch_sobol_batch_{p}_42")
    man = json.load(open(pre + ".manifest.json"))
    L = [json.loads(l) for l in open(pre + ".jsonl")]
    novo = pd.read_parquet(pre + "__real.parquet")
    tim = pd.read_parquet(pre + "__timing.parquet")
    pop = pd.read_parquet(pre + "__pop.parquet")
    surr = pd.read_parquet(pre + "__surrogate.parquet")
    old_pre = f"{S42}/q10_{p}/42/exp_batch_sobol_batch_{p}_42"
    velho = pd.read_parquet(old_pre + "__real.parquet")
    man42 = json.load(open(old_pre + ".manifest.json"))
    L42 = [json.loads(l) for l in open(old_pre + ".jsonl")]
    pop42 = pd.read_parquet(old_pre + "__pop.parquet")
    xc = [c for c in novo.columns if c.startswith("x") and c[1:].isdigit()]
    fc = [c for c in novo.columns if c.startswith("f") and c[1:].isdigit()]
    D = len(xc)
    dec = [x for x in L if x.get("rec") == "decision"]
    ck = [x for x in L if x.get("rec") == "checkpoint"]

    r = {"problema": p, "D": D}
    # --- NAO-PERTURBACAO: PRE-T11 x POS-T11, mesma semente, mesmo q
    r["X_bit_igual"] = bool(np.array_equal(novo[xc].values, velho[xc].values))
    r["F_bit_igual"] = bool(np.array_equal(novo[fc].values, velho[fc].values))
    r["dX_max"] = float(np.abs(novo[xc].values.astype(np.float64) -
                               velho[xc].values.astype(np.float64)).max())
    r["dF_max"] = float(np.abs(novo[fc].values.astype(np.float64) -
                               velho[fc].values.astype(np.float64)).max())
    r["linhas_igual"] = (len(novo) == len(velho) == man["maxfe"])
    r["pop_igual"] = bool(pop.shape == pop42.shape and
                          np.array_equal(pop.values, pop42.values))
    d42 = [x for x in L42 if x.get("rec") == "decision"]
    r["seeds_iguais"] = int(sum(int(a["seed_sobol"] == b["seed_sobol"])
                                for a, b in zip(dec, d42)))
    r["fbest_iguais"] = int(sum(int(np.allclose(a["f_best"], b["f_best"],
                                                rtol=0, atol=0))
                                for a, b in zip(dec, d42)))
    # --- as correcoes, no ajuste REAL
    r["q_manifesto"] = man["q"]; r["maxfe"] = man["maxfe"]
    r["n_geracoes"] = man["n_geracoes"]
    r["n_front1_presente"] = sum(1 for e in dec if "n_front1" in e)
    F = novo[fc].values.astype(np.float64)
    ok = 0
    for e in dec:
        ok += int(int(e["n_front1"]) ==
                  int(len(_problems._nds_filter(F[:int(e["fe"])]))))
    r["n_front1_correto"] = ok
    nfs = [int(e["n_front1"]) for e in dec]
    r["n_front1_faixa"] = f"{min(nfs)}–{max(nfs)}"
    r["n_front1_distintos"] = len(set(nfs))
    r["n_front1_monotonico"] = int(sum(int(b >= a) for a, b in
                                       zip(nfs, nfs[1:])))
    t = man["timing"]
    r["tempo_aval_real_s"] = t["tempo_aval_real_s"]
    r["tempo_total_s"] = t["tempo_total_s"]
    r["frac_aval_wall"] = t["tempo_aval_real_s"] / t["tempo_total_s"]
    r["proxy_4_sem_doe"] = float((tim["tempo_geracao_s"] -
                                  tim["tempo_busca_s"]).sum())
    r["aval_vs_proxy"] = r["tempo_aval_real_s"] / r["proxy_4_sem_doe"]
    r["params_presente"] = "params" in man
    r["params_q"] = man["params"]["q"]
    r["params_maxfe"] = man["params"]["maxfe"]
    r["schema_version"] = man["schema_version"]
    r["campanha_id"] = man.get("campanha_id")
    r["repo_hash"] = (man.get("repo_hash") or "")[:12]
    r["n_checkpoints"] = len(ck)
    r["custo_checkpoint_s"] = round(sum(c["tempo_checkpoint_s"] for c in ck), 4)
    r["frac_checkpoint_wall"] = r["custo_checkpoint_s"] / t["tempo_total_s"]
    r["surr_linhas"] = len(surr); r["surr_cols"] = surr.shape[1]
    r["sonda_status"] = man["sonda"]["status"]
    r["fit_null"] = int(tim["tempo_fit_s"].isna().sum())
    r["guards"] = sum(1 for x in L if x.get("rec") == "guard")
    r["cache_hits"] = man["cache_hits"]
    r["motivo_parada"] = man["motivo_parada"]
    r["wall_medido_s"] = round(wall, 3)
    r["wall_s42_s"] = man42["timing"]["tempo_total_s"]
    rows.append(r)
    print(f"  {p:10s} X_bit_igual={r['X_bit_igual']} "
          f"n_front1={r['n_front1_correto']}/200 "
          f"aval={r['tempo_aval_real_s']}s ckpt={r['n_checkpoints']}")

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/b4_rerun_q10.csv", index=False)
for c in df.columns:
    print(f"{c:24s}", list(df[c]))
print("\ntempdir preservado p/ inspecao:", td)
