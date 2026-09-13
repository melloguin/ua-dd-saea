import json
import numpy as np
import pandas as pd

BASE = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/main/e7/"
SND = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/"

for prob in ["MMF1", "DTLZ2", "ZDT1"]:
    sur = pd.read_parquet(BASE + f"exp_main_e7_{prob}_42__surrogate.parquet")
    gab = pd.read_parquet(SND + f"sonda_{prob}.parquet")
    M = len([c for c in gab.columns if c.startswith("f") and c[1:].isdigit()])
    fcols = [f"f{j}" for j in range(M)]
    snd = sur[sur["regime"] == "sonda"]
    gens = sorted(snd["geracao"].unique())
    print("=" * 80)
    print(f"{prob}: gabarito linhas={len(gab)} cols={list(gab.columns)[:6]}...; blocos sonda gens={gens}")
    out = []
    for g in [gens[0], gens[len(gens)//2], gens[-1]]:
        blk = snd[snd["geracao"] == g].reset_index(drop=True)
        assert len(blk) == 2000, len(blk)
        ymin = np.array(json.loads(blk["transf_params"].iloc[0])["ymin"])
        mu = blk[[f"mu_{j}" for j in range(M)]].to_numpy() + ymin  # volta ao cru
        sg = blk[[f"sigma_{j}" for j in range(M)]].to_numpy()
        ft = gab.iloc[:2000][fcols].to_numpy()  # join POR POSICAO (online = 2000 primeiros)
        wape = np.abs(mu - ft).sum() / np.abs(ft).sum() * 100
        cov = (np.abs(mu - ft) <= 1.96 * sg).mean()
        out.append((g, wape, cov, sg.mean()))
    for g, w, c, s in out:
        print(f"  bloco ger={g}: WAPE={w:.1f}% cobertura95={c:.2f} sigma_medio={s:.4f}")
