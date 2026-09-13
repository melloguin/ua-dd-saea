import json
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e81"
SONDA = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda"

BOUNDS = {"MMF1": (np.array([1.0, -1.0]), np.array([3.0, 1.0])),
          "DTLZ2": (np.zeros(12), np.ones(12)),
          "ZDT1": (np.zeros(30), np.ones(30))}

for prob in ["MMF1", "DTLZ2", "ZDT1"]:
    stem = f"{BASE}/exp_main_e81_{prob}_42"
    real = pd.read_parquet(stem + "__real.parquet")
    sur = pd.read_parquet(stem + "__surrogate.parquet")
    pop = pd.read_parquet(stem + "__pop.parquet")
    evs = [json.loads(l) for l in open(stem + ".jsonl") if l.strip()]
    decs = {e["geracao"]: e for e in evs if e.get("rec") == "decision"}
    D = len([c for c in real.columns if c.startswith("x")])
    xcols = [f"x{i}" for i in range(D)]
    mcols = sorted([c for c in sur.columns if c.startswith("mu_")])
    scols = sorted([c for c in sur.columns if c.startswith("sigma_")])
    fcols = sorted([c for c in real.columns if c.startswith("f") and c[1:].isdigit()])
    busca = sur[sur["regime"] == "online"]
    print("=" * 90, f"\n### {prob}")

    # (a) x space of layers
    print(f"  [espacos] real.x0 range=({real['x0'].min():.3f},{real['x0'].max():.3f}) | busca.x0 range=({busca['x0'].min():.3f},{busca['x0'].max():.3f})")
    sonda_l = sur[sur["regime"] == "sonda"]
    print(f"             sonda(camada3).x0 range=({sonda_l['x0'].min():.3f},{sonda_l['x0'].max():.3f})")

    # (b) pop semantics: rows per gen == n_init + gen?
    gsz = pop.groupby("geracao").size()
    n_init = real[real["fase"] == "init"].shape[0]
    ok = all(gsz.loc[g] == n_init + g for g in gsz.index)
    print(f"  [pop] rows/gen == n_init+g (dataset acumulado)? {ok}")

    # (c) n_front_acq (jsonl) == n busca rows per gen
    bg = busca.groupby("geracao").size()
    mism = [g for g in bg.index if decs[g]["n_front_acq"] != bg.loc[g]]
    print(f"  [camada3=rank-0] n_front_acq==rows_busca(gen) em {len(bg)-len(mism)}/{len(bg)} gens; mismatches={mism[:5]}")

    # (d) maximin verification (normalized [0,1] space) for 3 gens
    lo, hi = BOUNDS[prob]
    results = []
    for g in [1, len(bg) // 2, len(bg)]:
        cand = busca[busca["geracao"] == g]
        d_ev = decs[g]
        n_train = d_ev["n_train"]
        ds = real.sort_values("fe_index").head(n_train)
        C01 = (cand[xcols].to_numpy(np.float64) - lo) / (hi - lo)
        T01 = (ds[xcols].to_numpy(np.float64) - lo) / (hi - lo)
        mind = cdist(C01, T01).min(axis=1)
        chosen_mask = cand["real_solution_id"].notna().to_numpy()
        argmax_is_chosen = bool(chosen_mask[mind.argmax()])
        mm_data = mind[chosen_mask][0] if chosen_mask.any() else np.nan
        mm_log = d_ev["maximin_escolhido"][0]
        results.append((g, argmax_is_chosen, abs(mm_data - mm_log) < 1e-4, mm_data, mm_log))
    for g, a, b, md, ml in results:
        print(f"  [maximin] gen={g}: escolhido==argmax(dist-min)? {a} | maximin_data={md:.5f} vs jsonl={ml:.5f} match={b}")

    # (e) mu_sel_nat vs camada3 chosen row
    g = len(bg)
    row = busca[(busca["geracao"] == g) & busca["real_solution_id"].notna()]
    mu3 = row[mcols].to_numpy(np.float64)[0]
    mu_j = np.array(decs[g]["mu_sel_nat"][0])
    print(f"  [mu_sel] camada3={np.round(mu3,5).tolist()} vs jsonl={np.round(mu_j,5).tolist()} | max|dif|={np.abs(mu3-mu_j).max():.2e} (float32 na camada)")

    # (f) erro de fantasia no infill: mu vs f real (join por real_solution_id), ultima geracao
    j = busca[busca["real_solution_id"].notna()].merge(
        real[["solution_id"] + fcols], left_on="real_solution_id", right_on="solution_id")
    err = np.abs(j[mcols].to_numpy(np.float64) - j[fcols].to_numpy(np.float64))
    print(f"  [fantasia infills] n={len(j)} | mediana |mu-f| por obj = {np.round(np.median(err,axis=0),4).tolist()}")

    # (g) sonda vs gabarito por posicao (ultimo bloco): WAPE
    art = pd.read_parquet(f"{SONDA}/sonda_{prob}.parquet")
    lastg = int(sonda_l["geracao"].max())
    blk = sonda_l[sonda_l["geracao"] == lastg].reset_index(drop=True)
    gab = art.head(2000)
    x_match = np.allclose(blk[xcols].to_numpy(np.float64), gab[xcols].to_numpy(np.float64), atol=1e-5)
    fgab = gab[[c for c in gab.columns if c.startswith("f")]].to_numpy(np.float64)
    mu = blk[mcols].to_numpy(np.float64)
    wape = np.abs(mu - fgab).sum(axis=0) / np.abs(fgab).sum(axis=0)
    print(f"  [sonda] artefato cols={list(art.columns)[:4]}...S={len(art)} | x bloco==artefato(pos)? {x_match} | WAPE ultimo bloco={np.round(wape,4).tolist()}")

    # (h) cobertura ±2sigma no ultimo bloco da sonda (calibracao)
    sg = blk[scols].to_numpy(np.float64)
    cov2 = ((np.abs(mu - fgab) <= 2 * sg).mean(axis=0))
    print(f"  [calib] cobertura |erro|<=2sigma (ultimo bloco) = {np.round(cov2,3).tolist()} (nominal ~0.954)")

    # (i) sigma no candidato escolhido cai com o tempo?
    sel = busca[busca["real_solution_id"].notna()].sort_values("geracao")
    s0 = sel[scols].head(10).mean().to_numpy()
    s1 = sel[scols].tail(10).mean().to_numpy()
    print(f"  [sigma_sel] media 10 primeiras gens={np.round(s0,4).tolist()} vs 10 ultimas={np.round(s1,4).tolist()}")
